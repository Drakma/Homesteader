"""
Builds the HOME OFFICE pack (assets/office/<id>/) in headless Blender: free, local, low-poly furniture with procedural fabric and wood textures.
8 pieces x 2 styles (classic, modern) x 4 colours = 64 items. A category of its own, apart from the kit furniture and the other room packs.

    blender --background --python tools/make_office_assets.py                  (every item)
    blender --background --python tools/make_office_assets.py -- sofa bookshelf   (only these models)
    python tools/make_office_assets.py --icons [--force]                         (outside Blender: render the 128 px icons)

Upholstered pieces, lamps, rugs and the plant pot vary in FABRIC colour (classic: burgundy, forest green, navy, camel leather; modern: charcoal, stone, teal, mustard); wooden
pieces vary in WOOD colour (classic: mahogany, walnut, cherry, oak; modern: birch, walnut, white, black). Models in tools/office_models.py, palettes in tools/living_lib.py.
Afterwards: python tools/make_office_assets.py --icons ; python tools/generate_unity_asset_catalog.py ; python tools/package_catalog_as_mods.py
"""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OFFICE = os.path.join(ROOT, 'assets', 'office')
TOOLS = os.path.join(ROOT, 'tools')

STYLES = ('classic', 'modern')
STYLE_LABEL = {'classic': 'Classic', 'modern': 'Modern'}
LIGHT = {"id": "bulb", "color": "#FFD9A0", "intensity": 2.5, "range_m": 6, "on": "always", "power_w": 12, "type": "point", "shadows": False, "requires_power": True}

# model, stub, name, description, kind (fabric | wood | rug), weight kg, price, extras  (extras: wall, support (deck height), light (bulb height m), watts)
PIECES = [
    ('office_desk', 'desk', 'Writing Desk', 'A writing desk with a drawer pedestal.', 'wood', 32, 340, {'support': '0.76'}),
    ('executive_desk', 'executive_desk', 'Executive Desk', 'A large desk with two drawer pedestals and a modesty panel.', 'wood', 64, 780, {'support': '0.78'}),
    ('credenza', 'credenza', 'Credenza', 'A credenza with drawers and doors.', 'wood', 44, 460, {'support': '0.76'}),
    ('filing_cabinet', 'filing_cabinet', 'Filing Cabinet', 'A two-drawer filing cabinet.', 'wood', 24, 190, {'support': '0.72'}),
    ('lateral_file', 'lateral_file', 'Lateral File', 'A wide two-drawer lateral filing cabinet.', 'wood', 30, 260, {'support': '0.70'}),
    ('whiteboard_wall', 'whiteboard', 'Whiteboard', 'A framed whiteboard with a marker tray. Mount it on a wall.', 'wood', 8, 95, {'wall': True}),
    ('corkboard_wall', 'corkboard', 'Cork Board', 'A framed cork board with pinned notes. Mount it on a wall.', 'wood', 4, 60, {'wall': True}),
    ('office_chair', 'office_chair', 'Office Chair', 'A swivel office chair on a five-star base.', 'fabric', 12, 260, {}),
    ('guest_chair', 'guest_chair', 'Guest Chair', 'An upholstered chair for visitors.', 'fabric', 7, 150, {}),
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
                out.append(dict(model=model, style=style, kind=kind, color=ck, id='office_%s_%s_%s' % (stub, style, ck),
                                name='%s %s %s' % (STYLE_LABEL[style], clabel, name), desc='%s %s' % (desc, STYLE_NOTE[style]),
                                kg=kg, price=round(price * PRICE_FACTOR[style]), extras=ex, label=clabel))
    return out


def manifest(v, tris, dims):
    """The item manifest, plus its storage (closed container and / or shelf decks) from tools/furniture_storage.py."""
    import furniture_storage
    man = _manifest(v, tris, dims)
    furniture_storage.apply(man, 'office', v['model'], v.get('style'))
    import short_names
    short_names.apply(man)   # the short display names (tools/short_names.py)
    return man


def _manifest(v, tris, dims):
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
        'id': v['id'], 'name': v['name'], 'category': 'office', 'description': v['desc'], 'icon': v['id'] + '.png',
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
        'category_fields': {'dimensions_m': {'width': round(w, 3), 'depth': round(d, 3), 'height': round(h, 3)}, 'office_kind': v['model'], 'style': v['style'],
                            'color': v['color'], 'power_draw_w': watts},
    }
    if 'light' in ex:
        man['lights'] = [dict(LIGHT, offset_m=[0, ex['light'], 0])]
    return man


def readme(v, tris, dims):
    w, d, h = dims
    return ('# %s\n\n%s\n\nProcedural model (tools/make_office_assets.py, tools/office_models.py), %d triangles, %.2f x %.2f x %.2f m (W x D x H).%s\n'
            % (v['name'], v['desc'], tris, w, d, h, ' A wall item: mount it on a wall.' if v['extras'].get('wall') else ''))


def build_all(only):
    sys.path.insert(0, TOOLS)
    import kitchen_lib as L
    import living_lib as LL
    import office_models as M
    built = 0
    for v in variants():
        if only and v['model'] not in only:
            continue
        L.reset_scene()
        P = LL.Palette(v['style'], v['kind'], v['color'])
        obj = getattr(M, v['model'])(P).build()
        lo, hi = L.bounds(obj)
        dims = (hi.x - lo.x, hi.y - lo.y, hi.z - lo.z)
        folder = os.path.join(OFFICE, v['id'])
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
    print('OFFICE: %d items' % built)


def make_icons(workers=4):
    from concurrent.futures import ThreadPoolExecutor
    force = '--force' in sys.argv
    jobs = []
    for v in variants():
        folder = os.path.join(OFFICE, v['id'])
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
