import cv2
import numpy as np
from PIL import Image
import os
import glob

def add_watermark_to_panels(image_path, watermark_path, output_path, min_area_ratio=0.01):
    # Load image with OpenCV to find panels
    img = cv2.imread(image_path)
    if img is None:
        print(f"Could not read {image_path}")
        return

    # Load watermark with Pillow
    try:
        watermark = Image.open(watermark_path).convert("RGBA")
    except Exception as e:
        print(f"Could not load watermark: {e}")
        return
        
    # Watermark is kept opaque as requested

    # Detect panels using OpenCV
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Blur to reduce noise
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Canny edge detection
    edges = cv2.Canny(blurred, 50, 150)
    
    # Dilate edges to connect broken lines and form solid blocks for panels
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
    dilated = cv2.dilate(edges, kernel, iterations=4)
    
    # Find contours (the panels)
    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Convert original OpenCV image (BGR) to PIL Image (RGBA) for watermarking
    img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)).convert("RGBA")
    
    total_area = img.shape[0] * img.shape[1]
    
    # Filter valid panels
    valid_panels = []
    for contour in contours:
        area = cv2.contourArea(contour)
        if area > total_area * min_area_ratio:
            x, y, w, h = cv2.boundingRect(contour)
            valid_panels.append((x, y, w, h))
            
    if not valid_panels:
        print(f"Processed '{os.path.basename(image_path)}' -> No panels found, skipping watermark.")
        # Save without watermark to avoid losing the file in pipeline
        final_img = img_pil.convert("RGB")
        final_img.save(output_path, quality=100, subsampling=0)
        return

    # Find the bottom-most panel (max y + h)
    valid_panels.sort(key=lambda p: p[1] + p[3], reverse=True)
    bottom_most_panel = valid_panels[0]
    
    x, y, w, h = bottom_most_panel
    
    # Prepare watermark
    wm = watermark.copy()
    wm_w, wm_h = wm.size
    
    # Resize watermark to 85% of the panel's width
    target_w = int(w * 0.85)
    scale = target_w / wm_w
    target_h = max(1, int(wm_h * scale))
    
    wm = wm.resize((target_w, target_h), Image.Resampling.LANCZOS)
    wm_w, wm_h = wm.size
        
    # Position: Horizontally centered, at the very bottom edge of the panel
    pos_x = x + (w - wm_w) // 2
    pos_y = y + h - wm_h
    
    # Ensure coordinates don't go out of bounds
    pos_x = max(x, pos_x)
    pos_y = max(y, pos_y)
    
    # Paste watermark
    img_pil.paste(wm, (pos_x, pos_y), wm)

    # Convert back to RGB and save with maximum quality to prevent quality loss
    final_img = img_pil.convert("RGB")
    final_img.save(output_path, quality=100, subsampling=0)
    print(f"Processed '{os.path.basename(image_path)}' -> Placed 1 watermark on bottom panel.")


def main():
    input_dir = "input"
    output_dir = "output"
    watermark_path = "watermark.png"
    
    print("Manga/Webtoon Panel Watermarker")
    print("-" * 30)
    
    if not os.path.exists(watermark_path):
        print(f"[ERROR] Watermark image not found at '{watermark_path}'.")
        print("Please place a 'watermark.png' file in the same directory as this script.")
        return

    # Check for input images
    extensions = ('*.png', '*.jpg', '*.jpeg', '*.webp')
    image_paths = set()
    for ext in extensions:
        for path in glob.glob(os.path.join(input_dir, ext)):
            image_paths.add(path)
        # Also check for uppercase extensions (useful on Linux/macOS)
        for path in glob.glob(os.path.join(input_dir, ext.upper())):
            image_paths.add(path)
            
    image_paths = list(image_paths)
        
    if not image_paths:
        print(f"[INFO] No images found in the '{input_dir}/' directory.")
        print("Please place some images there to process.")
        return
        
    print(f"[INFO] Found {len(image_paths)} images to process.")
    
    for img_path in image_paths:
        filename = os.path.basename(img_path)
        out_path = os.path.join(output_dir, filename)
        add_watermark_to_panels(img_path, watermark_path, out_path)
        
    print("-" * 30)
    print("Processing complete!")

if __name__ == "__main__":
    main()
