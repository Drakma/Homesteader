"""
Builds the corrugated steel roofing (every colour) and the coloured corrugated steel wall siding, with their stacks of 10 and 20, as GLBs in
headless Blender: free, local, low-poly (no Meshy).

    blender --background --python tools/make_corrugated.py
    python tools/render_icon_from_model.py assets/building/<id>/<id>.glb assets/building/<id>/<id>.png

  roofing_steel_corrugated[_red|_green|_black]              a 1.6 m by 0.88 m sheet, the waves running down its length
  ..._stack_10 / _stack_20                                  the sheets piled into a block and held by two steel straps, no pallet
  building_steel_siding_corrugated_red | _green | _black    the galvanized wall panel (building_steel_siding_corrugated, 0.9 m by 2.44 m, a
                                                            model that this script does not rebuild) with its material recoloured
  ..._stack_10 / _stack_20                                  the panels lying flat, nested, as the galvanized stacks are

The colours are the standing seam roofing's (roofing_seam_red / _green / _black). A new item gets its manifest from the galvanized one (name,
description, look_color and a slightly higher price); an item that is already in the kit keeps its name, price and the rest. Tags (#roofing,
#siding, #metal_siding) and the ~roofing / ~siding equivalencies are updated separately.

Conventions: 1 unit = 1 m, pivot at the centre of the footprint, ground at z = 0, the length along x (the siding: along its own long axis).
"""
import json
import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_simple_props as props  # noqa: E402    (mat, save)

BUILD = os.path.join(props.ROOT, 'assets', 'building')
ROOF, SIDING = 'roofing_steel_corrugated', 'building_steel_siding_corrugated'
# suffix: (word in the name, colour, extra on the price)
COLOURS = {
    '': ('', '#b9bec4', 1.0),
    '_red': ('Red', '#8f2d27', 1.18),
    '_green': ('Green', '#2f6a49', 1.18),
    '_black': ('Black', '#25272b', 1.25),
}
SHEET_L, SHEET_W, WAVES, WAVE_H = 1.6, 0.88, 11, 0.03
ROOF_PITCH = 0.04            # a sheet of the roofing block adds this much height
SIDING_PITCH = 0.008         # nested wall panels


def srgb(hex_):
    return tuple(int(hex_[i:i + 2], 16) / 255.0 for i in (1, 3, 5))


def linear(hex_):
    return tuple(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in srgb(hex_))


def sheet(bm, z0, mi, seg=6):
    """One roofing sheet: a sine wave across its width, straight down its length."""
    n = WAVES * seg
    a, b = [], []
    for k in range(n + 1):
        y = -SHEET_W / 2 + SHEET_W * k / n
        z = z0 + WAVE_H / 2 * (1 - math.cos(2 * math.pi * k / seg))
        a.append(bm.verts.new((-SHEET_L / 2, y, z)))
        b.append(bm.verts.new((SHEET_L / 2, y, z)))
    for k in range(n):
        f = bm.faces.new((a[k], b[k], b[k + 1], a[k + 1]))
        f.material_index = mi
        f.smooth = True


def box(bm, lo, hi, mi):
    r = bmesh.ops.create_cube(bm, size=1.0)
    for v in r['verts']:
        v.co = Vector((lo[i] + (v.co[i] + 0.5) * (hi[i] - lo[i]) for i in range(3)))
    for f in set(f for v in r['verts'] for f in v.link_faces):
        f.material_index = mi


