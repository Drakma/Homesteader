"""
Builds the four stage models of the manual well (foundation, framing, walls, complete) as GLBs in headless Blender: free, local, low-poly.
Reads each stage manifest of assets/structures/<id>/stages/<stage>/ and writes <stage item id>.glb beside it (and the manifest's models[]).
tools/build_well_group.py makes the manifests first and renders the icons afterwards.

    blender --background --python tools/make_well_stages.py -- water_well_manual

  foundation  a gravel apron and a round concrete footing ring
  framing     the footing and the stone lining of the shaft (courses of fieldstone), dark water at the bottom
  walls       the lining carried up to a waist-high curb, two timber posts and the cross beam between them
  complete    the posts and beam under a small shingled gable roof, a windlass with its crank, the rope and a bucket

Conventions as in docs/STRUCTURE_STAGES_GUIDE.md: 1 unit = 1 m, pivot at the centre of the footprint, ground at z = 0, front on the -Y side,
an empty FrontMarker in front of it. A well has no door, so the game just says it is finished.
"""
import json
import math
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_structure_stages as base   # Builder, material
import make_silo_stages as silo         # band, tube, disc, cone (round shapes)

STRUCTURES = base.STRUCTURES
WELLS = ['water_well_manual']
SIDES = 24
COURSE_H = 0.13
FOOT_H = 0.18
R_OUT, R_IN = 0.74, 0.46


def mats():
    return {
        'concrete': base.material('Concrete', (0.6, 0.6, 0.58), 0.95),
        'gravel': base.material('Gravel', (0.55, 0.53, 0.5), 1.0),
        'stone': base.material('Masonry', (0.62, 0.6, 0.56), 0.95),
        'water': base.material('Water', (0.08, 0.16, 0.22), 0.1),
        'log': base.material('Log', (0.5, 0.36, 0.22), 0.9),
        'wood': base.material('Plank', (0.62, 0.48, 0.3), 0.9),
        'roof': base.material('Shingle', (0.36, 0.3, 0.26), 0.9),
        'rope': base.material('Rope', (0.72, 0.62, 0.42), 1.0),
        'metal': base.material('SteelDark', (0.33, 0.36, 0.38), 0.55),
    }


def foundation(b, fb, M):
    silo.band(fb, 1.0, 0.0, 1.0, 0.04, M['gravel'], n=SIDES, closed_top=True)                    # the gravel apron round the well
    silo.tube(fb, 0.82, 0.42, 0.0, FOOT_H, M['concrete'], n=SIDES)                                # the footing ring


def lining(b, M, courses):
    """The stone lining: stacked courses, each a hollow ring, the joints staggered by a turn and the radius varying a little."""
    for k in range(courses):
        z0 = FOOT_H + k * COURSE_H
        r = R_OUT + (0.012 if k % 2 else 0.0)
        silo.tube(b, r, R_IN, z0, z0 + COURSE_H * 0.97, M['stone'], n=SIDES)
    silo.disc(b, R_IN - 0.01, FOOT_H + 0.05, M['water'], n=SIDES)                                  # the dark water far down the shaft
    # a cap stone ring on the top course
    ztop = FOOT_H + courses * COURSE_H
    silo.tube(b, R_OUT + 0.06, R_IN - 0.04, ztop, ztop + 0.05, M['stone'], n=SIDES)


def framing(b, fb, M):
    foundation(b, fb, M)
    lining(b, M, 4)


def walls(b, fb, M, roofed=False):
    foundation(b, fb, M)
    lining(b, M, 6)
    ztop = FOOT_H + 6 * COURSE_H + 0.05
    for sx in (-0.88, 0.88):
        b.log((sx, 0.0, FOOT_H), (sx, 0.0, 2.05), 0.07, M['log'], sides=8)              # the two posts
        b.box(sx - 0.14, sx + 0.14, -0.14, 0.14, FOOT_H, FOOT_H + 0.08, M['log'])         # their feet
    b.log((-0.95, 0.0, 2.0), (0.95, 0.0, 2.0), 0.065, M['log'], sides=8)                     # the cross beam
    for sx, d in ((-0.88, 1), (0.88, -1)):
        b.log((sx, 0.0, 1.55), (sx + d * 0.3, 0.0, 2.0), 0.035, M['log'], sides=6)           # knee braces


def complete(b, fb, M):
    walls(b, fb, M, roofed=True)
    for sx in (-1.0, 1.0):
        b.roof_slab(sx, 2.02, 2.5, -0.72, 0.72, 0.04, M['roof'])                            # the two roof slopes
    for y in (-0.69, 0.69):
        # the gable sits 2 cm below the slabs' top and 1 cm inside their ends, so none of its faces lies in the same plane as a roof face (they z-fought there)
        b.prism_gable(-1.0, 1.0, y, 0.04, 2.0, 2.48, M['wood'])                            # the gable ends
    b.log((0.0, -0.72, 2.5), (0.0, 0.72, 2.5), 0.04, M['log'], sides=6)                      # the ridge
    # the windlass: a log across the posts under the beam, a crank handle at one end, the rope down to the bucket
    b.log((-0.92, 0.0, 1.72), (0.92, 0.0, 1.72), 0.07, M['wood'], sides=10)
    b.log((0.92, 0.0, 1.72), (1.05, 0.0, 1.72), 0.03, M['metal'], sides=6)
    b.log((1.05, 0.0, 1.72), (1.05, -0.28, 1.72), 0.02, M['metal'], sides=6)
    b.log((1.05, -0.28, 1.72), (1.05, -0.28, 1.5), 0.025, M['wood'], sides=6)
    b.log((0.0, 0.0, 1.66), (0.0, 0.0, 1.02), 0.012, M['rope'], sides=5)
    silo.band(b, 0.12, 0.86, 0.14, 1.04, M['wood'], n=12, closed_bottom=True)               # the bucket
    b.log((-0.14, 0.0, 1.04), (0.14, 0.0, 1.04), 0.008, M['metal'], sides=4)                 # its bail


def stage_manifest(structure, stage_folder):
    folder = os.path.join(STRUCTURES, structure, 'stages', stage_folder)
    for fn in sorted(os.listdir(folder)):
        if fn.endswith('.json'):
            return folder, os.path.join(folder, fn)
    raise FileNotFoundError(folder)


STAGES = [('struct_foundation', foundation), ('struct_framing', framing), ('struct_walls', walls), ('struct_complete', complete)]


def main():
    argv = sys.argv
    ids = argv[argv.index('--') + 1:] if '--' in argv else list(WELLS)
    for structure in ids:
        for stage_folder, fn in STAGES:
            folder, manifest_path = stage_manifest(structure, stage_folder)
            d = json.load(open(manifest_path, encoding='utf-8'))
            dims = d['category_fields']['dimensions_m']
            w, depth, h = dims['width'], dims['depth'], dims['height']
            for o in list(bpy.data.objects):
                bpy.data.objects.remove(o, do_unlink=True)
            M = mats()
            b = base.Builder(d['id'])
            fb = base.Builder('Foundation')
            fn(b, fb, M)
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
