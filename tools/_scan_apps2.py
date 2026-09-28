import cv2
import numpy as np

# Load apps2.jpg
img2 = cv2.imread(r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Resources\apps2.jpg")
h2, w2, _ = img2.shape
print("apps2:", w2, h2)

# Scan horizontal segments across y=500 in apps2:
row_scan = img2[500, :, :]
is_icon = np.any(row_scan < 235, axis=1)
segs = []
in_seg = False
start = 0
for x, val in enumerate(is_icon):
    if val and not in_seg:
        in_seg = True
        start = x
    elif not val and in_seg:
        in_seg = False
        segs.append((start, x))
if in_seg:
    segs.append((start, len(is_icon)))
print("apps2 y=500 segments:", segs)
