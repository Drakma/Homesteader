import os
import cv2
import numpy as np
from PIL import Image

OUT_DIR = r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Resources\HUDTree\PhoneIcons"
os.makedirs(OUT_DIR, exist_ok=True)

img1 = cv2.imread(r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Resources\apps1.jpg")
img2 = cv2.imread(r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Resources\apps2.jpg")

# 12 apps in apps1.jpg (3 rows x 4 cols):
apps1_info = [
    # Row 0
    [
        ("app_board_meeting", "Board Meeting", "Lumber Yard"),
        ("app_nail_it", "Nail It", "Home Depot"),
        ("app_lettuce_shop", "Lettuce Shop", "Grocer"),
        ("app_hay_there", "Hay There", "Feed Store"),
    ],
    # Row 1
    [
        ("app_cache_flow", "Cache Flow", "Bank"),
        ("app_bazaar_behavior", "Bazaar Behavior", "Exchange"),
        ("app_shift_happens", "Shift Happens", "Auto / Vehicle Store"),
        ("app_tank_you", "Tank You", "Water Well / Water Storage"),
    ],
    # Row 2
    [
        ("app_drafting_behind_you", "Drafting Behind You", "Livestock / Animals"),
        ("app_tractor_beam", "Tractor Beam", "Heavy Equipment"),
        ("app_wheel_deal", "Wheel Deal", "Dealership / Vehicles"),
        ("app_sofa_so_good", "Sofa So Good", "Furniture Store"),
    ]
]

# 3 apps in apps2.jpg (1 row x 3 cols):
apps2_info = [
    ("app_grid_os", "Volt", "Grid OS (Solar/Power)"),
    ("app_resview_levels", "ResView", "ResView (Utilities)"),
    ("app_good_almanac", "Almanac", "Almanac (Forecasts)")
]

def clean_and_save_badge(cell_img, out_id):
    # Find bounding box of pixels that deviate from white background:
    # A pixel belongs to the icon if at least one channel is <= 235
    mask = np.any(cell_img <= 235, axis=2)
    coords = cv2.findNonZero(mask.astype(np.uint8))
    if coords is None:
        print(f"Error: no coords for {out_id}")
        return
    bx, by, bw, bh = cv2.boundingRect(coords)
    
    # Crop badge
    badge = cell_img[by : by + bh, bx : bx + bw]
    h_b, w_b, _ = badge.shape
    
    # Create smooth anti-aliased transparency for the rounded rectangle corners
    # Floodfill from four corners on pixels with all channels > 230
    diff = (12, 12, 12)
    corners = [(0, 0), (w_b - 1, 0), (0, h_b - 1), (w_b - 1, h_b - 1)]
    filled = np.zeros((h_b, w_b), dtype=np.uint8)
    for cx, cy in corners:
        if np.all(badge[cy, cx] > 225):
            c_img = badge.copy()
            c_mask = np.zeros((h_b + 2, w_b + 2), dtype=np.uint8)
            cv2.floodFill(c_img, c_mask, (cx, cy), (0, 255, 0), diff, diff, cv2.FLOODFILL_MASK_ONLY | (255 << 8))
            filled = np.maximum(filled, c_mask[1:-1, 1:-1])
            
    dist = cv2.distanceTransform((filled == 0).astype(np.uint8), cv2.DIST_L2, 5)
    alpha = np.clip(dist * 1.5, 0.0, 1.0) * 255.0
    
    rgb = cv2.cvtColor(badge, cv2.COLOR_BGR2RGB)
    rgba = np.dstack([rgb, alpha.astype(np.uint8)])
    pil_img = Image.fromarray(rgba, mode="RGBA")
    
    # Standardize to 128x128
    max_dim = 114
    ratio = min(max_dim / float(pil_img.width), max_dim / float(pil_img.height))
    new_w = int(round(pil_img.width * ratio))
    new_h = int(round(pil_img.height * ratio))
    pil_resized = pil_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    
    final_icon = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
    paste_x = (128 - new_w) // 2
    paste_y = (128 - new_h) // 2
    final_icon.paste(pil_resized, (paste_x, paste_y), pil_resized)
    
    out_path = os.path.join(OUT_DIR, f"{out_id}.png")
    final_icon.save(out_path, "PNG")
    print(f"Extracted and saved: {out_id}.png")

# Process apps1 (3 rows, 4 cols)
col_w = img1.shape[1] // 4
row_ranges = [
    (0, 430),
    (530, 960),
    (1030, 1460)
]

for r in range(3):
    y0, y1 = row_ranges[r]
    for c in range(4):
        x0 = c * col_w
        x1 = (c + 1) * col_w
        cell = img1[y0:y1, x0:x1]
        out_id = apps1_info[r][c][0]
        clean_and_save_badge(cell, out_id)

# Process apps2 (1 row, 3 cols)
col_w2 = img2.shape[1] // 3
for c in range(3):
    x0 = c * col_w2
    x1 = (c + 1) * col_w2
    cell = img2[280:980, x0:x1]
    out_id = apps2_info[c][0]
    clean_and_save_badge(cell, out_id)

print("\nAll 15 icons extracted cleanly!")
