"""
Writes the DISH items (assets/food/): breakfasts, mains, sides, salads and desserts from the table in tools/dish_data.py. Icon-only foods; the icons are cut from Gemini sheets
(tools/extract_icon_sheet.py) into assets/_scratch/dishes/out1 ... out4. The meals come from the same table (tools/make_meals.py).

    python tools/make_dishes_more.py [food_id ...]
Afterwards: python tools/make_meals.py ; python tools/generate_unity_asset_catalog.py ; python tools/package_catalog_as_mods.py
"""
import copy
import json
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import dish_data  # noqa: E402

FOOD = os.path.join(ROOT, 'assets', 'food')
ICONS = os.path.join(ROOT, 'assets', '_scratch', 'dishes')
NL = chr(10)

if __name__ == '__main__':
    with open(os.path.join(FOOD, 'food_bread', 'food_bread.json'), encoding='utf-8') as f:
        base = json.load(f)
    only = sys.argv[1:]   # ids: write only those (the others are left as they are)
    for d in dish_data.DISHES:
        iid = d['id']
        if only and iid not in only:
            continue
        m = copy.deepcopy(base)
        m['id'], m['name'], m['description'], m['icon'] = iid, d['name'], d['desc'], iid + '.png'
        m['properties'].update({'weight_kg': d['kg'], 'max_stack_size': 10, 'base_value': d['price'], 'happiness_modifier': d['happy'], 'thirst_restore': 0, 'stamina_restore': d['stamina'],
                                'wellness_modifier': 1, 'is_buyable': False, 'sale_unit': 'ea'})
        m['properties'].pop('stores', None)
        if d['bowl']:
            m['properties']['leaves_item'] = 'kitchen_bowl'   # eaten: the bowl is left (Kitchen/Consumption.cs)
        else:
            m['properties'].pop('leaves_item', None)
        size = (0.2, 0.2, 0.08) if d['bowl'] else (0.26, 0.26, 0.06)
        m['models'] = []
        m['category_fields'] = {'hunger_restore': d['hunger'], 'dimensions_m': {'width': size[0], 'depth': size[1], 'height': size[2]}}
        folder = os.path.join(FOOD, iid)
        os.makedirs(folder, exist_ok=True)
        with open(os.path.join(folder, iid + '.json'), 'w', encoding='utf-8', newline=NL) as f:
            json.dump(m, f, indent=2, ensure_ascii=False)
            f.write(NL)
        with open(os.path.join(folder, 'README.md'), 'w', encoding='utf-8', newline=NL) as f:
            f.write('# %s' % d['name'] + NL + NL + d['desc'] + NL + NL + 'Icon-only item (no 3D model), written by tools/make_dishes_more.py from tools/dish_data.py.' + NL)
        src = [os.path.join(ICONS, 'out%d' % n, iid + '.png') for n in range(1, 6)]
        shutil.copyfile([s for s in src if os.path.exists(s)][0], os.path.join(folder, iid + '.png'))
        print('wrote', iid)
