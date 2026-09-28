import cv2
import numpy as np

# Load apps1 and apps2
img1 = cv2.imread(r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Resources\apps1.jpg")
img2 = cv2.imread(r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Resources\apps2.jpg")

# In apps1:
# We know the icon size is 352x352.
# Col 0 icon is at x = 285, y = 94.
# Let's find the exact (x, y) for all 12 icons in apps1!

# Let's search horizontally for the 4 column positions in Row 0 (y around 94):
# We can find the top-left of each icon by detecting where the background transitions from pure white (RGB > 245)
# to non-white along row y = 200:
row0_scan = img1[200, :, :]
# Find non-white pixels:
is_icon = np.any(row0_scan < 235, axis=1)

# Find contiguous segments of True:
segments = []
in_seg = False
start = 0
for x, val in enumerate(is_icon):
    if val and not in_seg:
        in_seg = True
        start = x
    elif not val and in_seg:
        in_seg = False
        segments.append((start, x))
if in_seg:
    segments.append((start, len(is_icon)))

print("Row 0 horizontal segments:", segments)

# Let's do the same for Row 1 (y around 600) and Row 2 (y around 1100):
for r_y in [200, 700, 1200]:
    row_scan = img1[r_y, :, :]
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
    print(f"y={r_y} horizontal segments:", segs)
