#!/usr/bin/env python3
"""
Generic concept-sheet item extractor.
Segments a concept sheet (solid dark slate background) into connected-component
items via outside-in flood fill, sorts them in reading order (row-major), and
extracts each into a clean 128x128 RGBA canvas per the Homesteader Item Icon
Style Guide (outside-in perimeter flood fill, <=104px max dim, 12px margin,
alpha=0 border).
"""
import sys
import math
from PIL import Image, ImageFilter


def find_components(img, tol=28.0, min_area=10000, erode=0):
    im = img.convert("RGB")
    w, h = im.size
    px = im.load()

    # sample background color from the four corners (average small patches)
    corners = []
    patch = 6
    for (cx, cy) in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]:
        for dx in range(patch):
            for dy in range(patch):
                x = min(w - 1, max(0, cx + (dx if cx == 0 else -dx)))
                y = min(h - 1, max(0, cy + (dy if cy == 0 else -dy)))
                corners.append(px[x, y])
    bg = tuple(sum(c[i] for c in corners) / len(corners) for i in range(3))

    def is_bg(p):
        return math.sqrt(sum((p[i] - bg[i]) ** 2 for i in range(3))) < tol

    # binary fg mask (255=foreground), then erode a few px to snap thin bridges
    # between items that touch across row/column boundaries in the raw render.
    mask = Image.new("L", (w, h), 0)
    mpx = mask.load()
    for y in range(h):
        for x in range(w):
            if not is_bg(px[x, y]):
                mpx[x, y] = 255
    if erode > 0:
        mask = mask.filter(ImageFilter.MinFilter(2 * erode + 1))
    mpx = mask.load()

    visited = bytearray(w * h)  # 0=unvisited fg, 1=processed

    def idx(x, y):
        return y * w + x

    from collections import deque
    comps = []
    for y in range(h):
        for x in range(w):
            i = idx(x, y)
            if not visited[i] and mpx[x, y] == 255:
                comp_pixels = []
                q = deque([(x, y)])
                visited[i] = 1
                minx = maxx = x
                miny = maxy = y
                while q:
                    cx, cy = q.popleft()
                    comp_pixels.append((cx, cy))
                    minx = min(minx, cx); maxx = max(maxx, cx)
                    miny = min(miny, cy); maxy = max(maxy, cy)
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nx, ny = cx + dx, cy + dy
                        if 0 <= nx < w and 0 <= ny < h:
                            ni = idx(nx, ny)
                            if not visited[ni] and mpx[nx, ny] == 255:
                                visited[ni] = 1
                                q.append((nx, ny))
                if len(comp_pixels) >= min_area:
                    # grow bbox back out by the erosion radius since the mask shrank
                    comps.append((max(0, minx - erode), max(0, miny - erode),
                                  min(w - 1, maxx + erode), min(h - 1, maxy + erode),
                                  len(comp_pixels)))
    return comps, bg


def extract_from_bbox(img, bbox, bg, tol=28.0, pad=14, max_dim=104, target_size=128):
    x0, y0, x1, y1, _area = bbox
    w, h = img.size
    cx0 = max(0, x0 - pad)
    cy0 = max(0, y0 - pad)
    cx1 = min(w, x1 + pad + 1)
    cy1 = min(h, y1 + pad + 1)
    crop = img.crop((cx0, cy0, cx1, cy1)).convert("RGB")
    cw, ch = crop.size

    def is_bg(p):
        return math.sqrt(sum((p[i] - bg[i]) ** 2 for i in range(3))) < tol

    rgba = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    cpx = crop.load()
    for yy in range(ch):
        for xx in range(cw):
            p = cpx[xx, yy]
            if not is_bg(p):
                d = math.sqrt(sum((p[i] - bg[i]) ** 2 for i in range(3)))
                alpha = 255 if d >= tol + 8 else min(255, max(0, int(255 * (d - tol + 8) / 8.0)))
                rgba.putpixel((xx, yy), (p[0], p[1], p[2], alpha))

    bbox2 = rgba.split()[3].getbbox()
    if not bbox2:
        return None
    item_only = rgba.crop(bbox2)
    scale = min(float(max_dim) / item_only.width, float(max_dim) / item_only.height)
    nw = max(1, int(round(item_only.width * scale)))
    nh = max(1, int(round(item_only.height * scale)))
    resized = item_only.resize((nw, nh), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (target_size, target_size), (0, 0, 0, 0))
    canvas.paste(resized, ((target_size - nw) // 2, (target_size - nh) // 2), resized)
    return canvas


def main(sheet_path, names, out_dir, max_rows=None):
    img = Image.open(sheet_path)
    comps, bg = find_components(img)
    print(f"Detected {len(comps)} components, bg={bg}")

    # cluster into rows by y-center proximity
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
    if max_rows:
        rows = rows[:max_rows]

    ordered = []
    for row in rows:
        ordered.extend(sorted(row["items"], key=lambda c: (c[0] + c[2]) / 2))

    print(f"Ordered {len(ordered)} items across {len(rows)} rows")
    if len(ordered) != len(names):
        print(f"WARNING: found {len(ordered)} items but {len(names)} names given")

    import os
    os.makedirs(out_dir, exist_ok=True)
    for name, bbox in zip(names, ordered):
        canvas = extract_from_bbox(img, bbox, bg)
        if canvas is None:
            print(f"FAILED to extract {name}")
            continue
        out_path = os.path.join(out_dir, f"{name}.png")
        canvas.save(out_path)
        print(f"Saved {out_path}  bbox={bbox}")


if __name__ == "__main__":
    sheet = sys.argv[1]
    names = sys.argv[2].split(",")
    out_dir = sys.argv[3]
    max_rows = int(sys.argv[4]) if len(sys.argv) > 4 else None
    main(sheet, names, out_dir, max_rows)
