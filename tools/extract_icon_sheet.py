"""
Cuts a Gemini contact sheet (items on a flat dark slate background) into standardized 128 px item icons.

    python tools/extract_icon_sheet.py <sheet.png> <dest_folder_pattern> <id> <id> ...
    e.g. python tools/extract_icon_sheet.py assets/_scratch/muffins/sheet1.png "assets/food/{id}/{id}.png" food_cornbread food_corn_muffin ...

The ids are in reading order (rows top to bottom, left to right). The background is removed by flood fill from the border (colour of the corners, with a tolerance), the items are the
connected blobs left, and the count must match the ids. Output goes through regen_icons.standardize_icon_image.
"""
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import regen_icons  # noqa: E402


def main():
    sheet, pattern, ids = sys.argv[1], sys.argv[2], sys.argv[3:]
    im = Image.open(sheet).convert('RGB')
    a = np.asarray(im).astype(np.int32)
    bg = np.median(np.concatenate([a[:6, :6].reshape(-1, 3), a[:6, -6:].reshape(-1, 3), a[-6:, :6].reshape(-1, 3), a[-6:, -6:].reshape(-1, 3)]), axis=0)
    dist = np.sqrt(((a - bg) ** 2).sum(-1))
    # background = what the flood fill reaches from the border through near-background pixels (a global threshold would eat dark parts of the items, such as navy cups)
    near = dist < 9
    reach, _ = ndimage.label(near)
    border = set(np.unique(np.concatenate([reach[0], reach[-1], reach[:, 0], reach[:, -1]]))) - {0}
    bgmask = np.isin(reach, list(border))
    fg = ~bgmask
    fg = ndimage.binary_opening(fg, iterations=2)       # drops the soft halo and noise specks
    fg = ndimage.binary_fill_holes(fg)
    lab, n = ndimage.label(fg)
    sizes = ndimage.sum(fg, lab, range(1, n + 1))
    keep = [i + 1 for i, s in enumerate(sizes) if s > 0.004 * fg.size]
    if len(keep) != len(ids):
        print('FOUND %d items, expected %d' % (len(keep), len(ids)))
        sys.exit(1)
    boxes = []
    for i in keep:
        ys, xs = np.where(lab == i)
        boxes.append((i, ys.mean(), xs.mean(), ys.min(), ys.max(), xs.min(), xs.max()))
    # rows: cluster by y centre
    boxes.sort(key=lambda b: b[1])
    rows, cur = [], [boxes[0]]
    for b in boxes[1:]:
        if b[1] - np.mean([c[1] for c in cur]) > 0.5 * (cur[0][4] - cur[0][3]):
            rows.append(cur)
            cur = [b]
        else:
            cur.append(b)
    rows.append(cur)
    ordered = [b for r in rows for b in sorted(r, key=lambda b: b[2])]
    rgba = np.dstack([np.asarray(im), np.zeros(fg.shape, np.uint8)])
    for (i, _, _, y0, y1, x0, x1), iid in zip(ordered, ids):
        mask = (lab == i)
        mask = ndimage.binary_erosion(mask, iterations=2)
        out = rgba.copy()
        out[..., 3] = (mask * 255).astype(np.uint8)
        crop = Image.fromarray(out[max(0, y0 - 4):y1 + 5, max(0, x0 - 4):x1 + 5], 'RGBA')
        dest = pattern.replace('{id}', iid)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        raw = dest + '.raw.png'
        crop.save(raw)
        ok, msg = regen_icons.standardize_icon_image(raw, dest)
        os.remove(raw)
        print(ok, iid, msg)


if __name__ == '__main__':
    main()
