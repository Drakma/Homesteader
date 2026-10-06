"""
Audits the finished structure models for the faults that show in play, in headless Blender: free, local.

    blender --background --python tools/audit_structures.py                      (every structure's complete stage)
    blender --background --python tools/audit_structures.py -- barn small_cabin  (only these)

For each model:
  gaps         rays are cast from points inside the building (a grid at two heights) in every direction; a ray that gets out without meeting anything is a gap
               (a wall that stops short of the roof, a hole at a corner, a missing gable). The exits are clustered and reported by where they leave the box.
  fighting     triangles of different objects or materials that lie in the same plane and overlap (texture fighting / z-fighting, bleed through).
  walls        each Wall_* part's lowest and highest point against the roof's.
A list of every finding goes to assets/_scratch/audit/structures.txt.
"""
import glob
import json
import math
import os
import sys

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'assets', '_scratch', 'audit')
os.makedirs(OUT, exist_ok=True)

SKIP = ('waste_', 'water_well_concrete', 'water_well_wooden', 'wind_turbine', 'grain_silo', 'struct_camper', 'struct_tent', 'struct_light_pole', 'water_well_manual')


def fib_dirs(n):
    out = []
    ga = math.pi * (3 - math.sqrt(5))
    for i in range(n):
        z = 1 - 2 * (i + 0.5) / n
        r = math.sqrt(max(0.0, 1 - z * z))
        a = ga * i
        out.append(Vector((r * math.cos(a), r * math.sin(a), z)))
    return out


def load(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=path)
    objs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    return objs


def part_name(o):
    n = o.name
    p = o
    while p is not None:
        for key in ('Roof', 'Porch', 'WindowGlass', 'Wall_Front', 'Wall_Back', 'Wall_Left', 'Wall_Right', 'DoorHinge', 'Foundation'):
            if p.name.startswith(key):
                return key
        p = p.parent
    return n


def tris_world(objs):
    """verts, tris (index triples), and per triangle: the object, the material index."""
    verts, tris, owner = [], [], []
    for o in objs:
        mw = o.matrix_world
        base = len(verts)
        me = o.data
        me.calc_loop_triangles()
        for v in me.vertices:
            verts.append(mw @ v.co)
        for t in me.loop_triangles:
            tris.append((base + t.vertices[0], base + t.vertices[1], base + t.vertices[2]))
            mi = t.material_index
            mname = me.materials[mi].name if mi < len(me.materials) and me.materials[mi] else '?'
            owner.append((o.name, mname, part_name(o)))
    return verts, tris, owner


