import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *


from src.gui.Menu_bar_horizontal import MenuBarHorizontal
from src.controller.manager import Manager
from src.gui.grid_over_image import GridOverImage
from src.gui.parametrs import GridSettings


# ⁡⁢⁢⁢INFO⁡: Главное окно

class AppWFMetric(QMainWindow):
    def __init__(self):
        super().__init__()
        self.__manager = Manager()
        self.__first_tab = QWidget()
        self.__menubar = self.menuBar()
        self.__menu_handler = MenuBarHorizontal()
        
        self.initUI()

    def initUI(self):
        tabs = QTabWidget()
        self.setCentralWidget(tabs)

        # Первая вкладка для сетки
        self.first_vbox = QHBoxLayout(self.__first_tab)
        tabs.addTab(self.__first_tab, "Изображение")



        # Вторая вкладка с надписью "Привет, мир!"
        second_tab = QWidget()
        second_vbox = QVBoxLayout(second_tab)
        hello_world_label = QLabel("Привет, мир!")
        second_vbox.addWidget(hello_world_label)
        tabs.addTab(second_tab, "Отчет анализа")

        # --- МЕНЮ ---
        self.__menu_handler.setup_menu(self.__menubar)
        self.__connect_menu_signals()

    
        # Размер окна и заголовок
        self.setGeometry(300, 300, 1000, 800)
        self.setWindowTitle('Метрика волнового фронта')


        # FIXME: Автоматизировать задаваемые параметры окна
        
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
        if filename:
            processed_models, contours = self.__manager.start(filename)
            if processed_models:
                self.clear_layout(target_layout)

                # Создаем новый виджет с сеткой и добавляем его в существующий макет
                # Передаем хранилище углов в виджет

                viewer = GridOverImage()
                viewer.set_pixmap_and_draw_grid(processed_models[0], contours)
                
                settings_widget = GridSettings(viewer)

                # Добавляем виджет в существующий макет
                target_layout.addWidget(viewer)
                target_layout.addWidget(settings_widget)

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