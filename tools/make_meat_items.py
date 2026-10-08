"""
Writes the meat cuts as icon-only items (no model): 8 raw cuts in assets/ingredients/ and their 8 cooked versions in assets/food/.
Each raw cut points at its cooked item (next_item_id), so the processing chain is complete. Icons come from ICON_DIR (128 px, rendered from Gemini sheets).

    python tools/make_meat_items.py <icon_dir>
Afterwards: python tools/generate_unity_asset_catalog.py ; python tools/package_catalog_as_mods.py ; python tools/update_catalog_readme.py
"""
import json
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, 'assets')

# raw id, raw name, raw kg, raw price, raw dims (w, d, h), raw description, method, cooked id, cooked name, cooked description, cooked dims, hunger, price
CUTS = [
    ('ingredient_steak', 'Ribeye Steak', 0.34, 16, (0.2, 0.17, 0.03), 'A raw beef ribeye steak with a rim of fat.', 'grill',
     'food_steak_grilled', 'Grilled Ribeye Steak', 'A ribeye steak grilled with dark char marks.', (0.2, 0.17, 0.03), 35, 24),
    ('ingredient_ground_beef', 'Ground Beef', 0.45, 11, (0.12, 0.12, 0.04), 'Raw ground beef, ready to form into patties.', 'grill',
     'food_ground_beef_grilled', 'Grilled Burger Patty', 'A ground beef patty grilled with char marks.', (0.12, 0.12, 0.03), 25, 15),
    ('ingredient_pork_chop', 'Bone-In Pork Chop', 0.25, 9, (0.16, 0.18, 0.03), 'A raw bone-in pork chop.', 'grill',
     'food_pork_chop_grilled', 'Grilled Bone-In Pork Chop', 'A bone-in pork chop grilled with char marks.', (0.16, 0.18, 0.03), 28, 15),
    ('ingredient_bacon', 'Bacon', 0.45, 12, (0.15, 0.2, 0.02), 'Raw sliced bacon, ready to fry.', 'cook',
     'food_bacon_cooked', 'Crispy Bacon', 'Bacon strips fried crisp.', (0.15, 0.2, 0.01), 18, 15),
    ('ingredient_sausage', 'Pork Sausage', 0.45, 10, (0.12, 0.2, 0.04), 'Raw pork sausage links.', 'grill',
     'food_sausage_grilled', 'Grilled Sausage', 'Pork sausage links grilled until browned.', (0.12, 0.2, 0.04), 28, 14),
    ('ingredient_ham', 'Whole Ham', 3.0, 28, (0.3, 0.2, 0.18), 'A whole raw cured ham with the bone in.', 'bake',
     'food_ham_baked', 'Baked Ham', 'A whole ham baked with a golden glaze.', (0.3, 0.2, 0.18), 70, 42),
    ('ingredient_lamb_chop', 'Lamb Rib Chop', 0.2, 12, (0.1, 0.22, 0.03), 'A raw lamb rib chop with a frenched bone.', 'grill',
     'food_lamb_chop_grilled', 'Grilled Lamb Chop', 'A lamb rib chop grilled with char marks.', (0.1, 0.22, 0.03), 26, 18),
    ('ingredient_goat_meat', 'Goat Leg', 0.9, 16, (0.2, 0.25, 0.14), 'A raw bone-in goat leg.', 'bake',
     'food_goat_meat_baked', 'Roast Goat Leg', 'A goat leg roasted until deeply browned.', (0.2, 0.25, 0.14), 55, 26),
]
ICON_OF = {c[0]: c[0] for c in CUTS}
ICON_OF.update({c[7]: c[7] for c in CUTS})
RAW_ICON_SRC = {'ingredient_steak': 'ingredient_steak', 'ingredient_ground_beef': 'ingredient_ground_beef', 'ingredient_pork_chop': 'ingredient_pork_chop',
                'ingredient_bacon': 'ingredient_bacon', 'ingredient_sausage': 'ingredient_sausage', 'ingredient_ham': 'ingredient_ham',
                'ingredient_lamb_chop': 'ingredient_lamb_chop', 'ingredient_goat_meat': 'ingredient_goat_meat'}
UTIL = {
    'water': {'metric': 'None (unplumbed / dry)', 'details': 'None (unplumbed / dry)'},
    'electricity': {'metric': 'None (passive / unpowered)', 'details': 'None (passive / unpowered)'},
    'sewage': {'metric': 'None (no waste discharge)', 'details': 'None (no waste discharge)'},
    'battery': {'metric': 'None (no internal battery)', 'details': 'None (no internal battery)'},
    'internet': {'metric': 'None (offline / non-networked)', 'details': 'None (offline / non-networked)'},
}
GROWTH = {'is_growable': False, 'growth_type': None, 'species': None, 'max_age': None, 'time_unit': None, 'total_stages': 0, 'current_stage': None, 'stages': []}
NL = chr(10)


def manifest(item, category, name, desc, kg, price, dims, fields, props_extra):
    props = {'weight_kg': kg, 'max_stack_size': 99, 'base_value': price, 'is_consumable': False, 'footprint': None,
             'happiness_modifier': 0, 'thirst_restore': 0, 'energy_restore': 0, 'stamina_restore': 0, 'wellness_modifier': 0,
             'is_buyable': True, 'stores': ['grocer'], 'sale_unit': 'ea'}
    props.update(props_extra)
    w, d, h = dims
    cf = dict(fields)
    cf['dimensions_m'] = {'width': w, 'depth': d, 'height': h}
    return {'$schema': 'https://homesteader.game/schemas/item_v1.json', 'id': item, 'name': name, 'category': category, 'description': desc,
            'icon': item + '.png', 'properties': props, 'models': [], 'utilities': UTIL, 'growth': GROWTH,
            'plugin_metadata': {'version': '1.0.0', 'author': 'Homesteader Core', 'compatible_api': 'v1'}, 'category_fields': cf}


def write(item, category, m, icon_dir, icon_id):
    folder = os.path.join(ASSETS, category, item)
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, item + '.json'), 'w', encoding='utf-8', newline=NL) as f:
        json.dump(m, f, indent=2, ensure_ascii=False)
        f.write(NL)
    with open(os.path.join(folder, 'README.md'), 'w', encoding='utf-8', newline=NL) as f:
        f.write('# %s' % m['name'] + NL + NL + m['description'] + NL + NL + 'Icon-only item (no 3D model), written by tools/make_meat_items.py.' + NL)
    shutil.copyfile(os.path.join(icon_dir, icon_id + '.png'), os.path.join(folder, item + '.png'))
    print('wrote', category, item)


if __name__ == '__main__':
    icon_dir = sys.argv[1]
    for raw, rname, rkg, rprice, rdims, rdesc, method, cooked, cname, cdesc, cdims, hunger, cprice in CUTS:
        write(raw, 'ingredients', manifest(raw, 'ingredients', rname, rdesc, rkg, rprice, rdims, {'processing_method': method, 'next_item_id': cooked}, {}), icon_dir, raw)
        write(cooked, 'food', manifest(cooked, 'food', cname, cdesc, rkg, cprice, cdims, {'hunger_restore': hunger},
                                       {'happiness_modifier': 10, 'thirst_restore': 2, 'stamina_restore': hunger, 'wellness_modifier': 2}), icon_dir, cooked)
