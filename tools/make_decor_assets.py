"""
Builds the DECOR pack (assets/decor/<id>/) in headless Blender: curtains and drapes (four fabric colours) and house plants (four pot colours), each in a classic and a modern style.
(2 + 6) pieces x 2 styles x 4 colours = 64 items. A category of its own.

    blender --background --python tools/make_decor_assets.py                 (every item; or: -- curtains)
    python tools/make_decor_assets.py --icons [--force]                       (outside Blender: the 128 px icons)

Curtains and drapes mount on an inside wall (attach_surface wall, attach_side interior), like a wall light: the click sets the height of the HEM (a curtain's bottom, a drape's floor).
Plants stand on the floor (placeable; the small succulent fits a shelf) and the hanging fern hangs from the ceiling (attach_surface ceiling).
Models: tools/decor_models.py (curtains), tools/decor_plants.py (plants). Colours: the living room fabrics (tools/living_colors.py), the pot colours (decor_plants.POT_RGB).
Afterwards: python tools/make_decor_assets.py --icons ; python tools/generate_unity_asset_catalog.py ; python tools/package_catalog_as_mods.py
"""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'assets', 'decor')
TOOLS = os.path.join(ROOT, 'tools')
STYLES = ('classic', 'modern')
STYLE_LABEL = {'classic': 'Classic', 'modern': 'Modern'}
sys.path.insert(0, TOOLS)

# model, stub, name, description, kg, price, mount (wall | floor | ceiling), models module
PLANTS = [
    ('fig', 'fig', 'Fiddle-Leaf Fig', 'A tall fiddle-leaf fig in a pot, for a corner of a living room.', 9.0, 85, 'floor'),
    ('palm', 'palm', 'Parlor Palm', 'A bushy parlor palm with arching fronds, in a pot.', 8.0, 72, 'floor'),
    ('snake', 'snake', 'Snake Plant', 'A snake plant with stiff upright leaves, in a pot.', 4.5, 38, 'floor'),
    ('monstera', 'monstera', 'Monstera', 'A monstera with big split leaves, in a pot.', 8.5, 78, 'floor'),
    ('succulent', 'succulent', 'Succulent Pot', 'A small succulent in a pot, for a shelf or a table.', 0.8, 14, 'floor'),
    ('hanging_fern', 'fern', 'Hanging Fern', 'A hanging basket of fern. Mount it on a ceiling inside.', 3.5, 44, 'ceiling'),
]
PIECES = [
    ('curtains', 'curtains', 'Curtains', 'A pair of sill-length curtains on a rod, open at the sides. Mount it on an inside wall above a window: the click sets the bottom hem.', 2.4, 58, 'wall'),
    ('drapes', 'drapes', 'Drapes', 'A pair of heavy floor-length drapes, tied back at the sides, hung from a rod with a valance or a ceiling track. Mount it on an inside wall: the click sets the floor.', 6.5, 140, 'wall'),
]
STYLE_NOTE = {'classic': 'Classic styling, with a brass rod.', 'modern': 'Modern styling, with a matte black rail.'}
PLANT_NOTE = {'classic': 'Classic styling, in a tapered pot on a saucer.', 'modern': 'Modern styling, in a plain drum planter.'}


def variants():
    import living_colors as C
    import decor_colors as PL
    out = []
    for model, stub, name, desc, kg, price, mount in PIECES:
        for style in STYLES:
            for key, label, rgb in C.FABRICS[style]:
                out.append(dict(model=model, kind='curtain', mount=mount, style=style, color=key, rgb=rgb, id='decor_%s_%s_%s' % (stub, style, key),
                                name='%s %s %s' % (STYLE_LABEL[style], label, name), desc='%s %s' % (desc, STYLE_NOTE[style]),
                                kg=kg, price=round(price * (1.12 if style == 'classic' else 1.0))))
    for model, stub, name, desc, kg, price, mount in PLANTS:
        for style in STYLES:
            for key in PL.POT_RGB[style]:
                out.append(dict(model=model, kind='plant', mount=mount, style=style, color=key, rgb=PL.POT_RGB[style][key], id='decor_%s_%s_%s' % (stub, style, key),
                                name='%s %s Pot %s' % (STYLE_LABEL[style], key.title(), name), desc='%s %s' % (desc, PLANT_NOTE[style]),
                                kg=kg, price=round(price * (1.12 if style == 'classic' else 1.0))))
    return out


