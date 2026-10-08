"""
Builds the L-SHAPED HOUSE (assets/structures/l_house) in headless Blender: free, local, low-poly. Same five construction stages, conventions and recipes as the farmhouse
(docs/STRUCTURE_STAGES_GUIDE.md), but two WINGS joined into an L:

    wing A  the long front wing, 16 x 9 m, ridge left to right, porch along the whole front, front door, the living / kitchen / dining room, a bedroom, bath and laundry
    wing B  the cross wing behind it on the right, 8 m wide and 10 m deep, ridge front to back, a den in front and two bedrooms behind

Each wing is built with the rectangular builders of tools/make_building_stages.py (so walls, windows, framing, roofs, partitions and doors are the same), then put together:
wing B is built 4.5 m longer than it is, to run its roof up into the main roof (the valley), and everything of it that is not roof is cut off where it meets the main wing's
back wall (a wide doorway in that wall joins the two). Its wall parts are renamed "Wall_Left@B" ... so the game finds one wall rectangle per wing (ConstructionSite.WallRects).

    blender --background --python tools/make_l_house.py
    then: python tools/fix_structure_overlaps.py (blender) -- l_house ; python tools/make_l_house.py --icons ; generate_unity_asset_catalog.py ; package_catalog_as_mods.py
"""
import copy
import json
import os
import subprocess
import sys

import bmesh
import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_building_stages as mb  # noqa: E402
import make_structure_stages as base  # noqa: E402

ROOT = base.ROOT
STRUCTURES = base.STRUCTURES
SID = 'l_house'
NAME = 'L-Shaped House'
Builder = base.Builder
win = mb.win

# wing A (the main wing) and wing B (the cross wing), in metres
AW, AD, PORCH = 16.0, 9.0, 1.8
BW, BD = 8.0, 10.0
BX = 4.0                                    # the cross wing's centre x (it stands against the right end: x 0 .. 8 of -8 .. 8)
FOUND, WALL_H, H_TOTAL = 0.3, 2.7, 6.4
IN = mb.IN
EXT = AD / 2                                # the cross wing is built this much longer, into the main wing, so its roof meets the main ridge
CUT_Y = AD / 2 - IN                         # (in the main wing's own coordinates) where everything but the cross wing's roof is cut off: the main wing's back wall, inside face
DOORWAY = (1.5, 6.5)                        # the opening in the main wing's back wall, x

PALETTE = dict(siding=(0.9, 0.9, 0.86), trim=(0.97, 0.97, 0.95), shutter=(0.2, 0.28, 0.34), shingle=(0.3, 0.27, 0.28), shingle_dark=(0.2, 0.18, 0.19),
               door=(0.2, 0.3, 0.38), door_panel=(0.16, 0.25, 0.32))

CFG_A = dict(
    name=NAME, ceiling=True, rib_course=0.5, w=AW, d=AD, wall_h=WALL_H, h_total=H_TOTAL, found_h=FOUND, ov=0.4, porch=PORCH, stages=5, style='siding', ridge_x=True,
    chimney=('left', -0.6), palette=PALETTE, door_x=0.0, shutters=True,
    openings=dict(front=[win(-6.0), win(-2.6), win(2.6), win(6.0)],
                  back=[win(-6.5), win(-1.0), (DOORWAY[0], DOORWAY[1], 0.0, 2.4)],
                  left=[win(-1.0), win(2.8, 0.7, 0.6, 1.5)],
                  right=[win(-0.8)]),
    partitions=[dict(axis='x', pos=-3.5, lo=None, hi=None, h=None, doors=[(-1.2, -0.3), (2.4, 3.3)]),          # the west block: bedroom, bath, laundry
                dict(axis='y', pos=0.7, lo=None, hi=-3.5, h=None, doors=[]),
                dict(axis='x', pos=-5.75, lo=0.7, hi=None, h=None, doors=[(2.3, 3.2)])])

