import os
import math
from PIL import Image, ImageDraw

_this_dir = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(_this_dir)  # tools/ sits at the repo root (one level up)
CONCEPTS_DIR = os.path.join(BASE_DIR, "concepts")
ITEMS_DIR = os.path.join(BASE_DIR, "assets", "items")
FRAMED_DIR = os.path.join(ITEMS_DIR, "framed")

# Unreal Engine UI directory
UNREAL_ICONS_DIR = r"C:\Users\casey\Desktop\Homesteader\Homesteader\Content\Homesteader\UI\Icons"
UNREAL_FRAMED_DIR = os.path.join(UNREAL_ICONS_DIR, "Framed")

for d in [ITEMS_DIR, FRAMED_DIR, UNREAL_ICONS_DIR, UNREAL_FRAMED_DIR]:
    os.makedirs(d, exist_ok=True)

TARGET_SIZE = 128  # High resolution 128x128 game icons

def extract_and_process_item(sheet, cx, cy, box_size, bg_color, name, label, tolerance=24, feather=16):
    """
    Extracts an item from a sheet.
    Generates:
      1. Isolated transparent item (centered at 128x128).
      2. Framed icon tile (128x128 with rounded transparent corners).
    """
    half = box_size // 2
    # 1. Framed crop (slightly larger box)
    frame_box = int(box_size * 1.08)
    f_half = frame_box // 2
    frame_crop = sheet.crop((cx - f_half, cy - f_half, cx + f_half, cy + f_half)).convert("RGBA")
    
    # Create rounded corner mask for framed tile
    mask = Image.new("L", frame_crop.size, 0)
    draw_mask = ImageDraw.Draw(mask)
    draw_mask.rounded_rectangle([(0, 0), (frame_crop.width - 1, frame_crop.height - 1)], radius=int(frame_crop.width * 0.16), fill=255)
    
    framed_tile = frame_crop.copy()
    framed_tile.putalpha(mask)
    framed_tile_128 = framed_tile.resize((TARGET_SIZE, TARGET_SIZE), Image.Resampling.LANCZOS)
    
    # Save framed tile
    framed_tile_128.save(os.path.join(FRAMED_DIR, f"{name}.png"))
    framed_tile_128.save(os.path.join(UNREAL_FRAMED_DIR, f"{name}.png"))
    
    # 2. Isolated transparent item
    inner_crop = sheet.crop((cx - half, cy - half, cx + half, cy + half)).convert("RGBA")
    data = list(inner_crop.getdata())
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
            
    inner_crop.putdata(new_data)
    
    # Crop tightly to item pixels
    bbox = inner_crop.getbbox()
    if bbox:
        item_only = inner_crop.crop(bbox)
        # Center in square canvas with margins
        canvas = Image.new("RGBA", (TARGET_SIZE, TARGET_SIZE), (0, 0, 0, 0))
        max_dim = int(TARGET_SIZE * 0.86)
        scale = min(max_dim / item_only.width, max_dim / item_only.height)
        new_w = max(1, int(item_only.width * scale))
        new_h = max(1, int(item_only.height * scale))
        resized = item_only.resize((new_w, new_h), Image.Resampling.LANCZOS)
        offset_x = (TARGET_SIZE - new_w) // 2
        offset_y = (TARGET_SIZE - new_h) // 2
        canvas.paste(resized, (offset_x, offset_y), resized)
        
        # Save isolated transparent item
        canvas.save(os.path.join(ITEMS_DIR, f"{name}.png"))
        canvas.save(os.path.join(UNREAL_ICONS_DIR, f"{name}.png"))
    else:
        # Fallback to framed if bbox is empty
        framed_tile_128.save(os.path.join(ITEMS_DIR, f"{name}.png"))
        framed_tile_128.save(os.path.join(UNREAL_ICONS_DIR, f"{name}.png"))

    print(f"  Processed {name} ({label})")


