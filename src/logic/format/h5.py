# Главная задача чтение данных из файлов формата h5
import h5py 
import matplotlib.pyplot as plt
from src.logic.model.model_image import model_image
from pathlib import Path

class h5():
    # TODO: Сделать класс валидатор который будет проверять правильность записи типов и т.д.

    def open_file(name_file: str):
        abs_path = Path(name_file).resolve()
        path_file = abs_path if abs_path.is_file() else abs_path.parent.joinpath('data', name_file)
        with h5py.File(path_file, 'r') as f:
            # FIXME: исправить прямое обращение к ключу
            data = f['data'][:]
            # ⁡⁣⁢⁢IDEA⁡: Сделать выводом функции массив с данными из файла
            return data
            # FIXME: закрыть файл
            # TODO: записать размер изображений в модель

            # TODO: функция которая на вход берет изображение разбивает на субапертуры 

            # TODO: для проверки вывести картинку субапертуры
