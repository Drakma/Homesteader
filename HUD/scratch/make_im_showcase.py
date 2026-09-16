import os
from PIL import Image, ImageDraw

ICON_PATH = r"C:\Users\casey\Desktop\Homesteader\HUD\scratch\batch3\all_extracted\baby_calf.png"
RENDERS_DIR = r"C:\Users\casey\Desktop\Homesteader\HUD\scratch\renders_test"
OUT_PATH = r"C:\Users\casey\.gemini\antigravity\brain\6940286d-0152-4b36-9e37-9e6cff11c21a\instantmesh_showcase.png"

orig = Image.open(ICON_PATH).convert("RGBA")
v0 = Image.open(os.path.join(RENDERS_DIR, "im_turntable_0deg.png")).convert("RGBA")
v90 = Image.open(os.path.join(RENDERS_DIR, "im_turntable_90deg.png")).convert("RGBA")
v180 = Image.open(os.path.join(RENDERS_DIR, "im_turntable_180deg.png")).convert("RGBA")
v270 = Image.open(os.path.join(RENDERS_DIR, "im_turntable_270deg.png")).convert("RGBA")

W, H = 1100, 300
canvas = Image.new("RGBA", (W, H), (22, 27, 34, 255))
draw = ImageDraw.Draw(canvas)

draw.text((20, 15), "InstantMesh AI 3D Reconstruction Test (Free API): Target Icon vs. 360 TurnTable Views", fill=(240, 240, 245, 255))

panels = [
    ("Target Icon", orig),
    ("View 0°", v0),
    ("View 90°", v90),
    ("View 180°", v180),
    ("View 270°", v270),
]

card_w = 200
card_h = 230

for idx, (title, img) in enumerate(panels):
    x = 20 + idx * (card_w + 15)
    y = 45
    draw.rectangle([x, y, x + card_w, y + card_h], fill=(28, 33, 40, 255), outline=(48, 54, 61, 255))
    draw.text((x + 10, y + 10), title, fill=(88, 166, 255, 255) if idx == 0 else (46, 160, 67, 255))
    
    bbox = img.split()[3].getbbox()
    if bbox:
        cropped = img.crop(bbox)
        scale = min(170 / cropped.width, 170 / cropped.height)
        rw, rh = int(cropped.width * scale), int(cropped.height * scale)
        scaled = cropped.resize((rw, rh), Image.Resampling.LANCZOS)
        canvas.paste(scaled, (x + (card_w - rw)//2, y + 35 + (170 - rh)//2), scaled)

canvas.save(OUT_PATH)
print("Saved showcase to:", OUT_PATH)

