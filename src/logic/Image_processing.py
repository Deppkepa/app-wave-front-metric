import numpy as np
import cv2
import matplotlib.pyplot as plt
from src.logic.format.h5 import h5
from src.logic.model.model_subaperture import model_subaperture
from src.logic.model.model_image import model_image
class image_processing:

    def start(name_file:str):
        # ⁡⁢⁢⁢INFO⁡⁡⁡: Открывает файл и выдает массив с данными из файла
        images = h5.open_file(name_file)
        collecting_model_img = []
        for image in images:
            # делаем картинку бинарной (картинка, светлые объекты=1, темные объекты=2)
            _, binary = cv2.threshold(image, 100, 255, cv2.THRESH_BINARY)
            # Ищем контуры субапертур(бинарное изображение, внешние точки, только угловые точки)
            contours, _ = cv2.findContours(binary.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            extracted_subapertures = image_processing.cut_subaperture(image, contours)
            # FIXME: Тут нужно уже преобразовывать в субапертуры а потом уже в список собирать эти субапертуры
            result_subaperture, index_table = image_processing.sequence_definition_sub(extracted_subapertures)
            collecting_model_sub = []
            for i in result_subaperture:    
                collecting_model_sub.append(model_subaperture().create(i['sequence_num'], i['subaperture'], i['schematic_contour']))
            collecting_model_img.append(model_image().create(image, collecting_model_sub, index_table))
        return collecting_model_img


    # Вырезает по заданным контурам субапертуры
    def cut_subaperture(image:np, contours:tuple):
        extracted_subapertures = []
        for contour in contours:
            # упрощаем контор до схематичного
            epsilon = 0.05 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)
            if len(approx) == 4:
                x, y, width, height = cv2.boundingRect(approx) # x, y - координаты верхнего левого угла              
                # FIXME: Нужно подумать над порогом проверки. Может использовать площадь или периметр для отсечения дефектов
                min_size = 20  # минимальный размер стороны квадрата
                max_aspect_ratio = 1.5  # максимальный коэффициент соотношения сторон
                if width >= min_size and height >= min_size and abs(width / height - 1) <= max_aspect_ratio:
                    extracted_subaperture = {
                        'subaperture': image[y:y + height, x:x + width],
                        'schematic_contour': (x, y, width, height),
                        'sequence_num': 0
                        }
                    extracted_subapertures.append(extracted_subaperture)            
        return extracted_subapertures   # Первичная обработка изображения для её разбивки на субапертуры
    

    def sequence_definition_sub(list_subaperture:list):
        #FIXME: Написать проверки на структуру данных
        # Сортируем субапертуры по вертикальной, затем по горизонтальной координате
        sorted_subapertures = sorted(
            list_subaperture,
            key=lambda s: (s['schematic_contour'][1], s['schematic_contour'][0])  # сначала y, затем x
        )
        count_row = 0
        count_col = 1
        memory = 0
        step = 0
        # Присваиваем уникальные номера в порядке сортировки
        for index, subaperture in enumerate(sorted_subapertures, start=1):
            subaperture['sequence_num'] = index
            if subaperture['schematic_contour'][1] - subaperture['schematic_contour'][1] < 5:
                step += 1
                if subaperture['schematic_contour'][1] != memory and subaperture['schematic_contour'][1] - memory > 5:
                    memory = subaperture['schematic_contour'][1]
                    count_col += 1
                    if step > count_row:
                        count_row = step
                    step = 0
        return sorted_subapertures, (count_col, count_row)