import sqlite3
import math
import numpy as np
import json
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QSlider,
                             QHBoxLayout, QPushButton, QLineEdit)
from PyQt5.QtCore import Qt, pyqtSlot
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.patches import Circle

class AnalysisReportWidget(QWidget):
    """Вкладка «Отчет анализа»: волновой фронт, наклоны (центроиды) и коэффициенты Цернике."""

    def __init__(self, db_path=None, file_id=None, parent=None):
        super().__init__(parent)
        self.db_path = db_path
        self.file_id = file_id
        self._frame_ids = []            # (frame_index, frame_id)
        self._total_frames = 0
        self._cached_matrices = {}      # frame_id -> (coeffs, rms)
        self._tilt_cache = {}           # frame_id -> (pos_x, pos_y, dx, dy)

        self._cbar_wavefront = None
        self._cbar_tilt = None

        self._init_ui()

        if self.file_id is not None:
            self.load_results()
        else:
            self._show_message("Файл не загружен")

    # ----------------------------------------------------------------------
    def _init_ui(self):
        main_layout = QVBoxLayout(self)

        self.info_label = QLabel("Нет данных")
        self.info_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.info_label)

        # Новая компоновка: 2 строки (верхняя – 2 графика, нижняя – 1 широкий)
        self.figure = Figure(figsize=(10, 8), tight_layout=True)
        self.canvas = FigureCanvas(self.figure)
        gs = self.figure.add_gridspec(2, 2, height_ratios=[1, 0.7])
        self.ax_wavefront = self.figure.add_subplot(gs[0, 0])   # левый верхний
        self.ax_tilt      = self.figure.add_subplot(gs[0, 1])   # правый верхний
        self.ax_bars      = self.figure.add_subplot(gs[1, :])   # вся нижняя строка

        canvas_layout = QHBoxLayout()
        canvas_layout.addStretch()
        canvas_layout.addWidget(self.canvas)
        canvas_layout.addStretch()
        main_layout.addLayout(canvas_layout)

        main_layout.addStretch()

        # Панель управления кадрами (как раньше)
        control_layout = QHBoxLayout()
        self.prev_btn = QPushButton("◀ Предыдущий")
        self.prev_btn.clicked.connect(self._prev_frame)
        self.frame_slider = QSlider(Qt.Horizontal)
        self.frame_slider.setMinimum(0)
        self.frame_slider.setMaximum(0)
        self.frame_slider.setEnabled(False)
        self.frame_slider.valueChanged.connect(self._on_slider_changed)
        self.next_btn = QPushButton("Следующий ▶")
        self.next_btn.clicked.connect(self._next_frame)
        self.frame_input = QLineEdit()
        self.frame_input.setFixedWidth(60)
        self.frame_input.setPlaceholderText("№")
        self.frame_input.returnPressed.connect(self._on_input_return)
        self.frame_index_label = QLabel("0 / 0")

        control_layout.addWidget(self.prev_btn)
        control_layout.addWidget(self.frame_slider, stretch=1)
        control_layout.addWidget(self.next_btn)
        control_layout.addWidget(self.frame_input)
        control_layout.addWidget(self.frame_index_label)

        control_container = QWidget()
        control_container.setLayout(control_layout)
        control_container.setContentsMargins(0, 0, 0, 10)
        main_layout.addWidget(control_container)

    # ----------------------------------------------------------------------
    def set_db_and_file(self, db_path, file_id):
        self.db_path = db_path
        self.file_id = file_id
        self.load_results()

    def load_results(self):
        if not self.db_path or self.file_id is None:
            self._show_message("Файл не загружен")
            return

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Есть ли результаты анализа?
            cursor.execute(
                "SELECT COUNT(*) FROM frames f "
                "JOIN frame_analysis_results r ON f.id = r.frame_id "
                "WHERE f.file_id = ?", (self.file_id,))
            count = cursor.fetchone()[0]

            if count == 0:
                self._show_message(
                    "Анализ ещё не проводился.\n"
                    "Нажмите кнопку «Сохранить для всех кадров»,\n"
                    "чтобы запустить C++ анализ."
                )
                conn.close()
                return

            # Список обработанных кадров
            cursor.execute(
                "SELECT f.frame_index, f.id FROM frames f "
                "JOIN frame_analysis_results r ON f.id = r.frame_id "
                "WHERE f.file_id = ? ORDER BY f.frame_index", (self.file_id,))
            self._frame_ids = cursor.fetchall()
            self._total_frames = len(self._frame_ids)

            # Кэширование коэффициентов и RMS
            self._cached_matrices.clear()
            for _, frame_id in self._frame_ids:
                cursor.execute("SELECT result_data FROM frame_analysis_results WHERE frame_id = ?", (frame_id,))
                row = cursor.fetchone()
                if row:
                    res = json.loads(row[0])
                    coeffs = np.array(res["coefficients"])
                    rms = res.get("rms", 0.0)
                    self._cached_matrices[frame_id] = (coeffs, rms)

            conn.close()

            # Настройка слайдера
            self.frame_slider.blockSignals(True)
            self.frame_slider.setMaximum(self._total_frames - 1)
            self.frame_slider.setValue(0)
            self.frame_slider.setEnabled(True)
            self.frame_slider.blockSignals(False)
            self.frame_input.setText("1")
            self.frame_input.setEnabled(True)
            self.prev_btn.setEnabled(True)
            self.next_btn.setEnabled(self._total_frames > 1)

            self._update_display(0)
        except Exception as e:
            self._show_message(f"Ошибка загрузки: {e}")

    def _show_message(self, text):
        self.info_label.setText(text)
        self.frame_slider.setMaximum(0)
        self.frame_slider.setEnabled(False)
        self.frame_input.setEnabled(False)
        self.prev_btn.setEnabled(False)
        self.next_btn.setEnabled(False)
        self.frame_index_label.setText("0 / 0")
        for ax in [self.ax_wavefront, self.ax_tilt, self.ax_bars]:
            ax.clear()
        self._remove_colorbars()
        self.canvas.draw()

    # ----------------------------------------------------------------------
    @pyqtSlot(int)
    def _on_slider_changed(self, idx):
        self._go_to_frame(idx)

    def _prev_frame(self):
        if self.frame_slider.value() > 0:
            self.frame_slider.setValue(self.frame_slider.value() - 1)

    def _next_frame(self):
        if self.frame_slider.value() < self.frame_slider.maximum():
            self.frame_slider.setValue(self.frame_slider.value() + 1)

    def _on_input_return(self):
        try:
            num = int(self.frame_input.text())
        except ValueError:
            return
        if 1 <= num <= self._total_frames:
            self._go_to_frame(num - 1)
        else:
            self.frame_input.setText(str(self.frame_slider.value() + 1))

    def _go_to_frame(self, slider_idx):
        self.frame_input.setText(str(slider_idx + 1))
        self.prev_btn.setEnabled(slider_idx > 0)
        self.next_btn.setEnabled(slider_idx < self._total_frames - 1)
        self.frame_slider.blockSignals(True)
        self.frame_slider.setValue(slider_idx)
        self.frame_slider.blockSignals(False)
        self._update_display(slider_idx)

    
    def invalidate_cache(self):
        """Очищает кэши отчёта, чтобы при следующем обновлении загрузить актуальные данные."""
        self._tilt_cache.clear()
    
    def invalidate_all_cache(self):
        """Полностью очищает все кэши отчёта."""
        self._tilt_cache.clear()
        self._cached_matrices.clear()
        
    # ----------------------------------------------------------------------
    def _load_tilt_data(self, frame_id):
        """Загружает центроиды для указанного frame_id и возвращает (pos_x, pos_y, dx, dy)."""
        if frame_id in self._tilt_cache:
            return self._tilt_cache[frame_id]

        pos_x, pos_y, dx, dy = [], [], [], []
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            query = ("""
                SELECT s.pos_x, s.width, s.pos_y, s.height, m.measurement_data 
                FROM subapertures s 
                JOIN subap_measurements m ON s.id = m.subaperture_id 
                WHERE s.frame_id = ? AND s.excluded = 0 AND s.is_valid = 1;
                """
            )
            cursor.execute(query, (frame_id,))
            rows = cursor.fetchall()
            print(f"[DEBUG] frame_id={frame_id}, rows found: {len(rows)}")
            for row in rows:
                px, sw, py, sh, meas_str = row
                meas = json.loads(meas_str)
                cx = meas["centroid_x"]
                cy = meas["centroid_y"]
                pos_x.append(px + sw / 2.0)
                pos_y.append(py + sh / 2.0)
                dx.append(cx - sw / 2.0)
                dy.append(cy - sh / 2.0)
            conn.close()
        except Exception as e:
            print(f"[DEBUG] _load_tilt_data error: {e}")

        data = (np.array(pos_x), np.array(pos_y), np.array(dx), np.array(dy))
        self._tilt_cache[frame_id] = data
        return data

    # ----------------------------------------------------------------------
    def _update_display(self, slider_idx):
        if not self._frame_ids or slider_idx >= len(self._frame_ids):
            return

        frame_index, frame_id = self._frame_ids[slider_idx]
        coeffs, rms = self._cached_matrices.get(frame_id, (None, None))
        if coeffs is None:
            self._show_message(f"Данные для кадра {frame_index} отсутствуют.")
            return

        self._remove_colorbars()

        # --- Волновой фронт ---
        self._draw_wavefront(self.ax_wavefront, coeffs,
                             f"Волновой фронт\nRMS = {rms:.3f} нм")

        # --- Тилт-карта (центроиды) ---
        pos_x, pos_y, dx, dy = self._load_tilt_data(frame_id)
        self._draw_tilt_map(self.ax_tilt, pos_x, pos_y, dx, dy,
                            f"Наклоны (центроиды)\nКадр {frame_index}")

        # --- Коэффициенты Цернике ---
        self.ax_bars.clear()
        idx = np.arange(1, len(coeffs) + 1)
        self.ax_bars.bar(idx, coeffs, color='steelblue')
        self.ax_bars.axhline(0, color='black', linewidth=0.8)
        self.ax_bars.set_title("Коэффициенты Цернике (амплитуда)")
        self.ax_bars.set_xlabel("Номер моды (j)")
        self.ax_bars.set_ylabel("Амплитуда, нм")
        self.ax_bars.set_xticks(idx)

        self.info_label.setText(f"Кадр {frame_index}  |  RMS = {rms:.4f} нм")
        self.frame_index_label.setText(f"{slider_idx + 1} / {self._total_frames}")
        self.canvas.draw()

    # ----------------------------------------------------------------------
    def _remove_colorbars(self):
        for attr in ['_cbar_wavefront', '_cbar_tilt']:
            cbar = getattr(self, attr, None)
            if cbar is not None:
                try:
                    cbar.remove()
                except AttributeError:
                    pass
                setattr(self, attr, None)
        for ax in self.figure.axes:
            if hasattr(ax, 'colorbar') and ax.colorbar is not None:
                try:
                    ax.colorbar.remove()
                except AttributeError:
                    pass

    def _draw_wavefront(self, ax, coeffs, title):
        ax.clear()
        size = 256
        y, x = np.mgrid[-1:1:size*1j, -1:1:size*1j]
        rho = np.sqrt(x**2 + y**2)
        theta = np.arctan2(y, x)
        mask = rho <= 1.0

        W = np.zeros_like(rho)
        for j in range(1, len(coeffs) + 1):
            Z = self._zernike_polar(j, rho, theta)
            W += coeffs[j-1] * Z
        W[~mask] = np.nan

        im = ax.imshow(W, extent=[-1, 1, -1, 1], origin='lower',
                       cmap='RdBu_r', interpolation='bilinear')
        self._cbar_wavefront = self.figure.colorbar(im, ax=ax, label='нм')
        ax.add_patch(Circle((0, 0), 1.0, fill=False, color='black', linewidth=1.5))
        ax.set_title(title)
        ax.set_xlabel("X (нормированная апертура)")
        ax.set_ylabel("Y (нормированная апертура)")
        ax.set_aspect('equal')

    def _draw_tilt_map(self, ax, pos_x, pos_y, dx, dy, title):
        ax.clear()
        if len(pos_x) == 0:
            ax.set_title(f"{title}\n(нет данных)")
            return

        amp = np.sqrt(dx**2 + dy**2)
        # Диагностика
        print(f"[TILT] {len(pos_x)} cells, "
            f"dx ∈ [{dx.min():.2f}, {dx.max():.2f}], "
            f"dy ∈ [{dy.min():.2f}, {dy.max():.2f}], "
            f"max amp = {amp.max():.2f} px")

        if amp.max() < 1e-9:
            ax.set_title(f"{title}\n(смещения нулевые)")
            return

        # Увеличиваем длину стрелок в 50 раз для наглядности
        scale_factor = 50.0
        quiver = ax.quiver(pos_x, pos_y,
                        dx * scale_factor, dy * scale_factor, amp,
                        cmap='plasma', scale=1.0, scale_units='xy',
                        angles='xy', width=0.004)
        self._cbar_tilt = self.figure.colorbar(quiver, ax=ax, label='Смещение, пиксели')
        ax.set_title(title)
        ax.set_xlabel("X (пиксели)")
        ax.set_ylabel("Y (пиксели)")
        ax.set_aspect('equal')
        ax.autoscale_view()
        ax.margins(0.1)

    # ----------------------------------------------------------------------
    @staticmethod
    def _zernike_polar(j, rho, theta):
        """Полином Цернике OSA/ANSI (j = 1..15)."""
        n_vals = [0, 1, 1, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 4]
        m_vals = [0, 1,-1, 0,-2, 2,-1, 1,-3, 3, 0, 2,-2, 4,-4]
        if j < 1 or j > len(n_vals):
            return np.zeros_like(rho)
        n = n_vals[j-1]
        m = m_vals[j-1]
        m_abs = abs(m)

        R = np.zeros_like(rho)
        for k in range((n - m_abs) // 2 + 1):
            coeff = ((-1)**k * math.factorial(n - k) /
                     (math.factorial(k) * math.factorial((n + m_abs)//2 - k) *
                      math.factorial((n - m_abs)//2 - k)))
            R += coeff * rho**(n - 2*k)

        if m == 0:
            return R
        elif m > 0:
            return R * np.cos(m * theta)
        else:
            return R * np.sin(m_abs * theta)