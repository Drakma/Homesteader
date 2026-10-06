"""
Builds a pallet of 10 and a pallet of 20 for every bag item, as GLBs in headless Blender: free, local, low-poly.

    blender --background --python tools/make_bag_pallets.py
    blender --background --python tools/make_bag_pallets.py -- 20lb_sand_bag building_grout_bag

For each bag in BAGS it reads assets/building/<bag>/<bag>.glb (the detailed, textured bag) and its manifest, and writes
assets/building/<bag>_pallet_<n>/ with the model, the manifest and the README (a manifest that already exists keeps its name, price and the
rest: only its model entry and dimensions are updated). EXTRA lists other pallet sizes. The icons are rendered afterwards with
tools/render_icon_from_model.py.

The detailed bag is some 4,000 triangles, so a pallet does not copy it. The bag is photographed square-on from above and from its four
sides (flat lit, its own texture), the five pictures go into one small atlas, and every bag on the pallet is a 12-triangle block with those
pictures on its faces. The pallet itself is plain boxes. A pallet of 20 is some 400 triangles.

Conventions: 1 unit = 1 m, pivot at the centre of the footprint, ground at z = 0.
"""
import json
import math
import os
import random
import sys
import tempfile

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(ROOT, 'assets', 'building')

BAGS = ['20lb_cement_bag', '20lb_sand_bag', '20lb_aggregate_rock_bag', 'building_mortar_mix_bag', 'building_grout_bag', 'building_insulation_blown_bag',
        'building_concrete_mix_bag']
COUNTS = (10, 20)
# other pallets: (bag, count) -> the item id (an item that existed before this script and keeps its id)
EXTRA = {('building_concrete_mix_bag', 40): 'building_concrete_mix_pallet'}

PALLET_W, PALLET_D, PALLET_H = 1.2, 1.0, 0.15
PALLET_KG = 20.0
OVERHANG = 1.08        # a layer may overhang the pallet by this much
TILE = 256             # one picture of the atlas, in pixels
VIEWS = ('top', 'front', 'back', 'left', 'right')


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def load_bag(bag):
    """The detailed bag, as one mesh object with its transform applied. Returns (object, lo, hi)."""
    bpy.ops.import_scene.gltf(filepath=os.path.join(BUILD, bag, bag + '.glb'))
    bpy.context.view_layer.update()
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    for o in meshes:
        o.data.transform(o.matrix_world)
        o.matrix_world = Matrix.Identity(4)
    pts = [v.co for o in meshes for v in o.data.vertices]
    lo = Vector([min(p[i] for p in pts) for i in range(3)])
    hi = Vector([max(p[i] for p in pts) for i in range(3)])
    return meshes, lo, hi


def photograph(lo, hi, folder):
    """Five square-on pictures of the bag (flat lit, transparent background). Returns {view: float RGBA array, TILE x TILE, row 0 at the bottom}."""
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_WORKBENCH'
    sc.display.shading.light = 'FLAT'
    sc.display.shading.color_type = 'TEXTURE'
    sc.render.film_transparent = True
    sc.render.resolution_x = sc.render.resolution_y = TILE
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_mode = 'RGBA'
    sc.view_settings.view_transform = 'Standard'
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
    sc.collection.objects.link(cam)
    sc.camera = cam
    cam.data.type = 'ORTHO'
    c = (lo + hi) / 2
    sx, sy, sz = hi - lo
    # view: (camera direction from the centre, up, picture width, picture height)
    setup = {
        'top': (Vector((0, 0, 1)), Vector((0, 1, 0)), sx, sy),
        'front': (Vector((0, -1, 0)), Vector((0, 0, 1)), sx, sz),
        'back': (Vector((0, 1, 0)), Vector((0, 0, 1)), sx, sz),
        'left': (Vector((-1, 0, 0)), Vector((0, 0, 1)), sy, sz),
        'right': (Vector((1, 0, 0)), Vector((0, 0, 1)), sy, sz),
    }
    out = {}
    for view, (d, up, w, h) in setup.items():
        cam.location = c + d * 5.0
        z = d                                   # the camera looks along -Z of its own frame
        x = up.cross(z).normalized()
        y = z.cross(x)
        cam.matrix_world = Matrix(((x.x, y.x, z.x, cam.location.x), (x.y, y.y, z.y, cam.location.y), (x.z, y.z, z.z, cam.location.z), (0, 0, 0, 1)))
        # the picture is square and the bag sits in the middle of it at its true shape; bag_block() maps a face to that part of the picture
        cam.data.ortho_scale = max(w, h)
        path = os.path.join(folder, view + '.png')
        sc.render.filepath = path
        bpy.ops.render.render(write_still=True)
        img = bpy.data.images.load(path)
        a = np.empty(TILE * TILE * 4, dtype=np.float32)
        img.pixels.foreach_get(a)
        out[view] = a.reshape(TILE, TILE, 4).copy()
        bpy.data.images.remove(img)
    bpy.data.objects.remove(cam)
    return out


