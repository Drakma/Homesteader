import os
import cv2
import numpy as np
from PIL import Image

# Output directory for phone app icons
OUT_DIR = r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Resources\HUDTree\PhoneIcons"
os.makedirs(OUT_DIR, exist_ok=True)

# Load full images
img1 = cv2.imread(r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Resources\apps1.jpg")
img2 = cv2.imread(r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Resources\apps2.jpg")

# Definitions of apps with their bounding box crops in apps1.jpg and apps2.jpg
# apps1: 2816 wide, 1536 tall
# 3 rows, 4 columns
# Let's verify the exact coordinates for the 12 icons in apps1:
# Col 0: x in [250, 680]
# Col 1: x in [950, 1380]
# Col 2: x in [1650, 2080]
# Col 3: x in [2350, 2780]
# Row 0: y in [80, 470]
# Row 1: y in [580, 970]
# Row 2: y in [1080, 1470]

# apps2: 2816 wide, 1536 tall
# 1 row, 3 columns:
# Col 0: x in [240, 850], y in [350, 960]
# Col 1: x in [1100, 1710], y in [350, 960]
# Col 2: x in [1950, 2560], y in [350, 960]

def extract_and_standardize_icon(img, search_box, out_name):
    x0, y0, x1, y1 = search_box
    cell = img[y0:y1, x0:x1]
    
    # Threshold out the pure white background (~250..255)
    gray = cv2.cvtColor(cell, cv2.COLOR_BGR2GRAY)
    mask = gray < 240
    coords = cv2.findNonZero(mask.astype(np.uint8))
    if coords is None:
        print(f"Error finding coords for {out_name}")
        return
        
    bx, by, bw, bh = cv2.boundingRect(coords)
    
    # We want ONLY the rounded square icon badge, NOT the text below it!
    # The icon badge is roughly square (w approx equals h of the badge).
    # Since bw is the width of the badge, the badge height is approximately bw (or slightly more with rounded corners).
    # Any non-white pixels further down (beyond by + bw + small pad) are the text lines!
    badge_h = min(bh, int(bw * 1.02))
    
    # Crop the badge
    badge = cell[by : by + badge_h, bx : bx + bw]
    
    # Now let's create a clean alpha mask for the rounded rectangle badge
    # The badge has rounded corners and anti-aliasing against the white background.
    # Floodfill from four corners to identify outer white background
    h_b, w_b, _ = badge.shape
    flood_mask = np.zeros((h_b + 2, w_b + 2), dtype=np.uint8)
    diff = (12, 12, 12)
    corners = [(0, 0), (w_b - 1, 0), (0, h_b - 1), (w_b - 1, h_b - 1),
               (w_b // 2, 0), (0, h_b // 2), (w_b - 1, h_b // 2), (w_b // 2, h_b - 1)]
    
    filled = np.zeros((h_b, w_b), dtype=np.uint8)
    for cx, cy in corners:
        # Check if corner is near white
        if np.mean(badge[cy, cx]) > 220:
            c_img = badge.copy()
            c_mask = np.zeros((h_b + 2, w_b + 2), dtype=np.uint8)
            cv2.floodFill(c_img, c_mask, (cx, cy), (0, 255, 0), diff, diff, cv2.FLOODFILL_MASK_ONLY | (255 << 8))
            filled = np.maximum(filled, c_mask[1:-1, 1:-1])
            
    # Compute smooth distance transform for soft anti-aliased edge
    dist = cv2.distanceTransform((filled == 0).astype(np.uint8), cv2.DIST_L2, 5)
    alpha = np.clip(dist * 1.5, 0.0, 1.0) * 255.0
    
    # Convert BGR to RGB
    rgb = cv2.cvtColor(badge, cv2.COLOR_BGR2RGB)
    
    # Combine to RGBA
    rgba = np.dstack([rgb, alpha.astype(np.uint8)])
    pil_img = Image.fromarray(rgba, mode="RGBA")
    
    # Tight crop by alpha
    bbox = pil_img.getbbox()
    if bbox:
        pil_img = pil_img.crop(bbox)
        
    # Resize to standard 128x128 with max 104px content (or 116px for phone app tile)
    max_dim = 112
    ratio = min(max_dim / float(pil_img.width), max_dim / float(pil_img.height))
    new_w = int(round(pil_img.width * ratio))
    new_h = int(round(pil_img.height * ratio))
    pil_resized = pil_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    
    final_icon = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
    paste_x = (128 - new_w) // 2
    paste_y = (128 - new_h) // 2
    final_icon.paste(pil_resized, (paste_x, paste_y), pil_resized)
    
    out_path = os.path.join(OUT_DIR, f"{out_name}.png")
    final_icon.save(out_path, "PNG")
    print(f"Saved icon: {out_name}.png ({new_w}x{new_h})")

# Coordinates in apps1.jpg:
col_w = img1.shape[1] // 4 # 704
row_h_approx = [
    (60, 480),
    (560, 980),
    (1060, 1480)
]

apps1_names = [
    ["app_board_meeting", "app_nail_it", "app_lettuce_shop", "app_hay_there"],
    ["app_cache_flow", "app_bazaar_behavior", "app_shift_happens", "app_tank_you"],
    ["app_drafting_behind_you", "app_tractor_beam", "app_wheel_deal", "app_sofa_so_good"]
]

for r_idx in range(3):
    y0, y1 = row_h_approx[r_idx]
    for c_idx in range(4):
        x0 = c_idx * col_w
        x1 = (c_idx + 1) * col_w
        out_name = apps1_names[r_idx][c_idx]
        extract_and_standardize_icon(img1, (x0, y0, x1, y1), out_name)

# Coordinates in apps2.jpg:
apps2_col_w = img2.shape[1] // 3 # ~938
apps2_names = ["app_grid_os", "app_resview_levels", "app_good_almanac"]

for c_idx in range(3):
    x0 = c_idx * apps2_col_w
    x1 = (c_idx + 1) * apps2_col_w
    out_name = apps2_names[c_idx]
    extract_and_standardize_icon(img2, (x0, 300, x1, 1050), out_name)

print("All 15 app icons extracted successfully!")
