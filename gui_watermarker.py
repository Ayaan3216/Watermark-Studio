import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from PIL import Image, ImageTk, ImageDraw
import threading
import os
import glob
import time
import cv2
import numpy as np
import sys

try:
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

# ─────────────────────────── THEMES ───────────────────────────
THEMES = {
    "light": {
        "BG": "#f2f2f7",
        "PANEL": "#ffffff",
        "ACCENT": "#34C759", # Apple Green
        "TEXT": "#000000",
        "TEXT_DIM": "#8e8e93",
        "SLIDER_BG": "#e5e5ea",
        "BTN_HOVER": "#f2f2f7",
        "BORDER": "#e5e5ea",
        "CANVAS_BG": "#e5e5ea"
    },
    "dark": {
        "BG": "#000000",
        "PANEL": "#1c1c1e",
        "ACCENT": "#30D158", # Apple Green (Dark Mode)
        "TEXT": "#ffffff",
        "TEXT_DIM": "#98989d",
        "SLIDER_BG": "#3a3a3c",
        "BTN_HOVER": "#2c2c2e",
        "BORDER": "#38383a",
        "CANVAS_BG": "#000000"
    }
}

FONT_TITLE  = ("Segoe UI", 16)
FONT_BTN    = ("Segoe UI", 10, "bold")
FONT_LABEL  = ("Segoe UI", 9)
FONT_SECTION = ("Segoe UI", 8, "bold")

# ─────────────────────────── PILL BUTTON ─────────────────────────
class PillButton(tk.Canvas):
    def __init__(self, parent, text, command, is_primary=False, width=160, height=36, theme_dict=None, **kw):
        super().__init__(parent, width=width, height=height, highlightthickness=0, cursor="hand2", **kw)
        self.command = command
        self.is_primary = is_primary
        self.w, self.h = width, height
        self.text_str = text
        self.t = theme_dict
        self.configure(bg=self.t["PANEL"])
        self._draw()
        self.bind("<Enter>",    self._on_enter)
        self.bind("<Leave>",    self._on_leave)
        self.bind("<Button-1>", self._on_click)
        self.bind("<ButtonRelease-1>", self._on_release)

    def update_theme(self, theme_dict):
        self.t = theme_dict
        self.configure(bg=self.t["PANEL"])
        self._draw()

    def _draw(self, hover=False, pressed=False):
        self.delete("all")
        if self.is_primary:
            fill = self.t["ACCENT"]
            text_color = "#ffffff"
            if pressed: fill = "#2E8B57" # Darker green
            elif hover: fill = "#3CB371" # Lighter green
        else:
            fill = self.t["SLIDER_BG"]
            text_color = self.t["ACCENT"]
            if hover: fill = self.t["BORDER"]
            if pressed: fill = self.t["TEXT_DIM"]
            
        r = self.h // 2
        x0, y0, x1, y1 = 2, 2, self.w-2, self.h-2
        
        self.create_arc(x0, y0, x0+2*r, y0+2*r, start=90, extent=180, fill=fill, outline="")
        self.create_arc(x1-2*r, y0, x1, y0+2*r, start=-90, extent=180, fill=fill, outline="")
        self.create_rectangle(x0+r, y0, x1-r, y1, fill=fill, outline="")
        
        self.create_text(self.w//2, self.h//2, text=self.text_str, fill=text_color, font=FONT_BTN)

    def _on_enter(self, e):  self._draw(hover=True)
    def _on_leave(self, e):  self._draw()
    def _on_click(self, e):  self._draw(pressed=True)
    def _on_release(self, e):
        self._draw(hover=True)
        if self.command:
            self.after(50, self.command)

# ─────────────────────────── PROGRESS DIALOG ─────────────────────────
class ProgressDialog(tk.Toplevel):
    def __init__(self, parent, title="Processing…", t=None):
        super().__init__(parent)
        self.t = t or THEMES["light"]
        self.title(title)
        self.configure(bg=self.t["PANEL"])
        self.resizable(False, False)
        self.overrideredirect(True)
        w, h = 340, 110
        px = parent.winfo_rootx() + parent.winfo_width()//2 - w//2
        py = parent.winfo_rooty() + parent.winfo_height()//2 - h//2
        self.geometry(f"{w}x{h}+{px}+{py}")
        
        self.border = tk.Frame(self, bg=self.t["BORDER"], bd=1)
        self.border.pack(fill="both", expand=True)
        self.inner = tk.Frame(self.border, bg=self.t["PANEL"])
        self.inner.pack(fill="both", expand=True, padx=1, pady=1)
        
        tk.Label(self.inner, text=title, bg=self.t["PANEL"], fg=self.t["TEXT"], font=FONT_BTN).pack(pady=(16,4))
        self.lbl = tk.Label(self.inner, text="Starting…", bg=self.t["PANEL"], fg=self.t["TEXT_DIM"], font=FONT_LABEL)
        self.lbl.pack()
        
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Apple.Horizontal.TProgressbar",
                         troughcolor=self.t["SLIDER_BG"], background=self.t["ACCENT"],
                         bordercolor=self.t["PANEL"], lightcolor=self.t["ACCENT"], darkcolor=self.t["ACCENT"])
        self.bar = ttk.Progressbar(self.inner, style="Apple.Horizontal.TProgressbar",
                                   orient="horizontal", length=300, mode="determinate")
        self.bar.pack(pady=8)
        self.grab_set()

    def update_progress(self, value, text=""):
        self.bar["value"] = value
        if text: self.lbl.config(text=text)
        self.update_idletasks()

