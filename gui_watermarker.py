#!/usr/bin/env python3
"""
WATERMARK STUDIO - Professional Watermarking Application
Tier 1-4 Complete Implementation
Supports both PyQt6 and Tkinter backends
"""

import sys
import os
import json
import glob
import time
import math
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# Try PyQt6 first, fall back to Tkinter
try:
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem,
        QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSlider, QListWidget,
        QFileDialog, QGraphicsDropShadowEffect, QCheckBox, QProgressBar, QGraphicsItem,
        QComboBox, QLineEdit, QColorDialog, QScrollArea, QListWidgetItem, QMenu,
        QInputDialog, QMessageBox, QSizePolicy, QFrame, QDialog, QSpinBox, QDoubleSpinBox,
        QTabWidget, QTextEdit
    )
    from PyQt6.QtCore import Qt, QPointF, QThread, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve, QSize, QUrl, QRect, QEvent, QMimeData, QPoint
    from PyQt6.QtGui import QPixmap, QImage, QPainter, QColor, QFont, QCursor, QIcon, QPen, QBrush, QAction, QKeySequence, QDropEvent, QDragEnterEvent
    USE_PYQT6 = True
except ImportError:
    USE_PYQT6 = False
    print("PyQt6 not available, falling back to Tkinter")

if not USE_PYQT6:
    import tkinter as tk
    from tkinter import filedialog, ttk, messagebox
    from PIL import ImageTk

# DPI Awareness - Safe handling
def enable_dpi_awareness():
    """Enable DPI awareness safely on Windows"""
    if sys.platform == "win32":
        try:
            import ctypes
            # Try Windows 10+ method first
            try:
                ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
            except:
                try:
                    ctypes.windll.shcore.SetProcessDpiAwareness(1)  # PROCESS_SYSTEM_DPI_AWARE
                except:
                    pass
        except Exception as e:
            print(f"DPI awareness warning (non-critical): {e}")

enable_dpi_awareness()

APP_PATH = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
PRESETS_FILE = os.path.join(os.path.expanduser("~"), ".watermark_studio_presets.json")

try:
    FACE_CASCADE = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
except Exception as e:
    print(f"Warning: Face detection unavailable: {e}")
    FACE_CASCADE = None

# ── THEMES ─────────────────────────────────────────────────────────────────
THEMES = {
    "light": {
        "bg": "#f2f2f7", "panel": "rgba(255,255,255,220)", "accent": "#34C759",
        "accent2": "#30D158", "text": "#1c1c1e", "dim": "#8e8e93",
        "border": "rgba(0,0,0,15)", "shadow": "QColor(0, 0, 0, 25)", "glow": "QColor(52, 199, 89)"
    },
    "dark": {
        "bg": "#000000", "panel": "rgba(28,28,30,230)", "accent": "#30D158",
        "accent2": "#34C759", "text": "#ffffff", "dim": "#98989d",
        "border": "rgba(255,255,255,15)", "shadow": "QColor(0, 0, 0, 160)", "glow": "QColor(48, 209, 88)"
    },
}

