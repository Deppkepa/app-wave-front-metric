# import os
# import sqlite3
# import numpy as np
# from typing import List, Optional, Tuple

# class SubapStorage:
#     """Единое хранилище для всех файлов: SQLite БД analysis.db."""
    
#     def __init__(self, base_dir: str = "analysis_jobs"):
#         self.base_dir = base_dir
#         self.db_path = None
#         self._conn = None
#         self._cursor = None

#     def init_db(self) -> str:
#         """
#         Создаёт (если отсутствует) папку base_dir и файл analysis.db,
#         а также все необходимые таблицы и индексы.
#         Возвращает путь к БД.
#         """
#         os.makedirs(self.base_dir, exist_ok=True)
#         self.db_path = os.path.join(self.base_dir, "analysis.db")
#         self._connect()
#         self._create_tables()
#         self._close()
#         return self.db_path

#     def _connect(self):
#         """Открывает соединение с БД."""
#         if self._conn is None:
#             self._conn = sqlite3.connect(self.db_path)
#             self._cursor = self._conn.cursor()

#     def _close(self):
#         """Закрывает соединение с БД."""
#         if self._conn:
#             self._conn.close()
#             self._conn = None
#             self._cursor = None

#     def _create_tables(self):
#         """Создаёт таблицы и индексы, если они ещё не созданы."""
#         # Таблица files
#         self._cursor.execute('''
#             CREATE TABLE IF NOT EXISTS files (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 original_path TEXT NOT NULL,
#                 file_hash TEXT NOT NULL UNIQUE,
#                 file_size INTEGER,
#                 last_modified TIMESTAMP,
#                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#                 updated_at TIMESTAMP
#             )
#         ''')
#         # Таблица frames
#         self._cursor.execute('''
#             CREATE TABLE IF NOT EXISTS frames (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 file_id INTEGER NOT NULL,
#                 frame_index INTEGER NOT NULL,
#                 image_width INTEGER NOT NULL,
#                 image_height INTEGER NOT NULL,
#                 grid_rows INTEGER NOT NULL,
#                 grid_cols INTEGER NOT NULL,
#                 archive_path TEXT,                 -- новая колонка
#                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#                 UNIQUE(file_id, frame_index),
#                 FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
#             )
#         ''')
#         # Таблица subapertures
#         self._cursor.execute('''
#             CREATE TABLE IF NOT EXISTS subapertures (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 frame_id INTEGER NOT NULL,
#                 grid_col INTEGER NOT NULL,
#                 grid_row INTEGER NOT NULL,
#                 file_path TEXT,
#                 width INTEGER NOT NULL,
#                 height INTEGER NOT NULL,
#                 pos_x INTEGER NOT NULL,
#                 pos_y INTEGER NOT NULL,
#                 excluded INTEGER DEFAULT 0,
#                 is_valid INTEGER DEFAULT 0,
#                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#                 UNIQUE(frame_id, grid_col, grid_row),
#                 FOREIGN KEY (frame_id) REFERENCES frames(id) ON DELETE CASCADE
#             )
#         ''')
        
#         self._cursor.execute('''
#             CREATE TABLE IF NOT EXISTS analysis_methods (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 method_name TEXT NOT NULL UNIQUE,
#                 version TEXT DEFAULT '1.0',
#                 description TEXT,
#                 default_params TEXT
#             );
#         ''')
        
#         self._cursor.execute('''
#             CREATE TABLE IF NOT EXISTS subap_measurements (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 subaperture_id INTEGER NOT NULL,
#                 method_id INTEGER NOT NULL,
#                 measurement_data TEXT NOT NULL,
#                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#                 UNIQUE(subaperture_id, method_id),
#                 FOREIGN KEY (subaperture_id) REFERENCES subapertures(id) ON DELETE CASCADE,
#                 FOREIGN KEY (method_id) REFERENCES analysis_methods(id) ON DELETE CASCADE
#             );             
#         ''')
        
