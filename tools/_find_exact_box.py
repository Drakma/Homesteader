import cv2
import numpy as np

img1 = cv2.imread(r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Resources\apps1.jpg")
h1, w1, _ = img1.shape
col_w = w1 // 4 # 704

# In icon_r0_c0, we took cx = 352, cy = 210 with box_half = 175.
# We saw the top-left corner of the icon at around (110, 60).
# That means the icon's center is further down and right:
# Let's find the bounding box of the non-white icon in the cell [0:550, 0:704]
cell0 = img1[0:550, 0:704]
gray = cv2.cvtColor(cell0, cv2.COLOR_BGR2GRAY)
# The background is pure white (~255)
mask = gray < 245
coords = cv2.findNonZero(mask.astype(np.uint8))
x, y, w, h = cv2.boundingRect(coords)
print(f"Cell 0 icon bounding box: x={x}, y={y}, w={w}, h={h}")

# Let's save the exact cropped icon to verify
cv2.imwrite("tools/test_exact_icon0.png", cell0[y:y+h, x:x+w])
