import numpy as np
import cv2
import matplotlib.pyplot as plt
from src.logic.model.model_subaperture import model_subaperture

class image_processing:

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
                
                # Пропускаем слишком маленькие фигуры (можно настроить фильтр размеров)
                min_size = 20  # минимальный размер стороны квадрата
                max_aspect_ratio = 1.5  # максимальный коэффициент соотношения сторон
                if width >= min_size and height >= min_size and abs(width / height - 1) <= max_aspect_ratio:
                    extracted_subaperture = image[y:y + height, x:x + width]
                    extracted_subapertures.append(extracted_subaperture)
        return extracted_subapertures

    # Первичная обработка изображения для её разбивки на субапертуры
    def split_image(images:np):
        for image in images:
            # делаем картинку бинарной (картинка, светлые объекты=1, темные объекты=2)
            _, binary = cv2.threshold(image, 100, 255, cv2.THRESH_BINARY)
            # Ищем контуры субапертур(бинарное изображение, внешние точки, только угловые точки)
            contours, _ = cv2.findContours(binary.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            result = image_processing.cut_subaperture(image, contours)
            # FIXME: Тут нужно уже преобразовывать в субапертуры а потом уже в список собирать эти субапертуры
            


            
            # for index, square in enumerate(, start=1):
                
            #     plt.figure(figsize=(4, 4))
            #     plt.title(f"Квадрат №{index}")
            #     plt.imshow(square)  # Конвертируем обратно в RGB для matplotlib
            #     plt.axis('off')
            #     plt.show()
            #     # if index == 32:
            #     #     break
            #     break
            break


    