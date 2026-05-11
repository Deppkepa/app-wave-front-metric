import subprocess
import os
from PyQt5.QtCore import QThread, pyqtSignal

class AnalysisThread(QThread):
    progress = pyqtSignal(int, int)   # current, total
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, db_path: str, file_id: int, method_name: str = "zernike_polynomials",
                 start_frame=0, end_frame=None):
        super().__init__()
        self.db_path = db_path
        self.file_id = file_id
        self.method_name = method_name
        self.start_frame = start_frame
        self.end_frame = end_frame if end_frame is not None else 1000000
        self._cancel = False

    def cancel(self):
        self._cancel = True

    def run(self):
        exe_path = os.path.join(os.getcwd(), "src", "logic", "analyze", "analyze.exe")
        print("DEBUG: exe_path =", exe_path)
        if not os.path.exists(exe_path):
            self.error.emit(f"analyze.exe не найден по пути {exe_path}")
            return
        db_abs = os.path.abspath(self.db_path)
        exe_abs = os.path.abspath(exe_path)
        cmd = [
            exe_abs,
            "--db", db_abs,
            "--file-id", str(self.file_id),
            "--method", self.method_name,
            "--start-frame", str(self.start_frame),
            "--end-frame", str(self.end_frame)
        ]
        print("DEBUG: команда запуска:", cmd)
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                text=True, encoding='utf-8')
        while True:
            if self._cancel:
                proc.terminate()
                self.error.emit("Анализ отменён пользователем")
                return
            line = proc.stdout.readline()
            if not line and proc.poll() is not None:
                break
            line = line.strip()
            if line.startswith("PROGRESS"):
                parts = line.split()
                if len(parts) == 2:
                    cur_str, total_str = parts[1].split('/')
                    self.progress.emit(int(cur_str), int(total_str))
        stderr_out = proc.stderr.read()
        if proc.returncode != 0:
            self.error.emit(f"Ошибка анализа (код {proc.returncode}): {stderr_out}")
        else:
            self.finished.emit()