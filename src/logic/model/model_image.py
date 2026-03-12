# модель изображения с субапертур
from src.logic.model.model_subaperture import model_subaperture
import numpy as np

from src.logic.unique_entity import unique_entity


class model_image(unique_entity):
    __image: np.ndarray = None
    __subapertures: list = [] # FIXME: должны сохранятся объекта типа model_subaperture
    __count: int = 0
    __row_col: tuple = ()


    @property
    def image(self) -> np.ndarray:
        return self.__image

    @image.setter
    def image(self, image: np.ndarray):
        self.__image = image

    @property
    def subapertures(self) -> list:
        return self.__subapertures
    

    # TODO: Сделать класс валидатор который будет проверять правильность записи типов и т.д.
    @subapertures.setter
    def subapertures(self, subaperture: model_subaperture):
        self.__subapertures = subaperture

    @property
    def count(self) -> int:
        return self.__count

    @count.setter
    def count(self, count: np.ndarray):
        self.__count = count

    @property
    def row_col(self) -> tuple:
        return self.__row_col

    @row_col.setter
    def row_col(self, row_col:tuple):
        self.__row_col = row_col

    def create(self, image:np.ndarray, subaperture:list, row_col:tuple):
        item = model_image()
        item.image = image
        item.subapertures = subaperture
        item.count = len(subaperture)
        item.row_col = row_col
        return item
