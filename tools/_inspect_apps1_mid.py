import cv2
import numpy as np

# Load apps1.jpg
img1 = cv2.imread(r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Resources\apps1.jpg")
h, w, _ = img1.shape
print(f"apps1: {w}x{h}")

# In apps1, there are actually 3 visual rows of apps!
# Let's save vertical slices around the middle rows to see row 1 full (the ones with "CACHE FLOW", "BAZAAR BEHAVIOR", "SHIFT HAPPENS", "TANK YOU")
# Let's see the y-coordinates:
# Row 0: y in [0, 520]
# Row 1: y in [480, 1020]
# Row 2: y in [980, 1536]

col_w = w // 4

for c in range(4):
    x0 = c * col_w
    x1 = (c + 1) * col_w
    mid_cell = img1[450:1050, x0:x1]
    cv2.imwrite(f"tools/apps1_mid_c{c}.jpg", cv2.resize(mid_cell, (350, 300)))

print("Saved apps1 mid row!")
