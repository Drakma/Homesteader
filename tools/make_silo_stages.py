"""
Builds the four stage models of the grain silos (foundation, framing, walls, complete) as GLBs in headless Blender: free, local, low-poly.
It reads each stage manifest of assets/structures/<id>/stages/<stage>/ (dimensions_m: width = depth = the footprint in whole metres, height = the
stage's overall height) and the SILOS table below (tower radius and body height), writes <stage item id>.glb beside the manifest and the manifest's
models[]. tools/build_silo_groups.py makes the manifests first and renders the icons afterwards.

    blender --background --python tools/make_silo_stages.py -- grain_silo_small grain_silo_medium grain_silo_large

  foundation  a round concrete slab with a plinth and the base of the discharge pad
  framing     the slab, steel posts round the circle, hoops at intervals, a top ring
  walls       the slab and the corrugated steel tower (hollow, open at the top)
  complete    the tower closed by a conical roof with a vent cap, a roof hatch, a ladder up the front, a discharge chute with its slide gate

Conventions as in docs/STRUCTURE_STAGES_GUIDE.md: 1 unit = 1 m, pivot at the centre of the footprint, ground at z = 0, front (the ladder and the chute) on
the -Y side, an empty FrontMarker in front of it. A silo has no door, so the game just says it is finished.
"""
import json
import math
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_structure_stages as base   # Builder, material

ROOT = base.ROOT
STRUCTURES = base.STRUCTURES

# id -> (tower radius, body height from the slab to the eaves)
SILOS = {
    'grain_silo_small': (1.1, 6.0),
    'grain_silo_medium': (2.0, 10.0),
    'grain_silo_large': (3.0, 15.0),
}
SLAB_H = 0.3
SIDES = 20


def ring(r, z, n=SIDES, off=0.0):
    return [(r * math.cos(2 * math.pi * i / n + off), r * math.sin(2 * math.pi * i / n + off), z) for i in range(n)]


def new_faces(b, quads, m):
    i = b.mat_index(m)
    for q in quads:
        f = b.bm.faces.new([b.bm.verts.new(p) for p in q])
        f.material_index = i


def band(b, r0, z0, r1, z1, m, n=SIDES, closed_top=False, closed_bottom=False, inward=False):
    """A tapering band of quads from (r0, z0) to (r1, z1) round the circle (a cylinder wall when r0 == r1)."""
    a, c = ring(r0, z0, n), ring(r1, z1, n)
    quads = []
    for i in range(n):
        j = (i + 1) % n
        q = (a[i], a[j], c[j], c[i])
        quads.append(q[::-1] if inward else q)
    if closed_top:
        quads.append(tuple(c[::-1]) if not inward else tuple(c))
    if closed_bottom:
        quads.append(tuple(a) if not inward else tuple(a[::-1]))
    new_faces(b, quads, m)


def disc(b, r, z, m, n=SIDES, up=True):
    pts = ring(r, z, n)
    new_faces(b, [tuple(pts) if up else tuple(pts[::-1])], m)


def cone(b, r, z0, z1, m, n=SIDES):
    a = ring(r, z0, n)
    apex = (0.0, 0.0, z1)
    i = b.mat_index(m)
    for k in range(n):
        j = (k + 1) % n
        f = b.bm.faces.new([b.bm.verts.new(a[k]), b.bm.verts.new(a[j]), b.bm.verts.new(apex)])
        f.material_index = i
    disc(b, r, z0, m, n, up=False)


def tube(b, r_out, r_in, z0, z1, m, n=SIDES):
    """A hollow wall: outer and inner surfaces and the top and bottom rims."""
    band(b, r_out, z0, r_out, z1, m, n)
    band(b, r_in, z0, r_in, z1, m, n, inward=True)
    ro, ri = ring(r_out, z1, n), ring(r_in, z1, n)
    bo, bi = ring(r_out, z0, n), ring(r_in, z0, n)
    top, bottom = [], []
    for i in range(n):
        j = (i + 1) % n
        top.append((ro[i], ro[j], ri[j], ri[i])[::-1])
        bottom.append((bo[i], bo[j], bi[j], bi[i]))
    new_faces(b, top, m)
    new_faces(b, bottom, m)


