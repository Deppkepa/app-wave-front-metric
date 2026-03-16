# src/gui/GridSubapertureView.py
from PyQt5.QtWidgets import QGraphicsScene, QGraphicsView, QGraphicsPixmapItem, QWidget, QSlider, QStackedWidget, QVBoxLayout
from PyQt5.QtGui import QPixmap, QImage
import numpy as np
from PyQt5.QtCore import Qt


class GridSubapertureView(QWidget):


    @staticmethod
    def range_images(images):
        pass
        
    @staticmethod
    def create_view(images, scene_size):
        scenes = []
        for image in images:
            scene = QGraphicsScene()
            for subaperture in image.subapertures:
                x, y, _, _ = subaperture.schematic_contour
                pixmap = GridSubapertureView.ndarray_to_pixmap(subaperture.subaperture)
                fragment_item = QGraphicsPixmapItem(pixmap)
                fragment_item.setPos(x, y)
                scene.addItem(fragment_item)
            scenes.append(scene)
        
        # Создаем контейнер для стека и ползунка
        container = QWidget()
        layout = QVBoxLayout(container)
        
        # Виджет для переключения сцен
        stacked_widget = QStackedWidget()
        for scene in scenes:
            view = QGraphicsView(scene)
            stacked_widget.addWidget(view)
        
        # Ползунок для переключения между сценами
        slider = QSlider(Qt.Horizontal)
        slider.setRange(0, len(scenes) - 1)
        slider.valueChanged.connect(stacked_widget.setCurrentIndex)
        
        # Объединяем в одном макете
        layout.addWidget(stacked_widget)
        layout.addWidget(slider)
        
        return container
    
    # FIXME: убрать в будущем эту функцию (вынесена в класс)
    @staticmethod
    def ndarray_to_pixmap(arr):
        
        height, width = arr.shape[:2]
        if arr.ndim == 2:
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
        raw_bytes = arr.tobytes()
        qimg = QImage(raw_bytes, width, height, byte_count, format_qimage)
        return QPixmap.fromImage(qimg)
