# src/gui/scrollable_image_view.py
from PyQt5.QtWidgets import QScrollArea, QWidget
from PyQt5.QtCore import Qt, QPoint, pyqtSignal, QTimer
from PyQt5.QtGui import QWheelEvent, QMouseEvent

class ScrollableImageView(QScrollArea):
    zoomChanged = pyqtSignal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(False) # запрещаем менять размер виджиту, поскольку сами будем явно задавать
        self.setAlignment(Qt.AlignCenter) 
        self.setFrameShape(QScrollArea.NoFrame)
        self._image_widget = None
        self._zoom_factor = 1.0 # Текущий масштаб
        self._zoom_min = 1.0 
        self._zoom_max = 5.0 
        self._zoom_step = 1.25 
        self._panning = False # Флаг что сейчас происходит перемещение картинки через зажатую кнопку
        self._pan_start_pos = QPoint() # Начальная позиция мыши (в координатах viewport)
        self._pan_start_scroll = QPoint() # Начальное положения скролл-баров в момент нажатия
        self.setMouseTracking(True)


    def set_image_widget(self, widget: QWidget):
        if self._image_widget is not None:
            self._image_widget.deleteLater()
        self._image_widget = widget
        self.setWidget(widget)
        self._update_widget_size()


    def _update_widget_size(self):
        if not self._image_widget:
            return
        
        if hasattr(self._image_widget, 'original_size_hint'):
            orig_size = self._image_widget.original_size_hint()
        else:
            orig_size = self._image_widget.sizeHint()
            
        new_width = int(orig_size.width() * self._zoom_factor)
        new_height = int(orig_size.height() * self._zoom_factor)
        
        self._image_widget.setFixedSize(new_width, new_height)

        if hasattr(self._image_widget, 'set_zoom_factor'):
            self._image_widget.set_zoom_factor(self._zoom_factor)
        elif hasattr(self._image_widget, 'scale_factor'):
            self._image_widget.scale_factor = self._zoom_factor
            
        self._image_widget.updateGeometry()
        self._image_widget.update()

    # anchor (точка в координатах viewport, обычно event.pos() от колесика мыши)
    def zoom_to(self, factor: float, anchor: QPoint = None):
        new_factor = max(self._zoom_min, min(self._zoom_max, factor))
        if abs(new_factor - self._zoom_factor) < 1e-6:
            return

        old_widget_pos = None
        if anchor is not None and self._image_widget:
            old_widget_pos = self._image_widget.mapFromGlobal(self.viewport().mapToGlobal(anchor))
            if not self._image_widget.rect().contains(old_widget_pos):
                anchor = None

        old_factor = self._zoom_factor
        self._zoom_factor = new_factor
        self._update_widget_size()
        self.zoomChanged.emit(self._zoom_factor)

        if anchor is not None and old_widget_pos is not None:
            new_widget_pos = old_widget_pos * (self._zoom_factor / old_factor)
            target_scroll_x = int(new_widget_pos.x() - anchor.x())
            target_scroll_y = int(new_widget_pos.y() - anchor.y())
            h_max = self.horizontalScrollBar().maximum()
            v_max = self.verticalScrollBar().maximum()
            self.horizontalScrollBar().setValue(min(max(target_scroll_x, 0), h_max))
            self.verticalScrollBar().setValue(min(max(target_scroll_y, 0), v_max))
            
    # Результат: когда вы крутите колёсико, точка изображения, 
    # на которую указывал курсор, остаётся на том же месте, а не уезжает в сторону.

    def zoom_in(self, anchor: QPoint = None): # Увеличивает н шаг
        self.zoom_to(self._zoom_factor * self._zoom_step, anchor)

    def zoom_out(self, anchor: QPoint = None): # Уменьшает уменьшает на шаг
        self.zoom_to(self._zoom_factor / self._zoom_step, anchor)

    def reset_zoom(self): 
        self.zoom_to(1.0)
        QTimer.singleShot(50, lambda: self.horizontalScrollBar().setValue(0))
        QTimer.singleShot(50, lambda: self.verticalScrollBar().setValue(0))

    def wheelEvent(self, event: QWheelEvent):
        if event.modifiers() == Qt.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self.zoom_in(anchor=event.pos())
            else:
                self.zoom_out(anchor=event.pos())
        else:
            super().wheelEvent(event)

    def mousePressEvent(self, event: QMouseEvent): # нажатие кнопки
        if event.button() == Qt.RightButton:
            self._panning = True
            self._pan_start_pos = event.pos()
            self._pan_start_scroll = QPoint(self.horizontalScrollBar().value(),
                                            self.verticalScrollBar().value())
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
        else:
            super().mousePressEvent(event)
 
    def mouseMoveEvent(self, event: QMouseEvent): # движение мыши
        if self._panning:
            delta = event.pos() - self._pan_start_pos
            new_h = self._pan_start_scroll.x() - delta.x()
            new_v = self._pan_start_scroll.y() - delta.y()
            self.horizontalScrollBar().setValue(new_h)
            self.verticalScrollBar().setValue(new_v)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent): # опускание мыши
        if event.button() == Qt.RightButton and self._panning:
            self._panning = False
            self.setCursor(Qt.ArrowCursor)
            event.accept()
        else:
            super().mouseReleaseEvent(event)