def atlas(pics, name):
    """The five pictures side by side in one image (transparent pixels take the bag's own colour, so a block's corners are never see-through)."""
    solid = np.concatenate([p[p[..., 3] > 0.99][:, :3] for p in pics.values()])
    body = np.median(solid, axis=0)
    a = np.ones((TILE, TILE * len(VIEWS), 4), dtype=np.float32)
    for k, view in enumerate(VIEWS):
        p = pics[view]
        al = p[..., 3:4]
        a[:, k * TILE:(k + 1) * TILE, :3] = p[..., :3] * al + body * (1 - al)      # (a loaded PNG has straight alpha)
    img = bpy.data.images.new(name, TILE * len(VIEWS), TILE, alpha=False)
    img.pixels.foreach_set(a.ravel())
    img.pack()
    return img


def material(name, rgb=None, image=None, rough=0.8):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Roughness'].default_value = rough
    if image is not None:
        t = m.node_tree.nodes.new('ShaderNodeTexImage')
        t.image = image
        m.node_tree.links.new(t.outputs['Color'], b.inputs['Base Color'])
    else:
        b.inputs['Base Color'].default_value = (*rgb, 1.0)
    return m


def box(bm, x0, x1, y0, y1, z0, z1, mat_index):
    r = bmesh.ops.create_cube(bm, size=1.0)
    for v in r['verts']:
        v.co = Vector((x0 + (v.co.x + 0.5) * (x1 - x0), y0 + (v.co.y + 0.5) * (y1 - y0), z0 + (v.co.z + 0.5) * (z1 - z0)))
    for f in set(f for v in r['verts'] for f in v.link_faces):
        f.material_index = mat_index


def pallet(bm, mi):
    """A plain wooden pallet: three runners, seven deck boards, three bottom boards."""
    w, d, h = PALLET_W, PALLET_D, PALLET_H
    for y in (-d / 2 + 0.05, 0.0, d / 2 - 0.05):
        box(bm, -w / 2, w / 2, y - 0.05, y + 0.05, 0.022, h - 0.022, mi)
    n = 7
    for k in range(n):
        x = -w / 2 + 0.05 + (w - 0.1) * k / (n - 1)
        box(bm, x - 0.05, x + 0.05, -d / 2, d / 2, h - 0.022, h, mi)
    for x in (-w / 2 + 0.05, 0.0, w / 2 - 0.05):
        box(bm, x - 0.05, x + 0.05, -d / 2, d / 2, 0.0, 0.022, mi)