def mats():
    return {
        'concrete': base.material('Concrete', (0.6, 0.6, 0.58), 0.95),
        'steel': base.material('Siding', (0.8, 0.83, 0.85), 0.4),
        'dark': base.material('SteelDark', (0.33, 0.36, 0.38), 0.55),
        'roof': base.material('Roof', (0.3, 0.36, 0.42), 0.5),
    }


def foundation(b, fb, R, H, M):
    rs = R + 0.4
    band(fb, rs, 0.0, rs, SLAB_H, M['concrete'], closed_top=True, closed_bottom=True)
    band(fb, R + 0.12, SLAB_H, R + 0.12, SLAB_H + 0.1, M['concrete'], closed_top=True)      # the plinth the tower stands on
    # the discharge pad: a small apron in front of the chute
    fb.box(-0.5, 0.5, -(rs + 0.45), -(rs - 0.25), 0.0, SLAB_H * 0.8, M['concrete'])


def framing(b, fb, R, H, M):
    foundation(b, fb, R, H, M)
    posts = 8 if R < 1.5 else (12 if R < 2.5 else 16)
    z0, z1 = SLAB_H + 0.1, SLAB_H + H
    pts = [(R * math.cos(2 * math.pi * i / posts), R * math.sin(2 * math.pi * i / posts)) for i in range(posts)]
    for x, y in pts:
        b.log((x, y, z0), (x, y, z1), 0.06, M['dark'], sides=6)
    levels = max(3, int(H / 2.2))
    for k in range(levels + 1):
        z = z0 + (z1 - z0) * k / levels
        for i in range(posts):
            a, c = pts[i], pts[(i + 1) % posts]
            b.log((a[0], a[1], z), (c[0], c[1], z), 0.045, M['dark'], sides=4)
    # diagonal bracing in the lowest bay, as a start of the panels
    for i in range(0, posts, 2):
        a, c = pts[i], pts[(i + 1) % posts]
        b.log((a[0], a[1], z0), (c[0], c[1], z0 + (z1 - z0) / levels), 0.03, M['dark'], sides=4)


def corrugation(b, R, z0, z1, M, step=0.5):
    z = z0 + step
    while z < z1 - 0.05:
        band(b, R + 0.03, z, R + 0.03, z + 0.07, M['steel'], n=16)
        z += step


def walls(b, fb, R, H, M, roofed=False):
    foundation(b, fb, R, H, M)
    z0, z1 = SLAB_H + 0.1, SLAB_H + H
    tube(b, R, R - 0.05, z0, z1, M['steel']) if not roofed else band(b, R, z0, R, z1, M['steel'], closed_bottom=True)
    band(b, R + 0.025, z0, R + 0.025, z0 + 0.35, M['dark'])      # the anchor ring at the base
    corrugation(b, R, z0 + 0.35, z1, M)
    band(b, R + 0.04, z1 - 0.12, R + 0.04, z1, M['dark'])           # the top ring (eave stiffener)


