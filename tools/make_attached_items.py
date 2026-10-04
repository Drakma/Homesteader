"""
Builds the ATTACHED assets in headless Blender: things that mount on a building's wall or ceiling (see docs/ATTACHED_ITEMS.md).

  electricity_panel_breaker_subpanel   the outdoor breaker box (its model is rebuilt wall-ready: 0.40 x 0.60 x 0.15 m, as its manifest says);
                                       mounted on the OUTSIDE of a building it brings electricity to it
  electricity_light_sconce_interior    a wall sconce for rooms (on while the building has power)
  electricity_light_sconce_exterior    a wall lantern for the outside (on from dusk to dawn while the building has power)
  electricity_light_ceiling_flush      a flush dome ceiling light
  electricity_light_ceiling_pendant    a pendant ceiling light

Model convention (matches the game's GLB loading): the BACK of a wall item is the plane y = 0 and it sticks out towards -y (front = -y, which is +z
in the game: measured, the model occupies z = 0 .. +depth), bottom at z = 0, centred on x. A ceiling item hangs from its TOP: z = 0 is the lowest point, the top (touching the ceiling) is its height.
The manifests (properties.attach_surface / attach_side / provides_power and "lights") are written here too. The icon is rendered afterwards:

    python tools/render_icon_from_model.py <glb> <png>

    blender --background --python tools/make_attached_items.py
"""
import copy
import json
import math
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_structure_stages as base  # noqa: E402

ROOT = base.ROOT
ELEC = os.path.join(ROOT, 'assets', 'electricity')
TEMPLATE = 'electricity_panel_breaker_subpanel'


def reset():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)


def export(b, folder, item_id):
    obj = b.finish()
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    out = os.path.join(folder, item_id + '.glb')
    bpy.ops.export_scene.gltf(filepath=out, export_format='GLB', use_selection=True, export_yup=True)
    tris = sum(len(p.vertices) - 2 for p in obj.data.polygons)
    mn = [min(v.co[i] for v in obj.data.vertices) for i in range(3)]
    mx = [max(v.co[i] for v in obj.data.vertices) for i in range(3)]
    return tris, (mx[0] - mn[0], mx[2] - mn[2], mx[1] - mn[1])   # width, height, depth


# ------------------------------------------------------------------ the models

def breaker_panel():
    b = base.Builder('electricity_panel_breaker_subpanel')
    body = base.material('PanelBody', (0.5, 0.53, 0.57), 0.45)
    door = base.material('PanelDoor', (0.6, 0.63, 0.66), 0.4)
    dark = base.material('PanelDark', (0.12, 0.12, 0.13), 0.6)
    label = base.material('PanelLabel', (0.92, 0.9, 0.8), 0.8)
    red = base.material('PanelMain', (0.75, 0.12, 0.1), 0.5)
    w, h, d = 0.40, 0.60, 0.15
    b.box(-w / 2, w / 2, -d, 0.0, 0.0, h, body)                               # the enclosure
    b.box(-w / 2 + 0.02, w / 2 - 0.02, -d - 0.012, -d, 0.025, h - 0.025, door)   # the hinged door, proud of the box
    b.box(-w / 2 + 0.005, -w / 2 + 0.02, -d - 0.02, -d + 0.005, 0.07, 0.13, dark)    # hinges
    b.box(-w / 2 + 0.005, -w / 2 + 0.02, -d - 0.02, -d + 0.005, h - 0.13, h - 0.07, dark)
    b.box(w / 2 - 0.075, w / 2 - 0.045, -d - 0.035, -d - 0.012, h / 2 - 0.04, h / 2 + 0.04, dark)   # the latch handle
    b.box(-0.09, 0.09, -d - 0.016, -d - 0.012, h - 0.12, h - 0.06, label)      # the circuit label
    b.box(-0.03, 0.03, -d - 0.02, -d - 0.012, h - 0.19, h - 0.15, red)         # the main breaker mark
    b.log((0.0, -d / 2, 0.0), (0.0, -d / 2, -0.07), 0.025, dark, sides=8)       # a conduit stub out of the bottom
    return b, (w, h, d)


def sconce_interior():
    b = base.Builder('electricity_light_sconce_interior')
    brass = base.material('SconceBrass', (0.72, 0.56, 0.28), 0.35)
    shade = base.material('SconceShade', (0.98, 0.94, 0.82), 0.8)
    b.box(-0.045, 0.045, -0.015, 0.0, 0.0, 0.17, brass)                        # the back plate
    b.box(-0.012, 0.012, -0.06, -0.015, 0.05, 0.075, brass)                    # the arm out from the plate
    b.box(-0.05, 0.05, -0.15, -0.045, 0.045, 0.2, shade)                       # the frosted shade, a small box
    b.box(-0.055, 0.055, -0.155, -0.04, 0.04, 0.05, brass)                     # its lower cap
    b.box(-0.055, 0.055, -0.155, -0.04, 0.195, 0.21, brass)                    # and its top cap
    return b, (0.11, 0.21, 0.155)