def bag_block(bm, uv, size, mi, turn, pos):
    """One bag as a block (its top a little smaller than its base), with the bag's pictures on its faces. `turn`: a quarter turn about the vertical."""
    sx, sy, sz = size
    t = 0.06
    lo_ = [(-sx / 2, -sy / 2, 0.0), (sx / 2, -sy / 2, 0.0), (sx / 2, sy / 2, 0.0), (-sx / 2, sy / 2, 0.0)]
    hi_ = [(x * (1 - t), y * (1 - t), sz) for x, y, _ in lo_]
    n = len(VIEWS)

    span = {'top': (sx, sy), 'front': (sx, sz), 'back': (sx, sz), 'left': (sy, sz), 'right': (sy, sz)}

    def tile(view, u, v):
        w, h = span[view]                                  # the bag fills the middle w x h of a square picture max(w, h) across
        m = max(w, h)
        u = 0.5 + (min(max(u, 0.0), 1.0) - 0.5) * w / m
        v = 0.5 + (min(max(v, 0.0), 1.0) - 0.5) * h / m
        return ((VIEWS.index(view) + u) / n, v)

    # face: (corner points, view, how a point maps to the picture's (u, v))
    faces = [
        (hi_, 'top', lambda p: (p[0] / sx + 0.5, p[1] / sy + 0.5)),
        ([lo_[0], lo_[1], hi_[1], hi_[0]], 'front', lambda p: (p[0] / sx + 0.5, p[2] / sz)),
        ([lo_[2], lo_[3], hi_[3], hi_[2]], 'back', lambda p: (0.5 - p[0] / sx, p[2] / sz)),
        ([lo_[3], lo_[0], hi_[0], hi_[3]], 'left', lambda p: (0.5 - p[1] / sy, p[2] / sz)),
        ([lo_[1], lo_[2], hi_[2], hi_[1]], 'right', lambda p: (p[1] / sy + 0.5, p[2] / sz)),
        (lo_[::-1], 'top', lambda p: (p[0] / sx + 0.5, p[1] / sy + 0.5)),
    ]
    rot = Matrix.Rotation(turn, 4, 'Z')
    for pts, view, fn in faces:
        vs = [bm.verts.new(rot @ Vector(p) + Vector(pos)) for p in pts]
        f = bm.faces.new(vs)
        f.material_index = mi
        for loop, p in zip(f.loops, pts):
            loop[uv].uv = tile(view, *fn(p))


def layout(size, n):
    """How the bags lie on the pallet: (bags along x, bags along y, lying across?). At least two layers when it can, a top layer at least half full,
    then as many bags per layer as fit (full layers count for more), and never a long thin strip."""
    sx, sy, _ = size
    best = None
    for across in (False, True):
        bx, by = (sy, sx) if across else (sx, sy)
        for cx in range(1, int(PALLET_W * OVERHANG / bx) + 1):
            for cy in range(1, int(PALLET_D * OVERHANG / by) + 1):
                per = cx * cy
                layers = math.ceil(n / per)
                w, d = cx * bx, cy * by
                if max(w, d) / min(w, d) > 2.2:
                    continue
                top = n - per * (layers - 1)                       # bags on the top layer
                score = (layers >= 2, top * 2 >= per, (per * (1.5 if n % per == 0 else 1.0)) if layers >= 2 else -per, -layers)
                if best is None or score > best[0]:
                    best = (score, cx, cy, across)
    return best[1:]


