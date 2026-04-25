import os
import unittest
import numpy as np
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtWidgets import QApplication
from src.logic.format.pixmap import Pixmap

class TestJobPixmap(unittest.TestCase):

    # Метод для инициализации графического контекста
    @classmethod
    def setUpClass(cls):
        plugins_path = r"D:\проекты с гита\app-wave-front-metric\.venv\Lib\site-packages\PyQt5\Qt5\plugins"
        os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = plugins_path
        cls.app = QApplication([])

    # Метод для освобождения ресурсов
    @classmethod
    def tearDownClass(cls):
        cls.app.quit()
        # del os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"]
    
    def setUp(self):
        """Готовит тестовые данные"""
        self.__valid_grayscale_image = np.random.randint(0, 256, size=(100, 100), dtype=np.uint8)
        self.__invalid_dimensions_image = np.random.randint(0, 256, size=(100, 100, 3), dtype=np.uint8)
        self.__zero_size_image = np.zeros((0, 0), dtype=np.uint8)
        
    """Сами тесты""" 
        
    # --- Тест 1: Проверка валидных параметров для серого изображения ---
    def test_preparing_qimage_parameters_valid(self):
        params = Pixmap.preparing_qimage_parameters(self.__valid_grayscale_image)
        _ , width, height, byte_count, format_qimage = params
        
        self.assertEqual(width, 100)
        self.assertEqual(height, 100)
        self.assertEqual(byte_count, 100 * self.__valid_grayscale_image.itemsize)
        self.assertEqual(format_qimage, QImage.Format_Grayscale8)


    # --- Тест 2: Проверка ошибки для неподдерживаемых размерности массива ---
    def test_preparing_qimage_parameters_invalid_dimensions(self):
        with self.assertRaises(ValueError) as error_context:
            Pixmap.preparing_qimage_parameters(self.__invalid_dimensions_image)
        self.assertIn("Unsupported image format.", str(error_context.exception))


    # --- Тест 3: Проверка ошибки для пустого массива ---
    def test_preparing_qimage_parameters_zero_size(self):
        with self.assertRaises(ValueError) as error_context:
            Pixmap.preparing_qimage_parameters(self.__zero_size_image)
        self.assertIn("Empty array provided.", str(error_context.exception))


    # --- Тест 4: Проверка успешного преобразования в pixmap ---
    def test_ndarray_to_pixmap_valid(self):
        pixmap = Pixmap.ndarray_to_pixmap(self.__valid_grayscale_image)
        
        self.assertIsInstance(pixmap, QPixmap)
        self.assertFalse(pixmap.isNull())
        self.assertEqual(pixmap.width(), 100)
        self.assertEqual(pixmap.height(), 100)    