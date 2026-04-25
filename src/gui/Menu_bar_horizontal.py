# Класс реализующий верхнее меню
from PyQt5.QtWidgets import *
from PyQt5.QtCore import pyqtSignal, QObject

class MenuBarHorizontal(QObject):

    signal_file_open = pyqtSignal()
    signal_file_new = pyqtSignal()
    signal_file_save = pyqtSignal()
    signal_file_save_as = pyqtSignal()
    signal_file_close = pyqtSignal()
    signal_file_exit = pyqtSignal()
    signal_edit_copy = pyqtSignal()

    def setup_menu(self, menubar):

        # --- Меню "Файл" ---
        file_menu = menubar.addMenu('Файл')
        self._create_action(file_menu, 'Новый', 'Ctrl+N', self.signal_file_new)
        file_menu.addSeparator()
        self._create_action(file_menu, 'Открыть', 'Ctrl+O', self.signal_file_open)
        self._create_action(file_menu, 'Сохранить', 'Ctrl+S', self.signal_file_save)
        self._create_action(file_menu, 'Сохранить как...', None, self.signal_file_save_as)
        file_menu.addSeparator()
        self._create_action(file_menu, 'Закрыть файл', None, self.signal_file_close)
        self._create_action(file_menu, 'Выход', 'Ctrl+Q', self.signal_file_exit)

        # --- Меню "Правка" ---
        edit_menu = menubar.addMenu('Правка')
        self._create_action(edit_menu, 'Копировать', 'Ctrl+C', self.signal_edit_copy)


    def _create_action(self, menu, text, shortcut, signal_to_emit):
        action = QAction(text, menu.parent())
        if shortcut:
            action.setShortcut(shortcut)
        # Когда пользователь нажмет кнопку, меню само испустит сигнал.
        action.triggered.connect(signal_to_emit.emit)
        menu.addAction(action)
    

    