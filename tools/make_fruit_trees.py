"""
Writes the kit side of the extra FRUIT and NUT TREES: for each species a growth group (assets/logging/<tree>/), a plantable sapling and an icon-only fruit item
(assets/food/food_<fruit>/). The trees themselves are built in code (Assets/Scripts/World/ProceduralVegetation.cs, one `Species` line each); the kit group supplies
the rules (what picks the fruit, the drops, when it ripens, where it can be planted, what felling gives). Stage models are procedural, so the stages name no files.

    python tools/make_fruit_trees.py <fruit_icon_dir>           (food_<fruit>.png, 128 px, from the Gemini sheet)
Afterwards: python tools/generate_unity_asset_catalog.py ; python tools/package_catalog_as_mods.py ; python tools/update_catalog_readme.py
Tree icons (assets/logging/<tree>/<tree>.png) are rendered from the procedural tree in Unity (ForestTrees.MakeIconProxy); until then a placeholder is copied.
"""
import copy
import json
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGGING = os.path.join(ROOT, 'assets', 'logging')
FOOD = os.path.join(ROOT, 'assets', 'food')
NL = chr(10)

# tree, fruit item, fruit name, description, max_age (game days to the fruiting stage), kg, price, hunger, thirst, stamina, happiness, wellness
TREES = [
    ('pear', 'food_pear', 'Fresh Pear', 'A ripe green-yellow pear.', 90, 0.18, 6, 9, 6, 9, 5, 2),
    ('peach', 'food_peach', 'Fresh Peach', 'A ripe peach, soft and blushed.', 70, 0.15, 6, 8, 6, 8, 6, 2),
    ('cherry', 'food_cherry', 'Fresh Cherries', 'A pair of ripe red cherries.', 90, 0.04, 6, 4, 3, 5, 6, 2),
    ('plum', 'food_plum', 'Fresh Plum', 'A ripe purple plum.', 80, 0.07, 5, 6, 4, 6, 5, 2),
    ('apricot', 'food_apricot', 'Fresh Apricot', 'A ripe orange apricot.', 80, 0.06, 5, 6, 4, 6, 5, 2),
    ('fig', 'food_fig', 'Fresh Fig', 'A ripe purple fig.', 70, 0.05, 7, 7, 3, 9, 5, 2),
    ('walnut', 'food_walnut', 'Walnuts', 'Walnuts in their shells.', 150, 0.12, 8, 12, 0, 14, 4, 3),
    ('pecan', 'food_pecan', 'Pecans', 'Pecans in their smooth shells.', 160, 0.1, 9, 12, 0, 14, 5, 3),
    ('hazelnut', 'food_hazelnut', 'Hazelnuts', 'Hazelnuts in their smooth shells.', 120, 0.08, 8, 11, 0, 13, 4, 3),
    ('grape', 'food_grapes', 'Grapes', 'A bunch of ripe purple grapes.', 60, 0.25, 7, 6, 8, 8, 6, 3),      # the grapevine is a trellis row (Shape.Trellis), not a tree
]
TITLE = {'grape': 'Grapevine'}
APPLE_STAGES = [(1, 0, 12), (2, 12, 32), (3, 32, 60), (4, 60, 80), (5, 80, 81)]      # the apple's windows, scaled to each tree's own age
STAGE_NAMES = ['sapling', 'small', 'medium', 'mature', 'fruiting']


