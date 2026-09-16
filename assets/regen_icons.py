#!/usr/bin/env python3
"""
Homesteader Icon Regeneration Engine
Strictly adheres to the Homesteader Item Icon Creation Ruleset & Style Guide:
  1. No borders, card boxes, frames, or halos
  2. Full view without geometry clipping
  3. Strictly 128x128 px 32-bit RGBA PNG
  4. Item bounding box fits inside MAX_DIM = 104 px (>= 12px clean margin on all 4 sides)
  5. 100% outer perimeter alpha = 0 (x=0, x=127, y=0, y=127)
  6. Outside-In Perimeter Flood Fill & De-Spill for background extraction
"""

import os
import sys
import math
import shutil
import argparse
from PIL import Image

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HUD_DIR = os.path.join(os.path.dirname(BASE_DIR), "HUD")
GAME_DIR = os.path.join(os.path.dirname(BASE_DIR), "Homesteader")

TARGET_SIZE = 128
PADDING = 12
MAX_ITEM_DIM = 104  # 128 - 12*2 = 104px

def find_best_source_image(category, item_id):
    """Locates the best source image across assets, HUD authentic extracts, and renders."""
    item_dir = os.path.join(BASE_DIR, category, item_id)
    canonical_png = os.path.join(item_dir, f"{item_id}.png")
    
    candidates = []
    
    # 1. Check local item folder for any PNG
    if os.path.exists(item_dir):
        for f in os.listdir(item_dir):
            if f.endswith(".png") and not f.startswith("T_") and not f.startswith("palette"):
                candidates.append(os.path.join(item_dir, f))
                
    # 2. Check HUD authentic extracted items
    hud_items_dir = os.path.join(HUD_DIR, "assets", "items")
    if os.path.exists(hud_items_dir):
        # Direct match
        direct = os.path.join(hud_items_dir, f"{item_id}.png")
        if os.path.exists(direct):
            candidates.insert(0, direct)
            
        # Strip prefixes to find source (e.g. animal_fish_bass -> fish_bass.png)
        prefixes = [
            "animal_fish_", "animal_", "fishing_", "seed_", "ingredient_fillet_",
            "ingredient_", "mat_bale_", "mat_pelt_", "mat_", "food_",
            "electricity_", "water_", "waste_", "net_", "tool_", "machinery_", "struct_"
        ]
        for p in prefixes:
            if item_id.startswith(p):
                short = item_id[len(p):]
                c1 = os.path.join(hud_items_dir, f"{short}.png")
                if os.path.exists(c1):
                    candidates.append(c1)
                break
                
    # 3. Check scratch renders
    render_dirs = [
        os.path.join(HUD_DIR, "scratch", "renders_animals"),
        os.path.join(HUD_DIR, "scratch", "renders_structures"),
        os.path.join(HUD_DIR, "scratch", "renders_clutter"),
        os.path.join(HUD_DIR, "scratch", "renders_trees"),
    ]
    for rdir in render_dirs:
        if os.path.exists(rdir):
            for rf in os.listdir(rdir):
                if rf.lower().endswith(".png"):
                    # Check if item name is in render file
                    clean_id = item_id.replace("_", "").lower()
                    clean_rf = rf.replace("_", "").lower()
                    if clean_id in clean_rf or any(part in clean_rf for part in item_id.split("_") if len(part) > 4):
                        candidates.append(os.path.join(rdir, rf))

    # Prefer canonical png if it exists and has good content
    if os.path.exists(canonical_png):
        candidates.insert(0, canonical_png)
        
    return candidates[0] if candidates else None

