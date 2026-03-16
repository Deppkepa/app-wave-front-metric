from PyQt5.QtWidgets import QLabel, QApplication, QMainWindow
from PyQt5.QtGui import QPainter, QPen
from PyQt5.QtCore import Qt


class grid_over_image(QLabel):
    # TODO: Просмотреть как работает код

    def __init__(self, parent=None):
        super(grid_over_image, self).__init__(parent)
        self.__pixmap = None
        self.__cell_size = None
    
    def setPixmapAndDrawGrid(self, value, cell_size=50):
        """
        Устанавливает пиксмап и одновременно запускает перерисовку с добавлением сетки.
        
        :param pixmap: Объект QPixmap, содержащий исходное изображение.
        :param cell_size: Размер ячейки сетки (ширина и высота клетки).
        """
        self.__pixmap = value
        print(self.__pixmap)
        self.__cell_size = cell_size
        self.update()  # принудительная перерисовка
    
    def paintEvent(self, event):
        if self.__pixmap is None:
            return 
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self.__pixmap)  # рисуем основное изображение
        
        pen = QPen(Qt.red, 4, Qt.SolidLine)  # создаём перо для рисования линии сетки
        painter.setPen(pen)
        
        width = self.__pixmap.width()
        height = self.__pixmap.height()
        
        for x in range(0, width + self.__cell_size, self.__cell_size):
            painter.drawLine(x, 0, x, height)  # вертикальные линии
        
        for y in range(0, height + self.__cell_size, self.__cell_size):
            painter.drawLine(0, y, width, y)   # горизонтальные линии