def load(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def save(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline=NL) as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write(NL)


def put(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline=NL) as f:
        f.write(text)


def group(tree, fruit, max_age, base):
    g = copy.deepcopy(base)
    title = TITLE.get(tree, tree.capitalize())
    g['id'], g['name'], g['icon'] = tree, title, tree + '.png'
    g['description'] = ('A tree lifecycle growing through 5 stages (sapling -> small -> medium -> mature -> fruiting) over %d days. No fruit is visible until the final fruiting stage. '
                        'This group is the authoritative owner of the %s scheme.' % (max_age, tree))
    gr = g['growth']
    gr['species'], gr['max_age'] = tree, max_age
    scale = max_age / 81.0
    stages = []
    for (n, lo, hi), name in zip(APPLE_STAGES, STAGE_NAMES):
        stages.append({'stage': n, 'name': name, 'age_min': round(lo * scale, 1), 'age_max': round(hi * scale, 1) if n < 5 else max_age})
    stages[-1]['age_min'] = round(80 * scale, 1)
    gr['stages'] = stages                                    # no resource / model: the stage trees are procedural
    r = gr['rules']
    r['yield']['extras'] = [{'item_id': fruit, 'amount_min': 5, 'amount_max': 10}]
    r['fruit']['drops'] = [{'item_id': fruit, 'amount_min': 1, 'amount_max': 1}]
    r['planting']['item_id'] = 'plantable_sapling_' + tree
    r.pop('failure', None)                                   # (the dead tree is procedural too)
    return g


def sapling(tree, base):
    s = copy.deepcopy(base)
    sid = 'plantable_sapling_' + tree
    s['id'], s['name'], s['icon'] = sid, 'Plantable Sapling ' + tree.capitalize(), sid + '.png'
    s['description'] = 'A %s tree sapling, ready to plant.' % tree
    if tree == 'grape':
        s['name'], s['description'] = 'Plantable Grapevine', 'A grapevine cutting. It is planted together with its own trellis, and grows up it.'
    s['models'] = []
    return s


def fruit_item(row, base):
    tree, fid, name, desc, _age, kg, price, hunger, thirst, stamina, happy, well = row
    f = copy.deepcopy(base)
    f['id'], f['name'], f['description'], f['icon'] = fid, name, desc, fid + '.png'
    pr = f['properties']
    pr.update({'weight_kg': kg, 'max_stack_size': 20, 'base_value': price, 'happiness_modifier': happy, 'thirst_restore': thirst, 'stamina_restore': stamina,
               'wellness_modifier': well, 'is_buyable': True, 'stores': ['grocer'], 'sale_unit': 'ea'})
    f['models'] = []
    f['category_fields'] = {'hunger_restore': hunger, 'dimensions_m': {'width': 0.08, 'depth': 0.08, 'height': 0.08}}
    return f


if __name__ == '__main__':
    icon_dir = sys.argv[1]
    base_group = load(os.path.join(LOGGING, 'apple', 'apple.json'))
    base_sapling = load(os.path.join(LOGGING, 'plantable_sapling_apple', 'plantable_sapling_apple.json'))
    base_food = load(os.path.join(FOOD, 'food_apple', 'food_apple.json'))
    sapling_icon = os.path.join(LOGGING, 'plantable_sapling_apple', 'plantable_sapling_apple.png')
    for row in TREES:
        tree, fid, age = row[0], row[1], row[4]
        g = group(tree, fid, age, base_group)
        save(os.path.join(LOGGING, tree, tree + '.json'), g)
        put(os.path.join(LOGGING, tree, 'README.md'), '# %s' % g['name'] + NL + NL + g['description'] + NL + NL + 'Procedural tree (ProceduralVegetation.cs); rules from tools/make_fruit_trees.py.' + NL)
        tree_icon = os.path.join(LOGGING, tree, tree + '.png')
        if not os.path.exists(tree_icon):
            shutil.copyfile(os.path.join(LOGGING, 'apple', 'apple.png'), tree_icon)          # placeholder until the real one is rendered in Unity
        s = sapling(tree, base_sapling)
        save(os.path.join(LOGGING, s['id'], s['id'] + '.json'), s)
        put(os.path.join(LOGGING, s['id'], 'README.md'), '# %s' % s['name'] + NL + NL + s['description'] + NL)
        if not os.path.exists(os.path.join(LOGGING, s['id'], s['id'] + '.png')):
            shutil.copyfile(sapling_icon, os.path.join(LOGGING, s['id'], s['id'] + '.png'))
        f = fruit_item(row, base_food)
        save(os.path.join(FOOD, fid, fid + '.json'), f)
        put(os.path.join(FOOD, fid, 'README.md'), '# %s' % f['name'] + NL + NL + f['description'] + NL + NL + 'Icon-only item (no 3D model), written by tools/make_fruit_trees.py.' + NL)
        shutil.copyfile(os.path.join(icon_dir, fid + '.png'), os.path.join(FOOD, fid, fid + '.png'))
        print('wrote', tree, fid)
    # the fruits join the `food` tag
    tag_path = os.path.join(ROOT, 'assets', '_schemas', 'material_tags.json')
    tags = load(tag_path)
    for row in TREES:
        if row[1] not in tags['tags']['food']:
            tags['tags']['food'].append(row[1])
    with open(tag_path, 'w', encoding='utf-8', newline=NL) as f:
        json.dump(tags, f, indent=2, ensure_ascii=False)
        f.write(NL)
    print('tag food: %d members' % len(tags['tags']['food']))
