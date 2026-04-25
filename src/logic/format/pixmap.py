from PyQt5.QtGui import QPixmap, QImage
import numpy as np

class Pixmap():
    
    @staticmethod
    def preparing_qimage_parameters(arr: np.ndarray):
        if arr.size == 0:
            raise ValueError("Empty array provided.")
        if arr.ndim != 2:
            raise ValueError("Unsupported image format.")
        height, width = arr.shape[:2]
        format_qimage = QImage.Format_Grayscale8
        byte_count = width * arr.itemsize
        raw_bytes = arr.tobytes()
        return (raw_bytes, width, height, byte_count, format_qimage)

    @staticmethod
    def ndarray_to_pixmap(arr: np.ndarray):
        params = Pixmap.preparing_qimage_parameters(arr)
        raw_bytes, width, height, byte_count, format_qimage = params
        qimg = QImage(raw_bytes, width, height, byte_count, format_qimage)
        return QPixmap.fromImage(qimg)