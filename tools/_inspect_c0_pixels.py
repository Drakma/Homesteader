import cv2
import numpy as np

img = cv2.imread("tools/c0_full.png")
icon_zone = img[0:390, :]
h, w, _ = icon_zone.shape

# Let's inspect pixel values across the top edge and left edge:
print("Top-left 5x5 BGR:\n", icon_zone[0:5, 0:5])
print("Middle of top row (x=352, y=0:10):\n", icon_zone[0:10, 350:354])
# Where does the actual icon begin? The icon has a drop shadow or rounded corner!
# The center of the icon in c0_full is roughly at x = 352, y = 200.
# The icon is about 330x330 px.
# Let's sample a point definitely inside the icon: (352, 200) -> BGR:
print("Center (x=352, y=200):", icon_zone[200, 352])
# The outer background is white [254, 254, 254]
# Why did diff > 4 match (0,0)? Let's check icon_zone[0, 0]:
print("Pixel at (0,0):", icon_zone[0, 0])
