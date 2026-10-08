"""
Paints the icons of the extra dishes in tools/dish_extra.py (assets/_scratch/dishes/out5/<id>.png, picked up by tools/make_dishes_more.py). Free and local (PIL): a dish on the same
plate as the pasta icons (make_dish_items.plate), or in the same bowl as the soups (make_dish_items.bowl) with chunks of food on the broth.

    python tools/make_more_dish_icons.py [food_id ...]
Afterwards: python tools/make_dishes_more.py <ids> ; python tools/make_meals.py ; python tools/generate_unity_asset_catalog.py ; python tools/package_catalog_as_mods.py
"""
import os
import random
import sys

from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import make_dish_items as M  # noqa: E402
import make_pasta_bread_icons as P  # noqa: E402
import regen_icons  # noqa: E402

OUT = os.path.join(ROOT, 'assets', '_scratch', 'dishes', 'out5')
shade = M.shade


def lighter(c, k=0.25):
    return tuple(min(255, int(v + (255 - v) * k)) for v in c)


def blob(d, cx, cy, rx, ry, col, depth=8):
    d.ellipse((cx - rx, cy - ry + depth, cx + rx, cy + ry + depth), fill=shade(col, 0.68))
    d.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=col)
    d.ellipse((cx - rx * 0.62, cy - ry * 0.72, cx - rx * 0.1, cy - ry * 0.3), fill=lighter(col))


def rr(d, x0, y0, x1, y1, col, r=14, depth=8):
    d.rounded_rectangle((x0, y0 + depth, x1, y1 + depth), radius=r, fill=shade(col, 0.68))
    d.rounded_rectangle((x0, y0, x1, y1), radius=r, fill=col)


def speck(d, rnd, col, n, size, cx, cy, rx, ry):
    for _ in range(n):
        x, y = rnd.randint(int(cx - rx), int(cx + rx)), rnd.randint(int(cy - ry), int(cy + ry))
        if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1.0:
            r = max(2, size + rnd.randint(-1, 2))
            d.ellipse((x - r, y - r * 0.7, x + r, y + r * 0.7), fill=col)


def tube(d, x0, y0, x1, y1, w, col):
    for dy, c in ((6, shade(col, 0.68)), (0, col)):
        d.line((x0, y0 + dy, x1, y1 + dy), fill=c, width=w)
        for x, y in ((x0, y0 + dy), (x1, y1 + dy)):
            d.ellipse((x - w / 2, y - w / 2, x + w / 2, y + w / 2), fill=c)


def slice_of(d, cx, cy, rx, ry, col, inner):
    d.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=col)
    d.ellipse((cx - rx * 0.78, cy - ry * 0.74, cx + rx * 0.78, cy + ry * 0.74), fill=inner)


BREAD, CRUST = (232, 192, 120), (176, 118, 58)
GREEN, RED, CREAM, GOLD, BROWN = (96, 160, 64), (206, 56, 40), (246, 236, 208), (222, 160, 64), (120, 70, 42)


def sandwich(d, rnd, layers, bun=False):
    """A side view stack on the plate: a bottom slice, the layers (colour, height), a domed top."""
    d.ellipse((60, 360, 452, 440), fill=shade(M.WHITE, 0.8))
    d.ellipse((60, 340, 452, 424), fill=M.WHITE)
    d.ellipse((60, 340, 452, 424), outline=M.RIM, width=8)
    y = 360
    rr(d, 130, y - 22, 382, y + 12, CRUST if not bun else (214, 150, 70), r=14, depth=6)
    y -= 22
    for col, h in layers:
        if col == GREEN:
            for x in range(124, 388, 30):
                d.ellipse((x, y - h - 4, x + 44, y + 6), fill=col)
        else:
            rr(d, 124, y - h, 388, y, col, r=8, depth=3)
        y -= h
    top = (214, 150, 70) if bun else BREAD
    d.pieslice((130, y - 70, 382, y + 40), 180, 360, fill=shade(top, 0.78))
    d.pieslice((136, y - 66, 376, y + 34), 180, 360, fill=top)
    if bun:
        speck(d, rnd, (250, 240, 220), 16, 3, 256, y - 24, 100, 24)


