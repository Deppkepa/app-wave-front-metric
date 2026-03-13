# Модель субапертуры - маленькое изображение на большом
import numpy as np

class model_subaperture():
    __num_grid: int = 0 # номер субапертуры в сетке на изображении
    __subaperture: np.ndarray = None # массив субапертуры
    __schematic_contour: tuple = () # (x, y, width, height)
    
    # __size: tuple = () # размеры субапертуры
    # __selected_analysis: bool = False # флаг что пользователь выбрал эту субапертуру для анализа
    # __centroid: float = 0.0

    @property
    def num_grid(self) -> int:
        return self.__num_grid
    
    @num_grid.setter
    def num_grid(self, value:int):
        self.__num_grid = value

    @property
    def subaperture(self) -> np.ndarray:
        return self.__subaperture
    
    @subaperture.setter
    def subaperture(self, value:np.ndarray):
        self.__subaperture = value

    @property
    def schematic_contour(self) -> tuple:
        return self.__schematic_contour
    
    @schematic_contour.setter
    def schematic_contour(self, value:tuple):
        self.__schematic_contour = value

    
    def create(self, num_grid:int, subaperture:np.ndarray, schematic_contour:tuple):
        item = model_subaperture()
        item.num_grid = num_grid
        item.subaperture = subaperture
        item.schematic_contour = schematic_contour
        return item
        