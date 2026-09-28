from PIL import Image
import numpy as np

src_path = r"C:/Users/casey/.gemini/antigravity/brain/22a79297-c0db-46b0-a570-39cffdd3aaae/.user_uploaded/media_1789973909748.png"
img = Image.open(src_path).convert("RGBA")
arr = np.array(img)

# For each of the three icons, let's inspect the top, left, right, bottom of the squircle
# Icon 1: ~113 to 324 X, 134 to 345 Y (without shadow)
# Let's crop candidate regions and check
for name, x1, x2 in [("voltvision", 100, 340), ("techtrak", 400, 630), ("trailer_shack", 700, 930)]:
    crop = arr[120:380, x1:x2]
    # In each crop, let's find the squircle boundary. The background is white (r>250, g>250, b>250)
    is_not_white = ~((crop[:, :, 0] > 248) & (crop[:, :, 1] > 248) & (crop[:, :, 2] > 248))
    # Ignore bottom shadow (shadow has low saturation and moderate darkness)
    # Let's print bounds of is_not_white
    ys, xs = np.where(is_not_white)
    print(f"{name}: Y={ys.min()+120}..{ys.max()+120} (H={ys.max()-ys.min()+1}), X={xs.min()+x1}..{xs.max()+x1} (W={xs.max()-xs.min()+1})")

