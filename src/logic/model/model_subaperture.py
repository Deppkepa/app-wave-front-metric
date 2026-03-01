# Модель субапертуры - маленькое изображение на большом
import numpy

class model_subaperture():
    __num_in_grid: int = 0 # номер субапертуры в сетке на изображении
    __frame: list = [] # массив субапертуры
    __size: tuple = () # размеры субапертуры
    __selected_analysis: bool = False # флаг что пользователь выбрал эту субапертуру для анализа
    __centroid: float = 0.0

    


    