def build(bag, n, item=None):
    reset()
    meshes, lo, hi = load_bag(bag)
    size = tuple(hi - lo)
    with tempfile.TemporaryDirectory() as tmp:
        pics = photograph(lo, hi, tmp)
    for o in meshes:
        bpy.data.objects.remove(o)
    item = item or '%s_pallet_%d' % (bag, n)
    img = atlas(pics, item + '_bags')
    mats = [material('PalletWood', (0.62, 0.47, 0.3), rough=0.9), material('Bags', image=img)]
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new('UVMap')
    pallet(bm, 0)
    cx, cy, across = layout(size, n)
    bx, by = (size[1], size[0]) if across else (size[0], size[1])
    rnd = random.Random(sum(ord(ch) for ch in bag) * 31 + n)        # the same pallet every run
    placed = 0
    layer = 0
    while placed < n:
        left = n - placed
        slots = [(i, j) for j in range(cy) for i in range(cx)]
        if left < len(slots):                                        # the top layer, part full: its bags sit in the middle rows
            slots = sorted(slots, key=lambda s: (abs(s[1] - (cy - 1) / 2), abs(s[0] - (cx - 1) / 2)))[:left]
        for i, j in slots:
            x = (i - (cx - 1) / 2) * bx + rnd.uniform(-0.006, 0.006)
            y = (j - (cy - 1) / 2) * by + rnd.uniform(-0.006, 0.006)
            turn = (math.pi / 2 if across else 0.0) + (math.pi if (layer + i + j) % 2 else 0.0) + math.radians(rnd.uniform(-1.5, 1.5))
            bag_block(bm, uv, (size[0] * 0.985, size[1] * 0.985, size[2]), 1, turn, (x, y, PALLET_H + layer * size[2] * 0.97))
            placed += 1
        layer += 1
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(item)
    bm.to_mesh(me)
    bm.free()
    for m in mats:
        me.materials.append(m)
    obj = bpy.data.objects.new(item, me)
    bpy.context.collection.objects.link(obj)
    pts = [v.co for v in me.vertices]
    dims = [max(p[i] for p in pts) - min(p[i] for p in pts) for i in range(3)]
    tris = sum(len(p.vertices) - 2 for p in me.polygons)
    folder = os.path.join(BUILD, item)
    os.makedirs(folder, exist_ok=True)
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.gltf(filepath=os.path.join(folder, item + '.glb'), export_format='GLB', use_selection=True, export_yup=True)

    src = json.load(open(os.path.join(BUILD, bag, bag + '.json'), encoding='utf-8'))
    manifest = os.path.join(folder, item + '.json')
    if os.path.exists(manifest):
        m = json.load(open(manifest, encoding='utf-8'))        # an item that is already in the kit keeps its name, price and the rest: only the model changes
    else:
        m = json.loads(json.dumps(src))
        name = src['name'].split(' (')[0]
        m['id'] = item
        m['name'] = '%s Pallet' % name
        m['description'] = 'A wooden pallet stacked with %d of: %s' % (n, src['description'][0].lower() + src['description'][1:])
        m['icon'] = item + '.png'
        p = m['properties']
        p['weight_kg'] = round(src['properties']['weight_kg'] * n + PALLET_KG, 1)
        p['base_value'] = src['properties']['base_value'] * n
        p['max_stack_size'] = 1
        for k in [k for k in p if k.startswith('look_')]:
            del p[k]
    m['models'] = [{'file': item + '.glb', 'format': 'glb', 'dimensions_m': {'x': round(dims[0], 3), 'y': round(dims[2], 3), 'z': round(dims[1], 3)}, 'triangles': tris}]
    m.pop('dimensions', None)
    m['category_fields'] = {'dimensions_m': {'width': round(dims[0], 2), 'depth': round(dims[1], 2), 'height': round(dims[2], 2)}}
    with open(manifest, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(m, f, indent=2)
    with open(os.path.join(folder, 'README.md'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('# %s\n\n%s\n\nProcedural model (tools/make_bag_pallets.py) from `%s`: %d bags in %d layers on a 1.2 m by 1.0 m pallet, %d triangles, '
                '%.2f m tall.\n' % (m['name'], m['description'], bag, n, layer, tris, dims[2]))
    print('pallet', item, '%dx%d per layer, %d layers' % (cx, cy, layer), tris, 'tris', '%.2f %.2f %.2f' % tuple(dims))


def main():
    argv = sys.argv
    bags = argv[argv.index('--') + 1:] if '--' in argv else BAGS
    for bag in bags:
        for n in COUNTS:
            build(bag, n)
        for (b, n), item in EXTRA.items():
            if b == bag:
                build(bag, n, item)


if __name__ == '__main__':
    main()
