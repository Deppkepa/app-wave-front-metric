from PyQt5.QtCore import QThread, pyqtSignal
from src.controller.manager import Manager

class LoaderThread(QThread):
    finished = pyqtSignal(object)   # manager
    error = pyqtSignal(str)
    progress = pyqtSignal(int, int)  # текущее значение, максимум

    def __init__(self, file_path: str):
        super().__init__()
        self.file_path = file_path
        self._is_canceled = False
        

    def cancel(self):
        self._is_canceled = True

    def run(self):
        try:
            manager = Manager(cache_size=10)   # кэш 10 QPixmap
            def report_progress(current, total):
                print(current, total)
                self.progress.emit(current, total)
            total = manager.open_file(self.file_path, progress_callback=report_progress)
            if self._is_canceled:
                manager.close()
                return
            self.finished.emit(manager)
        except Exception as e:
            self.error.emit(str(e))