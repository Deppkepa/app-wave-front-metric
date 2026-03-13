import sys
from PyQt5.QtWidgets import *
from src.gui.Menu_bar_horizontal import menu_bar_horizontal
from src.controller.manager import manager
from src.gui.grid_subaperture import GridSubapertureView
from src.logic.model.model_image import model_image

#  Главное окно.

class app_w_f_metric(QMainWindow):
    __manager_logic:manager = manager
    __path_file:str = ""

    @property
    def path_file(self) -> str:
        return self.__path_file

    @path_file.setter
    def image(self, path: str):
        self.__path_file = path

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        lbl = QLabel('Hello World!', self)
        lbl.move(50, 50)  # Перемещаем лейбл на позицию (50, 50)
        menubar = self.menuBar()
        menu_bar_horizontal().setup_menu(menubar, self)
        

        # Создаём виджет с грид-сеткой
        # grid_widget = GridSubapertureView.create_grid(subapertures, rows=2, columns=2)

        # # Ставим виджет в центральное пространство окна
        # self.setCentralWidget(grid_widget)

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
            print(f"Выбран файл: {self.__path_file}")

            # Обращаемся к менеджеру для обработки данных
            processed_models = self.__manager_logic.process_date(filename)
            print(processed_models[0].row_col)
            grid_widget = GridSubapertureView.create_view(processed_models[0].subapertures, (500, 500))
            # print(processed_models[0])
            self.takeCentralWidget()
            self.setCentralWidget(grid_widget)
            
            
            
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