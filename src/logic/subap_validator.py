import numpy as np
import cv2

class SubapValidator:
    def __init__(self, threshold=0.5):
        self._spot_template = None
        self._contours = None
        self.threshold = threshold

    def set_contours(self, contours: dict):
        """Устанавливает контуры сетки (необходимо для определения валидных ячеек кадра)."""
        self._contours = contours

    def set_template_from_synthetic(self, size=15, sigma=3):
        """Создаёт синтетический эталон (гауссово пятно)."""
        ax = np.linspace(-(size-1)/2, (size-1)/2, size)
        x, y = np.meshgrid(ax, ax)
        gauss = np.exp(-(x**2 + y**2) / (2 * sigma**2))
        gauss = (gauss / gauss.max() * 255).astype(np.uint8)
        self._spot_template = gauss

    def set_template_from_real(self, img: np.ndarray, num_cols: int, num_rows: int, margin=2):
        """
        Создаёт эталон из реальных центральных ячеек изображения.
        img: полное изображение (первый кадр)
        num_cols, num_rows: размеры сетки (количество ячеек по горизонтали и вертикали)
        margin: сколько ячеек отступить от края (чтобы брать только те, где гарантированно есть пятно)
        """
        if self._contours is None:
            raise RuntimeError("Сначала установите контуры через set_contours()")
        xs = self._contours['x']
        ys = self._contours['y']
        max_w = self._contours['max_width']
        max_h = self._contours['max_height']
        templates = []
        for row in range(margin, num_rows - margin):
            y = ys[row]
            for col in range(margin, num_cols - margin):
                x = xs[col]
                if col == 0:
                    w = xs[1] - x - 5
                else:
                    w = max_w
                if row == 0:
                    h = ys[1] - y - 5
                else:
                    h = max_h
                if w <= 0 or h <= 0:
                    continue
                if y + h > img.shape[0] or x + w > img.shape[1]:
                    continue
                sub = img[y:y+h, x:x+w]
                if sub.dtype == np.uint16:
                    sub = (sub / 256).astype(np.uint8)
                mean = np.mean(sub)
                std = np.std(sub)
                if std > 1e-6:
                    norm_sub = (sub - mean) / std
                else:
                    norm_sub = sub - mean
                templates.append(norm_sub)
        if not templates:
            self.set_template_from_synthetic()
            return
        avg = np.mean(templates, axis=0)
        avg = (avg - avg.min()) / (avg.max() - avg.min()) * 255
        self._spot_template = avg.astype(np.uint8)

    def has_spot(self, sub_img: np.ndarray) -> bool:
        """Проверяет, содержит ли одна субапертура пятно (корреляция с эталоном)."""
        if self._spot_template is None:
            raise RuntimeError("Эталон не установлен. Вызовите set_template_from_synthetic() или set_template_from_real()")
        if sub_img.dtype == np.uint16:
            sub_img = (sub_img / 256).astype(np.uint8)
        h, w = sub_img.shape
        th, tw = self._spot_template.shape
        if h < th or w < tw:
            tpl = cv2.resize(self._spot_template, (w, h))
        else:
            tpl = self._spot_template
        result = cv2.matchTemplate(sub_img, tpl, cv2.TM_CCOEFF_NORMED)
        return np.max(result) > self.threshold

    def determine_valid_cells(self, img: np.ndarray) -> set:
        """
        Возвращает множество (col, row) валидных ячеек для данного изображения.
        """
        if self._contours is None:
            raise RuntimeError("Сначала установите контуры через set_contours()")
        xs = self._contours['x']
        ys = self._contours['y']
        max_w = self._contours['max_width']
        max_h = self._contours['max_height']
        valid = set()
        for row, y in enumerate(ys[:-1]):
            for col, x in enumerate(xs[:-1]):
                if col == 0:
                    w = xs[1] - x - 5
                else:
                    w = max_w
                if row == 0:
                    h = ys[1] - y - 5
                else:
                    h = max_h
                if w <= 0 or h <= 0:
                    continue
                if y + h > img.shape[0] or x + w > img.shape[1]:
                    continue
                sub = img[y:y+h, x:x+w]
                if self.has_spot(sub):
                    valid.add((col, row))
        return valid