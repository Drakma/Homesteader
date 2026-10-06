"""
Cures texture fighting (z-fighting) in the structure models, in headless Blender: free, local.

    blender --background --python tools/fix_structure_overlaps.py                    (every stage model of every structure)
    blender --background --python tools/fix_structure_overlaps.py -- barn small_cabin
    blender --background --python tools/fix_structure_overlaps.py -- --check          (only count, change nothing)

Two faces of different parts or materials that lie in the same plane, face the same way and overlap are drawn on the same depth: the picture flickers between them
(trim lying flush with siding, a floor on the slab, a roof board on a rafter). For each such pair the face of the LAYER THAT SITS ON TOP (by material: trim over siding,
a floor over the slab, glass over everything, ...) is lifted 5 mm along its own normal, so the two never share a depth. The model is written back as a GLB.

The structure generators (make_structure_stages.py, make_building_stages.py, make_house_stages.py) write models that fight like this, so run this AFTER generating, and then
python tools/package_catalog_as_mods.py to copy the models into the mod. docs/STRUCTURE_STAGES_GUIDE.md.
"""
import glob
import importlib.util
import os
import sys

import bpy
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location('audit_structures', os.path.join(ROOT, 'tools', 'audit_structures.py'))
aud = importlib.util.module_from_spec(spec)
spec.loader.exec_module(aud)

LIFT = 0.005
WINDOW = 0.004                                     # planes closer than this are the same plane

# what sits on top of what: the higher number is lifted off the lower
PRIORITY = {
    'concrete': 0, 'steel': 0, 'stone': 0, 'brick': 0, 'masonry': 1, 'sheathing': 1, 'siding': 1, 'log': 1, 'roof': 1, 'metal': 1, 'corrugated': 1,
    'shingle': 2, 'interior': 3, 'floor': 3, 'deck': 3, 'concretedark': 3, 'flooring': 3, 'carpet': 3, 'tile': 3,
    'timber': 4, 'trim': 4, 'aluminium': 4, 'frame': 4, 'hearth': 4, 'door': 4, 'soot': 5, 'glass': 6,
}


def prio(matname):
    base = matname.split('.')[0].lower()
    if base in PRIORITY:
        return PRIORITY[base]
    for k, v in PRIORITY.items():
        if base.startswith(k):
            return v
    return 2


def process(path, fix):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=path)
    objs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    if not objs:
        return 0, 0
    verts, tris, owner = aud.tris_world(objs)
    # which object, which vertex of it: the same order as tris_world builds them
    index_of = []
    base = 0
    for o in objs:
        index_of.append((o, base, len(o.data.vertices)))
        base += len(o.data.vertices)

    groups = {}
    normals = []
    for ti, t in enumerate(tris):
        a, b, c = verts[t[0]], verts[t[1]], verts[t[2]]
        n = (b - a).cross(c - a)
        if n.length / 2 < 1e-5:
            normals.append(None)
            continue
        n.normalize()
        normals.append(n)
        groups.setdefault((round(n.x * 50), round(n.y * 50), round(n.z * 50)), []).append((n.dot(a), ti))

    lifts = {}          # triangle index -> True
    pairs = 0
    for lst in groups.values():
        lst.sort()
        for i in range(len(lst)):
            di, ti = lst[i]
            j = i + 1
            while j < len(lst) and lst[j][0] - di < WINDOW:
                tj = lst[j][1]
                j += 1
                oa, ob = owner[ti], owner[tj]
                if oa[0] == ob[0] and oa[1] == ob[1]:
                    continue
                if not aud.tri_overlap(verts, tris[ti], tris[tj]):
                    continue
                pairs += 1
                pa, pb = prio(oa[1]), prio(ob[1])
                if pa != pb:
                    top = ti if pa > pb else tj
                else:
                    top = tj                                       # the same kind of layer: the later one
                lifts[top] = True
    moved = 0
    if fix and lifts:
        offsets = {}        # global vertex index -> summed world offset
        for ti in lifts:
            n = normals[ti]
            for vi in tris[ti]:
                offsets[vi] = offsets.get(vi, Vector((0, 0, 0))) + n * LIFT
        for vi, off in offsets.items():
            if off.length > LIFT * 1.5:
                off = off.normalized() * LIFT * 1.5
            for o, b0, cnt in index_of:
                if b0 <= vi < b0 + cnt:
                    local = o.matrix_world.inverted().to_3x3() @ off
                    o.data.vertices[vi - b0].co += local
                    moved += 1
                    break
        for o in objs:
            o.data.update()
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=False, export_yup=True)
    return pairs, moved


def main():
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    check = '--check' in args
    only = [a for a in args if not a.startswith('--')]
    total_before = 0
    for folder in sorted(glob.glob(os.path.join(ROOT, 'assets', 'structures', '*'))):
        sid = os.path.basename(folder)
        if only and sid not in only:
            continue
        if not only and sid.startswith(aud.SKIP):
            continue
        for g in sorted(glob.glob(os.path.join(folder, 'stages', '*', '*.glb'))):
            base = os.path.basename(g)
            if base.startswith('SM_'):
                continue
            try:
                pairs, moved = process(g, not check)
            except Exception as e:
                import traceback
                traceback.print_exc()
                print('FAILED', g, e)
                continue
            total_before += pairs
            print('%s/%s: %d overlapping pairs%s' % (sid, base, pairs, '' if check else ', %d vertices lifted' % moved))
    print('TOTAL pairs', total_before)


if __name__ == '__main__':
    main()
