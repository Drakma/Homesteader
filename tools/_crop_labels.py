import cv2
import numpy as np

# Let's inspect the entire sheets apps1 and apps2 with vertical divisions.
# Let's save slices of apps1 specifically showing the labels under each icon:
img1 = cv2.imread(r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Resources\apps1.jpg")
h1, w1, _ = img1.shape
col_w = w1 // 4

# Let's crop just the label area under each of the 12 icons:
# Row 0 labels: y approx 430 to 520
# Row 1 labels: y approx 940 to 1040
# Row 2 labels: y approx 1440 to 1536

for r, (ly0, ly1) in enumerate([(430, 520), (940, 1040), (1440, 1536)]):
    for c in range(4):
        x0 = c * col_w
        x1 = (c + 1) * col_w
        lbl = img1[ly0:ly1, x0:x1]
        cv2.imwrite(f"tools/lbl_r{r}_c{c}.png", lbl)

print("Saved all 12 labels for apps1!")
