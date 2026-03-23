from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

class GridSettings(QWidget):
    def __init__(self, viewer, parent=None):
        super().__init__(parent)
        self.viewer = viewer
        
        # Фиксируем размер виджета с параметрами
        self.setFixedWidth(250)  # Можно поменять ширину по своему усмотрению
        # self.setFixedHeight(200)  # Можно поменять высоту по своему усмотрению

        layout = QFormLayout(self)
        

        # Поля ввода параметров
        self.cell_size_input = QSpinBox()

        # Ползунок для масштабирования изображения
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setMinimum(100)  # минимальный масштаб 10%
        self.zoom_slider.setMaximum(500)  # максимальный масштаб 500%
        self.zoom_slider.setSingleStep(100)
        self.zoom_slider.setValue(int(self.viewer.scale_factor * 100))  # начальное значение в процентах
        self.zoom_slider.valueChanged.connect(self.onZoomChange)

        # Добавляем элементы в форму
        
        layout.addRow("Масштаб (%):", self.zoom_slider)

    def onZoomChange(self, value):
        # Масштабируем изображение в диапазоне от 10% до 500%
        factor = value / 100.0
        self.viewer.scale_factor = factor
        self.viewer.update()