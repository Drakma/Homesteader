import math
from PIL import Image

def extract_true_full_item(sheet_img, cx, cy, search_radius, bg_colors):
    r = search_radius
    crop = sheet_img.crop((cx - r, cy - r, cx + r, cy + r)).convert("RGBA")
    w, h = crop.size
    
    data = list(crop.getdata())
    is_fg = []
    for p in data:
        min_d = min(math.dist(p[:3], bg) for bg in bg_colors)
        is_fg.append(min_d > 22)
        
    mask = [[is_fg[y * w + x] for x in range(w)] for y in range(h)]
    
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
                
    center_x, center_y = w / 2.0, h / 2.0
    
    valid_comps = []
    for comp in components:
        touches_outer = any(p[0] <= 1 or p[0] >= w - 2 or p[1] <= 1 or p[1] >= h - 2 for p in comp)
        if not touches_outer:
            valid_comps.append(comp)
            
    if not valid_comps:
        return None
        
    def comp_score(c):
        size = len(c)
        avg_x = sum(p[0] for p in c) / size
        avg_y = sum(p[1] for p in c) / size
        d = math.dist((avg_x, avg_y), (center_x, center_y))
        return size / (1.0 + (d / 25.0)**2)
        
    valid_comps.sort(key=comp_score, reverse=True)
    item_pixels = set(valid_comps[0])
    
    for comp in valid_comps[1:]:
        size = len(comp)
        if size >= 15:
            avg_x = sum(p[0] for p in comp) / size
            avg_y = sum(p[1] for p in comp) / size
            d = math.dist((avg_x, avg_y), (center_x, center_y))
            if d < 65.0:
                item_pixels.update(comp)
                
    clean_crop = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    for x, y in item_pixels:
        r_c, g_c, b_c, _ = crop.getpixel((x, y))
        min_d = min(math.dist((r_c, g_c, b_c), bg) for bg in bg_colors)
        if min_d <= 22:
            alpha = int(255 * (min_d / 22.0))
        else:
            alpha = 255
        clean_crop.putpixel((x, y), (r_c, g_c, b_c, alpha))
        
    bbox = clean_crop.split()[3].getbbox()
    if not bbox:
        return None
    item_only = clean_crop.crop(bbox)
    
    TARGET_SIZE = 128
    PADDING = 12
    max_dim = TARGET_SIZE - 2 * PADDING
    scale = min(max_dim / item_only.width, max_dim / item_only.height)
    new_w = max(1, int(item_only.width * scale))
    new_h = max(1, int(item_only.height * scale))
    resized = item_only.resize((new_w, new_h), Image.Resampling.LANCZOS)
    
    canvas = Image.new("RGBA", (TARGET_SIZE, TARGET_SIZE), (0, 0, 0, 0))
    offset_x = (TARGET_SIZE - new_w) // 2
    offset_y = (TARGET_SIZE - new_h) // 2
    canvas.paste(resized, (offset_x, offset_y), resized)
    
    return canvas, item_only.size, (new_w, new_h)

# 1. Corn
crops_img = Image.open(r"c:\Users\casey\Desktop\Homesteader\HUD\concepts\sheet_crops_produce.jpg")
icon_corn, orig_size, new_size = extract_true_full_item(crops_img, 161, 217, 95, [(36, 46, 56)])
print(f"Corn: orig={orig_size} -> scaled={new_size}, final bbox={icon_corn.split()[3].getbbox()}")
icon_corn.save(r"c:\Users\casey\Desktop\Homesteader\HUD\test_corn_full.png")

# 2. Axe
tools_img = Image.open(r"c:\Users\casey\Desktop\Homesteader\HUD\concepts\sheet_tools.jpg")
icon_axe, orig_size, new_size = extract_true_full_item(tools_img, 934, 190, 85, [(65, 78, 95), (44, 52, 63)])
print(f"Axe: orig={orig_size} -> scaled={new_size}, final bbox={icon_axe.split()[3].getbbox()}")
icon_axe.save(r"c:\Users\casey\Desktop\Homesteader\HUD\test_axe_full.png")

# 3. Hoe
icon_hoe, orig_size, new_size = extract_true_full_item(tools_img, 441, 190, 85, [(65, 78, 95), (44, 52, 63)])
print(f"Hoe: orig={orig_size} -> scaled={new_size}, final bbox={icon_hoe.split()[3].getbbox()}")
icon_hoe.save(r"c:\Users\casey\Desktop\Homesteader\HUD\test_hoe_full.png")

# 4. Pickaxe
icon_pick, orig_size, new_size = extract_true_full_item(tools_img, 441, 410, 85, [(65, 78, 95), (44, 52, 63)])
print(f"Pickaxe: orig={orig_size} -> scaled={new_size}, final bbox={icon_pick.split()[3].getbbox()}")
icon_pick.save(r"c:\Users\casey\Desktop\Homesteader\HUD\test_pick_full.png")

# 5. Egg
amp_img = Image.open(r"c:\Users\casey\Desktop\Homesteader\HUD\concepts\sheet_animals_meats_pelts.jpg")
icon_egg, orig_size, new_size = extract_true_full_item(amp_img, 150, 139, 78, [(36, 45, 57)])
print(f"Egg: orig={orig_size} -> scaled={new_size}, final bbox={icon_egg.split()[3].getbbox()}")
icon_egg.save(r"c:\Users\casey\Desktop\Homesteader\HUD\test_egg_full.png")
