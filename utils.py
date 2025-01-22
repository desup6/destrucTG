from PIL import Image
from io import BytesIO

def add_watermark(image_bytes, watermark_bytes):
    img = Image.open(BytesIO(image_bytes)).convert("RGBA")
    w, h = img.size
    watermark = Image.open(watermark_bytes)
    ww, wh = watermark.size
    new_width = w // 10
    new_height = wh // (ww // new_width)
    watermark = watermark.resize((new_width, new_height)).convert("RGBA")
    img.alpha_composite(watermark, (w - new_width, h - new_height))
    bio = BytesIO()
    bio.name = 'image.png'
    img.save(bio, format="PNG")
    bio.seek(0)
    return bio

