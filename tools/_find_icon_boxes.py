import cv2
import numpy as np

# apps1: 2816 x 1536
# 3 rows x 4 columns = 12 apps!
# apps2: 2816 x 1536
# 1 row x 3 columns = 3 apps!
# Total = 15 apps!

# Let's inspect coordinates for apps1 and apps2.
img1 = cv2.imread(r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Resources\apps1.jpg")
img2 = cv2.imread(r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Resources\apps2.jpg")

print("img1:", img1.shape)
print("img2:", img2.shape)

# Let's write a script to find the bounding boxes of all 12 rounded square app icons in apps1
# and the 3 rounded square app icons in apps2.
# Notice each icon has rounded corners and dark borders or colored background.
