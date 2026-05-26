import os
import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal
from src.logic.Image_processing import ImageProcessing
from src.logic.subap_validator import SubapValidator
import multiprocessing as mp
from functools import partial

def _worker_process(chunk_indices, common_args, queue):
    for idx in chunk_indices:
        try:
            result = _process_one_frame((idx, *common_args))
            queue.put(('progress', result))
        except Exception as e:
            queue.put(('error', idx, str(e)))
            break

def _process_one_frame(args):
    """
    Аргументы: (frame_idx, h5_path, contours, db_path, file_id, output_dir,
               image_width, image_height, template_np, threshold)
    Возвращает frame_idx (для прогресса) или выбрасывает исключение.
    """
    (frame_idx, h5_path, contours, db_path, file_id,
     output_dir, image_width, image_height, template_np, threshold) = args

    # Каждый процесс открывает свой reader (h5py не потокобезопасен)
    from src.logic.format.h5 import H5LazyReader
    from src.logic.subap_validator import SubapValidator
    from src.logic.storage import SubapStorage
    import numpy as np
    import os

    reader = H5LazyReader(h5_path)
    try:
        img = reader.get_image(frame_idx)
        if img.dtype == np.uint16:
            img = (img / 256).astype(np.uint8)

        # Создаём валидатор и устанавливаем готовый шаблон (переданный из главного процесса)
        validator = SubapValidator(threshold=threshold)
        validator.set_contours(contours)
        # Устанавливаем шаблон (переданный numpy массив)
        validator._spot_template = template_np   # прямой доступ, но можно добавить setter

        # Валидация ячеек
        valid_set = validator.determine_valid_cells(img)
        if not valid_set:
            return frame_idx

        # Нарезка субапертур (копируем из существующего кода)
        xs = contours['x']
        ys = contours['y']
        max_w = contours['max_width']
        max_h = contours['max_height']
        sub_arrays = []
        meta_data = []
        target = sorted(valid_set, key=lambda cell: (cell[1], cell[0]))
        for col, row in target:
            x = xs[col]
            y = ys[row]
            w = xs[1] - x - 5 if col == 0 else max_w
            h = ys[1] - y - 5 if row == 0 else max_h
            sub_img = img[y:y+h, x:x+w]
            sub_arrays.append(sub_img)
            meta_data.append((col, row, x, y, w, h, 0))

        # Хранилище (открывает своё соединение с БД)
        storage = SubapStorage(base_dir=os.path.dirname(db_path))
        storage.db_path = db_path
        
        if storage.is_frame_ready(file_id, frame_idx):
            return frame_idx

        num_cols = len(xs) - 1
        num_rows = len(ys) - 1
        frame_id = storage.get_or_create_frame(file_id, frame_idx,
                                               image_width, image_height,
                                               num_rows, num_cols)
        # Создаём все записи субапертур для этого кадра (если их ещё нет)
        storage.create_subapertures_for_frame(frame_id, contours)
        archive_path = os.path.join(output_dir, f"frame_{frame_idx}.npz")
        storage.save_frame_archive(frame_id, archive_path, sub_arrays, meta_data)
        storage.update_cells_status(frame_id, valid_set, set())
        # storage.exclude_invalid_cells(frame_id)

        return frame_idx
    finally:
        reader.close()

