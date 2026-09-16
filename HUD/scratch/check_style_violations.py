import os, sys, glob
from PIL import Image
from collections import defaultdict

HUD_ITEMS = r"C:\Users\casey\Desktop\Homesteader\HUD\assets\items"
UE5_ICONS = r"C:\Users\casey\Desktop\Homesteader\Homesteader\Content\Homesteader\UI\Icons"

def analyze_image(path):
    im = Image.open(path)
    w, h = im.size
    mode = im.mode
    issues = []
    
    if (w, h) != (128, 128):
        issues.append(f"size_{w}x{h}")
    if mode != "RGBA":
        issues.append(f"mode_{mode}")
        return issues
        
    px = im.load()
    
    # 1. Check perimeter alpha
    bad_perim = 0
    for x in range(w):
        if px[x, 0][3] > 0 or px[x, h-1][3] > 0:
            bad_perim += 1
    for y in range(h):
        if px[0, y][3] > 0 or px[w-1, y][3] > 0:
            bad_perim += 1
    if bad_perim > 0:
        issues.append(f"bad_perimeter_{bad_perim}px")
        
    # 2. Check bounding box margin
    bbox = im.getbbox()
    if not bbox:
        issues.append("empty_transparent")
    else:
        bx0, by0, bx1, by1 = bbox
        bw, bh = bx1 - bx0, by1 - by0
        margin = min(bx0, by0, w - bx1, h - by1)
        if margin < 12:
            issues.append(f"margin_{margin}px")
        if bw > 104 or bh > 104:
            issues.append(f"oversize_{bw}x{bh}")
            
    # 3. Check for solid/near-solid square borders/frames
    # Check if border rectangle exists around margin
    border_pixels = 0
    for x in range(10, w-10):
        if px[x, 10][3] > 180 and px[x, h-11][3] > 180:
            border_pixels += 1
    if border_pixels > 80:
        issues.append("possible_frame_border")
        
    # 4. Check color variance / flat vector
    # Low number of unique colors often means flat 2D graphic or primitive vector
    colors = len(set(im.getdata()))
    if colors < 40:
        issues.append(f"flat_2d_low_colors_{colors}")
        
    return issues

print("=== Analyzing UE5 UI/Icons (recursive) ===")
ue5_results = {}
for root, dirs, files in os.walk(UE5_ICONS):
    for f in files:
        if f.endswith(".png"):
            p = os.path.join(root, f)
            rel = os.path.relpath(p, UE5_ICONS)
            iss = analyze_image(p)
            if iss:
                ue5_results[rel] = iss

print(f"Files with issues in UE5 UI/Icons: {len(ue5_results)}")
for f, iss in ue5_results.items():
    print(f"  {f:<45}: {', '.join(iss)}")

print("\n=== Analyzing HUD/assets (recursive) ===")
hud_assets_dir = r"C:\Users\casey\Desktop\Homesteader\HUD\assets"
hud_all_results = {}
for root, dirs, files in os.walk(hud_assets_dir):
    for f in files:
        if f.endswith(".png"):
            p = os.path.join(root, f)
            rel = os.path.relpath(p, hud_assets_dir)
            iss = analyze_image(p)
            if iss:
                hud_all_results[rel] = iss

print(f"Files with issues in HUD/assets: {len(hud_all_results)}")
for f, iss in hud_all_results.items():
    print(f"  {f:<45}: {', '.join(iss)}")

