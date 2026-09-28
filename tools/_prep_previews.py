import cv2
import numpy as np

# In apps1 and apps2, let's understand the grid.
# apps1 is 2816 wide, 1536 tall.
# Let's inspect where the icons are centered.
# Let's write a script to crop around each app icon + text together cleanly to inspect all 8 per sheet.

img1 = cv2.imread(r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Resources\apps1.jpg")
h, w, _ = img1.shape
print(f"Sheet size: {w}x{h}")

# If there are 8 apps on apps1 and 8 apps on apps2:
# What are the 8 apps on apps1 and what are the apps on apps2?
# Let's save thumbnails of each app region including the text below it so we can read every name and replacement!
# Let's do a 2x4 grid, but with proper offsets.
col_w = w // 4
row_h = h // 2

for r in range(2):
    for c in range(4):
        x0 = c * col_w
        x1 = (c + 1) * col_w
        y0 = r * row_h
        y1 = (r + 1) * row_h
        # Save a smaller preview (e.g. 350x380) with text
        cell = img1[y0:y1, x0:x1]
        cv2.imwrite(f"tools/p_apps1_{r}_{c}.jpg", cv2.resize(cell, (350, 380)))

img2 = cv2.imread(r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Resources\apps2.jpg")
for r in range(2):
    for c in range(4):
        x0 = c * col_w
        x1 = (c + 1) * col_w
        y0 = r * row_h
        y1 = (r + 1) * row_h
        cell = img2[y0:y1, x0:x1]
        cv2.imwrite(f"tools/p_apps2_{r}_{c}.jpg", cv2.resize(cell, (350, 380)))

print("Saved preview thumbnails for inspection.")