# the cross wing: built EXT longer at its front (toward the main wing's ridge)
BDE = BD + EXT
CFG_B = dict(
    name=NAME + ' (cross wing)', ceiling=True, rib_course=0.5, w=BW, d=BDE, wall_h=WALL_H, h_total=H_TOTAL, found_h=FOUND, ov=0.4, stages=5, style='siding', open_front=True,
    palette=PALETTE, door_x=0.0, shutters=False,
    openings=dict(front=[], back=[win(-2.0), win(2.0)], left=[win(-1.0), win(2.0), win(4.0)], right=[win(-1.0), win(2.0), win(4.0)]),
    partitions=[])


def cut_local():
    """Where the main wing's inner back face is, in the cross wing's own coordinates (its centre is the middle of its extended length)."""
    # in the L's coordinates (the main wing's centre is y = 0) the cross wing runs from y = 0 to y = BDE; its centre is at BDE / 2
    return CUT_Y - BDE / 2


def b_partitions():
    cut = cut_local()
    den_back = cut + 4.3                                           # the den (open to the main wing) is 4.3 m deep, the bedrooms behind it
    inner_hi = BDE / 2 - IN
    return [dict(axis='y', pos=den_back, lo=None, hi=None, h=None, doors=[(-2.1, -1.2), (1.2, 2.1)]),
            dict(axis='x', pos=0.0, lo=den_back, hi=None, h=None, doors=[])]


# ------------------------------------------------------------------ putting the wings together

def clip(obj, y_cut):
    """Cuts a mesh object off at the plane y = y_cut (its own coordinates), keeping y >= y_cut."""
    if obj.type != 'MESH':
        return
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
    bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(0.0, y_cut, 0.0), plane_no=(0.0, 1.0, 0.0), clear_inner=True)
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()


def join_into(target, other):
    bpy.ops.object.select_all(action='DESELECT')
    other.select_set(True)
    target.select_set(True)
    bpy.context.view_layer.objects.active = target
    bpy.ops.object.join()


KEEP_WHOLE = ('Roof', 'WindowGlass')            # the cross wing's roof and glass are kept whole (the roof runs on up into the main roof)


def is_window_object(name):
    """The movable windows' objects (WindowFrame_k, WindowGlass_k, WindowMuntin_k_n, WinSpec_k_...): numbered across both wings, so they keep their names, and they are never cut."""
    return name.startswith('WinSpec_') or (name.startswith('Window') and name != 'WindowGlass')


def respec(o, du_x, du_y, suffix):
    """A WinSpec empty written in its own wing's frame is rewritten in the whole house's: the offset of the wing is added along the wall (x for the front and back walls, y for the
    left and right ones), the wall gets the wing's tag, and the empty goes back to the origin (the game reads where the loader moved the model from it: docs/WINDOWS.md)."""
    p = o.name.split('.')[0].split('_')
    if len(p) < 7:
        return
    wall = p[2]
    d = du_x if wall in ('front', 'back') else du_y
    p[2] = wall + suffix
    p[3] = str(int(p[3]) + round(d * 1000))
    p[4] = str(int(p[4]) + round(d * 1000))
    o.name = '_'.join(p)
    o.location = (0.0, 0.0, 0.0)


