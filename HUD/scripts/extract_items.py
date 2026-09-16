import os
import math
from PIL import Image

_this_dir = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(_this_dir) if os.path.basename(_this_dir) == chr(115)+chr(99)+chr(114)+chr(105)+chr(112)+chr(116)+chr(115) else _this_dir
CONCEPTS_DIR = os.path.join(BASE_DIR, "concepts")
ITEMS_DIR = os.path.join(BASE_DIR, "assets", "items")
PNG_DIR = os.path.join(BASE_DIR, "assets", "png")
os.makedirs(ITEMS_DIR, exist_ok=True)
os.makedirs(PNG_DIR, exist_ok=True)

sheet_path = os.path.join(CONCEPTS_DIR, "compact_modern_ui_kit_sheet.jpg")
sheet = Image.open(sheet_path).convert("RGBA")

modern_sheet_path = os.path.join(CONCEPTS_DIR, "modern_homesteader_ui_kit.jpg")
modern_sheet = Image.open(modern_sheet_path).convert("RGBA")

def make_transparent(crop_img, bg_color=(44, 52, 63), tolerance=20, feather=16):
    """Cleanly converts dark slate background into a smooth transparent alpha channel."""
    rgba = crop_img.convert("RGBA")
    data = list(rgba.getdata())
    new_data = []
    
    br, bg, bb = bg_color[:3]
    for item in data:
        r, g, b, a = item
        dist = math.sqrt((r - br)**2 + (g - bg)**2 + (b - bb)**2)
        if dist <= tolerance:
            new_data.append((0, 0, 0, 0))
        elif dist >= tolerance + feather:
            new_data.append((r, g, b, 255))
        else:
            alpha = int(255 * ((dist - tolerance) / feather))
            new_data.append((r, g, b, alpha))
            
    rgba.putdata(new_data)
    return rgba

print("--- 1. Extracting 12 Low-Poly Game Items from Compact Modern UI Kit ---")
COLS = [764, 867, 970, 1073, 1176, 1278]
BOX_SIZE = 80

ROW1_ITEMS = [
    ("icon_heart", "Ruby Heart"),
    ("icon_stamina", "Cyan Lightning Bolt"),
    ("icon_coin", "Gold Coin"),
    ("icon_water", "Crystal Water Droplet"),
    ("icon_solar", "Solar Sun"),
    ("icon_battery", "Battery Power"),
]

ROW2_ITEMS = [
    ("icon_axe", "Woodcutting Axe"),
    ("icon_watering_can", "Watering Can"),
    ("icon_wood_log", "Timber Log"),
    ("icon_wheat", "Wheat Stalk"),
    ("icon_seeds", "Crop Seeds"),
    ("icon_bread", "Baked Bread"),
]

for i, (name, label) in enumerate(ROW1_ITEMS):
    cx = COLS[i]
    cy = 586
    x1, y1 = cx - BOX_SIZE // 2, cy - BOX_SIZE // 2
    crop = sheet.crop((x1, y1, x1 + BOX_SIZE, y1 + BOX_SIZE))
    crop_trans = make_transparent(crop, bg_color=(44, 52, 63))
    
    crop.save(os.path.join(ITEMS_DIR, f"{name}_opaque.png"))
    crop_trans.save(os.path.join(ITEMS_DIR, f"{name}.png"))
    crop_trans.save(os.path.join(PNG_DIR, f"{name}.png"))
    print(f"  Extracted {label} -> assets/items/{name}.png")

for i, (name, label) in enumerate(ROW2_ITEMS):
    cx = COLS[i]
    cy = 688
    x1, y1 = cx - BOX_SIZE // 2, cy - BOX_SIZE // 2
    crop = sheet.crop((x1, y1, x1 + BOX_SIZE, y1 + BOX_SIZE))
    crop_trans = make_transparent(crop, bg_color=(44, 52, 63))
    
    crop.save(os.path.join(ITEMS_DIR, f"{name}_opaque.png"))
    crop_trans.save(os.path.join(ITEMS_DIR, f"{name}.png"))
    crop_trans.save(os.path.join(PNG_DIR, f"{name}.png"))
    print(f"  Extracted {label} -> assets/items/{name}.png")

print("\n--- 2. Extracting Pickaxe & Shovel in Matching Style ---")
# From modern_homesteader_ui_kit:
# Pickaxe: cx ~ 800, cy ~ 695; Shovel: cx ~ 905, cy ~ 695
tools = [
    ("icon_pickaxe", "Mining Pickaxe", 800, 695),
    ("icon_shovel", "Digging Shovel", 905, 695),
]
for name, label, cx, cy in tools:
    x1, y1 = cx - BOX_SIZE // 2, cy - BOX_SIZE // 2
    crop = modern_sheet.crop((x1, y1, x1 + BOX_SIZE, y1 + BOX_SIZE))
    crop_trans = make_transparent(crop, bg_color=(36, 35, 41), tolerance=22, feather=18)
    crop.save(os.path.join(ITEMS_DIR, f"{name}_opaque.png"))
    crop_trans.save(os.path.join(ITEMS_DIR, f"{name}.png"))
    crop_trans.save(os.path.join(PNG_DIR, f"{name}.png"))
    print(f"  Extracted {label} -> assets/items/{name}.png")

print("\n--- 3. Extracting Top Bar, Hotbar & Dialog Components ---")
# Top-Left Player Status Card: x: 50..425, y: 70..155
status_crop = sheet.crop((50, 70, 428, 155))
make_transparent(status_crop, (44, 52, 63), tolerance=16, feather=14).save(os.path.join(PNG_DIR, "compact_player_status_kit.png"))
print("  Extracted compact_player_status_kit.png")

# Top-Center Time Module: x: 520..845, y: 70..155
time_crop = sheet.crop((520, 70, 845, 155))
make_transparent(time_crop, (44, 52, 63), tolerance=16, feather=14).save(os.path.join(PNG_DIR, "compact_time_season_kit.png"))
print("  Extracted compact_time_season_kit.png")

# Top-Right Resource Capsule: x: 940..1320, y: 70..155
res_crop = sheet.crop((940, 70, 1320, 155))
make_transparent(res_crop, (44, 52, 63), tolerance=16, feather=14).save(os.path.join(PNG_DIR, "compact_resources_kit.png"))
print("  Extracted compact_resources_kit.png")

# Hotbar Tray: x: 50..810, y: 238..294
hotbar_crop = sheet.crop((50, 238, 810, 294))
make_transparent(hotbar_crop, (44, 52, 63), tolerance=16, feather=14).save(os.path.join(PNG_DIR, "compact_hotbar_tray_kit.png"))
print("  Extracted compact_hotbar_tray_kit.png")

# Golden Active Selector Bracket: x: 275..355, y: 235..298
sel_crop = sheet.crop((275, 235, 355, 298))
make_transparent(sel_crop, (44, 52, 63), tolerance=18, feather=14).save(os.path.join(PNG_DIR, "compact_selector_active_kit.png"))
print("  Extracted compact_selector_active_kit.png")

# Crafting Window Dialog: x: 50..660, y: 460..735
win_crop = sheet.crop((50, 460, 660, 735))
make_transparent(win_crop, (44, 52, 63), tolerance=16, feather=14).save(os.path.join(PNG_DIR, "compact_window_crafting_kit.png"))
print("  Extracted compact_window_crafting_kit.png")

print("\nFinished extracting all assets from the compact modern UI kit sheet!")