def sauce_bowl(broth, chunks):
    def extras(d, rnd):
        for col, n, size in chunks:
            M.dots(d, rnd, shade(col, 0.82), n, size + 2)
            M.dots(d, random.Random(n * 7 + size), col, n, size)
    return extras


def tray(d):
    P.empty_plate(d)


# ---------------------------------------------------------------------------- the plate dishes: each draws on an empty plate

def omelet(d, r):
    blob(d, 256, 336, 150, 60, (250, 214, 90))
    d.arc((120, 290, 392, 380), 200, 340, fill=shade((250, 214, 90), 0.7), width=6)
    speck(d, r, (96, 160, 64), 14, 4, 256, 330, 110, 36)
    speck(d, r, (255, 240, 180), 8, 5, 256, 330, 100, 32)


def quiche(d, r):
    d.polygon([(256, 270), (416, 360), (300, 410), (150, 370)], fill=shade(GOLD, 0.8))
    d.polygon([(256, 280), (396, 360), (300, 396), (166, 366)], fill=(252, 226, 120))
    speck(d, r, RED, 12, 5, 290, 350, 90, 30)
    speck(d, r, GREEN, 8, 3, 290, 350, 90, 30)
    d.line((150, 370, 256, 270), fill=GOLD, width=10)


def deviled(d, r):
    for cx, cy in ((190, 310), (320, 310), (190, 370), (320, 370)):
        d.ellipse((cx - 56, cy - 36, cx + 56, cy + 36), fill=(248, 246, 238))
        d.ellipse((cx - 56, cy - 36, cx + 56, cy + 36), outline=(214, 208, 190), width=3)
        d.ellipse((cx - 28, cy - 18, cx + 28, cy + 18), fill=(248, 200, 60))
        d.ellipse((cx - 6, cy - 4, cx + 6, cy + 4), fill=(206, 90, 40))


def blt(d, r):
    sandwich(d, r, [((190, 80, 60), 10), (RED, 14), (GREEN, 12), ((190, 80, 60), 10)])


def grilled_cheese(d, r):
    for pts, off in (([(120, 380), (300, 290), (330, 380)], 0), ([(200, 400), (380, 300), (410, 390)], 0)):
        d.polygon(pts, fill=shade(GOLD, 0.7))
        inner = [(pts[0][0] + 12, pts[0][1] - 6), (pts[1][0] - 2, pts[1][1] + 14), (pts[2][0] - 14, pts[2][1] - 6)]
        d.polygon(inner, fill=(214, 150, 70))
        d.line([pts[0], pts[2]], fill=(252, 214, 70), width=14)


def ham_sandwich(d, r):
    sandwich(d, r, [((238, 150, 150), 12), ((252, 220, 80), 8), (GREEN, 12)])


def fish_sandwich(d, r):
    sandwich(d, r, [((222, 160, 64), 24), (GREEN, 12)], bun=True)


def fried_chicken(d, r):
    for cx, cy, a in ((180, 330, 0), (300, 310, 0), (330, 380, 0)):
        blob(d, cx, cy, 78, 44, (200, 130, 50))
        speck(d, r, (150, 90, 36), 22, 5, cx, cy, 64, 30)
        d.ellipse((cx + 56, cy - 14, cx + 100, cy + 12), fill=(240, 228, 206))


def pork_apples(d, r):
    blob(d, 220, 330, 100, 58, (196, 140, 96))
    for k in range(4):
        d.line((150 + k * 34, 300, 170 + k * 34, 370), fill=shade((196, 140, 96), 0.6), width=7)
    for cx, cy in ((340, 310), (370, 350), (330, 380)):
        d.pieslice((cx - 40, cy - 40, cx + 40, cy + 40), 200, 340, fill=RED)
        d.pieslice((cx - 30, cy - 30, cx + 30, cy + 30), 200, 340, fill=(250, 238, 190))


def roast(meat, a, b):
    def f(d, r):
        blob(d, 240, 330, 110, 62, meat)
        speck(d, r, shade(meat, 0.7), 24, 6, 240, 330, 90, 40)
        for cx, cy in a:
            blob(d, cx, cy, 34, 24, (240, 214, 150), depth=5)
        for x0, y0, x1, y1 in b:
            tube(d, x0, y0, x1, y1, 22, (240, 130, 30))
        speck(d, r, (80, 150, 60), 14, 4, 250, 330, 140, 50)
    return f


