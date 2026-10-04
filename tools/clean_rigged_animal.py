"""
Cleans a Mesh2Motion rigged animal in headless Blender: removes the stray helper sphere the export carries, fixes the weights that tear at the
hind legs and the tail, scales the model to its real-world height and exports a GLB with all its clips.

    blender --background --python tools/clean_rigged_animal.py -- <in.glb> <out.glb> <height_m> <mode> [group_json_out]

mode:  auto   throw the exported weights away and let Blender compute heat-diffusion weights from the bones, then smooth them
       clean  keep the exported weights; limit to 4 bones, drop tiny weights, smooth, and re-weight the tail by distance along the tail chain
"""
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:]
src, dst, height, mode = argv[0], argv[1], float(argv[2]), argv[3]

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
sc = bpy.context.scene
arm = [o for o in sc.objects if o.type == 'ARMATURE'][0]
body = None
for o in list(sc.objects):
    if o.type == 'MESH':
        if len(o.vertex_groups) == 0 and len(o.data.polygons) < 200:
            bpy.data.objects.remove(o, do_unlink=True)      # the helper sphere
        else:
            body = o
assert body is not None


def select_only(*objs):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[-1]


# ---- scale to the real height and stand on the ground: the ARMATURE object carries the scale and the offset (the mesh is its child)
bpy.context.view_layer.update()
cs = [body.matrix_world @ Vector(c) for c in body.bound_box]
mn = Vector((min(c.x for c in cs), min(c.y for c in cs), min(c.z for c in cs)))
mx = Vector((max(c.x for c in cs), max(c.y for c in cs), max(c.z for c in cs)))
k = height / (mx.z - mn.z)
arm.scale = (k, k, k)
arm.location = (-(mn.x + mx.x) / 2 * k, -(mn.y + mx.y) / 2 * k, -mn.z * k)
bpy.context.view_layer.update()

if mode == 'auto':
    select_only(body)
    for g in list(body.vertex_groups):
        body.vertex_groups.remove(g)
    for m in list(body.modifiers):
        body.modifiers.remove(m)
    body.parent = None
    select_only(body, arm)
    bpy.ops.object.parent_set(type='ARMATURE_AUTO')
else:
    # tail: re-weight the vertices near the tail chain by position along it
    tail = [arm.data.bones[n] for n in ('tail_1', 'tail_2', 'tail_3', 'tail_4') if n in arm.data.bones]
    hips = arm.data.bones['hips']
    pts = [arm.matrix_world @ tail[0].head_local] + [arm.matrix_world @ b.tail_local for b in tail]
    hip_y = (arm.matrix_world @ hips.head_local)
    # which way is "back": from the head bone to the tail start
    head = arm.matrix_world @ arm.data.bones['head'].head_local
    back = (pts[0] - head)
    back.z = 0
    back.normalize()
    radius = 0.18 * height
    mw = body.matrix_world
    names = [b.name for b in tail]
    for v in body.data.vertices:
        p = mw @ v.co
        along = (p - pts[0]).dot(back)
        if along < -0.02 * height:
            continue                                          # in front of the tail's start: not tail
        # distance to the polyline
        best, bt = 1e9, 0.0
        for i in range(len(pts) - 1):
            a, b = pts[i], pts[i + 1]
            ab = b - a
            t = max(0.0, min(1.0, (p - a).dot(ab) / max(1e-9, ab.length_squared)))
            d = (p - (a + ab * t)).length
            if d < best:
                best, bt = d, i + t
        if best > radius or p.z < pts[0].z - 0.35 * height:
            continue
        for g in list(v.groups):
            body.vertex_groups[g.group].remove([v.index])
        i = int(min(bt, len(names) - 1e-6))
        f = bt - i
        body.vertex_groups[names[i]].add([v.index], 1.0 - f, 'REPLACE')
        if i + 1 < len(names):
            body.vertex_groups[names[i + 1]].add([v.index], f, 'REPLACE')

# ---- clean the weights in Python: smooth over the mesh edges, keep the strongest 4 bones per vertex, normalise
mesh = body.data
nv = len(mesh.vertices)
nbrs = [[] for _ in range(nv)]
for e in mesh.edges:
    a, b = e.vertices
    nbrs[a].append(b)
    nbrs[b].append(a)
# vertices that share a position (the mesh is made of islands with split vertices) are neighbours too
pos = {}
for v in mesh.vertices:
    pos.setdefault((round(v.co.x, 4), round(v.co.y, 4), round(v.co.z, 4)), []).append(v.index)
for group in pos.values():
    for i in group:
        nbrs[i].extend(j for j in group if j != i)
W = [dict((g.group, g.weight) for g in v.groups) for v in mesh.vertices]
for _ in range(3):
    new = []
    for i in range(nv):
        acc = {}
        for j in nbrs[i]:
            for g, w in W[j].items():
                acc[g] = acc.get(g, 0.0) + w / len(nbrs[i])
        cur = W[i]
        keys = set(cur) | set(acc)
        new.append({g: 0.5 * cur.get(g, 0.0) + 0.5 * acc.get(g, 0.0) for g in keys} if nbrs[i] else cur)
    W = new
for g in list(body.vertex_groups):
    pass
for i in range(nv):
    top = sorted(W[i].items(), key=lambda kv: -kv[1])[:4]
    top = [(g, w) for g, w in top if w > 0.02] or top[:1]
    tot = sum(w for _, w in top) or 1.0
    W[i] = {g: w / tot for g, w in top}
for vg in body.vertex_groups:
    vg.remove(list(range(nv)))
for i in range(nv):
    for g, w in W[i].items():
        body.vertex_groups[g].add([i], w, 'REPLACE')

for img in bpy.data.images:
    w_, h_ = img.size
    if max(w_, h_) > 1024:
        img.scale(max(1, w_ // 2), max(1, h_ // 2))      # 2048 -> 1024
print('INFO before export', [(o.name, o.type) for o in bpy.context.scene.objects], [(o.name, o.users) for o in bpy.data.objects])
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=dst, export_format='GLB', use_selection=False, export_yup=True, export_animations=True,
                          export_animation_mode='ACTIONS', export_image_format='JPEG', export_jpeg_quality=85)
print('INFO cleaned', mode, 'tris', sum(len(p.vertices) - 2 for p in body.data.polygons), 'actions', [a.name for a in bpy.data.actions])
