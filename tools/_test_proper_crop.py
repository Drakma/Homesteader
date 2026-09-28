import cv2
import numpy as np

img = cv2.imread("tools/c0_full.png")
icon_zone = img[0:390, :]

# The background is white (all 3 channels > 240)
# Pixels that are NOT background have at least one channel <= 230:
mask = np.any(icon_zone <= 230, axis=2)

coords = cv2.findNonZero(mask.astype(np.uint8))
bx, by, bw, bh = cv2.boundingRect(coords)
print(f"Proper Icon Bounding Box: x={bx}, y={by}, w={bw}, h={bh}")

cv2.imwrite("tools/test_proper_icon0.png", icon_zone[by:by+bh, bx:bx+bw])
print("Saved test_proper_icon0.png")
