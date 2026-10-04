#!/usr/bin/env python3
"""
Splits the seed packet sheet and the harvest sheet (Downloads/seeds.jpg, harvest.jpg) into one 128x128 RGBA icon per item.

    python tools/split_crop_sheets.py

Writes assets/_scratch/crop_icons_final/seed_<crop>.png and harvest_<crop>.png (tools/build_crop_groups.py copies them into the seed and harvest
items). Icons follow the Homesteader icon standard: 128x128, transparent border, largest side 104 px.
"""
import os

import cv2
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'assets', '_scratch', 'crop_icons_final')
DL = os.path.join(os.path.expanduser('~'), 'Downloads')

# seeds.jpg: a 4 x 4 grid, row by row (the last four cells are a repeated broccoli and three blanks: not used)
SEEDS = ['onion', 'garlic', 'lettuce', 'cabbage', 'peas', 'green_beans', 'cucumber', 'zucchini', 'peppers', 'radish', 'beet', 'broccoli']

# harvest.jpg (2814 x 1536): item centres in the 2000 px wide preview, scaled by 1.407
SCALE = 2814 / 2000.0
HARVEST = {
    'onion': (500, 335), 'garlic': (760, 330), 'cabbage': (1245, 320),
    'lettuce': (510, 515), 'peas': (770, 540), 'green_beans': (1000, 520), 'cucumber': (1245, 535), 'zucchini': (1505, 530),
    'peppers': (440, 735), 'radish': (790, 740), 'beet': (1020, 730), 'broccoli': (1250, 735), 'spinach': (1500, 740),
}