# ─────────────────────────── MAIN APP ────────────────────────────────
class WatermarkApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Watermark Studio")
        self.geometry("1400x900")
        self.minsize(1000, 600)

        # State
        self.current_theme     = "light"
        self.image_paths       = []     
        self.current_img_idx   = -1
        self.orig_image        = None   
        self.orig_watermark    = None   
        self.display_image     = None   
        self.display_scale     = 1.0    
        self.wm_scale          = 1.0    
        
        self.img_px            = 0      # Centered X padding
        self.img_py            = 0      # Centered Y padding
        self.wm_x              = 0      # Relative to img_px
        self.wm_y              = 0      # Relative to img_py
        
        self._user_moved_wm    = False  
        self._drag_ox          = 0
        self._drag_oy          = 0
        self._tk_img           = None
        self._tk_wm            = None
        self._canvas_img_id    = None
        self._canvas_wm_id     = None
        self._fast_mode        = False
        
        # Theme tracking
        self.anim_buttons = []
        self.theme_labels = []
        self.theme_dim_labels = []
        self.theme_frames = []
        self.theme_bg_frames = []

        self._build_ui()
        self._apply_theme()

    def _build_ui(self):
        t = THEMES[self.current_theme]
        
        # ── Header ──
        self.header = tk.Frame(self, height=60)
        self.header.pack(fill="x")
        self.header.pack_propagate(False)
        self.theme_frames.append(self.header)
        
        self.header_lbl = tk.Label(self.header, text="Watermark Studio", font=FONT_TITLE)
        self.header_lbl.pack(side="left", padx=20, pady=10)
        
        self.theme_btn = PillButton(self.header, "Dark Mode", self._toggle_theme, is_primary=False, width=100, height=28, theme_dict=t)
        self.theme_btn.pack(side="right", padx=20, pady=16)
        self.anim_buttons.append(self.theme_btn)

        # ── Left sidebar ──
        self.sidebar = tk.Frame(self, width=300)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        self.theme_frames.append(self.sidebar)
        
        self.border_line = tk.Frame(self.sidebar, width=1)
        self.border_line.pack(side="right", fill="y")

        def section(txt, pad=(16, 4)):
            lbl = tk.Label(self.sidebar, text=txt.upper(), font=FONT_SECTION)
            lbl.pack(anchor="w", padx=20, pady=pad)
            self.theme_dim_labels.append(lbl)

        # LOAD SECTION
        section("Media")
        load_frame = tk.Frame(self.sidebar)
        load_frame.pack(fill="x", padx=20)
        self.theme_frames.append(load_frame)
        
        b1 = PillButton(load_frame, "Load Folder", self._load_folder, is_primary=False, width=125, height=32, theme_dict=t)
        b1.pack(side="left")
        b2 = PillButton(load_frame, "Load WM", self._load_watermark, is_primary=False, width=125, height=32, theme_dict=t)
        b2.pack(side="right")
        self.anim_buttons.extend([b1, b2])

        # LISTBOX
        self.list_frame = tk.Frame(self.sidebar)
        self.list_frame.pack(fill="both", expand=True, padx=20, pady=10)
        self.theme_bg_frames.append(self.list_frame)
        
        self.listbox = tk.Listbox(self.list_frame, highlightthickness=0, borderwidth=0, font=FONT_LABEL)
        sb = tk.Scrollbar(self.list_frame, orient="vertical", command=self.listbox.yview)
        self.listbox.config(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.listbox.pack(side="left", fill="both", expand=True)
        self.listbox.bind("<<ListboxSelect>>", self._on_listbox_select)

        # IMAGE ZOOM
        section("Image Zoom")
        self.img_zoom_var = tk.DoubleVar(value=100)
        zf = tk.Frame(self.sidebar)
        zf.pack(fill="x", padx=20)
        self.theme_frames.append(zf)
        
        l1 = tk.Label(zf, text="Zoom:", font=FONT_LABEL)
        l1.pack(side="left")
        self.img_zoom_pct_lbl = tk.Label(zf, text="100%", font=FONT_LABEL)
        self.img_zoom_pct_lbl.pack(side="right")
        self.theme_dim_labels.append(l1)
        self.theme_labels.append(self.img_zoom_pct_lbl)
        
        self.img_zoom_slider = ttk.Scale(self.sidebar, from_=10, to=400, variable=self.img_zoom_var,
                                     orient="horizontal", style="Apple.Horizontal.TScale",
                                     command=self._on_img_zoom_change, length=260)
        self.img_zoom_slider.pack(padx=20, pady=4)
        
        qf_zoom = tk.Frame(self.sidebar)
        qf_zoom.pack(padx=20, pady=2, fill="x")
        self.theme_frames.append(qf_zoom)
        b_fit = PillButton(qf_zoom, "Fit to Bounds", self._fit_to_canvas_btn, is_primary=False, width=260, height=28, theme_dict=t)
        b_fit.pack()
        self.anim_buttons.append(b_fit)

        # WATERMARK SIZE SLIDER
        section("Watermark Scale")
        self.size_var = tk.DoubleVar(value=100)
        wf = tk.Frame(self.sidebar)
        wf.pack(fill="x", padx=20)
        self.theme_frames.append(wf)
        
        l2 = tk.Label(wf, text="Scale:", font=FONT_LABEL)
        l2.pack(side="left")
        self.size_pct_lbl = tk.Label(wf, text="100%", font=FONT_LABEL)
        self.size_pct_lbl.pack(side="right")
        self.theme_dim_labels.append(l2)
        self.theme_labels.append(self.size_pct_lbl)
        
        self.size_slider = ttk.Scale(self.sidebar, from_=10, to=300, variable=self.size_var,
                                     orient="horizontal", style="Apple.Horizontal.TScale",
                                     command=self._on_size_change, length=260)
        self.size_slider.pack(padx=20, pady=4)

        # SAVE OPTIONS
        section("Settings")
        self.save_mode = tk.StringVar(value="new_folder")
        ttk.Radiobutton(self.sidebar, text="Save to 'output' folder", variable=self.save_mode, value="new_folder", style="TRadiobutton").pack(anchor="w", padx=20)
        ttk.Radiobutton(self.sidebar, text="Overwrite original files", variable=self.save_mode, value="overwrite", style="TRadiobutton").pack(anchor="w", padx=20, pady=(4,0))

        self.smart_placement = tk.BooleanVar(value=True)
        ttk.Checkbutton(self.sidebar, text="Smart Placement (Batch)", variable=self.smart_placement, style="TCheckbutton").pack(anchor="w", padx=20, pady=(8,0))

        # EXPORT
        section("Export", pad=(24, 8))
        b3 = PillButton(self.sidebar, "Save Current", self._save_current, is_primary=True, width=260, height=38, theme_dict=t)
        b3.pack(padx=20, pady=4)
        b4 = PillButton(self.sidebar, "Batch Process Folder", self._save_batch, is_primary=True, width=260, height=38, theme_dict=t)
        b4.pack(padx=20, pady=4)
        self.anim_buttons.extend([b3, b4])

        # Status bar
        self.status_lbl = tk.Label(self.sidebar, text="Ready", font=FONT_LABEL, wraplength=260, justify="left")
        self.status_lbl.pack(side="bottom", padx=20, pady=20, anchor="w")
        self.theme_dim_labels.append(self.status_lbl)

        # ── Canvas area ──
        self.canvas_frame = tk.Frame(self)
        self.canvas_frame.pack(side="left", fill="both", expand=True)
        self.theme_frames.append(self.canvas_frame)

        self.canvas = tk.Canvas(self.canvas_frame, highlightthickness=0, cursor="crosshair")
        self.canvas.pack(fill="both", expand=True)

        self.canvas.tag_bind("watermark", "<ButtonPress-1>",   self._wm_press)
        self.canvas.tag_bind("watermark", "<B1-Motion>",       self._wm_drag)
        self.canvas.tag_bind("watermark", "<ButtonRelease-1>", self._wm_release)
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Configure>", self._on_canvas_resize)
        self.bind("<Up>",    lambda e: self._arrow_move(0, -10))
        self.bind("<Down>",  lambda e: self._arrow_move(0, 10))
        self.bind("<Left>",  lambda e: self._arrow_move(-10, 0))
        self.bind("<Right>", lambda e: self._arrow_move(10, 0))
        self.canvas.bind("<Enter>", lambda e: self.canvas.focus_set())

    def _toggle_theme(self):
        self.current_theme = "dark" if self.current_theme == "light" else "light"
        self.theme_btn.text_str = "Light Mode" if self.current_theme == "dark" else "Dark Mode"
        self._apply_theme()

    def _apply_theme(self):
        t = THEMES[self.current_theme]
        self.configure(bg=t["BG"])
        
        for f in self.theme_frames:
            f.configure(bg=t["PANEL"])
        for f in self.theme_bg_frames:
            f.configure(bg=t["BG"])
            
        self.header_lbl.configure(bg=t["PANEL"], fg=t["TEXT"])
        self.border_line.configure(bg=t["BORDER"])
        
        for btn in self.anim_buttons:
            btn.update_theme(t)
            
        self.listbox.configure(bg=t["BG"], fg=t["TEXT"], selectbackground=t["ACCENT"], selectforeground="#ffffff")
        self.canvas.configure(bg=t["CANVAS_BG"])
        
        for lbl in self.theme_labels:
            lbl.configure(bg=t["PANEL"], fg=t["TEXT"])
        for lbl in self.theme_dim_labels:
            lbl.configure(bg=t["PANEL"], fg=t["TEXT_DIM"])
            
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Apple.Horizontal.TScale", troughcolor=t["SLIDER_BG"], background=t["PANEL"], sliderthickness=16)
        style.configure("TRadiobutton", background=t["PANEL"], foreground=t["TEXT"])
        style.map("TRadiobutton", background=[('active', t["PANEL"])])
        style.configure("TCheckbutton", background=t["PANEL"], foreground=t["TEXT"])
        style.map("TCheckbutton", background=[('active', t["PANEL"])])
        
        self._refresh_canvas()

    # ── iOS Custom Overlay Scrollbars ─────────────────────────────────
    def _draw_overlay_scrollbars(self):
        self.canvas.delete("overlay_scrollbar")
        yv = self.canvas.yview()
        xv = self.canvas.xview()
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        
        sb_color = "#b0b0b5" if self.current_theme == "light" else "#5c5c60"
        
        if yv[0] > 0 or yv[1] < 1.0:
            sb_h = ch * (yv[1] - yv[0])
            sb_y = ch * yv[0]
            self._draw_pill(cw - 12, sb_y + 4, cw - 4, sb_y + sb_h - 4, sb_color, "overlay_scrollbar")
                                         
        if xv[0] > 0 or xv[1] < 1.0:
            sb_w = cw * (xv[1] - xv[0])
            sb_x = cw * xv[0]
            self._draw_pill(sb_x + 4, ch - 12, sb_x + sb_w - 4, ch - 4, sb_color, "overlay_scrollbar")

    def _draw_pill(self, x0, y0, x1, y1, color, tags):
        r = min(x1-x0, y1-y0) // 2
        if r <= 0: return
        self.canvas.create_arc(x0, y0, x0+2*r, y0+2*r, start=90, extent=180, fill=color, outline="", tags=tags)
        self.canvas.create_arc(x1-2*r, y1-2*r, x1, y1, start=-90, extent=180, fill=color, outline="", tags=tags)
        self.canvas.create_rectangle(x0+r, y0, x1-r, y1, fill=color, outline="", tags=tags)
        self.canvas.create_rectangle(x0, y0+r, x1, y1-r, fill=color, outline="", tags=tags)

    def _on_canvas_resize(self, event=None):
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        if hasattr(self, '_last_cw') and self._last_cw == cw and getattr(self, '_last_ch', 0) == ch:
            return
        self._last_cw = cw
        self._last_ch = ch
        
        if self.orig_image:
            self._refresh_canvas()
        self._draw_overlay_scrollbars()

    # ── Input Handlers ────────────────────────────────────────────────
    def _clamp_watermark(self):
        if not self.display_image or not self.orig_watermark: return
        img_w, img_h = self.display_image.size
        wm_disp = self._get_display_watermark()
        if not wm_disp: return
        wm_w, wm_h = wm_disp.size
        
        margin_x = int(wm_w * 0.8)
        margin_y = int(wm_h * 0.8)
        self.wm_x = max(-margin_x, min(self.wm_x, img_w + margin_x - wm_w))
        self.wm_y = max(-margin_y, min(self.wm_y, img_h + margin_y - wm_h))

    def _update_glow(self):
        self.canvas.delete("glow")
        if not self.display_image or not self.orig_watermark: return
        img_w, img_h = self.display_image.size
        wm_disp = self._get_display_watermark()
        if not wm_disp: return
        wm_w, wm_h = wm_disp.size
        
        t = THEMES[self.current_theme]
        glow_color = t["ACCENT"]
        w = 4
        T = 5
        
        if self.wm_x <= T:
            self.canvas.create_line(self.img_px, self.img_py, self.img_px, self.img_py+img_h, fill=glow_color, width=w, tags="glow")
        if self.wm_x + wm_w >= img_w - T:
            self.canvas.create_line(self.img_px+img_w, self.img_py, self.img_px+img_w, self.img_py+img_h, fill=glow_color, width=w, tags="glow")
        if self.wm_y <= T:
            self.canvas.create_line(self.img_px, self.img_py, self.img_px+img_w, self.img_py, fill=glow_color, width=w, tags="glow")
        if self.wm_y + wm_h >= img_h - T:
            self.canvas.create_line(self.img_px, self.img_py+img_h, self.img_px+img_w, self.img_py+img_h, fill=glow_color, width=w, tags="glow")

    def _arrow_move(self, dx, dy):
        if self.focus_get() == self.listbox: return
        if not self.orig_watermark or not self._canvas_wm_id: return
        self.wm_x += dx
        self.wm_y += dy
        self._clamp_watermark()
        self.canvas.coords(self._canvas_wm_id, self.img_px + self.wm_x, self.img_py + self.wm_y)
        self._update_glow()
        self._user_moved_wm = True

    def _on_mousewheel(self, e):
        if e.state & 0x0004:
            delta = 10 if e.delta > 0 else -10
            new_val = max(10, min(300, self.size_var.get() + delta))
            self.size_var.set(new_val)
            self._on_size_change(new_val)
        else:
            self.canvas.yview_scroll(int(-1*(e.delta/120)), "units")
            self._draw_overlay_scrollbars()

    def _draw_placeholder(self):
        self.canvas.delete("all")
        t = THEMES[self.current_theme]
        self.canvas.create_text(500, 300, text="Load a folder to get started",
            fill=t["TEXT_DIM"], font=("Segoe UI", 16), tags="placeholder")

    # ── Loading ───────────────────────────────────────────────────────
    def _load_folder(self):
        folder = filedialog.askdirectory(title="Select Folder")
        if not folder: return
        
        dlg = ProgressDialog(self, "Scanning Folder…", t=THEMES[self.current_theme])
        def work():
            dlg.update_progress(50, "Finding images…")
            exts = ('*.png', '*.jpg', '*.jpeg', '*.webp')
            paths = []
            for ext in exts:
                paths.extend(glob.glob(os.path.join(folder, ext)))
                paths.extend(glob.glob(os.path.join(folder, ext.upper())))
            paths = sorted(list(set(paths)))
            dlg.update_progress(100, f"Found {len(paths)} images")
            time.sleep(0.3)
            self.after(0, dlg.destroy)
            self.after(0, lambda: self._populate_listbox(paths))
        threading.Thread(target=work, daemon=True).start()

    def _populate_listbox(self, paths):
        self.image_paths = paths
        self.listbox.delete(0, tk.END)
        for p in paths:
            self.listbox.insert(tk.END, os.path.basename(p))
        if paths:
            self.listbox.selection_set(0)
            self._load_image_from_list(0)
            self.status_lbl.config(text=f"Loaded {len(paths)} images.")

    def _on_listbox_select(self, event):
        sel = self.listbox.curselection()
        if not sel: return
        self._load_image_from_list(sel[0])

    def _load_image_from_list(self, idx):
        if idx == self.current_img_idx: return
        self.current_img_idx = idx
        path = self.image_paths[idx]
        
        dlg = ProgressDialog(self, "Loading Image…", t=THEMES[self.current_theme])
        def work():
            dlg.update_progress(30, "Reading file…")
            img = Image.open(path).convert("RGBA")
            dlg.update_progress(70, "Preparing…")
            self.orig_image = img
            self._user_moved_wm = False 
            dlg.update_progress(100, "Done!")
            time.sleep(0.1)
            self.after(0, dlg.destroy)
            self.after(0, self._fit_to_canvas_btn)
        threading.Thread(target=work, daemon=True).start()

    def _load_watermark(self):
        path = filedialog.askopenfilename(
            title="Select Watermark",
            filetypes=[("PNG", "*.png"), ("Images", "*.png *.jpg *.jpeg"), ("All", "*.*")])
        if not path: return
        self._load_watermark_file(path)

    def _load_watermark_file(self, path):
        dlg = ProgressDialog(self, "Loading Watermark…", t=THEMES[self.current_theme])
        def work():
            dlg.update_progress(50, "Reading watermark…")
            self.orig_watermark = Image.open(path).convert("RGBA")
            self.size_var.set(100)
            self._user_moved_wm = False
            dlg.update_progress(100, "Applying…")
            time.sleep(0.2)
            self.after(0, dlg.destroy)
            if self.orig_image:
                self.after(0, self._fit_image_to_canvas)
                self.after(0, self._refresh_canvas)
            self.after(0, lambda: self.status_lbl.config(text=f"Watermark: {os.path.basename(path)}"))
        threading.Thread(target=work, daemon=True).start()

    # ── Canvas helpers ────────────────────────────────────────────────
    def _fit_image_to_canvas(self):
        if not self.orig_image: return
        iw, ih = self.orig_image.size
        self.display_scale = self.img_zoom_var.get() / 100.0
        nw = max(1, int(iw * self.display_scale))
        nh = max(1, int(ih * self.display_scale))
        
        # 60fps Optimization: Use NEAREST when actively dragging the slider, BILINEAR when finished
        resampling = Image.Resampling.NEAREST if getattr(self, '_fast_mode', False) else Image.Resampling.BILINEAR
        self.display_image = self.orig_image.resize((nw, nh), resampling)
        
        if self.orig_watermark and not self._user_moved_wm:
            wm_disp = self._get_display_watermark()
            if wm_disp:
                self.wm_x = (nw - wm_disp.size[0]) // 2
                self.wm_y = nh - wm_disp.size[1]
        self._clamp_watermark()

    def _get_display_watermark(self):
        if not self.orig_watermark: return None
        ow, oh = self.orig_watermark.size
        factor = self.display_scale * (self.size_var.get() / 100.0)
        nw = max(4, int(ow * factor))
        nh = max(4, int(oh * factor))
        resampling = Image.Resampling.NEAREST if getattr(self, '_fast_mode', False) else Image.Resampling.BILINEAR
        return self.orig_watermark.resize((nw, nh), resampling)

    def _refresh_canvas(self):
        self.canvas.delete("all")
        if self.orig_image:
            if not self.display_image: self._fit_image_to_canvas()
            
            iw, ih = self.display_image.size
            cw = self.canvas.winfo_width()
            ch = self.canvas.winfo_height()
            
            # Dynamic Centering: Equal padding if zoomed out, zero padding if zoomed in past bounds
            self.img_px = (cw - iw) // 2 if iw < cw else 0
            self.img_py = (ch - ih) // 2 if ih < ch else 0
            
            # Scrollregion bounds the image correctly
            self.canvas.configure(scrollregion=(0, 0, max(cw, iw), max(ch, ih)))
            
            self._tk_img = ImageTk.PhotoImage(self.display_image)
            self._canvas_img_id = self.canvas.create_image(self.img_px, self.img_py, anchor="nw", image=self._tk_img, tags="bg_image")
            
            # Subtle boundary line
            t = THEMES[self.current_theme]
            self.canvas.create_rectangle(self.img_px, self.img_py, self.img_px+iw, self.img_py+ih, outline=t["BORDER"], width=1, tags="boundary")
            
        if self.orig_watermark:
            wm_disp = self._get_display_watermark()
            self._tk_wm = ImageTk.PhotoImage(wm_disp)
            self._canvas_wm_id = self.canvas.create_image(
                self.img_px + self.wm_x, self.img_py + self.wm_y, anchor="nw", image=self._tk_wm, tags="watermark")

        self._update_glow()
        self._draw_overlay_scrollbars()
        if not self.orig_image: self._draw_placeholder()

    # ── Drag ──────────────────────────────────────────────────────────
    def _wm_press(self, e):
        cx = self.canvas.canvasx(e.x)
        cy = self.canvas.canvasy(e.y)
        self._drag_ox = cx - (self.wm_x + self.img_px)
        self._drag_oy = cy - (self.wm_y + self.img_py)
        self._user_moved_wm = True
        self.canvas.config(cursor="fleur")

    def _wm_drag(self, e):
        if e.y > self.canvas.winfo_height() - 40: self.canvas.yview_scroll(1, "units")
        elif e.y < 40: self.canvas.yview_scroll(-1, "units")
        if e.x > self.canvas.winfo_width() - 40: self.canvas.xview_scroll(1, "units")
        elif e.x < 40: self.canvas.xview_scroll(-1, "units")

        cx = self.canvas.canvasx(e.x)
        cy = self.canvas.canvasy(e.y)
        self.wm_x = cx - self._drag_ox - self.img_px
        self.wm_y = cy - self._drag_oy - self.img_py
        self._clamp_watermark()
        self.canvas.coords(self._canvas_wm_id, self.img_px + self.wm_x, self.img_py + self.wm_y)
        self._update_glow()
        self._draw_overlay_scrollbars()

    def _wm_release(self, e):
        self.canvas.config(cursor="crosshair")

    # ── Resize ────────────────────────────────────────────────────────
    def _fit_to_canvas_btn(self):
        if not self.orig_image: return
        self.update_idletasks()
        cw = self.canvas.winfo_width()
        iw = self.orig_image.width
        if iw <= 0: return
        pct = max(10, min(400, int((cw / iw) * 100)))
        self.img_zoom_var.set(pct)
        self.img_zoom_pct_lbl.config(text=f"{pct}%")
        self._apply_img_zoom_hq()

    def _on_size_change(self, val):
        pct = int(float(val))
        self.size_pct_lbl.config(text=f"{pct}%")
        self._fast_mode = True
        self._clamp_watermark()
        self._refresh_canvas()
        if hasattr(self, '_wm_size_job'): self.after_cancel(self._wm_size_job)
        self._wm_size_job = self.after(150, self._apply_wm_size_hq)

    def _apply_wm_size_hq(self):
        self._fast_mode = False
        self._clamp_watermark()
        self._refresh_canvas()

    def _on_img_zoom_change(self, val):
        pct = int(float(val))
        self.img_zoom_pct_lbl.config(text=f"{pct}%")
        self._fast_mode = True
        self._fit_image_to_canvas()
        self._refresh_canvas()
        if hasattr(self, '_zoom_job'): self.after_cancel(self._zoom_job)
        self._zoom_job = self.after(150, self._apply_img_zoom_hq)

    def _apply_img_zoom_hq(self):
        self._fast_mode = False
        self._fit_image_to_canvas()
        self._refresh_canvas()

    # ── Saving Logic ──────────────────────────────────────────────────
    def _get_relative_wm_metrics(self):
        if not self.display_image or not self.orig_watermark: return None
        dw, dh = self.display_image.size
        wm_disp = self._get_display_watermark()
        if not wm_disp: return None
        wm_cw, wm_ch = wm_disp.size
        center_x = self.wm_x + (wm_cw / 2)
        center_y = self.wm_y + (wm_ch / 2)
        rel_cx = center_x / dw
        rel_cy = center_y / dh
        actual_wm_width_in_orig = (wm_cw / self.display_scale)
        rel_scale = actual_wm_width_in_orig / self.orig_image.size[0]
        return rel_cx, rel_cy, rel_scale

    def _find_smart_position(self, base_img, wm_w, wm_h):
        cv_img = np.array(base_img.convert('RGB'))
        gray = cv2.cvtColor(cv_img, cv2.COLOR_RGB2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        integral = cv2.integral(edges)
        img_h, img_w = gray.shape
        if wm_w >= img_w or wm_h >= img_h: return (img_w - wm_w) // 2, img_h - wm_h
        min_score, best_x, best_y = float('inf'), 0, 0
        stride_x, stride_y = max(1, img_w // 50), max(1, img_h // 50)
        y_penalty_factor = 255 * 5  
        for y in range(0, img_h - wm_h + 1, stride_y):
            for x in range(0, img_w - wm_w + 1, stride_x):
                sum_edges = (integral[y + wm_h, x + wm_w] - integral[y, x + wm_w] - integral[y + wm_h, x] + integral[y, x])
                score = sum_edges + ((img_h - wm_h) - y) * y_penalty_factor
                if score < min_score:
                    min_score, best_x, best_y = score, x, y
        return int(best_x), int(best_y)

    def _process_single_image(self, img_path, metrics, use_smart=False):
        try:
            base_img = Image.open(img_path).convert("RGBA")
            iw, ih = base_img.size
            rel_cx, rel_cy, rel_scale = metrics
            ow, oh = self.orig_watermark.size
            target_w = int(iw * rel_scale)
            scale = target_w / ow
            target_h = int(oh * scale)
            wm_final = self.orig_watermark.resize((max(1, target_w), max(1, target_h)), Image.Resampling.LANCZOS)
            
            if use_smart: px, py = self._find_smart_position(base_img, target_w, target_h)
            else:
                px = int((iw * rel_cx) - (target_w / 2))
                py = int((ih * rel_cy) - (target_h / 2))
            
            base_img.paste(wm_final, (px, py), wm_final)
            
            if self.save_mode.get() == "overwrite": out_path = img_path
            else:
                out_dir = os.path.join(os.path.dirname(img_path), "output")
                os.makedirs(out_dir, exist_ok=True)
                out_path = os.path.join(out_dir, os.path.basename(img_path))
                
            save_kw = {"quality": 100, "subsampling": 0} if out_path.lower().endswith((".jpg", ".jpeg")) else {}
            base_img.convert("RGB").save(out_path, **save_kw)
            return True
        except Exception as e:
            print(f"Failed to process {img_path}: {e}")
            return False

    def _save_current(self):
        if not self.orig_image or not self.orig_watermark or self.current_img_idx < 0:
            messagebox.showwarning("Warning", "Please load an image and watermark first.")
            return
        metrics = self._get_relative_wm_metrics()
        path = self.image_paths[self.current_img_idx]
        dlg = ProgressDialog(self, "Saving Image…", t=THEMES[self.current_theme])
        def work():
            dlg.update_progress(50, "Compositing & Saving…")
            success = self._process_single_image(path, metrics)
            dlg.update_progress(100, "Done!")
            time.sleep(0.3)
            self.after(0, dlg.destroy)
            msg = f"✔ Saved: {os.path.basename(path)}" if success else "❌ Save failed."
            self.after(0, lambda: self.status_lbl.config(text=msg))
        threading.Thread(target=work, daemon=True).start()

    def _save_batch(self):
        if not self.image_paths or not self.orig_watermark:
            messagebox.showwarning("Warning", "Please load a folder and a watermark first.")
            return
        metrics = self._get_relative_wm_metrics()
        total = len(self.image_paths)
        use_smart = self.smart_placement.get()
        dlg = ProgressDialog(self, f"Batch Processing {total} images…", t=THEMES[self.current_theme])
        def work():
            success_count = 0
            for i, path in enumerate(self.image_paths):
                pct = int((i / total) * 100)
                dlg.update_progress(pct, f"Processing {i+1}/{total}...")
                if self._process_single_image(path, metrics, use_smart=use_smart): success_count += 1
            dlg.update_progress(100, "Finished Batch!")
            time.sleep(0.5)
            self.after(0, dlg.destroy)
            self.after(0, lambda: self.status_lbl.config(text=f"✔ Batch complete. Processed {success_count}/{total} images."))
        threading.Thread(target=work, daemon=True).start()

if __name__ == "__main__":
    app = WatermarkApp()
    
    if getattr(sys, 'frozen', False):
        application_path = sys._MEIPASS
    else:
        application_path = os.path.dirname(os.path.abspath(__file__))
        
    wm_default = os.path.join(application_path, "watermark.png")
    if os.path.exists(wm_default):
        app._load_watermark_file(wm_default)
    app.mainloop()
