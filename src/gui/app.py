import sys
from PyQt5.QtWidgets import *
from src.gui.Menu_bar_horizontal import menu_bar_horizontal
from src.controller.manager import manager
from src.gui.grid_subaperture import GridSubapertureView
from src.logic.model.model_image import model_image
from PyQt5.QtCore import Qt

#  Главное окно.

class app_w_f_metric(QMainWindow):
    # __manager_logic:manager = manager()
    __path_file:str = ""
    

    # FIXME: Сделать setap and propertu для менеджера

    @property
    def path_file(self) -> str:
        return self.__path_file

    @path_file.setter
    def path_file(self, path: str):
        self.__path_file = path

    def __init__(self):
        super().__init__()
        self.__manager = manager()
        self.__first_tab = QWidget()
        self.initUI()

    def initUI(self):
        tabs = QTabWidget()
        self.setCentralWidget(tabs)

        # Первая вкладка для сетки
        
        first_vbox = QVBoxLayout(self.__first_tab)
        tabs.addTab(self.__first_tab, "Изображение")

        # Вторая вкладка с надписью "Привет, мир!"
        second_tab = QWidget()
        second_vbox = QVBoxLayout(second_tab)
        hello_world_label = QLabel("Привет, мир!")
        second_vbox.addWidget(hello_world_label)
        tabs.addTab(second_tab, "Сообщение")

        # Меню с кнопкой "Открыть файл"
        menubar = self.menuBar()
        menu_bar = menu_bar_horizontal()
        menu_bar.setup_menu(menubar, self)

        

        # Размер окна и заголовок
        self.setGeometry(300, 300, 1000, 800)
        self.setWindowTitle('Метрика волнового фронта')


        # # FIXME: Автоматизировать задаваемые параметры окна
        
    
    def new_file(self):
        print("Создали новый файл!")

    def open_file(self):
        options = QFileDialog.Options()
        filename, _ = QFileDialog.getOpenFileName(self, "Выберите файл", "", "Все файлы (*);;", options=options)
        if filename:
            processed_models = self.__manager.process_date(filename)
            if processed_models:
                # Удаляем старые элементы с первой вкладки
                while self.__first_tab.layout().count():
                    child = self.__first_tab.layout().takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()
                
                # Создаем новую сетку
                print(type(processed_models))
                grid_widget = GridSubapertureView.create_view(processed_models, (0, 0))
                # grid_widget = GridSubapertureView.range_images()
                self.__first_tab.layout().addWidget(grid_widget)
            
            
            
        print( f"Вы выбрали файл: {self.__path_file}")

    

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