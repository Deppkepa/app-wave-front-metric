from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

class grid_over_image(QLabel):
    def __init__(self, parent=None):
        super(grid_over_image, self).__init__(parent)
        self.__pixmap = None
        self.__counts = {}
        self._cell_size = 10
        self._start_x = 0
        self._start_y = 0
        self._scale_factor = 1.0  # Начальный масштаб 100%
        self.__click_history = [] 


     # Свойство для получения истории кликов (защищаем от внешнего изменения списка)
    @property
    def click_history(self):
        return self.__click_history.copy()

    # Свойство для получения последней точки (или None)
    @property
    def last_click_point(self):
        if self.__click_history:
            return self.__click_history[-1]
        return None
    
    # Свойство scale_factor
    @property
    def scale_factor(self):
        return self._scale_factor

    @scale_factor.setter
    def scale_factor(self, value):
        self._scale_factor = max(value, 0.1)  # Минимальный масштаб 10% от исходного размера
        self.update()

    def setPixmapAndDrawGrid(self, value, counts):
        self.__pixmap = value
        self.__counts = counts
        self.update()  # Перерисовка

    # --- НОВОЕ: Обработчик клика мыши ---
    def mousePressEvent(self, event):
        # Проверяем, что изображение загружено и клик был левой кнопкой мыши
        if self.__pixmap is not None and event.button() == Qt.LeftButton:
            
            # Получаем координаты клика относительно верхнего левого угла виджета
            click_pos = event.pos()
            
            # Вычисляем координаты на ИСХОДНОМ изображении
            # Для этого делим координаты виджета на текущий коэффициент масштабирования
            original_x = int(click_pos.x() / self.scale_factor)
            original_y = int(click_pos.y() / self.scale_factor)
            
            # Сохраняем координаты в историю
            self.__click_history.append((original_x, original_y))
            
            # Принудительно перерисовываем виджет, чтобы отобразить изменения (например, новую точку)
            self.update()
            
            # Вызываем родительский метод (не обязательно, но хорошая практика)
            super().mousePressEvent(event)

    def paintEvent(self, event):
        if self.__pixmap is None or len(self.__counts) == 0:
            return 
        w = int(self.__pixmap.width() * self.scale_factor)
        h = int(self.__pixmap.height() * self.scale_factor)

        painter = QPainter(self)
        painter.drawPixmap(0, 0, self.__pixmap.scaled(w, h))

        pen = QPen(Qt.GlobalColor.darkGreen, 4, Qt.PenStyle.SolidLine)
        painter.setPen(pen)

        # Горизонтальная сетка
        for y in self.__counts['y']:
            scaled_y = int(y * self.scale_factor)
            painter.drawLine(0, scaled_y, w, scaled_y)

        # Вертикальная сетка
        for x in self.__counts['x']:
            scaled_x = int(x * self.scale_factor)
            painter.drawLine(scaled_x, 0, scaled_x, h)

        
        
        # --- НОВОЕ: Рисуем точки кликов ---
        pen_points = QPen(Qt.red, 3, Qt.PenStyle.SolidLine) # Толще и красным цветом
        painter.setPen(pen_points)
        
        for (x, y) in self.click_history:
            Xx = self.search_point(self.__counts['x'], x)
            Yy = self.search_point(self.__counts['y'], y)
            # Масштабируем координаты для отрисовки на экране
            scaled_points = [
                QPoint(int(Xx * self.scale_factor), int(Yy * self.scale_factor)),
                QPoint(int((Xx + 36) * self.scale_factor), int(Yy * self.scale_factor)),
                QPoint(int((Xx + 36) * self.scale_factor), int((Yy + 36) * self.scale_factor)),
                QPoint(int(Xx * self.scale_factor), int((Yy + 36) * self.scale_factor))
            ]
            
            # Рисуем квадрат по вершинам
            painter.drawPolygon(QPolygon(scaled_points))
            # # Масштабируем координаты сохраненной точки для отрисовки на экране
            # painter.drawPoint(int(x * self.scale_factor), int(y * self.scale_factor))
            


    def search_point(self, list_point, point):
        for index, value in enumerate(list_point):
            if value > point:
                return list_point[index - 1]
                
    def slice_image_by_grid(self):
        if self.__pixmap is None or len(self.__counts) == 0:
            return []

        slices = [] # Список для хранения нарезанных фрагментов

        # Перебираем все горизонтальные полосы (по Y)
        for i in range(len(self.__counts['y']) - 1):
            y_top = self.__counts['y'][i]
            y_bottom = self.__counts['y'][i + 1]
            height = y_bottom - y_top

            # Перебираем все вертикальные полосы (по X) внутри текущей горизонтальной полосы
            for j in range(len(self.__counts['x']) - 1):
                x_left = self.__counts['x'][j]
                x_right = self.__counts['x'][j + 1]
                width = x_right - x_left

                # Вырезаем фрагмент из исходного изображения (не масштабированного!)
                slice_pixmap = self.__pixmap.copy(x_left, y_top, width, height)
                
                # Сохраняем фрагмент в список (или сразу сохраняем на диск)
                slices.append(slice_pixmap)

        return slices    
