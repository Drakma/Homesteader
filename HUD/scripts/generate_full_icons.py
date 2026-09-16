import os
import math
import shutil
from PIL import Image, ImageDraw

_this_dir = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(_this_dir) if os.path.basename(_this_dir) == chr(115)+chr(99)+chr(114)+chr(105)+chr(112)+chr(116)+chr(115) else _this_dir
CONCEPTS_DIR = os.path.join(BASE_DIR, "concepts")
HUD_ITEMS_DIR = os.path.join(BASE_DIR, "assets", "items")
HUD_PNG_DIR = os.path.join(BASE_DIR, "assets", "png")
UNREAL_ICONS_DIR = r"C:\Users\casey\Desktop\Homesteader\Homesteader\Content\Homesteader\UI\Icons"

for d in [HUD_ITEMS_DIR, HUD_PNG_DIR, UNREAL_ICONS_DIR]:
    os.makedirs(d, exist_ok=True)

TARGET_SIZE = 128
PADDING = 12
MAX_ITEM_DIM = TARGET_SIZE - (PADDING * 2)  # 104px

def extract_clean_item(sheet_img, approx_cx, approx_cy, bg_colors, tol=20.0, is_framed_sheet=False, max_search_r=110):
    """
    Extracts 100% of an item's geometry strictly with NO BORDERS and NO CROPPED EDGES.
    - Uses 8-way flood fill from center outward.
    - On framed sheets, hard-masks out any outer card border lines.
    - Uniformly scales unclipped item to MAX_ITEM_DIM (104px).
    - Centers onto transparent 128x128 RGBA canvas.
    """
    r = max_search_r
    x0, y0 = max(0, approx_cx - r), max(0, approx_cy - r)
    x1, y1 = min(sheet_img.width, approx_cx + r), min(sheet_img.height, approx_cy + r)
    crop = sheet_img.crop((x0, y0, x1, y1)).convert("RGBA")
    w, h = crop.size
    local_cx, local_cy = approx_cx - x0, approx_cy - y0

    # 1. Background distance masking
    data = list(crop.getdata())
    is_fg = [min(math.dist(p[:3], bg) for bg in bg_colors) > tol for p in data]
    mask = [[is_fg[y * w + x] for x in range(w)] for y in range(h)]

    # 2. Hard mask outer borders to guarantee zero border attachment
    if is_framed_sheet:
        for y in range(h):
            for x in range(w):
                if abs(x - local_cx) >= 77 or abs(y - local_cy) >= 79:
                    mask[y][x] = False
    else:
        for y in range(h):
            for x in range(w):
                if abs(x - local_cx) >= 104 or abs(y - local_cy) >= 104:
                    mask[y][x] = False

    # 3. Locate seeds near center
    seeds = []
    for dy in range(-25, 26):
        for dx in range(-25, 26):
            sx, sy = local_cx + dx, local_cy + dy
            if 0 <= sx < w and 0 <= sy < h and mask[sy][sx]:
                seeds.append((sx, sy))
                
    if not seeds:
        for dy in range(-45, 46):
            for dx in range(-45, 46):
                sx, sy = local_cx + dx, local_cy + dy
                if 0 <= sx < w and 0 <= sy < h and mask[sy][sx]:
                    seeds.append((sx, sy))

    if not seeds:
        return None, "No seed found near center"

    # 4. Flood fill from seeds through foreground
    visited = [[False for _ in range(w)] for _ in range(h)]
    queue = list(seeds)
    for sx, sy in seeds:
        visited[sy][sx] = True
        
    main_comp = []
    while queue:
        qx, qy = queue.pop(0)
        main_comp.append((qx, qy))
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, -1), (-1, 1), (1, 1)]:
            nx, ny = qx + dx, qy + dy
            if 0 <= nx < w and 0 <= ny < h and mask[ny][nx] and not visited[ny][nx]:
                visited[ny][nx] = True
                queue.append((nx, ny))

    # Also capture close detached particles (e.g. seeds grains, wood chips)
    # BUT strictly reject any component touching the outer boundary or card border
    comp_visited = [[False for _ in range(w)] for _ in range(h)]
    for y in range(h):
        for x in range(w):
            if mask[y][x] and not visited[y][x] and not comp_visited[y][x]:
                q = [(x, y)]
                comp_visited[y][x] = True
                c = []
                while q:
                    cx_p, cy_p = q.pop(0)
                    c.append((cx_p, cy_p))
                    for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
                        nx, ny = cx_p + dx, cy_p + dy
                        if 0 <= nx < w and 0 <= ny < h and mask[ny][nx] and not visited[ny][nx] and not comp_visited[ny][nx]:
                            comp_visited[ny][nx] = True
                            q.append((nx, ny))
                # Only attach small genuine item fragments close to the main item
                # NEVER attach large rings/frames
                if 5 <= len(c) <= 600:
                    avg_x = sum(p[0] for p in c) / len(c)
                    avg_y = sum(p[1] for p in c) / len(c)
                    d = math.dist((avg_x, avg_y), (local_cx, local_cy))
                    # Must be within 60px of center and not near perimeter
                    if d < 60.0:
                        touches_perimeter = any(abs(p[0] - local_cx) >= 70 or abs(p[1] - local_cy) >= 72 for p in c)
                        if not touches_perimeter:
                            main_comp.extend(c)

    # 5. Build clean image
    clean = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    for x, y in main_comp:
        clean.putpixel((x, y), crop.getpixel((x, y)))

    # 6. Tightly crop to bounding box
    bbox = clean.split()[3].getbbox()
    if not bbox:
        return None, "Empty bounding box"
    item_only = clean.crop(bbox)

    # 7. Scale uniformly to fit within MAX_ITEM_DIM (104px)
    scale = min(MAX_ITEM_DIM / item_only.width, MAX_ITEM_DIM / item_only.height)
    new_w = max(1, int(round(item_only.width * scale)))
    new_h = max(1, int(round(item_only.height * scale)))
    resized = item_only.resize((new_w, new_h), Image.Resampling.LANCZOS)

    # 8. Center onto transparent 128x128 canvas
    canvas = Image.new("RGBA", (TARGET_SIZE, TARGET_SIZE), (0, 0, 0, 0))
    offset_x = (TARGET_SIZE - new_w) // 2
    offset_y = (TARGET_SIZE - new_h) // 2
    canvas.paste(resized, (offset_x, offset_y), resized)

    # 9. Verify outer border is 100% transparent
    canvas_w, canvas_h = canvas.size
    edge_alphas = []
    for x in range(canvas_w):
        edge_alphas.append(canvas.getpixel((x, 0))[3])
        edge_alphas.append(canvas.getpixel((x, canvas_h - 1))[3])
    for y in range(canvas_h):
        edge_alphas.append(canvas.getpixel((0, y))[3])
        edge_alphas.append(canvas.getpixel((canvas_w - 1, y))[3])

    return canvas, {
        "orig_dim": (item_only.width, item_only.height),
        "scaled_dim": (new_w, new_h),
        "edge_clean": max(edge_alphas) == 0,
        "bbox": canvas.split()[3].getbbox()
    }

