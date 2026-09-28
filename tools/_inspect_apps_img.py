import cv2
import numpy as np

# Load apps1.jpg and apps2.jpg
img1 = cv2.imread(r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Resources\apps1.jpg")
img2 = cv2.imread(r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Resources\apps2.jpg")

print(f"apps1: {img1.shape}")
print(f"apps2: {img2.shape}")