#         self._cursor.execute('''
#             CREATE TABLE IF NOT EXISTS frame_analysis_results (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 frame_id INTEGER NOT NULL,
#                 method_id INTEGER NOT NULL,
#                 result_data TEXT NOT NULL,
#                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#                 UNIQUE(frame_id, method_id),
#                 FOREIGN KEY (frame_id) REFERENCES frames(id) ON DELETE CASCADE,
#                 FOREIGN KEY (method_id) REFERENCES analysis_methods(id) ON DELETE CASCADE
#             );          
#         ''')
#         # Индексы
#         self._cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_hash ON files(file_hash)")
#         self._cursor.execute("CREATE INDEX IF NOT EXISTS idx_frames_file_id ON frames(file_id)")
#         self._cursor.execute("CREATE INDEX IF NOT EXISTS idx_sub_frame_id ON subapertures(frame_id)")
        
#         # Индексы для быстрого поиска
#         self._cursor.execute("CREATE INDEX IF NOT EXISTS idx_subap_meas_subap ON subap_measurements(subaperture_id)")
#         self._cursor.execute("CREATE INDEX IF NOT EXISTS idx_subap_meas_method ON subap_measurements(method_id)")
#         self._cursor.execute("CREATE INDEX IF NOT EXISTS idx_frame_res_frame ON frame_analysis_results(frame_id)")
#         self._cursor.execute("CREATE INDEX IF NOT EXISTS idx_frame_res_method ON frame_analysis_results(method_id)")

#         # Предварительное наполнение метода Цернике, если его ещё нет
#         self._cursor.execute("INSERT OR IGNORE INTO analysis_methods (method_name, version, description, default_params) VALUES (?, ?, ?, ?)",
#                             ("zernike_polynomials", "1.0",
#                             "Wavefront reconstruction via Zernike polynomials up to 4th order",
#                             '{"max_order": 4, "normalization_radius": 1.0}'))
#         self._conn.commit()

#     # --- Работа с таблицей files ---
    
        
    

#     def insert_file(self, path: str, file_hash: str, size: int, mtime: float) -> int:
#         self._connect()
#         self._cursor.execute('''
#             INSERT INTO files (original_path, file_hash, file_size, last_modified)
#             VALUES (?, ?, ?, ?)
#         ''', (path, file_hash, size, mtime))
#         self._conn.commit()
#         file_id = self._cursor.lastrowid
#         self._close()
#         return file_id
    
#     def get_frame_id(self, file_id: int, frame_index: int) -> int:
#         self._connect()
#         self._cursor.execute("SELECT id FROM frames WHERE file_id = ? AND frame_index = ?", (file_id, frame_index))
#         row = self._cursor.fetchone()
#         self._close()
#         if row is None:
#             raise RuntimeError(f"Нет записи в frames для file_id={file_id}, frame_index={frame_index}")
#         return row[0]
    
#     def get_file_id(self, file_hash: str):
#         self._connect()
#         self._cursor.execute("SELECT id FROM files WHERE file_hash = ?", (file_hash,))
#         row = self._cursor.fetchone()
#         self._close()
#         return row[0] if row else None


#     def update_file_path(self, file_id: int, new_path: str, mtime: float):
#         self._connect()
#         self._cursor.execute("UPDATE files SET original_path = ?, last_modified = ? WHERE id = ?",
#                              (new_path, mtime, file_id))
#         self._conn.commit()
#         self._close()
        
#     def update_frame_archive_path(self, frame_id: int, archive_path: str):
#         """Обновляет поле archive_path в таблице frames."""
#         self._connect()
#         self._cursor.execute("UPDATE frames SET archive_path = ? WHERE id = ?", (archive_path, frame_id))
#         self._conn.commit()
#         self._close()

#     # def save_frame_archive(self, frame_id: int, archive_path: str, sub_arrays: list, meta_data: list):
#     #     """
#     #     Сохраняет субапертуры кадра в один .npz архив и обновляет archive_path в БД.
#     #     sub_arrays: список 2D массивов субапертур.
#     #     meta_data: список кортежей (col, row, x, y, w, h, excluded) для каждой субапертуры.
#     #     """
#     #     # Сохраняем архив
#     #     np.savez(archive_path, subapertures=np.array(sub_arrays, dtype=object), metadata=np.array(meta_data, dtype=object))
#     #     # Обновляем запись в frames
#     #     self.update_frame_archive_path(frame_id, archive_path)
    
