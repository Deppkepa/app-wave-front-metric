# модель изображения с субапертур
from src.logic.model.model_subaperture import model_subaperture


class model_image():
    __subapertures: list = []
    __count: int = 0

    @property
    def subapertures(self) -> list:
        return self.__subapertures
    

    # TODO: Сделать класс валидатор который будет проверять правильность записи типов и т.д.
    @subapertures.setter
    def subapertures(self, subaperture: model_subaperture):
        self.__subapertures.append(subaperture)