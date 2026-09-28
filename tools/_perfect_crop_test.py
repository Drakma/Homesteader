import cv2
import numpy as np
from PIL import Image

# Load cell_0_0_raw.png
img = cv2.imread("tools/cell_0_0_raw.png")
h, w, _ = img.shape
print(f"Size: {w}x{h}")

# The background is pure white [255, 255, 255]
# Let's inspect background color at the top corners:
print("Corner (0,0):", img[0, 0])
print("Corner (w-1,0):", img[0, w-1])

# The icon is in the upper part, text "BOARD MEETING" is at the bottom (y > 440)
# Icon region: y in [0, 440]
icon_region = img[0:440, :]

# Floodfill from (0,0) with white tolerance to isolate the background outside the rounded rectangle
# Background is [255, 255, 255]
# Icon has light yellow at top [198, 240, 254], so RGB difference is ~55.
# If tolerance is 15, floodfill will stop exactly at the rounded rectangle edge!
h_i, w_i, _ = icon_region.shape
flood_mask = np.zeros((h_i + 2, w_i + 2), dtype=np.uint8)
diff = (10, 10, 10)
c_img = icon_region.copy()

# Seed points in outer white space
seeds = [(0, 0), (w_i - 1, 0), (0, h_i - 1), (w_i - 1, h_i - 1)]
filled = np.zeros((h_i, w_i), dtype=np.uint8)
for sx, sy in seeds:
    c_mask = np.zeros((h_i + 2, w_i + 2), dtype=np.uint8)
    cv2.floodFill(c_img, c_mask, (sx, sy), (0, 255, 0), diff, diff, cv2.FLOODFILL_MASK_ONLY | (255 << 8))
    filled = np.maximum(filled, c_mask[1:-1, 1:-1])

# Invert mask: icon is where filled == 0
icon_mask = (filled == 0).astype(np.uint8)
coords = cv2.findNonZero(icon_mask)
bx, by, bw, bh = cv2.boundingRect(coords)
print(f"Icon bounding box: x={bx}, y={by}, w={bw}, h={bh}")

# Crop to bounding box
badge = icon_region[by:by+bh, bx:bx+bw]
badge_mask = icon_mask[by:by+bh, bx:bx+bw]

# Soft distance transform for anti-aliasing
dist = cv2.distanceTransform(badge_mask, cv2.DIST_L2, 5)
alpha = np.clip(dist * 1.5, 0.0, 1.0) * 255.0

rgb = cv2.cvtColor(badge, cv2.COLOR_BGR2RGB)
rgba = np.dstack([rgb, alpha.astype(np.uint8)])
pil_badge = Image.fromarray(rgba, mode="RGBA")

# Resize to 128x128
pil_resized = pil_badge.resize((116, 116), Image.Resampling.LANCZOS)
final_icon = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
final_icon.paste(pil_resized, (6, 6), pil_resized)

final_icon.save("tools/perfect_board_meeting.png", "PNG")
print("Saved perfect_board_meeting.png!")