#     def save_frame_archive(self, frame_id: int, archive_path: str, sub_arrays: list, meta_data: list):
#         """
#         Сохраняет субапертуры кадра в один .npz архив и обновляет archive_path в БД.
#         sub_arrays: список 2D массивов субапертур (все должны быть одинакового размера!)
#         meta_data: список кортежей (col, row, x, y, w, h, excluded) для каждой субапертуры.
#         """
#         if not sub_arrays:
#             return
        
#         # Проверяем, что все субапертуры одинакового размера
#         shapes = [arr.shape for arr in sub_arrays]
#         first_shape = shapes[0]
#         if not all(s == first_shape for s in shapes):
#             # Если размеры разные, дополняем нулями до максимального
#             max_h = max(s[0] for s in shapes)
#             max_w = max(s[1] for s in shapes)
#             padded = []
#             for arr in sub_arrays:
#                 pad_h = max_h - arr.shape[0]
#                 pad_w = max_w - arr.shape[1]
#                 padded_arr = np.pad(arr, ((0, pad_h), (0, pad_w)), mode='constant', constant_values=0)
#                 padded.append(padded_arr)
#             sub_array_3d = np.stack(padded, axis=0)
#         else:
#             # Все одинаковые – просто стек
#             sub_array_3d = np.stack(sub_arrays, axis=0)
        
#         # Сохраняем как непрерывный uint8 массив
#         np.savez(archive_path, 
#                 subapertures=sub_array_3d.astype(np.uint8), 
#                 metadata=np.array(meta_data, dtype=np.int32))
        
#         self.update_frame_archive_path(frame_id, archive_path)

#     def update_cells_status(self, frame_id: int, valid_set: set, excluded_set: set, file_paths: dict = None):
#         """
#         Обновляет is_valid и excluded для ячеек кадра. file_paths опционален (для совместимости).
#         """
#         self._connect()
#         try:
#             # Сброс excluded для всех ячеек кадра
#             self._cursor.execute("UPDATE subapertures SET excluded = 0 WHERE frame_id = ?", (frame_id,))
#             # Установка is_valid=1 для валидных
#             for col, row in valid_set:
#                 self._cursor.execute("""
#                     UPDATE subapertures SET is_valid = 1
#                     WHERE frame_id = ? AND grid_col = ? AND grid_row = ?
#                 """, (frame_id, col, row))
#             # Установка excluded=1 для выбранных
#             for col, row in excluded_set:
#                 self._cursor.execute("""
#                     UPDATE subapertures SET excluded = 1
#                     WHERE frame_id = ? AND grid_col = ? AND grid_row = ?
#                 """, (frame_id, col, row))
#             # Обновление file_path (если переданы)
#             if file_paths:
#                 for (col, row), path in file_paths.items():
#                     self._cursor.execute("""
#                         UPDATE subapertures SET file_path = ?
#                         WHERE frame_id = ? AND grid_col = ? AND grid_row = ?
#                     """, (path, frame_id, col, row))
#             self._conn.commit()
#         finally:
#             self._close()

#     # --- Методы для работы с frames и subapertures (будут использоваться при сохранении анализа) ---
#     # Они должны открывать/закрывать соединение при каждом вызове
#     # ...

#     def close(self):
#         self._close()
        
#     def get_archive_path(self, frame_id: int) -> Optional[str]:
#         """Возвращает archive_path для данного frame_id."""
#         self._connect()
#         self._cursor.execute("SELECT archive_path FROM frames WHERE id = ?", (frame_id,))
#         row = self._cursor.fetchone()
#         self._close()
#         return row[0] if row else None

#     def is_frame_ready(self, file_id: int, frame_index: int) -> bool:
#         """Проверяет, существует ли уже архив для кадра."""
#         try:
#             frame_id = self.get_frame_id(file_id, frame_index)
#             arch = self.get_archive_path(frame_id)
#             return arch is not None and os.path.exists(arch)
#         except RuntimeError:
#             return False

#     def clear_valid_status(self, frame_id: int):
#         """Сбрасывает is_valid=0 для всех ячеек кадра (используется при переподготовке)."""
#         self._connect()
#         self._cursor.execute("UPDATE subapertures SET is_valid = 0 WHERE frame_id = ?", (frame_id,))
#         self._conn.commit()
#         self._close()
        
