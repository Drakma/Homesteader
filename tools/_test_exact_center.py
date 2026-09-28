import cv2
import numpy as np

# Load apps1.jpg
img1 = cv2.imread(r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Resources\apps1.jpg")

# In apps1 row 0:
# Col 0 (BOARD MEETING): x in [0, 704], y in [0, 480]
col0 = img1[0:480, 0:704]

# Let's inspect where the icon actually is!
# We can find it by finding the center of mass or bounding box of pixels where:
# Not pure white. Notice background is (255, 255, 255).
# The icon has lumber strips in the center: (R ~ 200, G ~ 100, B ~ 60)
# Let's find coordinates of pixels with B < 200:
mask = col0[:, :, 0] < 200
coords = cv2.findNonZero(mask.astype(np.uint8))
bx, by, bw, bh = cv2.boundingRect(coords)
print(f"Col 0 inner art bounds: x={bx}, y={by}, w={bw}, h={bh}")

# The rounded square icon is centered on this!
# Center of the lumber symbol:
cx = bx + bw // 2
cy = by + bh // 2
print(f"Center of icon: ({cx}, {cy})")

# The icon is about 352x352 px (half is 176)
icon_half = 176
exact_icon = col0[cy - icon_half : cy + icon_half, cx - icon_half : cx + icon_half]
cv2.imwrite("tools/exact_bm.png", exact_icon)
print("Saved exact_bm.png shape:", exact_icon.shape)
