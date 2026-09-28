import cv2
import numpy as np

# Load apps1 and apps2
img1 = cv2.imread(r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Resources\apps1.jpg")
col_w = img1.shape[1] // 4

# In app_card_1_0_0, the bottom text "(LUMBER YARD)" was cut off because y1 was 520.
# Let's see the full vertical height of each cell:
# Row 0: y from 60 to 570
# Row 1: y from 560 to 1070
# Row 2: y from 1060 to 1536

row_bounds = [
    (60, 560),
    (560, 1060),
    (1060, 1536)
]

for r_idx, (y0, y1) in enumerate(row_bounds):
    for c_idx in range(4):
        x0 = c_idx * col_w
        x1 = (c_idx + 1) * col_w
        app_crop = img1[y0:y1, x0:x1]
        cv2.imwrite(f"tools/card1_{r_idx}_{c_idx}.jpg", cv2.resize(app_crop, (352, 250)))

img2 = cv2.imread(r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Resources\apps2.jpg")
col_w2 = img2.shape[1] // 3
for c_idx in range(3):
    x0 = c_idx * col_w2
    x1 = (c_idx + 1) * col_w2
    app_crop = img2[300:1250, x0:x1]
    cv2.imwrite(f"tools/card2_{c_idx}.jpg", cv2.resize(app_crop, (352, 350)))

print("Saved all 15 cards with full text!")