# -------------------------------------------------------------------------
# SHEET 1: CROPS & PRODUCE (10 items)
# -------------------------------------------------------------------------
print("\n[1/5] Processing Crops & Produce...")
crops_img = Image.open(os.path.join(CONCEPTS_DIR, "sheet_crops_produce.jpg")).convert("RGBA")
crops_bg = (34, 42, 53)
crops_rows = [217, 551]
crops_cols = [161, 424, 693, 963, 1215]

crops_grid = [
    [("crop_corn", "Corn"), ("crop_tomato", "Tomato"), ("crop_carrot", "Carrot"), ("crop_wheat", "Wheat"), ("crop_potato", "Potato")],
    [("crop_pumpkin", "Pumpkin"), ("crop_strawberry", "Strawberry"), ("crop_sunflower", "Sunflower"), ("crop_cotton", "Cotton Boll"), ("crop_herb", "Herbs")]
]

for r_idx, row in enumerate(crops_grid):
    cy = crops_rows[r_idx]
    for c_idx, (item_id, label) in enumerate(row):
        cx = crops_cols[c_idx]
        extract_and_process_item(crops_img, cx, cy, box_size=165, bg_color=crops_bg, name=item_id, label=label, tolerance=25, feather=18)


# -------------------------------------------------------------------------
# SHEET 2: SEEDS (10 items)
# -------------------------------------------------------------------------
print("\n[2/5] Processing Seeds...")
seeds_img = Image.open(os.path.join(CONCEPTS_DIR, "sheet_seeds.jpg")).convert("RGBA")
seeds_bg = (34, 42, 53)
seeds_rows = [207, 556]
seeds_cols = [184, 440, 687, 939, 1191]

seeds_grid = [
    [("seed_corn", "Corn Seeds"), ("seed_tomato", "Tomato Seeds"), ("seed_carrot", "Carrot Seeds"), ("seed_wheat", "Wheat Seeds"), ("seed_potato", "Potato Seeds")],
    [("seed_pumpkin", "Pumpkin Seeds"), ("seed_strawberry", "Strawberry Seeds"), ("seed_sunflower", "Sunflower Seeds"), ("seed_cotton", "Cotton Seeds"), ("seed_herb", "Herb Seeds")]
]

for r_idx, row in enumerate(seeds_grid):
    cy = seeds_rows[r_idx]
    for c_idx, (item_id, label) in enumerate(row):
        cx = seeds_cols[c_idx]
        extract_and_process_item(seeds_img, cx, cy, box_size=165, bg_color=seeds_bg, name=item_id, label=label, tolerance=24, feather=16)


# -------------------------------------------------------------------------
# SHEET 3: TOOLS (9 items)
# -------------------------------------------------------------------------
print("\n[3/5] Processing Tools...")
tools_img = Image.open(os.path.join(CONCEPTS_DIR, "sheet_tools.jpg")).convert("RGBA")
tools_bg = (44, 52, 63)
tools_rows = [190, 410, 630]
tools_cols = [441, 688, 934]

tools_grid = [
    [("tool_hoe", "Hoe"), ("tool_watering_can", "Watering Can"), ("tool_axe", "Axe")],
    [("tool_pickaxe", "Pickaxe"), ("tool_sickle", "Sickle"), ("tool_hammer", "Hammer")],
    [("tool_wrench", "Wrench"), ("tool_shovel", "Shovel"), ("tool_seedbag", "Seed Bag")]
]

for r_idx, row in enumerate(tools_grid):
    cy = tools_rows[r_idx]
    for c_idx, (item_id, label) in enumerate(row):
        cx = tools_cols[c_idx]
        extract_and_process_item(tools_img, cx, cy, box_size=170, bg_color=tools_bg, name=item_id, label=label, tolerance=24, feather=16)


