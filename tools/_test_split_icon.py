import cv2
import numpy as np

# Load test_exact_icon0.png
img = cv2.imread("tools/test_exact_icon0.png")
h, w, _ = img.shape

# The text "BOARD MEETING" begins around y = 350
# Let's inspect where the icon's bottom rounded corner ends:
# Look at horizontal lines:
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# The icon is roughly square (w is 352, so icon height should be ~352)
# Let's crop the icon only: [0:352, 0:352]
icon_only = img[0:352, 0:w]
cv2.imwrite("tools/test_icon_only0.png", icon_only)

# And text only:
text_only = img[352:h, :]
cv2.imwrite("tools/test_text_only0.png", text_only)

print(f"Icon only shape: {icon_only.shape}, Text only shape: {text_only.shape}")
