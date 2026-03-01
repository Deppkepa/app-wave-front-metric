# чтение файлов формата h5
import h5py 
import matplotlib.pyplot as plt
from src.logic.model.model_image import model_image

class read_format_h5():
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
            # Доступ к набору данных 'data'
            data = f['data']
            
            # TODO: записать размер изображений в модель

            # Формируем вывод о размерах данных
            shape = data.shape
            return f"Размер данных: {shape}"  # Должно показать (6400, 480, 640)
            
            # TODO: функция которая на вход берет изображение разбивает на субапертуры 

            # Поскольку данные трёхмерные, берем первую картинку (первый срез)
            # first_image = data[0, :, :]  # Берём нулевое изображение
            
            
            # TODO: для проверки вывести картинку субапертуры
