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

class Manager:
    def __init__(self, cache_size=10):
        self._reader = None
        self._compressed_images = []   # список QByteArray (JPEG)
        self._contours = None
        self._cache = OrderedDict()    # index -> QPixmap
        self._cache_size = cache_size
        self._cache_mutex = QMutex()
        self._total = 0

    def open_file(self, file_path: str, progress_callback=None) -> int:
        """Открывает HDF5, сжимает все кадры в JPEG и хранит в памяти."""
        self._reader = H5LazyReader(file_path)
        self._total = self._reader.num_images

        # Контуры вычисляем один раз на первом кадре (полноразмерном)
        first_img = self._reader.get_image(0)
        self._contours = ImageProcessing.search_contours(first_img)

        # Сжимаем все кадры в JPEG и сохраняем в список
        self._compressed_images = []
        for i in range(self._total):
            if progress_callback and i % 10 == 0:  # не вызываем на каждом кадре, чтобы не перегружать
                progress_callback(i + 1, self._total)
                print(progress_callback)
            img = self._reader.get_image(i)
            # Приводим к 8-бит (если uint16 -> /256)
            if img.dtype == np.uint16:
                img = (img / 256).astype(np.uint8)
            elif img.dtype != np.uint8:
                img = img.astype(np.uint8)

            # Конвертируем numpy в QImage
            h, w = img.shape
            qimg = QImage(img.data, w, h, w, QImage.Format_Grayscale8)
            # Сжимаем в JPEG в QByteArray
            buffer = QBuffer()
            buffer.open(QBuffer.WriteOnly)
            qimg.save(buffer, "JPEG", quality=85)   # качество 85
            compressed_data = buffer.data()
            buffer.close()
            self._compressed_images.append(compressed_data)

        # Закрываем читатель (данные уже все в памяти в сжатом виде)
        self._reader.close()
        self._reader = None
        return self._total

    def get_pixmap(self, index: int) -> QPixmap:
        """Возвращает QPixmap для индекса (используя кэш)."""
        if index < 0 or index >= self._total:
            raise IndexError

        # Проверяем кэш
        with QMutexLocker(self._cache_mutex):
            if index in self._cache:
                self._cache.move_to_end(index)
                return self._cache[index]

        # Нет в кэше: декодируем JPEG
        compressed = self._compressed_images[index]
        pixmap = QPixmap()
        if not pixmap.loadFromData(compressed, "JPEG"):
            raise RuntimeError(f"Failed to decode JPEG for index {index}")

        # Помещаем в кэш
        with QMutexLocker(self._cache_mutex):
            self._cache[index] = pixmap
            if len(self._cache) > self._cache_size:
                self._cache.popitem(last=False)
        return pixmap

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


    



    # FIXME: сделать функцию которая будет определять формат файла и вызывать функцию

    
    

   
         