def interior_inside_cross_wing():
    """The main wing's back wall is an OUTSIDE wall only where nothing stands behind it. Where the cross wing is built against it (x 0 .. 8) its back face is a room wall: the faces of the
    siding, sheathing and trim layers that look into the cross wing (and the reveals of the doorway between the two) take the interior finish, so no siding shows inside. The wall is split at
    the cross wing's two sides first, so only the part inside the cross wing changes. The doorway (the arch between the living room and the den) gets a casing of trim on both sides."""
    wall = bpy.data.objects.get('Wall_Back')
    if wall is None or wall.type != 'MESH':
        return
    mats = wall.data.materials
    slot = next((i for i, m in enumerate(mats) if m is not None and m.name.startswith('Interior')), None)
    trim = next((i for i, m in enumerate(mats) if m is not None and m.name.startswith('Trim')), None)
    if slot is None:
        return
    outer = tuple(i for i, m in enumerate(mats) if m is not None and m.name.split('.')[0] in ('Siding', 'Sheathing', 'Trim'))
    x0, x1 = BX - BW / 2, BX + BW / 2
    d0, d1 = DOORWAY[0], DOORWAY[1]
    bm = bmesh.new()
    bm.from_mesh(wall.data)
    for xp in (x0, x1):
        bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(xp, 0.0, 0.0), plane_no=(1.0, 0.0, 0.0))
    bm.normal_update()
    n = 0
    flat = set()                                                                 # the outer vertices of the siding boards inside the cross wing: flattened below
    siding = tuple(i for i, m in enumerate(mats) if m is not None and m.name.startswith('Siding'))
    den_y, liv_y, jz0, jz1 = None, None, None, None
    for f in bm.faces:
        c = f.calc_center_median()
        if not (x0 - 1e-4 <= c.x <= x1 + 1e-4):
            continue
        if f.material_index in outer and f.normal.y > 0.5:
            if f.material_index in siding:
                flat.update(f.verts)
            f.material_index = slot
            n += 1
            den_y = c.y if den_y is None else max(den_y, c.y)
        elif f.normal.y < -0.5 and f.material_index == slot and abs(c.x - (d0 + d1) / 2) < (d1 - d0) / 2:
            liv_y = c.y if liv_y is None else min(liv_y, c.y)
        elif abs(f.normal.x) > 0.9 and (abs(c.x - d0) < 0.03 or abs(c.x - d1) < 0.03):
            if f.material_index in outer:
                f.material_index = slot                                          # the reveal of the doorway
            for v in f.verts:
                jz0 = v.co.z if jz0 is None else min(jz0, v.co.z)
                jz1 = v.co.z if jz1 is None else max(jz1, v.co.z)
    if flat:
        # the clapboards are lapped (each board stands a little proud of the one under it), which still shows on the den side as a siding pattern: the outer face is made one flat plane
        y_flat = max(v.co.y for v in flat)
        for v in flat:
            v.co.y = y_flat
        den_y = y_flat
    if trim is not None and den_y is not None and jz1 is not None and jz1 - jz0 > 1.0:
        t, k, out = 0.07, 0.015, 0.0
        head = jz1                                                               # the top of the doorway
        for y_face, direction in ((den_y, 1.0), (liv_y, -1.0)):
            if y_face is None:
                continue
            ya, yb = (y_face, y_face + k) if direction > 0 else (y_face - k, y_face)
            for (ax0, ax1, az0, az1) in ((d0 - t, d0, jz0, head + t), (d1, d1 + t, jz0, head + t), (d0 - t, d1 + t, head, head + t)):
                res = bmesh.ops.create_cube(bm, size=1.0)
                for v in res['verts']:
                    v.co.x = ax0 + (v.co.x + 0.5) * (ax1 - ax0)
                    v.co.y = ya + (v.co.y + 0.5) * (yb - ya)
                    v.co.z = az0 + (v.co.z + 0.5) * (az1 - az0)
                for f in {f for v in res['verts'] for f in v.link_faces}:
                    f.material_index = trim
    bm.to_mesh(wall.data)
    bm.free()
    wall.data.update()
    print('l_house: %d back-wall faces inside the cross wing given the interior finish; doorway z %s..%s' % (n, jz0, jz1))


