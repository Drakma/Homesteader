#!/usr/bin/env python3
"""Extract items from a concept sheet at native resolution (no icon downscale)."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extract_sheet_auto import find_components, extract_from_bbox
from PIL import Image


def main(sheet_path, names, out_dir, pad=20):
    img = Image.open(sheet_path)
    comps, bg = find_components(img)
    comps_sorted = sorted(comps, key=lambda b: (b[1] + b[3]) / 2)
    rows = []
    row_thresh = img.size[1] * 0.08
    for c in comps_sorted:
        ycenter = (c[1] + c[3]) / 2
        placed = False
        for row in rows:
            if abs(row["y"] - ycenter) < row_thresh:
                row["items"].append(c)
                row["y"] = (row["y"] * len(row["items"]) + ycenter) / (len(row["items"]) + 1)
                placed = True
                break
        if not placed:
            rows.append({"y": ycenter, "items": [c]})
    rows.sort(key=lambda r: r["y"])
    ordered = []
    for row in rows:
        ordered.extend(sorted(row["items"], key=lambda c: (c[0] + c[2]) / 2))

    print(f"Detected {len(ordered)} components across {len(rows)} rows for {len(names)} names")
    os.makedirs(out_dir, exist_ok=True)
    for name, bbox in zip(names, ordered):
        # full-res extract: no downscale, no square canvas, just tight alpha crop with padding
        x0, y0, x1, y1, _ = bbox
        w, h = img.size
        cx0 = max(0, x0 - pad); cy0 = max(0, y0 - pad)
        cx1 = min(w, x1 + pad + 1); cy1 = min(h, y1 + pad + 1)
        crop = img.crop((cx0, cy0, cx1, cy1)).convert("RGB")
        import math
        cw, ch = crop.size
        cpx = crop.load()
        rgba = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        tol = 28.0
        for yy in range(ch):
            for xx in range(cw):
                p = cpx[xx, yy]
                d = math.sqrt(sum((p[i] - bg[i]) ** 2 for i in range(3)))
                if d >= tol:
                    alpha = 255 if d >= tol + 8 else int(255 * (d - tol) / 8.0)
                    rgba.putpixel((xx, yy), (p[0], p[1], p[2], alpha))
        bbox2 = rgba.split()[3].getbbox()
        if not bbox2:
            print(f"FAILED {name}")
            continue
        final = rgba.crop(bbox2)
        out_path = os.path.join(out_dir, f"{name}.png")
        final.save(out_path)
        print(f"Saved {out_path}  size={final.size}  bbox={bbox}")


if __name__ == "__main__":
    sheet = sys.argv[1]
    names = sys.argv[2].split(",")
    out_dir = sys.argv[3]
    main(sheet, names, out_dir)
