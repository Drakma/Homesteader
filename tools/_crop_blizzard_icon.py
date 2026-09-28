import cv2
import numpy as np
from PIL import Image

# Read the sheet image
sheet_path = r"Homesteader\Assets\Resources\weather_sheet.jpg"
img_bgr = cv2.imread(sheet_path)
h, w, _ = img_bgr.shape
print(f"Sheet dimensions: {w}x{h}")

# The image is 2 rows by 4 columns.
# Column 4 (bottom right) is "BLIZZARD"
# Row 0: Sunny (col 0), Partly Cloudy (col 1), Cloudy (col 2), Rain (col 3)
# Row 1: Thunderstorm (col 0), Snow (col 1), Wind (col 2), Blizzard (col 3)

col_w = w / 4.0
row_h = h / 2.0

# Blizzard is in col 3, row 1
# Let's crop the Blizzard cell
x0 = int(3 * col_w)
x1 = w
y0 = int(row_h)
y1 = h

cell = img_bgr[y0:y1, x0:x1]
ch, cw, _ = cell.shape
print(f"Cell dimensions: {cw}x{ch}")

# The icon itself is in the upper ~80% of the cell, text "BLIZZARD" is at the bottom ~20%
# Let's exclude the text at the bottom:
icon_crop = cell[0:int(ch * 0.82), :]

# Let's convert to RGBA with clean background transparency
# The background is clean pure white (or very near 255)
# Let's inspect the background colors
gray = cv2.cvtColor(icon_crop, cv2.COLOR_BGR2GRAY)

# Find bounding box of non-white content
# White is > 245
mask_nonwhite = gray < 246

# Find bounding box of the actual artwork
coords = cv2.findNonZero(mask_nonwhite.astype(np.uint8))
bx, by, bw, bh = cv2.boundingRect(coords)
print(f"Artwork bounding box within cell: x={bx}, y={by}, w={bw}, h={bh}")

# Crop to artwork with small padding
pad = 6
ax0 = max(0, bx - pad)
ay0 = max(0, by - pad)
ax1 = min(cw, bx + bw + pad)
ay1 = min(int(ch * 0.82), by + bh + pad)

art = icon_crop[ay0:ay1, ax0:ax1]
arth, artw, _ = art.shape
print(f"Art crop: {artw}x{arth}")

# Save debug crop to see
cv2.imwrite(r"Homesteader\Assets\Resources\debug_blizzard_crop.png", art)
print("Saved debug_blizzard_crop.png")
