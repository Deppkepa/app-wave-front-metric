# src/gui/parametrs.py
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtCore import pyqtSignal

class GridSettings(QWidget):
    saveRequested = pyqtSignal()
    """
    Панель управления для настройки отображения изображения с сеткой.
    Содержит ползунок масштаба, кнопку сброса и (опционально) другие параметры.
    """
    def __init__(self, scrollable_view, carousel=None, parent=None):
        """
        :param scrollable_view: экземпляр ScrollableImageView, который управляет масштабом
        """
        super().__init__(parent)
        self.scrollable = scrollable_view
        self.carousel = carousel   # ссылка на ImageCarousel

        # Фиксируем ширину панели (как и было)
        self.setFixedWidth(250)

        # Основной вертикальный layout
        layout = QVBoxLayout(self)
        
        

        # --- Блок масштабирования ---
        zoom_group = QGroupBox("Масштаб")
        zoom_layout = QFormLayout(zoom_group)

        # Ползунок масштаба (от 10% до 500%)
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setMinimum(100)     # 10%
        self.zoom_slider.setMaximum(500)    # 500%
        self.zoom_slider.setValue(int(self.scrollable._zoom_factor * 100))
        self.zoom_slider.valueChanged.connect(self.on_zoom_slider_changed)

        # Текущее значение масштаба (можно добавить для удобства)
        self.zoom_label = QLabel(f"{self.zoom_slider.value()}%")
        self.zoom_label.setAlignment(Qt.AlignCenter)

        # Кнопка сброса масштаба
        reset_btn = QPushButton("Сбросить масштаб (100%)")
        reset_btn.clicked.connect(self.scrollable.reset_zoom)

        zoom_layout.addRow("Масштаб (%):", self.zoom_slider)
        zoom_layout.addRow("Текущий:", self.zoom_label)
        zoom_layout.addRow(reset_btn)

        # --- Подключаем сигнал от scrollable для обновления ползунка при зуме мышью ---
        self.scrollable.zoomChanged.connect(self.on_zoom_from_view)

        # --- Добавляем группу в основной layout ---
        layout.addWidget(zoom_group)
        
        
        # --- Кнопки действий ---
        self.save_all_btn = QPushButton("Сохранить для всех кадров")
        self.save_all_btn.setEnabled(False)   # станет активной после подготовки
        self.save_all_btn.clicked.connect(self.on_save_all)
        
        self.save_current_btn = QPushButton("Сохранить для текущего кадра")
        self.save_current_btn.setEnabled(False)
        self.save_current_btn.clicked.connect(self.on_save_current)

        self.start_analysis_btn = QPushButton("Произвести анализ")
        self.start_analysis_btn.setEnabled(False)
        self.start_analysis_btn.clicked.connect(self.on_start_analysis)
        
        self.reset_current_btn = QPushButton("Сбросить исключения (тек.)")
        self.reset_current_btn.clicked.connect(self.on_reset_current)
        self.reset_all_btn = QPushButton("Сбросить исключения (все)")
        self.reset_all_btn.clicked.connect(self.on_reset_all)

        layout.addWidget(self.save_all_btn)
        layout.addWidget(self.save_current_btn)
        layout.addWidget(self.start_analysis_btn)
        layout.addWidget(self.reset_current_btn)
        layout.addWidget(self.reset_all_btn)
        
        layout.addStretch()   # Прижимаем содержимое к верху

        # Если в будущем понадобятся другие параметры (цвет сетки, толщина линий и т.д.),
        # их можно добавить сюда.

    def set_reset_enabled(self, enabled):
        self.reset_current_btn.setEnabled(enabled)
        self.reset_all_btn.setEnabled(enabled)

    def on_reset_current(self):
        if self.carousel:
            self.carousel.reset_excluded_current()

    def on_reset_all(self):
        if self.carousel:
            self.carousel.reset_excluded_all()
    
    def on_zoom_slider_changed(self, value):
        """Обработчик изменения ползунка – устанавливаем масштаб в scrollable."""
        factor = value / 100.0
        self.scrollable.zoom_to(factor)
        # Обновляем текстовую метку (хотя она обновится и через zoomChanged, но для скорости)
        self.zoom_label.setText(f"{value}%")

    def on_zoom_from_view(self, factor):
        """
        Синхронизация ползунка и метки при изменении масштаба извне
        (например, при вращении колёсика мыши с Ctrl).
        """
        percent = int(factor * 100)
        # Блокируем сигналы, чтобы не вызвать рекурсию
        self.zoom_slider.blockSignals(True)
        self.zoom_slider.setValue(percent)
        self.zoom_slider.blockSignals(False)
        self.zoom_label.setText(f"{percent}%")
    
    def set_save_all_enabled(self, enabled):
        self.save_all_btn.setEnabled(enabled)
        
    def set_save_current_enabled(self, enabled):
        self.save_current_btn.setEnabled(enabled)

    def set_analysis_enabled(self, enabled):
        self.start_analysis_btn.setEnabled(enabled)

    def on_save_all(self):
        if self.carousel:
            self.carousel.save_all_frames()
            # Разрешаем кнопку анализа
            if hasattr(self.carousel, 'set_analysis_enabled'):
                self.carousel.set_analysis_enabled(True)
                self.start_analysis_btn.setEnabled(True)

    def on_start_analysis(self):
        if self.carousel:
            self.carousel.start_analysis()
    
    def on_save_current(self):
        if self.carousel:
            self.carousel.save_current_frame()