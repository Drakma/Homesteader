import os
import shutil
from PIL import Image, ImageDraw, ImageFont

GROUND_DIR = "assets/ground/textures"
ARTIFACT_DIR = r"C:\Users\casey\.gemini\antigravity\brain\6940286d-0152-4b36-9e37-9e6cff11c21a"

ground_types = [
    "grass", "dirt", "gravel", "sand", "snow",
    "farmland", "forest_floor", "mud", "tall_grass", "trampled_grass",
    "path", "road", "black_top", "concrete", "bricks",
    "flagstone", "wood_planks", "swamp", "pond", "deep_water"
]

# 1. Montage of all 20 terrain BaseColors
cols, rows = 5, 4
tile_s = 200
montage = Image.new("RGB", (cols * tile_s, rows * (tile_s + 28)), (22, 26, 34))
draw = ImageDraw.Draw(montage)

for idx, g_name in enumerate(ground_types):
    c = idx % cols
    r = idx // cols
    x = c * tile_s
    y = r * (tile_s + 28)
    
    tex_path = os.path.join(GROUND_DIR, g_name, f"T_Ground_{g_name}_BaseColor.png")
    if os.path.exists(tex_path):
        img = Image.open(tex_path).resize((tile_s, tile_s), Image.Resampling.LANCZOS)
        montage.paste(img, (x, y))
    draw.rectangle([x, y + tile_s, x + tile_s, y + tile_s + 28], fill=(16, 19, 26))
    draw.text((x + 8, y + tile_s + 6), g_name.replace("_", " ").title(), fill=(220, 225, 235))

montage_path = "scratch/terrain_textures_all20_montage.png"
montage.save(montage_path)
shutil.copy(montage_path, os.path.join(ARTIFACT_DIR, "terrain_textures_all20_montage.png"))
print("Saved all 20 montage!")

# 2. Expansive 3x3 tiled preview of Gravel (Compacted Small Rocks)
def make_3x3_tile(g_name):
    tex_path = os.path.join(GROUND_DIR, g_name, f"T_Ground_{g_name}_BaseColor.png")
    img = Image.open(tex_path)
    w, h = img.size
    tiled = Image.new("RGB", (w * 3, h * 3))
    for ty in range(3):
        for tx in range(3):
            tiled.paste(img, (tx * w, ty * h))
    out_path = f"scratch/tiled_3x3_{g_name}.png"
    tiled.resize((600, 600), Image.Resampling.LANCZOS).save(out_path)
    shutil.copy(out_path, os.path.join(ARTIFACT_DIR, f"tiled_3x3_{g_name}.png"))
    print(f"Saved tiled 3x3 for {g_name}!")

make_3x3_tile("gravel")
make_3x3_tile("grass")
make_3x3_tile("dirt")
make_3x3_tile("farmland")