def manifest(v, tris, dims):
    w, d, h = dims
    props = {
        'weight_kg': float(v['kg']), 'max_stack_size': 1, 'base_value': int(v['price']), 'is_consumable': False,
        'footprint': '%.2fm W x %.2fm D x %.2fm H' % (w, d, h),
        'happiness_modifier': 1, 'thirst_restore': 0, 'energy_restore': 0, 'stamina_restore': 0, 'wellness_modifier': 0,
        'placeable': v['mount'] == 'floor', 'is_buyable': True, 'stores': ['furniture'], 'sale_unit': 'ea',
    }
    if v['mount'] == 'wall':
        props['attach_surface'], props['attach_side'] = 'wall', 'interior'
    elif v['mount'] == 'ceiling':
        props['attach_surface'], props['attach_side'] = 'ceiling', 'interior'
    return {
        '$schema': 'https://homesteader.game/schemas/item_v1.json',
        'id': v['id'], 'name': v['name'], 'category': 'decor', 'description': v['desc'], 'icon': v['id'] + '.png',
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
        'category_fields': {'dimensions_m': {'width': round(w, 3), 'depth': round(d, 3), 'height': round(h, 3)}, 'decor_kind': v['model'], 'style': v['style'],
                            'color': v['color'], 'mount': {'wall': 'wall_in', 'floor': 'floor', 'ceiling': 'ceiling'}[v['mount']]},
    }


def readme(v, tris, dims):
    w, d, h = dims
    nl = chr(10)
    return '# %s' % v['name'] + nl + nl + '%s' % v['desc'] + nl + nl + 'Procedural model (tools/make_decor_assets.py, tools/decor_models.py), %d triangles, %.2f x %.2f x %.2f m (W x D x H).' % (tris, w, d, h) + nl


def build_all(only):
    import kitchen_lib as L
    import decor_models as M
    import decor_plants as PM
    built = 0
    for v in variants():
        if only and v['model'] not in only:
            continue
        L.reset_scene()
        if v['kind'] == 'plant':
            obj = getattr(PM, v['model'])(PM.Pot(v['style'], v['color'])).build()
        else:
            obj = getattr(M, v['model'])(M.Deco(v['style'], v['color'], v['rgb'])).build()
        lo, hi = L.bounds(obj)
        dy = -hi.y if v['mount'] == 'wall' else 0.0                           # a wall piece: its back is the plane y = 0
        for vt in obj.data.vertices:
            vt.co.z -= lo.z
            vt.co.y += dy
        lo, hi = L.bounds(obj)
        dims = (hi.x - lo.x, hi.y - lo.y, hi.z - lo.z)
        folder = os.path.join(OUT, v['id'])
        os.makedirs(folder, exist_ok=True)
        L.export_glb(obj, os.path.join(folder, v['id'] + '.glb'))
        tris = obj['triangles']
        with open(os.path.join(folder, v['id'] + '.json'), 'w', encoding='utf-8', newline=chr(10)) as f:
            json.dump(manifest(v, tris, dims), f, indent=2, ensure_ascii=False)
            f.write(chr(10))
        with open(os.path.join(folder, 'README.md'), 'w', encoding='utf-8', newline=chr(10)) as f:
            f.write(readme(v, tris, dims))
        built += 1
        print('built', v['id'], tris, 'tris', '%.2f x %.2f x %.2f' % dims, 'zmin %.3f' % lo.z)
    print('DECOR: %d items' % built)


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
