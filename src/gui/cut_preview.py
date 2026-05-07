import sys
import matplotlib.pyplot as plt
import numpy as np
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QPushButton
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class SubapertureCutPreview(QDialog):
    def __init__(self, original_image, selected_rects, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Вырезанные субапертуры")
        self.resize(800, 600)
        
        layout = QVBoxLayout(self)
        
        # Кнопка закрытия
        btn_close = QPushButton("Закрыть")
        btn_close.clicked.connect(self.accept)
        
        # Matplotlib figure
        self.figure = Figure(figsize=(6, 4))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        layout.addWidget(btn_close)
        
        # Отрисовка
        self.draw_preview(original_image, selected_rects)
    
    def draw_preview(self, image, rects):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.imshow(image, cmap='gray')
        for rect in rects:
            x, y, w, h = rect['x'], rect['y'], rect['w'], rect['h']
            # Рисуем прямоугольник
            rect_patch = plt.Rectangle((x, y), w, h, linewidth=2, edgecolor='r', facecolor='none')
            ax.add_patch(rect_patch)
            # Подпись с индексами
            ax.text(x + w//2, y + h//2, f"({rect['row']},{rect['col']})",
                    color='yellow', fontsize=8, ha='center', va='center')
        ax.set_title(f"Всего выбранных субапертур: {len(rects)}")
        self.canvas.draw()