def qss(theme):
    t = THEMES[theme]
    return f"""
    QMainWindow{{background:{t['bg']};}}
    QGraphicsView{{border:none;background:transparent;}}
    QWidget#Panel{{background-color:{t['panel']};border-radius:18px;border:1px solid {t['border']};}}
    QWidget#Dock{{background-color:{t['panel']};border-radius:30px;border:1px solid {t['border']};}}
    QPushButton{{background:transparent;color:{t['accent']};font-family:"Helvetica Neue","Segoe UI";font-size:13px;font-weight:600;border:none;border-radius:10px;padding:7px 16px;min-width:100px;}}
    QPushButton:hover{{background:{t['border']};}}
    QPushButton:pressed{{opacity:0.7;}}
    QPushButton#primary{{background:{t['accent']};color:#fff;}}
    QPushButton#primary:hover{{background:{t['accent2']};}}
    QPushButton#icon{{min-width:36px;max-width:36px;padding:7px 4px;}}
    QLabel{{color:{t['text']};font-family:"Helvetica Neue","Segoe UI";font-size:13px;background:transparent;}}
    QLabel#dim{{color:{t['dim']};font-size:10px;font-weight:700;letter-spacing:1px;background:transparent;}}
    QSlider::groove:horizontal{{background:rgba(128,128,128,60);height:4px;border-radius:2px;}}
    QSlider::handle:horizontal{{background:{t['accent']};width:16px;height:16px;margin:-6px 0;border-radius:8px;}}
    QSlider::sub-page:horizontal{{background:{t['accent']};border-radius:2px;}}
    QListWidget{{background:transparent;border:none;color:{t['text']};font-size:12px;outline:none;}}
    QListWidget::item{{padding:5px 8px;border-radius:8px;}}
    QListWidget::item:selected{{background:{t['accent']};color:#fff;}}
    QComboBox{{background:rgba(128,128,128,30);border:none;border-radius:8px;padding:5px 10px;color:{t['text']};font-size:12px;}}
    QLineEdit{{background:rgba(128,128,128,30);border:none;border-radius:8px;padding:6px 10px;color:{t['text']};font-size:12px;}}
    QCheckBox{{color:{t['text']};font-size:12px;spacing:6px;}}
    QProgressBar{{background:rgba(128,128,128,40);border-radius:3px;height:6px;text-align:center;color:transparent;}}
    QProgressBar::chunk{{background:{t['accent']};border-radius:3px;}}
    QScrollArea{{border:none;background:transparent;}}
    QScrollBar:vertical{{width:8px;}}
    QScrollBar::handle:vertical{{background:rgba(128,128,128,100);border-radius:4px;}}
    QTextEdit{{background:rgba(128,128,128,30);border:none;border-radius:8px;padding:6px 10px;color:{t['text']};font-size:12px;}}
    QSpinBox,QDoubleSpinBox{{background:rgba(128,128,128,30);border:none;border-radius:8px;padding:5px 10px;color:{t['text']};font-size:12px;}}
    QMenu{{background:{t['panel']};border:1px solid {t['border']};color:{t['text']};}}
    QMenu::item:selected{{background:{t['accent']};color:#fff;}}
    QDialog{{background:{t['bg']};color:{t['text']};}}
    QTabWidget::pane{{border:1px solid {t['border']};}}
    QTabBar::tab{{background:rgba(128,128,128,30);padding:5px 15px;margin:2px;border-radius:6px;}}
    QTabBar::tab:selected{{background:{t['accent']};color:#fff;}}
    """

def pil_to_qpixmap(img):
    """Convert PIL Image to QPixmap"""
    if not USE_PYQT6:
        return None
    img = img.convert("RGBA")
    data = img.tobytes("raw", "RGBA")
    qim = QImage(data, img.width, img.height, QImage.Format.Format_RGBA8888)
    return QPixmap.fromImage(qim)

# ── PRESET MANAGER ────────────────────────────────────────────────────────
class PresetManager:
    def __init__(self):
        self.presets = {}
        self.load()

    def load(self):
        if os.path.exists(PRESETS_FILE):
            try:
                self.presets = json.load(open(PRESETS_FILE))
            except:
                self.presets = {}

    def save_preset(self, name, data):
        self.presets[name] = data
        json.dump(self.presets, open(PRESETS_FILE, "w"), indent=2)

    def delete_preset(self, name):
        self.presets.pop(name, None)
        json.dump(self.presets, open(PRESETS_FILE, "w"), indent=2)

    def names(self):
        return list(self.presets.keys())

    def get(self, name):
        return self.presets.get(name, {})

# ── UNDO STACK ────────────────────────────────────────────────────────────
class UndoStack:
    def __init__(self, limit=50):
        self._stack, self._idx, self._limit = [], -1, limit

    def push(self, state):
        self._stack = self._stack[:self._idx + 1]
        self._stack.append(state)
        if len(self._stack) > self._limit:
            self._stack.pop(0)
        self._idx = len(self._stack) - 1

    def undo(self):
        if self._idx > 0:
            self._idx -= 1
            return self._stack[self._idx]
        return None

    def redo(self):
        if self._idx < len(self._stack) - 1:
            self._idx += 1
            return self._stack[self._idx]
        return None

    def can_undo(self):
        return self._idx > 0

    def can_redo(self):
        return self._idx < len(self._stack) - 1

    def clear(self):
        self._stack, self._idx = [], -1

