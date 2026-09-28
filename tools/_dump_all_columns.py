import cv2
import numpy as np

img1 = cv2.imread(r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Resources\apps1.jpg")
img2 = cv2.imread(r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Resources\apps2.jpg")

print("apps1:", img1.shape)
print("apps2:", img2.shape)

# Let's save each of the 4 columns of apps1 and apps2 so we can read every single app and its replacement!
for col in range(4):
    x0 = col * 704
    x1 = (col + 1) * 704
    cv2.imwrite(f"tools/apps1_c{col}.jpg", cv2.resize(img1[:, x0:x1], (352, 768)))
    cv2.imwrite(f"tools/apps2_c{col}.jpg", cv2.resize(img2[:, x0:x1], (352, 768)))

print("Saved all 8 columns!")