def standardize_icon_image(src_path, dst_path=None, max_dim=MAX_ITEM_DIM, target_size=TARGET_SIZE):
    """
    Applies the Homesteader Item Icon Ruleset:
    - Outside-In flood fill background isolation
    - Tight bounding box crop
    - Lanczos aspect-ratio preserved scaling to max_dim (<= 104px)
    - Perfectly centered on 128x128 canvas (>= 12px safe margin)
    - 100% outer perimeter alpha = 0
    """
    if not os.path.exists(src_path):
        return False, f"Source image does not exist: {src_path}"

    try:
        im = Image.open(src_path).convert("RGBA")
    except Exception as e:
        return False, f"Failed to load image: {e}"

    w, h = im.size

    # 1. Perimeter inspection: detect if background removal is necessary
    perim = []
    for x in range(w):
        perim.append(im.getpixel((x, 0)))
        perim.append(im.getpixel((x, h - 1)))
    for y in range(h):
        perim.append(im.getpixel((0, y)))
        perim.append(im.getpixel((w - 1, y)))

    avg_alpha = sum(p[3] for p in perim) / len(perim)

    # If canvas perimeter is not already transparent, apply outside-in flood fill
    if avg_alpha > 15:
        bg_r = sum(p[0] for p in perim) / len(perim)
        bg_g = sum(p[1] for p in perim) / len(perim)
        bg_b = sum(p[2] for p in perim) / len(perim)
        bg = (bg_r, bg_g, bg_b)
        tol_low = 22.0
        tol_high = 45.0

        def is_bg(p):
            if p[3] < 15:
                return True
            d = math.sqrt((p[0] - bg[0])**2 + (p[1] - bg[1])**2 + (p[2] - bg[2])**2)
            return d < tol_low

        visited = [[False] * w for _ in range(h)]
        queue = []
        for x in range(w):
            if is_bg(im.getpixel((x, 0))):
                visited[0][x] = True
                queue.append((x, 0))
            if is_bg(im.getpixel((x, h - 1))):
                visited[h - 1][x] = True
                queue.append((x, h - 1))
        for y in range(h):
            if not visited[y][0] and is_bg(im.getpixel((0, y))):
                visited[y][0] = True
                queue.append((0, y))
            if not visited[y][w - 1] and is_bg(im.getpixel((w - 1, y))):
                visited[y][w - 1] = True
                queue.append((w - 1, y))

        while queue:
            qx, qy = queue.pop(0)
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = qx + dx, qy + dy
                if 0 <= nx < w and 0 <= ny < h and not visited[ny][nx] and is_bg(im.getpixel((nx, ny))):
                    visited[ny][nx] = True
                    queue.append((nx, ny))

        rgba = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        for y in range(h):
            for x in range(w):
                if not visited[y][x]:
                    px = im.getpixel((x, y))
                    d = math.sqrt((px[0] - bg[0])**2 + (px[1] - bg[1])**2 + (px[2] - bg[2])**2)
                    if d < tol_low:
                        alpha = 0
                    elif d > tol_high:
                        alpha = px[3]
                    else:
                        ratio = (d - tol_low) / (tol_high - tol_low)
                        alpha = int(px[3] * ratio)
                    rgba.putpixel((x, y), (px[0], px[1], px[2], alpha))
        im = rgba

    # 2. Extract bounding box
    alpha_chan = im.split()[3]
    bbox = alpha_chan.getbbox()
    if not bbox:
        return False, "Item became completely transparent or empty."

    item_only = im.crop(bbox)
    iw, ih = item_only.size

    # 3. Uniform aspect-ratio scaling to max_dim (104px)
    scale = min(float(max_dim) / iw, float(max_dim) / ih)
    nw = max(1, int(round(iw * scale)))
    nh = max(1, int(round(ih * scale)))
    resized = item_only.resize((nw, nh), Image.Resampling.LANCZOS)

    # 4. Center onto pure transparent 128x128 RGBA canvas
    canvas = Image.new("RGBA", (target_size, target_size), (0, 0, 0, 0))
    offset_x = (target_size - nw) // 2
    offset_y = (target_size - nh) // 2
    canvas.paste(resized, (offset_x, offset_y), resized)

    # 5. Guarantee 100% clean outer perimeter
    for x in range(target_size):
        canvas.putpixel((x, 0), (0, 0, 0, 0))
        canvas.putpixel((x, target_size - 1), (0, 0, 0, 0))
    for y in range(target_size):
        canvas.putpixel((0, y), (0, 0, 0, 0))
        canvas.putpixel((target_size - 1, y), (0, 0, 0, 0))

    dest = dst_path or src_path
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    canvas.save(dest, "PNG")

    return True, f"Standardized {nw}x{nh} inside {target_size}x{target_size} canvas."

