"""
Writes the SOUPS and PASTA DISHES (assets/food/): icon-only foods, the icons painted here with PIL (free, local). Soups are served in a Soup Bowl (kitchen_bowl, an ingredient of the soup meal);
pasta dishes go on a plate like any food. The meals are in tools/make_meals.py (DISHES).

    python tools/make_dish_items.py
Afterwards: python tools/make_meals.py ; python tools/generate_unity_asset_catalog.py ; python tools/package_catalog_as_mods.py
"""
import copy
import json
import os
import random
import sys

from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import regen_icons  # noqa: E402

FOOD = os.path.join(ROOT, 'assets', 'food')
NL = chr(10)
S = 512

# id, name, description, kg, price, hunger, stamina, happiness
SOUPS = [
    ('food_tomato_soup', 'Tomato Soup', 'A bowl of smooth tomato soup with a little basil.', 0.45, 7, 20, 18, 9),
    ('food_vegetable_soup', 'Vegetable Soup', 'A bowl of broth full of potato, carrot, green beans and tomato.', 0.5, 8, 24, 22, 8),
    ('food_chicken_noodle_soup', 'Chicken Noodle Soup', 'A bowl of chicken broth with noodles, carrot and onion.', 0.5, 9, 28, 24, 11),
    ('food_potato_soup', 'Potato Soup', 'A thick, creamy potato soup topped with bacon.', 0.5, 9, 28, 24, 11),
    ('food_beef_barley_soup', 'Beef Barley Soup', 'A hearty bowl of beef, pearl barley and vegetables.', 0.5, 10, 30, 26, 11),
    ('food_pumpkin_soup', 'Pumpkin Soup', 'A smooth, sweet pumpkin soup with a swirl of butter.', 0.45, 8, 22, 20, 10),
]
PASTAS = [
    ('food_spaghetti', 'Spaghetti Marinara', 'Spaghetti in a marinara sauce of tomato and herbs.', 0.35, 8, 28, 22, 9),
    ('food_spaghetti_meatballs', 'Spaghetti and Meatballs', 'Spaghetti and sauce with beef meatballs.', 0.45, 11, 38, 30, 13),
    ('food_sausage_pasta', 'Sausage Pasta', 'Spaghetti in tomato sauce with sliced sausage.', 0.45, 10, 36, 28, 12),
    ('food_buttered_noodles', 'Buttered Noodles', 'Plain spaghetti tossed in butter and salt.', 0.3, 5, 22, 18, 7),
    ('food_mac_and_cheese', 'Macaroni and Cheese', 'Pasta in a rich cheese sauce.', 0.4, 9, 32, 24, 14),
]
WHITE, RIM = (244, 244, 240), (46, 90, 184)


def shade(c, k):
    return tuple(max(0, min(255, int(v * k))) for v in c)


def bowl(d, broth, extras):
    # the body is the lower half of a tall ellipse that starts at the rim ellipse's centre line, so the bowl is one piece under the rim
    d.ellipse((190, 380, 322, 428), fill=shade(WHITE, 0.7))   # the foot
    d.pieslice((70, -10, 442, 410), 0, 180, fill=shade(WHITE, 0.9))
    d.pieslice((70, -10, 442, 410), 25, 155, fill=WHITE)
    d.ellipse((70, 120, 442, 280), fill=WHITE)
    d.ellipse((74, 124, 438, 276), outline=RIM, width=9)
    d.ellipse((96, 140, 416, 262), fill=shade(broth, 0.8))
    d.ellipse((104, 146, 408, 252), fill=broth)
    extras(d, random.Random(7))
    d.ellipse((130, 152, 260, 190), fill=tuple(min(255, c + 26) for c in broth))


def dots(d, rnd, colour, n, size):
    for _ in range(n):
        x, y = rnd.randint(120, 390), rnd.randint(160, 244)
        if ((x - 256) / 150.0) ** 2 + ((y - 198) / 52.0) ** 2 < 1.0:
            r = size + rnd.randint(-2, 3)
            d.ellipse((x - r, y - r * 0.7, x + r, y + r * 0.7), fill=colour)


def noodles(d, rnd, colour, n):
    for _ in range(n):
        x, y = rnd.randint(140, 360), rnd.randint(170, 232)
        d.arc((x, y, x + 50, y + 22), rnd.randint(0, 180), rnd.randint(200, 360), fill=colour, width=5)


def soup(d, iid):
    if iid == 'food_tomato_soup':
        def e(d, r):
            dots(d, r, (70, 140, 52), 9, 7)
            d.ellipse((236, 176, 276, 200), fill=(246, 236, 220))
        bowl(d, (214, 70, 44), e)
    elif iid == 'food_vegetable_soup':
        def e(d, r):
            dots(d, r, (240, 130, 30), 9, 10)
            dots(d, r, (240, 214, 130), 6, 9)
            dots(d, r, (80, 150, 60), 8, 6)
            dots(d, r, (200, 50, 40), 4, 9)
        bowl(d, (214, 150, 62), e)
    elif iid == 'food_chicken_noodle_soup':
        def e(d, r):
            noodles(d, r, (250, 230, 150), 14)
            dots(d, r, (240, 130, 30), 5, 9)
            dots(d, r, (236, 226, 200), 5, 11)
        bowl(d, (232, 186, 80), e)
    elif iid == 'food_potato_soup':
        def e(d, r):
            dots(d, r, (196, 90, 70), 7, 8)
            dots(d, r, (80, 150, 60), 8, 4)
        bowl(d, (240, 226, 190), e)
    elif iid == 'food_beef_barley_soup':
        def e(d, r):
            dots(d, r, (124, 70, 46), 6, 12)
            dots(d, r, (226, 206, 150), 14, 6)
            dots(d, r, (240, 130, 30), 4, 8)
        bowl(d, (150, 96, 56), e)
    else:
        def e(d, r):
            d.arc((190, 168, 330, 238), 20, 330, fill=(250, 230, 160), width=9)
        bowl(d, (236, 140, 40), e)


