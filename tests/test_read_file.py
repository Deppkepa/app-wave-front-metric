import unittest
from src.logic.manager import manager
import matplotlib.pyplot as plt
import cv2
from PIL import Image
import numpy as np
from skimage.filters import threshold_otsu
from src.logic.Image_processing import image_processing

class TestJobFile(unittest.TestCase):
    __test_manager = manager
    # ⁡⁢⁢⁢INFO⁡: тест направлен на открытие файла формата h5
    def test_read_file(self):
        # TODO: Провести проверки на неправильный путь в функцию
        # TODO: Реализовать отдельный файл с обработчиком ошибок и Log
        name_file = "data\sunspot1300.h5"   
        result = self.__test_manager.read_file(name_file)
        assert len(result.shape) != 0

    #  INFO: тест направлен на проверку разбивки изображения на субапертур
    def test_image_in_subaperture(self):
        name_file = "data\sunspot1300.h5"
        images = self.__test_manager.read_file(name_file)
        result = self.__test_manager.image_in_subaperture(images)
        # result = image_processing.split_image(result)
        

if __name__ == "__main__": 
    unittest.main() 
        

