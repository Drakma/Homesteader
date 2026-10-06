"""
Builds the ready-made building parts in headless Blender and writes their manifests (assets/building/<id>/): doors, windows, roof trusses and the two
bagged mixes. Free, local, low-poly, GLB with plain colour materials. Run the icons afterwards:

    blender --background --python tools/make_building_items.py
    python tools/render_icon_from_model.py assets/building/<id>/<id>.glb assets/building/<id>/<id>.png        (every item)
    python tools/generate_unity_asset_catalog.py ; python tools/package_catalog_as_mods.py

Pivot at the middle of the part's footprint with the bottom at z = 0, front = -Y. Dimensions are in the manifest (category_fields.dimensions_m).
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
BUILD = os.path.join(ROOT, 'assets', 'building')


def reset():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)


def timber():
    return base.material('Timber', (0.74, 0.58, 0.36), 0.85)


# ------------------------------------------------------------------ doors

def panel_door(name, w, h, thick, slab_rgb, panels_rgb, knob=True):
    b = base.Builder(name)
    slab = base.material('DoorSlab', slab_rgb, 0.7)
    panel = base.material('DoorPanel', panels_rgb, 0.65)
    metal = base.material('DoorHardware', (0.55, 0.5, 0.4), 0.35)
    b.box(-w / 2, w / 2, -thick / 2, thick / 2, 0.0, h, slab)
    # raised panels on both faces: two columns of two (a tall lower pair and a short upper pair)
    for fy in (-1, 1):
        y0, y1 = (-thick / 2 - 0.008, -thick / 2) if fy < 0 else (thick / 2, thick / 2 + 0.008)
        for cx in (-1, 1):
            x0, x1 = (0.07 * w + cx * 0.0, 0.46 * w) if cx > 0 else (-0.46 * w, -0.07 * w)
            b.box(x0, x1, y0, y1, 0.08 * h, 0.52 * h, panel)
            b.box(x0, x1, y0, y1, 0.58 * h, 0.92 * h, panel)
    if knob:
        for fy in (-1, 1):
            b.box(w / 2 - 0.1, w / 2 - 0.06, (-thick / 2 - 0.05) if fy < 0 else thick / 2, (-thick / 2) if fy < 0 else thick / 2 + 0.05, 0.98, 1.04, metal)
    for hz in (0.25, h / 2, h - 0.25):
        b.box(-w / 2 - 0.012, -w / 2 + 0.01, -thick / 2 - 0.006, thick / 2 + 0.006, hz - 0.07, hz + 0.07, metal)   # hinges
    return b


def exterior_door():
    return panel_door('building_door_exterior', 1.2, 2.3, 0.06, (0.45, 0.28, 0.16), (0.52, 0.33, 0.19))


def interior_door():
    return panel_door('building_door_interior', 0.9, 2.1, 0.04, (0.86, 0.82, 0.74), (0.9, 0.86, 0.78))


def barn_door():
    b = base.Builder('building_door_barn_sliding')
    board = base.material('BarnBoard', (0.55, 0.16, 0.12), 0.85)
    brace = base.material('BarnBrace', (0.93, 0.9, 0.82), 0.8)
    metal = base.material('Track', (0.25, 0.25, 0.27), 0.5)
    w, h, t = 1.8, 2.3, 0.05
    b.box(-w / 2, w / 2, -t / 2, t / 2, 0.0, h, board)
    for k in range(1, 6):    # board joints
        x = -w / 2 + w * k / 6
        b.box(x - 0.004, x + 0.004, -t / 2 - 0.004, -t / 2, 0.0, h, metal)
    for z0, z1 in ((0.05, 0.2), (h / 2 - 0.08, h / 2 + 0.08), (h - 0.2, h - 0.05)):
        b.box(-w / 2 + 0.05, w / 2 - 0.05, -t / 2 - 0.03, -t / 2, z0, z1, brace)    # the three rails
    b.log((-w / 2 + 0.1, -t / 2 - 0.02, 0.15), (w / 2 - 0.1, -t / 2 - 0.02, h - 0.15), 0.045, brace, sides=4)   # the diagonal brace
    b.box(-w / 2, w / 2, -0.03, 0.03, h + 0.04, h + 0.1, metal)                    # the hanger track
    for x in (-w * 0.35, w * 0.35):
        b.box(x - 0.04, x + 0.04, -0.03, 0.03, h - 0.04, h + 0.04, metal)         # the rollers
    return b


# ------------------------------------------------------------------ windows

def window(name, w, h, bars_v, bars_h, frame_rgb, rails=0):
    b = base.Builder(name)
    frame = base.material('Frame', frame_rgb, 0.6)
    t = 0.07
    f = 0.05
    b.box(-w / 2, w / 2, -t / 2, t / 2, 0.0, f, frame)
    b.box(-w / 2, w / 2, -t / 2, t / 2, h - f, h, frame)
    b.box(-w / 2, -w / 2 + f, -t / 2, t / 2, f, h - f, frame)
    b.box(w / 2 - f, w / 2, -t / 2, t / 2, f, h - f, frame)
    for i in range(1, bars_v + 1):                  # vertical muntins
        x = -w / 2 + w * i / (bars_v + 1)
        b.box(x - 0.01, x + 0.01, -t / 2 + 0.01, t / 2 - 0.01, f, h - f, frame)
    for j in range(1, bars_h + 1):
        z = h * j / (bars_h + 1)
        b.box(-w / 2 + f, w / 2 - f, -t / 2 + 0.01, t / 2 - 0.01, z - 0.01, z + 0.01, frame)
    b.box(-w / 2 - 0.03, w / 2 + 0.03, -t / 2 - 0.04, t / 2, -0.03, 0.0, frame)     # the sill
    glass = base.Builder(name + '_glass')
    glass.box(-w / 2 + f, w / 2 - f, -0.006, 0.006, f, h - f, base.glass_material())
    return b, glass


def double_hung():
    b, g = window('building_window_double_hung', 0.9, 1.4, 1, 1, (0.93, 0.92, 0.88))
    b.box(-0.45 + 0.05, 0.45 - 0.05, -0.045, 0.045, 0.7 - 0.025, 0.7 + 0.025, base.material('Frame', (0.93, 0.92, 0.88), 0.6))   # the meeting rail
    return b, g


def picture_window():
    return window('building_window_picture', 1.5, 1.2, 0, 0, (0.28, 0.3, 0.32))


def slider_window():
    b, g = window('building_window_slider', 1.2, 0.8, 1, 0, (0.93, 0.92, 0.88))
    return b, g


# ------------------------------------------------------------------ trusses

def truss(name, span, rise, depth=0.2):
    """A W-type roof truss: two rafters, the bottom chord, a king post and two webs. Drawn upright in the XZ plane, 2 x 4 lumber, centred on x."""
    b = base.Builder(name)
    wood = timber()
    r = 0.04
    # y is the thickness of the truss (the lumber's face width)
    ex = span / 2
    pts = {
        'L': (-ex, 0.0), 'R': (ex, 0.0), 'A': (0.0, rise),
        'LB': (-ex / 3, 0.0), 'RB': (ex / 3, 0.0),
        'LM': (-ex / 2, rise / 2), 'RM': (ex / 2, rise / 2),
    }

    def beam(a, c, w=0.09, d=0.04):
        (ax, az), (cx, cz) = pts[a], pts[c]
        b.log((ax, 0.0, az), (cx, 0.0, cz), 0.045, wood, sides=4)

    beam('L', 'A')
    beam('A', 'R')
    beam('L', 'R')
    beam('A', 'LB')
    beam('A', 'RB')
    beam('LM', 'LB')
    beam('RM', 'RB')
    b.box(-0.09, 0.09, -0.05, 0.05, 0.0, 0.07, base.material('Plate', (0.55, 0.55, 0.57), 0.5))        # the gusset plate at the heel (left)
    b.box(-0.09, 0.09, -0.05, 0.05, rise - 0.07, rise + 0.02, base.material('Plate', (0.55, 0.55, 0.57), 0.5))   # and at the peak
    return b


# ------------------------------------------------------------------ bags

def bag(name, w, h, d, body_rgb, band_rgb):
    b = base.Builder(name)
    paper = base.material('BagPaper', body_rgb, 0.9)
    band = base.material('BagLabel', band_rgb, 0.8)
    top = base.material('BagTop', (body_rgb[0] * 0.85, body_rgb[1] * 0.85, body_rgb[2] * 0.85), 0.9)
    b.box(-w / 2, w / 2, -d / 2, d / 2, 0.0, h * 0.92, paper)
    b.box(-w / 2 + 0.02, w / 2 - 0.02, -d / 2 + 0.015, d / 2 - 0.015, h * 0.92, h, top)                 # the folded top
    b.box(-w / 2 + 0.03, w / 2 - 0.03, -d / 2 - 0.004, -d / 2, h * 0.3, h * 0.7, band)                   # the label panel on the front
    return b


def mortar_bag():
    return bag('building_mortar_mix_bag', 0.42, 0.62, 0.14, (0.78, 0.72, 0.6), (0.16, 0.36, 0.55))


def concrete_bag():
    return bag('building_concrete_mix_bag', 0.45, 0.68, 0.15, (0.62, 0.62, 0.6), (0.85, 0.65, 0.12))


# ------------------------------------------------------------------ the table

ITEMS = [
    # id, name, description, builder, weight kg, stack, value, tags
    ('building_door_exterior', 'Exterior Door', 'A solid wood entry door, 1.2 m by 2.3 m, hung on three hinges.', exterior_door, 45.0, 4, 220, ['doors']),
    ('building_door_interior', 'Interior Door', 'A hollow-core panel door, 0.9 m by 2.1 m.', interior_door, 18.0, 6, 85, ['doors']),
    ('building_door_barn_sliding', 'Barn Door', 'A sliding barn door with a diagonal brace, hanger track and rollers.', barn_door, 70.0, 2, 290, ['doors']),
    ('building_window_double_hung', 'Double-Hung Window', 'A double-hung window, 0.9 m by 1.4 m, with a sill.', double_hung, 16.0, 6, 150, ['windows']),
    ('building_window_picture', 'Picture Window', 'A large fixed window, 1.5 m by 1.2 m.', picture_window, 24.0, 4, 210, ['windows']),
    ('building_window_slider', 'Sliding Window', 'A small sliding window, 1.2 m by 0.8 m.', slider_window, 11.0, 6, 115, ['windows']),
    ('building_truss_small', 'Small Roof Truss', 'A W-type roof truss for a 4 m span, 2x4 lumber with gusset plates.', lambda: truss('building_truss_small', 4.0, 1.2), 28.0, 10, 95, ['roof_trusses']),
    ('building_truss_medium', 'Medium Roof Truss', 'A W-type roof truss for a 6 m span, 2x4 lumber with gusset plates.', lambda: truss('building_truss_medium', 6.0, 1.8), 46.0, 10, 160, ['roof_trusses']),
    ('building_truss_large', 'Large Roof Truss', 'A W-type roof truss for an 8 m span, 2x4 lumber with gusset plates.', lambda: truss('building_truss_large', 8.0, 2.4), 70.0, 8, 250, ['roof_trusses']),
    ('building_mortar_mix_bag', 'Mortar Mix Bag', 'A 60 lb bag of dry mortar mix for laying brick, block and stone.', mortar_bag, 27.0, 20, 14, ['mortar']),
    ('building_concrete_mix_bag', 'Concrete Mix Bag', 'A 20 lb bag of ready-mix concrete: add water and pour.', concrete_bag, 9.0, 20, 12, ['mortar']),
]


def export(b, extra, folder, item_id):
    objs = [b.finish()] + ([extra.finish()] if extra is not None else [])
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    out = os.path.join(folder, item_id + '.glb')
    bpy.ops.export_scene.gltf(filepath=out, export_format='GLB', use_selection=True, export_yup=True)
    tris = sum(len(p.vertices) - 2 for o in objs for p in o.data.polygons)
    mn = [min(v.co[i] for o in objs for v in o.data.vertices) for i in range(3)]
    mx = [max(v.co[i] for o in objs for v in o.data.vertices) for i in range(3)]
    return tris, [round(mx[i] - mn[i], 3) for i in range(3)]


# Items listed above whose model, manifest and README are no longer built by this script (it would overwrite them).
# building_mortar_mix_bag: the sand bag's model (20lb_sand_bag) recoloured off-white and blue with a MORTAR MIX label, at 60 lb size.
# building_grout_bag (listed in make_building_items2.py): the same model in dark slate and green with a GROUT label, at 25 lb size.
# building_insulation_blown_bag (make_building_items2.py): a Meshy image-to-3D model (meshy-t2, smart-topology) of a plastic-wrapped bale.
# building_concrete_mix_bag: the same sand bag model in orange and charcoal with a CONCRETE MIX label, at 80 lb size.
# building_concrete_mix_pallet (make_building_packs.py): built by tools/make_bag_pallets.py from that bag. building_mortar_mix_pallet: retired
# (replaced by building_mortar_mix_bag_pallet_10 / _20 from make_bag_pallets.py).
# building_romex_14_2_spool, building_romex_10_3_spool (make_building_items2.py): built by tools/make_romex.py (coils and spools lying on their side).
HAND_MADE = {'building_mortar_mix_bag', 'building_grout_bag', 'building_insulation_blown_bag', 'building_concrete_mix_bag',
             'building_concrete_mix_pallet', 'building_mortar_mix_pallet', 'building_romex_14_2_spool', 'building_romex_10_3_spool',
             'building_door_hardware_set'}     # tools/make_door_hardware.py


# Items the player can stand on the ground (properties.placeable). A placed door takes paint from a paint can (PlacedObject.TryPaintAtRay): its
# materials named Door... are recoloured, DoorHardware and Glass are not.
PLACEABLE = {'building_door_exterior', 'building_door_interior'}


def main():
    tmpl = json.load(open(os.path.join(BUILD, 'building_glass', 'building_glass.json'), encoding='utf-8'))
    tags_path = os.path.join(ROOT, 'assets', '_schemas', 'material_tags.json')
    tags = json.load(open(tags_path, encoding='utf-8'))
    for item_id, name, desc, build, weight, stack, value, tag_list in ITEMS:
        if item_id in HAND_MADE:
            print('item', item_id, 'skipped: its model is not built here')
            continue
        reset()
        res = build()
        b, extra = res if isinstance(res, tuple) else (res, None)
        folder = os.path.join(BUILD, item_id)
        os.makedirs(folder, exist_ok=True)
        tris, (sx, sy, sz) = export(b, extra, folder, item_id)
        m = copy.deepcopy(tmpl)
        m['id'] = item_id
        m['name'] = name
        m['description'] = desc
        m['icon'] = item_id + '.png'
        m['properties'].update({'weight_kg': weight, 'max_stack_size': stack, 'base_value': value})
        if item_id in PLACEABLE:
            m['properties']['placeable'] = True
        m['models'] = [{'file': item_id + '.glb', 'format': 'glb', 'dimensions_m': {'x': sx, 'y': sz, 'z': sy}, 'triangles': tris}]
        m['category_fields'] = {'dimensions_m': {'width': sx, 'depth': sy, 'height': sz}}
        with open(os.path.join(folder, item_id + '.json'), 'w', encoding='utf-8', newline='\n') as f:
            json.dump(m, f, indent=2)
        open(os.path.join(folder, 'README.md'), 'w', encoding='utf-8', newline='\n').write('# %s\n\n%s\n\nProcedural model (tools/make_building_items.py), %d triangles.\n' % (name, desc, tris))
        for t in tag_list:
            members = tags['tags'].setdefault(t, [])
            if item_id not in members:
                members.append(item_id)
        print('item', item_id, tris, 'tris', sx, sy, sz)
    tmp = tags_path + '.tmp'
    with open(tmp, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(tags, f, indent=2)
    os.replace(tmp, tags_path)


if __name__ == '__main__':
    main()
