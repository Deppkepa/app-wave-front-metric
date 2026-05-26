# ⁡⁢⁢⁢INFO⁡⁡: пока временный класс который будет управлять всеми классами
# INFO: Output: Готовые модели, Input: имя файла
# INFO: Активизация преобразования данных из файла в модели

import numpy as np
from typing import Tuple, Dict
from collections import OrderedDict
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import QByteArray, QMutex, QMutexLocker, QBuffer
from src.logic.format.h5 import H5LazyReader
from src.logic.Image_processing import ImageProcessing
from src.logic.format.pixmap import Pixmap
import os, hashlib, cv2
from src.logic.subap_validator import SubapValidator
from src.logic.storage import SubapStorage
from src.logic.prepare_thread import PrepareThread

from src.logic.analysis_thread import AnalysisThread

class Manager:
    def __init__(self, cache_size=10):
        self._reader = None
        self._cached_valid_masks = None   # для хранения масок из PrepareThread
        self._compressed_images = []   # список QByteArray (JPEG)
        self._contours = None
        self._cache = OrderedDict()    # index -> QPixmap
        self._cache_size = cache_size
        self._cache_mutex = QMutex()
        # self._storage = None
        self._total = 0
        self.prepare_thread = None
        self._subaperture_rects = None   # список словарей с прямоугольниками и индексами
        # self._file_path = None
        self.validator = None
        self.analysis_thread = None

    
    def open_file(self, file_path: str, progress_callback=None) -> int:
        """Открывает HDF5, сжимает все кадры в JPEG и хранит в памяти."""
        self._reader = H5LazyReader(file_path)
        self._total = self._reader.num_images

        # Контуры вычисляем один раз на первом кадре (полноразмерном)
        first_img = self._reader.get_image(0)
        self._contours = ImageProcessing.search_contours(first_img)
        # Создаём валидатор
        self.validator = SubapValidator(threshold=0.5)
        self.validator.set_contours(self._contours)
        num_cols = len(self._contours['x']) - 1
        num_rows = len(self._contours['y']) - 1
        self.validator.set_template_from_real(first_img, num_cols, num_rows, margin=2)
        # Единое хранилище – создаём при первом открытии любого файла
        if not hasattr(self, '_storage'):
            self._storage = SubapStorage()
            self._storage.init_db()          # ← здесь создаётся БД (если её нет)
            self._db_path = self._storage.db_path

        # Далее: вычисляем хеш, регистрируем файл, получаем file_id
        file_hash = self._reader.compute_hash()
        file_id = self._storage.get_file_id(file_hash)
        if file_id is None:
            file_id = self._storage.insert_file(file_path, file_hash,
                                                os.path.getsize(file_path),
                                                os.path.getmtime(file_path))
        else:
            self._storage.update_file_path(file_id, file_path, os.path.getmtime(file_path))
        self._file_id = file_id

        # Не забываем сохранить размеры изображения
        self._image_height, self._image_width = self._reader.image_shape
        # Кэш сжатых JPEG
        # cache_dir = os.path.join(self._storage.base_dir, f"file_{file_id}", "jpg_cache")
        # if os.path.isdir(cache_dir) and len(os.listdir(cache_dir)) == self._total:
        #     # Загружаем из кэша
        #     self._compressed_images = []
        #     for i in range(self._total):
        #         with open(os.path.join(cache_dir, f"frame_{i}.jpg"), "rb") as f:
        #             data = f.read()
        #             self._compressed_images.append(QByteArray(data))
        #     if progress_callback:
        #         progress_callback(self._total, self._total)
        #     return self._total

        # # Иначе сжимаем и сохраняем в кэш
        # os.makedirs(cache_dir, exist_ok=True)
        # self._compressed_images = []
        # for i in range(self._total):
        #     if progress_callback:
        #         progress_callback(i + 1, self._total)
        #     img = self._reader.get_image(i)
        #     if img.dtype == np.uint16:
        #         img = (img / 256).astype(np.uint8)
        #     elif img.dtype != np.uint8:
        #         img = img.astype(np.uint8)

        #     h, w = img.shape
        #     qimg = QImage(img.data, w, h, w, QImage.Format_Grayscale8)
            # buffer = QBuffer()
            # buffer.open(QBuffer.WriteOnly)
            # qimg.save(buffer, "JPEG", quality=85)
            # compressed_data = buffer.data()
            # buffer.close()
            # self._compressed_images.append(compressed_data)

            # Сохраняем в кэш
            # with open(os.path.join(cache_dir, f"frame_{i}.jpg"), "wb") as f:
            #     f.write(compressed_data.data())
        
        

        # Закрываем читатель (данные уже все в памяти в сжатом виде)
        # self._reader.close()
        # self._reader = None
        return self._total

    def get_pixmap(self, index: int) -> QPixmap:
        """Возвращает QPixmap для индекса (используя кэш)."""
        if index < 0 or index >= self._total:
            raise IndexError

        # Проверяем кэш
        with QMutexLocker(self._cache_mutex):
            if index in self._cache:
                return self._cache[index]
                # self._cache.move_to_end(index)
                # return self._cache[index]
        # Лениво читаем кадр из HDF5
        img = self._reader.get_image(index)
        if img.dtype == np.uint16:
            img = (img / 256).astype(np.uint8)
        elif img.dtype != np.uint8:
            img = img.astype(np.uint8)

        h, w = img.shape
        qimg = QImage(img.data, w, h, w, QImage.Format_Grayscale8)
        pix = QPixmap.fromImage(qimg)

        # # Нет в кэше: декодируем JPEG
        # compressed = self._compressed_images[index]
        # pixmap = QPixmap()
        # if not pixmap.loadFromData(compressed, "JPEG"):
        #     raise RuntimeError(f"Failed to decode JPEG for index {index}")

        # Помещаем в кэш
        with QMutexLocker(self._cache_mutex):
            self._cache[index] = pix
            if len(self._cache) > self._cache_size:
                self._cache.popitem(last=False)
        return pix

    def get_image_and_contours(self, index: int) -> Tuple[QPixmap, dict]:
        """Возвращает (QPixmap, contours) для индекса."""
        pix = self.get_pixmap(index)
        return pix, self._contours

    def get_num_images(self) -> int:
        return self._total

    def close(self):
        with QMutexLocker(self._cache_mutex):
            self._cache.clear()
        self._compressed_images.clear()
        if self._reader:
            self._reader.close()
        
        
    def cancel_background_init(self):
        if hasattr(self, '_preinit_thread') and self._preinit_thread.isRunning():
            self._preinit_thread.cancel()
            self._preinit_thread.wait()
            
    
    # def run_background_init(self):
    #     """Запускает фоновую инициализацию метаданных."""
    #     if not hasattr(self, '_storage') or self._storage.db_path is None:
    #         raise RuntimeError("Сначала откройте файл")
    #     from src.logic.preinit_thread import PreinitThread
    #     self._preinit_thread = PreinitThread(
    #         db_path=self._storage.db_path,
    #         file_id=self._file_id,
    #         contours=self._contours,
    #         total_frames=self._total,
    #         image_width=self._image_width,
    #         image_height=self._image_height
    #     )
    #     # self._preinit_thread.progress.connect(self._on_preinit_progress)  # опционально
    #     self._preinit_thread.start()
    
    def run_background_init(self):
        if not hasattr(self, '_storage') or self._storage.db_path is None:
            raise RuntimeError("Сначала откройте файл")
        from src.logic.preinit_thread import PreinitThread
        self._preinit_thread = PreinitThread(
            db_path=self._storage.db_path,
            file_id=self._file_id,
            contours=self._contours,
            total_frames=self._total,
            image_width=self._image_width,
            image_height=self._image_height
        )
        self._preinit_thread.finished.connect(self._on_preinit_finished)
        self._preinit_thread.start()

    def _on_preinit_finished(self):
        # Скелет таблиц готов – запускаем нарезку
        
        self.prepare_all_subapertures()
        
    def cancel_prepare(self):
        # if hasattr(self, 'prepare_thread') and self.prepare_thread.isRunning():
        if self.prepare_thread is not None and self.prepare_thread.isRunning():
            self.prepare_thread.cancel()
            self.prepare_thread.wait()

    def update_excluded_for_frame(self, frame_index: int, excluded_cells: list):
        frame_id = self._storage.get_frame_id(self._file_id, frame_index)
        excluded_set = set(excluded_cells)
        
        # Получаем valid_set из кэша или вычисляем заново (fallback)
        if self._cached_valid_masks is not None and frame_index in self._cached_valid_masks:
            mask = self._cached_valid_masks[frame_index]
            valid_set = set()
            rows, cols = mask.shape
            for row in range(rows):
                for col in range(cols):
                    if mask[row, col]:
                        valid_set.add((col, row))
        else:
            # Если кэша нет (например, подготовка ещё не завершена), вычисляем
            img = self._reader.get_image(frame_index)
            valid_set = self.validator.determine_valid_cells(img)
        
        self._storage.update_cells_status(frame_id, valid_set, excluded_set)
        print(f"Кадр {frame_index}: обновлены исключения")

    def save_subapertures_for_frame(self, frame_index: int, excluded_cells: list):
        self.update_excluded_for_frame(frame_index, excluded_cells)

    def save_subapertures_for_all_frames(self, excluded_cells: list):
        """Применяет список исключённых ячеек ко всем кадрам файла (быстро)."""
        excluded_set = set(excluded_cells)
        self._storage.update_excluded_for_all_frames(self._file_id, excluded_set)
        print(f"Применены исключения ко всем {self._total} кадрам")
    
    # def save_subapertures_for_all_frames(self, excluded_cells: list):
    #     """
    #     Нарезает и сохраняет субапертуры для всех кадров файла,
    #     используя единый шаблон исключённых ячеек (excluded_cells).
    #     """
    #     total = self._total
    #     # Папка для архивов (создаётся один раз)
    #     if not hasattr(self, '_npy_dir'):
    #         self._npy_dir = os.path.join(self._storage.base_dir, f"file_{self._file_id}")
    #         os.makedirs(self._npy_dir, exist_ok=True)

    #     excluded_set = set(excluded_cells)

    #     for frame_idx in range(total):
    #         img = self._reader.get_image(frame_idx)
    #         valid_set = self.validator.determine_valid_cells(img)
    #         target = [(col, row) for (col, row) in valid_set if (col, row) not in excluded_set]
    #         if not target:
    #             continue

    #         frame_id = self._storage.get_frame_id(self._file_id, frame_idx)
    #         sub_arrays, meta_data = self._prepare_frame_archive_data(img, target)

    #         # Сохраняем архив через storage
    #         archive_path = os.path.join(self._npy_dir, f"frame_{frame_idx}.npz")
    #         self._storage.save_frame_archive(frame_id, archive_path, sub_arrays, meta_data)

    #         # Обновляем is_valid и excluded в subapertures (file_path не меняем)
    #         self._storage.update_cells_status(frame_id, valid_set, excluded_set)
    #         print(f"Кадр {frame_idx}: сохранено {len(target)} субапертур в архив {archive_path}")
 
    
    # def save_subapertures_for_frame(self, frame_index: int, excluded_cells: list):
    #     img = self._reader.get_image(frame_index)
    #     valid_set = self.validator.determine_valid_cells(img)
    #     excluded_set = set(excluded_cells)
    #     target = [(col, row) for (col, row) in valid_set if (col, row) not in excluded_set]
    #     if not target:
    #         print("Нет ячеек для сохранения")
    #         return

    #     if not hasattr(self, '_npy_dir'):
    #         self._npy_dir = os.path.join(self._storage.base_dir, f"file_{self._file_id}")
    #         os.makedirs(self._npy_dir, exist_ok=True)

    #     sub_arrays, meta_data = self._prepare_frame_archive_data(img, target)

    #     frame_id = self._storage.get_frame_id(self._file_id, frame_index)
    #     archive_path = os.path.join(self._npy_dir, f"frame_{frame_index}.npz")
    #     self._storage.save_frame_archive(frame_id, archive_path, sub_arrays, meta_data)
    #     self._storage.update_cells_status(frame_id, valid_set, excluded_set)
    #     print(f"Кадр {frame_index}: сохранено {len(target)} субапертур в архив {archive_path}")
        
    def _prepare_frame_archive_data(self, img, target):
        """
        Принимает изображение кадра и список целевых ячеек (target).
        Возвращает:
            sub_arrays: список 2D массивов субапертур (порядок соответствует target)
            meta_data: список кортежей (col, row, x, y, w, h, excluded) для каждой ячейки
        """
        xs = self._contours['x']
        ys = self._contours['y']
        max_w = self._contours['max_width']
        max_h = self._contours['max_height']
        
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
            meta_data.append((col, row, x, y, w, h, 0))  # excluded для сохраняемой ячейки всегда 0
        return sub_arrays, meta_data
    # FIXME: сделать функцию которая будет определять формат файла и вызывать функцию
    
    def prepare_all_subapertures(self):
        """Запускает подготовку всех субапертур (однократную нарезку).
        Возвращает True, если подготовка запущена (создан поток), иначе False."""
        if not hasattr(self, '_npy_dir'):
            self._npy_dir = os.path.join(self._storage.base_dir, f"file_{self._file_id}")
            os.makedirs(self._npy_dir, exist_ok=True)
        
        # Быстрая проверка по флагу в БД
        if self._storage.is_file_prepared(self._file_id):
            print("Файл уже полностью подготовлен, подготовка не требуется.")
            print("Файл уже полностью подготовлен, подготовка не требуется.")
            return False   # <-- подготовка не запущена
        
        self.prepare_thread = PrepareThread(
            reader=self._reader,
            contours=self._contours,
            validator=self.validator,
            storage=self._storage,
            file_id=self._file_id,
            total_frames=self._total,
            output_dir=self._npy_dir,
            image_width=self._image_width,
            image_height=self._image_height
        )
        self.prepare_thread.progress.connect(self._on_prepare_progress)
        self.prepare_thread.finished.connect(self._on_prepare_finished)
        self.prepare_thread.error.connect(self._on_prepare_error)
        self.prepare_thread.start()
        return True

    def _on_prepare_progress(self, current, total):
        print(f"Подготовка: {current}/{total}")  # можно передавать сигнал в GUI

    def _on_prepare_finished(self):
        if self.prepare_thread is not None and self.prepare_thread.isFinished():
            self._cached_valid_masks = self.prepare_thread.valid_masks   # сохраняем маски
        self._storage.mark_file_prepared(self._file_id)
        print("Подготовка всех субапертур завершена")

    def _on_prepare_error(self, err):
        print(f"Ошибка при подготовке: {err}")

    def run_analysis(self, method_name="zernike_polynomials"):
            """Запускает C++ анализ после того, как подготовка завершена."""
            print("DEBUG: run_analysis вызван, db_path =", self._storage.db_path, "file_id =", self._file_id)
            if not hasattr(self, '_storage') or not self._storage.db_path:
                raise RuntimeError("Хранилище не инициализировано")
            self.analysis_thread = AnalysisThread(
                self._storage.db_path, self._file_id, method_name
                # self._storage.db_path, self._file_id, method_name
            )
            # Сигналы пробросим в App через сам Manager, либо Manager сам будет их emit'ить.
            # Рекомендуется, чтобы Manager имел свои сигналы (но для простоты можно подключить в App).
            # Пока реализуем через подключение в App, поэтому здесь просто сохраняем ссылку.
            # Для этого изменим метод run_analysis, чтобы он возвращал поток, а App сама подключалась.
            print("DEBUG: AnalysisThread (многопроцессный) создан")
            return self.analysis_thread
    
    def get_excluded_cells_for_frame(self, frame_index: int) -> list:
        """Возвращает список (col, row) исключённых ячеек для кадра из текущего файла."""
        if not hasattr(self, '_storage') or not self._storage.db_path:
            return []
        return self._storage.get_excluded_cells_for_frame(self._file_id, frame_index)
    
    def has_excluded_cells(self) -> bool:
        """Проверяет, сохранены ли исключённые ячейки для текущего файла."""
        if not hasattr(self, '_storage') or not self._storage.db_path:
            return False
        return self._storage.has_excluded_cells_for_file(self._file_id)
    
    def get_default_excluded_cells(self, frame_index: int) -> list:
        """Возвращает список (col, row) невалидных ячеек (is_valid=0) для указанного кадра."""
        if not hasattr(self, '_storage') or not self._storage.db_path:
            return []
        return self._storage.get_invalid_cells(self._file_id, frame_index)

    def reset_excluded_to_invalid(self):
        """Сбрасывает флаг excluded для всех кадров файла: excluded=1 только для невалидных (is_valid=0)."""
        self._storage.reset_excluded_to_invalid(self._file_id)