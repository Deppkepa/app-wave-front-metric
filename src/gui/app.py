import sys
from PyQt5.QtWidgets import *
from src.gui.Menu_bar_horizontal import menu_bar_horizontal
from src.logic.manager import manager

#  Главное окно.

class app_w_f_metric(QMainWindow):
    __manager_logic: manager = manager()
    __path_file:str = ""

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        lbl = QLabel('Hello World!', self)
        lbl.move(50, 50)  # Перемещаем лейбл на позицию (50, 50)
        menubar = self.menuBar()
        menu_bar_horizontal().setup_menu(menubar, self)
        

        # Параметры окна
        # FIXME: Автоматизировать задаваемые параметры окна
        self.setGeometry(250, 200, 1366, 768)  # Левый верхний угол, ширина, высота
        self.setWindowTitle('Metric wave-front')

    
    
    def new_file(self):
        print("Создали новый файл!")

    def open_file(self):
        # Диалог выбора файла
        options = QFileDialog.Options()
        filename, _ = QFileDialog.getOpenFileName(self, "Выбрать файл", "", "All Files (*)", options=options)
        
        if filename:
            self.__path_file = filename
            manager.process_date(filename)
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

    # def create_menu_bar(self):
    #     # Создание меню-бара
    #     menubar = self.menuBar()  # Получаем стандартный виджет меню-бара
        
    #     # Меню "Файл"
    #     file_menu = menubar.addMenu('Файл')
        
    #     # Действие "Открыть файл"
    #     open_action = QAction('Открыть', self)
    #     open_action.triggered.connect(self.open_file)  # Подключаем обработчик события
    #     file_menu.addAction(open_action)
        
    #     # Действие "Выход"
    #     exit_action = QAction('Выход', self)
    #     exit_action.triggered.connect(self.close)  # Закрываем приложение
    #     file_menu.addAction(exit_action)
        
    #     # Меню "Редактирование"
    #     edit_menu = menubar.addMenu('Правка')
        
    #     # Действие "Копировать"
    #     copy_action = QAction('Копировать', self)
    #     edit_menu.addAction(copy_action)

        
    
        


    