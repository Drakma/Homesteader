import cv2
import numpy as np

# Load c0_full.png
img = cv2.imread("tools/c0_full.png")
h, w, _ = img.shape
print(f"c0_full size: {w}x{h}")

# The background is white (RGB > 245)
# In c0_full, the icon badge is a rounded rectangle with gradient:
# top is light cream (~250, 230, 200), bottom is warm orange/coral (~240, 140, 110)
# Notice the top right of the badge has color (253, 238, 202), which is very close to white!
# So a simple grayscale threshold < 240 clipped the top of the badge!
# Let's see the color difference:
# Background is pure white: [255, 255, 255]
# Let's inspect rows from top down to find where pixels deviate from white [255, 255, 255]:

diff = np.max(np.abs(img.astype(np.int32) - 255), axis=2)
# Any pixel with diff > 4 is not pure white background!
mask = diff > 4

coords = cv2.findNonZero(mask.astype(np.uint8))
bx, by, bw, bh = cv2.boundingRect(coords)
print(f"Full content bounding box: x={bx}, y={by}, w={bw}, h={bh}")

# The icon is in the upper part, text is at the bottom.
# The text "BOARD MEETING" starts at around y = 400.
# Let's find the gap between the icon bottom and the text top:
# Project horizontally (count non-white pixels per row):
row_counts = np.sum(mask, axis=1)
for y in range(by + 250, by + bh):
    if row_counts[y] == 0:
        print(f"Empty row found at y={y}!")
        break
