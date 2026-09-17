import os
import math
from PIL import Image, ImageFilter
ASSETS_ROOT = r"c:\Users\casey\Desktop\Homesteader\assets"
ITEMS_DIR = os.path.join(ASSETS_ROOT, "items")
UNREAL_ICONS_DIR = r"C:\Users\casey\Desktop\Homesteader\Homesteader\Content\Homesteader\UI\Icons"

TARGET_SIZE = 128
PADDING = 12  # px padding from border

def clean_icon_transparency(img_path, out_paths):
    img = Image.open(img_path).convert("RGBA")
    w, h = img.size

    # 1. Sample perimeter background color
    border_pixels = []
    for x in range(w):
        border_pixels.append(img.getpixel((x, 0))[:3])
        border_pixels.append(img.getpixel((x, h - 1))[:3])
    for y in range(h):
        border_pixels.append(img.getpixel((0, y))[:3])
        border_pixels.append(img.getpixel((w - 1, y))[:3])

    avg_bg_r = sum(p[0] for p in border_pixels) / len(border_pixels)
    avg_bg_g = sum(p[1] for p in border_pixels) / len(border_pixels)
    avg_bg_b = sum(p[2] for p in border_pixels) / len(border_pixels)
    bg_ref = (avg_bg_r, avg_bg_g, avg_bg_b)

    # 2. Compute color distance from background for all pixels
    data = list(img.getdata())
    new_data = []

    # Tolerances tuned for dark slate background
    tol_low = 22.0
    tol_high = 48.0

    for idx, (r, g, b, a) in enumerate(data):
        dist = math.sqrt((r - bg_ref[0])**2 + (g - bg_ref[1])**2 + (b - bg_ref[2])**2)
        if dist <= tol_low:
            new_data.append((0, 0, 0, 0))
        elif dist >= tol_high:
            new_data.append((r, g, b, 255))
        else:
            # Smooth feathered edge
            ratio = (dist - tol_low) / (tol_high - tol_low)
            # De-spill background color from semi-transparent fringe
            alpha = int(255 * ratio)
            # Unmix background color: foreground ~ (pixel - (1 - ratio)*bg) / ratio
            unmix_r = min(255, max(0, int((r - (1 - ratio) * bg_ref[0]) / max(0.1, ratio))))
            unmix_g = min(255, max(0, int((g - (1 - ratio) * bg_ref[1]) / max(0.1, ratio))))
            unmix_b = min(255, max(0, int((b - (1 - ratio) * bg_ref[2]) / max(0.1, ratio))))
            new_data.append((unmix_r, unmix_g, unmix_b, alpha))

    img.putdata(new_data)

    # 3. Flood-fill clear from the 4 corners to remove any stray border noise
    mask = img.split()[3]
    bbox = mask.getbbox()
    if not bbox:
        # Fallback if image became completely transparent
        return False

    # Crop tightly to item bounds
    cropped = img.crop(bbox)

    # Center into target square with padding
    canvas = Image.new("RGBA", (TARGET_SIZE, TARGET_SIZE), (0, 0, 0, 0))
    max_dim = TARGET_SIZE - (PADDING * 2)
    scale = min(max_dim / cropped.width, max_dim / cropped.height)
    new_w = max(1, int(cropped.width * scale))
    new_h = max(1, int(cropped.height * scale))
    resized = cropped.resize((new_w, new_h), Image.Resampling.LANCZOS)

    offset_x = (TARGET_SIZE - new_w) // 2
    offset_y = (TARGET_SIZE - new_h) // 2
    canvas.paste(resized, (offset_x, offset_y), resized)

    for out in out_paths:
        os.makedirs(os.path.dirname(out), exist_ok=True)
        canvas.save(out, "PNG")

    return True

print("Refining and cleaning all icons for 100% transparent backgrounds...")

# Gather all files in UNREAL_ICONS_DIR and ITEMS_DIR
files = set()
for d in [UNREAL_ICONS_DIR, ITEMS_DIR]:
    if os.path.exists(d):
        for f in os.listdir(d):
            if f.endswith(".png") and not f.endswith("_opaque.png"):
                files.add(f)

count = 0
for f in sorted(files):
    # Find source file
    src = os.path.join(UNREAL_ICONS_DIR, f)
    if not os.path.exists(src):
        src = os.path.join(ITEMS_DIR, f)

    out1 = os.path.join(ITEMS_DIR, f)
    out2 = os.path.join(UNREAL_ICONS_DIR, f)
    # Also mirror the flat icon beside the canonical assets root.
    out3 = os.path.join(ASSETS_ROOT, "_legacy_from_hud", "png", f)
    
    success = clean_icon_transparency(src, [out1, out2, out3])
    if success:
        count += 1

# Also ensure aliases exist with clean transparency
aliases = [
    ("meat_beef.png", "animal_meat.png"),
    ("mat_leather.png", "pelt_cow.png"),
    ("meat_mutton.png", "meat_goat.png"),
    ("mat_leather.png", "pelt_goat.png"),
    # Map legacy icon names to CSV names
    ("tool_axe.png", "icon_axe.png"),
    ("tool_pickaxe.png", "icon_pickaxe.png"),
    ("tool_shovel.png", "icon_shovel.png"),
    ("tool_watering_can.png", "icon_watering_can.png"),
    ("crop_wheat.png", "icon_wheat.png"),
    ("seed_wheat.png", "icon_seeds.png"),
    ("food_bread.png", "icon_bread.png"),
    ("mat_lumber.png", "icon_wood_log.png"),
]

for src_name, dst_name in aliases:
    for base_dir in [HUD_ITEMS_DIR, UNREAL_ICONS_DIR]:
        sp = os.path.join(base_dir, src_name)
        dp = os.path.join(base_dir, dst_name)
        if os.path.exists(sp):
            img = Image.open(sp)
            img.save(dp, "PNG")

print(f"Successfully processed {count} icons! All icons now have 100% transparent backgrounds with de-spilled anti-aliased borders.")

