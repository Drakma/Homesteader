import cv2
import numpy as np

# Load apps1 and apps2
img1 = cv2.imread(r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Resources\apps1.jpg")
img2 = cv2.imread(r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Resources\apps2.jpg")

print("apps1 shape:", img1.shape)
print("apps2 shape:", img2.shape)

# apps1 has 8 icons in 2 visual rows:
# Looking at apps1_row1_full and apps1_row2_full:
# Row 1 (top): y approx [120, 680]
#   Col 0: BOARD MEETING (LUMBER YARD)
#   Col 1: NAIL IT (HOME DEPOT STORE)
#   Col 2: LETTUCE SHOP (GROCER)
#   Col 3: HAY THERE (FARMER'S FEED STORE)
# Row 2 (bottom): y approx [720, 1450]
#   Col 0: CACHE FLOW (BANK)  [top of icon is around y=720, label at bottom, then drafting behind you below it?]
# Wait! Let's inspect the vertical layout of apps1.jpg!

# Let's save 3 vertical slices of apps1 across full height:
cv2.imwrite("tools/apps1_col0_full.jpg", cv2.resize(img1[:, 0:704], (352, 768)))
cv2.imwrite("tools/apps1_col1_full.jpg", cv2.resize(img1[:, 704:1408], (352, 768)))
cv2.imwrite("tools/apps2_full.jpg", cv2.resize(img2, (704, 384)))

print("Saved column slices")
