import cv2
import numpy as np

# Let's inspect the subtext under BOARD MEETING:
# In test_exact_icon0.png, we saw:
# "BOARD MEETING"
# "(LUMBER YARD)"
# Let's write a script to crop both the title and parenthetical subtext for all 12 on apps1 and all 3 on apps2,
# and save each as a combined image so we can review them all!

img1 = cv2.imread(r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Resources\apps1.jpg")
col_w = img1.shape[1] // 4 # 704

# Let's crop each app (icon + text) cleanly:
# Row 0: y from 80 to 520
# Row 1: y from 590 to 1030
# Row 2: y from 1090 to 1530

row_bounds = [
    (80, 520),
    (590, 1030),
    (1090, 1530)
]

for r_idx, (y0, y1) in enumerate(row_bounds):
    for c_idx in range(4):
        x0 = c_idx * col_w
        x1 = (c_idx + 1) * col_w
        app_crop = img1[y0:y1, x0:x1]
        cv2.imwrite(f"tools/app_card_1_{r_idx}_{c_idx}.png", app_crop)

img2 = cv2.imread(r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Resources\apps2.jpg")
col_w2 = img2.shape[1] // 3
for c_idx in range(3):
    x0 = c_idx * col_w2
    x1 = (c_idx + 1) * col_w2
    app_crop = img2[360:1150, x0:x1]
    cv2.imwrite(f"tools/app_card_2_{c_idx}.png", app_crop)

print("Saved all 15 app cards with text!")