def sconce_exterior():
    b = base.Builder('electricity_light_sconce_exterior')
    black = base.material('LanternBlack', (0.08, 0.08, 0.09), 0.5)
    glass = base.material('LanternGlass', (0.96, 0.93, 0.8), 0.7)
    b.box(-0.05, 0.05, -0.02, 0.0, 0.0, 0.26, black)                           # the back plate
    b.box(-0.015, 0.015, -0.1, -0.02, 0.09, 0.11, black)                       # the bracket
    b.box(-0.065, 0.065, -0.2, -0.055, 0.03, 0.04, black)                      # the lantern base
    b.box(-0.05, 0.05, -0.19, -0.065, 0.04, 0.24, glass)                       # the glass
    for x in (-0.055, 0.055):
        for y in (-0.06, -0.19):
            b.box(x - 0.006, x + 0.006, y - 0.006, y + 0.006, 0.04, 0.24, black)   # the cage corners
    b.box(-0.07, 0.07, -0.2, -0.05, 0.24, 0.255, black)                        # the roof
    b.box(-0.04, 0.04, -0.17, -0.08, 0.255, 0.285, black)                      # the cap
    return b, (0.14, 0.285, 0.2)


def ceiling_flush():
    b = base.Builder('electricity_light_ceiling_flush')
    white = base.material('FlushWhite', (0.93, 0.93, 0.9), 0.6)
    trim = base.material('FlushTrim', (0.72, 0.72, 0.7), 0.4)
    shade = base.material('FlushShade', (0.98, 0.95, 0.85), 0.8)
    h = 0.08
    b.log((0.0, 0.0, 0.0), (0.0, 0.0, 0.012), 0.17, trim, sides=14)             # the trim ring (lowest)
    b.log((0.0, 0.0, 0.012), (0.0, 0.0, h - 0.015), 0.155, shade, sides=14)     # the frosted dome
    b.log((0.0, 0.0, h - 0.015), (0.0, 0.0, h), 0.12, white, sides=14)          # the canopy on the ceiling
    return b, (0.34, h, 0.34)


def ceiling_pendant():
    b = base.Builder('electricity_light_ceiling_pendant')
    white = base.material('PendantCanopy', (0.9, 0.9, 0.88), 0.5)
    cord = base.material('PendantCord', (0.1, 0.1, 0.11), 0.7)
    shade = base.material('PendantShade', (0.2, 0.34, 0.3), 0.55)
    inner = base.material('PendantInner', (0.98, 0.95, 0.85), 0.8)
    h = 0.75
    b.log((0.0, 0.0, 0.0), (0.0, 0.0, 0.04), 0.17, inner, sides=12)             # the bulb glow under the shade
    b.log((0.0, 0.0, 0.04), (0.0, 0.0, 0.26), 0.17, shade, sides=12)            # the drum shade
    b.log((0.0, 0.0, 0.26), (0.0, 0.0, 0.265), 0.04, white, sides=8)            # the cap
    b.log((0.0, 0.0, 0.265), (0.0, 0.0, h - 0.025), 0.007, cord, sides=5)       # the cord
    b.log((0.0, 0.0, h - 0.025), (0.0, 0.0, h), 0.06, white, sides=10)          # the canopy on the ceiling
    return b, (0.34, h, 0.34)


def fluorescent(n_bulbs):
    """A 1.2 m fluorescent fixture with n_bulbs tubes side by side under a white reflector, hung from the ceiling."""
    b = base.Builder('electricity_light_fluorescent_%dbulb' % n_bulbs)
    white = base.material('FixtureWhite', (0.93, 0.94, 0.95), 0.45)
    grey = base.material('FixtureGrey', (0.55, 0.57, 0.6), 0.5)
    tube = base.material('TubeWhite', (0.99, 1.0, 1.0), 0.15)
    pitch = 0.075
    width = n_bulbs * pitch + 0.03
    length = 1.2
    h = 0.075
    b.box(-length / 2, length / 2, -width / 2, width / 2, 0.035, h, white)                      # the reflector body on the ceiling
    for i in range(n_bulbs):
        y = (i - (n_bulbs - 1) / 2.0) * pitch
        b.log((-length / 2 + 0.05, y, 0.0185), (length / 2 - 0.05, y, 0.0185), 0.0185, tube, sides=8)   # a tube
        for x in (-length / 2 + 0.03, length / 2 - 0.03):
            b.box(x - 0.02, x + 0.02, y - 0.02, y + 0.02, 0.0, 0.037, grey)                      # its lamp holders
    b.box(-length / 2, -length / 2 + 0.012, -width / 2, width / 2, 0.0, h, white)               # end plates
    b.box(length / 2 - 0.012, length / 2, -width / 2, width / 2, 0.0, h, white)
    return b, (length, h, width)


