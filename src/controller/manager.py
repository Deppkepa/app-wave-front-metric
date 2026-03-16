# ⁡⁢⁢⁢INFO⁡⁡: пока временный класс который будет управлять всеми классами
import h5py
from pathlib import Path
from src.logic.format.h5 import h5
import numpy as np
from src.logic.Image_processing import image_processing
from src.logic.format.pixmap import pixmap


class manager():

    # INFO: Output: Готовые модели, Input: имя файла
    # INFO: Активизация преобразования данных из файла в модели
    def process_date(self, name_file:str):
        return image_processing.start(name_file)
    
    def start(self, name_file:str):
        images = h5.open_file(name_file)
        result = []
        for image in images:
            result.append(pixmap.ndarray_to_pixmap(image))
        return result
    
    
    



    # FIXME: сделать функцию которая будет определять формат файла и вызывать функцию

    
    

   
         