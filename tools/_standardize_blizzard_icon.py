import cv2
import numpy as np
from PIL import Image

# Read the cropped blizzard art
crop_path = r"Homesteader\Assets\Resources\debug_blizzard_crop.png"
img_bgr = cv2.imread(crop_path)
h, w, _ = img_bgr.shape

# The background is off-white studio background (~248..255).
# Some parts of the snowflakes are very light cyan/white (~235..250).
# Let's inspect background color specifically from outer borders:
border_pixels = np.concatenate([
    img_bgr[0, :], img_bgr[-1, :], img_bgr[:, 0], img_bgr[:, -1]
])
bg_color = np.median(border_pixels, axis=0) # [B, G, R]
print(f"Detected background BGR: {bg_color}")

# Calculate color difference from background
diff = np.linalg.norm(img_bgr.astype(np.float32) - bg_color.astype(np.float32), axis=2)

# Floodfill from corners to only remove exterior background, never inside the cloud!
mask = np.zeros((h + 2, w + 2), dtype=np.uint8)
flood_diff = (8, 8, 8)

# Floodfill from four corners
corners = [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1), 
           (w // 2, 0), (0, h // 2), (w - 1, h // 2), (w // 2, h - 1)]

filled_mask = np.zeros((h, w), dtype=np.uint8)
for cx, cy in corners:
    c_img = img_bgr.copy()
    c_mask = np.zeros((h + 2, w + 2), dtype=np.uint8)
    # Use floodfill with tolerance
    cv2.floodFill(c_img, c_mask, (cx, cy), (0, 255, 0), flood_diff, flood_diff, cv2.FLOODFILL_MASK_ONLY | (255 << 8))
    filled_mask = np.maximum(filled_mask, c_mask[1:-1, 1:-1])

# Alpha channel: where filled_mask is 255, alpha is 0.
# Near the transition boundary, create smooth anti-aliased edge:
# Compute distance from outer background
dist_to_bg = cv2.distanceTransform((filled_mask == 0).astype(np.uint8), cv2.DIST_L2, 5)

alpha = np.clip(dist_to_bg * 1.5, 0.0, 1.0) * 255.0

# For pixels where background was removed, de-fringe the white background from edges
# Un-premultiply against the background color
alpha_norm = (alpha / 255.0)[:, :, np.newaxis]
img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB).astype(np.float32)
bg_rgb = np.array([bg_color[2], bg_color[1], bg_color[0]], dtype=np.float32)

# De-multiply edge pixels: C_art = (C_blend - (1 - a) * C_bg) / max(a, 0.05)
clean_rgb = np.where(alpha_norm > 0.01, (img_rgb - (1.0 - alpha_norm) * bg_rgb) / np.maximum(alpha_norm, 0.05), img_rgb)
clean_rgb = np.clip(clean_rgb, 0, 255).astype(np.uint8)

# Construct RGBA image
rgba = np.dstack([clean_rgb, alpha.astype(np.uint8)])
pil_img = Image.fromarray(rgba, mode="RGBA")

# Standardize to 128x128 RGBA (max 104px content, 12px margin, perimeter alpha=0, no borders)
# Find tight bounding box of visible alpha
bbox = pil_img.getbbox()
pil_cropped = pil_img.crop(bbox)

# Target max dimension = 104px (12px margin on 128x128)
max_dim = 104
ratio = min(max_dim / float(pil_cropped.width), max_dim / float(pil_cropped.height))
new_w = int(round(pil_cropped.width * ratio))
new_h = int(round(pil_cropped.height * ratio))
pil_resized = pil_cropped.resize((new_w, new_h), Image.Resampling.LANCZOS)

final_icon = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
paste_x = (128 - new_w) // 2
paste_y = (128 - new_h) // 2
final_icon.paste(pil_resized, (paste_x, paste_y), pil_resized)

out_path = r"Homesteader\Assets\Resources\HUDTree\KitSprites\weather\weather_blizzard.png"
final_icon.save(out_path, "PNG")
print(f"Saved standardized 128x128 icon to {out_path}!")