# ------------------------------------------------------------------ the items

LIGHT = dict(type='point', shadows=False, requires_power=True)

ITEMS = [
    dict(id='electricity_panel_breaker_subpanel', model=breaker_panel, name='Outdoor Breaker Subpanel', existing=True,
         desc='A weatherproof breaker box. Mount it on the OUTSIDE of a building (left click a wall with it in hand) to bring electricity to that building: its lights then work.',
         value=150, weight=12.0, attach=('wall', 'exterior'), provides_power=True, lights=None),
    dict(id='electricity_light_sconce_interior', model=sconce_interior, name='Wall Sconce', value=22, weight=0.6, attach=('wall', 'interior'),
         desc='A small wall light for a room. Mount it on an inside wall; it lights while the building has power (a breaker box on the outside).',
         lights=[dict(id='lamp', color='#FFE2B0', intensity=3.0, range_m=7.0, offset_m=[0.0, 0.14, 0.12], on='always', power_w=9, **LIGHT)]),
    dict(id='electricity_light_sconce_exterior', model=sconce_exterior, name='Exterior Wall Lantern', value=34, weight=1.1, attach=('wall', 'exterior'),
         desc='A weatherproof lantern for the outside of a building. It lights from dusk to dawn while the building has power (a breaker box on the outside).',
         lights=[dict(id='lamp', color='#FFD79A', intensity=3.6, range_m=10.0, offset_m=[0.0, 0.17, 0.14], on='night', power_w=12, **LIGHT)]),
    dict(id='electricity_light_ceiling_flush', model=ceiling_flush, name='Flush Ceiling Light', value=26, weight=0.8, attach=('ceiling', 'interior'),
         desc='A round dome light that sits flat on the ceiling. Mount it inside a building; it lights while the building has power (a breaker box on the outside).',
         lights=[dict(id='lamp', color='#FFF0D0', intensity=3.4, range_m=8.0, offset_m=[0.0, -0.12, 0.0], on='always', power_w=14, **LIGHT)]),
    dict(id='electricity_light_ceiling_pendant', model=ceiling_pendant, name='Pendant Ceiling Light', value=38, weight=1.0, attach=('ceiling', 'interior'),
         desc='A shaded light that hangs from the ceiling on a cord. Mount it inside a building; it lights while the building has power (a breaker box on the outside).',
         lights=[dict(id='lamp', color='#FFE6B8', intensity=3.2, range_m=8.0, offset_m=[0.0, 0.06, 0.0], on='always', power_w=14, **LIGHT)]),
    dict(id='electricity_light_fluorescent_2bulb', model=lambda: fluorescent(2), name='Fluorescent Light (2 Bulb)', value=45, weight=2.5, attach=('ceiling', 'interior'),
         desc='A 2-tube fluorescent fixture: a bright white light with a wide, deep throw that sputters for a few seconds when it comes on. Mount it inside a building; it lights while the building has power (a breaker box on the outside).',
         lights=[dict(id='tube1', color='#F2F7FF', intensity=7.0, range_m=16.0, offset_m=[-0.3, -0.14, 0.0], on='always', power_w=32, flicker=0.05, startup_flicker=0.85, startup_seconds=3.0, min_level=0.2, **LIGHT),
                 dict(id='tube2', color='#F2F7FF', intensity=7.0, range_m=16.0, offset_m=[0.3, -0.14, 0.0], on='always', power_w=32, flicker=0.05, startup_flicker=0.85, startup_seconds=3.0, min_level=0.2, **LIGHT)]),
    dict(id='electricity_light_fluorescent_4bulb', model=lambda: fluorescent(4), name='Fluorescent Light (4 Bulb)', value=80, weight=4.0, attach=('ceiling', 'interior'),
         desc='A 4-tube fluorescent fixture: a bright white light with a wide, deep throw that sputters for a few seconds when it comes on. Mount it inside a building; it lights while the building has power (a breaker box on the outside).',
         lights=[dict(id='tube1', color='#F2F7FF', intensity=8.0, range_m=20.0, offset_m=[-0.3, -0.14, 0.0], on='always', power_w=64, flicker=0.05, startup_flicker=0.85, startup_seconds=3.0, min_level=0.2, **LIGHT),
                 dict(id='tube2', color='#F2F7FF', intensity=8.0, range_m=20.0, offset_m=[0.3, -0.14, 0.0], on='always', power_w=64, flicker=0.05, startup_flicker=0.85, startup_seconds=3.0, min_level=0.2, **LIGHT)]),
    dict(id='electricity_light_fluorescent_8bulb', model=lambda: fluorescent(8), name='Fluorescent Light (8 Bulb)', value=140, weight=7.0, attach=('ceiling', 'interior'),
         desc='A 8-tube fluorescent fixture: a bright white light with a wide, deep throw that sputters for a few seconds when it comes on. Mount it inside a building; it lights while the building has power (a breaker box on the outside).',
         lights=[dict(id='tube1', color='#F2F7FF', intensity=8.0, range_m=24.0, offset_m=[-0.3, -0.14, -0.15], on='always', power_w=64, flicker=0.05, startup_flicker=0.85, startup_seconds=3.0, min_level=0.2, **LIGHT),
                 dict(id='tube2', color='#F2F7FF', intensity=8.0, range_m=24.0, offset_m=[0.3, -0.14, -0.15], on='always', power_w=64, flicker=0.05, startup_flicker=0.85, startup_seconds=3.0, min_level=0.2, **LIGHT),
                 dict(id='tube3', color='#F2F7FF', intensity=8.0, range_m=24.0, offset_m=[-0.3, -0.14, 0.15], on='always', power_w=64, flicker=0.05, startup_flicker=0.85, startup_seconds=3.0, min_level=0.2, **LIGHT),
                 dict(id='tube4', color='#F2F7FF', intensity=8.0, range_m=24.0, offset_m=[0.3, -0.14, 0.15], on='always', power_w=64, flicker=0.05, startup_flicker=0.85, startup_seconds=3.0, min_level=0.2, **LIGHT)]),
]


