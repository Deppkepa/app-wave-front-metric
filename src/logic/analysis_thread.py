# import subprocess
# import os
# from PyQt5.QtCore import QThread, pyqtSignal

# class AnalysisThread(QThread):
#     progress = pyqtSignal(int, int)   # current, total
#     finished = pyqtSignal()
#     error = pyqtSignal(str)

#     def __init__(self, db_path: str, file_id: int, method_name: str = "zernike_polynomials",
#                  start_frame=0, end_frame=None):
#         super().__init__()
#         self.db_path = db_path
#         self.file_id = file_id
#         self.method_name = method_name
#         self.start_frame = start_frame
#         self.end_frame = end_frame if end_frame is not None else 1000000
#         self._cancel = False

#     def cancel(self):
#         self._cancel = True

#     def run(self):
#         exe_path = os.path.join(os.getcwd(), "src", "logic", "analyze", "analyze.exe")
#         print("DEBUG: exe_path =", exe_path)
#         if not os.path.exists(exe_path):
#             self.error.emit(f"analyze.exe не найден по пути {exe_path}")
#             return
#         db_abs = os.path.abspath(self.db_path)
#         exe_abs = os.path.abspath(exe_path)
#         cmd = [
#             exe_abs,
#             "--db", db_abs,
#             "--file-id", str(self.file_id),
#             "--method", self.method_name,
#             "--start-frame", str(self.start_frame),
#             "--end-frame", str(self.end_frame)
#         ]
#         print("DEBUG: команда запуска:", cmd)
#         proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
#                                 text=True, encoding='utf-8')
#         while True:
#             if self._cancel:
#                 proc.terminate()
#                 self.error.emit("Анализ отменён пользователем")
#                 return
#             line = proc.stdout.readline()
#             if not line and proc.poll() is not None:
#                 break
#             line = line.strip()
#             if line.startswith("PROGRESS"):
#                 parts = line.split()
#                 if len(parts) == 2:
#                     cur_str, total_str = parts[1].split('/')
#                     self.progress.emit(int(cur_str), int(total_str))
#         stderr_out = proc.stderr.read()
#         if proc.returncode != 0:
#             self.error.emit(f"Ошибка анализа (код {proc.returncode}): {stderr_out}")
#         else:
#             self.finished.emit()

import subprocess
import os
import sqlite3
import multiprocessing as mp
from PyQt5.QtCore import QThread, pyqtSignal
from queue import Queue
import threading

