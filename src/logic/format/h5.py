# Главная задача чтение данных из файлов формата h5
import h5py
from pathlib import Path


class H5ReaderError(Exception):
    """Базовый класс для всех ошибок, связанных с чтением HDF5 файлов этим модулем."""
    pass

class CountKeyError(H5ReaderError):
    """Ошибка, когда ключей больше одного."""
    pass

class FileAccessError(Exception):
    """Ошибка, связанная с доступом к файлу (нет прав, не найден)."""
    pass

class H5():
    __key:str = '' # ключ от данных
    __count_image:int = 0 # количество изображений
    __shape_image:tuple = () # Размеры изображения

    @property
    def key(self) -> str:
        return self.__key
    
    @key.setter
    def key(self, value: str):
        self.__key = value
        
        
    @property
    def count_image(self) -> int:
        return self.__count_image
    
    @count_image.setter
    def count_image(self, value: int):
        self.__count_image = value
    
    
    @property
    def shape_image(self) -> tuple:
        return self.__shape_image
    
    @shape_image.setter
    def shape_image(self, value: tuple):
        self.__shape_image = value
        
    
    # Проверка расположения файла по пути
    def check_file_exists(self, path_file: str):
        if not path_file.is_file():
            raise FileAccessError(f"The file was not found on the way: {path_file}")
    
    def open_file(self, name_file: str):
        input_path = Path(name_file).resolve()
        self.check_file_exists(input_path)
        
        # Сначала пробуем открыть файл (ошибки доступа)
        try:
            f = h5py.File(input_path, 'r')
        except OSError as e:
            raise H5ReaderError(f"Couldn't open the file {input_path}: {e}")

        # Если файл открылся успешно, работаем с ним в контексте менеджера
        with f:
            key_f = list(f.keys())
            if len(key_f) == 0:
                raise H5ReaderError("The file does not contain any keys (an empty file)")
            if len(key_f) > 1:
                raise CountKeyError(f"More than one key was found in the file: {key_f}. One key is expected.")  
            self.key = key_f[0]    
            # Валидация формы
            shape_f = f[self.key].shape
            if len(shape_f) == 3 and shape_f[0] > 0 and shape_f[1] > 0 and shape_f[2] > 0:
                self.count_image = shape_f[0]
                self.shape_image = shape_f[1:]
            else:
                raise H5ReaderError(f"Incorrect dimension of the data. Expected 3 axes (number of images, height, width), received {shape_f}.")
            data = f[self.key][:] # Вот здесь может возникнуть ошибка при чтении
            return data



        


            # FIXME: закрыть файл
            # TODO: записать размер изображений в модель
            # TODO: Сделать класс валидатор который будет проверять правильность записи типов и т.д.

            # TODO: функция которая на вход берет изображение разбивает на субапертуры 

            # TODO: для проверки вывести картинку субапертуры
