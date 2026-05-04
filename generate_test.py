from PIL import Image, ImageDraw

def create_dummy_images():
    # Create dummy watermark
    wm = Image.new('RGBA', (200, 50), (0, 0, 0, 0))
    d = ImageDraw.Draw(wm)
    d.rectangle([0, 0, 200, 50], fill=(255, 0, 0, 255))
    d.text((10, 10), "WATERMARK", fill=(255, 255, 255, 255))
    wm.save('watermark.png')

    # Create dummy manga strip (1000x3000)
    # White background, with 3 black rectangles as panels
    strip = Image.new('RGB', (1000, 3000), (255, 255, 255))
    d = ImageDraw.Draw(strip)
    
    # Panel 1
    d.rectangle([100, 100, 900, 800], fill=(0, 0, 0))
    
    # Panel 2
    d.rectangle([100, 1000, 900, 1900], fill=(0, 0, 0))
    
    # Panel 3
    d.rectangle([100, 2100, 900, 2900], fill=(0, 0, 0))
    
    strip.save('input/dummy_manga.png')

if __name__ == '__main__':
    create_dummy_images()