def audit(path, label):
    objs = load(path)
    if not objs:
        return ['no meshes']
    verts, tris, owner = tris_world(objs)
    bvh = BVHTree.FromPolygons([tuple(v) for v in verts], tris, epsilon=0.0)
    xs = [v.x for v in verts]; ys = [v.y for v in verts]; zs = [v.z for v in verts]
    x0, x1, y0, y1, z0, z1 = min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)
    lines = ['%s: %d tris, box %.2f x %.2f x %.2f' % (label, len(tris), x1 - x0, y1 - y0, z1 - z0)]

    # ---- walls against the roof
    parts = {}
    for o in objs:
        key = part_name(o)
        pz = [(o.matrix_world @ v.co).z for v in o.data.vertices]
        if not pz:
            continue
        a = parts.setdefault(key, [1e9, -1e9])
        a[0] = min(a[0], min(pz)); a[1] = max(a[1], max(pz))
    desc = ', '.join('%s %.2f..%.2f' % (k, v[0], v[1]) for k, v in sorted(parts.items()) if k.startswith('Wall') or k in ('Roof', 'Foundation'))
    lines.append('  parts (z): ' + desc)

    # ---- gaps: rays out of the inside
    dirs = fib_dirs(220)
    exits = {}
    inside = 0
    step = 0.7
    # the inside is within the walls (not under the roof's overhang or on the step): the box of the Wall_* parts, a little in
    wx, wy = [], []
    for o in objs:
        if part_name(o).startswith('Wall_'):
            for v in o.data.vertices:
                w = o.matrix_world @ v.co
                wx.append(w.x); wy.append(w.y)
    if wx:
        ix0, ix1, iy0, iy1 = min(wx) + 0.4, max(wx) - 0.4, min(wy) + 0.4, max(wy) - 0.4
    else:
        ix0, ix1, iy0, iy1 = x0 + 0.6, x1 - 0.6, y0 + 0.6, y1 - 0.6
    for zh in (0.9, 1.8):
        x = ix0
        while x <= ix1:
            y = iy0
            while y <= iy1:
                o = Vector((x, y, zh))
                # an inside point: something above it, and walls on the sides within the box
                up = bvh.ray_cast(o, Vector((0, 0, 1)), 50.0)
                if up[0] is None:
                    y += step; continue
                sides = sum(1 for d in (Vector((1, 0, 0)), Vector((-1, 0, 0)), Vector((0, 1, 0)), Vector((0, -1, 0))) if bvh.ray_cast(o, d, 60.0)[0] is not None)
                if sides < 3:
                    y += step; continue
                # not inside a solid (the first hit going up is very close and from the back of a face: skip points in solids)
                inside += 1
                for d in dirs:
                    if d.z < -0.2:
                        continue                         # (the floor)
                    hit = bvh.ray_cast(o, d, 80.0)
                    if hit[0] is not None:
                        continue
                    # where does it leave the box?
                    tmax = 1e9
                    for axis, lo, hi in ((0, x0, x1), (1, y0, y1), (2, z0, z1 + 5)):
                        dc = d[axis]
                        if abs(dc) > 1e-6:
                            tt = ((hi if dc > 0 else lo) - o[axis]) / dc
                            tmax = min(tmax, tt)
                    p = o + d * tmax
                    key = (round(p.x * 2) / 2, round(p.y * 2) / 2, round(p.z * 2) / 2)
                    exits[key] = exits.get(key, 0) + 1
                y += step
            x += step
    lines.append('  inside points sampled: %d' % inside)
    if inside == 0:
        lines.append('  (no enclosed inside found: an open structure, or the shell has gaps everywhere)')
    else:
        total = sum(exits.values())
        lines.append('  escaping rays: %d' % total)
        for key, n in sorted(exits.items(), key=lambda kv: -kv[1])[:12]:
            lines.append('    leaves near (%.1f, %.1f, %.1f): %d rays' % (key[0], key[1], key[2], n))

    # ---- fighting: coplanar overlapping triangles of different parts
    planes = {}
    for ti, t in enumerate(tris):
        a, b, c = verts[t[0]], verts[t[1]], verts[t[2]]
        n = (b - a).cross(c - a)
        area = n.length / 2
        if area < 1e-5:
            continue
        n.normalize()
        d = n.dot(a)
        key = (round(n.x * 50), round(n.y * 50), round(n.z * 50), round(d / 0.004))
        planes.setdefault(key, []).append(ti)
    fights = {}
    for key, lst in planes.items():
        if len(lst) < 2:
            continue
        for i in range(len(lst)):
            for j in range(i + 1, len(lst)):
                oa, ob = owner[lst[i]], owner[lst[j]]
                if oa[0] == ob[0] and oa[1] == ob[1]:
                    continue
                if tri_overlap(verts, tris[lst[i]], tris[lst[j]]):
                    ta, tb = tris[lst[i]], tris[lst[j]]
                    c = (verts[ta[0]] + verts[ta[1]] + verts[ta[2]]) / 3
                    k = (oa[2], oa[1], ob[2], ob[1])
                    f = fights.setdefault(k, [0, c])
                    f[0] += 1
    if fights:
        lines.append('  FIGHTING (coplanar overlapping faces): %d pairs of parts' % len(fights))
        for k, (n, c) in sorted(fights.items(), key=lambda kv: -kv[1][0])[:14]:
            lines.append('    %s/%s  vs  %s/%s : %d faces, e.g. at (%.2f, %.2f, %.2f)' % (k[0], k[1], k[2], k[3], n, c.x, c.y, c.z))
    else:
        lines.append('  no coplanar overlaps')
    return lines


def tri_overlap(verts, ta, tb):
    """A rough test on the shared plane: a centroid or a corner of one triangle inside the other (areas that only touch an edge do not count)."""
    A = [verts[i] for i in ta]
    B = [verts[i] for i in tb]
    n = (A[1] - A[0]).cross(A[2] - A[0])
    if n.length < 1e-9:
        return False
    n.normalize()
    ax = max(range(3), key=lambda k: abs(n[k]))
    idx = [k for k in range(3) if k != ax]

    def p2(v):
        return (v[idx[0]], v[idx[1]])

    def inside(p, tri):
        (x, y) = p
        s = []
        for i in range(3):
            (x1, y1), (x2, y2) = tri[i], tri[(i + 1) % 3]
            s.append((x2 - x1) * (y - y1) - (y2 - y1) * (x - x1))
        eps = 1e-4
        return all(v > eps for v in s) or all(v < -eps for v in s)
    a2 = [p2(v) for v in A]
    b2 = [p2(v) for v in B]
    ca = (sum(p[0] for p in a2) / 3, sum(p[1] for p in a2) / 3)
    cb = (sum(p[0] for p in b2) / 3, sum(p[1] for p in b2) / 3)
    return inside(ca, b2) or inside(cb, a2) or any(inside(p, b2) for p in a2) or any(inside(p, a2) for p in b2)


def targets(only):
    out = []
    for folder in sorted(glob.glob(os.path.join(ROOT, 'assets', 'structures', '*'))):
        sid = os.path.basename(folder)
        if only and sid not in only:
            continue
        if not only and sid.startswith(SKIP):
            continue
        for stage in ('struct_complete', 'struct_finishings'):
            for g in glob.glob(os.path.join(folder, 'stages', stage, '*.glb')):
                base = os.path.basename(g)
                if base.startswith('SM_') or base.count('_block') or base.count('_brick') or base.count('_stilts') or base.count('_poured'):
                    continue
                out.append((sid + '/' + stage, g))
    return out


def main():
    only = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    report = []
    for label, path in targets(only):
        try:
            lines = audit(path, label)
        except Exception as e:
            import traceback
            traceback.print_exc()
            lines = [label + ': FAILED ' + str(e)]
        report.extend(lines)
        print('\n'.join(lines))
    with open(os.path.join(OUT, 'structures.txt'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(report) + '\n')


if __name__ == '__main__':
    main()
