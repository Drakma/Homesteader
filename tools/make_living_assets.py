"""
Builds the LIVING / FAMILY ROOM pack (assets/living/<id>/) in headless Blender: free, local, low-poly furniture with procedural fabric, leather and wood textures.
28 pieces x 2 styles (classic, modern) x 4 colours = 224 items. A category of its own, apart from the kit's furniture and the kitchen pack.

    blender --background --python tools/make_living_assets.py                  (every item)
    blender --background --python tools/make_living_assets.py -- sofa bookshelf   (only these models)
    python tools/make_living_assets.py --icons [--force]                         (outside Blender: render the 128 px icons)

Upholstered pieces, lamps, rugs and the plant pot vary in FABRIC colour (classic: burgundy, forest green, navy, camel leather; modern: charcoal, stone, teal, mustard); wooden
pieces vary in WOOD colour (classic: mahogany, walnut, cherry, oak; modern: birch, walnut, white, black). Models in tools/living_models.py, palettes in tools/living_lib.py.
Afterwards: python tools/make_living_assets.py --icons ; python tools/generate_unity_asset_catalog.py ; python tools/package_catalog_as_mods.py
"""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIVING = os.path.join(ROOT, 'assets', 'living')
TOOLS = os.path.join(ROOT, 'tools')

STYLES = ('classic', 'modern')
STYLE_LABEL = {'classic': 'Classic', 'modern': 'Modern'}
LIGHT = {"id": "bulb", "color": "#FFD9A0", "intensity": 2.5, "range_m": 6, "on": "always", "power_w": 12, "type": "point", "shadows": False, "requires_power": True}

# model, stub, name, description, kind (fabric | wood | rug), weight kg, price, extras  (extras: wall, support (deck height), light (bulb height m), watts)
PIECES = [
    ('sofa', 'sofa', 'Sofa', 'A three-seat sofa with loose seat and back cushions and two throw pillows.', 'fabric', 48, 780, {}),
    ('loveseat', 'loveseat', 'Loveseat', 'A two-seat loveseat with loose cushions and throw pillows.', 'fabric', 34, 560, {}),
    ('armchair', 'armchair', 'Armchair', 'An upholstered armchair with a loose seat cushion.', 'fabric', 20, 340, {}),
    ('recliner', 'recliner', 'Recliner', 'A deep recliner with its footrest out.', 'fabric', 36, 520, {}),
    ('sectional', 'sectional', 'Sectional Sofa', 'An L-shaped sectional: a three-seat sofa with a chaise.', 'fabric', 82, 1380, {}),
    ('ottoman', 'ottoman', 'Ottoman', 'A cushioned ottoman on short legs.', 'fabric', 9, 130, {'support': '0.42'}),
    ('pouf', 'pouf', 'Floor Pouf', 'A round floor pouf.', 'fabric', 4, 70, {}),
    ('accent_chair', 'accent_chair', 'Accent Chair', 'A statement accent chair for a corner of the room.', 'fabric', 14, 290, {}),
    ('floor_lamp', 'floor_lamp', 'Floor Lamp', 'A tall floor lamp with a fabric shade. It lights the room when it has power.', 'fabric', 4.5, 95, {'light': 1.45}),
    ('table_lamp', 'table_lamp', 'Table Lamp', 'A table lamp with a fabric shade. It lights the room when it has power.', 'fabric', 2.2, 45, {'light': 0.45}),
    ('area_rug', 'area_rug', 'Area Rug', 'A large woven area rug with a border and a medallion.', 'rug', 11, 220, {}),
    ('plant_pot', 'plant', 'Potted Plant', 'A leafy houseplant in a glazed pot.', 'fabric', 7, 60, {}),
    ('coffee_table', 'coffee_table', 'Coffee Table', 'A low coffee table with a lower shelf.', 'wood', 16, 240, {'support': '0.45'}),
    ('end_table', 'end_table', 'End Table', 'A side table for beside the sofa.', 'wood', 9, 120, {'support': '0.60'}),
    ('console_table', 'console_table', 'Console Table', 'A narrow console table for a hall or behind the sofa.', 'wood', 14, 180, {'support': '0.80'}),
    ('tv_stand', 'tv_stand', 'TV Stand', 'A low media console for the television.', 'wood', 28, 260, {'support': '0.55'}),
    ('sideboard', 'sideboard', 'Sideboard', 'A long sideboard with doors and drawers.', 'wood', 44, 460, {'support': '0.85'}),
    ('bookshelf', 'bookshelf', 'Bookshelf', 'A tall open bookshelf with five shelves, full of books.', 'wood', 30, 210, {'support': '0.12,0.52,0.92,1.32,1.70'}),
    ('display_cabinet', 'display_cabinet', 'Display Cabinet', 'A glass-door display cabinet over a closed cabinet.', 'wood', 46, 520, {}),
    ('toy_chest', 'toy_chest', 'Toy Chest', 'A chest with a lid for the toys.', 'wood', 12, 95, {'support': '0.50'}),
    ('rocker', 'rocker', 'Rocking Chair', 'A rocking chair for the family room.', 'wood', 9, 170, {}),
    ('piano', 'piano', 'Piano', 'A piano with a keyboard and a music stand.', 'wood', 90, 1400, {}),
    ('tv', 'tv', 'Television', 'A television set for the family room.', 'wood', 14, 380, {'watts': 90}),
    ('wall_tv', 'wall_tv', 'Wall-Mount TV', 'A 55 inch flat-screen TV on a wall bracket. Mount it on a wall.', 'wood', 16, 520, {'wall': True, 'watts': 90}),
    ('wall_tv_large', 'wall_tv_large', 'Large Wall-Mount TV', 'A 75 inch flat-screen TV on a wall bracket. Mount it on a wall.', 'wood', 30, 980, {'wall': True, 'watts': 150}),
    ('wall_mirror', 'wall_mirror', 'Wall Mirror', 'A framed wall mirror. Mount it on a wall.', 'wood', 6, 120, {'wall': True}),
    ('wall_art', 'wall_art', 'Framed Picture', 'A framed picture. Mount it on a wall.', 'wood', 3, 70, {'wall': True}),
    ('wall_clock', 'wall_clock', 'Wall Clock', 'A round wall clock. Mount it on a wall.', 'wood', 2, 55, {'wall': True}),
]
STYLE_NOTE = {'classic': 'Classic styling: turned legs, rolled arms, mouldings and brass.', 'modern': 'Modern styling: clean lines, slim tapered legs and black metal.'}
PRICE_FACTOR = {'classic': 1.12, 'modern': 1.0}


