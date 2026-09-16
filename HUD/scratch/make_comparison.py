import os
from PIL import Image, ImageDraw, ImageFont

ORIGINAL_ICON = r"C:\Users\casey\Desktop\Homesteader\HUD\scratch\batch3\all_extracted\baby_calf.png"
RENDER_PATH = r"C:\Users\casey\Desktop\Homesteader\HUD\scratch\renders_test\instantmesh_calf_render_front.png"
OUT_PATH = r"C:\Users\casey\.gemini\antigravity\brain\6940286d-0152-4b36-9e37-9e6cff11c21a\calf_icon_comparison.png"

if os.path.exists(ORIGINAL_ICON) and os.path.exists(RENDER_PATH):
    orig = Image.open(ORIGINAL_ICON).convert("RGBA")
    rend = Image.open(RENDER_PATH).convert("RGBA")
    
    # Canvas
    W, H = 700, 360
    canvas = Image.new("RGBA", (W, H), (22, 27, 34, 255))
    draw = ImageDraw.Draw(canvas)
    
    # Title
    draw.text((20, 15), "TEST COMPARISON: Original Item Icon vs. New Organic 3D Model Render", fill=(240, 240, 245, 255))
    
    # Cards
    card_w = 320
    card_h = 280
    
    # Card 1: Original
    draw.rectangle([20, 50, 20 + card_w, 50 + card_h], fill=(28, 33, 40, 255), outline=(48, 54, 61, 255))
    draw.text((35, 60), "1. TARGET ITEM ICON (baby_calf.png)", fill=(88, 166, 255, 255))
    orig_scaled = orig.resize((200, 200), Image.Resampling.LANCZOS)
    canvas.paste(orig_scaled, (20 + (card_w - 200)//2, 50 + 40), orig_scaled)
    
    # Card 2: 3D Render
    draw.rectangle([360, 50, 360 + card_w, 50 + card_h], fill=(28, 33, 40, 255), outline=(48, 54, 61, 255))
    draw.text((375, 60), "2. NEW ORGANIC 3D MODEL RENDER", fill=(46, 160, 67, 255))
    
    bbox = rend.split()[3].getbbox()
    if bbox:
        cropped = rend.crop(bbox)
        scale = min(200 / cropped.width, 200 / cropped.height)
        rw, rh = int(cropped.width * scale), int(cropped.height * scale)
        rend_scaled = cropped.resize((rw, rh), Image.Resampling.LANCZOS)
        canvas.paste(rend_scaled, (360 + (card_w - rw)//2, 50 + 40 + (200 - rh)//2), rend_scaled)
    
    canvas.save(OUT_PATH)
    print(f"Saved comparison to: {OUT_PATH}")

