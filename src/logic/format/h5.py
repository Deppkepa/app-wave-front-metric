import h5py, os, hashlib
from pathlib import Path
import numpy as np

class H5ReaderError(Exception):
    pass

class CountKeyError(H5ReaderError):
    pass

class FileAccessError(Exception):
    pass

# --- Новый класс для ленивого чтения (только по индексу) ---
class H5LazyReader:
    def __init__(self, file_path: str):
        self._path = Path(file_path).resolve()
        self._f = None
        self._key = None
        self._num_images = None
        self._image_shape = None

    def _ensure_open(self):
        if self._f is None:
            if not self._path.is_file():
                raise FileAccessError(f"File not found: {self._path}")
            self._f = h5py.File(self._path, 'r')
            keys = list(self._f.keys())
            if len(keys) == 0:
                raise H5ReaderError("No keys in file")
            if len(keys) > 1:
                raise CountKeyError(f"Expected 1 key, got {keys}")
            self._key = keys[0]
            shape = self._f[self._key].shape
            if len(shape) != 3 or shape[0] <= 0 or shape[1] <= 0 or shape[2] <= 0:
                raise H5ReaderError(f"Invalid shape {shape}, expected (N, H, W)")
            self._num_images = shape[0]
            self._image_shape = shape[1:]

    @property
    def num_images(self) -> int:
        self._ensure_open()
        return self._num_images

    @property
    def image_shape(self) -> tuple:
        self._ensure_open()
        return self._image_shape

    def get_image(self, index: int) -> np.ndarray:
        self._ensure_open()
        if index < 0 or index >= self.num_images:
            raise IndexError(f"Index {index} out of range (0..{self.num_images-1})")
        return self._f[self._key][index]

    def compute_hash(self) -> str:
        """
        Вычисляет идентификатор HDF5 файла на основе:
        - размера файла,
        - количества кадров,
        - формы изображения,
        - первых 4096 байт первого кадра.
        Возвращает шестнадцатеричную строку MD5.
        """
        self._ensure_open()  # убедимся, что файл открыт
    
        size = os.path.getsize(self._path)
        num_frames = self.num_images
        h, w = self.image_shape
        first_frame = self.get_image(0)
        frame_bytes = first_frame.tobytes()
        sample = frame_bytes[:4096]
        
        md5 = hashlib.md5()
        md5.update(str(size).encode())
        md5.update(str(num_frames).encode())
        md5.update(str(h).encode())
        md5.update(str(w).encode())
        md5.update(sample)
        return md5.hexdigest()
    
    def close(self):
        if self._f is not None:
            self._f.close()
            self._f = None

    def __enter__(self):
        self._ensure_open()
        return self

    def __exit__(self, *args):
        self.close()
        
    

