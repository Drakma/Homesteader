"""
Writes the BUNS and what goes in them (assets/food/): the Burger Bun and the Hot Dog Bun (baked in the oven), and the Hamburger and the Hot Dog (a bun round a grilled patty / sausage, put together
on the counter with no appliance). Icon-only foods (no model). The meals are in tools/make_meals.py.

    python tools/make_bun_items.py <icon_dir>        (food_burger_bun.png, food_hot_dog_bun.png, food_burger.png, food_hot_dog.png: 128 px)
Afterwards: python tools/make_meals.py ; python tools/generate_unity_asset_catalog.py ; python tools/package_catalog_as_mods.py
"""
import copy
import json
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FOOD = os.path.join(ROOT, 'assets', 'food')
NL = chr(10)

# id, name, description, size, weight kg, price, hunger, stamina, happiness
BUNS = [
    ('food_burger_bun', 'Burger Bun', 'A soft sesame-seed bun for a burger patty.', (0.11, 0.11, 0.07), 0.08, 3, 8, 8, 4),
    ('food_hot_dog_bun', 'Hot Dog Bun', 'A long soft bun for a sausage.', (0.07, 0.19, 0.06), 0.06, 3, 8, 8, 4),
    ('food_burger', 'Hamburger', 'A grilled beef patty in a sesame-seed bun.', (0.11, 0.11, 0.1), 0.25, 10, 40, 30, 12),
    ('food_hot_dog', 'Hot Dog', 'A grilled sausage in a soft bun.', (0.07, 0.19, 0.07), 0.15, 7, 28, 22, 10),
]

if __name__ == '__main__':
    icon_dir = sys.argv[1]
    with open(os.path.join(FOOD, 'food_bread', 'food_bread.json'), encoding='utf-8') as f:
        base = json.load(f)
    for iid, name, desc, (w, d, h), kg, price, hunger, stamina, happy in BUNS:
        m = copy.deepcopy(base)
        m['id'], m['name'], m['description'], m['icon'] = iid, name, desc, iid + '.png'
        m['properties'].update({'weight_kg': kg, 'max_stack_size': 20, 'base_value': price, 'happiness_modifier': happy, 'thirst_restore': 0, 'stamina_restore': stamina,
                                'wellness_modifier': 1, 'is_buyable': True, 'stores': ['grocer'], 'sale_unit': 'ea'})
        m['models'] = []
        m['category_fields'] = {'hunger_restore': hunger, 'dimensions_m': {'width': w, 'depth': d, 'height': h}}
        folder = os.path.join(FOOD, iid)
        os.makedirs(folder, exist_ok=True)
        with open(os.path.join(folder, iid + '.json'), 'w', encoding='utf-8', newline=NL) as f:
            json.dump(m, f, indent=2, ensure_ascii=False)
            f.write(NL)
        with open(os.path.join(folder, 'README.md'), 'w', encoding='utf-8', newline=NL) as f:
            f.write('# %s' % name + NL + NL + desc + NL + NL + 'Icon-only item (no 3D model), written by tools/make_bun_items.py.' + NL)
        shutil.copyfile(os.path.join(icon_dir, iid + '.png'), os.path.join(folder, iid + '.png'))
        print('wrote', iid)