def complete(b, fb, R, H, M):
    walls(b, fb, R, H, M, roofed=True)
    z1 = SLAB_H + H
    rise = R * 0.55
    cone(b, R + 0.14, z1, z1 + rise, M['roof'])
    band(b, R + 0.14, z1 - 0.06, R + 0.14, z1, M['roof'])           # the roof edge
    # vent cap on the apex
    vz = z1 + rise
    band(b, 0.16 + 0.04 * R, vz - 0.04, 0.16 + 0.04 * R, vz + 0.22, M['dark'], closed_top=True)
    cone(b, 0.26 + 0.05 * R, vz + 0.22, vz + 0.45, M['roof'])
    # a roof hatch on the +Y slope
    hy = (R + 0.14) * 0.55
    hz = z1 + rise * (1 - 0.55) - 0.02
    b.box(-0.3, 0.3, hy - 0.3, hy + 0.3, hz, hz + 0.16, M['dark'])
    # the ladder up the front (-Y): rails, rungs and stand-off brackets
    fy = -(R + 0.12)
    top = z1 + 0.45
    for sx in (-0.2, 0.2):
        b.box(sx - 0.025, sx + 0.025, fy - 0.07, fy - 0.01, SLAB_H + 0.5, top, M['dark'])
    z = SLAB_H + 0.8
    while z < top - 0.1:
        b.box(-0.2, 0.2, fy - 0.05, fy - 0.01, z, z + 0.035, M['dark'])
        z += 0.3
    z = SLAB_H + 1.2
    while z < top - 0.3:
        for sx in (-0.2, 0.2):
            b.box(sx - 0.02, sx + 0.02, fy - 0.01, fy + 0.07, z, z + 0.05, M['dark'])
        z += 1.6
    # the discharge chute: a short horizontal spout through the wall near the base with its slide gate
    cz = SLAB_H + 0.9
    b.log((0.0, -(R - 0.1), cz), (0.0, -(R + 0.65), cz), 0.12, M['dark'], sides=8)
    b.box(-0.17, 0.17, -(R + 0.45), -(R + 0.3), cz - 0.17, cz + 0.2, M['steel'])      # the slide gate
    b.box(-0.2, 0.2, -(R + 0.62), -(R + 0.58), cz - 0.2, cz + 0.2, M['dark'])          # the spout flange


def stage_manifest(structure, stage_folder):
    folder = os.path.join(STRUCTURES, structure, 'stages', stage_folder)
    for fn in sorted(os.listdir(folder)):
        if fn.endswith('.json'):
            return folder, os.path.join(folder, fn)
    raise FileNotFoundError(folder)


STAGES = [('struct_foundation', foundation), ('struct_framing', framing), ('struct_walls', walls), ('struct_complete', complete)]


def main():
    argv = sys.argv
    ids = argv[argv.index('--') + 1:] if '--' in argv else list(SILOS)
    for structure in ids:
        R, H = SILOS[structure]
        for stage_folder, fn in STAGES:
            folder, manifest_path = stage_manifest(structure, stage_folder)
            d = json.load(open(manifest_path, encoding='utf-8'))
            dims = d['category_fields']['dimensions_m']
            w, depth, h = dims['width'], dims['depth'], dims['height']
            for o in list(bpy.data.objects):
                bpy.data.objects.remove(o, do_unlink=True)
            M = mats()
            b = base.Builder(d['id'])
            fb = base.Builder('Foundation')      # the slab and plinth: its own object, so another foundation style can replace it
            fn(b, fb, R, H, M)
            fobj = fb.finish()
            obj = b.finish()
            marker = bpy.data.objects.new('FrontMarker', None)
            marker.location = (0.0, -depth / 2 - 0.8, 0.05)
            bpy.context.collection.objects.link(marker)
            bpy.ops.object.select_all(action='DESELECT')
            for o in (obj, fobj, marker):
                o.select_set(True)
            bpy.context.view_layer.objects.active = obj
            out = os.path.join(folder, d['id'] + '.glb')
            bpy.ops.export_scene.gltf(filepath=out, export_format='GLB', use_selection=True, export_yup=True)
            tris = sum(len(p.vertices) - 2 for o in (obj, fobj) for p in o.data.polygons)
            d['models'] = [{'file': d['id'] + '.glb', 'format': 'glb', 'dimensions_m': {'x': w, 'y': h, 'z': depth}, 'triangles': tris}]
            json.dump(d, open(manifest_path, 'w', encoding='utf-8'), indent=2)
            print('stage', d['id'], tris, 'tris ->', out)


if __name__ == '__main__':
    main()
