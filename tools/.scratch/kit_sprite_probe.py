"""Verify dimensions and unique sizes of the kit sprites before baking them
into Unity atlases. Also flags perimeter-alpha=0 violations."""
import os, sys
from collections import Counter
from PIL import Image

KIT = r"C:\Users\casey\Desktop\Homesteader\assets\hud_kit\sprites"
print(f"Kit root: {KIT}")
sizes = Counter()
files = []
for sub in os.listdir(KIT):
    sub_p = os.path.join(KIT, sub)
    if not os.path.isdir(sub_p):
        continue
    for fn in sorted(os.listdir(sub_p)):
        if not fn.lower().endswith(".png"):
            continue
        path = os.path.join(sub_p, fn)
        files.append(path)
        try:
            im = Image.open(path)
            sizes[im.size] += 1
        except Exception as e:
            print(f"BAD {path}: {e}")
print(f"Total: {len(files)} files")
print("Sizes (top 10):")
for s, c in sizes.most_common(10):
    print(f"  {s} : {c}")

# Sample a flash to confirm the canvas contract (perimeter alpha = 0).
violations = []
for path in files:
    im = Image.open(path)
    im = im.convert("RGBA")
    w, h = im.size
    px = im.load()
    for x in range(w):
        if px[x, 0][3] != 0 or px[x, h - 1][3] != 0:
            violations.append((path, "h-edge"))
            break
    for y in range(h):
        if px[0, y][3] != 0 or px[w - 1, y][3] != 0:
            violations.append((path, "v-edge"))
            break
print(f"Perimeter-alpha violations: {len(violations)}")
for v in violations[:5]:
    print("  ", v)