def write_item(spec, folder, tris, dims):
    item_id = spec['id']
    mpath = os.path.join(folder, item_id + '.json')
    if os.path.exists(mpath):
        m = json.load(open(mpath, encoding='utf-8'))
    else:
        m = copy.deepcopy(json.load(open(os.path.join(ELEC, TEMPLATE, TEMPLATE + '.json'), encoding='utf-8')))
        m['id'] = item_id
        m['icon'] = item_id + '.png'
    m['name'] = spec['name']
    m['description'] = spec['desc']
    p = m['properties']
    surface, side = spec['attach']
    p.update({'weight_kg': spec['weight'], 'max_stack_size': 10, 'base_value': spec['value'], 'is_buyable': True, 'stores': ['voltvision'],
              'sale_unit': 'ea', 'placeable': False, 'attach_surface': surface, 'attach_side': side})
    if spec.get('provides_power'):
        p['provides_power'] = True
    else:
        p.pop('provides_power', None)
    w, h, d = dims
    p['footprint'] = '%.2fm W x %.2fm D x %.2fm H' % (w, d, h)
    m['models'] = [{'file': item_id + '.glb', 'format': 'glb', 'dimensions_m': {'x': round(w, 3), 'y': round(h, 3), 'z': round(d, 3)}, 'triangles': tris}]
    if spec.get('lights'):
        m['lights'] = spec['lights']
    else:
        m.pop('lights', None)
    cf = m.setdefault('category_fields', {})
    cf['dimensions_m'] = {'width': round(w, 3), 'depth': round(d, 3), 'height': round(h, 3)}
    cf['fuel_type'] = 'none'
    cf['fuel_consumption_l_per_min'] = 0
    cf['max_power_w'] = 40000 if spec.get('provides_power') else 0
    cf['tank_capacity_l'] = 0
    json.dump(m, open(mpath, 'w', encoding='utf-8'), indent=2)
    readme = '# %s\n\n**Item ID:** `%s`  \n**Category:** `electricity`  \n**Icon:** ![%s](%s.png)\n\n%s\n\nMounts on a %s (%s side). See docs/ATTACHED_ITEMS.md.\n' % (
        spec['name'], item_id, spec['name'], item_id, spec['desc'], surface, side)
    open(os.path.join(folder, 'README.md'), 'w', encoding='utf-8').write(readme)


def main():
    argv = sys.argv
    only = argv[argv.index('--') + 1:] if '--' in argv else None
    for spec in ITEMS:
        if only and spec['id'] not in only:
            continue
        reset()
        folder = os.path.join(ELEC, spec['id'])
        os.makedirs(folder, exist_ok=True)
        b, dims = spec['model']()
        tris, measured = export(b, folder, spec['id'])
        # the old model of the outdoor panel was a differently shaped box under another file name: the manifest now points at the new one
        if spec.get('existing'):
            for fn in ('panel_breaker_subpanel.glb', 'panel_breaker_subpanel.obj', 'panel_breaker_subpanel.mtl'):
                old = os.path.join(folder, fn)
                if os.path.exists(old):
                    os.remove(old)
        write_item(spec, folder, tris, dims)
        print('item', spec['id'], tris, 'tris', [round(x, 3) for x in measured])


if __name__ == '__main__':
    main()
