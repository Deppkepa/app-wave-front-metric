from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from src.gui.Menu_bar_horizontal import MenuBarHorizontal
from src.gui.parametrs import GridSettings
from src.gui.loader_thread import LoaderThread
from src.gui.image_carousel import ImageCarousel
from src.gui.analysis_report import AnalysisReportWidget
import os

class AppWFMetric(QMainWindow):
    def __init__(self):
        super().__init__()
        self.__first_tab = QWidget()
        self.__menubar = self.menuBar()
        self.__menu_handler = MenuBarHorizontal()
        self.current_thread = None
        self._manager = None
        self.report_widget = None
        self.second_vbox = None
        self.settings_widget = None
        self._busy = False
        self._file_name_label = None    # метка для отображения имени файла
        self.initUI()
        # Автоматическое открытие последнего файла
        self._last_file = self._load_last_file_path()
        if self._last_file and os.path.exists(self._last_file):
            QTimer.singleShot(100, lambda: self._auto_open_last_file())

    def initUI(self):
        tabs = QTabWidget()
        self.setCentralWidget(tabs)

        # ─── Вкладка "Изображение" ─────────────────────────────
        # Вертикальный контейнер для метки и горизонтального слоя
        tab_layout = QVBoxLayout(self.__first_tab)
        tab_layout.setContentsMargins(5, 5, 5, 5)

        # Метка с именем файла
        self._file_name_label = QLabel("")
        self._file_name_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        font = self._file_name_label.font()
        font.setPointSize(10)
        self._file_name_label.setFont(font)
        tab_layout.addWidget(self._file_name_label)

        # Горизонтальный слой (остаётся без изменений)
        self.first_vbox = QHBoxLayout()
        self._welcome_label = QLabel("Откройте файл формата .h5 для начала работы")
        self._welcome_label.setAlignment(Qt.AlignCenter)
        self.first_vbox.addStretch()
        self.first_vbox.addWidget(self._welcome_label)
        self.first_vbox.addStretch()
        tab_layout.addLayout(self.first_vbox, stretch=1)

        tabs.addTab(self.__first_tab, "Изображение")

        # ─── Вкладка "Отчет анализа" ───────────────────────────
        second_tab = QWidget()
        self.second_vbox = QVBoxLayout(second_tab)
        self.report_widget = AnalysisReportWidget()
        self.second_vbox.addWidget(self.report_widget)
        tabs.addTab(second_tab, "Отчет анализа")

        # ─── Меню ──────────────────────────────────────────────
        self.__menu_handler.setup_menu(self.__menubar)
        self.__connect_menu_signals()

        self.center_window()
        self.setWindowTitle('Метрика волнового фронта')

        # Прогресс-бар
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setVisible(False)
        self.progress_bar.setFixedHeight(15)
        self.progress_bar.setFixedWidth(150)
        self.progress_bar.setTextVisible(True)
        self.statusBar().addPermanentWidget(self.progress_bar)

    def center_window(self):
        screen_geometry = QApplication.primaryScreen().availableGeometry()
        screen_center = screen_geometry.center()
        window_width = 1000
        window_height = 800
        x = screen_center.x() - window_width // 2
        y = screen_center.y() - window_height // 2
        self.setGeometry(x, y, window_width, window_height)

    def __connect_menu_signals(self):
        self.__menu_handler.signal_file_open.connect(lambda: self.open_file(self.first_vbox))
        self.__menu_handler.signal_file_new.connect(self.new_file)
        self.__menu_handler.signal_file_save.connect(self.save_file)
        self.__menu_handler.signal_file_save_as.connect(self.save_as_file)
        self.__menu_handler.signal_file_close.connect(self.close_file)
        self.__menu_handler.signal_file_exit.connect(self.close)
        self.__menu_handler.signal_about.connect(self.show_about_dialog)

    def _set_busy_state(self, busy: bool):
        self._busy = busy
        file_menu = self.__menubar.findChild(QMenu, "Файл")
        if file_menu:
            file_menu.setEnabled(not busy)
        if self.settings_widget:
            self.settings_widget.setEnabled(not busy)
        if hasattr(self, '_carousel'):
            self._carousel.set_controls_enabled(not busy)

    def _auto_open_last_file(self):
        self.open_file(self.first_vbox, file_path=self._last_file)

    def _load_last_file_path(self):
        settings = QSettings("WaveFrontMetric", "App")
        return settings.value("lastFile", "")

    def _save_last_file_path(self, path):
        settings = QSettings("WaveFrontMetric", "App")
        settings.setValue("lastFile", path)

    def new_file(self):
        print("Создали новый файл!")

    def open_file(self, target_layout, file_path=None):
        if self._busy:
            return
        if not file_path:
            options = QFileDialog.Options()
            file_path, _ = QFileDialog.getOpenFileName(self, "Выберите файл", "", "Все файлы (*);;", options=options)
        if not file_path:
            return
        self._set_busy_state(True)
        self.progress_bar.setVisible(True)
        self.statusBar().showMessage("Открытие файла и сжатие...", 0)
        QApplication.processEvents()

        self._save_last_file_path(file_path)
        self.current_thread = LoaderThread(file_path)
        self.current_thread.finished.connect(lambda manager: self._on_load_finished(target_layout, manager))
        self.current_thread.error.connect(self._on_load_error)
        self.current_thread.progress.connect(self._on_load_progress)
        self.current_thread.start()

    def _on_load_finished(self, target_layout, manager):
        self._manager = manager
        self._set_busy_state(False)
        self.progress_bar.setVisible(False)
        total = manager.get_num_images()
        self.statusBar().showMessage(f"Загружено {total} изображений", 2000)

        # ─── Отображаем имя файла ──────────────────────────────
        file_path = str(manager._reader._path)          # полный путь
        file_name = os.path.basename(file_path)         # только имя файла
        self._file_name_label.setText(f"Файл: {file_name}")
        self.setWindowTitle(f"Метрика волнового фронта - {file_name}")

        self.clear_layout(target_layout)

        carousel = ImageCarousel()
        carousel.reportResetRequested.connect(lambda: self.report_widget.invalidate_cache())
        carousel.analysisRequested.connect(lambda: self._start_analysis())
        carousel.statusMessage.connect(lambda msg: self.statusBar().showMessage(msg, 3000))
        self._carousel = carousel
        carousel.set_manager(manager, total)
        carousel.set_analysis_ready(False)

        # excluded = manager.get_excluded_cells_for_frame(0)
        # if excluded:
        #     carousel.viewer.set_click_history(excluded)

        settings_widget = GridSettings(carousel.scrollable, carousel=carousel)
        self.settings_widget = settings_widget
        self.settings_widget.set_reset_enabled(True)

        target_layout.addWidget(carousel, stretch=1)
        target_layout.addWidget(settings_widget, stretch=0)

        manager.run_background_init()
        self._prepare_timer = QTimer()
        self._prepare_timer.setInterval(50)
        self._prepare_timer.timeout.connect(lambda: self._check_prepare_thread(manager, carousel))
        self._prepare_timer.start(100)

        QTimer.singleShot(500, self.check_analysis_status)

    def check_analysis_status(self):
        if not self._manager or not hasattr(self._manager, '_storage') or not self._manager._storage.db_path:
            return
        db_path = self._manager._storage.db_path
        file_id = self._manager._file_id
        self.report_widget.set_db_and_file(db_path, file_id)

    def _on_load_error(self, error_msg):
        self._set_busy_state(False)
        self.progress_bar.setVisible(False)
        self.statusBar().showMessage("Ошибка загрузки", 3000)
        QMessageBox.critical(self, "Ошибка загрузки", error_msg)

    def _on_load_progress(self, current, total):
        percent = int(current / total * 100) if total > 0 else 0
        self.progress_bar.setValue(percent)
        self.statusBar().showMessage(f"Загрузка: {current} из {total}", 0)

    def closeEvent(self, event):
        if self._busy:
            QMessageBox.information(self, "Процесс выполняется",
                                    "Дождитесь окончания текущего процесса перед закрытием.")
            event.ignore()
            return
        if self.current_thread and self.current_thread.isRunning():
            reply = QMessageBox.question(self, "Подождите", "Идёт загрузка. Прервать?",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.current_thread.terminate()
                self.current_thread.wait()
            else:
                event.ignore()
                return
        if hasattr(self, '_manager') and self._manager:
            self._manager.cancel_background_init()
            self._manager.cancel_prepare()
        event.accept()

    def _check_prepare_thread(self, manager, carousel):
        if hasattr(manager, 'prepare_thread') and manager.prepare_thread is not None:
            self._prepare_timer.stop()
            pt = manager.prepare_thread
            pt.progress.connect(self._on_prepare_progress)
            pt.finished.connect(lambda: self._on_prepare_finished_with_carousel(carousel))
            pt.error.connect(self._on_prepare_error)
            if pt.isFinished():
                self._on_prepare_finished_with_carousel(carousel)
            else:
                total = pt.total
                self.progress_bar.setRange(0, total)
                self.progress_bar.setValue(0)
                self.progress_bar.setVisible(True)
                self.statusBar().showMessage("Подготовка субапертур...", 0)

    def _on_prepare_finished_with_carousel(self, carousel):
        print("Подготовка всех субапертур завершена")
        self.progress_bar.setVisible(False)
        self.statusBar().showMessage("Подготовка завершена", 2000)
        carousel.set_analysis_ready(True)
        self.settings_widget.set_save_all_enabled(True)
        self.settings_widget.set_save_current_enabled(True)
        if self._manager and self._manager.has_excluded_cells():
            carousel.set_analysis_enabled(True)
            self.settings_widget.set_analysis_enabled(True)
        # Заставляем отчёт перечитать данные после возможного изменения исключений
        self.report_widget.invalidate_cache()

    def _on_prepare_progress(self, current, total):
        self.progress_bar.setValue(current)
        self.statusBar().showMessage(f"Подготовка: {current}/{total}", 0)

    def _on_prepare_finished(self):
        pass

    def _start_analysis(self):
        if self._busy:
            return
        print("DEBUG: _start_analysis вызван")
        if not self._manager:
            return
        self._set_busy_state(True)
        if hasattr(self.report_widget, 'invalidate_cache'):
            self.report_widget.invalidate_all_cache()
        try:
            analysis_thread = self._manager.run_analysis()
            if analysis_thread:
                analysis_thread.progress.connect(self._on_analysis_progress)
                analysis_thread.finished.connect(self._on_analysis_finished)
                analysis_thread.error.connect(self._on_analysis_error)
                analysis_thread.start()
                self.progress_bar.setRange(0, 0)
                self.progress_bar.setVisible(True)
                self.statusBar().showMessage("Начат анализ...")
        except Exception as e:
            self._set_busy_state(False)
            QMessageBox.critical(self, "Ошибка", f"Не удалось запустить анализ: {e}")

    def _on_analysis_progress(self, current, total):
        self.progress_bar.setRange(0, total)
        self.progress_bar.setValue(current)
        self.statusBar().showMessage(f"Анализ: {current}/{total}", 0)

    def _on_analysis_finished(self):
        self._set_busy_state(False)
        self.progress_bar.setVisible(False)
        self.statusBar().showMessage("Анализ завершён", 3000)
        self.check_analysis_status()

    def _on_analysis_error(self, err_msg):
        self._set_busy_state(False)
        print("DEBUG: analysis error:", err_msg)
        self.progress_bar.setVisible(False)
        self.statusBar().showMessage("Ошибка анализа", 3000)
        QMessageBox.critical(self, "Ошибка анализа", err_msg)

    def _on_prepare_error(self, err):
        self.progress_bar.setVisible(False)
        self.statusBar().showMessage("Ошибка подготовки", 3000)
        QMessageBox.critical(self, "Ошибка подготовки", err)

    def clear_layout(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    sub_layout = item.layout()
                    if sub_layout:
                        self.clear_layout(sub_layout)

    def show_about_dialog(self):
        QMessageBox.about(self, "О программе",
                          "Метрика волнового фронта\n\n"
                          "Приложение для анализа данных датчика волнового фронта.\n"
                          "Инструкция появится позже.")

    def save_file(self):
        print("сохранили файл!")

    def save_as_file(self):
        print("сохранили как файл!")

    def close_file(self):
        print("Закрыть файл!")

    def exit_file(self):
        self.close()