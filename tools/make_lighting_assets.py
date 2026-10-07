"""
Builds the LIGHTING pack (assets/lighting/<id>/) in headless Blender: ceiling, wall (inside and outside) and outdoor post lights, each in a classic and a modern style and four metal finishes.
16 pieces x 2 styles x 4 finishes = 128 items. A category of its own; the older building_light_* items are untouched.

    blender --background --python tools/make_lighting_assets.py                 (every item; or: -- chandelier bollard)
    python tools/make_lighting_assets.py --icons [--force]                       (outside Blender: the 128 px icons)

Ceiling lights hang from the ceiling (attach_surface ceiling), wall lights mount inside or outside (attach_surface wall, attach_side), post lights stand on the ground. Light
offsets are [x, y up, z out from the wall] (a ceiling piece's y is measured from its lowest point). Models: tools/lighting_models.py.
Afterwards: python tools/make_lighting_assets.py --icons ; python tools/generate_unity_asset_catalog.py ; python tools/package_catalog_as_mods.py
"""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'assets', 'lighting')
TOOLS = os.path.join(ROOT, 'tools')
STYLES = ('classic', 'modern')
STYLE_LABEL = {'classic': 'Classic', 'modern': 'Modern'}
FINISH = {'classic': [('brass', 'Antique Brass', 1.15), ('bronze', 'Oiled Bronze', 1.1), ('black', 'Black Iron', 1.0), ('white', 'White', 0.95)],
          'modern': [('chrome', 'Chrome', 1.15), ('black', 'Matte Black', 1.0), ('nickel', 'Brushed Nickel', 1.1), ('white', 'White', 0.95)]}

