# src/gui/GridSubapertureView.py
from PyQt5.QtWidgets import QGraphicsScene, QGraphicsView, QGraphicsPixmapItem, QMainWindow
from PyQt5.QtGui import QPixmap, QImage
import numpy as np

class GridSubapertureView(QMainWindow):

    # Статический метод для создания сцены с восстановленным изображением
    @staticmethod
    def create_view(subapertures, scene_size):
        # Создаем сцену и виджет просмотра
        scene = QGraphicsScene()
        
        view = QGraphicsView(scene)
        # view.setStyleSheet("background-color: red;")
        
        # Загружаем и располагаем фрагменты на сцене
        for subaperture in subapertures:
            # Получаем координаты и размеры из модели
            x, y, w, h = subaperture.schematic_contour
            
            # Преобразуем массив NumPy в QPixmap
            pixmap = GridSubapertureView.nparray_to_pixmap(subaperture.subaperture)
            
            # Создаем графический элемент для фрагмента
            fragment_item = QGraphicsPixmapItem(pixmap)
            
            # Устанавливаем позицию фрагмента на сцене
            fragment_item.setPos(x, y)
            
            # Добавляем элемент на сцену
            scene.addItem(fragment_item)
        
        # Настраиваем размеры сцены
        scene.setSceneRect(0, 0, scene_size[0], scene_size[1])
        
        # Создаем окно для отображения
        window = QMainWindow()
        window.setCentralWidget(view)
        window.setWindowTitle("Восстановленное изображение")
        window.resize(scene_size[0], scene_size[1])
        
        return window

    # Вспомогательная функция для преобразования NumPy в QPixmap
    @staticmethod
    def nparray_to_pixmap(arr):
        """
        Преобразует NumPy array в QPixmap.
        """
        # Получаем высоту и ширину изображения
        height, width = arr.shape[:2]
        
        # Определяем формат изображения
        if arr.ndim == 2:  # Монохромное (чёрно-белое) изображение
            format_qimage = QImage.Format_Grayscale8
            byte_count = width * arr.itemsize
        elif arr.ndim == 3 and arr.shape[-1] == 3:  # RGB изображение
            format_qimage = QImage.Format_RGB888
            byte_count = width * arr.itemsize * 3
        elif arr.ndim == 3 and arr.shape[-1] == 4:  # RGBA изображение
            format_qimage = QImage.Format_RGBA8888
            byte_count = width * arr.itemsize * 4
        else:
            raise ValueError("Неподдерживаемый формат изображения.")

        # Получаем сырые байты изображения
        raw_bytes = arr.tobytes()

        # Создаем QImage из сырых байтов
        qimg = QImage(raw_bytes, width, height, byte_count, format_qimage)

        # Возвращаем QPixmap, созданный из QImage
        return QPixmap.fromImage(qimg)