def salmon(d, r):
    blob(d, 250, 330, 140, 56, (244, 140, 100))
    for k in range(5):
        d.arc((130 + k * 46, 296, 190 + k * 46, 360), 200, 340, fill=(252, 190, 160), width=6)
    d.ellipse((330, 330, 400, 380), fill=(250, 224, 70))
    d.ellipse((340, 340, 390, 370), fill=(255, 244, 150))
    speck(d, r, GREEN, 12, 4, 230, 330, 100, 30)


def biscuits(d, r):
    for cx, cy in ((190, 320), (320, 320), (256, 380)):
        blob(d, cx, cy, 62, 40, (236, 190, 110))
        d.ellipse((cx - 44, cy - 28, cx + 44, cy + 6), fill=(244, 206, 130))


def waffles(d, r):
    rr(d, 150, 280, 360, 400, (226, 170, 80), r=18)
    for k in range(1, 5):
        d.line((150 + k * 42, 284, 150 + k * 42, 396), fill=shade((226, 170, 80), 0.7), width=5)
        d.line((154, 280 + k * 24, 356, 280 + k * 24), fill=shade((226, 170, 80), 0.7), width=5)
    rr(d, 220, 310, 290, 350, (255, 236, 120), r=8, depth=5)
    d.ellipse((290, 340, 420, 400), fill=(150, 80, 30))


def hash_browns(d, r):
    for x0, y0 in ((130, 290), (250, 300), (190, 350)):
        rr(d, x0, y0, x0 + 124, y0 + 50, (214, 150, 60), r=18)
        speck(d, r, (150, 90, 36), 16, 4, x0 + 62, y0 + 25, 52, 18)


def sausage_eggs(d, r):
    tube(d, 130, 310, 290, 330, 34, (150, 80, 50))
    tube(d, 130, 365, 290, 385, 34, (150, 80, 50))
    for cx, cy in ((350, 320), (350, 380)):
        blob(d, cx, cy, 60, 36, (252, 250, 244))
        d.ellipse((cx - 22, cy - 14, cx + 22, cy + 14), fill=(250, 190, 40))


def gravy(d, r):
    for cx, cy in ((180, 340), (330, 340)):
        blob(d, cx, cy, 70, 44, (236, 190, 110))
    blob(d, 256, 336, 150, 56, (240, 230, 206))
    speck(d, r, (60, 56, 52), 40, 3, 256, 336, 130, 40)
    speck(d, r, (150, 80, 50), 12, 5, 256, 336, 110, 34)


def fries(d, r):
    for k in range(13):
        x = 150 + k * 16
        tube(d, x, 310 + (k % 3) * 8, x + 12, 380, 18, (244, 200, 80))
    blob(d, 400, 380, 30, 20, (200, 40, 36), depth=4)


def corn(d, r):
    for y in (310, 370):
        tube(d, 140, y, 360, y, 46, (250, 214, 70))
        for x in range(150, 350, 22):
            d.line((x, y - 18, x, y + 22), fill=(226, 170, 40), width=3)
        d.ellipse((330, y - 24, 392, y + 24), fill=(120, 170, 70))
    rr(d, 220, 330, 280, 352, (255, 240, 130), r=6, depth=4)


def bean_casserole(d, r):
    blob(d, 256, 336, 150, 60, (236, 224, 190))
    for k in range(16):
        x, y = r.randint(150, 360), r.randint(300, 370)
        d.line((x, y, x + r.randint(20, 50), y + r.randint(-14, 14)), fill=(80, 150, 60), width=7)
    speck(d, r, (190, 120, 50), 40, 4, 256, 336, 130, 44)


