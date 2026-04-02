from PyQt5.QtGui import QPixmap, QImage

class Pixmap():

    @staticmethod
    def ndarray_to_pixmap(arr):
        
        height, width = arr.shape[:2]
        if arr.ndim == 2:
            format_qimage = QImage.Format_Grayscale8
            byte_count = width * arr.itemsize
        elif arr.ndim == 3 and arr.shape[-1] == 3:  # RGB изображение
            format_qimage = QImage.Format_RGB888
            byte_count = width * arr.itemsize * 3
        elif arr.ndim == 3 and arr.shape[-1] == 4:  # RGBA изображение
            format_qimage = QImage.Format_RGBA8888
            byte_count = width * arr.itemsize * 4
        else:
            raise ValueError("Неподдерживаемый формат изображения.")
        raw_bytes = arr.tobytes()
        qimg = QImage(raw_bytes, width, height, byte_count, format_qimage)
        return QPixmap.fromImage(qimg)