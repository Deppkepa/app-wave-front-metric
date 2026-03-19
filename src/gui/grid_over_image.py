from PyQt5.QtWidgets import QLabel, QApplication, QMainWindow
from PyQt5.QtGui import QPainter, QPen
from PyQt5.QtCore import Qt
from src.logic.format.pixmap import pixmap


class grid_over_image(QLabel):
    # TODO: Просмотреть как работает код

    def __init__(self, parent=None):
        super(grid_over_image, self).__init__(parent)
        self.__pixmap = None
        self.__cell_size = None
        self.__points = []
    
    def setPixmapAndDrawGrid(self, value, cell_size=50):
        """
        Устанавливает пиксмап и одновременно запускает перерисовку с добавлением сетки.
        
        :param pixmap: Объект QPixmap, содержащий исходное изображение.
        :param cell_size: Размер ячейки сетки (ширина и высота клетки).
        """

        self.__pixmap = pixmap.ndarray_to_pixmap(value.image)
        self.__model_img = value
        
        self.__cell_size = cell_size
        for i in value.subapertures:
            
            self.__points.append(i.schematic_contour[:2])
        self.update()  # принудительная перерисовка
    
    def paintEvent(self, event):
        if self.__pixmap is None or len(self.__points) == 0:
            return 


        w = self.__pixmap.width()
        h = self.__pixmap.height()

        painter = QPainter(self)
        painter.drawPixmap(0, 0, self.__pixmap)

        pen = QPen(Qt.blue, 2, Qt.PenStyle.SolidLine)
        painter.setPen(pen)

        # группируем точки по столбцам и строкам
        cols_points = []
        rows_points = []
        # FIXME: Вытащить самую большую h субапертур поделить и добавить парочку точек по которым нужно будет дорисовать сетку

        for point in self.__points:
            x, y = point  # поменяли порядок на привычный (x, y) 
            cols_points.append(y)
            rows_points.append(x)
        cols_points = list(set(cols_points))
        rows_points = list(set(rows_points))

        sorted_numbers = sorted(cols_points)
        result_cols = [sorted_numbers[0]] 

        for number in sorted_numbers[1:]:
            if abs(number - result_cols[-1]) > 5:  # Если разница с последним элементом результата больше 5
                result_cols.append(number)
        

        sorted_numbers = sorted(rows_points)  # Сначала сортируем список

        if sorted_numbers[0] // 2 > 5:
            result_rows = [(sorted_numbers[0] // 2) + 1]  # Начинаем с первого элемента

        print(w)
        for number in sorted_numbers:
            if abs(number - result_rows[-1]) > 5:  # Если разница с последним элементом результата больше 5
                result_rows.append(number)

        print(abs(result_rows[-1] - w))
        while abs(result_rows[-1] - w) > 35:
            result_rows.append(result_rows[-1] + 35)

        
        print(result_rows)
        # Горизонтальная сетка
        for y in result_cols:
            painter.drawLine(0, y - 2, w, y - 2)


        # вертикальное сетка
        for x in result_rows:
            painter.drawLine(x - 2, 0, x - 2, h)