def beets(d, r):
    for k in range(9):
        x, y = 150 + (k % 3) * 80 + r.randint(-8, 8), 296 + (k // 3) * 36
        rr(d, x, y, x + 60, y + 34, (150, 30, 70), r=8, depth=5)
    speck(d, r, GREEN, 14, 4, 256, 336, 130, 50)


def broccoli_cheese(d, r):
    blob(d, 256, 340, 140, 50, (252, 210, 70))
    for cx, cy in ((190, 320), (256, 300), (320, 320), (230, 350), (300, 352)):
        d.rectangle((cx - 8, cy, cx + 8, cy + 40), fill=(120, 170, 80))
        blob(d, cx, cy, 38, 28, (60, 140, 50), depth=4)


def pilaf(d, r):
    blob(d, 256, 336, 140, 56, (222, 190, 120))
    speck(d, r, (186, 140, 70), 50, 4, 256, 336, 120, 40)
    speck(d, r, (240, 130, 30), 12, 4, 256, 336, 110, 36)
    speck(d, r, GREEN, 12, 3, 256, 336, 110, 36)


def cobbler(fruit, inner):
    def f(d, r):
        rr(d, 130, 280, 382, 400, (200, 140, 70), r=30)
        d.rounded_rectangle((146, 290, 366, 384), radius=24, fill=shade(fruit, 0.8))
        for k in range(7):
            x, y = 160 + (k % 4) * 54, 300 + (k // 4) * 50
            d.pieslice((x, y, x + 70, y + 54), 180, 360, fill=fruit)
            d.pieslice((x + 8, y + 8, x + 62, y + 50), 180, 360, fill=inner)
        for cx, cy in ((200, 330), (300, 340), (250, 360)):
            blob(d, cx, cy, 40, 26, (226, 170, 80), depth=4)
    return f


def flax_bread(d, r):
    rr(d, 130, 290, 382, 380, (160, 100, 50), r=40)
    d.rounded_rectangle((146, 296, 366, 340), radius=30, fill=(190, 130, 66))
    speck(d, r, (70, 40, 20), 40, 3, 256, 320, 100, 18)
    for x in (200, 256, 312):
        d.line((x, 300, x - 8, 372), fill=(120, 70, 30), width=4)


def brownies(d, r):
    for x0, y0 in ((140, 290), (250, 296), (190, 346), (300, 350)):
        rr(d, x0, y0, x0 + 96, y0 + 52, (96, 52, 30), r=10)
        d.rounded_rectangle((x0 + 8, y0 + 6, x0 + 88, y0 + 22), radius=6, fill=(126, 76, 46))
        speck(d, r, (60, 32, 18), 6, 3, x0 + 48, y0 + 28, 36, 14)


def truffle_pasta(d, r):
    M.plate(d, (246, 222, 150), None, lambda d, rr_: [d.polygon([(x, y), (x + 20, y + 6), (x + 8, y + 16)], fill=(40, 30, 28)) for x, y in [(rr_.randint(190, 330), rr_.randint(260, 340)) for _ in range(16)]])


# ---------------------------------------------------------------------------- the table

PLATE = {
    'food_omelet': omelet, 'food_quiche': quiche, 'food_deviled_eggs': deviled, 'food_blt': blt, 'food_grilled_cheese': grilled_cheese,
    'food_ham_sandwich': ham_sandwich, 'food_fish_sandwich': fish_sandwich, 'food_fried_chicken': fried_chicken, 'food_pork_chops_apples': pork_apples,
    'food_lamb_roast': roast((120, 70, 44), [(380, 320), (390, 380)], [(120, 390, 190, 350)]),
    'food_goat_roast': roast((136, 86, 56), [(130, 330), (150, 392)], [(330, 300, 400, 340), (340, 370, 410, 400)]),
    'food_baked_salmon': salmon, 'food_biscuits': biscuits, 'food_waffles': waffles, 'food_hash_browns': hash_browns, 'food_sausage_and_eggs': sausage_eggs,
    'food_biscuits_gravy': gravy, 'food_french_fries': fries, 'food_corn_on_the_cob': corn, 'food_green_bean_casserole': bean_casserole, 'food_roasted_beets': beets,
    'food_broccoli_and_cheese': broccoli_cheese, 'food_cracked_wheat_pilaf': pilaf,
    'food_peach_cobbler': cobbler((246, 150, 60), (252, 200, 120)), 'food_apple_cobbler': cobbler((206, 70, 50), (250, 236, 190)),
    'food_flax_bread': flax_bread, 'food_truffle_pasta': truffle_pasta, 'food_brownies': brownies,
}
CREAMY, TOM = (240, 224, 170), (200, 80, 48)
BOWL = {   # broth colour, chunks (colour, count, size)
    'food_egg_salad': ((246, 226, 150), [((252, 250, 240), 10, 12), ((250, 200, 60), 6, 8), (GREEN, 6, 4)]),
    'food_ham_and_beans': ((176, 104, 54), [((238, 150, 150), 7, 12), ((236, 214, 170), 10, 8), (CREAM, 5, 8)]),
    'food_apple_porridge': ((232, 214, 176), [(RED, 6, 9), ((250, 240, 200), 6, 8), ((120, 70, 42), 6, 4)]),
    'food_broccoli_cheese_soup': ((236, 204, 96), [((60, 140, 50), 10, 8), ((252, 226, 120), 5, 6)]),
    'food_borscht': ((166, 30, 62), [(CREAM, 4, 9), (GREEN, 8, 4), ((220, 90, 100), 6, 8)]),
    'food_beef_chili': ((142, 52, 32), [(BROWN, 9, 10), ((180, 40, 40), 8, 8), (GREEN, 5, 5)]),
    'food_veggie_chili': ((172, 64, 34), [((236, 214, 170), 9, 9), (GREEN, 6, 8), (RED, 6, 8)]),
    'food_potato_salad': (CREAMY, [((246, 238, 206), 10, 11), ((250, 206, 70), 6, 8), (GREEN, 6, 4)]),
    'food_cucumber_salad': ((200, 230, 170), [((110, 170, 80), 10, 11), ((250, 250, 240), 8, 8)]),
    'food_caesar_salad': ((118, 176, 80), [((226, 176, 100), 9, 9), ((250, 248, 236), 6, 7), ((70, 130, 50), 8, 10)]),
    'food_fruit_salad': ((246, 214, 150), [(RED, 7, 9), ((250, 150, 40), 7, 9), ((140, 190, 70), 6, 8), ((120, 50, 110), 6, 7)]),
    'food_ice_cream': ((250, 238, 212), [((255, 252, 240), 8, 14), ((246, 200, 210), 5, 10), ((140, 90, 60), 6, 4)]),
    'food_chocolate_pudding': ((92, 52, 34), [((130, 82, 56), 8, 12), ((60, 32, 20), 8, 6), ((250, 240, 220), 3, 8)]),
    'food_custard': ((252, 232, 150), [((200, 150, 70), 10, 3), ((255, 244, 190), 5, 10)]),
    'food_strawberry_gelatin': ((222, 44, 74), [((250, 120, 140), 6, 10), ((255, 210, 220), 4, 9), (RED, 6, 7)]),
}
IDS = list(PLATE) + list(BOWL)


def paint(iid):
    im = Image.new('RGBA', (M.S, M.S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    rnd = random.Random(sum(map(ord, iid)))
    if iid in PLATE:
        if iid in ('food_blt', 'food_ham_sandwich', 'food_fish_sandwich', 'food_grilled_cheese') or iid == 'food_truffle_pasta':
            if iid != 'food_grilled_cheese' and iid != 'food_truffle_pasta':
                PLATE[iid](d, rnd)
            else:
                tray(d) if iid == 'food_grilled_cheese' else None
                PLATE[iid](d, rnd)
        else:
            tray(d)
            PLATE[iid](d, rnd)
    else:
        broth, chunks = BOWL[iid]
        M.bowl(d, broth, sauce_bowl(broth, chunks))
    return im.filter(ImageFilter.GaussianBlur(0.8))


if __name__ == '__main__':
    only = sys.argv[1:] or IDS
    os.makedirs(OUT, exist_ok=True)
    sheet = Image.new('RGBA', (128 * 10, 128 * ((len(only) + 9) // 10)), (30, 30, 40, 255))
    for k, iid in enumerate(only):
        raw = os.path.join(OUT, iid + '_raw.png')
        paint(iid).save(raw)
        ok, msg = regen_icons.standardize_icon_image(raw, os.path.join(OUT, iid + '.png'))
        os.remove(raw)
        sheet.alpha_composite(Image.open(os.path.join(OUT, iid + '.png')).convert('RGBA'), ((k % 10) * 128, (k // 10) * 128))
    sheet.save(os.path.join(ROOT, 'assets', '_scratch', 'dishes', 'more_sheet.png'))
    print('painted', len(only))
