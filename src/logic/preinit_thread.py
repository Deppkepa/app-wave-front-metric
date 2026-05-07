# src/logic/preinit_thread.py
import sqlite3
from PyQt5.QtCore import QThread, pyqtSignal

class PreinitThread(QThread):
    progress = pyqtSignal(int, int)   # текущий кадр, всего

    def __init__(self, db_path: str, file_id: int, contours: dict,
                 total_frames: int, image_width: int, image_height: int):
        super().__init__()
        self.db_path = db_path
        self.file_id = file_id
        self.contours = contours
        self.total = total_frames
        self.image_width = image_width
        self.image_height = image_height
        self._cancel = False

    def cancel(self):
        self._cancel = True

    def run(self):
        conn = sqlite3.connect(self.db_path, timeout=10)
        cursor = conn.cursor()
        # Убедимся, что таблицы существуют (можно вызвать создание, если нужно)
        # но они уже должны быть созданы главным потоком

        xs = self.contours['x']
        ys = self.contours['y']
        max_w = self.contours.get('max_width', 0)
        max_h = self.contours.get('max_height', 0)
        num_cols = len(xs) - 1
        num_rows = len(ys) - 1

        # Получаем уже обработанные frame_index для этого file_id
        cursor.execute("SELECT frame_index FROM frames WHERE file_id = ?", (self.file_id,))
        processed_frames = {row[0] for row in cursor.fetchall()}

        for idx in range(self.total):
            if self._cancel:
                break
            if idx in processed_frames:
                continue

            try:
                # Вставляем frame
                cursor.execute('''
                    INSERT INTO frames (file_id, frame_index, image_width, image_height, grid_rows, grid_cols)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (self.file_id, idx, self.image_width, self.image_height, num_rows, num_cols))
                frame_id = cursor.lastrowid

                # Вставляем все ячейки для этого кадра
                rows = []
                for row_idx, y in enumerate(ys[:-1]):
                    for col_idx, x in enumerate(xs[:-1]):
                        if col_idx == 0:
                            w = xs[1] - x - 5
                        else:
                            w = max_w
                        if row_idx == 0:
                            h = ys[1] - y - 5
                        else:
                            h = max_h
                        rows.append((frame_id, col_idx, row_idx, x, y, w, h))

                cursor.executemany('''
                    INSERT INTO subapertures
                    (frame_id, grid_col, grid_row, pos_x, pos_y, width, height, is_valid, file_path, excluded)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 0, NULL, 0)
                ''', rows)

                # Коммитим раз в 100 кадров для производительности
                if idx % 100 == 0:
                    conn.commit()
                    self.progress.emit(idx + 1, self.total)

            except sqlite3.Error as e:
                print(f"Ошибка при вставке кадра {idx}: {e}")
                # Можно откатить транзакцию, но проще продолжить
                conn.rollback()
                continue

        conn.commit()
        conn.close()
        self.progress.emit(self.total, self.total)