def variants():
    sys.path.insert(0, TOOLS)
    from living_colors import colors
    out = []
    for model, stub, name, desc, kind, kg, price, ex in PIECES:
        for style in STYLES:
            for ck, clabel in colors(style, kind):
                out.append(dict(model=model, style=style, kind=kind, color=ck, id='living_%s_%s_%s' % (stub, style, ck),
                                name='%s %s %s' % (STYLE_LABEL[style], clabel, name), desc='%s %s' % (desc, STYLE_NOTE[style]),
                                kg=kg, price=round(price * PRICE_FACTOR[style]), extras=ex, label=clabel))
    return out


def manifest(v, tris, dims):
    w, d, h = dims
    ex = v['extras']
    props = {
        'weight_kg': float(v['kg']), 'max_stack_size': 1, 'base_value': int(v['price']), 'is_consumable': False,
        'footprint': '%.2fm W x %.2fm D x %.2fm H' % (w, d, h),
        'happiness_modifier': 0, 'thirst_restore': 0, 'energy_restore': 0, 'stamina_restore': 0, 'wellness_modifier': 0,
        'placeable': not ex.get('wall'), 'wrench_remove': True, 'is_buyable': True, 'stores': ['furniture'], 'sale_unit': 'ea',
    }
    if ex.get('wall'):
        props['attach_surface'] = 'wall'
        props['attach_side'] = 'interior'
    if ex.get('support'):
        props['support_surface'] = True
        props['deck_heights'] = ex['support']
    watts = int(ex.get('watts', 0)) or (12 if 'light' in ex else 0)
    man = {
        '$schema': 'https://homesteader.game/schemas/item_v1.json',
        'id': v['id'], 'name': v['name'], 'category': 'living', 'description': v['desc'], 'icon': v['id'] + '.png',
        'properties': props,
        'models': [{'file': v['id'] + '.glb', 'format': 'glb', 'dimensions_m': {'x': round(w, 3), 'y': round(h, 3), 'z': round(d, 3)}, 'triangles': int(tris)}],
        'utilities': {
            'water': {'metric': 'None (unplumbed / dry)', 'details': 'None (unplumbed / dry)'},
            'electricity': ({'metric': '%d W' % watts, 'details': 'Draws about %d W while it runs.' % watts} if watts else {'metric': 'None (passive / unpowered)', 'details': 'None (passive / unpowered)'}),
            'sewage': {'metric': 'None (no waste discharge)', 'details': 'None (no waste discharge)'},
            'battery': {'metric': 'None (no internal battery)', 'details': 'None (no internal battery)'},
            'internet': {'metric': 'None (offline / non-networked)', 'details': 'None (offline / non-networked)'},
        },
        'growth': {'is_growable': False, 'growth_type': None, 'species': None, 'max_age': None, 'time_unit': None, 'total_stages': 0, 'current_stage': None, 'stages': []},
        'plugin_metadata': {'version': '1.0.0', 'author': 'Homesteader Core', 'compatible_api': 'v1'},
        'category_fields': {'dimensions_m': {'width': round(w, 3), 'depth': round(d, 3), 'height': round(h, 3)}, 'living_kind': v['model'], 'style': v['style'],
                            'color': v['color'], 'power_draw_w': watts},
    }
    if 'light' in ex:
        man['lights'] = [dict(LIGHT, offset_m=[0, ex['light'], 0])]
    return man


