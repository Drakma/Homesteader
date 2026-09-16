import os
import math
from PIL import Image

hud_root = r"c:\Users\casey\Desktop\Homesteader\HUD"
test_dir = os.path.join(hud_root, "scratch", "test_extracted")
os.makedirs(test_dir, exist_ok=True)

def extract_outside_in(sheet_img, cx, cy, r_x, r_y, tol=22.0):
    w, h = sheet_img.size
    x0, y0 = max(0, cx - r_x), max(0, cy - r_y)
    x1, y1 = min(w, cx + r_x), min(h, cy + r_y)
    
    crop = sheet_img.crop((x0, y0, x1, y1)).convert("RGB")
    cw, ch = crop.size
    
    # Background sampling around outer border
    border_px = []
    for x in range(cw):
        border_px.append(crop.getpixel((x, 0)))
        border_px.append(crop.getpixel((x, ch - 1)))
    for y in range(ch):
        border_px.append(crop.getpixel((0, y)))
        border_px.append(crop.getpixel((cw - 1, y)))
        
    bg_r = sum(p[0] for p in border_px) / len(border_px)
    bg_g = sum(p[1] for p in border_px) / len(border_px)
    bg_b = sum(p[2] for p in border_px) / len(border_px)
    bg = (bg_r, bg_g, bg_b)
    
    def is_bg(px):
        return math.sqrt((px[0]-bg[0])**2 + (px[1]-bg[1])**2 + (px[2]-bg[2])**2) < tol
        
    visited = [[False]*cw for _ in range(ch)]
    queue = []
    for x in range(cw):
        if is_bg(crop.getpixel((x, 0))):
            visited[0][x] = True
            queue.append((x, 0))
        if is_bg(crop.getpixel((x, ch - 1))):
            visited[ch - 1][x] = True
            queue.append((x, ch - 1))
    for y in range(ch):
        if not visited[y][0] and is_bg(crop.getpixel((0, y))):
            visited[y][0] = True
            queue.append((0, y))
        if not visited[y][cw - 1] and is_bg(crop.getpixel((cw - 1, y))):
            visited[y][cw - 1] = True
            queue.append((cw - 1, y))
            
    while queue:
        qx, qy = queue.pop(0)
        for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
            nx, ny = qx + dx, qy + dy
            if 0 <= nx < cw and 0 <= ny < ch and not visited[ny][nx]:
                if is_bg(crop.getpixel((nx, ny))):
                    visited[ny][nx] = True
                    queue.append((nx, ny))
                    
    # Foreground mask
    rgba = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    for y in range(ch):
        for x in range(cw):
            if not visited[y][x]:
                px = crop.getpixel((x, y))
                d = math.sqrt((px[0]-bg[0])**2 + (px[1]-bg[1])**2 + (px[2]-bg[2])**2)
                # Feathering
                if d < tol + 6:
                    alpha = min(255, max(0, int(255 * (d - tol + 6) / 6.0)))
                else:
                    alpha = 255
                rgba.putpixel((x, y), (px[0], px[1], px[2], alpha))
                
    bbox = rgba.split()[3].getbbox()
    if not bbox:
        return None
    item_only = rgba.crop(bbox)
    
    # Scale to max 104px (12px safe margin on 128 canvas)
    scale = min(104.0 / item_only.width, 104.0 / item_only.height)
    nw = max(1, int(round(item_only.width * scale)))
    nh = max(1, int(round(item_only.height * scale)))
    resized = item_only.resize((nw, nh), Image.Resampling.LANCZOS)
    
    canvas = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
    canvas.paste(resized, ((128 - nw) // 2, (128 - nh) // 2), resized)
    return canvas

# Test UI & Clutter sheet
ui_path = os.path.join(hud_root, "concepts", "concept_ui_clutter_sheet.jpg")
ui_img = Image.open(ui_path)

ui_items = [
    ("icon_coin", 170, 175, 120, 120),
    ("icon_heart", 512, 175, 120, 120),
    ("icon_stamina", 830, 175, 120, 120),
    ("icon_water", 170, 500, 120, 120),
    ("icon_battery", 500, 500, 120, 120),
    ("icon_solar", 830, 500, 120, 120),
    ("clutter_branch", 170, 830, 130, 120),
    ("clutter_dirt_clump", 500, 825, 130, 120),
    ("clutter_grass_tuft", 830, 825, 120, 120),
]

for name, cx, cy, rx, ry in ui_items:
    res = extract_outside_in(ui_img, cx, cy, rx, ry, tol=22.0)
    if res:
        res.save(os.path.join(test_dir, f"{name}.png"))
        print(f"Extracted UI: {name}")
    else:
        print(f"FAILED UI: {name}")

# Test Fish & Fillets sheet (exclude text labels below y)
fish_path = os.path.join(hud_root, "concepts", "concept_fish_fillets_sheet.jpg")
fish_img = Image.open(fish_path)

fish_items = [
    ("fish_catfish", 180, 115, 140, 75),
    ("fish_walleye", 512, 125, 140, 70),
    ("fish_crappie", 850, 120, 140, 75),
    ("fillet_bass", 170, 365, 130, 65),
    ("fillet_salmon", 500, 365, 120, 70),
    ("fillet_trout", 840, 365, 130, 65),
    ("fillet_catfish", 170, 610, 130, 65),
    ("fillet_walleye", 500, 610, 130, 65),
    ("fillet_crappie", 835, 610, 120, 65),
    ("meat_goat", 170, 855, 120, 70),
    ("pelt_goat", 500, 855, 120, 70),
    ("pelt_cow", 840, 855, 130, 70),
]

for name, cx, cy, rx, ry in fish_items:
    res = extract_outside_in(fish_img, cx, cy, rx, ry, tol=20.0)
    if res:
        res.save(os.path.join(test_dir, f"{name}.png"))
        print(f"Extracted Fish/Fillet: {name}")
    else:
        print(f"FAILED Fish/Fillet: {name}")

