# ⁡⁢⁢⁢INFO⁡⁡: пока временный класс который будет управлять всеми классами
import h5py
from pathlib import Path
from src.logic.format.h5 import h5
import numpy as np
from src.logic.Image_processing import image_processing


class manager():

    # INFO: Output: Готовые модели, Input: имя файла
    # INFO: Активизация преобразования данных из файла в модели
    def process_date(name_file:str):
        return image_processing.start(name_file)
    
    
    



    # FIXME: сделать функцию которая будет определять формат файла и вызывать функцию

    
    

   
         