def regen_icon(category, item_id):
    """Regenerates a single item icon in the assets library and mirrors to game/HUD if available."""
    item_dir = os.path.join(BASE_DIR, category, item_id)
    if not os.path.isdir(item_dir):
        return False, (
            f"Asset folder not found: {category}/{item_id}. "
            f"Regeneration never creates a new item folder (the item may have been "
            f"moved/renamed to a different category since this was last loaded — refresh and retry)."
        )

    src = find_best_source_image(category, item_id)
    if not src:
        return False, f"No suitable source icon found for {category}/{item_id}"

    dst = os.path.join(BASE_DIR, category, item_id, f"{item_id}.png")
    ok, msg = standardize_icon_image(src, dst)
    if not ok:
        return False, msg

    # Mirror to HUD assets and UE5 icons if directories exist
    try:
        hud_dst = os.path.join(HUD_DIR, "assets", "items", f"{item_id}.png")
        if os.path.exists(os.path.dirname(hud_dst)):
            shutil.copy2(dst, hud_dst)
            
        ue5_dst = os.path.join(GAME_DIR, "Content", "Homesteader", "UI", "Icons", f"{item_id}.png")
        if os.path.exists(os.path.dirname(ue5_dst)):
            shutil.copy2(dst, ue5_dst)
    except Exception:
        pass

    return True, f"Successfully regenerated {category}/{item_id}.png"

def regen_batch(items):
    """Regenerates icons for an explicit list of items: [{'category': '...', 'id': '...'}]"""
    results = []
    for it in items:
        cat = it.get("category")
        iid = it.get("id", it.get("item_id"))
        if not cat or not iid:
            results.append({"category": cat, "item_id": iid, "success": False, "error": "Missing category or id"})
            continue
        ok, msg = regen_icon(cat, iid)
        results.append({"category": cat, "item_id": iid, "success": ok, "message": msg})
    return results

def regen_all(target_category=None):
    """Regenerates icons across all categories or a specific category."""
    items_to_process = []
    cats = [target_category] if target_category else [
        d for d in os.listdir(BASE_DIR) if os.path.isdir(os.path.join(BASE_DIR, d)) and not d.startswith(".")
    ]

    for cat in cats:
        cat_dir = os.path.join(BASE_DIR, cat)
        if not os.path.isdir(cat_dir):
            continue
        for item in os.listdir(cat_dir):
            item_dir = os.path.join(cat_dir, item)
            if os.path.isdir(item_dir):
                items_to_process.append({"category": cat, "id": item})

    return regen_batch(items_to_process)

def main():
    parser = argparse.ArgumentParser(description="Homesteader Icon Regeneration Tool")
    parser.add_argument("--all", action="store_true", help="Regenerate all icons in the project")
    parser.add_argument("--category", type=str, help="Target specific category")
    parser.add_argument("--item", type=str, help="Target specific item ID")
    args = parser.parse_args()

    if args.category and args.item:
        ok, msg = regen_icon(args.category, args.item)
        print(f"[{'PASS' if ok else 'FAIL'}] {args.category}/{args.item}: {msg}")
    elif args.all or args.category:
        results = regen_all(args.category)
        successes = sum(1 for r in results if r["success"])
        print(f"Regenerated {successes}/{len(results)} icons successfully.")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()

