#!/usr/bin/env python3
"""Extract a single logo (many disjoint shapes) from a solid-bg image as one
tightly-cropped transparent PNG, keeping ALL foreground pixels (not just the
largest connected component)."""
import sys
import math
from PIL import Image


def extract(path, out_path, tol=28.0):
    img = Image.open(path).convert("RGB")
    w, h = img.size
    px = img.load()

    corners = []
    patch = 6
    for (cx, cy) in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]:
        for dx in range(patch):
            for dy in range(patch):
                x = min(w - 1, max(0, cx + (dx if cx == 0 else -dx)))
                y = min(h - 1, max(0, cy + (dy if cy == 0 else -dy)))
                corners.append(px[x, y])
    bg = tuple(sum(c[i] for c in corners) / len(corners) for i in range(3))

    rgba = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    for y in range(h):
        for x in range(w):
            p = px[x, y]
            d = math.sqrt(sum((p[i] - bg[i]) ** 2 for i in range(3)))
            if d >= tol:
                alpha = 255 if d >= tol + 8 else int(255 * (d - tol) / 8.0)
                rgba.putpixel((x, y), (p[0], p[1], p[2], alpha))

    bbox = rgba.split()[3].getbbox()
    if not bbox:
        print("FAILED: nothing detected")
        return
    cropped = rgba.crop(bbox)
    cropped.save(out_path)
    print(f"Saved {out_path} size={cropped.size} bg={bg}")


if __name__ == "__main__":
    extract(sys.argv[1], sys.argv[2])
