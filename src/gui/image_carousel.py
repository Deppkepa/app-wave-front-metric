from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QSlider, QPushButton, QLabel
from PyQt5.QtCore import Qt, pyqtSignal
from src.gui.scroll import ScrollableImageView
from src.gui.grid_over_image import GridOverImage

class ImageCarousel(QWidget):
    """
    Виджет для просмотра нескольких изображений с сеткой.
    Позволяет переключаться между ними с помощью ползунка и кнопок.
    """
    currentIndexChanged = pyqtSignal(int)  # сигнал при смене индекса

    def __init__(self, parent=None):
        super().__init__(parent)
        self._images = []          # список QPixmap
        self._contours = None      # данные сетки (словарь с x, y и т.д.)
        self._current_index = 0

        # Создаём виджет с прокруткой и внутренний GridOverImage
        self.scrollable = ScrollableImageView()
        self.viewer = GridOverImage()
        self.scrollable.set_image_widget(self.viewer)

        # Панель управления
        control_panel = QWidget()
        control_layout = QHBoxLayout(control_panel)
        control_layout.setContentsMargins(0, 5, 0, 5)

        # Кнопка "Назад"
        self.prev_btn = QPushButton("<")
        self.prev_btn.setFixedSize(30, 25)
        self.prev_btn.clicked.connect(self.prev_image)

        # Ползунок
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(0)
        self.slider.valueChanged.connect(self.on_slider_changed)

        # Метка с номером текущего изображения
        self.index_label = QLabel("0 / 0")
        self.index_label.setAlignment(Qt.AlignCenter)
        self.index_label.setMinimumWidth(60)

        # Кнопка "Вперёд"
        self.next_btn = QPushButton(">")
        self.next_btn.setFixedSize(30, 25)
        self.next_btn.clicked.connect(self.next_image)

        control_layout.addWidget(self.prev_btn)
        control_layout.addWidget(self.slider, stretch=1)
        control_layout.addWidget(self.index_label)
        control_layout.addWidget(self.next_btn)

        # Основной layout: scrollable + панель управления сверху (или снизу)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.scrollable, stretch=1)
        main_layout.addWidget(control_panel, stretch=0)

    def set_images(self, images, contours):
        """
        Устанавливает список изображений (QPixmap) и общие данные сетки.
        """
        if not images:
            return
        self._images = images
        self._contours = contours
        self._current_index = 0
        self.slider.setMaximum(len(images) - 1)
        self.update_current_image()
        self.update_controls()

    def update_current_image(self):
        """Обновляет GridOverImage текущим изображением и сеткой."""
        if 0 <= self._current_index < len(self._images):
            pixmap = self._images[self._current_index]
            self.viewer.set_pixmap_and_draw_grid(pixmap, self._contours)
            # Не сбрасываем масштаб и позицию — они сохраняются автоматически

    def update_controls(self):
        """Обновляет состояние элементов управления (ползунок, метка, кнопки)."""
        self.slider.blockSignals(True)
        self.slider.setValue(self._current_index)
        self.slider.blockSignals(False)
        self.index_label.setText(f"{self._current_index + 1} / {len(self._images)}")
        self.prev_btn.setEnabled(self._current_index > 0)
        self.next_btn.setEnabled(self._current_index < len(self._images) - 1)

    def on_slider_changed(self, value):
        """Обработчик изменения ползунка."""
        if value != self._current_index:
            self._current_index = value
            self.update_current_image()
            self.update_controls()
            self.currentIndexChanged.emit(self._current_index)

    def next_image(self):
        """Переход к следующему изображению."""
        if self._current_index < len(self._images) - 1:
            self._current_index += 1
            self.update_current_image()
            self.update_controls()
            self.currentIndexChanged.emit(self._current_index)

    def prev_image(self):
        """Переход к предыдущему изображению."""
        if self._current_index > 0:
            self._current_index -= 1
            self.update_current_image()
            self.update_controls()
            self.currentIndexChanged.emit(self._current_index)

    def reset_zoom(self):
        """Сброс масштаба и позиции текущего изображения (можно привязать к кнопке)."""
        self.scrollable.reset_zoom()
        
    def update_current_image(self):
        if 0 <= self._current_index < len(self._images):
            pixmap = self._images[self._current_index]
            self.viewer.set_pixmap_and_draw_grid(pixmap, self._contours)
            self.scrollable._update_widget_size()