# Класс реализующий верхнее меню
from PyQt5.QtWidgets import *

class menu_bar_horizontal():
    
    __path_file:str = ""

    # def create(self):
    #     menubar = self.menuBar()
    #     return menubar

    
    def setup_menu(self, menubar, parent):

        # меню файл
        file_menu = menubar.addMenu('Файл')
        self.setup_option_new(file_menu, parent)
        self.setup_option_open(file_menu, parent)
        self.setup_option_save(file_menu, parent)
        self.setup_option_save_as(file_menu, parent)
        self.setup_option_close(file_menu, parent)
        self.setup_option_exit(file_menu, parent)

        # меню правка
        edit_menu = menubar.addMenu('Правка')
        self.setup_option_copy(edit_menu, parent)
        
    
    def setup_option_new(self, file_menu, parent):
        # Действие "Новый"
        open_action = QAction('Новый', parent)
        open_action.triggered.connect(parent.new_file)  # Подключаем обработчик события
        file_menu.addAction(open_action)  
        

    def setup_option_open(self, file_menu, parent):
        # Действие "Открыть файл"
        open_action = QAction('Открыть', parent)
        open_action.triggered.connect(parent.open_file)  # Подключаем обработчик события
        file_menu.addAction(open_action)  

    def setup_option_save(self, file_menu, parent):
        # Действие "Сохранить файл"
        open_action = QAction('Сохранить', parent)
        open_action.triggered.connect(parent.save_file)  # Подключаем обработчик события
        file_menu.addAction(open_action)

    def setup_option_save_as(self, file_menu, parent):
        # Действие "сохранить как"
        open_action = QAction('Сохранить как', parent)
        open_action.triggered.connect(parent.save_as_file)  # Подключаем обработчик события
        file_menu.addAction(open_action)  
    
    def setup_option_close(self, file_menu, parent):
        # Действие "Закрыть файл"
        open_action = QAction('Закрыть файл', parent)
        open_action.triggered.connect(parent.close_file)  # Подключаем обработчик события
        file_menu.addAction(open_action) 

    def setup_option_exit(self, file_menu, parent):
        # Действие "Выход"
        open_action = QAction('Выход', parent)
        open_action.triggered.connect(parent.close)  # Подключаем обработчик события
        file_menu.addAction(open_action) 

    def setup_option_copy(self, edit_menu, parent):

        # Действие "Копировать"
        copy_action = QAction('Копировать', parent)
        copy_action.triggered.connect(parent.copy_text)
        edit_menu.addAction(copy_action)
   
    

    