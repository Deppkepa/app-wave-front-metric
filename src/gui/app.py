
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *


from src.gui.Menu_bar_horizontal import MenuBarHorizontal
from src.gui.parametrs import GridSettings
from src.gui.loader_thread import LoaderThread
from src.gui.image_carousel import ImageCarousel



# ⁡⁢⁢⁢INFO⁡: Главное окно

class AppWFMetric(QMainWindow):
    def __init__(self):
        super().__init__()
        self.__first_tab = QWidget()
        self.__menubar = self.menuBar()
        self.__menu_handler = MenuBarHorizontal()
        self.current_thread = None
        self.initUI()

    def initUI(self):
        
        # --- ТАБ ---
        tabs = QTabWidget()
        self.setCentralWidget(tabs)

        self.first_vbox = QHBoxLayout(self.__first_tab)
        tabs.addTab(self.__first_tab, "Изображение")

        second_tab = QWidget()
        second_vbox = QVBoxLayout(second_tab)
        hello_world_label = QLabel("Привет, мир!")
        second_vbox.addWidget(hello_world_label)
        tabs.addTab(second_tab, "Отчет анализа")

        # --- МЕНЮ ---
        self.__menu_handler.setup_menu(self.__menubar)
        self.__connect_menu_signals()
        
        # --- РАЗМЕР ОКНА И ЗАГОЛОВОК ---
        self.center_window()
        self.setWindowTitle('Метрика волнового фронта')
        
        # --- ПРОГРЕСС БАР ---
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
        """
        Внутренняя функция для соединения всех сигналов меню с соответствующими слотами.
        """
        self.__menu_handler.signal_file_open.connect(lambda: self.open_file(self.first_vbox))
        self.__menu_handler.signal_file_new.connect(self.new_file)
        self.__menu_handler.signal_file_save.connect(self.save_file)
        self.__menu_handler.signal_file_save_as.connect(self.save_as_file)
        self.__menu_handler.signal_file_close.connect(self.close_file)
        self.__menu_handler.signal_file_exit.connect(self.exit_file)
   
    
    def new_file(self):
        print("Создали новый файл!")


    def open_file(self, target_layout):
        options = QFileDialog.Options()
        filename, _ = QFileDialog.getOpenFileName(self, "Выберите файл", "", "Все файлы (*);;", options=options)
        if not filename:
            return
        self.progress_bar.setVisible(True)
        self.statusBar().showMessage("Открытие файла и сжатие...", 0)
        QApplication.processEvents()

        self.current_thread = LoaderThread(filename)
        self.current_thread.finished.connect(lambda manager: self._on_load_finished(target_layout, manager))
        self.current_thread.error.connect(self._on_load_error)
        self.current_thread.progress.connect(self._on_load_progress)
        self.current_thread.start()

    def _on_load_finished(self, target_layout, manager):
        self.progress_bar.setVisible(False)
        total = manager.get_num_images()
        self.statusBar().showMessage(f"Загружено {total} изображений (сжато в память)", 2000)

        self.clear_layout(target_layout)

        carousel = ImageCarousel()
        carousel.set_manager(manager, total)

        settings_widget = GridSettings(carousel.scrollable)

        target_layout.addWidget(carousel, stretch=1)
        target_layout.addWidget(settings_widget, stretch=0)


    def _on_load_error(self, error_msg):
        self.progress_bar.setVisible(False)
        self.statusBar().showMessage("Ошибка загрузки", 3000)
        QMessageBox.critical(self, "Ошибка загрузки", error_msg)
        
        
    def _on_load_progress(self, current, total):
        percent = int(current / total * 100) if total > 0 else 0
        self.progress_bar.setValue(percent)
        self.statusBar().showMessage(f"Загрузка: {current} из {total}", 0)


    def closeEvent(self, event):
        if self.current_thread and self.current_thread.isRunning():
            reply = QMessageBox.question(self, "Подождите", "Идёт загрузка. Прервать?",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.current_thread.terminate()
                self.current_thread.wait()
            else:
                event.ignore()
                return
        event.accept()


    def clear_layout(self, layout):
        """Рекурсивно удаляет все виджеты из layout"""
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

     
 
    def save_file(self):
        print("сохранили файл!")

    def save_as_file(self):
        print("сохранили как файл!")
    
    def close_file(self):
        print("Закрыть файл!")

    def exit_file(self):
        print("Выход")

    def copy_text(self):
        print("Скопировали текст")