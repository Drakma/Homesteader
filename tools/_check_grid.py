import cv2

# Check where the icon was actually located in cell 0
img1 = cv2.imread(r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Resources\apps1.jpg")
# Let's save the full top row with grid lines
h, w, _ = img1.shape
print("apps1 size:", w, h)

# Save the top half with vertical divider lines at 704, 1408, 2112:
debug_row0 = img1[0:520, :].copy()
for x in [704, 1408, 2112]:
    cv2.line(debug_row0, (x, 0), (x, 520), (0, 0, 255), 3)

cv2.imwrite("tools/debug_row0_grid.jpg", cv2.resize(debug_row0, (1408, 260)))
print("Saved debug_row0_grid.jpg")
