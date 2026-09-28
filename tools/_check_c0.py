import cv2

# Check card1_0_0 vs apps1
card = cv2.imread("tools/card1_0_0.jpg")
print("card shape:", card.shape)
# Save card at full resolution
img1 = cv2.imread(r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Resources\apps1.jpg")
c0_full = img1[60:560, 0:704]
cv2.imwrite("tools/c0_full.png", c0_full)
print("Saved c0_full.png")
