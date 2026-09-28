import cv2
import numpy as np

img2 = cv2.imread(r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Resources\apps2.jpg")
h, w, _ = img2.shape
print("apps2 shape:", w, h)

# Let's save 4 slices across apps2 with proper horizontal coverage
# Let's see where the icons are located in apps2
cv2.imwrite("tools/apps2_full.jpg", cv2.resize(img2, (1408, 768)))
