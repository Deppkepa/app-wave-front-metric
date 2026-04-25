# ⁡⁢⁢⁢INFO⁡⁡: пока временный класс который будет управлять всеми классами
from src.logic.format.h5 import H5
import numpy as np
from src.logic.Image_processing import ImageProcessing
from src.logic.format.pixmap import Pixmap


class Manager():
    # INFO: Output: Готовые модели, Input: имя файла
    # INFO: Активизация преобразования данных из файла в модели
    def process_date(self, name_file:str): # не пользуется
        return ImageProcessing.start(name_file)
    
    def start(self, name_file:str):
        images = H5().open_file(name_file)
        contours = ImageProcessing.search_contours(images[0])
        result = []
        for image in images:
            result.append(Pixmap.ndarray_to_pixmap(image))
        return result, contours
    


    



    # FIXME: сделать функцию которая будет определять формат файла и вызывать функцию

    
    

   
         