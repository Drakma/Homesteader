"""
Paints the extra STEW icons (assets/_scratch/dishes/out5/<id>.png, picked up by tools/make_dishes_more.py): the same bowl as the soups (make_dish_items.bowl) with chunks of meat and vegetables.

    python tools/make_stew_icons.py
Afterwards: python tools/make_dishes_more.py <ids> ; python tools/make_meals.py ; python tools/generate_unity_asset_catalog.py ; python tools/package_catalog_as_mods.py
"""
import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import make_dish_items as M  # noqa: E402
import regen_icons  # noqa: E402

OUT = os.path.join(ROOT, 'assets', '_scratch', 'dishes', 'out5')
MEAT, CARROT, POTATO, GREEN, RED = (112, 66, 42), (240, 130, 30), (236, 214, 150), (80, 150, 60), (200, 50, 40)

# id: (broth colour, [(chunk colour, count, size)])
STEWS = {
    'food_lamb_stew': ((176, 104, 60), [(MEAT, 7, 14), (CARROT, 6, 10), (POTATO, 7, 11)]),
    'food_goat_stew': ((186, 84, 50), [((120, 62, 40), 6, 14), (RED, 5, 9), (CARROT, 5, 10), (POTATO, 5, 11)]),
    'food_pork_stew': ((196, 130, 70), [((214, 160, 130), 7, 14), (GREEN, 8, 7), (POTATO, 7, 11)]),
    'food_sausage_stew': ((204, 92, 52), [((150, 80, 56), 7, 13), (RED, 5, 10), ((230, 190, 60), 5, 8), (POTATO, 5, 11)]),
    'food_fish_stew': ((222, 118, 58), [((246, 236, 220), 7, 14), (RED, 5, 9), (POTATO, 5, 11), (GREEN, 4, 5)]),
    'food_vegetable_stew': ((210, 112, 56), [(CARROT, 7, 11), (POTATO, 7, 11), (GREEN, 8, 6), (RED, 5, 9)]),
}


def paint(iid):
    from PIL import Image, ImageDraw, ImageFilter
    broth, chunks = STEWS[iid]
    im = Image.new('RGBA', (M.S, M.S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)

    def extras(d, rnd):
        for colour, n, size in chunks:
            M.dots(d, rnd, M.shade(colour, 0.85), n, size + 2)
            M.dots(d, random.Random(n * 7 + size), colour, n, size)
    M.bowl(d, broth, extras)
    return im.filter(ImageFilter.GaussianBlur(0.8))


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    for iid in STEWS:
        raw = os.path.join(OUT, iid + '_raw.png')
        paint(iid).save(raw)
        print(regen_icons.standardize_icon_image(raw, os.path.join(OUT, iid + '.png')), iid)
        os.remove(raw)
