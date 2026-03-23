import numpy as np
import cv2
import matplotlib.pyplot as plt
from src.logic.format.h5 import h5
from src.logic.model.model_subaperture import model_subaperture
from src.logic.model.model_image import model_image
class image_processing:


    def search_contours(image):
        # делаем картинку бинарной (картинка, светлые объекты=1, темные объекты=2)
        _, binary = cv2.threshold(image, 100, 255, cv2.THRESH_BINARY)
        # Ищем контуры субапертур(бинарное изображение, внешние точки, только угловые точки)
        contours, _ = cv2.findContours(binary.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        # extracted_subapertures = image_processing.cut_subaperture(image, contours)
        # print(extracted_subapertures)
        coordinates_list = []  # Создаем пустой список для хранения координат
        point_x = []
        point_y = []
        width_list = []
        height_list = []
        for contour in contours:
            # Упрощаем контур до схематического представления
            epsilon = 0.05 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)
            
            if len(approx) == 4:
                x, y, width, height = cv2.boundingRect(approx)  # Получаем координаты и размеры рамки вокруг контура
                
                # Проверяем условия по размеру и пропорциям
                min_size = 20      # Минимальный размер стороны
                max_aspect_ratio = 1.5  # Максимальное соотношение сторон
                
                if width >= min_size and height >= min_size and abs(width / height - 1) <= max_aspect_ratio:
                    # Если условие выполнено, добавляем координаты и размеры в итоговый список
                    point_x.append(x)
                    point_y.append(y)

                    width_list.append(width)
                    height_list.append(height)
                    
        
        
        point_x = list(set(point_x))
        sorted_numbers = sorted(point_x)
        result_rows = [sorted_numbers[0]] 
        for number in sorted_numbers[1:]:
            if abs(number - result_rows[-1]) > 5:  # Если разница с последним элементом результата больше 5
                result_rows.append(number)
        
         
        

        point_y = list(set(point_y))
        sorted_num = sorted(point_y)
        result_cols = [sorted_num[0]] 
        for number in sorted_num[1:]:
            if abs(number - result_cols[-1]) > 5:  # Если разница с последним элементом результата больше 5
                result_cols.append(number)
        # box_1 = image_processing.check_borders(result_rows, image.shape[0], max(width_list))
        # box_2 = 
        
        result_points = {'x': image_processing.check_borders(result_rows, image.shape[1], max(width_list)),
                         'y': image_processing.check_borders(result_cols, image.shape[0], max(height_list)),
                         'max_width': max(width_list),
                         'max_height': max(height_list)}
        return result_points
        
    def check_borders(count_list, size_image, max_size_sub):
        
        while abs(count_list[-1] - size_image) >= max_size_sub:
            count_list.append(count_list[-1] + max_size_sub)
        
        while count_list[0] // 2 > max_size_sub:
                count_list.insert(0, count_list[0] - max_size_sub - 3)
        if count_list[0] != 0:
            count_list.insert(0, 0)
            
            
        return count_list

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
        # count_element = []
        # Присваиваем уникальные номера в порядке сортировки
        for index, subaperture in enumerate(sorted_subapertures, start=1):
            subaperture['sequence_num'] = index
            # print(subaperture['schematic_contour'])
            if subaperture['schematic_contour'][1] - subaperture['schematic_contour'][1] < 5:
                step += 1
                if subaperture['schematic_contour'][1] != memory and subaperture['schematic_contour'][1] - memory > 5:
                    memory = subaperture['schematic_contour'][1]
                    # count_element.append(step - 1)
                    count_col += 1

                    # print(count_col, step)
                    if step > count_row:
                        count_row = step
                    step = 0
            
        return sorted_subapertures, (count_col, count_row)