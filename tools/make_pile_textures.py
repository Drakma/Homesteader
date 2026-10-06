#!/usr/bin/env python3
"""
Procedural seamless textures for the bulk material piles (sand, gravel, dirt, mulch, bedding stone, manure), 512 x 512, written to assets/_scratch/pile_tex/.
tools/make_pile_models.py embeds them in the pile GLBs. Plain python (numpy + PIL), no Blender.

    python tools/make_pile_textures.py
"""
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'assets', '_scratch', 'pile_tex')
N = 512


def rng(seed):
    return np.random.default_rng(seed)


def tile_wrap(points, n):
    """The points repeated in the 8 neighbouring tiles, so cell patterns are seamless."""
    out = []
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            out.append(points + np.array([dx * n, dy * n]))
    return np.concatenate(out)


def voronoi(seed, cells, palette, border=0.0, jitter=0.12):
    """A Voronoi mosaic (seamless): each cell its own colour from the palette with a little variation, dark thin borders."""
    r = rng(seed)
    pts = r.random((cells, 2)) * N
    cols = np.array([palette[r.integers(len(palette))] for _ in range(cells)], dtype=float)
    cols *= (1.0 + (r.random((cells, 1)) - 0.5) * jitter * 2)
    allp = tile_wrap(pts, N)
    allc = np.tile(cols, (9, 1))
    ys, xs = np.mgrid[0:N, 0:N]
    grid = np.stack([xs.ravel(), ys.ravel()], axis=1).astype(float)
    # nearest and second nearest point: the gap tells the border
    best = np.full(len(grid), 1e9)
    second = np.full(len(grid), 1e9)
    idx = np.zeros(len(grid), dtype=int)
    for i, p in enumerate(allp):
        d = np.hypot(grid[:, 0] - p[0], grid[:, 1] - p[1])
        closer = d < best
        second = np.where(closer, best, np.minimum(second, d))
        idx = np.where(closer, i, idx)
        best = np.where(closer, d, best)
    img = allc[idx].reshape(N, N, 3)
    gap = (second - best).reshape(N, N)
    if border > 0:
        shade = np.clip(gap / border, 0.0, 1.0)[..., None]
        img = img * (0.35 + 0.65 * shade)
    # rounded shading: darker towards the cell edge
    shade2 = np.clip(1.0 - best.reshape(N, N) / (N / np.sqrt(cells) * 0.9), 0.4, 1.0)[..., None]
    return img * (0.75 + 0.25 * shade2)


def noise(seed, scale):
    """Seamless value noise at a given feature size (pixels)."""
    r = rng(seed)
    g = max(2, N // scale)
    base = r.random((g, g))
    im = Image.fromarray((base * 255).astype(np.uint8)).resize((N, N), Image.BICUBIC)
    return np.asarray(im, dtype=float) / 255.0


def finish(img, seed, grain=0.06):
    r = rng(seed + 99)
    img = img + (r.random((N, N, 1)) - 0.5) * grain * 255 * 2 * 0.5
    return np.clip(img, 0, 255).astype(np.uint8)


def sand():
    base = np.array([205, 180, 128], dtype=float)
    img = np.ones((N, N, 3)) * base
    img *= (0.88 + 0.24 * noise(1, 64))[..., None]
    img *= (0.94 + 0.12 * noise(2, 8))[..., None]
    r = rng(3)
    for _ in range(2500):                      # darker and lighter grains
        x, y = r.integers(0, N, 2)
        v = r.choice([0.78, 1.12])
        img[y, x] *= v
    return finish(img, 3, 0.10)


def gravel():
    img = voronoi(11, 520, [(150, 148, 142), (120, 118, 114), (176, 170, 160), (96, 94, 92), (160, 140, 120)], border=3.5)
    img *= (0.92 + 0.16 * noise(12, 32))[..., None]
    return finish(img, 11, 0.08)


def dirt():
    img = np.ones((N, N, 3)) * np.array([92, 66, 46], dtype=float)
    img *= (0.70 + 0.55 * noise(21, 48))[..., None]
    clumps = voronoi(22, 140, [(88, 62, 42), (70, 48, 32), (104, 76, 54)], border=1.2)
    img = img * 0.45 + clumps * 0.55
    img *= (0.92 + 0.16 * noise(23, 6))[..., None]
    return finish(img, 21, 0.12)


def mulch():
    base = Image.new('RGB', (N, N), (62, 40, 24))
    d = ImageDraw.Draw(base)
    r = rng(31)
    palette = [(86, 54, 30), (110, 70, 38), (70, 44, 26), (128, 86, 48), (54, 34, 20)]
    for _ in range(2600):                      # wood chips: short thick strokes, every direction, wrapped at the edges
        x, y = r.random(2) * N
        a = r.random() * np.pi
        ln = 10 + r.random() * 22
        w = 3 + int(r.random() * 4)
        col = palette[r.integers(len(palette))]
        for ox in (-N, 0, N):
            for oy in (-N, 0, N):
                d.line([(x + ox, y + oy), (x + ox + np.cos(a) * ln, y + oy + np.sin(a) * ln)], fill=col, width=w)
    img = np.asarray(base, dtype=float)
    img *= (0.85 + 0.3 * noise(32, 24))[..., None]
    return finish(img, 31, 0.08)


def bedding_stone():
    img = voronoi(41, 230, [(168, 170, 176), (140, 142, 150), (190, 188, 184), (120, 124, 132), (176, 168, 156)], border=4.0, jitter=0.10)
    img *= (0.92 + 0.16 * noise(42, 40))[..., None]
    return finish(img, 41, 0.07)


def manure():
    img = np.ones((N, N, 3)) * np.array([72, 54, 36], dtype=float)
    img *= (0.65 + 0.7 * noise(51, 40))[..., None]
    clumps = voronoi(52, 90, [(78, 58, 38), (58, 42, 28), (92, 70, 44)], border=1.5, jitter=0.15)
    img = img * 0.4 + clumps * 0.6
    base = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(base)
    r = rng(53)
    for _ in range(900):                       # straw fibres
        x, y = r.random(2) * N
        a = r.random() * np.pi
        ln = 8 + r.random() * 18
        col = (130 + int(r.random() * 40), 104 + int(r.random() * 30), 60)
        for ox in (-N, 0, N):
            for oy in (-N, 0, N):
                d.line([(x + ox, y + oy), (x + ox + np.cos(a) * ln, y + oy + np.sin(a) * ln)], fill=col, width=1)
    return finish(np.asarray(base, dtype=float), 51, 0.08)


TEXTURES = {'sand': sand, 'gravel': gravel, 'dirt': dirt, 'mulch': mulch, 'bedding_stone': bedding_stone, 'manure': manure}

if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    for name, fn in TEXTURES.items():
        img = Image.fromarray(fn())
        img.save(os.path.join(OUT, name + '.png'))
        print('texture', name)
