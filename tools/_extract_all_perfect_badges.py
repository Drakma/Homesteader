import os
import cv2
import numpy as np
from PIL import Image

OUT_DIR = r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Resources\HUDTree\PhoneIcons"
os.makedirs(OUT_DIR, exist_ok=True)

img1 = cv2.imread(r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Resources\apps1.jpg")
img2 = cv2.imread(r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Resources\apps2.jpg")

apps1_grid = [
    # Row 0
    [
        ("app_board_meeting", "Board Meeting"),
        ("app_nail_it", "Nail It"),
        ("app_lettuce_shop", "Lettuce Shop"),
        ("app_hay_there", "Hay There"),
    ],
    # Row 1
    [
        ("app_cache_flow", "Cache Flow"),
        ("app_bazaar_behavior", "Bazaar Behavior"),
        ("app_shift_happens", "Shift Happens"),
        ("app_tank_you", "Tank You"),
    ],
    # Row 2
    [
        ("app_drafting_behind_you", "Drafting Behind You"),
        ("app_tractor_beam", "Tractor Beam"),
        ("app_wheel_deal", "Wheel Deal"),
        ("app_sofa_so_good", "Sofa So Good"),
    ]
]

apps2_grid = [
    ("app_grid_os", "Volt"),
    ("app_resview_levels", "ResView"),
    ("app_good_almanac", "Almanac")
]

def crop_and_standardize_badge(cell_img, out_id):
    h_c, w_c, _ = cell_img.shape
    # Floodfill from outer corners where pixel is near white
    diff = (10, 10, 10)
    c_img = cell_img.copy()
    seeds = [(0, 0), (w_c - 1, 0), (0, h_c - 1), (w_c - 1, h_c - 1),
             (w_c // 2, 0), (0, h_c // 2), (w_c - 1, h_c // 2), (w_c // 2, h_c - 1)]
    
    filled = np.zeros((h_c, w_c), dtype=np.uint8)
    for sx, sy in seeds:
        if np.mean(cell_img[sy, sx]) > 220:
            c_mask = np.zeros((h_c + 2, w_c + 2), dtype=np.uint8)
            cv2.floodFill(c_img, c_mask, (sx, sy), (0, 255, 0), diff, diff, cv2.FLOODFILL_MASK_ONLY | (255 << 8))
            filled = np.maximum(filled, c_mask[1:-1, 1:-1])
            
    icon_mask = (filled == 0).astype(np.uint8)
    coords = cv2.findNonZero(icon_mask)
    if coords is None:
        print(f"Error finding coords for {out_id}")
        return
    bx, by, bw, bh = cv2.boundingRect(coords)
    
    badge = cell_img[by:by+bh, bx:bx+bw]
    badge_mask = icon_mask[by:by+bh, bx:bx+bw]
    
    dist = cv2.distanceTransform(badge_mask, cv2.DIST_L2, 5)
    alpha = np.clip(dist * 1.5, 0.0, 1.0) * 255.0
    
    rgb = cv2.cvtColor(badge, cv2.COLOR_BGR2RGB)
    rgba = np.dstack([rgb, alpha.astype(np.uint8)])
    pil_badge = Image.fromarray(rgba, mode="RGBA")
    
    # Resize to 128x128 with max 116px badge
    pil_resized = pil_badge.resize((116, 116), Image.Resampling.LANCZOS)
    final_icon = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
    final_icon.paste(pil_resized, (6, 6), pil_resized)
    
    out_path = os.path.join(OUT_DIR, f"{out_id}.png")
    final_icon.save(out_path, "PNG")
    print(f"Extracted and saved: {out_id}.png")

# Process apps1:
col_w = img1.shape[1] // 4 # 704
row_ranges = [
    (0, 440),
    (530, 970),
    (1030, 1470)
]

for r in range(3):
    y0, y1 = row_ranges[r]
    for c in range(4):
        x0 = c * col_w
        x1 = (c + 1) * col_w
        cell = img1[y0:y1, x0:x1]
        out_id = apps1_grid[r][c][0]
        crop_and_standardize_badge(cell, out_id)

# Process apps2:
col_w2 = img2.shape[1] // 3 # ~938
for c in range(3):
    x0 = c * col_w2
    x1 = (c + 1) * col_w2
    cell = img2[280:920, x0:x1]
    out_id = apps2_grid[c][0]
    crop_and_standardize_badge(cell, out_id)

print("\nAll 15 official app icons processed and saved to PhoneIcons!")
