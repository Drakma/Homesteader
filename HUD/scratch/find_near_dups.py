import os
from PIL import Image, ImageChops, ImageStat

HUD_ITEMS = r"C:\Users\casey\Desktop\Homesteader\HUD\assets\items"
files = sorted([f for f in os.listdir(HUD_ITEMS) if f.endswith(".png")])

images = {}
for f in files:
    im = Image.open(os.path.join(HUD_ITEMS, f)).convert("RGBA")
    images[f] = im.resize((32, 32))

near_dups = []
for i in range(len(files)):
    f1 = files[i]
    im1 = images[f1]
    for j in range(i + 1, len(files)):
        f2 = files[j]
        im2 = images[f2]
        diff = ImageChops.difference(im1, im2)
        stat = ImageStat.Stat(diff)
        mean_diff = sum(stat.mean) / len(stat.mean)
        if mean_diff < 1.0:
            near_dups.append((f1, f2, mean_diff))

print(f"=== Virtually identical image pairs (diff < 1.0): {len(near_dups)} pairs ===")
for f1, f2, d in near_dups:
    print(f"  {f1:<30} <-> {f2:<30} (mean diff: {d:.2f})")
