"""
Builds the GARAGE / WORKSHOP pack (assets/garage/<id>/) in headless Blender: free, local, low-poly furniture with procedural fabric and wood textures.
14 pieces x 2 styles (classic, modern) x 4 colours = 112 items. A category of its own, apart from the kit furniture and the other room packs.

    blender --background --python tools/make_garage_assets.py                  (every item)
    blender --background --python tools/make_garage_assets.py -- sofa bookshelf   (only these models)
    python tools/make_garage_assets.py --icons [--force]                         (outside Blender: render the 128 px icons)

Painted-steel pieces, lamps, rugs and the plant pot vary in FABRIC colour (classic: burgundy, forest green, navy, camel leather; modern: charcoal, stone, teal, mustard); wooden
pieces vary in WOOD colour (classic: mahogany, walnut, cherry, oak; modern: birch, walnut, white, black). Models in tools/garage_models.py, palettes in tools/living_lib.py.
Afterwards: python tools/make_garage_assets.py --icons ; python tools/generate_unity_asset_catalog.py ; python tools/package_catalog_as_mods.py
"""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GARAGE = os.path.join(ROOT, 'assets', 'garage')
TOOLS = os.path.join(ROOT, 'tools')

STYLES = ('classic', 'modern')
STYLE_LABEL = {'classic': 'Classic', 'modern': 'Modern'}
LIGHT = {"id": "bulb", "color": "#FFD9A0", "intensity": 2.5, "range_m": 6, "on": "always", "power_w": 12, "type": "point", "shadows": False, "requires_power": True}

# model, stub, name, description, kind (fabric | wood | rug), weight kg, price, extras  (extras: wall, support (deck height), light (bulb height m), watts)
PIECES = [
    ('workbench', 'workbench', 'Workbench', 'A workshop bench with a thick top, a lower shelf and a vise.', 'wood', 55, 340, {'support': '0.92'}),
    ('pegboard_wall', 'pegboard', 'Pegboard Wall Panel', 'A pegboard with a hammer, a saw and wrenches on hooks. Mount it on a wall.', 'wood', 6, 70, {'wall': True}),
    ('sawhorse', 'sawhorse', 'Sawhorse', 'A sawhorse for cutting boards.', 'wood', 6, 45, {'support': '0.80'}),
    ('shop_stool', 'shop_stool', 'Shop Stool', 'A round-topped stool for the workshop.', 'wood', 4, 40, {}),
    ('lumber_rack_wall', 'lumber_rack', 'Lumber Rack', 'Three steel arms holding a stack of boards. Mount it on a wall.', 'paint', 14, 90, {'wall': True}),
    ('tool_chest_rolling', 'tool_chest', 'Rolling Tool Chest', 'A rolling tool chest with five drawers.', 'paint', 46, 420, {}),
    ('tool_chest_top', 'tool_chest_top', 'Top Tool Chest', 'A top tool chest with a lid and three drawers.', 'paint', 14, 150, {'support': '0.34'}),
    ('cabinet_tall', 'cabinet_tall', 'Tall Steel Cabinet', 'A tall two-door steel cabinet with vent slots.', 'paint', 52, 310, {}),
    ('cabinet_base', 'cabinet_base', 'Steel Base Cabinet', 'A base cabinet with drawers, doors and a wood top.', 'paint', 48, 280, {'support': '0.92'}),
    ('wall_cabinet', 'wall_cabinet', 'Steel Wall Cabinet', 'A two-door steel wall cabinet. Mount it on a wall.', 'paint', 16, 130, {'wall': True}),
    ('steel_shelving', 'shelving', 'Steel Shelving Unit', 'A steel shelving unit with boxes and bins.', 'paint', 30, 140, {'support': '0.15,0.63,1.11,1.59'}),
    ('parts_cabinet', 'parts_cabinet', 'Parts Cabinet', 'A small-parts cabinet with 24 labelled drawers.', 'paint', 12, 95, {}),
    ('air_compressor', 'air_compressor', 'Air Compressor', 'A tank air compressor on wheels.', 'paint', 38, 360, {'watts': 1500}),
    ('bench_grinder', 'bench_grinder', 'Bench Grinder', 'A bench grinder with two wheels.', 'paint', 9, 110, {'watts': 400}),
]
STYLE_NOTE = {'classic': 'Classic styling: turned legs, rolled arms, mouldings and brass.', 'modern': 'Modern styling: clean lines, slim tapered legs and black metal.'}
PRICE_FACTOR = {'classic': 1.12, 'modern': 1.0}


def variants():
    sys.path.insert(0, TOOLS)
    from garage_colors import colors
    out = []
    for model, stub, name, desc, kind, kg, price, ex in PIECES:
        for style in STYLES:
            for ck, clabel in colors(style, kind):
                out.append(dict(model=model, style=style, kind=kind, color=ck, id='garage_%s_%s_%s' % (stub, style, ck),
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
        'id': v['id'], 'name': v['name'], 'category': 'garage', 'description': v['desc'], 'icon': v['id'] + '.png',
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
        'category_fields': {'dimensions_m': {'width': round(w, 3), 'depth': round(d, 3), 'height': round(h, 3)}, 'garage_kind': v['model'], 'style': v['style'],
                            'color': v['color'], 'power_draw_w': watts, 'water_per_use_l': ex.get('water_per_use_l', 0), 'water_usage_lpm': ex.get('water_lpm', 0)},
    }
    if 'light' in ex:
        man['lights'] = [dict(LIGHT, offset_m=[0, ex['light'], 0])]
    return man


def readme(v, tris, dims):
    w, d, h = dims
    return ('# %s\n\n%s\n\nProcedural model (tools/make_garage_assets.py, tools/garage_models.py), %d triangles, %.2f x %.2f x %.2f m (W x D x H).%s\n'
            % (v['name'], v['desc'], tris, w, d, h, ' A wall item: mount it on a wall.' if v['extras'].get('wall') else ''))


def build_all(only):
    sys.path.insert(0, TOOLS)
    import kitchen_lib as L
    import garage_lib as LL
    import garage_models as M
    built = 0
    for v in variants():
        if only and v['model'] not in only:
            continue
        L.reset_scene()
        P = LL.GaragePalette(v['style'], v['kind'], v['color'])
        obj = getattr(M, v['model'])(P).build()
        lo, hi = L.bounds(obj)
        dims = (hi.x - lo.x, hi.y - lo.y, hi.z - lo.z)
        folder = os.path.join(GARAGE, v['id'])
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
    print('GARAGE: %d items' % built)


def make_icons(workers=4):
    from concurrent.futures import ThreadPoolExecutor
    force = '--force' in sys.argv
    jobs = []
    for v in variants():
        folder = os.path.join(GARAGE, v['id'])
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