def plate(d, pile, sauce=None, top=None):
    d.ellipse((50, 238, 462, 448), fill=shade(WHITE, 0.8))   # the plate's edge: thin
    d.ellipse((50, 230, 462, 440), fill=WHITE)
    d.ellipse((50, 230, 462, 440), outline=RIM, width=8)
    d.ellipse((96, 262, 416, 410), fill=shade(WHITE, 0.92))
    rnd = random.Random(3)
    d.ellipse((150, 240, 362, 380), fill=shade(pile, 0.85))
    for _ in range(46):
        x, y = rnd.randint(150, 330), rnd.randint(250, 350)
        d.arc((x, y, x + 66, y + 40), rnd.randint(0, 120), rnd.randint(200, 360), fill=pile, width=8)
    if sauce:
        d.ellipse((176, 226, 336, 320), fill=shade(sauce, 0.85))
        d.ellipse((184, 230, 328, 306), fill=sauce)
    if top:
        top(d, rnd)


def pasta(d, iid):
    yellow = (240, 206, 110)
    red = (206, 56, 40)
    if iid == 'food_spaghetti':
        def t(d, r):
            for x, y in ((230, 250), (270, 262), (250, 282)):
                d.ellipse((x, y, x + 14, y + 8), fill=(70, 140, 52))
        plate(d, yellow, red, t)
    elif iid == 'food_spaghetti_meatballs':
        def t(d, r):
            for x, y in ((214, 262), (262, 250), (300, 276), (246, 292)):
                d.ellipse((x - 26, y - 24, x + 26, y + 24), fill=(120, 66, 40))
                d.ellipse((x - 16, y - 18, x - 2, y - 8), fill=(160, 100, 70))
        plate(d, yellow, red, t)
    elif iid == 'food_sausage_pasta':
        def t(d, r):
            for x, y in ((210, 258), (250, 248), (294, 266), (236, 290), (284, 296)):
                d.ellipse((x - 24, y - 16, x + 24, y + 16), fill=(150, 80, 56))
                d.ellipse((x - 14, y - 9, x + 14, y + 9), fill=(186, 112, 80))
        plate(d, yellow, red, t)
    elif iid == 'food_buttered_noodles':
        plate(d, (246, 222, 140), None, lambda d, r: d.polygon([(236, 268), (282, 258), (292, 288), (246, 298)], fill=(255, 236, 90)))
    else:
        def t(d, r):
            for _ in range(20):
                x, y = r.randint(170, 340), r.randint(250, 340)
                d.arc((x, y, x + 34, y + 30), 30, 330, fill=(246, 168, 40), width=11)
        plate(d, (250, 170, 50), None, t)


def paint(iid):
    im = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    (soup if iid in [s[0] for s in SOUPS] else pasta)(d, iid)
    return im.filter(ImageFilter.GaussianBlur(0.8))


if __name__ == '__main__':
    with open(os.path.join(FOOD, 'food_bread', 'food_bread.json'), encoding='utf-8') as f:
        base = json.load(f)
    for group, size in ((SOUPS, (0.2, 0.2, 0.1)), (PASTAS, (0.26, 0.26, 0.05))):
        for iid, name, desc, kg, price, hunger, stamina, happy in group:
            m = copy.deepcopy(base)
            m['id'], m['name'], m['description'], m['icon'] = iid, name, desc, iid + '.png'
            m['properties'].update({'weight_kg': kg, 'max_stack_size': 10, 'base_value': price, 'happiness_modifier': happy, 'thirst_restore': 0, 'stamina_restore': stamina,
                                    'wellness_modifier': 1, 'is_buyable': False, 'sale_unit': 'ea'})
            m['properties'].pop('stores', None)
            if iid in [s[0] for s in SOUPS]:
                m['properties']['leaves_item'] = 'kitchen_bowl'   # eaten: the bowl is left (Kitchen/Consumption.cs)
            m['models'] = []
            m['category_fields'] = {'hunger_restore': hunger, 'dimensions_m': {'width': size[0], 'depth': size[1], 'height': size[2]}}
            folder = os.path.join(FOOD, iid)
            os.makedirs(folder, exist_ok=True)
            with open(os.path.join(folder, iid + '.json'), 'w', encoding='utf-8', newline=NL) as f:
                json.dump(m, f, indent=2, ensure_ascii=False)
                f.write(NL)
            with open(os.path.join(folder, 'README.md'), 'w', encoding='utf-8', newline=NL) as f:
                f.write('# %s' % name + NL + NL + desc + NL + NL + 'Icon-only item (no 3D model), written by tools/make_dish_items.py.' + NL)
            raw = os.path.join(folder, iid + '_raw.png')
            paint(iid).save(raw)
            ok, msg = regen_icons.standardize_icon_image(raw, os.path.join(folder, iid + '.png'))
            os.remove(raw)
            print(ok, iid)