# model, stub, name, description, mount (ceiling | wall_in | wall_out | ground), kg, price, watts, fan, intensity, range, {style: [light offsets]}
PIECES = [
    ('ceiling_flush', 'flush', 'Flush-Mount Ceiling Light', 'A flush-mount ceiling light with a frosted glass shade.', 'ceiling', 1.6, 58, 14, 0, 3.4, 8, {'classic': [(0, -0.10, 0)], 'modern': [(0, -0.10, 0)]}),
    ('ceiling_pendant', 'pendant', 'Pendant Light', 'A pendant light hanging on a cord from the ceiling.', 'ceiling', 1.8, 78, 14, 0, 3.2, 8, {'classic': [(0, 0.05, 0)], 'modern': [(0, 0.17, 0)]}),
    ('chandelier', 'chandelier', 'Chandelier', 'A chandelier for a dining room or a hall.', 'ceiling', 6.5, 320, 60, 0, 4.4, 10, {'classic': [(0, 0.30, 0)], 'modern': [(0, 0.10, 0)]}),
    ('ceiling_fan', 'ceiling_fan', 'Ceiling Fan With Light', 'A five-blade ceiling fan with a light kit.', 'ceiling', 7.5, 210, 75, 0, 3.0, 8, {'classic': [(0, -0.05, 0)], 'modern': [(0, -0.05, 0)]}),
    ('track_light', 'track', 'Track Light', 'A track with three adjustable spot heads.', 'ceiling', 2.4, 120, 24, 0, 2.2, 7, {'classic': [(-0.34, -0.08, -0.04), (0, -0.08, -0.04), (0.34, -0.08, -0.04)], 'modern': [(-0.34, -0.08, -0.04), (0, -0.08, -0.04), (0.34, -0.08, -0.04)]}),
    ('wall_sconce', 'sconce', 'Wall Sconce', 'A wall sconce for a hall or a bedroom. Mount it inside.', 'wall_in', 1.0, 52, 10, 0, 2.6, 7, {'classic': [(0, 0.22, 0.13)], 'modern': [(0, 0.20, 0.13)]}),
    ('vanity_bar', 'vanity_bar', 'Vanity Light Bar', 'A three-light vanity bar to go over a mirror. Mount it inside.', 'wall_in', 1.8, 88, 30, 0, 3.0, 7, {'classic': [(0, 0.07, 0.12)], 'modern': [(0, 0.05, 0.10)]}),
    ('picture_light', 'picture_light', 'Picture Light', 'A slim light to hang over a picture or a mirror. Mount it inside.', 'wall_in', 0.7, 42, 8, 0, 1.8, 4, {'classic': [(0, 0.05, 0.17)], 'modern': [(0, 0.05, 0.17)]}),
    ('swing_arm', 'swing_arm', 'Swing-Arm Wall Lamp', 'A reading lamp on a swing arm. Mount it inside.', 'wall_in', 1.4, 68, 10, 0, 2.8, 7, {'classic': [(0, 0.12, 0.52)], 'modern': [(0, 0.12, 0.52)]}),
    ('wall_lantern', 'wall_lantern', 'Exterior Wall Lantern', 'An exterior wall lantern, on from dusk to dawn. Mount it outside.', 'wall_out', 1.6, 64, 12, 0, 3.6, 10, {'classic': [(0, 0.20, 0.14), ], 'modern': [(0, 0.19, 0.10)]}),
    ('barn_light', 'barn_light', 'Barn Light', 'A gooseneck barn light with a wide shade, on from dusk to dawn. Mount it outside.', 'wall_out', 2.2, 85, 20, 0, 4.0, 11, {'classic': [(0, 0.03, 0.38)], 'modern': [(0, 0.03, 0.38)]}),
    ('flood_light', 'flood_light', 'Security Flood Light', 'A bright flood light, on from dusk to dawn. Mount it outside.', 'wall_out', 1.9, 72, 30, 0, 5.0, 14, {'classic': [(0, 0.10, 0.22)], 'modern': [(0, 0.10, 0.22)]}),
    ('post_lamp', 'post_lamp', 'Garden Post Lamp', 'A tall garden lamp post, on from dusk to dawn.', 'ground', 14, 240, 15, 0, 4.0, 12, {'classic': [(0, 1.87, 0)], 'modern': [(0, 2.08, 0)]}),
    ('pole_light', 'pole_light', 'Yard Pole Light', 'A tall pole light that floods the yard, on from dusk to dawn.', 'ground', 28, 340, 40, 0, 6.0, 16, {'classic': [(0.60, 3.50, 0)], 'modern': [(0.55, 3.62, 0)]}),
    ('bollard', 'bollard', 'Garden Bollard Light', 'A waist-high bollard light for a path or a drive, on from dusk to dawn.', 'ground', 6, 120, 8, 0, 2.0, 5, {'classic': [(0, 0.58, 0)], 'modern': [(0, 0.75, 0)]}),
    ('path_light', 'path_light', 'Path Light', 'A small stake light for edging a path, on from dusk to dawn.', 'ground', 1.2, 36, 4, 0, 1.4, 4, {'classic': [(0, 0.34, 0)], 'modern': [(0, 0.40, 0)]}),
]
STYLE_NOTE = {'classic': 'Classic styling.', 'modern': 'Modern styling.'}


def variants():
    out = []
    for model, stub, name, desc, mount, kg, price, watts, fan, inten, rng, lights in PIECES:
        for style in STYLES:
            for fk, flabel, factor in FINISH[style]:
                out.append(dict(model=model, style=style, finish=fk, id='lighting_%s_%s_%s' % (stub, style, fk), mount=mount,
                                name='%s %s %s' % (STYLE_LABEL[style], flabel, name), desc='%s %s' % (desc, STYLE_NOTE[style]),
                                kg=kg, price=round(price * factor * (1.12 if style == 'classic' else 1.0)), watts=watts, inten=inten, rng=rng, lights=lights[style]))
    return out