def readme(v, tris, dims):
    w, d, h = dims
    return ('# %s\n\n%s\n\nProcedural model (tools/make_living_assets.py, tools/living_models.py), %d triangles, %.2f x %.2f x %.2f m (W x D x H).%s\n'
            % (v['name'], v['desc'], tris, w, d, h, ' A wall item: mount it on a wall.' if v['extras'].get('wall') else ''))


def build_all(only):
    sys.path.insert(0, TOOLS)
    import kitchen_lib as L
    import living_lib as LL
    import living_models as M
    built = 0
    for v in variants():
        if only and v['model'] not in only:
            continue
        L.reset_scene()
        P = LL.Palette(v['style'], v['kind'], v['color'])
        obj = getattr(M, v['model'])(P).build()
        lo, hi = L.bounds(obj)
        dims = (hi.x - lo.x, hi.y - lo.y, hi.z - lo.z)
        folder = os.path.join(LIVING, v['id'])
        os.makedirs(folder, exist_ok=True)
        L.export_glb(obj, os.path.join(folder, v['id'] + '.glb'))
        tris = obj['triangles']
        with open(os.path.join(folder, v['id'] + '.json'), 'w', encoding='utf-8', newline='\n') as f:
            json.dump(manifest(v, tris, dims), f, indent=2, ensure_ascii=False)
            f.write('\n')
        with open(os.path.join(folder, 'README.md'), 'w', encoding='utf-8', newline='\n') as f:
            f.write(readme(v, tris, dims))
        built += 1
        print('built', v['id'], tris, 'tris', '%.2f x %.2f x %.2f' % dims)
    print('LIVING: %d items' % built)


def make_icons(workers=4):
    from concurrent.futures import ThreadPoolExecutor
    force = '--force' in sys.argv
    jobs = []
    for v in variants():
        folder = os.path.join(LIVING, v['id'])
        glb, png = os.path.join(folder, v['id'] + '.glb'), os.path.join(folder, v['id'] + '.png')
        if os.path.exists(glb) and (force or not os.path.exists(png)):
            jobs.append((glb, png))

    def one(job):
        r = subprocess.run([sys.executable, os.path.join(TOOLS, 'render_icon_from_model.py'), job[0], job[1]], capture_output=True, text=True)
        ok = os.path.exists(job[1]) and r.returncode == 0
        print(('icon ' if ok else 'FAILED ') + os.path.basename(job[1]))
        return ok
    with ThreadPoolExecutor(max_workers=workers) as ex:
        results = list(ex.map(one, jobs))
    print('ICONS: %d of %d' % (sum(results), len(jobs)))


if __name__ == '__main__':
    if '--icons' in sys.argv:
        make_icons()
    else:
        only = set(sys.argv[sys.argv.index('--') + 1:]) if '--' in sys.argv else set()
        build_all(only)
