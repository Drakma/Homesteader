"""
Builds the BATHROOM pack (assets/bathroom/<id>/) in headless Blender: free, local, low-poly fixtures, cabinets and accessories with procedural textures.
18 pieces x 2 styles (classic, modern) x 4 colours = 144 items. A category of its own, apart from the kit's appliances (toilet, sinks, shower stall) and the kitchen / living packs.

    blender --background --python tools/make_bathroom_assets.py                 (every item; or: -- toilet vanity_single)
    python tools/make_bathroom_assets.py --icons [--force]                       (outside Blender: the 128 px icons)

Colours: glazed fixtures (toilet, sinks, tubs, shower) vary in GLAZE (classic white, bone, sage, black; modern white, matte black, stone grey, navy); cabinets in WOOD
(classic mahogany, walnut, cherry, oak; modern birch, walnut, white, black); towels, mat and hamper in FABRIC; accessories in METAL finish. Models: tools/bathroom_models.py.
Afterwards: python tools/make_bathroom_assets.py --icons ; python tools/generate_unity_asset_catalog.py ; python tools/package_catalog_as_mods.py
"""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'assets', 'bathroom')
TOOLS = os.path.join(ROOT, 'tools')
STYLES = ('classic', 'modern')
STYLE_LABEL = {'classic': 'Classic', 'modern': 'Modern'}
STYLE_NOTE = {'classic': 'Classic styling.', 'modern': 'Modern styling.'}
PRICE_FACTOR = {'classic': 1.12, 'modern': 1.0}

# model, stub, name, description, kind (porcelain | wood | fabric | metal), mount (floor | wall), kg, price, extras
# extras: water_per_use_l, water_lpm, support (deck height), shelf, wall
PIECES = [
    ('toilet', 'toilet', 'Toilet', 'A toilet with a tank, a seat and a lid.', 'porcelain', 'floor', 38, 240, {'water_per_use_l': 6}),
    ('pedestal_sink', 'pedestal_sink', 'Pedestal Sink', 'A basin on a pedestal with a faucet.', 'porcelain', 'floor', 22, 190, {'water_per_use_l': 4, 'water_lpm': 6, 'support': '0.85'}),
    ('bathtub_alcove', 'bathtub_alcove', 'Alcove Bathtub', 'A rectangular bathtub with a deck faucet, for an alcove.', 'porcelain', 'floor', 70, 520, {'water_per_use_l': 150, 'water_lpm': 12}),
    ('bathtub_freestanding', 'bathtub_freestanding', 'Freestanding Bathtub', 'A freestanding bathtub with a faucet on its rim.', 'porcelain', 'floor', 95, 980, {'water_per_use_l': 160, 'water_lpm': 12}),
    ('shower_stall', 'shower_stall', 'Shower Stall', 'A corner shower with a tiled back, a glass door, a rain head and a valve.', 'porcelain', 'floor', 85, 640, {'water_per_use_l': 60, 'water_lpm': 8}),
    ('vanity_single', 'vanity_single', 'Single Vanity', 'A bathroom vanity with a stone top, a basin, a faucet and two doors.', 'wood', 'floor', 42, 460, {'water_per_use_l': 4, 'water_lpm': 6, 'support': '0.835'}),
    ('vanity_double', 'vanity_double', 'Double Vanity', 'A wide bathroom vanity with two basins, two faucets and four doors.', 'wood', 'floor', 78, 880, {'water_per_use_l': 4, 'water_lpm': 6, 'support': '0.835'}),
    ('medicine_cabinet', 'medicine_cabinet', 'Medicine Cabinet', 'A wall cabinet with a mirror door. Mount it on a wall.', 'wood', 'wall', 6, 95, {}),
    ('vanity_mirror', 'vanity_mirror', 'Bathroom Mirror', 'A framed mirror for over the basin. Mount it on a wall.', 'wood', 'wall', 5, 85, {}),
    ('linen_cabinet', 'linen_cabinet', 'Linen Cabinet', 'A tall cabinet with a glazed upper door and a closed lower door.', 'wood', 'floor', 36, 330, {}),
    ('towel_shelf', 'towel_shelf', 'Towel Shelf', 'A wall shelf with a towel bar under it. Mount it on a wall and stand things on it.', 'wood', 'wall', 4, 70, {'shelf': True}),
    ('hamper', 'hamper', 'Laundry Hamper', 'A laundry hamper with a fabric bag and a lid.', 'fabric', 'floor', 3.5, 60, {}),
    ('towel_stack', 'towel_stack', 'Towel Stack', 'A stack of folded towels with a rolled washcloth.', 'fabric', 'floor', 2.4, 38, {}),
    ('bath_mat', 'bath_mat', 'Bath Mat', 'A soft bath mat.', 'fabric', 'floor', 0.9, 24, {}),
    ('towel_bar', 'towel_bar', 'Towel Bar', 'A wall towel bar with a hand towel. Mount it on a wall.', 'metal', 'wall', 0.9, 34, {}),
    ('tp_holder', 'tp_holder', 'Toilet Paper Holder', 'A wall holder with a roll of toilet paper. Mount it on a wall.', 'metal', 'wall', 0.4, 18, {}),
    ('hook_rail', 'hook_rail', 'Robe Hook Rail', 'A wall rail with four hooks. Mount it on a wall.', 'metal', 'wall', 0.8, 30, {}),
    ('soap_set', 'soap_set', 'Soap and Toothbrush Set', 'A soap pump, a dish and a toothbrush cup on a small tray.', 'metal', 'floor', 0.8, 28, {'support_none': True}),
]


