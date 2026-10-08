"""
Paints the icons of the extra PASTA and BREAD dishes (assets/_scratch/dishes/out5/<id>.png, picked up by tools/make_dishes_more.py): spaghetti on the same plate as the other pasta dishes
(make_dish_items.plate), breadsticks and garlic bread on a plate.

    python tools/make_pasta_bread_icons.py
Afterwards: python tools/make_dishes_more.py <ids> ; python tools/make_meals.py ; python tools/generate_unity_asset_catalog.py ; python tools/package_catalog_as_mods.py
"""
import os
import random
import sys

from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import make_dish_items as M  # noqa: E402
import regen_icons  # noqa: E402

OUT = os.path.join(ROOT, 'assets', '_scratch', 'dishes', 'out5')
YELLOW = (240, 206, 110)


def empty_plate(d):
    d.ellipse((50, 238, 462, 448), fill=M.shade(M.WHITE, 0.8))
    d.ellipse((50, 230, 462, 440), fill=M.WHITE)
    d.ellipse((50, 230, 462, 440), outline=M.RIM, width=8)
    d.ellipse((96, 262, 416, 410), fill=M.shade(M.WHITE, 0.92))


def stick(d, x0, y0, x1, y1, w, crust, crumb):
    """A rounded bread stick from (x0, y0) to (x1, y1): a darker underside, then the golden top."""
    for dy, col in ((6, M.shade(crust, 0.7)), (0, crust)):
        d.line((x0, y0 + dy, x1, y1 + dy), fill=col, width=w)
        for x, y in ((x0, y0 + dy), (x1, y1 + dy)):
            d.ellipse((x - w / 2, y - w / 2, x + w / 2, y + w / 2), fill=col)
    d.line((x0 + 4, y0 - w // 5, x1 - 4, y1 - w // 5), fill=crumb, width=max(4, w // 4))


def sauce_dish(iid, d):
    rnd = random.Random(11)
    if iid == 'food_spaghetti_meat_sauce':
        def t(d, r):
            for _ in range(22):
                x, y = r.randint(190, 330), r.randint(238, 300)
                d.ellipse((x, y, x + 20, y + 14), fill=(96, 50, 34))
        M.plate(d, YELLOW, (176, 58, 38), t)
    elif iid == 'food_spaghetti_alfredo':
        def t(d, r):
            for _ in range(12):
                x, y = r.randint(200, 320), r.randint(240, 290)
                d.ellipse((x, y, x + 8, y + 6), fill=(80, 150, 60))
        M.plate(d, (246, 226, 170), (252, 242, 214), t)
    else:   # cacio e pepe: no sauce, a dusting of pepper and cheese
        def t(d, r):
            for _ in range(60):
                x, y = r.randint(170, 350), r.randint(250, 350)
                d.ellipse((x, y, x + 5, y + 4), fill=(30, 28, 26))
            for _ in range(10):
                x, y = r.randint(180, 330), r.randint(250, 340)
                d.polygon([(x, y), (x + 22, y + 4), (x + 8, y + 14)], fill=(255, 244, 200))
        M.plate(d, (246, 222, 140), None, t)


def bread_dish(iid, d):
    rnd = random.Random(5)
    empty_plate(d)
    golden, crumb = (214, 150, 70), (236, 190, 110)
    if iid == 'food_breadsticks':
        for i, (x0, y0, x1, y1) in enumerate(((130, 340, 350, 280), (140, 320, 370, 262), (150, 300, 388, 248), (130, 360, 330, 308))):
            stick(d, x0, y0, x1, y1, 40, golden, crumb)
        for _ in range(26):
            x, y = rnd.randint(150, 360), rnd.randint(270, 340)
            d.ellipse((x, y, x + 5, y + 4), fill=(250, 246, 236))
    else:
        for x, y, ang in ((150, 300, 0), (230, 280, 0), (310, 270, 0)):
            d.rounded_rectangle((x, y - 16, x + 120, y + 100), radius=26, fill=M.shade(golden, 0.75))   # the crust
            d.rounded_rectangle((x + 6, y - 10, x + 114, y + 88), radius=22, fill=(255, 232, 150))        # garlic butter
            for _ in range(14):
                gx, gy = rnd.randint(x + 12, x + 100), rnd.randint(y, y + 76)
                d.ellipse((gx, gy, gx + 8, gy + 5), fill=(80, 150, 60))
            for _ in range(6):
                gx, gy = rnd.randint(x + 14, x + 98), rnd.randint(y + 4, y + 74)
                d.ellipse((gx, gy, gx + 9, gy + 7), fill=(250, 244, 220))


IDS = ['food_spaghetti_meat_sauce', 'food_spaghetti_alfredo', 'food_cacio_e_pepe', 'food_breadsticks', 'food_garlic_bread']


def paint(iid):
    im = Image.new('RGBA', (M.S, M.S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    (sauce_dish if 'bread' not in iid else bread_dish)(iid, d)
    return im.filter(ImageFilter.GaussianBlur(0.8))


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    for iid in IDS:
        raw = os.path.join(OUT, iid + '_raw.png')
        paint(iid).save(raw)
        print(regen_icons.standardize_icon_image(raw, os.path.join(OUT, iid + '.png')), iid)
        os.remove(raw)