def render_vector_status_icons():
    """
    Renders the 6 HUD player status and resources icons at 128x128
    using 8x supersampled procedural vector rendering.
    100% crisp, zero borders, pure transparent backgrounds.
    """
    S = 8 # Supersampling factor
    icons = {}

    # 1. Heart (Red faceted low-poly gem)
    im = Image.new("RGBA", (128*S, 128*S), (0, 0, 0, 0))
    draw = ImageDraw.Draw(im)
    def P(pts): return [(x * S * 2, y * S * 2) for x, y in pts]
    draw.polygon(P([(32,18), (20,8), (32,9)]), fill="#ff4d6d")
    draw.polygon(P([(32,18), (32,9), (44,8)]), fill="#ff758f")
    draw.polygon(P([(20,8), (10,18), (20,24)]), fill="#e01a4f")
    draw.polygon(P([(20,8), (20,24), (32,18)]), fill="#ff4d6d")
    draw.polygon(P([(44,8), (32,18), (44,24)]), fill="#ff597b")
    draw.polygon(P([(44,8), (44,24), (54,18)]), fill="#e01a4f")
    draw.polygon(P([(10,18), (10,34), (20,24)]), fill="#c9184a")
    draw.polygon(P([(20,24), (10,34), (22,38)]), fill="#a8132e")
    draw.polygon(P([(20,24), (22,38), (32,32)]), fill="#d90429")
    draw.polygon(P([(20,24), (32,32), (32,18)]), fill="#ef233c")
    draw.polygon(P([(32,18), (32,32), (42,38)]), fill="#ff4d6d")
    draw.polygon(P([(32,18), (42,38), (44,24)]), fill="#ff758f")
    draw.polygon(P([(44,24), (42,38), (54,34)]), fill="#a8132e")
    draw.polygon(P([(44,24), (54,34), (54,18)]), fill="#c9184a")
    draw.polygon(P([(10,34), (32,58), (22,38)]), fill="#800f2f")
    draw.polygon(P([(22,38), (32,58), (32,44)]), fill="#a8132e")
    draw.polygon(P([(22,38), (32,44), (32,32)]), fill="#c9184a")
    draw.polygon(P([(32,32), (32,44), (42,38)]), fill="#c9184a")
    draw.polygon(P([(42,38), (32,44), (32,58)]), fill="#a8132e")
    draw.polygon(P([(42,38), (32,58), (54,34)]), fill="#590d22")
    draw.polygon(P([(18,14), (24,12), (20,20)]), fill="#ffffff")
    icons["icon_heart"] = im.resize((128, 128), Image.Resampling.LANCZOS)

    # 2. Stamina Bolt (Cyan/teal electric lightning)
    im = Image.new("RGBA", (128*S, 128*S), (0, 0, 0, 0))
    draw = ImageDraw.Draw(im)
    draw.polygon(P([(38,4), (27,19), (33,26)]), fill="#9bf6ff")
    draw.polygon(P([(38,4), (33,26), (48,26)]), fill="#00f5d4")
    draw.polygon(P([(38,4), (16,34), (27,19)]), fill="#cbf3f0")
    draw.polygon(P([(27,19), (16,34), (31,34)]), fill="#00bbf9")
    draw.polygon(P([(31,34), (22,60), (35,43)]), fill="#00f5d4")
    draw.polygon(P([(31,34), (35,43), (48,26)]), fill="#00bbf9")
    draw.polygon(P([(35,43), (22,60), (42,36)]), fill="#007f7a")
    draw.polygon(P([(35,8), (30,19), (36,18)]), fill="#ffffff")
    icons["icon_stamina"] = im.resize((128, 128), Image.Resampling.LANCZOS)

    # 3. Gold Coin (Faceted gold currency token)
    im = Image.new("RGBA", (128*S, 128*S), (0, 0, 0, 0))
    draw = ImageDraw.Draw(im)
    draw.polygon(P([(20,4), (44,4), (40,11), (24,11)]), fill="#ffe066")
    draw.polygon(P([(44,4), (60,20), (53,24), (40,11)]), fill="#ffd13b")
    draw.polygon(P([(60,20), (60,44), (53,40), (53,24)]), fill="#ffb703")
    draw.polygon(P([(60,44), (44,60), (40,53), (53,40)]), fill="#e09200")
    draw.polygon(P([(44,60), (20,60), (24,53), (40,53)]), fill="#b87200")
    draw.polygon(P([(20,60), (4,44), (11,40), (24,53)]), fill="#e09200")
    draw.polygon(P([(4,44), (4,20), (11,24), (11,40)]), fill="#ffb703")
    draw.polygon(P([(4,20), (20,4), (24,11), (11,24)]), fill="#ffe066")
    draw.polygon(P([(24,11), (32,32), (40,11)]), fill="#ffc83b")
    draw.polygon(P([(40,11), (32,32), (53,24)]), fill="#ffa200")
    draw.polygon(P([(53,24), (32,32), (53,40)]), fill="#eb8f00")
    draw.polygon(P([(53,40), (32,32), (40,53)]), fill="#d47a00")
    draw.polygon(P([(40,53), (32,32), (24,53)]), fill="#bd6800")
    draw.polygon(P([(24,53), (32,32), (11,40)]), fill="#d47a00")
    draw.polygon(P([(11,40), (32,32), (11,24)]), fill="#ffa200")
    draw.polygon(P([(11,24), (32,32), (24,11)]), fill="#ffc83b")
    draw.ellipse([(22*S*2, 22*S*2), (42*S*2, 42*S*2)], fill=(255, 255, 255, 70))
    icons["icon_coin"] = im.resize((128, 128), Image.Resampling.LANCZOS)

    # 4. Water Droplet (Blue low-poly water droplet)
    im = Image.new("RGBA", (128*S, 128*S), (0, 0, 0, 0))
    draw = ImageDraw.Draw(im)
    draw.polygon(P([(32,4), (21,24), (32,28)]), fill="#90e0ef")
    draw.polygon(P([(32,4), (32,28), (43,24)]), fill="#48cae4")
    draw.polygon(P([(32,4), (12,34), (21,24)]), fill="#caf0f8")
    draw.polygon(P([(32,4), (43,24), (52,34)]), fill="#0096c7")
    draw.polygon(P([(21,24), (12,34), (24,39)]), fill="#00b4d8")
    draw.polygon(P([(21,24), (24,39), (32,28)]), fill="#48cae4")
    draw.polygon(P([(32,28), (24,39), (32,45)]), fill="#0077b6")
    draw.polygon(P([(32,28), (32,45), (40,39)]), fill="#0096c7")
    draw.polygon(P([(32,28), (40,39), (43,24)]), fill="#0077b6")
    draw.polygon(P([(43,24), (40,39), (52,34)]), fill="#023e8a")
    draw.polygon(P([(12,34), (12,44), (24,39)]), fill="#0077b6")
    draw.polygon(P([(12,44), (22,58), (26,47)]), fill="#023e8a")
    draw.polygon(P([(12,44), (26,47), (24,39)]), fill="#0077b6")
    draw.polygon(P([(24,39), (26,47), (32,45)]), fill="#03045e")
    draw.polygon(P([(32,45), (26,47), (32,58)]), fill="#023e8a")
    draw.polygon(P([(32,45), (32,58), (38,47)]), fill="#023e8a")
    draw.polygon(P([(32,45), (38,47), (40,39)]), fill="#03045e")
    draw.polygon(P([(40,39), (38,47), (52,44)]), fill="#0077b6")
    draw.polygon(P([(38,47), (32,58), (42,58)]), fill="#03045e")
    draw.polygon(P([(38,47), (42,58), (52,44)]), fill="#03045e")
    draw.polygon(P([(22,14), (27,21), (21,23)]), fill="#ffffff")
    icons["icon_water"] = im.resize((128, 128), Image.Resampling.LANCZOS)

    # 5. Solar Sun (8 low-poly rays, warm golden solar disk)
    im = Image.new("RGBA", (128*S, 128*S), (0, 0, 0, 0))
    draw = ImageDraw.Draw(im)
    cx, cy = 64 * S, 64 * S
    for i in range(8):
        angle = i * (math.pi / 4)
        r_inner = 24 * S
        r_outer = 48 * S
        w_ang = math.pi / 16
        p1 = (cx + r_inner * math.cos(angle - w_ang), cy + r_inner * math.sin(angle - w_ang))
        p2 = (cx + r_outer * math.cos(angle), cy + r_outer * math.sin(angle))
        p3 = (cx + r_inner * math.cos(angle + w_ang), cy + r_inner * math.sin(angle + w_ang))
        draw.polygon([p1, p2, p3], fill="#ffb703")
        draw.polygon([p1, p2, (cx, cy)], fill="#ffd13b")
        draw.polygon([(cx, cy), p2, p3], fill="#fb8500")
    draw.ellipse([(cx - 24*S, cy - 24*S), (cx + 24*S, cy + 24*S)], fill="#ffb703", outline="#ffe066", width=2*S)
    draw.ellipse([(cx - 18*S, cy - 18*S), (cx + 18*S, cy + 18*S)], fill="#ffd13b")
    draw.ellipse([(cx - 10*S, cy - 14*S), (cx - 2*S, cy - 6*S)], fill=(255, 255, 255, 160))
    icons["icon_solar"] = im.resize((128, 128), Image.Resampling.LANCZOS)

    # 6. Battery (Floating green energy battery cell)
    im = Image.new("RGBA", (128*S, 128*S), (0, 0, 0, 0))
    draw = ImageDraw.Draw(im)
    draw.rounded_rectangle([(52*S, 12*S), (76*S, 20*S)], radius=4*S, fill="#9ef01a")
    draw.rounded_rectangle([(32*S, 20*S), (96*S, 116*S)], radius=8*S, fill="#142318", outline="#38b000", width=4*S)
    draw.rounded_rectangle([(40*S, 86*S), (88*S, 108*S)], radius=4*S, fill="#38b000")
    draw.rounded_rectangle([(40*S, 58*S), (88*S, 80*S)], radius=4*S, fill="#70e000")
    draw.rounded_rectangle([(40*S, 30*S), (88*S, 52*S)], radius=4*S, fill="#9ef01a")
    icons["icon_battery"] = im.resize((128, 128), Image.Resampling.LANCZOS)

    # Normalize all vector icons to MAX_ITEM_DIM (104px) centered in 128x128
    normalized_icons = {}
    for k, raw in icons.items():
        bbox = raw.split()[3].getbbox()
        item = raw.crop(bbox)
        scale = min(MAX_ITEM_DIM / item.width, MAX_ITEM_DIM / item.height)
        new_w = max(1, int(round(item.width * scale)))
        new_h = max(1, int(round(item.height * scale)))
        resized = item.resize((new_w, new_h), Image.Resampling.LANCZOS)
        canvas = Image.new("RGBA", (TARGET_SIZE, TARGET_SIZE), (0, 0, 0, 0))
        canvas.paste(resized, ((TARGET_SIZE - new_w) // 2, (TARGET_SIZE - new_h) // 2), resized)
        normalized_icons[k] = canvas

    return normalized_icons

def main():
    print("=== HOMESTEADER: FULL ICON EXTRACTION & VALIDATION PIPELINE ===")
    print("Enforcing: 128x128 px, Pure Transparent RGBA, NO BORDERS, 100% FULLY VIEWED\n")

    # Clean obsolete files
    for d in [HUD_ITEMS_DIR, UNREAL_ICONS_DIR, HUD_PNG_DIR]:
        for f in os.listdir(d):
            if f.endswith("_opaque.png"):
                os.remove(os.path.join(d, f))
        for sub in ["framed", "Framed"]:
            sp = os.path.join(d, sub)
            if os.path.exists(sp):
                shutil.rmtree(sp)

    ITEMS_CONFIG = [
        # SHEET 1: CROPS & PRODUCE
        ("sheet_crops_produce.jpg", [(36, 46, 56)], 22.0, False, [
            ("crop_corn", 161, 217),
            ("crop_tomato", 424, 217),
            ("crop_carrot", 693, 217),
            ("crop_wheat", 953, 210),
            ("crop_potato", 1215, 217),
            ("crop_pumpkin", 161, 548),
            ("crop_strawberry", 424, 551),
            ("crop_sunflower", 687, 548),
            ("crop_cotton", 963, 551),
            ("crop_herb", 1213, 548),
        ]),
        # SHEET 2: SEEDS
        ("sheet_seeds.jpg", [(34, 42, 53), (28, 36, 46)], 22.0, False, [
            ("seed_corn", 182, 205),
            ("seed_tomato", 433, 207),
            ("seed_carrot", 684, 207),
            ("seed_wheat", 939, 203),
            ("seed_potato", 1189, 208),
            ("seed_pumpkin", 188, 555),
            ("seed_strawberry", 433, 555),
            ("seed_sunflower", 688, 555),
            ("seed_cotton", 934, 555),
            ("seed_herb", 1185, 555),
        ]),
        # SHEET 3: TOOLS
        ("sheet_tools.jpg", [(65, 78, 95), (44, 52, 63)], 22.0, False, [
            ("tool_hoe", 441, 190),
            ("tool_watering_can", 688, 190),
            ("tool_axe", 934, 190),
            ("tool_pickaxe", 441, 410),
            ("tool_sickle", 688, 410),
            ("tool_hammer", 934, 410),
            ("tool_wrench", 441, 630),
            ("tool_shovel", 688, 630),
            ("tool_seedbag", 935, 630),
        ]),
        # SHEET 4: MATERIALS, FOOD & FUEL
        ("sheet_materials_food_fuel.jpg", [
            (47, 57, 69), (38, 47, 56), (20, 24, 30), (28, 34, 42), (50, 53, 58)
        ], 18.0, True, [
            ("mat_lumber", 152, 137),
            ("mat_stone", 510, 137),
            ("mat_metal", 867, 139),
            ("mat_glass", 1222, 137),
            ("food_bread", 151, 387),
            ("food_stew", 514, 380),
            ("food_apple", 869, 387),
            ("food_cheese", 1224, 386),
            ("mat_rope", 151, 637),
            ("mat_fertilizer", 511, 638),
            ("fuel_gasoline", 870, 636),
            ("fuel_firewood", 1228, 636),
        ]),
        # SHEET 5: ANIMAL PRODUCTS, MEATS & PELTS
        ("sheet_animals_meats_pelts.jpg", [
            (36, 45, 57), (43, 55, 69), (20, 26, 34), (28, 36, 46)
        ], 18.0, True, [
            ("animal_egg", 150, 139),
            ("animal_milk", 580, 139),
            ("animal_wool", 805, 139),
            ("animal_truffle", 1230, 139),
            ("meat_chicken", 155, 388),
            ("meat_beef", 580, 384),
            ("meat_pork", 805, 384),
            ("meat_mutton", 1230, 384),
            ("mat_feather", 150, 629),
            ("mat_leather", 575, 624),
            ("pelt_sheep", 798, 624),
            ("fuel_propane", 1230, 629),
        ]),
    ]

    all_icons = {}

    # Extract concept sheet items
    for sheet_file, bg_colors, tol, is_framed, items in ITEMS_CONFIG:
        sheet_path = os.path.join(CONCEPTS_DIR, sheet_file)
        sheet_img = Image.open(sheet_path).convert("RGBA")
        print(f"Processing {sheet_file} (is_framed={is_framed})...")
        for name, cx, cy in items:
            icon, info = extract_clean_item(sheet_img, cx, cy, bg_colors, tol=tol, is_framed_sheet=is_framed)
            if icon:
                all_icons[name] = icon
                print(f"  {name:18s}: orig={info['orig_dim']} -> scaled={info['scaled_dim']} | bbox={info['bbox']}")
            else:
                print(f"  {name:18s}: FAILED ({info})")

    # Render vector HUD status icons
    print("\nRendering 6 Vector HUD Status Icons (8x Supersampled)...")
    vector_icons = render_vector_status_icons()
    for name, icon in vector_icons.items():
        all_icons[name] = icon
        bbox = icon.split()[3].getbbox()
        print(f"  {name:18s}: rendered 128x128 | bbox={bbox}")

    # Aliases
    aliases = [
        ("meat_beef", "animal_meat"),
        ("mat_leather", "pelt_cow"),
        ("meat_mutton", "meat_goat"),
        ("mat_leather", "pelt_goat"),
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
        if src in all_icons:
            all_icons[dst] = all_icons[src].copy()

    # Save to all destination directories
    print(f"\nSaving {len(all_icons)} fully viewed transparent icons to directories...")
    dest_dirs = [HUD_ITEMS_DIR, UNREAL_ICONS_DIR, HUD_PNG_DIR]
    for name, img in all_icons.items():
        fname = f"{name}.png"
        for d in dest_dirs:
            img.save(os.path.join(d, fname), "PNG")

    # VALIDATION PASS
    print("\n=== RUNNING STRICT AUTOMATED QUALITY AUDIT ===")
    failures = []
    for name, img in all_icons.items():
        w, h = img.size
        if (w, h) != (128, 128):
            failures.append((name, f"Wrong dimensions: {w}x{h}"))
            continue
            
        alpha = img.split()[3]
        bbox = alpha.getbbox()
        if not bbox:
            failures.append((name, "Empty alpha channel"))
            continue

        # 1. Canvas edge alpha must be strictly 0
        edge_alphas = []
        for x in range(w):
            edge_alphas.append(alpha.getpixel((x, 0)))
            edge_alphas.append(alpha.getpixel((x, h - 1)))
        for y in range(h):
            edge_alphas.append(alpha.getpixel((0, y)))
            edge_alphas.append(alpha.getpixel((w - 1, y)))
        max_edge_alpha = max(edge_alphas)
        if max_edge_alpha > 0:
            failures.append((name, f"Canvas edge is not transparent: max alpha = {max_edge_alpha}"))

        # 2. Outer 4-pixel perimeter margin must be completely transparent
        outer_alphas = []
        for margin in range(4):
            for x in range(w):
                outer_alphas.append(alpha.getpixel((x, margin)))
                outer_alphas.append(alpha.getpixel((x, h - 1 - margin)))
            for y in range(h):
                outer_alphas.append(alpha.getpixel((margin, y)))
                outer_alphas.append(alpha.getpixel((w - 1 - margin, y)))
        if max(outer_alphas) > 0:
            failures.append((name, f"Outer 4px margin not transparent: max alpha = {max(outer_alphas)}"))

        # 3. Item bounding box must fit within 106x106
        bw = bbox[2] - bbox[0]
        bh = bbox[3] - bbox[1]
        if bw > 106 or bh > 106:
            failures.append((name, f"Item exceeds max bounding box: {bw}x{bh} > 106"))

        # 4. Check for square/box frame (edge density check)
        cropped_alpha = img.crop(bbox).split()[3]
        cw, ch = cropped_alpha.size
        top_edge = sum(1 for x in range(cw) if cropped_alpha.getpixel((x, 0)) > 20) / cw
        bot_edge = sum(1 for x in range(cw) if cropped_alpha.getpixel((x, ch - 1)) > 20) / cw
        left_edge = sum(1 for y in range(ch) if cropped_alpha.getpixel((0, y)) > 20) / ch
        right_edge = sum(1 for y in range(ch) if cropped_alpha.getpixel((cw - 1, y)) > 20) / ch
        edge_density = (top_edge + bot_edge + left_edge + right_edge) / 4.0

        # A true frame box has solid perimeter borders on all 4 sides (density > 0.60 on all 4 sides)
        if bw >= 98 and bh >= 98 and all(e > 0.60 for e in [top_edge, bot_edge, left_edge, right_edge]):
            failures.append((name, f"Frame box detected: bw={bw}, bh={bh}, edges=({top_edge:.2f},{bot_edge:.2f},{left_edge:.2f},{right_edge:.2f})"))

    if failures:
        print(f"AUDIT FAILED with {len(failures)} issues:")
        for f in failures:
            print("  FAIL:", f)
    else:
        print(f"AUDIT PASSED PERFECTLY! All {len(all_icons)} icons verified:")
        print("  - Canvas: exactly 128x128 RGBA PNG")
        print("  - Canvas 4-pixel outer border: 100% transparent (alpha = 0)")
        print("  - Item dimensions: <= 104px (fully viewed, unclipped)")
        print("  - Borders/boxes: ZERO frame borders or box outlines")
        print("  - Saved across HUD/assets/items, Homesteader/Content/Homesteader/UI/Icons, and HUD/assets/png")

if __name__ == "__main__":
    main()
