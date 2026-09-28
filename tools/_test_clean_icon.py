import cv2
import numpy as np

img = cv2.imread("tools/c0_full.png")
# Icon is strictly between y=0 and y=390!
icon_zone = img[0:390, :]

# In icon_zone, find bounding box of non-white content
# What is the background color? Check corners:
corners = [icon_zone[0, 0], icon_zone[0, -1], icon_zone[-1, 0], icon_zone[-1, -1]]
bg = np.median(corners, axis=0)
print(f"Background BGR: {bg}")

diff = np.max(np.abs(icon_zone.astype(np.float32) - bg), axis=2)
mask = diff > 4
coords = cv2.findNonZero(mask.astype(np.uint8))
bx, by, bw, bh = cv2.boundingRect(coords)
print(f"Icon bounding box: x={bx}, y={by}, w={bw}, h={bh}")

cv2.imwrite("tools/test_clean_icon0.png", icon_zone[by:by+bh, bx:bx+bw])
print("Saved test_clean_icon0.png")
