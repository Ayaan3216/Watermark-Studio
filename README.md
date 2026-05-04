# 💧 Watermark Studio

A blazing fast, professional-grade desktop application for batch watermarking images, manga chapters, and webtoons. Built with a sleek, iOS-inspired minimalist interface, it utilizes a custom hardware-accelerated 60fps rendering engine and OpenCV Computer Vision to automatically place watermarks without covering important details like faces or text bubbles.

---

## ✨ Features

- **Jony Ive / Apple-Inspired UI**: Beautiful, distraction-free minimalist design featuring pill buttons, dynamic centering, custom translucent overlay scrollbars, and a native Dark/Light Mode toggle.
- **Buttery Smooth 60fps Rendering**: Handles massive 10,000px+ vertical webtoon images without stuttering using a custom two-stage render engine (swapping seamlessly between `NEAREST` and `BILINEAR` sampling during interactions).
- **Smart Placement Engine**: Uses `OpenCV` Canny edge-detection and integral math to automatically scan manga panels and place your watermark in "quiet" areas—preventing the watermark from covering faces, complex art, or text bubbles during batch processing.
- **Infinite Drag-and-Drop Canvas**: Easily drag the watermark anywhere on the image. The custom soft-boundary math allows you to seamlessly overlap transparent padding off the edges for perfect placement.
- **Batch Processing**: Load an entire chapter folder, dial in your zoom and scale settings, and hit process. The engine will accurately map relative coordinates across images of varying resolutions and save them perfectly.
- **Standalone Executable**: Packaged into a single `Watermark Studio.exe` file. No python installations or terminal scripts required for the end user.

---

## 🚀 Quick Start (Using the Executable)

If you just want to use the app, download the latest `Watermark Studio.exe` from the **Releases** tab.

1. Double-click the `.exe` to launch.
2. Click **Load Folder** to select a directory containing your images (PNG, JPG, WEBP supported).
3. Click **Load WM** to select your transparent watermark logo.
4. Use the sliders or your mouse scroll wheel to adjust zoom and scale. Drag the watermark to position it.
5. Choose **Save to 'output' folder** and click **Batch Process Folder**.

---

## 🛠️ Developer Setup

If you want to run the source code or build the executable yourself:

### 1. Install Dependencies
Ensure you have Python 3.10+ installed. Then install the required libraries:

```bash
pip install -r requirements.txt
```

### 2. Run the Application
```bash
python gui_watermarker.py
```

### 3. Build the Executable
If you modify the source and want to compile it back into a standalone `.exe`, use `PyInstaller`:

```bash
pip install pyinstaller
pyinstaller --noconsole --onefile --add-data "watermark.png;." -n "Watermark Studio" gui_watermarker.py
```
*The compiled executable will be output to the `dist/` folder.*

---

## 🧠 How the Smart Placement Works
During batch processing, if "Smart Placement" is enabled, the program ignores your manual positioning and uses OpenCV edge-detection. It builds a high-speed *Integral Image* of the current page, scanning chunks of the image to find the region with the lowest "edge density" (the least amount of line-art/text). It then places the watermark cleanly into that empty space, guaranteeing your logo never obscures the manga's dialogue or character faces.

---

## 📄 License
This project is open-source and available under the [MIT License](LICENSE).