def manifest(v, tris, dims):
    w, d, h = dims
    mount = v['mount']
    props = {
        'weight_kg': float(v['kg']), 'max_stack_size': 1, 'base_value': int(v['price']), 'is_consumable': False,
        'footprint': '%.2fm W x %.2fm D x %.2fm H' % (w, d, h),
        'happiness_modifier': 0, 'thirst_restore': 0, 'energy_restore': 0, 'stamina_restore': 0, 'wellness_modifier': 0,
        'placeable': mount == 'ground', 'wrench_remove': True, 'is_buyable': True, 'stores': ['voltvision'], 'sale_unit': 'ea',
    }
    if mount == 'ceiling':
        props['attach_surface'], props['attach_side'] = 'ceiling', 'interior'
    elif mount in ('wall_in', 'wall_out'):
        props['attach_surface'], props['attach_side'] = 'wall', 'interior' if mount == 'wall_in' else 'exterior'
    night = mount in ('wall_out', 'ground')
    per = max(1, round(v['watts'] / len(v['lights']))) if v['model'] != 'ceiling_fan' else 15
    lights = [{'id': 'lamp%d' % (i + 1) if len(v['lights']) > 1 else 'lamp', 'color': '#FFD9A0' if night else '#FFE6B8', 'intensity': v['inten'], 'range_m': float(v['rng']),
               'offset_m': [x, y, z], 'on': 'night' if night else 'always', 'power_w': per, 'type': 'point', 'shadows': False, 'requires_power': True}
              for i, (x, y, z) in enumerate(v['lights'])]
    watts = v['watts']
    return {
        '$schema': 'https://homesteader.game/schemas/item_v1.json',
        'id': v['id'], 'name': v['name'], 'category': 'lighting', 'description': v['desc'], 'icon': v['id'] + '.png',
        'properties': props,
        'models': [{'file': v['id'] + '.glb', 'format': 'glb', 'dimensions_m': {'x': round(w, 3), 'y': round(h, 3), 'z': round(d, 3)}, 'triangles': int(tris)}],
        'lights': lights,
        'utilities': {
            'water': {'metric': 'None (unplumbed / dry)', 'details': 'None (unplumbed / dry)'},
            'electricity': {'metric': '%d W' % watts, 'details': 'Draws about %d W while it is on.' % watts},
            'sewage': {'metric': 'None (no waste discharge)', 'details': 'None (no waste discharge)'},
            'battery': {'metric': 'None (no internal battery)', 'details': 'None (no internal battery)'},
            'internet': {'metric': 'None (offline / non-networked)', 'details': 'None (offline / non-networked)'},
        },
        'growth': {'is_growable': False, 'growth_type': None, 'species': None, 'max_age': None, 'time_unit': None, 'total_stages': 0, 'current_stage': None, 'stages': []},
        'plugin_metadata': {'version': '1.0.0', 'author': 'Homesteader Core', 'compatible_api': 'v1'},
        'category_fields': {'dimensions_m': {'width': round(w, 3), 'depth': round(d, 3), 'height': round(h, 3)}, 'lighting_kind': v['model'], 'style': v['style'],
                            'finish': v['finish'], 'mount': mount, 'power_draw_w': watts},
    }


def readme(v, tris, dims):
    w, d, h = dims
    where = {'ceiling': 'Hangs from the ceiling of a finished building.', 'wall_in': 'Mounts on an inside wall.', 'wall_out': 'Mounts on an outside wall.', 'ground': 'Stands on the ground.'}[v['mount']]
    nl = chr(10)
    return '# %s' % v['name'] + nl + nl + '%s %s' % (v['desc'], where) + nl + nl + 'Procedural model (tools/make_lighting_assets.py, tools/lighting_models.py), %d triangles, %.2f x %.2f x %.2f m (W x D x H).' % (tris, w, d, h) + nl


def build_all(only):
    sys.path.insert(0, TOOLS)
    import kitchen_lib as L
    import lighting_models as M
    built = 0
    for v in variants():
        if only and v['model'] not in only:
            continue
        L.reset_scene()
        obj = getattr(M, v['model'])(M.Lamp(v['style'], v['finish'])).build()
        lo, hi = L.bounds(obj)
        dy = -hi.y if v['mount'] in ('wall_in', 'wall_out') else 0.0          # a wall piece: its back is the plane y = 0
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
    print('LIGHTING: %d items' % built)


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
