#!/usr/bin/env python3
"""Remove small disconnected alpha components (stray digit glyphs) from a PNG,
keeping only the largest connected foreground blob."""
import sys
from PIL import Image
from collections import deque


def clean(path):
    img = Image.open(path).convert("RGBA")
    w, h = img.size
    alpha = img.split()[3]
    apx = alpha.load()
    visited = bytearray(w * h)

    def idx(x, y):
        return y * w + x

    comps = []
    for y in range(h):
        for x in range(w):
            i = idx(x, y)
            if not visited[i] and apx[x, y] > 10:
                q = deque([(x, y)])
                visited[i] = 1
                pixels = []
                while q:
                    cx, cy = q.popleft()
                    pixels.append((cx, cy))
                    for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
                        nx, ny = cx+dx, cy+dy
                        if 0 <= nx < w and 0 <= ny < h:
                            ni = idx(nx, ny)
                            if not visited[ni] and apx[nx, ny] > 10:
                                visited[ni] = 1
                                q.append((nx, ny))
                comps.append(pixels)

    if len(comps) <= 1:
        print(f"{path}: only one component, nothing to strip")
        return

    comps.sort(key=len, reverse=True)
    keep = set(comps[0])
    dropped = sum(len(c) for c in comps[1:])
    print(f"{path}: keeping largest component ({len(comps[0])}px), dropping {len(comps)-1} others ({dropped}px)")

    px = img.load()
    for y in range(h):
        for x in range(w):
            if (x, y) not in keep and apx[x, y] > 0:
                px[x, y] = (0, 0, 0, 0)

    # Re-crop tight, then re-pad onto a clean 128x128 canvas (icon-style guide
    # spec) so stripping specks never silently shrinks/un-pads the final icon.
    bbox = img.split()[3].getbbox()
    item = img.crop(bbox)
    max_dim, target = 104, 128
    scale = min(max_dim / item.width, max_dim / item.height)
    nw, nh = max(1, round(item.width * scale)), max(1, round(item.height * scale))
    resized = item.resize((nw, nh), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (target, target), (0, 0, 0, 0))
    canvas.paste(resized, ((target - nw) // 2, (target - nh) // 2), resized)
    canvas.save(path)


if __name__ == "__main__":
    for p in sys.argv[1:]:
        clean(p)
