import cv2
import numpy as np

# Load apps1 and apps2
img1 = cv2.imread(r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Resources\apps1.jpg")
img2 = cv2.imread(r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Resources\apps2.jpg")

# In apps1 (2816 x 1536):
# 4 columns, each 704 px wide.
# 3 rows of apps:
# Let's inspect the bounding box of non-white content in each of the 12 cells of apps1:
# Row 0: y in [0, 512]
# Row 1: y in [512, 1024]
# Row 2: y in [1024, 1536]

for r in range(3):
    y0 = r * 512
    y1 = (r + 1) * 512
    for c in range(4):
        x0 = c * 704
        x1 = (c + 1) * 704
        cell = img1[y0:y1, x0:x1]
        gray = cv2.cvtColor(cell, cv2.COLOR_BGR2GRAY)
        mask = gray < 240
        coords = cv2.findNonZero(mask.astype(np.uint8))
        if coords is not None:
            bx, by, bw, bh = cv2.boundingRect(coords)
            # Save the full cell with text to read
            cv2.imwrite(f"tools/cell_r{r}_c{c}.png", cell[by:by+bh, bx:bx+bw])
            print(f"apps1 r{r} c{c}: x={bx}, y={by}, w={bw}, h={bh}")

# In apps2 (2816 x 1536):
# 1 row of 3 apps across width:
col_w2 = 2816 // 3 # ~938
for c in range(3):
    x0 = c * col_w2
    x1 = (c + 1) * col_w2
    cell = img2[:, x0:x1]
    gray = cv2.cvtColor(cell, cv2.COLOR_BGR2GRAY)
    mask = gray < 240
    coords = cv2.findNonZero(mask.astype(np.uint8))
    if coords is not None:
        bx, by, bw, bh = cv2.boundingRect(coords)
        cv2.imwrite(f"tools/apps2_c{c}.png", cell[by:by+bh, bx:bx+bw])
        print(f"apps2 c{c}: x={bx}, y={by}, w={bw}, h={bh}")

print("Extracted all 15 cells!")