def variants():
    sys.path.insert(0, TOOLS)
    from bathroom_colors import colors
    out = []
    for model, stub, name, desc, kind, mount, kg, price, ex in PIECES:
        for style in STYLES:
            for ck, clabel in colors(style, kind):
                out.append(dict(model=model, style=style, kind=kind, color=ck, mount=mount, id='bathroom_%s_%s_%s' % (stub, style, ck),
                                name='%s %s %s' % (STYLE_LABEL[style], clabel, name), desc='%s %s' % (desc, STYLE_NOTE[style]),
                                kg=kg, price=round(price * PRICE_FACTOR[style]), extras=ex))
    return out


def manifest(v, tris, dims):
    w, d, h = dims
    ex = v['extras']
    props = {
        'weight_kg': float(v['kg']), 'max_stack_size': 1, 'base_value': int(v['price']), 'is_consumable': False,
        'footprint': '%.2fm W x %.2fm D x %.2fm H' % (w, d, h),
        'happiness_modifier': 0, 'thirst_restore': 0, 'energy_restore': 0, 'stamina_restore': 0, 'wellness_modifier': 0,
        'placeable': True, 'wrench_remove': True, 'is_buyable': True, 'stores': ['furniture'], 'sale_unit': 'ea',
    }
    if ex.get('shelf'):
        props['support_surface'] = True
        props['deck_heights'] = '%.3f' % h
    if ex.get('support'):
        props['support_surface'] = True
        props['deck_heights'] = ex['support']
    fields = {'dimensions_m': {'width': round(w, 3), 'depth': round(d, 3), 'height': round(h, 3)}, 'bathroom_kind': v['model'], 'style': v['style'], 'color': v['color'],
              'water_per_use_l': ex.get('water_per_use_l', 0), 'water_usage_lpm': ex.get('water_lpm', 0)}
    return {
        '$schema': 'https://homesteader.game/schemas/item_v1.json',
        'id': v['id'], 'name': v['name'], 'category': 'bathroom', 'description': v['desc'], 'icon': v['id'] + '.png',
        'properties': props,
        'models': [{'file': v['id'] + '.glb', 'format': 'glb', 'dimensions_m': {'x': round(w, 3), 'y': round(h, 3), 'z': round(d, 3)}, 'triangles': int(tris)}],
        'utilities': {
            'water': {'metric': 'None (unplumbed / dry)', 'details': 'None (unplumbed / dry)'},
            'electricity': {'metric': 'None (passive / unpowered)', 'details': 'None (passive / unpowered)'},
            'sewage': {'metric': 'None (no waste discharge)', 'details': 'None (no waste discharge)'},
            'battery': {'metric': 'None (no internal battery)', 'details': 'None (no internal battery)'},
            'internet': {'metric': 'None (offline / non-networked)', 'details': 'None (offline / non-networked)'},
        },
        'growth': {'is_growable': False, 'growth_type': None, 'species': None, 'max_age': None, 'time_unit': None, 'total_stages': 0, 'current_stage': None, 'stages': []},
        'plugin_metadata': {'version': '1.0.0', 'author': 'Homesteader Core', 'compatible_api': 'v1'},
        'category_fields': fields,
    }


def readme(v, tris, dims):
    w, d, h = dims
    nl = chr(10)
    return ('# %s' % v['name'] + nl + nl + v['desc'] + nl + nl + 'Procedural model (tools/make_bathroom_assets.py, tools/bathroom_models.py), %d triangles, %.2f x %.2f x %.2f m (W x D x H).'
            % (tris, w, d, h) + nl)


def build_all(only):
    sys.path.insert(0, TOOLS)
    import bathroom_lib as BL
    import bathroom_models as M
    import kitchen_lib as L
    nl = chr(10)
    built = 0
    for v in variants():
        if only and v['model'] not in only:
            continue
        L.reset_scene()
        obj = getattr(M, v['model'])(BL.BathPalette(v['style'], v['kind'], v['color'])).build()
        lo, hi = L.bounds(obj)
        dy = -hi.y if v['mount'] == 'wall' else 0.0                                # a wall piece: its back is the plane y = 0
        for vt in obj.data.vertices:
            vt.co.z -= lo.z
            vt.co.y += dy
        lo, hi = L.bounds(obj)
        dims = (hi.x - lo.x, hi.y - lo.y, hi.z - lo.z)
        folder = os.path.join(OUT, v['id'])
        os.makedirs(folder, exist_ok=True)
        L.export_glb(obj, os.path.join(folder, v['id'] + '.glb'))
        tris = obj['triangles']
        with open(os.path.join(folder, v['id'] + '.json'), 'w', encoding='utf-8', newline=nl) as f:
            json.dump(manifest(v, tris, dims), f, indent=2, ensure_ascii=False)
            f.write(nl)
        with open(os.path.join(folder, 'README.md'), 'w', encoding='utf-8', newline=nl) as f:
            f.write(readme(v, tris, dims))
        built += 1
        print('built', v['id'], tris, 'tris', '%.2f x %.2f x %.2f' % dims)
    print('BATHROOM: %d items' % built)


def make_icons(workers=4):
    from concurrent.futures import ThreadPoolExecutor
    force = '--force' in sys.argv
    jobs = []
    for v in variants():
        folder = os.path.join(OUT, v['id'])
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
