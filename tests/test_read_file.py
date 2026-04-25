import unittest
from src.controller.manager import Manager
import matplotlib.pyplot as plt
from src.logic.format.h5 import H5
from src.logic.model.model_subaperture import ModelSubaperture
from src.logic.Image_processing import ImageProcessing

class TestJobFile(unittest.TestCase):
    __test_manager = Manager()
    # ⁡⁢⁢⁢INFO⁡: тест направлен на открытие файла формата h5
    def test_read_file(self):
        # TODO: Провести проверки на неправильный путь в функцию
        # TODO: Реализовать отдельный файл с обработчиком ошибок и Log
        name_file = "data\sunspot1300.h5"   
        result = H5.open_file(name_file)
        assert len(result.shape) != 0

    #  INFO: тест направлен на проверку разбивки изображения на субапертур
    def test_image_in_subaperture(self):
        name_file = "data\sunspot1300.h5"
        images = self.__test_manager.process_date(name_file)
        assert len(images) == 6400
        assert len(images[0].subapertures) != None
        assert type(images[0].subapertures[0]) == ModelSubaperture
        
    # FIXME: написать побольше тестов которые протестируют функционал 
    # 
    def test_manual_mode(self):
        name_file = "data\sunspot1300.h5"
        images = self.__test_manager.start(name_file)

    def test_search_contours(self):
        name_file = "data\sunspot1300.h5"
        images = H5().open_file(name_file)
        ImageProcessing.search_contours(images[0])
        # print(ImageProcessing.search_contours(images[0]))

if __name__ == "__main__": 
    unittest.main() 
        

