import cv2
import numpy as np

# In apps1.jpg and apps2.jpg:
# There are 2 rows of icons, but notice the vertical arrangement:
# The top row icon is around y = 80 to 450, its label is at y = 470 to 530.
# The bottom row icon is around y = 600 to 970, its label is at y = 990 to 1050.
# Let's inspect the actual height of icons and labels across apps1 and apps2.

img1 = cv2.imread(r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Resources\apps1.jpg")
h, w, _ = img1.shape
print("img1:", w, h)

# Let's create a montage or 8 separate slices centered on each (icon + label)
# Each column is w / 4 = 704 px wide.
# Top icon: y around [50, 600]
# Bottom icon: y around [550, 1150]
# Wait, are there only 2 rows? Let's check the bottom of apps1.

cv2.imwrite("tools/apps1_row1_full.jpg", cv2.resize(img1[0:768, :], (1408, 384)))
cv2.imwrite("tools/apps1_row2_full.jpg", cv2.resize(img1[768:1536, :], (1408, 384)))

img2 = cv2.imread(r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Resources\apps2.jpg")
cv2.imwrite("tools/apps2_row1_full.jpg", cv2.resize(img2[0:768, :], (1408, 384)))
cv2.imwrite("tools/apps2_row2_full.jpg", cv2.resize(img2[768:1536, :], (1408, 384)))

print("Saved full rows")