#     def get_or_create_frame(self, file_id: int, frame_index: int, image_width: int, image_height: int, grid_rows: int, grid_cols: int) -> int:
#         """
#         Возвращает id записи в таблице frames для указанного file_id и frame_index.
#         Если запись отсутствует, создаёт её.
#         """
#         self._connect()
#         try:
#             self._cursor.execute("SELECT id FROM frames WHERE file_id = ? AND frame_index = ?", (file_id, frame_index))
#             row = self._cursor.fetchone()
#             if row:
#                 return row[0]
#             self._cursor.execute('''
#                 INSERT INTO frames (file_id, frame_index, image_width, image_height, grid_rows, grid_cols)
#                 VALUES (?, ?, ?, ?, ?, ?)
#             ''', (file_id, frame_index, image_width, image_height, grid_rows, grid_cols))
#             self._conn.commit()
#             return self._cursor.lastrowid
#         finally:
#             self._close()
#     def update_excluded_for_all_frames(self, file_id: int, excluded_set: set):
#         """
#         Обновляет флаг excluded для всех субапертур указанного файла.
#         excluded_set: множество (col, row) ячеек, которые должны быть исключены.
#         """
#         self._connect()
#         try:
#             # 1. Сбросить excluded=0 для всех субапертур этого файла
#             self._cursor.execute("""
#                 UPDATE subapertures SET excluded = 0
#                 WHERE frame_id IN (SELECT id FROM frames WHERE file_id = ?)
#             """, (file_id,))
#             # 2. Установить excluded=1 для выбранных ячеек (для всех кадров)
#             if excluded_set:
#                 # Строим условие: (grid_col, grid_row) IN ((0,0), (1,2), ...)
#                 placeholders = ','.join(['(?,?)'] * len(excluded_set))
#                 params = []
#                 for col, row in excluded_set:
#                     params.extend([col, row])
#                 self._cursor.execute(f"""
#                     UPDATE subapertures SET excluded = 1
#                     WHERE frame_id IN (SELECT id FROM frames WHERE file_id = ?)
#                     AND (grid_col, grid_row) IN ({placeholders})
#                 """, (file_id, *params))
#             self._conn.commit()
#         finally:
#             self._close()
   
#     def get_method_id(self, method_name: str) -> int:
#         """Возвращает id метода по имени."""
#         self._connect()
#         self._cursor.execute("SELECT id FROM analysis_methods WHERE method_name = ?", (method_name,))
#         row = self._cursor.fetchone()
#         self._close()
#         if not row:
#             raise ValueError(f"Метод '{method_name}' не зарегистрирован в БД")
#         return row[0]

#     def insert_subap_measurement(self, subaperture_id: int, method_id: int, measurement_data: dict):
#         """Вставляет или обновляет измерения одной субапертуры."""
#         import json
#         data_json = json.dumps(measurement_data)
#         self._connect()
#         self._cursor.execute('''
#             INSERT OR REPLACE INTO subap_measurements
#             (subaperture_id, method_id, measurement_data)
#             VALUES (?, ?, ?)
#         ''', (subaperture_id, method_id, data_json))
#         self._conn.commit()
#         self._close()

#     def insert_frame_analysis_result(self, frame_id: int, method_id: int, result_data: dict):
#         """Сохраняет итоговый результат анализа кадра."""
#         import json
#         data_json = json.dumps(result_data)
#         self._connect()
#         self._cursor.execute('''
#             INSERT OR REPLACE INTO frame_analysis_results
#             (frame_id, method_id, result_data)
#             VALUES (?, ?, ?)
#         ''', (frame_id, method_id, data_json))
#         self._conn.commit()
#         self._close()

import os
import sqlite3
import numpy as np
import json
from typing import Optional, Dict

