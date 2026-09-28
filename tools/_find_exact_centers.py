import cv2
import numpy as np

# Load apps1.jpg
img1 = cv2.imread(r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Resources\apps1.jpg")

# In apps1 (2816 x 1536):
# What are the EXACT horizontal centers of the 4 columns?
# Let's inspect where the dark blue badge of NAIL IT is:
row0 = img1[0:500, :]
# Find blue badge (high blue, lower red):
blue_mask = (row0[:, :, 0] > 100) & (row0[:, :, 2] < 100)
coords = cv2.findNonZero(blue_mask.astype(np.uint8))
x, y, w, h = cv2.boundingRect(coords)
print(f"NAIL IT badge box: x={x}, y={y}, w={w}, h={h}")
cx_col1 = x + w // 2
cy_row0 = y + h // 2
print(f"Col 1 center: ({cx_col1}, {cy_row0}), width={w}, height={h}")

# The spacing between columns:
# Let's check GROCER (LETTUCE SHOP) green badge:
green_mask = (row0[:, :, 1] > 100) & (row0[:, :, 0] < 80) & (row0[:, :, 2] < 80)
coords_g = cv2.findNonZero(green_mask.astype(np.uint8))
xg, yg, wg, hg = cv2.boundingRect(coords_g)
cx_col2 = xg + wg // 2
print(f"Col 2 center: ({cx_col2}, {yg + hg//2}), width={wg}, height={hg}")

dx = cx_col2 - cx_col1
print(f"Column pitch dx = {dx}")
cx_col0 = cx_col1 - dx
cx_col3 = cx_col2 + dx
print(f"Calculated centers: col0={cx_col0}, col1={cx_col1}, col2={cx_col2}, col3={cx_col3}")

# Let's test crop around (cx_col0, cy_row0) with size 350x350:
box_half = 175
test_bm = img1[cy_row0 - box_half : cy_row0 + box_half, cx_col0 - box_half : cx_col0 + box_half]
cv2.imwrite("tools/test_bm_exact.png", test_bm)
print("Saved test_bm_exact.png")
