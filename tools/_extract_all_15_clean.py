import os
import cv2
import numpy as np
from PIL import Image

OUT_DIR = r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Resources\HUDTree\PhoneIcons"
os.makedirs(OUT_DIR, exist_ok=True)

img1 = cv2.imread(r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Resources\apps1.jpg")
img2 = cv2.imread(r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Resources\apps2.jpg")

# 12 apps in apps1.jpg:
apps1_names = [
    # Row 0
    [
        "app_board_meeting",      # Board Meeting (Lumber Yard)
        "app_nail_it",            # Nail It (Home Depot)
        "app_lettuce_shop",       # Lettuce Shop (Grocer)
        "app_hay_there",          # Hay There (Feed Store)
    ],
    # Row 1
    [
        "app_cache_flow",         # Cache Flow (Bank)
        "app_bazaar_behavior",    # Bazaar Behavior (Exchange)
        "app_shift_happens",      # Shift Happens (Auto / Vehicle Store)
        "app_tank_you",           # Tank You (Water Well)
    ],
    # Row 2
    [
        "app_drafting_behind_you",# Drafting Behind You (Livestock)
        "app_tractor_beam",       # Tractor Beam (Heavy Equipment)
        "app_wheel_deal",         # Wheel Deal (Dealership)
        "app_sofa_so_good",       # Sofa So Good (Furniture Store)
    ]
]

apps1_cols = [
    (285, 636),
    (933, 1284),
    (1580, 1931),
    (2229, 2580)
]

apps1_rows = [
    (94, 446),
    (595, 947),
    (1096, 1448)
]

# apps2: 3 apps
apps2_names = [
    "app_grid_os",          # Volt
    "app_resview_levels",   # ResView
    "app_good_almanac"      # Almanac
]

apps2_cols = [
    (311, 892),
    (1129, 1705),
    (1955, 2535)
]
apps2_row = (372, 950)

def extract_clean_icon(img, x_range, y_range, out_name):
    x0, x1 = x_range
    y0, y1 = y_range
    crop = img[y0:y1, x0:x1]
    h, w, _ = crop.shape
    
    # Floodfill outside of the rounded badge to create clean alpha
    flood_mask = np.zeros((h + 2, w + 2), dtype=np.uint8)
    diff = (12, 12, 12)
    c_img = crop.copy()
    corners = [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]
    filled = np.zeros((h, w), dtype=np.uint8)
    for sx, sy in corners:
        if np.mean(crop[sy, sx]) > 220:
            c_mask = np.zeros((h + 2, w + 2), dtype=np.uint8)
            cv2.floodFill(c_img, c_mask, (sx, sy), (0, 255, 0), diff, diff, cv2.FLOODFILL_MASK_ONLY | (255 << 8))
            filled = np.maximum(filled, c_mask[1:-1, 1:-1])
            
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
    
    out_path = os.path.join(OUT_DIR, f"{out_name}.png")
    final_icon.save(out_path, "PNG")
    print(f"Generated: {out_name}.png (128x128)")

# Process all 12 from apps1
for r in range(3):
    y_range = apps1_rows[r]
    for c in range(4):
        x_range = apps1_cols[c]
        out_name = apps1_names[r][c]
        extract_clean_icon(img1, x_range, y_range, out_name)

# Process all 3 from apps2
for c in range(3):
    x_range = apps2_cols[c]
    out_name = apps2_names[c]
    extract_clean_icon(img2, x_range, apps2_row, out_name)

print("\nALL 15 ICONS EXTRACTED PERFECTLY!")