def roofing(hex_, n):
    """n sheets: one lying on the ground, or a strapped block of them."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    steel = props.mat('CorrugatedSteel', linear(hex_), 0.42)
    steel.node_tree.nodes['Principled BSDF'].inputs['Metallic'].default_value = 0.35
    mats = [steel, props.mat('StackShadow', (0.05, 0.05, 0.055), 0.9), props.mat('Strap', (0.1, 0.1, 0.11), 0.5)]
    bm = bmesh.new()
    for k in range(n):
        sheet(bm, k * ROOF_PITCH, 0)
    if n > 1:
        top = (n - 1) * ROOF_PITCH + WAVE_H
        box(bm, (-SHEET_L / 2 + 0.006, -SHEET_W / 2 + 0.006, 0.002), (SHEET_L / 2 - 0.006, SHEET_W / 2 - 0.006, top - WAVE_H - 0.002), 1)     # the dark between the sheets
        for x in (-SHEET_L * 0.28, SHEET_L * 0.28):                                 # two straps round the block
            box(bm, (x - 0.016, -SHEET_W / 2 - 0.003, top), (x + 0.016, SHEET_W / 2 + 0.003, top + 0.002), 2)
            box(bm, (x - 0.016, -SHEET_W / 2 - 0.003, -0.0005), (x + 0.016, SHEET_W / 2 + 0.003, 0.0015), 2)
            for s in (-1, 1):
                y = s * (SHEET_W / 2 + 0.002)
                box(bm, (x - 0.016, y - 0.001, 0.0), (x + 0.016, y + 0.001, top + 0.002), 2)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new('roofing')
    bm.to_mesh(me)
    bm.free()
    for m in mats[:1 if n == 1 else 3]:
        me.materials.append(m)
    obj = bpy.data.objects.new('roofing', me)
    bpy.context.collection.objects.link(obj)
    return obj


def siding(hex_, n):
    """The galvanized wall panel in the colour; n > 1: nested in a flat stack (only the top panel is whole)."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=os.path.join(BUILD, SIDING, SIDING + '.glb'))
    obj = [o for o in bpy.context.scene.objects if o.type == 'MESH'][0]
    bpy.context.view_layer.update()
    obj.data.transform(obj.matrix_world)
    obj.matrix_world = Matrix.Identity(4)
    obj.parent = None
    for o in list(bpy.context.scene.objects):
        if o is not obj:
            bpy.data.objects.remove(o)
    for m in obj.data.materials:                  # the panel is one plain material (no texture): give it the colour, a little less mirror-like than bare zinc
        bsdf = m.node_tree.nodes['Principled BSDF']
        bsdf.inputs['Base Color'].default_value = (*linear(hex_), 1.0)
        bsdf.inputs['Metallic'].default_value = 0.35
        bsdf.inputs['Roughness'].default_value = 0.42
        m.name = 'M_Painted_Siding'
    if n > 1:
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        src = bm.faces[:]
        for k in range(1, n):                     # a lower panel: the top one hides its faces, so only its rim is kept
            r = bmesh.ops.duplicate(bm, geom=[f for f in src if abs(f.normal.z) < 0.3])
            bmesh.ops.translate(bm, verts=[e for e in r['geom'] if isinstance(e, bmesh.types.BMVert)], vec=(0, 0, -SIDING_PITCH * k))
        bmesh.ops.translate(bm, verts=bm.verts[:], vec=(0, 0, SIDING_PITCH * (n - 1)))
        obj.data.materials.append(props.mat('StackShadow', (0.05, 0.05, 0.055), 0.9))
        xs, ys = [v.co.x for v in bm.verts], [v.co.y for v in bm.verts]
        box(bm, (min(xs) + 0.004, min(ys) + 0.004, 0.0), (max(xs) - 0.004, max(ys) - 0.004, SIDING_PITCH * (n - 1) + 0.002), len(obj.data.materials) - 1)
        bm.to_mesh(obj.data)
        bm.free()
    return obj


def write(item, obj, base_item, word, hex_, price_x, n, note):
    obj.name = item
    folder = os.path.join(BUILD, item)
    os.makedirs(folder, exist_ok=True)
    pts = [v.co for v in obj.data.vertices]
    lo = [min(p[i] for p in pts) for i in range(3)]
    hi = [max(p[i] for p in pts) for i in range(3)]
    obj.data.transform(Matrix.Translation((-(lo[0] + hi[0]) / 2, -(lo[1] + hi[1]) / 2, -lo[2])))
    dims = [round(hi[i] - lo[i], 3) for i in range(3)]
    tris = sum(len(p.vertices) - 2 for p in obj.data.polygons)
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.gltf(filepath=os.path.join(folder, item + '.glb'), export_format='GLB', use_selection=True, export_yup=True)
    path = os.path.join(folder, item + '.json')
    if os.path.exists(path):
        m = json.load(open(path, encoding='utf-8'))
    else:                                         # a new colour: the galvanized item's manifest, renamed
        m = json.load(open(os.path.join(BUILD, base_item, base_item + '.json'), encoding='utf-8'))
        m.update({'id': item, 'icon': item + '.png', 'name': '%s %s' % (word, m['name']),
                  'description': m['description'].replace('Galvanized corrugated', '%s corrugated' % word).replace('galvanized', word.lower() + ' painted')})
        if not m['description'].lower().startswith(word.lower()) and word.lower() not in m['description'].lower():
            m['description'] = '%s. %s painted.' % (m['description'].rstrip('.'), word)
        p = m['properties']
        p['base_value'] = round(p['base_value'] * price_x)
        if 'look_color' in p:
            p['look_color'] = hex_
    m['models'] = [{'file': item + '.glb', 'format': 'glb', 'dimensions_m': {'x': dims[0], 'y': dims[2], 'z': dims[1]}, 'triangles': tris}]
    m['category_fields'] = dict(m.get('category_fields') or {}, dimensions_m={'width': round(dims[0], 2), 'depth': round(dims[1], 2), 'height': round(dims[2], 2)})
    m['properties']['placeable'] = True
    props.save(path, json.dumps(m, indent=2))
    props.save(os.path.join(folder, 'README.md'), '# %s\n\n%s\n\nModel by tools/make_corrugated.py, %d triangles, %.2f x %.2f x %.2f m. %s\n'
               % (m['name'], m['description'], tris, *dims, note))
    print('corrugated', item, '|', m['name'], '|', tris, 'tris |', dims)


def main():
    for suffix, (word, hex_, price_x) in COLOURS.items():
        for n in (1, 10, 20):
            tail = '' if n == 1 else '_stack_%d' % n
            write(ROOF + suffix + tail, roofing(hex_, n), ROOF + tail, word, hex_, price_x, n,
                  'A 1.6 m by 0.88 m corrugated sheet.' if n == 1 else '%d sheets in a block held by two steel straps, no pallet.' % n)
            if suffix:                            # the galvanized siding and its stacks are not rebuilt
                write(SIDING + suffix + tail, siding(hex_, n), SIDING + tail, word, hex_, price_x, n,
                      'The galvanized wall panel, recoloured.' if n == 1 else '%d panels lying flat, nested.' % n)


if __name__ == '__main__':
    main()
