import cv2

img1 = cv2.imread(r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Resources\apps1.jpg")
h, w, _ = img1.shape
col_w = w // 4

for c in range(1, 4):
    x0 = c * col_w
    x1 = (c + 1) * col_w
    mid_cell = img1[450:1050, x0:x1]
    cv2.imwrite(f"tools/apps1_mid_c{c}.jpg", cv2.resize(mid_cell, (350, 300)))

for c in range(4):
    x0 = c * col_w
    x1 = (c + 1) * col_w
    bot_cell = img1[1000:1536, x0:x1]
    cv2.imwrite(f"tools/apps1_bot_c{c}.jpg", cv2.resize(bot_cell, (350, 270)))

print("Saved all apps1 middle and bottom slices!")
