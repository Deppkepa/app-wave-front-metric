from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QSlider, QPushButton, QLabel, QLineEdit, QMessageBox
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from src.gui.scroll import ScrollableImageView
from src.gui.grid_over_image import GridOverImage

class ImageCarousel(QWidget):
    currentIndexChanged = pyqtSignal(int)
    analysisRequested = pyqtSignal()
    statusMessage = pyqtSignal(str)
    reportResetRequested = pyqtSignal() 

    def __init__(self, parent=None):
        super().__init__(parent)
        self._manager = None
        self._total_count = 0
        self._current_index = 0
        self._pending_slider_index = 0
        self._analysis_enabled = False

        self.scrollable = ScrollableImageView()
        self.viewer = GridOverImage()
        self.scrollable.set_image_widget(self.viewer)

        control_panel = QWidget()
        control_layout = QHBoxLayout(control_panel)
        control_layout.setContentsMargins(0, 5, 0, 5)

        self.prev_btn = QPushButton("<")
        self.prev_btn.setFixedSize(30, 25)
        self.prev_btn.clicked.connect(self.prev_image)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(0)
        self.slider.setTracking(True)
        self.slider.sliderMoved.connect(self.on_slider_moved)

        self.index_label = QLabel("0 / 0")
        self.index_label.setAlignment(Qt.AlignCenter)
        self.index_label.setMinimumWidth(60)

        self.next_btn = QPushButton(">")
        self.next_btn.setFixedSize(30, 25)
        self.next_btn.clicked.connect(self.next_image)

        self.frame_input = QLineEdit()
        self.frame_input.setFixedWidth(50)
        self.frame_input.setPlaceholderText("№")
        self.frame_input.returnPressed.connect(self._on_frame_input)

        control_layout.addWidget(self.prev_btn)
        control_layout.addWidget(self.slider, stretch=1)
        control_layout.addWidget(self.index_label)
        control_layout.addWidget(self.next_btn)
        control_layout.addWidget(self.frame_input)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.scrollable, stretch=1)
        main_layout.addWidget(control_panel, stretch=0)

        self._slider_timer = QTimer()
        self._slider_timer.setSingleShot(True)
        self._slider_timer.timeout.connect(self._on_slider_timer_timeout)
        self._slider_update_interval = 30

    def set_controls_enabled(self, enabled: bool):
        """Блокирует/разблокирует элементы управления каруселью."""
        self.prev_btn.setEnabled(enabled)
        self.next_btn.setEnabled(enabled)
        self.slider.setEnabled(enabled)
        self.frame_input.setEnabled(enabled)

    def set_analysis_ready(self, ready: bool):
        self._analysis_ready = ready

    def set_analysis_enabled(self, enabled: bool):
        self._analysis_enabled = enabled

    def is_analysis_enabled(self):
        return self._analysis_enabled

    def _on_frame_input(self):
        try:
            num = int(self.frame_input.text())
        except ValueError:
            return
        if 1 <= num <= self._total_count:
            self._current_index = num - 1
            self.update_current_image()
            self.update_controls()
            self.currentIndexChanged.emit(self._current_index)

    def save_current_for_analysis(self):
        if self._manager is None:
            return
        excluded = self.viewer.get_excluded_cells()
        self._manager.save_subapertures_for_frame(self._current_index, excluded)
        print(f"Запущено сохранение для кадра {self._current_index}")

    def save_all_frames(self):
        if self._manager is None:
            return
        excluded = self.viewer.get_excluded_cells()
        self._manager.save_subapertures_for_all_frames(excluded)
        self.statusMessage.emit("Исключённые ячейки сохранены для всех кадров.")
        self.set_analysis_enabled(True)
        self.reportResetRequested.emit()

    def start_analysis(self):
        if not self._analysis_enabled:
            QMessageBox.warning(self, "Предупреждение",
                                "Сначала сохраните исключённые ячейки (Сохранить для всех кадров)")
            return
        self.analysisRequested.emit()

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
            # После загрузки изображения обновляем отображение исключённых ячеек
            self.load_excluded_for_current_frame()
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
        self._pending_slider_index = value
        if not self._slider_timer.isActive():
            self._slider_timer.start(self._slider_update_interval)

    def _on_slider_timer_timeout(self):
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

    def get_excluded_cells(self):
        return self.viewer.get_excluded_cells()
    
    def load_excluded_for_current_frame(self):
        """Загружает исключённые ячейки для текущего кадра и отображает их."""
        if self._manager is None:
            return
        cells = self._manager.get_excluded_cells_for_frame(self._current_index)
        self.viewer.set_click_history(cells)

    def save_current_frame(self):
        """Сохраняет исключённые ячейки только для текущего кадра."""
        if self._manager is None:
            return
        excluded = self.viewer.get_excluded_cells()
        self._manager.save_subapertures_for_frame(self._current_index, excluded)
        self.statusMessage.emit(f"Исключения для кадра {self._current_index} сохранены.")
        self.reportResetRequested.emit()
        
    def reset_excluded_current(self):
        """Сбрасывает отображение исключений для текущего кадра к исходному (только невалидные), без сохранения в БД."""
        if self._manager is None:
            return
        cells = self._manager.get_default_excluded_cells(self._current_index)
        self.viewer.set_click_history(cells)
        self.statusMessage.emit(f"Сетка исключений для кадра {self._current_index} сброшена (без сохранения)")
        self.reportResetRequested.emit()

    def reset_excluded_all(self):
        """Сбрасывает исключения для всех кадров к исходным (только невалидные) и сохраняет в БД."""
        if self._manager is None:
            return
        self._manager.reset_excluded_to_invalid()
        self.statusMessage.emit("Исключения для всех кадров сброшены и сохранены")
        self.load_excluded_for_current_frame()
        self.reportResetRequested.emit()
    
    def _notify_report_reset(self):
        """Сообщает отчёту, что данные нужно перезагрузить."""
        # Получаем ссылку на виджет отчёта через родительские окна (костыль, но для простоты).
        # Лучше хранить ссылку на report_widget в carousel или пробрасывать через сигнал.
        # Предлагаю добавить сигнал к carousel, как уже есть statusMessage.
        # Вместо этого мы можем просто вызывать invalidate_cache у известного объекта.
        # Реализуем через сигнал, чтобы сохранить слабую связность.
        self.reportResetRequested.emit()