class AnalysisThread(QThread):
    progress = pyqtSignal(int, int)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, db_path: str, file_id: int, method_name: str = "zernike_polynomials"):
        super().__init__()
        self.db_path = db_path
        self.file_id = file_id
        self.method_name = method_name
        self._cancel = False
        self._processes = []
        self._total_frames = 0

    def cancel(self):
        self._cancel = True
        for proc in self._processes:
            if proc.poll() is None:
                proc.terminate()

    # def _get_frame_range(self):
    #     """Возвращает (min_frame_index, max_frame_index) для данного файла."""
    #     conn = sqlite3.connect(self.db_path)
    #     cur = conn.execute(
    #         "SELECT MIN(frame_index), MAX(frame_index) FROM frames WHERE file_id=?",
    #         (self.file_id,)
    #     )
    #     min_f, max_f = cur.fetchone()
    #     conn.close()
    #     if min_f is None or max_f is None:
    #         return None, None
    #     return min_f, max_f

    # def _split_ranges(self):
    #     """Разбивает реальный диапазон кадров на части по числу ядер."""
    #     min_idx, max_idx = self._get_frame_range()
    #     if min_idx is None:
    #         return []

    #     total_frames = max_idx - min_idx + 1
    #     self._total_frames = total_frames

    #     # Количество процессов = число ядер, но не больше количества кадров
    #     num_workers = min(mp.cpu_count(), total_frames)
    #     if num_workers == 0:
    #         return []

    #     chunk_size = max(1, total_frames // num_workers)
    #     ranges = []
    #     current = min_idx
    #     for i in range(num_workers):
    #         if current > max_idx:
    #             break
    #         end = min(current + chunk_size - 1, max_idx)
    #         ranges.append((current, end))
    #         current = end + 1
    #     return ranges

    def _get_existing_frame_indices(self):
        """Возвращает список frame_index, для которых есть archive_path, отсортированный по возрастанию."""
        conn = sqlite3.connect(self.db_path)
        cur = conn.execute(
            "SELECT frame_index FROM frames WHERE file_id=? AND archive_path IS NOT NULL ORDER BY frame_index",
            (self.file_id,)
        )
        indices = [row[0] for row in cur.fetchall()]
        #print(f"DEBUG: {indices}")
        conn.close()
        return indices
    
    def _split_indices(self, indices):
        """
        Разбивает список индексов на части (каждая часть – непрерывный подсписок исходного списка)
        по числу ядер CPU. Возвращает список кортежей (start_frame, end_frame) для каждого процесса.
        Гарантирует, что каждый процесс получит хотя бы один кадр (если всего кадров не меньше ядер).
        """
        total_frames = len(indices)
        self._total_frames = total_frames
        if total_frames == 0:
            return []
        num_workers = min(mp.cpu_count(), total_frames) # кол-во ядер, 12
        chunk_size = max(1, total_frames // num_workers + 1) # максимальное, между 1 и кол-во изображений делённое нацело на кол-во ядер + 1
        ranges = []
        for i in range(num_workers):
            start = i * chunk_size
            end = min(start + chunk_size, total_frames) - 1
            if start <= end:
                ranges.append((indices[start],indices[end]))
            
        print(f"DEBUG ranges: {ranges}")
        print(f"DEBUG total_frames: {total_frames}")
        print(f"DEBUG num_workers: {num_workers}")
        print(f"DEBUG chunk_size: {chunk_size}")
        return ranges
        #return [(0,799),(800,1599),(1600,2399),(2400,3199),(3200,3999),(4000,4799),(4800,5599),(5600,6399)]#ranges

    def run(self):
        exe_path = os.path.join(os.getcwd(), "src", "logic", "analyze", "analyze.exe")
        if not os.path.exists(exe_path):
            self.error.emit(f"analyze.exe не найден по пути {exe_path}")
            return

        # ranges = self._split_ranges()
        # if not ranges:
        #     self.error.emit("Нет кадров для анализа")
        #     return
        indices = self._get_existing_frame_indices()
        if not indices:
            self.error.emit("Нет кадров с архивом для анализа")
            return

        ranges = self._split_indices(indices)

        # Добавить эту строку:
        # self.progress.emit(0, self._total_frames)
        progress_queue = Queue()

        def read_output(proc, queue):
            for line in iter(proc.stdout.readline, ''):
                if line.startswith("PROGRESS"):
                    queue.put(1)
            proc.wait()
            queue.put(None)

        self._processes = []
        for s, e in ranges:
            cmd = [
                exe_path,
                "--db", os.path.abspath(self.db_path),
                "--file-id", str(self.file_id),
                "--method", self.method_name,
                "--start-frame", str(s),
                "--end-frame", str(e)
            ]
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    text=True, encoding='utf-8')
            self._processes.append(proc)
            t = threading.Thread(target=read_output, args=(proc, progress_queue))
            t.daemon = True
            t.start()

        processed = 0
        finished = 0
        errors = []
        last_emit = 0

        while finished < len(self._processes):
            try:
                val = progress_queue.get(timeout=0.5)
                if val is None:
                    finished += 1
                else:
                    processed += val
                    if processed - last_emit >= 5 or processed == self._total_frames:
                        self.progress.emit(processed, self._total_frames)
                        last_emit = processed
            except:
                pass

            if self._cancel:
                for p in self._processes:
                    if p.poll() is None:
                        p.terminate()
                break

        for p in self._processes:
            ret = p.wait()
            if ret != 0:
                stderr = p.stderr.read()
                errors.append(f"Процесс {p.pid} завершился с кодом {ret}: {stderr}")

        if errors:
            self.error.emit("\n".join(errors))
        elif not self._cancel:
            self.progress.emit(self._total_frames, self._total_frames)
            self.finished.emit()