class SubapStorage:
    """Единое хранилище для всех файлов: SQLite БД analysis.db.
       Все публичные методы открывают отдельное соединение и закрывают его,
       что делает класс безопасным для использования в разных потоках."""

    def __init__(self, base_dir: str = "analysis_jobs"):
        self.base_dir = base_dir
        self.db_path = None   # будет установлен после init_db

    def init_db(self) -> str:
        """Создаёт папку и файл БД, таблицы и индексы. Вызывается один раз."""
        os.makedirs(self.base_dir, exist_ok=True)
        self.db_path = os.path.join(self.base_dir, "analysis.db")
        conn = sqlite3.connect(self.db_path, timeout=10)
        try:
            with conn:
                conn.executescript(self._get_schema())
        finally:
            conn.close()
        return self.db_path

    def _get_schema(self) -> str:
        return """
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_path TEXT NOT NULL,
            file_hash TEXT NOT NULL UNIQUE,
            file_size INTEGER,
            last_modified TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS frames (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id INTEGER NOT NULL,
            frame_index INTEGER NOT NULL,
            image_width INTEGER NOT NULL,
            image_height INTEGER NOT NULL,
            grid_rows INTEGER NOT NULL,
            grid_cols INTEGER NOT NULL,
            archive_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(file_id, frame_index),
            FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS subapertures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            frame_id INTEGER NOT NULL,
            grid_col INTEGER NOT NULL,
            grid_row INTEGER NOT NULL,
            file_path TEXT,
            width INTEGER NOT NULL,
            height INTEGER NOT NULL,
            pos_x INTEGER NOT NULL,
            pos_y INTEGER NOT NULL,
            excluded INTEGER DEFAULT 0,
            is_valid INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(frame_id, grid_col, grid_row),
            FOREIGN KEY (frame_id) REFERENCES frames(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS analysis_methods (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            method_name TEXT NOT NULL UNIQUE,
            version TEXT DEFAULT '1.0',
            description TEXT,
            default_params TEXT
        );

        CREATE TABLE IF NOT EXISTS subap_measurements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subaperture_id INTEGER NOT NULL,
            method_id INTEGER NOT NULL,
            measurement_data TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(subaperture_id, method_id),
            FOREIGN KEY (subaperture_id) REFERENCES subapertures(id) ON DELETE CASCADE,
            FOREIGN KEY (method_id) REFERENCES analysis_methods(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS frame_analysis_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            frame_id INTEGER NOT NULL,
            method_id INTEGER NOT NULL,
            result_data TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(frame_id, method_id),
            FOREIGN KEY (frame_id) REFERENCES frames(id) ON DELETE CASCADE,
            FOREIGN KEY (method_id) REFERENCES analysis_methods(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_files_hash ON files(file_hash);
        CREATE INDEX IF NOT EXISTS idx_frames_file_id ON frames(file_id);
        CREATE INDEX IF NOT EXISTS idx_sub_frame_id ON subapertures(frame_id);
        CREATE INDEX IF NOT EXISTS idx_subap_meas_subap ON subap_measurements(subaperture_id);
        CREATE INDEX IF NOT EXISTS idx_subap_meas_method ON subap_measurements(method_id);
        CREATE INDEX IF NOT EXISTS idx_frame_res_frame ON frame_analysis_results(frame_id);
        CREATE INDEX IF NOT EXISTS idx_frame_res_method ON frame_analysis_results(method_id);

        INSERT OR IGNORE INTO analysis_methods (method_name, version, description, default_params)
        VALUES ('zernike_polynomials', '1.0',
                'Wavefront reconstruction via Zernike polynomials up to 4th order',
                '{"max_order": 4, "normalization_radius": 1.0}');
        """

    def _connect(self):
        """Открывает новое соединение с БД (для внутреннего использования в методах)."""
        return sqlite3.connect(self.db_path, timeout=10)

    # --- Существующие файл/фреймы ---
    def insert_file(self, path: str, file_hash: str, size: int, mtime: float) -> int:
        conn = self._connect()
        try:
            with conn:
                cur = conn.execute(
                    "INSERT INTO files (original_path, file_hash, file_size, last_modified) VALUES (?,?,?,?)",
                    (path, file_hash, size, mtime))
                return cur.lastrowid
        finally:
            conn.close()

    def get_file_id(self, file_hash: str):
        conn = self._connect()
        try:
            cur = conn.execute("SELECT id FROM files WHERE file_hash = ?", (file_hash,))
            row = cur.fetchone()
            return row[0] if row else None
        finally:
            conn.close()

    def update_file_path(self, file_id: int, new_path: str, mtime: float):
        conn = self._connect()
        try:
            with conn:
                conn.execute("UPDATE files SET original_path=?, last_modified=? WHERE id=?",
                             (new_path, mtime, file_id))
        finally:
            conn.close()

    def get_or_create_frame(self, file_id: int, frame_index: int,
                            image_width: int, image_height: int,
                            grid_rows: int, grid_cols: int) -> int:
        conn = self._connect()
        try:
            cur = conn.execute("SELECT id FROM frames WHERE file_id=? AND frame_index=?",
                               (file_id, frame_index))
            row = cur.fetchone()
            if row:
                return row[0]
            cur = conn.execute(
                "INSERT INTO frames (file_id, frame_index, image_width, image_height, grid_rows, grid_cols) "
                "VALUES (?,?,?,?,?,?)",
                (file_id, frame_index, image_width, image_height, grid_rows, grid_cols))
            conn.commit()
            return cur.lastrowid
        finally:
            conn.close()

    def get_frame_id(self, file_id: int, frame_index: int) -> int:
        conn = self._connect()
        try:
            cur = conn.execute("SELECT id FROM frames WHERE file_id=? AND frame_index=?",
                               (file_id, frame_index))
            row = cur.fetchone()
            if row is None:
                raise RuntimeError(f"Нет записи frames для file_id={file_id}, frame_index={frame_index}")
            return row[0]
        finally:
            conn.close()

    def update_frame_archive_path(self, frame_id: int, archive_path: str):
        conn = self._connect()
        try:
            with conn:
                conn.execute("UPDATE frames SET archive_path=? WHERE id=?", (archive_path, frame_id))
        finally:
            conn.close()

    def get_archive_path(self, frame_id: int) -> Optional[str]:
        conn = self._connect()
        try:
            cur = conn.execute("SELECT archive_path FROM frames WHERE id=?", (frame_id,))
            row = cur.fetchone()
            return row[0] if row else None
        finally:
            conn.close()

    def is_frame_ready(self, file_id: int, frame_index: int) -> bool:
        try:
            fid = self.get_frame_id(file_id, frame_index)
            arch = self.get_archive_path(fid)
            return arch is not None and os.path.exists(arch)
        except RuntimeError:
            return False

    def save_frame_archive(self, frame_id: int, archive_path: str,
                           sub_arrays: list, meta_data: list):
        if not sub_arrays:
            return
        shapes = [arr.shape for arr in sub_arrays]
        first_shape = shapes[0]
        if not all(s == first_shape for s in shapes):
            max_h = max(s[0] for s in shapes)
            max_w = max(s[1] for s in shapes)
            padded = []
            for arr in sub_arrays:
                pad_h = max_h - arr.shape[0]
                pad_w = max_w - arr.shape[1]
                padded_arr = np.pad(arr, ((0, pad_h), (0, pad_w)), mode='constant', constant_values=0)
                padded.append(padded_arr)
            sub_3d = np.stack(padded, axis=0)
        else:
            sub_3d = np.stack(sub_arrays, axis=0)
        np.savez(archive_path, subapertures=sub_3d.astype(np.uint8),
                 metadata=np.array(meta_data, dtype=np.int32))
        self.update_frame_archive_path(frame_id, archive_path)

    def update_cells_status(self, frame_id: int, valid_set: set, excluded_set: set,
                            file_paths: dict = None):
        conn = self._connect()
        try:
            with conn:
                for col, row in valid_set:
                    conn.execute("UPDATE subapertures SET is_valid=1 WHERE frame_id=? AND grid_col=? AND grid_row=?",
                                 (frame_id, col, row))
                conn.execute("UPDATE subapertures SET excluded=0 WHERE frame_id=? AND is_valid = 1", (frame_id,))
                for col, row in excluded_set:
                    conn.execute("UPDATE subapertures SET excluded=1 WHERE frame_id=? AND grid_col=? AND grid_row=?",
                                 (frame_id, col, row))
                if file_paths:
                    for (col, row), path in file_paths.items():
                        conn.execute("UPDATE subapertures SET file_path=? WHERE frame_id=? AND grid_col=? AND grid_row=?",
                                     (path, frame_id, col, row))
        finally:
            conn.close()

    def update_excluded_for_all_frames(self, file_id: int, excluded_set: set):
        conn = self._connect()
        try:
            with conn:
                conn.execute(
                    "UPDATE subapertures SET excluded=0 WHERE frame_id IN (SELECT id FROM frames WHERE file_id=?) AND is_valid = 1",
                    (file_id,))
                if excluded_set:
                    placeholders = ','.join(['(?,?)'] * len(excluded_set))
                    params = []
                    for col, row in excluded_set:
                        params.extend([col, row])
                    conn.execute(
                        f"UPDATE subapertures SET excluded=1 "
                        f"WHERE frame_id IN (SELECT id FROM frames WHERE file_id=?) "
                        f"AND (grid_col, grid_row) IN ({placeholders})",
                        (file_id, *params))
        finally:
            conn.close()

    # --- Методы для анализа ---
    def get_method_id(self, method_name: str) -> int:
        conn = self._connect()
        try:
            cur = conn.execute("SELECT id FROM analysis_methods WHERE method_name=?", (method_name,))
            row = cur.fetchone()
            if not row:
                raise ValueError(f"Метод '{method_name}' не зарегистрирован")
            return row[0]
        finally:
            conn.close()

    def insert_subap_measurement(self, subaperture_id: int, method_id: int,
                                 measurement_data: dict):
        conn = self._connect()
        try:
            with conn:
                conn.execute(
                    "INSERT OR REPLACE INTO subap_measurements (subaperture_id, method_id, measurement_data) "
                    "VALUES (?,?,?)",
                    (subaperture_id, method_id, json.dumps(measurement_data)))
        finally:
            conn.close()

    def insert_frame_analysis_result(self, frame_id: int, method_id: int,
                                     result_data: dict):
        conn = self._connect()
        try:
            with conn:
                conn.execute(
                    "INSERT OR REPLACE INTO frame_analysis_results (frame_id, method_id, result_data) "
                    "VALUES (?,?,?)",
                    (frame_id, method_id, json.dumps(result_data)))
        finally:
            conn.close()

    def get_excluded_cells_for_frame(self, file_id: int, frame_index: int) -> list:
        """Возвращает список (col, row) исключённых ячеек для указанного кадра."""
        conn = self._connect()
        try:
            cur = conn.execute(
                "SELECT grid_col, grid_row FROM subapertures "
                "WHERE frame_id = (SELECT id FROM frames WHERE file_id = ? AND frame_index = ?) "
                "AND excluded = 1",
                (file_id, frame_index)
            )
            return [(row[0], row[1]) for row in cur.fetchall()]
        finally:
            conn.close()
    
    def has_excluded_cells_for_file(self, file_id: int) -> bool:
        conn = self._connect()
        try:
            cur = conn.execute(
                "SELECT COUNT(*) FROM subapertures "
                "WHERE frame_id IN (SELECT id FROM frames WHERE file_id = ?) "
                "AND excluded = 1", (file_id,)
            )
            row = cur.fetchone()
            return row[0] > 0
        finally:
            conn.close()
    def exclude_invalid_cells(self, frame_id: int):
        """Помечает все невалидные ячейки (is_valid=0) как исключённые."""
        conn = self._connect()
        try:
            with conn:
                conn.execute(
                    "UPDATE subapertures SET excluded = 1 WHERE frame_id = ? AND is_valid = 0",
                    (frame_id,)
                )
        finally:
            conn.close()
            
    
    def get_invalid_cells(self, file_id: int, frame_index: int) -> list:
        """Возвращает (col, row) всех невалидных ячеек для указанного кадра."""
        conn = self._connect()
        try:
            cur = conn.execute(
                "SELECT grid_col, grid_row FROM subapertures "
                "WHERE frame_id = (SELECT id FROM frames WHERE file_id = ? AND frame_index = ?) "
                "AND is_valid = 0",
                (file_id, frame_index)
            )
            return [(row[0], row[1]) for row in cur.fetchall()]
        finally:
            conn.close()

    def reset_excluded_to_invalid(self, file_id: int):
        """Для всех кадров файла: сбрасывает excluded=0 валидным, excluded=1 невалидным."""
        conn = self._connect()
        try:
            with conn:
                conn.execute(
                    "UPDATE subapertures SET excluded = (CASE WHEN is_valid = 0 THEN 1 ELSE 0 END) "
                    "WHERE frame_id IN (SELECT id FROM frames WHERE file_id = ?)",
                    (file_id,)
                )
        finally:
            conn.close()