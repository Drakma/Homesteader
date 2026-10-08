"""
Builds the TABLEWARE the Meal Builder uses (assets/kitchen/<id>/): the Dinner Plate, the Soup Bowl, the Plated Meal (the same plate carrying up to four foods) and the Drinking Glass. Free and local (no Meshy).

  kitchen_plate         a plain plate, sold empty; the Meal Builder takes one from the kitchen's cabinets and shelves
  kitchen_plated_meal   a plate with a meal on it: a CONTAINER item (`container`: up to 4 items, foods only) holding the chosen foods. Not sold: it is made at the Meal Builder
  kitchen_bowl_meal     a soup bowl with one soup / stew / salad in it: a CONTAINER item (max 1 food). Not sold: made at the Meal Builder
  kitchen_glass         a drinking glass: a LIQUID container (0.3 L, takes any `#drink`); the Meal Builder pours the chosen drink into it

    blender --background --python tools/make_tableware_assets.py
    python tools/render_icon_from_model.py assets/kitchen/<id>/<id>.glb assets/kitchen/<id>/<id>.png
Afterwards: python tools/generate_unity_asset_catalog.py ; python tools/package_catalog_as_mods.py
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, 'tools')
OUT = os.path.join(ROOT, 'assets', 'kitchen')
NL = chr(10)

ITEMS = {
    'kitchen_plate': dict(model='plate', name='Dinner Plate', kg=0.45, price=4, buy=True,
                          desc='A plain white dinner plate with a blue rim. The Meal Builder serves a meal on one.'),
    'kitchen_plated_meal': dict(model='plate', name='Plated Meal', kg=0.5, price=0, buy=False,
                                desc='A dinner plate with a meal on it: up to four foods. Made at the Meal Builder.',
                                container={'capacity_kg': 3.0, 'accepts': ['food'], 'show_fill': False, 'max_items': 4}),
    'kitchen_bowl': dict(model='bowl', name='Soup Bowl', kg=0.35, price=4, buy=True,
                         desc='A deep white soup bowl with a blue rim. Soups are served in one: the bowl goes into the soup.'),
    'kitchen_bowl_meal': dict(model='bowl', name='Bowl of Food', kg=0.5, price=0, buy=False,
                              desc='A soup bowl with a soup, stew or salad in it. Made at the Meal Builder.',
                              container={'capacity_kg': 3.0, 'accepts': ['food'], 'show_fill': False, 'max_items': 1}),
    'kitchen_glass': dict(model='glass', name='Drinking Glass', kg=0.25, price=3, buy=True,
                          desc='A drinking glass that holds 0.3 L of a drink. The Meal Builder pours the drink into one.',
                          liquid={'capacity_l': 0.3, 'accepts': ['#drink']}),
}


def build(item):
    import bpy
    sys.path.insert(0, TOOLS)
    import kitchen_lib as L
    d = ITEMS[item]
    L.reset_scene()
    for m in list(bpy.data.materials):
        bpy.data.materials.remove(m)
    K = L.Mesh(item)
    if d['model'] == 'plate':
        white = L.material('PlateWhite', (0.95, 0.95, 0.93), 0.25, 0.0)
        blue = L.material('PlateRim', (0.18, 0.35, 0.72), 0.3, 0.0)
        K.lathe([(0.0, 0.0), (0.07, 0.0), (0.075, 0.004), (0.125, 0.020), (0.13, 0.026), (0.122, 0.026), (0.118, 0.020), (0.075, 0.010), (0.0, 0.010)], white, seg=40, hard=(2, 4))
        K.lathe([(0.113, 0.0185), (0.121, 0.0225), (0.121, 0.0238), (0.113, 0.0205)], blue, seg=40)   # the blue ring round the rim
    elif d['model'] == 'bowl':
        white = L.material('BowlWhite', (0.95, 0.95, 0.93), 0.25, 0.0)
        blue = L.material('BowlRim', (0.18, 0.35, 0.72), 0.3, 0.0)
        K.lathe([(0.0, 0.0), (0.04, 0.0), (0.045, 0.004), (0.075, 0.025), (0.095, 0.06), (0.098, 0.066), (0.092, 0.066), (0.089, 0.060), (0.070, 0.030), (0.0, 0.014)], white, seg=40, hard=(2, 4))
        K.lathe([(0.0905, 0.0585), (0.0965, 0.0635), (0.0965, 0.0648), (0.0905, 0.0598)], blue, seg=40)
    else:
        import bpy as _b
        glass = _b.data.materials.new('GlassClear')
        glass.use_nodes = True
        b = glass.node_tree.nodes['Principled BSDF']
        b.inputs['Base Color'].default_value = (0.82, 0.93, 0.95, 1.0)
        b.inputs['Roughness'].default_value = 0.05
        b.inputs['Alpha'].default_value = 0.42
        try:
            glass.surface_render_method = 'BLENDED'
        except Exception:
            pass
        K.lathe([(0.0, 0.0), (0.030, 0.0), (0.040, 0.11), (0.0365, 0.11), (0.0285, 0.012), (0.0, 0.012)], glass, seg=32, hard=(1,))
    obj = K.build()
    lo, hi = L.bounds(obj)
    dims = (hi.x - lo.x, hi.y - lo.y, hi.z - lo.z)
    folder = os.path.join(OUT, item)
    os.makedirs(folder, exist_ok=True)
    L.export_glb(obj, os.path.join(folder, item + '.glb'))
    manifest(item, obj['triangles'], dims)
    print('built', item, obj['triangles'], 'tris', '%.3f x %.3f x %.3f' % dims, 'zmin %.4f' % lo.z)


def manifest(item, tris, dims):
    d = ITEMS[item]
    w, dp, h = dims
    m = {
        '$schema': 'https://homesteader.game/schemas/item_v1.json',
        'id': item, 'name': d['name'], 'category': 'kitchen', 'description': d['desc'], 'icon': item + '.png',
        'properties': {
            'weight_kg': d['kg'], 'max_stack_size': 20 if item not in ('kitchen_plated_meal', 'kitchen_bowl_meal') else 1, 'base_value': d['price'], 'is_consumable': False,
            'footprint': '%.2fm W x %.2fm D x %.2fm H' % (w, dp, h),
            'happiness_modifier': 0, 'thirst_restore': 0, 'energy_restore': 0, 'stamina_restore': 0, 'wellness_modifier': 0,
            'placeable': True, 'is_buyable': d['buy'], 'sale_unit': 'ea',
        },
        'models': [{'file': item + '.glb', 'format': 'glb', 'dimensions_m': {'x': round(w, 3), 'y': round(h, 3), 'z': round(dp, 3)}, 'triangles': int(tris)}],
        'utilities': {
            'water': {'metric': 'None (unplumbed / dry)', 'details': 'None (unplumbed / dry)'},
            'electricity': {'metric': 'None (passive / unpowered)', 'details': 'None (passive / unpowered)'},
            'sewage': {'metric': 'None (no waste discharge)', 'details': 'None (no waste discharge)'},
            'battery': {'metric': 'None (no internal battery)', 'details': 'None (no internal battery)'},
            'internet': {'metric': 'None (offline / non-networked)', 'details': 'None (offline / non-networked)'},
        },
        'growth': {'is_growable': False, 'growth_type': None, 'species': None, 'max_age': None, 'time_unit': None, 'total_stages': 0, 'current_stage': None, 'stages': []},
        'plugin_metadata': {'version': '1.0.0', 'author': 'Homesteader Core', 'compatible_api': 'v1'},
        'category_fields': {'dimensions_m': {'width': round(w, 3), 'depth': round(dp, 3), 'height': round(h, 3)}, 'kitchen_kind': 'accessory', 'finish': 'ceramic' if d['model'] in ('plate', 'bowl') else 'glass', 'power_draw_w': 0},
    }
    if d['buy']:
        m['properties']['stores'] = ['furniture']
    if item == 'kitchen_plated_meal':
        m['properties']['leaves_item'] = 'kitchen_plate'   # eaten: the plate is left (Kitchen/Consumption.cs)
    if 'container' in d:
        m['container'] = d['container']
    if 'liquid' in d:
        m['liquid_container'] = d['liquid']
    with open(os.path.join(OUT, item, item + '.json'), 'w', encoding='utf-8', newline=NL) as f:
        json.dump(m, f, indent=2, ensure_ascii=False)
        f.write(NL)
    with open(os.path.join(OUT, item, 'README.md'), 'w', encoding='utf-8', newline=NL) as f:
        f.write('# %s' % d['name'] + NL + NL + d['desc'] + NL + NL + 'Procedural model (tools/make_tableware_assets.py), %d triangles.' % tris + NL)


if __name__ == '__main__':
    only = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    for it in (only or list(ITEMS)):
        build(it)