# -------------------------------------------------------------------------
# SHEET 4: MATERIALS, FOOD & FUEL (12 items)
# -------------------------------------------------------------------------
print("\n[4/5] Processing Materials, Food & Fuel...")
mff_img = Image.open(os.path.join(CONCEPTS_DIR, "sheet_materials_food_fuel.jpg")).convert("RGBA")
mff_bg = (44, 52, 63)
mff_rows = [152, 387, 637]
mff_cols = [152, 514, 871, 1229]

mff_grid = [
    [("mat_lumber", "Lumber"), ("mat_stone", "Stone"), ("mat_metal", "Metal Sheet"), ("mat_glass", "Glass Pane")],
    [("food_bread", "Bread"), ("food_stew", "Vegetable Stew"), ("food_apple", "Apple"), ("food_cheese", "Cheese")],
    [("mat_rope", "Rope"), ("mat_fertilizer", "Fertilizer"), ("fuel_gasoline", "Gasoline"), ("fuel_firewood", "Firewood")]
]

for r_idx, row in enumerate(mff_grid):
    cy = mff_rows[r_idx]
    for c_idx, (item_id, label) in enumerate(row):
        cx = mff_cols[c_idx]
        extract_and_process_item(mff_img, cx, cy, box_size=180, bg_color=mff_bg, name=item_id, label=label, tolerance=24, feather=16)


# -------------------------------------------------------------------------
# SHEET 5: ANIMAL PRODUCTS, MEATS & PELTS (12 items + derivations)
# -------------------------------------------------------------------------
print("\n[5/5] Processing Animal Products, Meats & Pelts...")
amp_img = Image.open(os.path.join(CONCEPTS_DIR, "sheet_animals_meats_pelts.jpg")).convert("RGBA")
amp_bg = (44, 52, 63)
amp_rows = [139, 384, 629]
amp_cols = [150, 580, 805, 1230]

amp_grid = [
    [("animal_egg", "Egg"), ("animal_milk", "Milk Jug"), ("animal_wool", "Wool"), ("animal_truffle", "Truffle")],
    [("meat_chicken", "Chicken Meat"), ("meat_beef", "Beef"), ("meat_pork", "Pork"), ("meat_mutton", "Mutton")],
    [("mat_feather", "Feathers"), ("mat_leather", "Leather"), ("pelt_sheep", "Sheepskin"), ("fuel_propane", "Propane Canister")]
]

for r_idx, row in enumerate(amp_grid):
    cy = amp_rows[r_idx]
    for c_idx, (item_id, label) in enumerate(row):
        cx = amp_cols[c_idx]
        extract_and_process_item(amp_img, cx, cy, box_size=180, bg_color=amp_bg, name=item_id, label=label, tolerance=24, feather=16)

# Derived aliases for animals:
print("\nCreating derived animal aliases...")
aliases = [
    ("meat_beef.png", "animal_meat.png", "Generic Meat (Dog Food)"),
    ("mat_leather.png", "pelt_cow.png", "Cow Pelt"),
    ("meat_mutton.png", "meat_goat.png", "Goat Meat"),
    ("mat_leather.png", "pelt_goat.png", "Goat Pelt / Hide"),
]
for src, dst, desc in aliases:
    # Isolated
    src_p = os.path.join(ITEMS_DIR, src)
    dst_p = os.path.join(ITEMS_DIR, dst)
    if os.path.exists(src_p):
        img = Image.open(src_p)
        img.save(dst_p)
        img.save(os.path.join(UNREAL_ICONS_DIR, dst))
    # Framed
    f_src_p = os.path.join(FRAMED_DIR, src)
    f_dst_p = os.path.join(FRAMED_DIR, dst)
    if os.path.exists(f_src_p):
        f_img = Image.open(f_src_p)
        f_img.save(f_dst_p)
        f_img.save(os.path.join(UNREAL_FRAMED_DIR, dst))
    print(f"  Created alias {dst} ({desc})")

print("\nSuccessfully generated ALL game items from DataTable CSVs!")
