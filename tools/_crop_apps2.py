import cv2
import numpy as np

img2 = cv2.imread(r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Resources\apps2.jpg")
h, w, _ = img2.shape

# Save 3 crops for apps2
c0 = img2[:, 0:950]
c1 = img2[:, 950:1850]
c2 = img2[:, 1850:2816]

cv2.imwrite("tools/apps2_item0.jpg", cv2.resize(c0, (475, 768)))
cv2.imwrite("tools/apps2_item1.jpg", cv2.resize(c1, (450, 768)))
cv2.imwrite("tools/apps2_item2.jpg", cv2.resize(c2, (483, 768)))

print("Saved apps2 items")
