import os
import math
import shutil
from PIL import Image

_this_dir = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(_this_dir)  # tools/ sits at the repo root (one level up)
CONCEPTS_DIR = os.path.join(BASE_DIR, "concepts")
HUD_ITEMS_DIR = os.path.join(BASE_DIR, "assets", "items")
HUD_PNG_DIR = os.path.join(BASE_DIR, "assets", "png")
UNREAL_ICONS_DIR = r"C:\Users\casey\Desktop\Homesteader\Homesteader\Content\Homesteader\UI\Icons"

for d in [HUD_ITEMS_DIR, HUD_PNG_DIR, UNREAL_ICONS_DIR]:
    os.makedirs(d, exist_ok=True)

TARGET_SIZE = 128
PADDING = 12  # Clean 12px margin on all sides of the 128x128 canvas

def clean_extract_item(sheet_img, cx, cy, box_radius, bg_colors, tol_low=20.0, tol_high=42.0, min_comp_size=25):
    """
    Extracts an isolated 3D item with 100% pure transparent background.
    - Uses multi-color background distance (handles slot interiors & outer backgrounds).
    - Feathered edge with de-spill to prevent background halos.
    - Connected component filtering to eliminate stray borders, slot edges, or frame lines.
    - Centers into 128x128 RGBA canvas with clean margins.
    """
    half = box_radius
    crop = sheet_img.crop((cx - half, cy - half, cx + half, cy + half)).convert("RGBA")
    w, h = crop.size
    
    # 1. Background color distance & de-spilling
    data = list(crop.getdata())
    new_data = []
    
    for r, g, b, a in data:
        # Distance to closest background reference
        best_dist = 999999.0
        best_bg = bg_colors[0]
        for bg in bg_colors:
            d = math.sqrt((r - bg[0])**2 + (g - bg[1])**2 + (b - bg[2])**2)
            if d < best_dist:
                best_dist = d
                best_bg = bg
                
        if best_dist <= tol_low:
            new_data.append((0, 0, 0, 0))
        elif best_dist >= tol_high:
            new_data.append((r, g, b, 255))
        else:
            ratio = (best_dist - tol_low) / (tol_high - tol_low)
            alpha = int(255 * ratio)
            # De-spill background color from semi-transparent edges
            unmix_r = min(255, max(0, int((r - (1.0 - ratio) * best_bg[0]) / max(0.1, ratio))))
            unmix_g = min(255, max(0, int((g - (1.0 - ratio) * best_bg[1]) / max(0.1, ratio))))
            unmix_b = min(255, max(0, int((b - (1.0 - ratio) * best_bg[2]) / max(0.1, ratio))))
            new_data.append((unmix_r, unmix_g, unmix_b, alpha))
            
    crop.putdata(new_data)
    
    # 2. Connected component analysis to keep ONLY the item
    alpha_channel = crop.split()[3]
    mask = [[alpha_channel.getpixel((x, y)) > 20 for x in range(w)] for y in range(h)]
    visited = [[False for _ in range(w)] for _ in range(h)]
    
    components = []
    for y in range(h):
        for x in range(w):
            if mask[y][x] and not visited[y][x]:
                comp = []
                queue = [(x, y)]
                visited[y][x] = True
                while queue:
                    qx, qy = queue.pop(0)
                    comp.append((qx, qy))
                    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nx, ny = qx + dx, qy + dy
                        if 0 <= nx < w and 0 <= ny < h and mask[ny][nx] and not visited[ny][nx]:
                            visited[ny][nx] = True
                            queue.append((nx, ny))
                components.append(comp)
                
    if not components:
        return None
        
    center_x, center_y = w / 2.0, h / 2.0
    
    def score_component(comp):
        size = len(comp)
        avg_x = sum(p[0] for p in comp) / size
        avg_y = sum(p[1] for p in comp) / size
        dist = math.sqrt((avg_x - center_x)**2 + (avg_y - center_y)**2)
        # Heavily favor large central components
        return size / (1.0 + (dist / 20.0)**2)
        
    components.sort(key=score_component, reverse=True)
    item_pixels = set(components[0])
    
    # Also attach secondary components if they are valid parts of the item (close to center & not border noise)
    for comp in components[1:]:
        size = len(comp)
        if size >= min_comp_size:
            avg_x = sum(p[0] for p in comp) / size
            avg_y = sum(p[1] for p in comp) / size
            dist = math.sqrt((avg_x - center_x)**2 + (avg_y - center_y)**2)
            touches_perimeter = any(p[0] <= 1 or p[0] >= w - 2 or p[1] <= 1 or p[1] >= h - 2 for p in comp)
            if dist < 42.0 and not touches_perimeter:
                item_pixels.update(comp)
                
    # Build isolated item image
    clean_crop = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    for x, y in item_pixels:
        clean_crop.putpixel((x, y), crop.getpixel((x, y)))
        
    # Crop tightly to item bounds
    bbox = clean_crop.split()[3].getbbox()
    if not bbox:
        return None
    item_only = clean_crop.crop(bbox)
    
    # Center into target square with padding
    canvas = Image.new("RGBA", (TARGET_SIZE, TARGET_SIZE), (0, 0, 0, 0))
    max_dim = TARGET_SIZE - (PADDING * 2)
    scale = min(max_dim / item_only.width, max_dim / item_only.height)
    new_w = max(1, int(item_only.width * scale))
    new_h = max(1, int(item_only.height * scale))
    resized = item_only.resize((new_w, new_h), Image.Resampling.LANCZOS)
    
    offset_x = (TARGET_SIZE - new_w) // 2
    offset_y = (TARGET_SIZE - new_h) // 2
    canvas.paste(resized, (offset_x, offset_y), resized)
    
    return canvas