class PrepareThread(QThread):
    progress = pyqtSignal(int, int)   # текущий кадр, всего
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, reader, contours, validator, storage, file_id, total_frames, output_dir,
                 image_width, image_height):
        super().__init__()
        self.reader = reader
        self.contours = contours
        self.validator = validator
        self.storage = storage
        self.file_id = file_id
        self.total = total_frames
        self.output_dir = output_dir
        self.image_width = image_width
        self.image_height = image_height
        self._cancel = False
        self.valid_masks = {}   # словарь: frame_idx -> 2D numpy bool массив (grid_rows, grid_cols)
        # Дополнительно сохраняем шаблон из валидатора (если он уже установлен)
        self.template = getattr(validator, '_spot_template', None)
        self.threshold = validator.threshold if validator else 0.5

    def cancel(self):
        self._cancel = True

    def _prepare_frame_archive_data(self, img, target):
        """Вспомогательный метод для подготовки массивов и метаданных."""
        xs = self.contours['x']
        ys = self.contours['y']
        max_w = self.contours['max_width']
        max_h = self.contours['max_height']
        sub_arrays = []
        meta_data = []
        for col, row in target:
            x = xs[col]
            y = ys[row]
            if col == 0:
                w = xs[1] - x - 5
            else:
                w = max_w
            if row == 0:
                h = ys[1] - y - 5
            else:
                h = max_h
            sub_img = img[y:y+h, x:x+w]
            sub_arrays.append(sub_img)
            meta_data.append((col, row, x, y, w, h, 0))
        return sub_arrays, meta_data

    # def run(self):
    #     try:
    #         self.output_dir = os.path.abspath(self.output_dir)
    #         num_cols = len(self.contours['x']) - 1
    #         num_rows = len(self.contours['y']) - 1
    #         for frame_idx in range(self.total):
    #             if self._cancel:
    #                 break
    #             if self.storage.is_frame_ready(self.file_id, frame_idx):
    #                 continue

    #             img = self.reader.get_image(frame_idx)
    #             if img.dtype == np.uint16:
    #                 img = (img / 256).astype(np.uint8)

    #             valid_set = self.validator.determine_valid_cells(img)
    #             mask = np.zeros((num_rows, num_cols), dtype=bool)
    #             for col, row in valid_set:
    #                 mask[row, col] = True
    #             self.valid_masks[frame_idx] = mask

    #             if not valid_set:
    #                 continue

    #             target = sorted(valid_set, key=lambda cell: (cell[1], cell[0]))
    #             sub_arrays, meta_data = self._prepare_frame_archive_data(img, target)

    #             frame_id = self.storage.get_or_create_frame(
    #                 self.file_id, frame_idx,
    #                 self.image_width, self.image_height,
    #                 num_rows, num_cols
    #             )
    #             archive_path = os.path.join(self.output_dir, f"frame_{frame_idx}.npz")
    #             archive_path = os.path.abspath(archive_path)
    #             self.storage.save_frame_archive(frame_id, archive_path, sub_arrays, meta_data)
    #             self.storage.update_cells_status(frame_id, valid_set, set())
    #             self.storage.exclude_invalid_cells(frame_id)
    #             self.progress.emit(frame_idx + 1, self.total)

    #         # Единственный finished после обработки всех кадров
    #         self.finished.emit()
    #     except Exception as e:
    #         self.error.emit(str(e))
    
    def run(self):
        print("DEBUG: PrepareThread.run started")
        # Отбираем только те кадры, для которых ещё нет архива
        indices_to_process = []
        for idx in range(self.total):
            if not self.storage.is_frame_ready(self.file_id, idx):
                indices_to_process.append(idx)
        
        if not indices_to_process:
            # Все кадры уже готовы – просто завершаем
            self.finished.emit()
            return
        
        # Далее работаем с indices_to_process вместо self.total и range(self.total)
        total_to_process = len(indices_to_process)
        # Количество процессов = число ядер CPU
        num_workers = mp.cpu_count()
        print(num_workers)
        # indices = list(range(self.total))
        # Разбиваем на чанки (каждый воркер получит ~ total / (num_workers*2) кадров)
        chunk_size = max(1, total_to_process // (num_workers * 2))
        chunks = [indices_to_process[i:i+chunk_size] for i in range(0, total_to_process, chunk_size)]

        # Очередь для прогресса
        progress_queue = mp.Queue()

        # Подготавливаем общие аргументы для каждого кадра (кроме индекса)
        common_args = (
            self.reader._path,
            self.contours,
            self.storage.db_path,
            self.file_id,
            self.output_dir,
            self.image_width,
            self.image_height,
            self.template,      # numpy массив шаблона
            self.threshold
        )



        processes = []
        for chunk in chunks:
            p = mp.Process(target=_worker_process, args=(chunk, common_args, progress_queue))
            p.start()
            processes.append(p)

        processed = 0
        errors = []
        while processed < total_to_process:
            try:
                item = progress_queue.get(timeout=0.5)
            except:
                # если все процессы завершены, выходим
                if all(not p.is_alive() for p in processes):
                    break
                continue

            if item[0] == 'progress':
                processed += 1
                self.progress.emit(processed, total_to_process)
            elif item[0] == 'error':
                _, idx, err_msg = item
                errors.append(f"Кадр {idx}: {err_msg}")
                processed += 1   # считаем ошибочный кадр как обработанный, чтобы не зависнуть
                self.progress.emit(processed, total_to_process)

            if self._cancel:
                for p in processes:
                    p.terminate()
                break

        for p in processes:
            p.join()

        if errors:
            self.error.emit("\n".join(errors))
        elif not self._cancel:
            self.finished.emit()
    