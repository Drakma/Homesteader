"""
Writes the QUICK BREADS (assets/food/): Cornbread, Corn Muffin, Muffin, Blueberry Muffin. Icon-only foods; the icons are cut from Gemini sheets (tools/extract_icon_sheet.py). The baking
meals are in tools/make_meals.py (BAKING): they need an oven or a range (the `#appliance_oven` tag holds ovens, toaster ovens, wood cookstoves and ranges).

    python tools/make_muffin_items.py
Afterwards: python tools/make_meals.py ; python tools/generate_unity_asset_catalog.py ; python tools/package_catalog_as_mods.py
"""
import copy
import json
import os
import sys

import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FOOD = os.path.join(ROOT, 'assets', 'food')
NL = chr(10)

# id, name, description, size, kg, price, hunger, stamina, happiness
ITEMS = [
    ('food_cornbread', 'Cornbread', 'A golden square of baked cornbread, crumbly and a little sweet.', (0.12, 0.12, 0.05), 0.2, 6, 16, 16, 8),
    ('food_corn_muffin', 'Corn Muffin', 'A small golden corn muffin with a domed top.', (0.07, 0.07, 0.065), 0.1, 4, 10, 10, 6),
    ('food_muffin', 'Muffin', 'A plain baked muffin in a paper cup.', (0.07, 0.07, 0.07), 0.1, 4, 10, 10, 6),
    ('food_blueberry_muffin', 'Blueberry Muffin', 'A baked muffin dotted with blueberries.', (0.07, 0.07, 0.07), 0.11, 5, 11, 11, 9),
]
FRUITS = [('blueberry', 'Blueberry', 'blueberries'), ('strawberry', 'Strawberry', 'strawberry pieces'), ('raspberry', 'Raspberry', 'raspberries'), ('cherry', 'Cherry', 'cherries'),
          ('apple', 'Apple', 'apple'), ('peach', 'Peach', 'peach'), ('pear', 'Pear', 'pear'), ('apricot', 'Apricot', 'apricot'), ('plum', 'Plum', 'plum'), ('fig', 'Fig', 'fig'),
          ('huckleberry', 'Huckleberry', 'huckleberries'), ('elderberry', 'Elderberry', 'elderberries'), ('haskap', 'Haskap', 'haskap berries'), ('lemon', 'Lemon', 'lemon'),
          ('orange', 'Orange', 'orange'), ('rhubarb', 'Rhubarb', 'rhubarb')]
ITEMS = [i for i in ITEMS if i[0] != 'food_blueberry_muffin']
for _k, _n, _w in FRUITS:
    ITEMS.append(('food_%s_muffin' % _k, '%s Muffin' % _n, 'A baked muffin with %s.' % _w, (0.07, 0.07, 0.07), 0.11, 5, 11, 11, 9))
ICONS = os.path.join(ROOT, 'assets', '_scratch', 'muffins')   # the icons are cut from the Gemini sheets by tools/extract_icon_sheet.py into out/, out2/, out3/


if __name__ == '__main__':
    with open(os.path.join(FOOD, 'food_bread', 'food_bread.json'), encoding='utf-8') as f:
        base = json.load(f)
    for iid, name, desc, (w, dp, h), kg, price, hunger, stamina, happy in ITEMS:
        m = copy.deepcopy(base)
        m['id'], m['name'], m['description'], m['icon'] = iid, name, desc, iid + '.png'
        m['properties'].update({'weight_kg': kg, 'max_stack_size': 20, 'base_value': price, 'happiness_modifier': happy, 'thirst_restore': 0, 'stamina_restore': stamina,
                                'wellness_modifier': 1, 'is_buyable': True, 'stores': ['grocer'], 'sale_unit': 'ea'})
        m['models'] = []
        m['category_fields'] = {'hunger_restore': hunger, 'dimensions_m': {'width': w, 'depth': dp, 'height': h}}
        folder = os.path.join(FOOD, iid)
        os.makedirs(folder, exist_ok=True)
        with open(os.path.join(folder, iid + '.json'), 'w', encoding='utf-8', newline=NL) as f:
            json.dump(m, f, indent=2, ensure_ascii=False)
            f.write(NL)
        with open(os.path.join(folder, 'README.md'), 'w', encoding='utf-8', newline=NL) as f:
            f.write('# %s' % name + NL + NL + desc + NL + NL + 'Icon-only item (no 3D model), written by tools/make_muffin_items.py.' + NL)
        src = [os.path.join(ICONS, d, iid + '.png') for d in ('out', 'out2', 'out3')]
        src = [s for s in src if os.path.exists(s)][0]
        shutil.copyfile(src, os.path.join(folder, iid + '.png'))
        print('wrote', iid)
