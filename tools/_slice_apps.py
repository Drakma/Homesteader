import cv2
import numpy as np

img1 = cv2.imread(r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Resources\apps1.jpg")
h, w, _ = img1.shape

# Let's crop into 8 cells (2 rows, 4 cols)
row_h = h // 2
col_w = w // 4

for r in range(2):
    for c in range(4):
        y0 = r * row_h
        y1 = (r + 1) * row_h
        x0 = c * col_w
        x1 = (c + 1) * col_w
        cell = img1[y0:y1, x0:x1]
        cv2.imwrite(f"tools/apps1_r{r}_c{c}.png", cell)

print("Saved cells for apps1")

img2 = cv2.imread(r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Resources\apps2.jpg")
for r in range(2):
    for c in range(4):
        y0 = r * row_h
        y1 = (r + 1) * row_h
        x0 = c * col_w
        x1 = (c + 1) * col_w
        cell = img2[y0:y1, x0:x1]
        cv2.imwrite(f"tools/apps2_r{r}_c{c}.png", cell)

print("Saved cells for apps2")