def to_icon(rgb, mask, path):
    """Crops to the mask, scales the longest side to 104 px, centres on a transparent 128 x 128 canvas."""
    ys, xs = np.where(mask > 0)
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    rgba = np.dstack([rgb, mask])[y0:y1, x0:x1]
    im = Image.fromarray(rgba.astype(np.uint8), 'RGBA')
    k = 104.0 / max(im.size)
    im = im.resize((max(1, round(im.width * k)), max(1, round(im.height * k))), Image.LANCZOS)
    canvas = Image.new('RGBA', (128, 128), (0, 0, 0, 0))
    canvas.alpha_composite(im, ((128 - im.width) // 2, (128 - im.height) // 2))
    canvas.save(path)


def seed_mask(cell):
    """A packet on pure white: everything that is not (nearly) white, holes filled, the largest piece."""
    diff = 255 - cell.min(axis=2)
    m = (diff > 10).astype(np.uint8) * 255
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(m)
    if n > 1:
        big = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
        m = (lab == big).astype(np.uint8) * 255
    cnts, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    out = np.zeros_like(m)
    cv2.drawContours(out, cnts, -1, 255, -1)
    return cv2.GaussianBlur(out, (3, 3), 0)


def grabcut_mask(img, cx, cy, half, paper_v=212, paper_s=26):
    h, w = img.shape[:2]
    x0, y0, x1, y1 = max(0, cx - half), max(0, cy - half), min(w, cx + half), min(h, cy + half)
    crop = img[y0:y1, x0:x1].copy()
    mask = np.zeros(crop.shape[:2], np.uint8)
    rect = (8, 8, crop.shape[1] - 16, crop.shape[0] - 16)
    bgd = np.zeros((1, 65), np.float64)
    fgd = np.zeros((1, 65), np.float64)
    cv2.grabCut(crop, mask, rect, bgd, fgd, 2, cv2.GC_INIT_WITH_RECT)
    # the white sheet and its soft shadow (bright, almost grey) are background for sure; the item is what is left
    hsv = cv2.cvtColor(crop, cv2.COLOR_RGB2HSV)
    sheet = (hsv[..., 1] < paper_s) & (hsv[..., 2] > paper_v)
    mask[sheet] = cv2.GC_BGD
    cv2.grabCut(crop, mask, None, bgd, fgd, 5, cv2.GC_INIT_WITH_MASK)
    m = np.where((mask == 1) | (mask == 3), 255, 0).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    # the white sheet the items stand on: flood it from the corners of the crop (a fixed, tight range around its own colour) and take it out
    paper = np.zeros((crop.shape[0] + 2, crop.shape[1] + 2), np.uint8)
    for sx, sy in ((2, 2), (crop.shape[1] - 3, 2), (2, crop.shape[0] - 3), (crop.shape[1] - 3, crop.shape[0] - 3)):
        cv2.floodFill(crop.copy(), paper, (sx, sy), 0, (9, 9, 9), (9, 9, 9), cv2.FLOODFILL_MASK_ONLY | cv2.FLOODFILL_FIXED_RANGE | (255 << 8))
    m[paper[1:-1, 1:-1] > 0] = 0
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(m)
    if n > 1:
        # keep the pieces that matter (a pepper pair, a radish and its leaves): everything over 8 percent of the biggest
        areas = stats[1:, cv2.CC_STAT_AREA]
        keep = [1 + i for i, a in enumerate(areas) if a >= 0.08 * areas.max()]
        m = np.isin(lab, keep).astype(np.uint8) * 255
    return crop, cv2.GaussianBlur(m, (3, 3), 0)


WHITE_PARTS = {'garlic', 'onion', 'radish'}   # items with white parts: a stricter idea of what counts as the sheet   # items that stand out from the white sheet by colour; GrabCut leaves paper on these


def colour_mask(img, cx, cy, half):
    h, w = img.shape[:2]
    x0, y0, x1, y1 = max(0, cx - half), max(0, cy - half), min(w, cx + half), min(h, cy + half)
    crop = img[y0:y1, x0:x1].copy()
    hsv = cv2.cvtColor(crop, cv2.COLOR_RGB2HSV)
    m = (((hsv[..., 1] > 34) | (hsv[..., 2] < 205)) * 255).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((11, 11), np.uint8))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(m)
    if n > 1:
        areas = stats[1:, cv2.CC_STAT_AREA]
        keep = [1 + i for i, a in enumerate(areas) if a >= 0.08 * areas.max()]
        m = np.isin(lab, keep).astype(np.uint8) * 255
    cnts, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    out = np.zeros_like(m)
    cv2.drawContours(out, cnts, -1, 255, -1)
    return crop, cv2.GaussianBlur(out, (3, 3), 0)


def main():
    os.makedirs(OUT, exist_ok=True)
    seeds = cv2.cvtColor(cv2.imread(os.path.join(DL, 'seeds.jpg')), cv2.COLOR_BGR2RGB)
    cell = seeds.shape[0] // 4
    for i, crop in enumerate(SEEDS):
        r, c = divmod(i, 4)
        part = seeds[r * cell:(r + 1) * cell, c * cell:(c + 1) * cell]
        to_icon(part, seed_mask(part), os.path.join(OUT, 'seed_%s.png' % crop))
    # a later sheet of the same packets whose last cell is the spinach packet
    extra = os.path.join(DL, 'Gemini_Generated_Image_y435wpy435wpy435.jpg')
    if os.path.exists(extra):
        more = cv2.cvtColor(cv2.imread(extra), cv2.COLOR_BGR2RGB)
        part = more[3 * cell:4 * cell, 3 * cell:4 * cell]
        to_icon(part, seed_mask(part), os.path.join(OUT, 'seed_spinach.png'))
    # the sheet of the remaining packets: a 4 x 4 grid, row by row
    more2 = os.path.join(DL, 'Gemini_Generated_Image_cfug1hcfug1hcfug.jpg')
    if os.path.exists(more2):
        sheet2 = cv2.cvtColor(cv2.imread(more2), cv2.COLOR_BGR2RGB)
        for i, crop in enumerate(['rhubarb', 'hops', 'tobacco', 'flax', 'alfalfa', 'oats', 'barley', 'soybeans', 'peanuts', 'watermelon', 'cantaloupe']):
            r, c = divmod(i, 4)
            part = sheet2[r * cell:(r + 1) * cell, c * cell:(c + 1) * cell]
            to_icon(part, seed_mask(part), os.path.join(OUT, 'seed_%s.png' % crop))
    harvest = cv2.cvtColor(cv2.imread(os.path.join(DL, 'harvest.jpg')), cv2.COLOR_BGR2RGB)
    for crop, (x, y) in HARVEST.items():
        if crop == 'peppers':
            rgb, m = colour_mask(harvest, int((x + 45) * SCALE), int(y * SCALE), 260)      # the red and the yellow pepper stand out by colour
        elif crop in WHITE_PARTS:
            rgb, m = grabcut_mask(harvest, int(x * SCALE), int(y * SCALE), 190, 236, 8)
        else:
            rgb, m = grabcut_mask(harvest, int(x * SCALE), int(y * SCALE), 190)
        to_icon(rgb, m, os.path.join(OUT, 'harvest_%s.png' % crop))
    # the second harvest sheet (generated here, assets/_scratch/harvest2.png, 709 x 388): item centres in its own pixels
    h2 = os.path.join(ROOT, 'assets', '_scratch', 'harvest2.png')
    if os.path.exists(h2):
        img2 = cv2.cvtColor(cv2.imread(h2), cv2.COLOR_BGR2RGB)
        for crop, (x, y) in {'rhubarb': (172, 85), 'hops': (298, 90), 'tobacco': (428, 88), 'flax': (548, 85), 'alfalfa': (162, 182), 'oats': (298, 180),
                             'barley': (428, 182), 'soybeans': (550, 185), 'peanuts': (160, 282), 'watermelon': (322, 285), 'cantaloupe': (485, 285)}.items():
            rgb, m = grabcut_mask(img2, x, y, 62, 238, 7) if crop in ('flax', 'oats', 'barley') else grabcut_mask(img2, x, y, 62)
            if crop == 'oats' and os.path.exists(os.path.join(OUT, 'harvest_oats.png')):
                continue       # regenerated on grey and segmented by hand
            to_icon(rgb, m, os.path.join(OUT, 'harvest_%s.png' % crop))
    print('wrote', len(os.listdir(OUT)), 'icons to', OUT)


if __name__ == '__main__':
    main()
