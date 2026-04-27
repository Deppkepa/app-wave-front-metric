from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import bisect

class GridOverImage(QLabel):
    """
    Виджет для отображения изображения с наложенной сеткой и возможностью клика по ячейкам.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.__pixmap = None  # Исходная картинка
        self._scaled_pixmap = None  # Кэш масштабированной картинки
        self._counts = {}  # Данные для сетки
        self._scale_factor = 1.0
        self.__click_history = [] # Защищаем список от внешнего изменения
        
    # --- Свойства ---
    @property
    def click_history(self):
        """Возвращает копию истории кликов для защиты данных."""
        return self.__click_history.copy()

    # @property
    # def last_click_point(self):
    #     """Возвращает координаты последнего клика или None."""
    #     return self.__click_history[-1] if self.__click_history else None

    @property
    def scale_factor(self):
        return self._scale_factor

    @scale_factor.setter
    def scale_factor(self, value):
        """Устанавливает масштаб и обновляет кэш изображения."""
        self._scale_factor = max(value, 0.1)
        self._scaled_pixmap = None # Сбрасываем кэш при изменении масштаба
        self.updateGeometry()   # <-- добавьте эту строку
        self.update()


    # --- Методы взаимодействия ---
    def set_pixmap_and_draw_grid(self, pixmap, counts):
        """
        Устанавливает новое изображение и данные сетки.
        :param pixmap: QPixmap с изображением.
        :param counts: Словарь с координатами сетки (x, y) и размерами.
        """
        self.__pixmap = pixmap
        self._counts = counts
        self._scaled_pixmap = None # Сбрасываем кэш при смене картинки
        self.update()

    # --- Обработка событий ---
    def mousePressEvent(self, event):
        if not self.__pixmap:
            return
        if event.button() == Qt.LeftButton:
            # ... существующая логика клика по сетке ...
            # (код, который вычисляет x_idx, y_idx и добавляет клик в историю)
            self.update()
            click_pos = event.pos()
        
            # Переводим координаты клика в координаты исходного изображения
            original_x = int(click_pos.x() / self.scale_factor)
            original_y = int(click_pos.y() / self.scale_factor)
            
            x_idx = bisect.bisect_right(self._counts['x'], original_x) - 1
            y_idx = bisect.bisect_right(self._counts['y'], original_y) - 1

            if (0 <= x_idx < len(self._counts['x']) - 1 and 
                0 <= y_idx < len(self._counts['y']) - 1):
                self.__click_history.append((x_idx, y_idx))
                self.update()
        else:
            super().mousePressEvent(event)

    # --- Отрисовка ---
    def paintEvent(self, event):
        painter = QPainter(self)
        
        if not self.__pixmap or not self._counts:
            painter.drawText(self.rect(), Qt.AlignCenter, "Загрузите изображение")
            return

        # Получаем размеры с учетом масштаба (кэшируем результат)
        w = int(self.__pixmap.width() * self.scale_factor)
        h = int(self.__pixmap.height() * self.scale_factor)
        
        # Отрисовка изображения (с кэшированием)
        if not self._scaled_pixmap or \
           (self._scaled_pixmap.width() != w or self._scaled_pixmap.height() != h):
            self._scaled_pixmap = self.__pixmap.scaled(w, h)
            
        painter.drawPixmap(0, 0, self._scaled_pixmap)
        
        # Настройка пера для сетки
        pen = QPen(Qt.darkGreen, 2, Qt.SolidLine)
        painter.setPen(pen)
        
        # Отрисовка основной сетки (вынесена в метод для чистоты)
        self._draw_main_grid(painter, w, h)
        
        # Отрисовка выделенных ячеек по клику (вынесена в метод)
        self._draw_clicked_cells(painter)

    def _draw_main_grid(self, painter, w, h):
        """Внутренний метод для отрисовки основной сетки."""
        for x in self._counts['x']:
            for y in self._counts['y']:
                scaled_x = int(x * self.scale_factor)
                scaled_y = int(y * self.scale_factor)
                
                if scaled_y >= h or scaled_x >= w:
                    continue

                width_sub = self._get_cell_width(x)
                height_sub = self._get_cell_height(y)
                
                rect = QRect(scaled_x, scaled_y,
                            int(width_sub * self.scale_factor),
                            int(height_sub * self.scale_factor))
                painter.drawRect(rect)

    def _draw_clicked_cells(self, painter):
        """Внутренний метод для отрисовки квадратов по клику."""
        pen_points = QPen(Qt.red, 2, Qt.SolidLine)
        painter.setPen(pen_points)
        
        for x_idx, y_idx in self.click_history:
            rect = self._get_cell_rect(x_idx, y_idx)
            if rect is None:
                continue

            # Проверка выхода за границы виджета (оптимизировано)
            if rect.bottom() > painter.device().height() or rect.right() > painter.device().width():
                continue

            painter.drawRect(rect)

    # --- Вспомогательные методы для расчета геометрии ---
    def _get_cell_width(self, x_coord):
        """Возвращает ширину ячейки для координаты X."""
        if x_coord == self._counts['x'][0]:
            return self._counts['x'][1] - x_coord - 5
        return self._counts['max_width']

    def _get_cell_height(self, y_coord):
        """Возвращает высоту ячейки для координаты Y."""
        if y_coord == self._counts['y'][0]:
            return self._counts['y'][1] - y_coord - 5
        return self._counts['max_height']
    
    # В классе GridOverImage добавьте:
    def original_size_hint(self):
        if self.__pixmap:
            return QSize(self.__pixmap.width(), self.__pixmap.height())
        return QSize(400, 300)

    def sizeHint(self):
        if self.__pixmap:
            w = int(self.__pixmap.width() * self.scale_factor)
            h = int(self.__pixmap.height() * self.scale_factor)
            return QSize(w, h)
        return QSize(400, 300)
    
    def _get_cell_rect(self, x_idx, y_idx):
        """
        Возвращает QRect для ячейки по индексам.
        Учитывает границы и условия "слишком близко к краю".
        """
        try:
            x0 = self._counts['x'][x_idx]
            x1 = self._counts['x'][x_idx + 1]
            y0 = self._counts['y'][y_idx]
            
            width_sub = self._get_cell_width(x0)
            height_sub = self._get_cell_height(y0)
            
            x0s = int(x0 * self.scale_factor)
            y0s = int(y0 * self.scale_factor)
            
            # Проверка правой границы (последний столбец)
            if x1 == self._counts['x'][-1]:
                widget_width = int(self.width())
                if widget_width - x0s - int(5 * self.scale_factor) <= int(15 * self.scale_factor):
                    return None

            return QRect(x0s, y0s,
                        int(width_sub * self.scale_factor),
                        int(height_sub * self.scale_factor))
                        
        except IndexError:
            return None
