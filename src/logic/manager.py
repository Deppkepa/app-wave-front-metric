# ⁡⁢⁢⁢INFO⁡⁡: пока временный класс который будет управлять всеми классами
import h5py
from pathlib import Path
from src.logic.format.h5 import h5
import numpy as np
from src.logic.Image_processing import image_processing

class manager():

    # FIXME: Функцию перенести в класс read_format_h5 а тут сделать функцию которая будет определять формат файла и вызывать функцию
    # ⁡⁢⁢⁢INFO⁡⁡⁡: Открывает файл и выдает массив с данными из файла
    def read_file(name_file: str):
        abs_path = Path(name_file).resolve()
        path_file = abs_path if abs_path.is_file() else abs_path.parent.joinpath('data', name_file)
        return h5.open_file(path_file)

    def image_in_subaperture(images:np):
        box = image_processing.split_image(images)
         