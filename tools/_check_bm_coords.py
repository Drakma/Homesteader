import cv2
import numpy as np

# In test_proper_icon0.png:
# Proper Icon Bounding Box: x=285, y=34, w=351, h=352 within cell0 (which was img1[0:550, 0:704]).
# That means in img1:
# Col 0 icon is at x = 285 to 636! (cx = 460.5)
# Wait! Earlier we saw:
# cell0 = img1[0:550, 0:704]
# cell0 icon x was 285! 285 + 351 = 636!
# That means the icon is at x = 285, y = 94 in img1!
# Let's verify directly:
img1 = cv2.imread(r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Resources\apps1.jpg")
bm_crop = img1[94:94+352, 285:285+352]
cv2.imwrite("tools/bm_from_coords.png", bm_crop)
print("Saved bm_from_coords.png shape:", bm_crop.shape)