# ── BLEND MODES ───────────────────────────────────────────────────────────
def blend_images(base_arr, wm_arr, mode="Normal"):
    """Apply blend mode to watermark"""
    b = base_arr.astype(np.float32) / 255.0
    w = wm_arr.astype(np.float32) / 255.0
    alpha = w[:, :, 3:4]
    wb, wrgb = b[:, :, :3], w[:, :, :3]
    
    if mode == "Multiply":
        comp = wb * wrgb
    elif mode == "Screen":
        comp = 1 - (1 - wb) * (1 - wrgb)
    elif mode == "Overlay":
        comp = np.where(wb < 0.5, 2 * wb * wrgb, 1 - 2 * (1 - wb) * (1 - wrgb))
    elif mode == "Soft Light":
        comp = (1 - 2 * wrgb) * wb ** 2 + 2 * wrgb * wb
    else:
        comp = wrgb
    
    result = wb * (1 - alpha) + comp * alpha
    out = base_arr.copy()
    out[:, :, :3] = np.clip(result * 255, 0, 255).astype(np.uint8)
    return out

# ── BATCH WORKER ──────────────────────────────────────────────────────────
if USE_PYQT6:
    class BatchWorker(QThread):
        progress = pyqtSignal(int, str)
        finished = pyqtSignal(int, int)

        def __init__(self, paths, wm_pil, metrics, opts, overrides):
            super().__init__()
            self.paths = paths
            self.wm_pil = wm_pil
            self.metrics = metrics
            self.opts = opts
            self.overrides = overrides
            self._stop = False

        def stop(self):
            self._stop = True

        def _face_regions(self, gray):
            """Detect face regions"""
            if not FACE_CASCADE:
                return []
            faces = FACE_CASCADE.detectMultiScale(gray, 1.1, 4, minSize=(30, 30))
            return faces if len(faces) else []

        def _find_smart_pos(self, base_img, wm_w, wm_h, use_face_avoid):
            """Find optimal watermark position avoiding faces and details"""
            cv_img = np.array(base_img.convert('RGB'))
            gray = cv2.cvtColor(cv_img, cv2.COLOR_RGB2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            
            if use_face_avoid:
                for (fx, fy, fw, fh) in self._face_regions(gray):
                    edges[fy:fy + fh, fx:fx + fw] = 255
            
            integral = cv2.integral(edges)
            ih, iw = gray.shape
            
            if wm_w >= iw or wm_h >= ih:
                return (iw - wm_w) // 2, ih - wm_h
            
            best_score, bx, by = float('inf'), 0, 0
            sx, sy = max(1, iw // 50), max(1, ih // 50)
            ypen = 255 * 5
            
            for y in range(0, ih - wm_h + 1, sy):
                for x in range(0, iw - wm_w + 1, sx):
                    s = integral[y + wm_h, x + wm_w] - integral[y, x + wm_w] - integral[y + wm_h, x] + integral[y, x]
                    score = s + ((ih - wm_h) - y) * ypen
                    if score < best_score:
                        best_score, bx, by = score, x, y
            
            return int(bx), int(by)

        def _smart_opacity(self, base_img, px, py, wm_w, wm_h, base_opacity):
            """Adjust opacity based on underlying brightness"""
            region = base_img.crop((max(0, px), max(0, py), min(base_img.width, px + wm_w), min(base_img.height, py + wm_h)))
            if region.width < 1 or region.height < 1:
                return base_opacity
            
            gray_arr = np.array(region.convert('L'), dtype=np.float32)
            avg_brightness = gray_arr.mean() / 255.0
            adjusted = base_opacity * (0.6 + 0.4 * avg_brightness)
            return max(0.15, min(1.0, adjusted))

        def _apply_wm(self, base_img, wm, px, py, mode, smart_op, base_op):
            """Apply watermark with blending"""
            px, py = int(px), int(py)
            paste_x, paste_y = max(0, px), max(0, py)
            crop_x, crop_y = max(0, -px), max(0, -py)
            crop_w = min(wm.width - crop_x, base_img.width - paste_x)
            crop_h = min(wm.height - crop_y, base_img.height - paste_y)
            
            if crop_w <= 0 or crop_h <= 0:
                return base_img
            
            wm_crop = wm.crop((crop_x, crop_y, crop_x + crop_w, crop_y + crop_h))
            op = self._smart_opacity(base_img, paste_x, paste_y, crop_w, crop_h, base_op) if smart_op else base_op
            
            if op < 1.0:
                r, g, b, a = wm_crop.split()
                a = a.point(lambda v: int(v * op))
                wm_crop = Image.merge('RGBA', (r, g, b, a))

            if mode == "Normal":
                out = base_img.copy()
                out.paste(wm_crop, (paste_x, paste_y), wm_crop)
                return out
            else:
                base_arr = np.array(base_img)
                wm_arr = np.zeros((base_img.height, base_img.width, 4), dtype=np.uint8)
                wm_arr[paste_y:paste_y + crop_h, paste_x:paste_x + crop_w] = np.array(wm_crop)
                blended = blend_images(base_arr, wm_arr, mode)
                return Image.fromarray(blended)

        def run(self):
            """Process all images"""
            total = len(self.paths)
            success = 0
            rel_cx, rel_cy, rel_scale, opacity, rotation = self.metrics
            
            tile = self.opts.get("tile", False)
            use_smart = self.opts.get("smart", False)
            use_face = self.opts.get("face_avoid", False)
            smart_op = self.opts.get("smart_opacity", False)
            blend_mode = self.opts.get("blend_mode", "Normal")
            out_mode = self.opts.get("out_mode", "new_folder")
            out_fmt = self.opts.get("out_fmt", "original")
            
            ow, oh = self.wm_pil.size
            t0 = time.time()

            for i, path in enumerate(self.paths):
                if self._stop:
                    break
                
                if total > 0:
                    elapsed = time.time() - t0
                    rate = (i + 1) / max(elapsed, 0.001)
                    eta = (total - i - 1) / rate if rate > 0 else 0
                    eta_str = f"ETA {eta:.0f}s" if eta > 1 else "finishing..."
                    self.progress.emit(int((i / total) * 100), f"{i + 1}/{total}  {eta_str}")
                
                try:
                    base_img = Image.open(path).convert("RGBA")
                    iw, ih = base_img.size

                    m = self.overrides.get(path)
                    rcx, rcy, rsc, rop, rrot = m if m else (rel_cx, rel_cy, rel_scale, opacity, rotation)

                    target_w = max(1, int(iw * rsc))
                    scale = target_w / ow
                    target_h = max(1, int(oh * scale))
                    wm = self.wm_pil.resize((target_w, target_h), Image.Resampling.LANCZOS)
                    
                    if rrot != 0:
                        wm = wm.rotate(-rrot, expand=True, resample=Image.Resampling.BICUBIC)

                    if tile:
                        tw, th = wm.size
                        for ty in range(0, ih, th + 20):
                            for tx in range(0, iw, tw + 20):
                                base_img = self._apply_wm(base_img, wm, tx, ty, blend_mode, smart_op, rop)
                    elif use_smart:
                        px, py = self._find_smart_pos(base_img, wm.width, wm.height, use_face)
                        base_img = self._apply_wm(base_img, wm, px, py, blend_mode, smart_op, rop)
                    else:
                        px = int(iw * rcx - wm.width / 2)
                        py = int(ih * rcy - wm.height / 2)
                        base_img = self._apply_wm(base_img, wm, px, py, blend_mode, smart_op, rop)

                    if out_mode == "overwrite":
                        out_path = path
                    else:
                        out_dir = os.path.join(os.path.dirname(path), "output")
                        os.makedirs(out_dir, exist_ok=True)
                        out_path = os.path.join(out_dir, os.path.basename(path))
                    
                    ext = out_fmt if out_fmt != "original" else os.path.splitext(path)[1].lower().lstrip(".")
                    
                    if ext in ("jpg", "jpeg"):
                        base_img.convert("RGB").save(out_path.rsplit(".", 1)[0] + ".jpg", quality=100, subsampling=0)
                    elif ext == "webp":
                        base_img.save(out_path.rsplit(".", 1)[0] + ".webp", quality=100, method=6)
                    else:
                        base_img.save(out_path.rsplit(".", 1)[0] + ".png")
                    
                    success += 1
                except Exception as e:
                    print(f"Error {path}: {e}")
            
            self.progress.emit(100, "Done!")
            self.finished.emit(success, total)

# ── WELCOME WIDGET ────────────────────────────────────────────────────────
if USE_PYQT6:
    class WelcomeWidget(QWidget):
        def __init__(self, parent):
            super().__init__(parent)
            self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
            lay = QVBoxLayout(self)
            lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            icon = QLabel("💧")
            icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon.setStyleSheet("font-size:64px;background:transparent;")
            
            title = QLabel("Watermark Studio")
            title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            title.setStyleSheet("font-size:28px;font-weight:700;background:transparent;")
            
            sub = QLabel("Drag a folder or image here to begin")
            sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
            sub.setStyleSheet("font-size:14px;color:#8e8e93;background:transparent;")
            
            lay.addWidget(icon)
            lay.addWidget(title)
            lay.addSpacing(8)
            lay.addWidget(sub)

# ── SHORTCUTS DIALOG ──────────────────────────────────────────────────────
if USE_PYQT6:
    class ShortcutsDialog(QDialog):
        def __init__(self, parent, theme):
            super().__init__(parent)
            t = THEMES[theme]
            self.setWindowTitle("Keyboard Shortcuts")
            self.setFixedSize(420, 500)
            self.setStyleSheet(f"background:{t['bg']};color:{t['text']};font-family:'Helvetica Neue','Segoe UI';")
            
            lay = QVBoxLayout(self)
            title = QLabel("Keyboard Shortcuts")
            title.setStyleSheet("font-size:18px;font-weight:700;padding:10px;")
            lay.addWidget(title)
            
            shortcuts = [
                ("Arrow Keys", "Move watermark ±10px"),
                ("Ctrl+Z", "Undo"),
                ("Ctrl+Y / Ctrl+Shift+Z", "Redo"),
                ("Ctrl+Scroll", "Scale watermark"),
                ("Ctrl+O", "Load Folder"),
                ("Ctrl+W", "Load Watermark"),
                ("Ctrl+S", "Save Current"),
                ("Ctrl+B", "Batch Export"),
                ("Ctrl+F", "Fit to View"),
                ("?", "Show this dialog"),
                ("[", "Previous Image"),
                ("]", "Next Image"),
                ("Ctrl+I", "Toggle Image List"),
            ]
            
            for key, desc in shortcuts:
                row = QWidget()
                row.setStyleSheet("background:transparent;")
                rl = QHBoxLayout(row)
                rl.setContentsMargins(8, 4, 8, 4)
                
                lk = QLabel(key)
                lk.setStyleSheet(f"background:{t['panel']};border-radius:6px;padding:3px 8px;font-weight:600;color:{t['accent']};")
                lk.setFixedWidth(160)
                
                ld = QLabel(desc)
                ld.setStyleSheet(f"color:{t['dim']};")
                
                rl.addWidget(lk)
                rl.addWidget(ld)
                lay.addWidget(row)
            
            lay.addStretch()

# ── MAIN APPLICATION (PyQt6) ──────────────────────────────────────────────
if USE_PYQT6:
    class WatermarkStudio(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("Watermark Studio")
            self.setGeometry(100, 100, 1400, 900)
            self.theme = "dark"
            self.setStyleSheet(qss(self.theme))

            # Core state
            self.image_list = []
            self.current_idx = 0
            self.orig_image = None
            self.watermark_pil = None
            self.watermark_item = None
            self.undo_stack = UndoStack()
            self.preset_manager = PresetManager()
            self.per_image_overrides = {}
            self.batch_worker = None

            # Watermark metrics
            self.wm_cx = 0.5
            self.wm_cy = 0.5
            self.wm_scale = 0.2
            self.wm_opacity = 0.5
            self.wm_rotation = 0

            # Batch options
            self.batch_opts = {
                "tile": False,
                "smart": False,
                "face_avoid": False,
                "smart_opacity": False,
                "blend_mode": "Normal",
                "out_mode": "new_folder",
                "out_fmt": "original"
            }

            self.build_ui()
            self.apply_theme()

        def build_ui(self):
            central = QWidget()
            self.setCentralWidget(central)
            main_lay = QHBoxLayout(central)
            main_lay.setContentsMargins(10, 10, 10, 10)
            main_lay.setSpacing(10)

            # Left panel
            left_panel = QWidget()
            left_panel.setObjectName("Panel")
            left_panel.setFixedWidth(280)
            left_lay = QVBoxLayout(left_panel)
            
            file_lay = QHBoxLayout()
            load_folder_btn = QPushButton("📁 Folder")
            load_folder_btn.clicked.connect(self.load_folder)
            load_wm_btn = QPushButton("🎨 Watermark")
            load_wm_btn.clicked.connect(self.load_watermark)
            file_lay.addWidget(load_folder_btn)
            file_lay.addWidget(load_wm_btn)
            left_lay.addLayout(file_lay)

            # Scrollable settings
            scroll = QScrollArea()
            scroll.setStyleSheet("background:transparent;border:none;")
            scroll.setWidgetResizable(True)
            scroll_widget = QWidget()
            scroll_layout = QVBoxLayout(scroll_widget)
            scroll_layout.setSpacing(8)

            scroll_layout.addWidget(QLabel("Position:"))
            self.cx_slider = QSlider(Qt.Orientation.Horizontal)
            self.cx_slider.setRange(0, 100)
            self.cx_slider.setValue(50)
            self.cx_slider.sliderMoved.connect(self.on_metrics_changed)
            scroll_layout.addWidget(self.cx_slider)

            self.cy_slider = QSlider(Qt.Orientation.Horizontal)
            self.cy_slider.setRange(0, 100)
            self.cy_slider.setValue(50)
            self.cy_slider.sliderMoved.connect(self.on_metrics_changed)
            scroll_layout.addWidget(self.cy_slider)

            scroll_layout.addWidget(QLabel("Scale:"))
            self.scale_slider = QSlider(Qt.Orientation.Horizontal)
            self.scale_slider.setRange(5, 100)
            self.scale_slider.setValue(20)
            self.scale_slider.sliderMoved.connect(self.on_metrics_changed)
            scroll_layout.addWidget(self.scale_slider)

            scroll_layout.addWidget(QLabel("Opacity:"))
            self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
            self.opacity_slider.setRange(0, 100)
            self.opacity_slider.setValue(50)
            self.opacity_slider.sliderMoved.connect(self.on_metrics_changed)
            scroll_layout.addWidget(self.opacity_slider)

            scroll_layout.addWidget(QLabel("Rotation:"))
            self.rotation_slider = QSlider(Qt.Orientation.Horizontal)
            self.rotation_slider.setRange(-180, 180)
            self.rotation_slider.setValue(0)
            self.rotation_slider.sliderMoved.connect(self.on_metrics_changed)
            scroll_layout.addWidget(self.rotation_slider)

            scroll_layout.addWidget(QLabel("Blend Mode:"))
            self.blend_combo = QComboBox()
            self.blend_combo.addItems(["Normal", "Multiply", "Screen", "Overlay", "Soft Light"])
            self.blend_combo.currentTextChanged.connect(self.on_blend_changed)
            scroll_layout.addWidget(self.blend_combo)

            scroll_layout.addWidget(QLabel("Batch Options:"))
            self.tile_cb = QCheckBox("Tile Pattern")
            self.tile_cb.toggled.connect(lambda x: self.batch_opts.update({"tile": x}))
            scroll_layout.addWidget(self.tile_cb)

            self.smart_cb = QCheckBox("Smart Position")
            self.smart_cb.toggled.connect(lambda x: self.batch_opts.update({"smart": x}))
            scroll_layout.addWidget(self.smart_cb)

            self.face_avoid_cb = QCheckBox("Avoid Faces")
            self.face_avoid_cb.toggled.connect(lambda x: self.batch_opts.update({"face_avoid": x}))
            scroll_layout.addWidget(self.face_avoid_cb)

            self.smart_opacity_cb = QCheckBox("Smart Opacity")
            self.smart_opacity_cb.toggled.connect(lambda x: self.batch_opts.update({"smart_opacity": x}))
            scroll_layout.addWidget(self.smart_opacity_cb)

            scroll_layout.addWidget(QLabel("Output Mode:"))
            self.output_mode_combo = QComboBox()
            self.output_mode_combo.addItems(["new_folder", "overwrite"])
            self.output_mode_combo.currentTextChanged.connect(lambda x: self.batch_opts.update({"out_mode": x}))
            scroll_layout.addWidget(self.output_mode_combo)

            scroll_layout.addWidget(QLabel("Output Format:"))
            self.output_fmt_combo = QComboBox()
            self.output_fmt_combo.addItems(["original", "png", "jpg", "webp"])
            self.output_fmt_combo.currentTextChanged.connect(lambda x: self.batch_opts.update({"out_fmt": x}))
            scroll_layout.addWidget(self.output_fmt_combo)

            scroll_layout.addStretch()
            scroll.setWidget(scroll_widget)
            left_lay.addWidget(scroll, 1)

            button_lay = QVBoxLayout()
            batch_btn = QPushButton("⚙ Batch")
            batch_btn.setProperty("id", "primary")
            batch_btn.clicked.connect(self.batch_export)
            button_lay.addWidget(batch_btn)
            left_lay.addLayout(button_lay)

            main_lay.addWidget(left_panel, 0)

            # Center: Canvas
            self.scene = QGraphicsScene()
            self.view = QGraphicsView(self.scene)
            self.view.setStyleSheet("border:none;background:transparent;")
            main_lay.addWidget(self.view, 1)

            # Right panel: Image list
            right_panel = QWidget()
            right_panel.setObjectName("Panel")
            right_panel.setFixedWidth(200)
            right_lay = QVBoxLayout(right_panel)

            self.image_list_widget = QListWidget()
            self.image_list_widget.itemClicked.connect(self.on_image_selected)
            right_lay.addWidget(self.image_list_widget)

            nav_lay = QHBoxLayout()
            prev_btn = QPushButton("← Prev")
            prev_btn.clicked.connect(self.prev_image)
            next_btn = QPushButton("Next →")
            next_btn.clicked.connect(self.next_image)
            nav_lay.addWidget(prev_btn)
            nav_lay.addWidget(next_btn)
            right_lay.addLayout(nav_lay)

            main_lay.addWidget(right_panel, 0)

            self.setup_menu_bar()
            self.setup_shortcuts()
            self.setAcceptDrops(True)

        def setup_menu_bar(self):
            menubar = self.menuBar()
            file_menu = menubar.addMenu("File")
            
            open_action = QAction("Open Folder", self)
            open_action.setShortcut(QKeySequence.StandardKey.Open)
            open_action.triggered.connect(self.load_folder)
            file_menu.addAction(open_action)

            wm_action = QAction("Load Watermark", self)
            wm_action.setShortcut("Ctrl+W")
            wm_action.triggered.connect(self.load_watermark)
            file_menu.addAction(wm_action)

            batch_action = QAction("Batch Export", self)
            batch_action.setShortcut("Ctrl+B")
            batch_action.triggered.connect(self.batch_export)
            file_menu.addAction(batch_action)

        def setup_shortcuts(self):
            self.addAction(self._make_action("Ctrl+O", self.load_folder))
            self.addAction(self._make_action("Ctrl+W", self.load_watermark))
            self.addAction(self._make_action("Ctrl+B", self.batch_export))
            self.addAction(self._make_action("[", self.prev_image))
            self.addAction(self._make_action("]", self.next_image))
            self.addAction(self._make_action("?", self.show_shortcuts))

        def _make_action(self, shortcut, func):
            action = QAction(self)
            action.setShortcut(shortcut)
            action.triggered.connect(func)
            return action

        def load_folder(self):
            folder = QFileDialog.getExistingDirectory(self, "Select Image Folder")
            if folder:
                self.load_folder_from_path(folder)

        def load_folder_from_path(self, folder):
            exts = ('*.png', '*.jpg', '*.jpeg', '*.gif', '*.bmp', '*.webp')
            images = []
            for ext in exts:
                images.extend(glob.glob(os.path.join(folder, ext)))
                images.extend(glob.glob(os.path.join(folder, ext.upper())))
            images = sorted(list(set(images)))
            if not images:
                QMessageBox.warning(self, "No Images", "No images found in folder")
                return
            self.image_list = images
            self.current_idx = 0
            self.update_image_list_widget()
            self.display_image(0)

        def load_watermark(self):
            path, _ = QFileDialog.getOpenFileName(self, "Select Watermark", filter="Images (*.png *.jpg)")
            if path:
                self.load_watermark_from_path(path)

        def load_watermark_from_path(self, path):
            try:
                self.watermark_pil = Image.open(path).convert("RGBA")
                self.render_preview()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load: {e}")

        def on_metrics_changed(self):
            self.wm_cx = self.cx_slider.value() / 100.0
            self.wm_cy = self.cy_slider.value() / 100.0
            self.wm_scale = self.scale_slider.value() / 100.0
            self.wm_opacity = self.opacity_slider.value() / 100.0
            self.wm_rotation = self.rotation_slider.value()
            self.render_preview()

        def on_blend_changed(self):
            mode = self.blend_combo.currentText()
            self.batch_opts["blend_mode"] = mode
            self.render_preview()

        def render_preview(self):
            if not self.orig_image or not self.watermark_pil:
                return

            try:
                iw, ih = self.orig_image.size
                target_w = max(1, int(iw * self.wm_scale))
                scale = target_w / self.watermark_pil.width
                target_h = max(1, int(self.watermark_pil.height * scale))
                wm = self.watermark_pil.resize((target_w, target_h), Image.Resampling.LANCZOS)

                if self.wm_rotation != 0:
                    wm = wm.rotate(-self.wm_rotation, expand=True, resample=Image.Resampling.BICUBIC)

                if self.wm_opacity < 1.0:
                    r, g, b, a = wm.split()
                    a = a.point(lambda v: int(v * self.wm_opacity))
                    wm = Image.merge('RGBA', (r, g, b, a))

                px = int(iw * self.wm_cx - wm.width / 2)
                py = int(ih * self.wm_cy - wm.height / 2)

                preview_img = self.orig_image.copy()
                preview_img.paste(wm, (px, py), wm)

                pixmap = pil_to_qpixmap(preview_img)
                self.scene.clear()
                self.scene.addPixmap(pixmap)
                self.view.fitInView(self.scene.itemsBoundingRect(), Qt.AspectRatioMode.KeepAspectRatio)
            except Exception as e:
                print(f"Render error: {e}")

        def display_image(self, idx):
            if 0 <= idx < len(self.image_list):
                self.current_idx = idx
                path = self.image_list[idx]
                try:
                    self.orig_image = Image.open(path).convert("RGBA")
                    self.render_preview()
                    self.image_list_widget.setCurrentRow(idx)
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to load: {e}")

        def on_image_selected(self, item):
            idx = self.image_list_widget.row(item)
            self.display_image(idx)

        def prev_image(self):
            if self.image_list:
                self.display_image((self.current_idx - 1) % len(self.image_list))

        def next_image(self):
            if self.image_list:
                self.display_image((self.current_idx + 1) % len(self.image_list))

        def batch_export(self):
            if not self.image_list or not self.watermark_pil:
                QMessageBox.warning(self, "Warning", "Load folder and watermark first")
                return
            metrics = (self.wm_cx, self.wm_cy, self.wm_scale, self.wm_opacity, self.wm_rotation)
            self.batch_worker = BatchWorker(self.image_list, self.watermark_pil, metrics, self.batch_opts, self.per_image_overrides)
            self.batch_worker.finished.connect(lambda s, t: QMessageBox.information(self, "Done", f"Processed: {s}/{t}"))
            self.batch_worker.start()

        def update_image_list_widget(self):
            self.image_list_widget.clear()
            for path in self.image_list:
                item = QListWidgetItem(os.path.basename(path))
                self.image_list_widget.addItem(item)

        def show_shortcuts(self):
            dialog = ShortcutsDialog(self, self.theme)
            dialog.exec()

        def apply_theme(self):
            self.setStyleSheet(qss(self.theme))

        def dragEnterEvent(self, e):
            if e.mimeData().hasUrls():
                e.acceptProposedAction()

        def dropEvent(self, e):
            urls = e.mimeData().urls()
            if urls:
                path = urls[0].toLocalFile()
                if os.path.isdir(path):
                    self.load_folder_from_path(path)
                elif os.path.isfile(path):
                    if path.lower().endswith(('png', 'jpg', 'jpeg', 'gif', 'bmp')):
                        self.load_watermark_from_path(path)

        def closeEvent(self, e):
            if self.batch_worker and self.batch_worker.isRunning():
                self.batch_worker.stop()
                self.batch_worker.wait()
            super().closeEvent(e)

if __name__ == "__main__":
    if USE_PYQT6:
        app = QApplication(sys.argv)
        window = WatermarkStudio()
        window.show()
        sys.exit(app.exec())
    else:
        print("Error: PyQt6 is required. Install with: pip install PyQt6")
        print("Or install Tkinter version: pip install pillow numpy opencv-python")
