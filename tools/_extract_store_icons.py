import numpy as np
from PIL import Image

src_path = r"C:/Users/casey/.gemini/antigravity/brain/22a79297-c0db-46b0-a570-39cffdd3aaae/.user_uploaded/media_1789973909748.png"
img = Image.open(src_path).convert("RGB")
arr = np.array(img)
bg_color = arr[10, 10]
diff = np.max(np.abs(arr.astype(int) - bg_color.astype(int)), axis=2)

icon_mask = diff[:380, :] > 25
y_indices = np.where(np.any(icon_mask, axis=1))[0]
ymin, ymax = y_indices[0], y_indices[-1]
print(f"Y bounds: {ymin} to {ymax} (height {ymax - ymin + 1})")

col_mask = np.any(icon_mask, axis=0)
diff_cols = np.diff(col_mask.astype(int))
starts = np.where(diff_cols == 1)[0] + 1
if col_mask[0]:
    starts = np.insert(starts, 0, 0)
ends = np.where(diff_cols == -1)[0]
if col_mask[-1]:
    ends = np.append(ends, len(col_mask) - 1)

print("Icon segments:")
for s, e in zip(starts, ends):
    print(f"  Col: {s} to {e} (width {e - s + 1})")

