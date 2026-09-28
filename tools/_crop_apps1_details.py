import cv2

img1 = cv2.imread(r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Resources\apps1.jpg")
h, w, _ = img1.shape
col_w = w // 4
row_h = h // 2

# Row 0
for c in range(4):
    cell = img1[0:row_h, c*col_w:(c+1)*col_w]
    cv2.imwrite(f"tools/apps1_r0_c{c}_detail.jpg", cv2.resize(cell, (400, 436)))

# Row 1
for c in range(4):
    cell = img1[row_h:h, c*col_w:(c+1)*col_w]
    cv2.imwrite(f"tools/apps1_r1_c{c}_detail.jpg", cv2.resize(cell, (400, 436)))

print("Saved apps1 details")
