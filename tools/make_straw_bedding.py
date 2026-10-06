"""
Builds the straw bedding item (assets/materials/mat_bedding_straw) in headless Blender: free, local, low-poly.

    blender --background --python tools/make_straw_bedding.py
    python tools/render_icon_from_model.py assets/materials/mat_bedding_straw/mat_bedding_straw.glb assets/materials/mat_bedding_straw/mat_bedding_straw.png

The model is a low heap of loose straw (it is what the icon is rendered from). In the game the bedding is not this heap: a straw bale spreads it
over the floor of a room (Assets/Scripts/Growth/StrawBedding.cs), which lays the straw as one mesh and hides this model. The item is not placeable
by hand and not sold: it only comes from spreading a bale.

Pivot at the middle of the footprint, bottom at z = 0.
"""
import json
import math
import os
import random
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_bag_pallets as bp  # noqa: E402    (material, box)

ITEM = 'mat_bedding_straw'
FOLDER = os.path.join(bp.ROOT, 'assets', 'materials', ITEM)


def build():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    rnd = random.Random(7)
    bm = bmesh.new()
    mats = [bp.material('Straw', (0.82, 0.68, 0.33), rough=0.95), bp.material('StrawLight', (0.92, 0.8, 0.46), rough=0.95),
            bp.material('StrawShade', (0.62, 0.5, 0.24), rough=0.95)]
    # the heap: a low mound, a ring of rim points round a few raised inner rings
    rings = [(0.55, 0.0), (0.5, 0.03), (0.36, 0.07), (0.2, 0.1)]
    seg = 12
    loops = []
    for r, z in rings:
        loops.append([bm.verts.new((r * (1 + rnd.uniform(-0.12, 0.12)) * math.cos(2 * math.pi * k / seg), r * (1 + rnd.uniform(-0.12, 0.12)) * math.sin(2 * math.pi * k / seg),
                                    z * (1 + rnd.uniform(-0.25, 0.25)))) for k in range(seg)])
    top = bm.verts.new((0.0, 0.0, 0.115))
    for a, b in zip(loops[:-1], loops[1:]):
        for k in range(seg):
            j = (k + 1) % seg
            bm.faces.new((a[k], a[j], b[j], b[k])).material_index = 0
    for k in range(seg):
        bm.faces.new((loops[-1][k], loops[-1][(k + 1) % seg], top)).material_index = 0
    bm.faces.new(loops[0][::-1]).material_index = 0
    # loose stalks lying on it, every which way
    for n in range(46):
        a = rnd.uniform(0, 2 * math.pi)
        d = rnd.uniform(0.0, 0.5)
        x, y = d * math.cos(a), d * math.sin(a)
        z = 0.115 * max(0.0, 1 - d / 0.56) + 0.012
        length = rnd.uniform(0.16, 0.32)
        r = bmesh.ops.create_cube(bm, size=1.0)
        mat = Matrix.Translation((x, y, z)) @ Matrix.Rotation(rnd.uniform(0, math.pi), 4, 'Z') @ Matrix.Rotation(rnd.uniform(-0.25, 0.25), 4, 'Y')
        for v in r['verts']:
            v.co = mat @ Vector((v.co.x * length, v.co.y * 0.012, v.co.z * 0.008))
        mi = rnd.choice((1, 1, 2))
        for f in set(f for v in r['verts'] for f in v.link_faces):
            f.material_index = mi
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(ITEM)
    bm.to_mesh(me)
    bm.free()
    for m in mats:
        me.materials.append(m)
    obj = bpy.data.objects.new(ITEM, me)
    bpy.context.collection.objects.link(obj)
    return obj


def main():
    obj = build()
    os.makedirs(FOLDER, exist_ok=True)
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.gltf(filepath=os.path.join(FOLDER, ITEM + '.glb'), export_format='GLB', use_selection=True, export_yup=True)
    pts = [v.co for v in obj.data.vertices]
    dims = [round(max(p[i] for p in pts) - min(p[i] for p in pts), 3) for i in range(3)]
    tris = sum(len(p.vertices) - 2 for p in obj.data.polygons)
    path = os.path.join(FOLDER, ITEM + '.json')
    if os.path.exists(path):
        m = json.load(open(path, encoding='utf-8'))
    else:
        m = json.load(open(os.path.join(bp.ROOT, 'assets', 'materials', 'mat_bale_straw_square', 'mat_bale_straw_square.json'), encoding='utf-8'))
        m['id'] = ITEM
        m['icon'] = ITEM + '.png'
        m['name'] = 'Straw Bedding'
        m['description'] = ('Loose straw spread over the floor of a room as animal bedding. Made by spreading a straw bale: hold a bale and right click '
                            'the floor of a room in a building. A shovel takes it up again.')
        p = m['properties']
        p.update({'weight_kg': 15.0, 'max_stack_size': 10, 'base_value': 0, 'is_buyable': False, 'placeable': False})
        p.pop('stores', None)
    m['models'] = [{'file': ITEM + '.glb', 'format': 'glb', 'dimensions_m': {'x': dims[0], 'y': dims[2], 'z': dims[1]}, 'triangles': tris}]
    m['category_fields'] = dict(m.get('category_fields') or {}, dimensions_m={'width': round(dims[0], 2), 'depth': round(dims[1], 2), 'height': round(dims[2], 2)})
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(m, f, indent=2)
    with open(os.path.join(FOLDER, 'README.md'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('# %s\n\n%s\n\nProcedural model (tools/make_straw_bedding.py), %d triangles: a heap of loose straw, used for the icon. In the game the bedding is laid '
                'as one mesh over the floor of the room (`Assets/Scripts/Growth/StrawBedding.cs`); one bale covers 12 square metres.\n' % (m['name'], m['description'], tris))
    print('bedding', ITEM, tris, 'tris', dims)


if __name__ == '__main__':
    main()
