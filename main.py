# Точка входа
import sys

from src.gui.app import app_w_f_metric
from PyQt5.QtWidgets import QApplication

def main():
    app = QApplication(sys.argv)
    window = app_w_f_metric()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()