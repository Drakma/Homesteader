"""Draws the icons of the path and road kits (no model: a curved strip of the surface, like the fence items have none).
    python tools/make_path_icons.py
128x128 RGBA, content within 104 px (12 px margin), fully transparent edge.
"""
import math
import os
import random

from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ITEMS = {
    'path_dirt': ((140, 107, 71), (110, 82, 52), 'dirt', 18),
    'path_gravel': ((168, 163, 153), (130, 126, 118), 'gravel', 18),
    'path_stone': ((152, 148, 142), (110, 106, 100), 'stone', 18),
    'road_gravel': ((158, 148, 128), (120, 112, 96), 'gravel', 30),
    'road_asphalt': ((56, 56, 61), (36, 36, 40), 'asphalt', 30),
}


def curve(t):
    # an S bend lying on the ground, seen from above-left (isometric squash)
    x = 14 + t * 100
    y = 64 + math.sin(t * math.pi * 1.6 - 0.8) * 22
    return x, y


def draw(iid):
    fill, edge, style, width = ITEMS[iid]
    S = 4
    im = Image.new('RGBA', (128 * S, 128 * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    left, right = [], []
    n = 60
    for i in range(n + 1):
        t = i / n
        x, y = curve(t)
        x2, y2 = curve(min(1.0, t + 0.01))
        x1, y1 = curve(max(0.0, t - 0.01))
        dx, dy = x2 - x1, y2 - y1
        l = math.hypot(dx, dy) or 1
        nx, ny = -dy / l, dx / l
        h = width * 0.5
        left.append(((x + nx * h) * S, (y + ny * h * 0.6) * S))
        right.append(((x - nx * h) * S, (y - ny * h * 0.6) * S))
    poly = left + right[::-1]
    shadow = [(px, py + 5 * S) for px, py in poly]
    d.polygon(shadow, fill=(0, 0, 0, 70))
    d.polygon(poly, fill=edge + (255,))
    # inner surface, slightly narrower
    inner_l, inner_r = [], []
    for (lx, ly), (rx, ry) in zip(left, right):
        cx, cy = (lx + rx) / 2, (ly + ry) / 2
        inner_l.append((cx + (lx - cx) * 0.82, cy + (ly - cy) * 0.82))
        inner_r.append((cx + (rx - cx) * 0.82, cy + (ry - cy) * 0.82))
    d.polygon(inner_l + inner_r[::-1], fill=fill + (255,))
    random.seed(iid)
    if style == 'asphalt':
        pts = [((l[0] + r[0]) / 2, (l[1] + r[1]) / 2) for l, r in zip(left, right)]
        for i in range(0, len(pts) - 3, 6):
            d.line([pts[i], pts[i + 3]], fill=(240, 200, 60, 255), width=int(1.6 * S))
    else:
        for _ in range(70):
            i = random.randrange(0, len(inner_l))
            k = random.random()
            x = inner_l[i][0] * k + inner_r[i][0] * (1 - k)
            y = inner_l[i][1] * k + inner_r[i][1] * (1 - k)
            r = random.uniform(0.8, 1.8) * S
            shade = random.choice([-22, -10, 14, 26])
            c = tuple(max(0, min(255, v + shade)) for v in fill) + (255,)
            if style == 'stone':
                d.rectangle([x - r * 1.6, y - r, x + r * 1.6, y + r], fill=c, outline=edge + (255,))
            else:
                d.ellipse([x - r, y - r, x + r, y + r], fill=c)
    im = im.resize((128, 128), Image.LANCZOS)
    # keep inside the margin and make the border transparent
    bbox = im.getbbox()
    if bbox:
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        scale = min(1.0, 104 / max(w, h))
        crop = im.crop(bbox)
        if scale < 1.0:
            crop = crop.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.LANCZOS)
        out = Image.new('RGBA', (128, 128), (0, 0, 0, 0))
        out.paste(crop, ((128 - crop.width) // 2, (128 - crop.height) // 2), crop)
        im = out
    return im


for iid in ITEMS:
    folder = os.path.join(ROOT, 'assets', 'building', iid)
    draw(iid).save(os.path.join(folder, iid + '.png'))
    print(iid, 'ok')
