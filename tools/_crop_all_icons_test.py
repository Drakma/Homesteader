import cv2
import numpy as np

img1 = cv2.imread(r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Resources\apps1.jpg")
h1, w1, _ = img1.shape
col_w = w1 // 4 # 704

# Row ranges in apps1:
# Row 0: icon y is roughly [40, 370], text is below [380, 480]
# Row 1: icon y is roughly [550, 880], text is below [890, 990]
# Row 2: icon y is roughly [1060, 1390], text is below [1400, 1500]

# Let's save a crop of each icon (just the icon box!) to verify exact boundaries
rows = [
    (40, 380),
    (550, 890),
    (1060, 1400)
]

for r_idx, (y0, y1) in enumerate(rows):
    for c_idx in range(4):
        x0 = c_idx * col_w
        x1 = (c_idx + 1) * col_w
        # Center horizontally in the column
        cx = (x0 + x1) // 2
        cy = (y0 + y1) // 2
        box_half = 175 # 350x350
        icon_crop = img1[cy - box_half : cy + box_half, cx - box_half : cx + box_half]
        cv2.imwrite(f"tools/icon_r{r_idx}_c{c_idx}.png", icon_crop)

print("Saved apps1 icon crops")

# apps2: 1 row of 3 icons
img2 = cv2.imread(r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Resources\apps2.jpg")
h2, w2, _ = img2.shape
# 3 icons horizontally:
# Col 0: cx ~ 550, cy ~ 480
# Col 1: cx ~ 1408, cy ~ 480
# Col 2: cx ~ 2266, cy ~ 480
apps2_centers = [(550, 480), (1408, 480), (2266, 480)]
for idx, (cx, cy) in enumerate(apps2_centers):
    box_half = 200
    icon_crop = img2[cy - box_half : cy + box_half, cx - box_half : cx + box_half]
    cv2.imwrite(f"tools/icon_apps2_{idx}.png", icon_crop)

print("Saved apps2 icon crops")