def main():
    print("=== EXTRACTING ALL ITEMS WITH 100% PURE TRANSPARENT BACKGROUNDS ===")
    
    # Remove any existing opaque or framed files to prevent confusion
    for d in [HUD_ITEMS_DIR, UNREAL_ICONS_DIR]:
        for f in os.listdir(d):
            if f.endswith("_opaque.png"):
                os.remove(os.path.join(d, f))
                print(f"  Removed obsolete opaque file: {f}")
        framed_sub = os.path.join(d, "framed")
        if os.path.exists(framed_sub):
            shutil.rmtree(framed_sub)
            print(f"  Removed framed directory from {d}")
        Framed_sub = os.path.join(d, "Framed")
        if os.path.exists(Framed_sub):
            shutil.rmtree(Framed_sub)
            print(f"  Removed Framed directory from {d}")

    extracted_icons = {}

    # 1. CROPS & PRODUCE (10 items)
    print("\n[1/6] Processing Crops & Produce...")
    crops_img = Image.open(os.path.join(CONCEPTS_DIR, "sheet_crops_produce.jpg")).convert("RGBA")
    crops_bg = [(36, 46, 56)]
    crops_grid = [
        [("crop_corn", 161, 217), ("crop_tomato", 424, 217), ("crop_carrot", 693, 217), ("crop_wheat", 963, 217), ("crop_potato", 1215, 217)],
        [("crop_pumpkin", 161, 551), ("crop_strawberry", 424, 551), ("crop_sunflower", 693, 551), ("crop_cotton", 963, 551), ("crop_herb", 1215, 551)]
    ]
    for row in crops_grid:
        for name, cx, cy in row:
            radius = 76 if name in ["crop_pumpkin", "crop_sunflower"] else 70
            icon = clean_extract_item(crops_img, cx, cy, box_radius=radius, bg_colors=crops_bg, tol_low=22.0, tol_high=40.0)
            if icon:
                extracted_icons[name] = icon
                print(f"  Cleaned {name} -> bbox={icon.split()[3].getbbox()}")

    # 2. SEEDS (10 items)
    print("\n[2/6] Processing Seeds...")
    seeds_img = Image.open(os.path.join(CONCEPTS_DIR, "sheet_seeds.jpg")).convert("RGBA")
    seeds_bg = [(34, 42, 53), (28, 36, 46)]
    seeds_grid = [
        [("seed_corn", 184, 207), ("seed_tomato", 440, 207), ("seed_carrot", 687, 207), ("seed_wheat", 939, 207), ("seed_potato", 1191, 207)],
        [("seed_pumpkin", 184, 556), ("seed_strawberry", 440, 556), ("seed_sunflower", 687, 556), ("seed_cotton", 939, 556), ("seed_herb", 1191, 556)]
    ]
    for row in seeds_grid:
        for name, cx, cy in row:
            icon = clean_extract_item(seeds_img, cx, cy, box_radius=68, bg_colors=seeds_bg, tol_low=22.0, tol_high=40.0)
            if icon:
                extracted_icons[name] = icon
                print(f"  Cleaned {name} -> bbox={icon.split()[3].getbbox()}")

    # 3. TOOLS (9 items)
    print("\n[3/6] Processing Tools (eliminating slate-blue slot box)...")
    tools_img = Image.open(os.path.join(CONCEPTS_DIR, "sheet_tools.jpg")).convert("RGBA")
    # Both slot interior and sheet background
    tools_bg = [(65, 78, 95), (44, 52, 63), (49, 57, 68)]
    tools_grid = [
        [("tool_hoe", 441, 190), ("tool_watering_can", 688, 190), ("tool_axe", 934, 190)],
        [("tool_pickaxe", 441, 410), ("tool_sickle", 688, 410), ("tool_hammer", 934, 410)],
        [("tool_wrench", 441, 630), ("tool_shovel", 688, 630), ("tool_seedbag", 934, 620)]
    ]
    for row in tools_grid:
        for name, cx, cy in row:
            radius = 70
            icon = clean_extract_item(tools_img, cx, cy, box_radius=radius, bg_colors=tools_bg, tol_low=22.0, tol_high=42.0)
            if icon:
                extracted_icons[name] = icon
                print(f"  Cleaned {name} -> bbox={icon.split()[3].getbbox()}")

    # 4. MATERIALS, FOOD & FUEL (12 items)
    print("\n[4/6] Processing Materials, Food & Fuel...")
    mff_img = Image.open(os.path.join(CONCEPTS_DIR, "sheet_materials_food_fuel.jpg")).convert("RGBA")
    mff_bg = [(47, 57, 69), (45, 55, 67)]
    mff_grid = [
        [("mat_lumber", 152, 152), ("mat_stone", 514, 152), ("mat_metal", 871, 152), ("mat_glass", 1229, 152)],
        [("food_bread", 152, 387), ("food_stew", 514, 387), ("food_apple", 871, 387), ("food_cheese", 1229, 387)],
        [("mat_rope", 152, 637), ("mat_fertilizer", 514, 637), ("fuel_gasoline", 871, 637), ("fuel_firewood", 1229, 637)]
    ]
    for row in mff_grid:
        for name, cx, cy in row:
            icon = clean_extract_item(mff_img, cx, cy, box_radius=68, bg_colors=mff_bg, tol_low=22.0, tol_high=40.0)
            if icon:
                extracted_icons[name] = icon
                print(f"  Cleaned {name} -> bbox={icon.split()[3].getbbox()}")

    # 5. ANIMAL PRODUCTS, MEATS & PELTS (12 items)
    print("\n[5/6] Processing Animal Products, Meats & Pelts (eliminating frame border)...")
    amp_img = Image.open(os.path.join(CONCEPTS_DIR, "sheet_animals_meats_pelts.jpg")).convert("RGBA")
    amp_bg = [(36, 45, 57), (43, 55, 69)]
    amp_grid = [
        [("animal_egg", 150, 139), ("animal_milk", 580, 139), ("animal_wool", 805, 139), ("animal_truffle", 1230, 139)],
        [("meat_chicken", 155, 388), ("meat_beef", 580, 384), ("meat_pork", 805, 384), ("meat_mutton", 1230, 384)],
        [("mat_feather", 150, 629), ("mat_leather", 580, 629), ("pelt_sheep", 805, 629), ("fuel_propane", 1230, 629)]
    ]
    for row in amp_grid:
        for name, cx, cy in row:
            icon = clean_extract_item(amp_img, cx, cy, box_radius=67, bg_colors=amp_bg, tol_low=20.0, tol_high=38.0)
            if icon:
                extracted_icons[name] = icon
                print(f"  Cleaned {name} -> bbox={icon.split()[3].getbbox()}")

    # 6. HUD STATUS ICONS (6 items)
    print("\n[6/6] Processing HUD Status Icons...")
    hud_sheet = Image.open(os.path.join(CONCEPTS_DIR, "compact_modern_ui_kit_sheet.jpg")).convert("RGBA")
    hud_bg = [(44, 52, 63)]
    status_icons = [
        ("icon_heart", 764, 586),
        ("icon_stamina", 867, 586),
        ("icon_coin", 970, 586),
        ("icon_water", 1073, 586),
        ("icon_solar", 1176, 586),
        ("icon_battery", 1278, 586),
    ]
    for name, cx, cy in status_icons:
        icon = clean_extract_item(hud_sheet, cx, cy, box_radius=38, bg_colors=hud_bg, tol_low=20.0, tol_high=38.0)
        if icon:
            extracted_icons[name] = icon
            print(f"  Cleaned {name} -> bbox={icon.split()[3].getbbox()}")

    # 7. DERIVED ALIASES & RE-MAPPINGS
    print("\nCreating derived aliases...")
    aliases = [
        ("meat_beef", "animal_meat"),
        ("mat_leather", "pelt_cow"),
        ("meat_mutton", "meat_goat"),
        ("mat_leather", "pelt_goat"),
        # Map tools and crops to legacy icon names
        ("tool_axe", "icon_axe"),
        ("tool_pickaxe", "icon_pickaxe"),
        ("tool_shovel", "icon_shovel"),
        ("tool_watering_can", "icon_watering_can"),
        ("crop_wheat", "icon_wheat"),
        ("seed_wheat", "icon_seeds"),
        ("food_bread", "icon_bread"),
        ("mat_lumber", "icon_wood_log"),
    ]
    for src, dst in aliases:
        if src in extracted_icons:
            extracted_icons[dst] = extracted_icons[src].copy()
            print(f"  Alias: {dst} -> {src}")

    # 8. SAVE TO ALL DESTINATION DIRECTORIES
    print("\nSaving all cleaned transparent icons to disk...")
    target_dirs = [HUD_ITEMS_DIR, UNREAL_ICONS_DIR, HUD_PNG_DIR]
    
    for name, img in extracted_icons.items():
        fname = f"{name}.png"
        for out_dir in target_dirs:
            img.save(os.path.join(out_dir, fname), "PNG")
            
    print(f"\nSUCCESS: Exported {len(extracted_icons)} 100% transparent icons to:")
    for out_dir in target_dirs:
        print(f"  - {out_dir}")

if __name__ == "__main__":
    main()

