"""
Builds five PANTRY ingredients (assets/ingredients/<id>/): Ground Black Pepper (a tin, used by Cacio e Pepe and Alfredo), Alfredo Sauce (a jar, simmered from butter, cheese and pepper), Toasted Bread (a slice toasted in the oven) Bread Crumbs (smashed toasted bread, for deep frying) and Cocoa Powder (a tin, for brownies and chocolate pudding).
Procedural, free and local (no Meshy). The manifests start from the salt carton and the pasta sauce jar.

    blender --background --python tools/make_pantry_extras.py
    python tools/render_icon_from_model.py assets/ingredients/<id>/<id>.glb assets/ingredients/<id>/<id>.png
Afterwards: python tools/make_meals.py ; python tools/generate_unity_asset_catalog.py ; python tools/package_catalog_as_mods.py
"""
import copy
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, 'tools')
OUT = os.path.join(ROOT, 'assets', 'ingredients')
NL = chr(10)

ITEMS = {
    'ingredient_pepper_ground': dict(base='ingredient_salt', name='Ground Black Pepper', kg=0.1, price=5, uses=60, category='Pantry Staples',
                                     desc='Finely ground black pepper in a tin with a shaker lid. Seasons.'),
    'ingredient_alfredo_sauce': dict(base='ingredient_pasta_sauce', name='Alfredo Sauce', kg=0.68, price=7, uses=4, category='Flour & Grains',
                                     desc='Creamy cheese and butter Alfredo sauce in a jar. Simmered from butter, cheese and pepper on the stove.'),
    'ingredient_bread_toasted': dict(base='ingredient_salt', name='Toasted Bread', kg=0.03, price=0, uses=None, category='Pantry Staples', buy=False,
                                     desc='A slice of bread toasted dry and hard in the oven. Smashed into bread crumbs.'),
    'ingredient_cocoa': dict(base='ingredient_salt', name='Cocoa Powder', kg=0.23, price=6, uses=30, category='Pantry Staples',
                             desc='Unsweetened cocoa powder in a tin. Brownies and chocolate pudding.'),
    'ingredient_bread_crumbs': dict(base='ingredient_salt', name='Bread Crumbs', kg=0.3, price=4, uses=12, category='Pantry Staples',
                                    desc='Dry bread crumbs in a canister. For breading and deep frying. Made by smashing toasted bread.'),
}


