import cv2
import numpy as np

# Load apps1 and apps2
img1 = cv2.imread(r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Resources\apps1.jpg")
img2 = cv2.imread(r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Resources\apps2.jpg")

print("img1:", img1.shape)
print("img2:", img2.shape)

# Let's write a script to crop out all 8 apps from apps1 and all 3 apps from apps2!
# On apps1:
# 2 rows x 4 columns:
# Row 0: y from 0 to ~760
# Row 1: y from 760 to 1536
# Col 0: x from 0 to 704
# Col 1: x from 704 to 1408
# Col 2: x from 1408 to 2112
# Col 3: x from 2112 to 2816

# On apps2:
# 1 row x 3 columns:
# x roughly centered:
# col 0: ~150 to ~900
# col 1: ~1000 to ~1800
# col 2: ~1850 to ~2650