def build_stage(folder, sid_stage_id):
    """Both wings of one stage, put together. Returns (main object, extra objects)."""
    import make_house_stages as hs
    M = mb.palette(CFG_A)
    cfg_b = copy.deepcopy(CFG_B)
    cfg_b['partitions'] = b_partitions()

    def wing(cfg):
        base.EXTRA_OBJECTS[:] = []
        c = mb.BCtx(cfg, cfg['h_total'], cfg['found_h'])
        hs.glass_builder = None
        b = Builder(sid_stage_id)
        mb.glass_builder = Builder('WindowGlass')
        mb.FB = Builder('Foundation')
        mb.PB = Builder('Porch')
        if folder == 'struct_foundation':
            mb.foundation(b, c, M)
        elif folder == 'struct_framing':
            mb.framing(b, c, M)
        elif folder == 'struct_walls':
            mb.walls_stage(b, c, M)
        else:
            hs.glass_builder = mb.glass_builder
            mb.complete(b, c, M, finishings=(folder == 'struct_finishings'))
            base.EXTRA_OBJECTS.append(mb.glass_builder.finish())
        if folder != 'struct_foundation' or True:
            base.EXTRA_OBJECTS.append(mb.FB.finish())
        mb.FB = None
        if mb.PB.bm.verts:
            base.EXTRA_OBJECTS.append(mb.PB.finish())
        else:
            mb.PB.bm.free()
        mb.PB = None
        return b.finish()

    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    wing(CFG_A)
    for o in bpy.data.objects:
        o.name = 'A:' + o.name
    a_all = list(bpy.data.objects)
    wing(cfg_b)
    b_all = [o for o in bpy.data.objects if not o.name.startswith('A:')]

    front, back = -AD / 2, BDE                                      # the L's extent front to back, the main wing's centre being y = 0
    shift = Vector((0.0, -(front + back) / 2, 0.0))                 # the model's origin is the middle of the footprint
    cut = cut_local()
    tops_b = [o for o in b_all if o.parent is None]
    for o in tops_b:
        if o.type == 'MESH' and o.name.split('.')[0] not in KEEP_WHOLE and not is_window_object(o.name.split('.')[0]):
            clip(o, cut)
    for o in a_all:
        if o.parent is None:
            o.location += shift
    for o in tops_b:
        o.location += Vector((BX, BDE / 2, 0.0)) + shift

    for o in b_all:                                                 # (children first: their parents keep their own names for the doors' sake)
        n = o.name.split('.')[0]
        if o.parent is not None and not is_window_object(n):
            o.name = n + '.B'
    for o in tops_b:
        n = o.name.split('.')[0]
        target = bpy.data.objects.get('A:' + n)
        if n.startswith('WinSpec_'):
            respec(o, BX + shift.x, BDE / 2 + shift.y, '@B')
        elif is_window_object(n):
            o.name = n                                              # numbered across both wings: no tag needed
        elif n.startswith('Wall_'):
            o.name = n + '@B'
        elif target is not None and n in ('Roof', 'WindowGlass', 'Foundation', 'Porch', 'Chimney', sid_stage_id):
            join_into(target, o)
        else:
            o.name = n + '.B'
    mains = None
    for o in a_all:
        if o.name.startswith('A:'):
            o.name = o.name[2:]
            if o.name.startswith('WinSpec_'):
                respec(o, shift.x, shift.y, '')
    interior_inside_cross_wing()
    main = bpy.data.objects[sid_stage_id]
    extras = [o for o in bpy.data.objects if o is not main and o.type in ('MESH', 'EMPTY') and o.parent is None and o.name != 'FrontMarker']
    return main, extras


# ------------------------------------------------------------------ manifests

def scale_recipe(node, k):
    if isinstance(node, list):
        return [scale_recipe(n, k) for n in node]
    if isinstance(node, dict):
        out = {}
        for key, v in node.items():
            if key == 'quantity' and isinstance(v, (int, float)):
                out[key] = max(1, int(round(v * k)))
            else:
                out[key] = scale_recipe(v, k)
        return out
    return node


def manifests(total_d):
    src = os.path.join(STRUCTURES, 'farmhouse')
    dst = os.path.join(STRUCTURES, SID)
    area = AW * AD + BW * BD
    k = area / (10.0 * 12.0)
    g = json.load(open(os.path.join(src, 'farmhouse.json'), encoding='utf-8'))
    g['id'] = SID
    g['name'] = NAME
    g['icon'] = SID + '.png'
    g['description'] = 'A large single-storey L-shaped house: a long front wing with a porch and a cross wing behind it, room for a family and a full set of furniture.'
    g['growth']['species'] = SID
    for s in g['growth']['stages']:
        s['construction_recipe'] = scale_recipe(s['construction_recipe'], k)
        s['icon'] = s['icon'].replace('farmhouse', SID)
        s['resource'] = s.get('resource', '')
    g['properties']['base_value'] = round(g['properties'].get('base_value', 2500) * k)
    os.makedirs(dst, exist_ok=True)
    json.dump(g, open(os.path.join(dst, SID + '.json'), 'w', encoding='utf-8'), indent=2)
    for folder in mb.STAGE_FOLDERS:
        sfolder = os.path.join(src, 'stages', folder)
        if not os.path.isdir(sfolder):
            continue
        m = json.load(open(os.path.join(sfolder, '%s_farmhouse.json' % folder), encoding='utf-8'))
        m['id'] = '%s_%s' % (folder, SID)
        m['name'] = m['name'].replace('Farmhouse', NAME)
        m['icon'] = m['id'] + '.png'
        m['description'] = m.get('description', '').replace('farmhouse', 'house')
        cf = m['category_fields']
        cf['dimensions_m'] = {'width': AW, 'depth': round(total_d, 2), 'height': FOUND if folder == 'struct_foundation' else H_TOTAL}
        cf['construction_recipe'] = scale_recipe(cf.get('construction_recipe', []), k)
        cf['room_count'] = 8
        cf['interior_area_m2'] = round(area * 0.8, 1)
        m['properties']['weight_kg'] = round(area * 90.0, 1)
        m['properties']['base_value'] = round(m['properties'].get('base_value', 0) * k)
        m['models'] = []
        d = os.path.join(dst, 'stages', folder)
        os.makedirs(d, exist_ok=True)
        json.dump(m, open(os.path.join(d, m['id'] + '.json'), 'w', encoding='utf-8'), indent=2)
        open(os.path.join(d, 'README.md'), 'w', encoding='utf-8').write('# %s\n\nStage of the %s (generated by tools/make_l_house.py).\n' % (m['name'], NAME))


