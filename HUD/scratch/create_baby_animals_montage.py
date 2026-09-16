import os
from PIL import Image, ImageDraw, ImageFont

RENDERS_DIR = r"C:\Users\casey\Desktop\Homesteader\HUD\scratch\renders_animals"
OUT_PATH = r"C:\Users\casey\.gemini\antigravity\brain\6940286d-0152-4b36-9e37-9e6cff11c21a\baby_animals_showcase.png"

# Group by species
GROUPS = [
    ("CALVES (Cattle)", [
        ("Holstein Spotted", "SKM_Animal_Cow_Calf_Holstein_render.png"),
        ("Jersey Caramel", "SKM_Animal_Cow_Calf_Jersey_render.png"),
        ("Highland Shaggy", "SKM_Animal_Cow_Calf_Highland_render.png"),
        ("Chestnut Star", "SKM_Animal_Cow_Calf_Chestnut_render.png"),
    ]),
    ("PIGLETS (Pigs)", [
        ("Yorkshire Pink", "SKM_Animal_Pig_Piglet_Pink_render.png"),
        ("Hampshire Belted", "SKM_Animal_Pig_Piglet_Hampshire_render.png"),
        ("Duroc Auburn", "SKM_Animal_Pig_Piglet_Duroc_render.png"),
        ("Spotted Piebald", "SKM_Animal_Pig_Piglet_Spotted_render.png"),
    ]),
    ("LAMBS (Sheep)", [
        ("Suffolk Mask", "SKM_Animal_Sheep_Lamb_Suffolk_render.png"),
        ("Pure White", "SKM_Animal_Sheep_Lamb_White_render.png"),
        ("Natural Tan", "SKM_Animal_Sheep_Lamb_Tan_render.png"),
        ("Spotted Fleece", "SKM_Animal_Sheep_Lamb_Spotted_render.png"),
    ]),
    ("GOAT KIDS (Goats)", [
        ("Alpine Brown", "SKM_Animal_Goat_Kid_Brown_render.png"),
        ("Saanen White", "SKM_Animal_Goat_Kid_White_render.png"),
        ("Piebald Black&White", "SKM_Animal_Goat_Kid_BlackWhite_render.png"),
    ]),
    ("CHICKS (Chickens)", [
        ("Golden Yellow", "SKM_Animal_Chicken_Chick_Yellow_render.png"),
        ("Soft White", "SKM_Animal_Chicken_Chick_White_render.png"),
        ("Barred Rock", "SKM_Animal_Chicken_Chick_Barred_render.png"),
        ("Rhode Island Brown", "SKM_Animal_Chicken_Chick_Brown_render.png"),
    ]),
]

# Layout: 5 rows (one per species)
CELL_SIZE = 240
HEADER_H = 40
PAD = 20
ROW_H = CELL_SIZE + HEADER_H + PAD
MAX_COLS = 4
W = PAD + MAX_COLS * (CELL_SIZE + PAD)
H = PAD + len(GROUPS) * ROW_H + 60

canvas = Image.new("RGBA", (W, H), (22, 27, 34, 255))
draw = ImageDraw.Draw(canvas)

# Title
draw.text((PAD, 15), "HOMESTEADER BABY ANIMALS SUITE (RIGGED & TEXTURED)", fill=(240, 240, 245, 255))

y_curr = 60
for group_title, items in GROUPS:
    draw.rectangle([PAD, y_curr, W - PAD, y_curr + 30], fill=(35, 42, 54, 255))
    draw.text((PAD + 10, y_curr + 6), group_title, fill=(88, 166, 255, 255))
    y_cells = y_curr + 35
    
    for idx, (label, fname) in enumerate(items):
        x = PAD + idx * (CELL_SIZE + PAD)
        # Background card
        draw.rectangle([x, y_cells, x + CELL_SIZE, y_cells + CELL_SIZE], fill=(28, 33, 40, 255), outline=(48, 54, 61, 255))
        
        fpath = os.path.join(RENDERS_DIR, fname)
        if os.path.exists(fpath):
            im = Image.open(fpath).convert("RGBA")
            im.thumbnail((CELL_SIZE - 20, CELL_SIZE - 40), Image.Resampling.LANCZOS)
            cx = x + (CELL_SIZE - im.width) // 2
            cy = y_cells + 10 + (CELL_SIZE - 40 - im.height) // 2
            canvas.paste(im, (cx, cy), im)
            
        # Label
        draw.text((x + 10, y_cells + CELL_SIZE - 24), label, fill=(201, 209, 217, 255))
        
    y_curr += ROW_H

canvas.save(OUT_PATH, "PNG")
print(f"Saved montage to {OUT_PATH}")

