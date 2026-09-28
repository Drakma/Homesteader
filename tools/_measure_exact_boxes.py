import os
import cv2
import numpy as np
from PIL import Image

OUT_DIR = r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Resources\HUDTree\PhoneIcons"
os.makedirs(OUT_DIR, exist_ok=True)

img1 = cv2.imread(r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Resources\apps1.jpg")
img2 = cv2.imread(r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Resources\apps2.jpg")

# In apps1 (2816 x 1536):
# 4 columns:
# Col 0: x in [285, 636]   (w = 351)
# Col 1: x in [933, 1284]  (w = 351)
# Col 2: x in [1580, 1931] (w = 351)
# Col 3: x in [2229, 2580] (w = 351)

# 3 rows:
# Let's find exact y0, y1 for Row 0, Row 1, Row 2:
# For each column, vertical scan:
def get_vertical_bounds(img, x_range, y_search_range):
    x0, x1 = x_range
    y_min, y_max = y_search_range
    sub = img[y_min:y_max, x0:x1]
    # Find rows with non-white pixels
    is_icon_row = np.any(sub < 235, axis=(1, 2))
    indices = np.where(is_icon_row)[0]
    if len(indices) == 0:
        return y_min, y_max
    return y_min + indices[0], y_min + indices[-1] + 1

# Let's inspect vertical bounds for the 3 rows:
r0_y = get_vertical_bounds(img1, (933, 1284), (50, 480))
r1_y = get_vertical_bounds(img1, (933, 1284), (550, 980))
r2_y = get_vertical_bounds(img1, (933, 1284), (1050, 1480))
print("apps1 row vertical bounds:")
print("Row 0:", r0_y, "height:", r0_y[1] - r0_y[0])
print("Row 1:", r1_y, "height:", r1_y[1] - r1_y[0])
print("Row 2:", r2_y, "height:", r2_y[1] - r2_y[0])

# apps2:
# Col 0: [311, 892]
# Col 1: [1129, 1705]
# Col 2: [1955, 2535]
c0_y2 = get_vertical_bounds(img2, (1129, 1705), (200, 1000))
print("apps2 vertical bounds:", c0_y2, "height:", c0_y2[1] - c0_y2[0])