def build_all():
    total_d = AD / 2 + BDE + 0.0 - (-AD / 2) - AD / 2 + 0.0
    total_d = BDE + AD / 2                                          # from the main wing's front wall to the cross wing's back wall
    manifests(total_d)
    for folder in mb.STAGE_FOLDERS:
        sid_stage_id = '%s_%s' % (folder, SID)
        sfolder = os.path.join(STRUCTURES, SID, 'stages', folder)
        mpath = os.path.join(sfolder, sid_stage_id + '.json')
        d = json.load(open(mpath, encoding='utf-8'))
        obj, extras = build_stage(folder, sid_stage_id)
        marker = bpy.data.objects.new('FrontMarker', None)
        marker.location = (0.0, -total_d / 2 - 0.8, 0.05)
        bpy.context.collection.objects.link(marker)
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        marker.select_set(True)
        for e in extras:
            e.select_set(True)
        bpy.context.view_layer.objects.active = obj
        out = os.path.join(sfolder, sid_stage_id + '.glb')
        bpy.ops.export_scene.gltf(filepath=out, export_format='GLB', use_selection=True, export_yup=True)
        tris = sum(len(p.vertices) - 2 for p in obj.data.polygons)
        for e in extras:
            if getattr(e, 'data', None) is not None and hasattr(e.data, 'polygons'):
                tris += sum(len(p.vertices) - 2 for p in e.data.polygons)
        d['models'] = [{'file': sid_stage_id + '.glb', 'format': 'glb', 'dimensions_m': {'x': AW, 'y': d['category_fields']['dimensions_m']['height'], 'z': round(total_d, 2)}, 'triangles': tris}]
        json.dump(d, open(mpath, 'w', encoding='utf-8'), indent=2)
        print('stage', sid_stage_id, tris, 'tris ->', out)


def make_icons():
    tools = os.path.join(ROOT, 'tools')
    jobs = []
    for folder in mb.STAGE_FOLDERS:
        sid_stage_id = '%s_%s' % (folder, SID)
        glb = os.path.join(STRUCTURES, SID, 'stages', folder, sid_stage_id + '.glb')
        if os.path.exists(glb):
            jobs.append((glb, os.path.join(STRUCTURES, SID, 'stages', folder, sid_stage_id + '.png')))
    final = os.path.join(STRUCTURES, SID, 'stages', 'struct_finishings', 'struct_finishings_%s.glb' % SID)
    if os.path.exists(final):
        jobs.append((final, os.path.join(STRUCTURES, SID, SID + '.png')))
    for glb, png in jobs:
        r = subprocess.run([sys.executable, os.path.join(tools, 'render_icon_from_model.py'), glb, png], capture_output=True, text=True)
        print(('icon ' if r.returncode == 0 else 'FAILED ') + os.path.basename(png))


if __name__ == '__main__':
    if '--icons' in sys.argv:
        make_icons()
    else:
        build_all()
