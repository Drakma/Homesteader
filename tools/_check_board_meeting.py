import cv2
import numpy as np

# Load apps1.jpg
img1 = cv2.imread(r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Resources\apps1.jpg")
h, w, _ = img1.shape

# Let's crop cell 0 (col 0, row 0) exactly around the icon
# In apps1, col 0 is x: [0, 704], row 0 is y: [0, 512]
cell = img1[0:512, 0:704]

# Let's find where the icon is located
# The icon has dark outer border / gradient
# Let's save a wide crop around the center of cell 0:
cv2.imwrite("tools/cell_0_0_raw.png", cell)
print("Saved cell_0_0_raw.png")