def build(item):
    import bpy
    sys.path.insert(0, TOOLS)
    import kitchen_lib as L
    L.reset_scene()
    for m in list(bpy.data.materials):
        bpy.data.materials.remove(m)
    K = L.Mesh(item)
    if item == 'ingredient_pepper_ground':
        tin = L.material('PepperTin', (0.10, 0.10, 0.11), 0.45, 0.2)
        label = L.material('PepperLabel', (0.90, 0.87, 0.78), 0.6, 0.0)
        stripe = L.material('PepperStripe', (0.70, 0.12, 0.10), 0.5, 0.0)
        cap = L.material('PepperCap', (0.72, 0.72, 0.74), 0.3, 0.8)
        K.lathe([(0.0, 0.0), (0.030, 0.0), (0.0325, 0.003), (0.0325, 0.085), (0.030, 0.088), (0.0, 0.088)], tin, seg=28, hard=(1, 3))
        K.lathe([(0.0328, 0.024), (0.0328, 0.064)], label, seg=28)
        K.lathe([(0.0330, 0.066), (0.0330, 0.072)], stripe, seg=28)
        K.lathe([(0.0, 0.0875), (0.0315, 0.0875), (0.0315, 0.105), (0.0, 0.105)], cap, seg=28, hard=(1, 2))
    elif item == 'ingredient_cocoa':
        tin = L.material('CocoaTin', (0.36, 0.20, 0.12), 0.45, 0.2)
        label = L.material('CocoaLabel', (0.93, 0.88, 0.78), 0.6, 0.0)
        stripe = L.material('CocoaStripe', (0.22, 0.10, 0.06), 0.5, 0.0)
        lid = L.material('CocoaLid', (0.62, 0.34, 0.18), 0.4, 0.0)
        K.lathe([(0.0, 0.0), (0.040, 0.0), (0.042, 0.003), (0.042, 0.105), (0.040, 0.108), (0.0, 0.108)], tin, seg=28, hard=(1, 3))
        K.lathe([(0.0428, 0.026), (0.0428, 0.082)], label, seg=28)
        K.lathe([(0.0430, 0.050), (0.0430, 0.058)], stripe, seg=28)
        K.lathe([(0.0, 0.1075), (0.0415, 0.1075), (0.0415, 0.120), (0.0, 0.120)], lid, seg=28, hard=(1, 2))
    elif item == 'ingredient_bread_toasted':
        crust = L.material('ToastCrust', (0.42, 0.24, 0.09), 0.8, 0.0)
        face = L.material('ToastFace', (0.76, 0.52, 0.24), 0.8, 0.0)
        K.rbox(-0.05, 0.05, -0.05, 0.05, 0.0, 0.014, crust, 0.012)
        K.rbox(-0.042, 0.042, -0.042, 0.042, 0.0135, 0.0152, face, 0.004)
    elif item == 'ingredient_bread_crumbs':
        tin = L.material('CrumbTin', (0.80, 0.64, 0.34), 0.5, 0.1)
        label = L.material('CrumbLabel', (0.95, 0.93, 0.86), 0.6, 0.0)
        stripe = L.material('CrumbStripe', (0.62, 0.30, 0.10), 0.5, 0.0)
        lid = L.material('CrumbLid', (0.70, 0.12, 0.08), 0.4, 0.0)
        K.lathe([(0.0, 0.0), (0.034, 0.0), (0.036, 0.003), (0.036, 0.118), (0.034, 0.121), (0.0, 0.121)], tin, seg=28, hard=(1, 3))
        K.lathe([(0.0368, 0.030), (0.0368, 0.092)], label, seg=28)
        K.lathe([(0.0370, 0.058), (0.0370, 0.066)], stripe, seg=28)
        K.lathe([(0.0, 0.1205), (0.0365, 0.1205), (0.0365, 0.134), (0.0, 0.134)], lid, seg=28, hard=(1, 2))
    else:
        sauce = L.material('AlfredoSauce', (0.95, 0.88, 0.66), 0.35, 0.0)
        label = L.material('AlfredoLabel', (0.96, 0.95, 0.90), 0.6, 0.0)
        stripe = L.material('AlfredoStripe', (0.88, 0.62, 0.20), 0.5, 0.0)
        lid = L.material('AlfredoLid', (0.80, 0.62, 0.16), 0.3, 0.7)
        K.lathe([(0.0, 0.0), (0.040, 0.0), (0.0425, 0.004), (0.0425, 0.105), (0.038, 0.113), (0.0, 0.113)], sauce, seg=28, hard=(1, 3))
        K.lathe([(0.0430, 0.030), (0.0430, 0.085)], label, seg=28)
        K.lathe([(0.0432, 0.062), (0.0432, 0.074)], stripe, seg=28)
        K.lathe([(0.0, 0.112), (0.0405, 0.112), (0.0405, 0.1395), (0.0, 0.1395)], lid, seg=28, hard=(1, 2))
    obj = K.build()
    lo, hi = L.bounds(obj)
    dims = (hi.x - lo.x, hi.y - lo.y, hi.z - lo.z)
    folder = os.path.join(OUT, item)
    os.makedirs(folder, exist_ok=True)
    L.export_glb(obj, os.path.join(folder, item + '.glb'))
    manifest(item, obj['triangles'], dims)
    print('built', item, obj['triangles'], 'tris', '%.3f x %.3f x %.3f' % dims)


def manifest(item, tris, dims):
    d = ITEMS[item]
    with open(os.path.join(OUT, d['base'], d['base'] + '.json'), encoding='utf-8') as f:
        m = json.load(f)
    m['id'], m['name'], m['description'], m['icon'] = item, d['name'], d['desc'], item + '.png'
    m['properties'].update({'weight_kg': d['kg'], 'base_value': d['price'], 'uses_per_item': d['uses'], 'store_category': d['category'], 'stores': ['grocer'], 'is_buyable': d.get('buy', True)})
    if d['uses'] is None:
        m['properties'].pop('uses_per_item', None)   # used whole
    if not d.get('buy', True):
        m['properties'].pop('stores', None)
    w, dp, h = round(dims[0], 3), round(dims[2], 3), round(dims[1], 3)
    m['models'] = [{'file': item + '.glb', 'format': 'glb', 'dimensions_m': {'x': w, 'y': h, 'z': dp}, 'triangles': tris}]
    m['category_fields'] = dict(copy.deepcopy(m.get('category_fields') or {}), dimensions_m={'width': w, 'depth': dp, 'height': h}, processing_method='none', next_item_id='')
    with open(os.path.join(OUT, item, item + '.json'), 'w', encoding='utf-8', newline=NL) as f:
        json.dump(m, f, indent=2, ensure_ascii=False)
        f.write(NL)
    with open(os.path.join(OUT, item, 'README.md'), 'w', encoding='utf-8', newline=NL) as f:
        f.write('# %s' % d['name'] + NL + NL + d['desc'] + NL + NL + 'Procedural model (tools/make_pantry_extras.py), %d triangles.' % tris + NL)


if __name__ == '__main__':
    only = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    for it in (only or list(ITEMS)):
        build(it)
