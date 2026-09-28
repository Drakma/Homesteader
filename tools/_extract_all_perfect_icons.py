import os
import cv2
import numpy as np
from PIL import Image

OUT_DIR = r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Resources\HUDTree\PhoneIcons"
os.makedirs(OUT_DIR, exist_ok=True)

img1 = cv2.imread(r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Resources\apps1.jpg")
img2 = cv2.imread(r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Resources\apps2.jpg")

# 12 apps in apps1.jpg:
# Center coordinates of the 4 columns and 3 rows:
# Looking at the grid, each icon is ~352x352 px.
# Let's find the centers for all 12 in apps1 and all 3 in apps2.

# apps1 columns:
# Col 0: cx = 460
# Col 1: cx = 1164
# Col 2: cx = 1868
# Col 3: cx = 2572
# Row 0: cy = 287
# Row 1: cy = 790
# Row 2: cy = 1290

apps1_layout = [
    # Row 0
    [
        ("app_board_meeting", 460, 287),
        ("app_nail_it", 1164, 287),
        ("app_lettuce_shop", 1868, 287),
        ("app_hay_there", 2572, 287),
    ],
    # Row 1
    [
        ("app_cache_flow", 460, 790),
        ("app_bazaar_behavior", 1164, 790),
        ("app_shift_happens", 1868, 790),
        ("app_tank_you", 2572, 790),
    ],
    # Row 2
    [
        ("app_drafting_behind_you", 460, 1237),
        ("app_tractor_beam", 1109, 1237),
        ("app_wheel_deal", 1755, 1237),
        ("app_sofa_so_good", 2404, 1237),
    ]
]

# apps2 has 3 icons:
# Image width 2816.
# Col 0: cx ~ 580, cy ~ 660
# Col 1: cx ~ 1408, cy ~ 660
# Col 2: cx ~ 2236, cy ~ 660
apps2_layout = [
    ("app_grid_os", 580, 660),
    ("app_resview_levels", 1408, 660),
    ("app_good_almanac", 2236, 660)
]

def crop_and_clean_icon(img, cx, cy, out_id, box_half=176):
    x0 = max(0, cx - box_half)
    x1 = min(img.shape[1], cx + box_half)
    y0 = max(0, cy - box_half)
    y1 = min(img.shape[0], cy + box_half)
    
    crop = img[y0:y1, x0:x1]
    h, w, _ = crop.shape
    
    # Outer background is white [255, 255, 255]
    # Floodfill outside of the rounded badge:
    flood_mask = np.zeros((h + 2, w + 2), dtype=np.uint8)
    diff = (12, 12, 12)
    c_img = crop.copy()
    corners = [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]
    filled = np.zeros((h, w), dtype=np.uint8)
    for sx, sy in corners:
        if np.mean(crop[sy, sx]) > 225:
            c_mask = np.zeros((h + 2, w + 2), dtype=np.uint8)
            cv2.floodFill(c_img, c_mask, (sx, sy), (0, 255, 0), diff, diff, cv2.FLOODFILL_MASK_ONLY | (255 << 8))
            filled = np.maximum(filled, c_mask[1:-1, 1:-1])
            
    # Alpha mask: badge is where filled == 0
    badge_mask = (filled == 0).astype(np.uint8)
    dist = cv2.distanceTransform(badge_mask, cv2.DIST_L2, 5)
    alpha = np.clip(dist * 1.5, 0.0, 1.0) * 255.0
    
    rgb = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
    rgba = np.dstack([rgb, alpha.astype(np.uint8)])
    pil_img = Image.fromarray(rgba, mode="RGBA")
    
    # Standardize to 128x128
    pil_resized = pil_img.resize((116, 116), Image.Resampling.LANCZOS)
    final_icon = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
    final_icon.paste(pil_resized, (6, 6), pil_resized)
    
    out_path = os.path.join(OUT_DIR, f"{out_id}.png")
    final_icon.save(out_path, "PNG")
    print(f"Saved: {out_id}.png")

for r in range(3):
    for c in range(4):
        out_id, cx, cy = apps1_layout[r][c]
        crop_and_clean_icon(img1, cx, cy, out_id)

for out_id, cx, cy in apps2_layout:
    # apps2 icons are slightly larger (~400x400)
    crop_and_clean_icon(img2, cx, cy, out_id, box_half=200)

print("\nAll 15 app icons extracted and standardized!")
