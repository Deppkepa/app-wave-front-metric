# чтение файлов формата h5
import h5py 
import matplotlib.pyplot as plt
from src.logic.model.model_image import model_image

class h5():
    # __path_file: str = ""

    # @property
    # def path_file(self) -> str:
    #     return self.__path_file
    

    # # TODO: Сделать класс валидатор который будет проверять правильность записи типов и т.д.
    # @path_file.setter
    # def path_file(self, path: str):
    #     self.__path_file = path

    def open_file(path_file: str):
        with h5py.File(path_file, 'r') as f:
            # FIXME: исправить прямое обращение к ключу
            
            data = f['data'][:]
            
            
            image_count = data.shape[0]
            frame_size = data.shape[1:]
            # ⁡⁣⁢⁢IDEA⁡: Сделать выводом функции массив с данными из файла

            # return f"Количество изображений в файле: {image_count}. \nРазмер субапертур: {frame_size}"
            return data
            # TODO: записать размер изображений в модель

            # TODO: функция которая на вход берет изображение разбивает на субапертуры 

            # TODO: для проверки вывести картинку субапертуры
