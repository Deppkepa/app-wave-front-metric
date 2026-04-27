from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QSlider, QPushButton, QLabel
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from src.gui.scroll import ScrollableImageView
from src.gui.grid_over_image import GridOverImage

class ImageCarousel(QWidget):
    currentIndexChanged = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._manager = None
        self._total_count = 0
        self._current_index = 0
        self._pending_slider_index = 0

        self.scrollable = ScrollableImageView()
        self.viewer = GridOverImage()
        self.scrollable.set_image_widget(self.viewer)

        # Панель управления
        control_panel = QWidget()
        control_layout = QHBoxLayout(control_panel)
        control_layout.setContentsMargins(0, 5, 0, 5)

        self.prev_btn = QPushButton("<")
        self.prev_btn.setFixedSize(30, 25)
        self.prev_btn.clicked.connect(self.prev_image)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(0)
        self.slider.setTracking(True)   # непрерывные сигналы
        self.slider.sliderMoved.connect(self.on_slider_moved)

        self.index_label = QLabel("0 / 0")
        self.index_label.setAlignment(Qt.AlignCenter)
        self.index_label.setMinimumWidth(60)

        self.next_btn = QPushButton(">")
        self.next_btn.setFixedSize(30, 25)
        self.next_btn.clicked.connect(self.next_image)

        control_layout.addWidget(self.prev_btn)
        control_layout.addWidget(self.slider, stretch=1)
        control_layout.addWidget(self.index_label)
        control_layout.addWidget(self.next_btn)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.scrollable, stretch=1)
        main_layout.addWidget(control_panel, stretch=0)

        # Таймер для throttling обновлений слайдера
        self._slider_timer = QTimer()
        self._slider_timer.setSingleShot(True)
        self._slider_timer.timeout.connect(self._on_slider_timer_timeout)
        self._slider_update_interval = 30   # мс (около 33 кадров в секунду)

    def set_manager(self, manager, total_images):
        self._manager = manager
        self._total_count = total_images
        self._current_index = 0
        self.slider.setMaximum(total_images - 1 if total_images > 0 else 0)
        self.update_current_image()
        self.update_controls()

    def update_current_image(self):
        if self._manager is None or self._total_count == 0:
            return
        try:
            pixmap, contours = self._manager.get_image_and_contours(self._current_index)
            self.viewer.set_pixmap_and_draw_grid(pixmap, contours)
            self.scrollable._update_widget_size()
        except Exception as e:
            print(f"Ошибка загрузки кадра {self._current_index}: {e}")

    def update_controls(self):
        self.slider.blockSignals(True)
        self.slider.setValue(self._current_index)
        self.slider.blockSignals(False)
        self.index_label.setText(f"{self._current_index + 1} / {self._total_count}")
        self.prev_btn.setEnabled(self._current_index > 0)
        self.next_btn.setEnabled(self._current_index < self._total_count - 1)

    def on_slider_moved(self, value):
        """Обработка движения ползунка с ограничением частоты обновлений."""
        self._pending_slider_index = value
        if not self._slider_timer.isActive():
            self._slider_timer.start(self._slider_update_interval)

    def _on_slider_timer_timeout(self):
        # Показываем кадр, соответствующий последнему положению ползунка
        if self._pending_slider_index != self._current_index:
            self._current_index = self._pending_slider_index
            self.update_current_image()
            self.update_controls()
            self.currentIndexChanged.emit(self._current_index)

    def next_image(self):
        if self._current_index < self._total_count - 1:
            self._current_index += 1
            self.update_current_image()
            self.update_controls()
            self.currentIndexChanged.emit(self._current_index)

    def prev_image(self):
        if self._current_index > 0:
            self._current_index -= 1
            self.update_current_image()
            self.update_controls()
            self.currentIndexChanged.emit(self._current_index)

    def reset_zoom(self):
        self.scrollable.reset_zoom()