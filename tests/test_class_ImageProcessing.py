import unittest
import numpy as np
from src.logic.Image_processing import *
from src.logic.format.h5 import H5
import tempfile
from pathlib import Path
import shutil

class TestJobImageProcessing(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Подготовка тестовых данных"""
        cls.__image_processing = ImageProcessing()
        cls.__test_h5 = H5()
        cls.__temp_dir = tempfile.TemporaryDirectory() 
        cls.__path_temp_dir = Path(cls.__temp_dir.name)
        source_path = Path("data") / "sunspot1300.h5"
        destination_path = cls.__path_temp_dir / "sunspot1300.h5"
        if not source_path.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")
        shutil.copy2(source_path, destination_path)
        if not destination_path.exists():
            raise FileNotFoundError(f"Destination file not copied: {destination_path}")
        date = cls.__test_h5.open_file(destination_path)
        cls.__test_image = date[0]

    
    """Сами тесты"""


    # --- Тест 1: Проверка успешного нахождение контуров субапертур и их высоты и ширины (не равно нулю)---
    def test_successful_contour_detection(self):
        result = self.__image_processing.search_contours(self.__test_image)
        self.assertGreater(len(result['x']), 0, "Количество точек по оси X равно нулю")
        self.assertGreater(len(result['y']), 0, "Количество точек по оси Y равно нулю")
        self.assertNotEqual(result['max_width'], 0, "Максимальная ширина равна нулю")
        self.assertNotEqual(result['max_height'], 0, "Максимальная высота равна нулю") 
    
    
    # --- Тест 2: Проверка уникальности элементов по x и y ---
    def test_unique_elements(self):
        result = self.__image_processing.search_contours(self.__test_image)
        self.assertEqual(len(result['y']), len(set(result['y'])), "Координаты Y не уникальны")
        self.assertEqual(len(result['x']), len(set(result['x'])), "Координаты X не уникальны")
        
        
    # --- Тест 3: Проверка на выход за границы по x и y ---    
    def test_exit_behind_border(self):
        result = self.__image_processing.search_contours(self.__test_image)
        shape_img = self.__test_image.shape
        self.assertLessEqual(result['y'][-1], shape_img[0], "Координаты Y выходят за границу высоты изображения")
        self.assertLessEqual(result['x'][-1], shape_img[1], "Координаты X выходят за границу ширины изображения")
        
        
    # --- Тест 4: Проверка на ошибку при подаче на вход пустого изображения ---
    def test_empty_image(self):
        with self.assertRaises(ImageError) as error_context:
            self.__image_processing.search_contours(np.zeros((0, 0), dtype=np.uint8))
        self.assertIn("Input image is empty.", str(error_context.exception))
        
    
    # --- Тест 5: Проверка на подачу на вход пустых параметров функции проверки границ ---
    def test_empty_parameters(self):
        with self.assertRaises(CoordinateError) as error_context:
            self.__image_processing.check_borders([], 480, 33)
        self.assertIn("The list of coordinates (x or y) cannot be empty.", str(error_context.exception))
        
        result = self.__image_processing.search_contours(self.__test_image)
        with self.assertRaises(SizeError) as error_context:
            self.__image_processing.check_borders(result['x'], 0, 33)
        self.assertIn("The size (height or width) of the image must be greater than zero.", str(error_context.exception))
        
        with self.assertRaises(SizeError) as error_context:
            self.__image_processing.check_borders(result['x'], 480, 0)
        self.assertIn("The size of the subaperture must be greater than zero", str(error_context.exception))
        
    
    # --- Тест 6: Проверка на обработку пустых списков кординат в функции simplification_contours
    def test_empty_coordinate_lists(self):
        with self.assertRaises(CoordinateError) as error_context:
            self.__image_processing.simplification_contours([], [])
        self.assertIn("Coordinate lists (x or y) cannot be empty.", str(error_context.exception))