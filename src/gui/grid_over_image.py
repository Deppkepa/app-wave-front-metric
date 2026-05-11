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
        self.setMouseTracking(True)   # ← добавляем
        
        # Для прямоугольного выделения
        self._selecting = False
        self._select_start = QPoint()
        self._select_end = QPoint()
    # --- Свойства ---
    @property
    def click_history(self):
        """Возвращает копию истории кликов для защиты данных."""
        return self.__click_history.copy()


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
        # self.__click_history.clear()   # ОЧИЩАЕМ ИСТОРИЮ
        self._scaled_pixmap = None # Сбрасываем кэш при смене картинки
        self.update()

    # --- Обработка событий ---
    def mousePressEvent(self, event):
        if not self.__pixmap:
            return
        if event.button() == Qt.LeftButton:
            # # ... существующая логика клика по сетке ...
            # # (код, который вычисляет x_idx, y_idx и добавляет клик в историю)
            # self.update()
            # click_pos = event.pos()
        
            # # Переводим координаты клика в координаты исходного изображения
            # original_x = int(click_pos.x() / self.scale_factor)
            # original_y = int(click_pos.y() / self.scale_factor)
            
            # x_idx = bisect.bisect_right(self._counts['x'], original_x) - 1
            # y_idx = bisect.bisect_right(self._counts['y'], original_y) - 1

            # if (0 <= x_idx < len(self._counts['x']) - 1 and 
            #     0 <= y_idx < len(self._counts['y']) - 1):
            #     if (x_idx, y_idx) in self.__click_history:
            #         self.__click_history.remove((x_idx, y_idx))
            #     else:
            #         self.__click_history.append((x_idx, y_idx))
            #     self.update()
            self._selecting = True
            self._select_start = event.pos()
            self._select_end = event.pos()
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
        # Выделенные ячейки
        pen_points = QPen(Qt.red, 2, Qt.SolidLine)
        painter.setPen(pen_points)
        for x_idx, y_idx in self.click_history:
            rect = self._get_cell_rect(x_idx, y_idx)
            if rect:
                painter.drawRect(rect)

        # Прямоугольник текущего выделения
        if self._selecting:
            painter.setPen(QPen(Qt.blue, 1, Qt.DashLine))
            painter.drawRect(QRect(self._select_start, self._select_end).normalized())
        # # Отрисовка выделенных ячеек по клику (вынесена в метод)
        # self._draw_clicked_cells(painter)

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
        
    def get_excluded_cells(self):
        """Возвращает список (x_idx, y_idx) ячеек, которые пользователь отметил как исключённые."""
        return self.click_history  # click_history уже возвращает копию
    
    def mouseMoveEvent(self, event):
        # """Показывает подсказку с индексами ячейки под курсором."""
        # if not self.__pixmap or not self._counts:
        #     return
        # # Координаты курсора в исходном изображении
        # orig_x = int(event.pos().x() / self.scale_factor)
        # orig_y = int(event.pos().y() / self.scale_factor)
        # xs = self._counts.get('x', [])
        # ys = self._counts.get('y', [])
        # if len(xs) < 2 or len(ys) < 2:
        #     return
        # # Индексы ячейки
        # col = bisect.bisect_right(xs, orig_x) - 1
        # row = bisect.bisect_right(ys, orig_y) - 1
        # if 0 <= col < len(xs) - 1 and 0 <= row < len(ys) - 1:
        #     self.setToolTip(f"Col: {col}, Row: {row}")
        # else:
        #     self.setToolTip("")
        # super().mouseMoveEvent(event)
        if self._selecting:
            self._select_end = event.pos()
            self.update()
        else:
            # Подсказка с индексами
            if self.__pixmap and self._counts:
                orig_x = int(event.pos().x() / self.scale_factor)
                orig_y = int(event.pos().y() / self.scale_factor)
                xs = self._counts.get('x', [])
                ys = self._counts.get('y', [])
                if len(xs) > 1 and len(ys) > 1:
                    col = bisect.bisect_right(xs, orig_x) - 1
                    row = bisect.bisect_right(ys, orig_y) - 1
                    if 0 <= col < len(xs)-1 and 0 <= row < len(ys)-1:
                        self.setToolTip(f"Col: {col}, Row: {row}")
                    else:
                        self.setToolTip("")
            super().mouseMoveEvent(event)
        
    def leaveEvent(self, event):
        self.setToolTip("")
        super().leaveEvent(event)
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self._selecting:
            self._selecting = False
            rect = QRect(self._select_start, self._select_end).normalized()
            if rect.width() > 2 and rect.height() > 2:
                self._apply_rect_selection(rect)
            else:
                # Обрабатываем как одиночный клик
                self._single_click(self._select_start)
            self.update()
        else:
            super().mouseReleaseEvent(event)
    
    def _apply_rect_selection(self, rect):
        """Добавить/удалить все ячейки, чьи центры попадают в прямоугольник."""
        # Переводим координаты прямоугольника в координаты исходного изображения
        x1 = rect.left() / self.scale_factor
        x2 = rect.right() / self.scale_factor
        y1 = rect.top() / self.scale_factor
        y2 = rect.bottom() / self.scale_factor

        cells_in_rect = []
        cols = self._counts['x']
        rows = self._counts['y']
        for col_idx in range(len(cols)-1):
            for row_idx in range(len(rows)-1):
                # Центр ячейки
                col_x = cols[col_idx]
                row_y = rows[row_idx]
                w = self._get_cell_width(col_x)
                h = self._get_cell_height(row_y)
                cx = col_x + w / 2
                cy = row_y + h / 2
                if (x1 <= cx <= x2 or x2 <= cx <= x1) and (y1 <= cy <= y2 or y2 <= cy <= y1):
                    cells_in_rect.append((col_idx, row_idx))

        if not cells_in_rect:
            return
        # Определяем операцию: если первая ячейка уже выделена — удаляем, иначе добавляем
        first_cell = cells_in_rect[0]
        remove = first_cell in self.__click_history
        for cell in cells_in_rect:
            if remove:
                if cell in self.__click_history:
                    self.__click_history.remove(cell)
            else:
                if cell not in self.__click_history:
                    self.__click_history.append(cell)
    
    def _single_click(self, pos):
        original_x = int(pos.x() / self.scale_factor)
        original_y = int(pos.y() / self.scale_factor)
        xs = self._counts.get('x', [])
        ys = self._counts.get('y', [])
        if len(xs) < 2 or len(ys) < 2:
            return
        x_idx = bisect.bisect_right(xs, original_x) - 1
        y_idx = bisect.bisect_right(ys, original_y) - 1
        if 0 <= x_idx < len(xs)-1 and 0 <= y_idx < len(ys)-1:
            if (x_idx, y_idx) in self.__click_history:
                self.__click_history.remove((x_idx, y_idx))
            else:
                self.__click_history.append((x_idx, y_idx))
    
    def set_click_history(self, cells):
        """Заменяет историю выделенных ячеек (например, при загрузке исключённых)."""
        self._GridOverImage__click_history = list(cells)   # доступ к приватному атрибуту
        self.update()
    

