import os
import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal
from src.logic.Image_processing import ImageProcessing
from src.logic.subap_validator import SubapValidator

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

    def run(self):
        try:
            self.output_dir = os.path.abspath(self.output_dir)
            num_cols = len(self.contours['x']) - 1
            num_rows = len(self.contours['y']) - 1
            for frame_idx in range(self.total):
                if self._cancel:
                    break
                if self.storage.is_frame_ready(self.file_id, frame_idx):
                    continue

                img = self.reader.get_image(frame_idx)
                if img.dtype == np.uint16:
                    img = (img / 256).astype(np.uint8)

                valid_set = self.validator.determine_valid_cells(img)
                mask = np.zeros((num_rows, num_cols), dtype=bool)
                for col, row in valid_set:
                    mask[row, col] = True
                self.valid_masks[frame_idx] = mask

                if not valid_set:
                    continue

                target = sorted(valid_set, key=lambda cell: (cell[1], cell[0]))
                sub_arrays, meta_data = self._prepare_frame_archive_data(img, target)

                frame_id = self.storage.get_or_create_frame(
                    self.file_id, frame_idx,
                    self.image_width, self.image_height,
                    num_rows, num_cols
                )
                archive_path = os.path.join(self.output_dir, f"frame_{frame_idx}.npz")
                archive_path = os.path.abspath(archive_path)
                self.storage.save_frame_archive(frame_id, archive_path, sub_arrays, meta_data)
                self.storage.update_cells_status(frame_id, valid_set, set())
                self.storage.exclude_invalid_cells(frame_id)
                self.progress.emit(frame_idx + 1, self.total)

            # Единственный finished после обработки всех кадров
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))
    