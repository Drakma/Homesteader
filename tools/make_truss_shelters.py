"""
Builds the OPEN-AIR STEEL TRUSS SHELTERS (assets/structures/steel_truss_shelter_2 / _3 / _5) in headless Blender: free, local, low-poly. A roof on steel columns and trusses over a
concrete slab, open on every side, with one vehicle bay between each pair of column lines: 2, 3 and 5 vehicles. Same four construction stages and conventions as the other
structures (docs/STRUCTURE_STAGES_GUIDE.md: metres, pivot at the footprint centre, front = -Y, FrontMarker, a Foundation part, a Roof part):

    1 foundation   the concrete slab with the column footings and parking lines
    2 framing      steel columns, eave and ridge beams, the roof trusses and knee braces
    3 purlins      the purlins across the trusses (the roof deck stage)
    4 roofing      corrugated steel panels with seams, ridge cap, eave trim

    blender --background --python tools/make_truss_shelters.py
    then: blender --background --python tools/fix_structure_overlaps.py -- steel_truss_shelter_2 steel_truss_shelter_3 steel_truss_shelter_5
          (icons)  generate_unity_asset_catalog.py ; package_catalog_as_mods.py
"""
import copy
import json
import math
import os
import sys

import bmesh
import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_building_stages as mb  # noqa: E402
import make_house_stages as hs  # noqa: E402
import make_structure_stages as base  # noqa: E402

ROOT = base.ROOT
STRUCTURES = base.STRUCTURES
Builder = base.Builder
colour = hs.colour

BAY = 3.8                        # one vehicle bay between two column lines
SPAN = 7.6                       # the clear span of a truss, front column line to back column line
Z_SLAB = 0.2                     # the top of the slab
Z_EAVE = 3.7                     # the column tops (a truck and a trailer pass under)
Z_RIDGE = 5.0
OVER = 0.5                       # the roof and the slab reach this far past the columns, every side

SHELTERS = {
    'steel_truss_shelter_2': dict(name='Steel Truss Shelter (2 Vehicles)', bays=2, price=4200,
                                  desc='An open-air steel truss shelter: a roof on steel columns over a concrete slab, room for two vehicles.'),
    'steel_truss_shelter_3': dict(name='Steel Truss Shelter (3 Vehicles)', bays=3, price=5800,
                                  desc='An open-air steel truss shelter: a roof on steel columns over a concrete slab, room for three vehicles.'),
    'steel_truss_shelter_5': dict(name='Steel Truss Shelter (5 Vehicles)', bays=5, price=9000,
                                  desc='An open-air steel truss shelter: a roof on steel columns over a concrete slab, room for five vehicles.'),
}
STAGES = [('struct_foundation', 'foundation'), ('struct_framing', 'framing'), ('struct_walls', 'purlins'), ('struct_complete', 'roofing')]


def dims(bays):
    return bays * BAY + 2 * OVER, SPAN + 2 * OVER                    # width (x), depth (y) of the footprint


def palette():
    cfg = dict(style='metal', palette=dict(siding=(0.72, 0.74, 0.76), trim=(0.9, 0.9, 0.88), shingle=(0.32, 0.38, 0.34), shingle_dark=(0.22, 0.27, 0.24)))
    M = mb.palette(cfg)
    M['frame'] = colour('SteelFrame', (0.2, 0.22, 0.25), 0.45)
    M['frame_light'] = colour('SteelBrace', (0.33, 0.35, 0.38), 0.5)
    M['line'] = colour('ParkingLine', (0.93, 0.9, 0.7), 0.8)
    return M


def member(b, a, c, m, r=0.045):
    b.log(a, c, r, m, sides=4)


def slope_panel(b, x0, x1, ylo, zlo, yhi, zhi, t, m):
    """A sloped slab from the lower edge (ylo, zlo) to the upper edge (yhi, zhi), thickness t along its normal (up and out)."""
    dy, dz = yhi - ylo, zhi - zlo
    ln = math.hypot(dy, dz)
    ny, nz = -dz / ln, dy / ln                                        # the normal of the lower-to-upper edge turned a quarter turn
    if nz < 0:
        ny, nz = -ny, -nz
    i = b.mat_index(m)
    pts = []
    for (y, z) in ((ylo, zlo), (yhi, zhi)):
        for x in (x0, x1):
            pts.append(b.bm.verts.new((x, y, z)))
            pts.append(b.bm.verts.new((x, y + ny * t, z + nz * t)))
    # pts: [lo x0 under, lo x0 top, lo x1 under, lo x1 top, hi x0 under, hi x0 top, hi x1 under, hi x1 top]
    q = lambda *ix: [pts[k] for k in ix]  # noqa: E731
    faces = (q(0, 2, 6, 4), q(1, 5, 7, 3), q(0, 4, 5, 1), q(2, 3, 7, 6), q(0, 1, 3, 2), q(4, 6, 7, 5))
    for f in faces:
        face = b.bm.faces.new(f)
        face.material_index = i


def truss(b, x, M):
    ys = (-SPAN / 2, -SPAN / 4, 0.0, SPAN / 4, SPAN / 2)
    zr, ze = Z_RIDGE - 0.1, Z_EAVE
    zm = ze + (zr - ze) / 2
    top = [(x, ys[0], ze), (x, ys[1], zm), (x, ys[2], zr), (x, ys[3], zm), (x, ys[4], ze)]
    bot = [(x, y, ze - 0.15) for y in ys]
    for k in range(4):
        member(b, top[k], top[k + 1], M['frame'], 0.05)             # the top chord
        member(b, bot[k], bot[k + 1], M['frame'], 0.045)            # the bottom chord
    for k in (1, 2, 3):
        member(b, bot[k], top[k], M['frame_light'], 0.032)          # the verticals
    member(b, top[1], bot[2], M['frame_light'], 0.03)               # the V of diagonals
    member(b, top[3], bot[2], M['frame_light'], 0.03)
    member(b, top[0], bot[0], M['frame'], 0.05)
    member(b, top[4], bot[4], M['frame'], 0.05)


def foundation_stage(b, FB, n, M):
    wd, dd = dims(n)
    FB.box(-wd / 2, wd / 2, -dd / 2, dd / 2, 0.0, Z_SLAB, M['concrete'])
    FB.box(-wd / 2 - 0.05, wd / 2 + 0.05, -dd / 2 - 0.05, dd / 2 + 0.05, 0.0, 0.06, M['concrete_dark'])
    for i in range(n + 1):
        x = -n * BAY / 2 + i * BAY
        for sy in (-1, 1):
            FB.box(x - 0.35, x + 0.35, sy * SPAN / 2 - 0.35, sy * SPAN / 2 + 0.35, Z_SLAB, Z_SLAB + 0.03, M['concrete_dark'])      # the footing pads (a little proud)
            for dx in (-0.14, 0.14):
                for dy in (-0.14, 0.14):
                    b.box(x + dx - 0.012, x + dx + 0.012, sy * SPAN / 2 + dy - 0.012, sy * SPAN / 2 + dy + 0.012, Z_SLAB + 0.03, Z_SLAB + 0.1, M['steel'])    # anchor bolts
    for i in range(n + 1):                                                                                         # parking lines between the bays
        x = -n * BAY / 2 + i * BAY
        b.box(x - 0.04, x + 0.04, -SPAN / 2 + 0.6, SPAN / 2 - 0.6, Z_SLAB, Z_SLAB + 0.004, M['line'])


def framing_stage(b, n, M):
    x0, x1 = -n * BAY / 2, n * BAY / 2
    for i in range(n + 1):
        x = x0 + i * BAY
        for sy in (-1, 1):
            y = sy * SPAN / 2
            b.box(x - 0.1, x + 0.1, y - 0.1, y + 0.1, Z_SLAB + 0.03, Z_EAVE, M['frame'])                          # the column
            b.box(x - 0.2, x + 0.2, y - 0.2, y + 0.2, Z_SLAB + 0.03, Z_SLAB + 0.05, M['frame_light'])           # its base plate
            member(b, (x, y, Z_EAVE - 1.0), (x, y - sy * 1.0, Z_EAVE - 0.15), M['frame_light'], 0.03)           # the knee brace
        truss(b, x, M)
    for sy in (-1, 1):
        y = sy * SPAN / 2
        b.box(x0 - 0.1, x1 + 0.1, y - 0.07, y + 0.07, Z_EAVE, Z_EAVE + 0.2, M['frame'])                          # the eave beams
    b.box(x0 - 0.1, x1 + 0.1, -0.06, 0.06, Z_RIDGE - 0.1, Z_RIDGE + 0.04, M['frame'])                          # the ridge beam
    for k in range(n):                                                                                           # X-bracing in the end bays' roof planes
        if k in (0, n - 1):
            xa, xb = x0 + k * BAY, x0 + (k + 1) * BAY
            for sy in (-1, 1):
                member(b, (xa, sy * SPAN / 2, Z_EAVE + 0.05), (xb, sy * 0.1, Z_RIDGE - 0.05), M['frame_light'], 0.015)


def purlin_stage(b, n, M):
    x0, x1 = -n * BAY / 2 - OVER, n * BAY / 2 + OVER
    ze, zr = Z_EAVE, Z_RIDGE - 0.1
    for sy in (-1, 1):
        for yy in (0.9, 1.8, 2.7, 3.4, SPAN / 2):
            z = ze + (zr - ze) * (1 - yy / (SPAN / 2)) + 0.05
            b.box(x0, x1, sy * yy - 0.05, sy * yy + 0.05, z, z + 0.08, M['frame_light'])


def roof_stage(roof, n, M):
    x0, x1 = -n * BAY / 2 - OVER, n * BAY / 2 + OVER
    ze, zr = Z_EAVE, Z_RIDGE - 0.1
    top0 = zr + 0.13                                                   # the top of the purlins at the ridge
    rise = (zr - ze) / (SPAN / 2)
    ye = SPAN / 2 + OVER
    for sy in (-1, 1):
        slope_panel(roof, x0, x1, sy * ye, ze + 0.13 - rise * OVER, sy * 0.0, top0, 0.04, M['shingle'])
        k = int((x1 - x0) / 0.9)
        for j in range(k + 1):                                         # the seams of the standing-seam panels
            xs = x0 + 0.1 + j * (x1 - x0 - 0.2) / k
            slope_panel(roof, xs - 0.015, xs + 0.015, sy * ye, ze + 0.13 - rise * OVER + 0.04, sy * 0.0, top0 + 0.04, 0.025, M['shingle_dark'])
        roof.box(x0, x1, sy * ye - 0.03, sy * ye + 0.03, ze - rise * OVER + 0.02, ze - rise * OVER + 0.2, M['trim'])      # the eave trim
    roof.box(x0, x1, -0.14, 0.14, top0 + 0.02, top0 + 0.12, M['shingle_dark'])                                        # the ridge cap
    for sx in (-1, 1):                                                                                                  # the gable-end rakes
        xe = x1 if sx > 0 else x0
        roof.box(xe - 0.03, xe + 0.03, -ye, ye, top0 - 0.2, top0 - 0.18, M['trim'])


# ------------------------------------------------------------------ manifests

def L(spec, q):
    return {'item_id': spec, 'quantity': q}


def S(title, mode, items):
    return {'section': title, 'mode': mode, 'items': items}


def recipes(n):
    wd, dd = dims(n)
    area = wd * dd
    k = area / 120.0
    t = n + 1                                                         # truss and column lines
    foundation = [
        L('~gravel', round(0.5 * k, 2)), L('~rebar', max(6, round(12 * k))), L('~anchor_bolts', 4 * 2 * t),
        S('Concrete slab', 'any', [
            S('Bagged concrete mix', 'all', [L('~concrete_mix', round(100 * k)), L('~water', round(90 * k))]),
            S('Mix your own: 1 cement, 2 sand, 3 aggregate', 'all', [L('~cement', round(18 * k)), L('~sand', round(0.22 * k, 2)), L('~gravel', round(0.32 * k, 2)), L('~water', round(80 * k))]),
        ])]
    framing = [L('~steel_frame_beam', 6 * t + 6), L('~truss_large', t), L('~lag_bolts', 8 * t), L('~anchor_bolts', 8 * t), L('~deck_screws', 40 * t)]
    purlins = [L('~steel_frame_beam', 2 * (n + 2)), L('~deck_screws', 120 * n), L('~metal', n)]
    roofing = [L('~roofing', round(60 * k)), L('building_roofing_nails_box', n + 1), L('building_flashing_roll', 2 + n), L('~metal', 2 + n),
               L('~fascia', round(24 * k)), L('~gutters', round(8 * n)), L('~downspout', 2 + n)]
    tools = {'foundation': [['tool_shovel', 'tool_pickaxe'], ['tool_trowel_hand'], ['tool_wheelbarrow', 'tool_steel_wheelbarrow', 'tool_cement_mixer']],
             'framing': [['tool_wrench_adjustable', 'tool_wrench_pipe'], ['tool_drill_corded', 'tool_drill_cordless_pro', 'tool_impact_driver_cordless'], ['tool_angle_grinder_corded', 'tool_angle_grinder_cordless']],
             'purlins': [['tool_drill_corded', 'tool_drill_cordless_pro', 'tool_impact_driver_cordless'], ['tool_angle_grinder_corded', 'tool_angle_grinder_cordless']],
             'roofing': [['tool_drill_corded', 'tool_drill_cordless_pro', 'tool_impact_driver_cordless'], ['tool_hammer_claw', 'tool_hammer']]}
    return {'foundation': foundation, 'framing': framing, 'purlins': purlins, 'roofing': roofing}, tools


def manifests(sid, cfg):
    n = cfg['bays']
    wd, dd = dims(n)
    src = os.path.join(STRUCTURES, 'large_metal_garage')
    dst = os.path.join(STRUCTURES, sid)
    rec, tools = recipes(n)
    g = json.load(open(os.path.join(src, 'large_metal_garage.json'), encoding='utf-8'))
    g['id'], g['name'], g['icon'], g['description'] = sid, cfg['name'], sid + '.png', cfg['desc']
    g['growth']['species'] = sid
    g['properties']['base_value'] = cfg['price']
    for (folder, sname), st in zip(STAGES, g['growth']['stages']):
        st['name'] = sname
        st['model'] = ''
        st['icon'] = '%s_%s.png' % (folder, sid)
        st['construction_recipe'] = rec[sname]
        st['required_tools'] = tools[sname]
    os.makedirs(dst, exist_ok=True)
    json.dump(g, open(os.path.join(dst, sid + '.json'), 'w', encoding='utf-8'), indent=2)
    for (folder, sname) in STAGES:
        m = json.load(open(os.path.join(src, 'stages', folder, '%s_large_metal_garage.json' % folder), encoding='utf-8'))
        m['id'] = '%s_%s' % (folder, sid)
        m['name'] = '%s - %s' % (cfg['name'], sname.capitalize())
        m['description'] = 'The %s phase of the %s.' % (sname, cfg['name'].lower())
        m['icon'] = m['id'] + '.png'
        cf = m['category_fields']
        cf['dimensions_m'] = {'width': round(wd, 2), 'depth': round(dd, 2), 'height': Z_SLAB if folder == 'struct_foundation' else Z_RIDGE + 0.15}
        cf['construction_recipe'] = rec[sname]
        cf['required_tools'] = tools[sname]
        cf['room_count'] = 0
        m['properties']['weight_kg'] = round(wd * dd * 120.0, 1)
        m['properties']['base_value'] = round(cfg['price'] * 0.25)
        m['models'] = []
        d = os.path.join(dst, 'stages', folder)
        os.makedirs(d, exist_ok=True)
        json.dump(m, open(os.path.join(d, m['id'] + '.json'), 'w', encoding='utf-8'), indent=2)
        open(os.path.join(d, 'README.md'), 'w', encoding='utf-8').write('# %s\n\nStage of the %s (generated by tools/make_truss_shelters.py).\n' % (m['name'], cfg['name']))


def build(sid):
    cfg = SHELTERS[sid]
    n = cfg['bays']
    wd, dd = dims(n)
    manifests(sid, cfg)
    M = palette()
    for folder, sname in STAGES:
        stage_id = '%s_%s' % (folder, sid)
        sfolder = os.path.join(STRUCTURES, sid, 'stages', folder)
        mpath = os.path.join(sfolder, stage_id + '.json')
        d = json.load(open(mpath, encoding='utf-8'))
        for o in list(bpy.data.objects):
            bpy.data.objects.remove(o, do_unlink=True)
        b = Builder(stage_id)
        FB = Builder('Foundation')
        roof = Builder('Roof')
        foundation_stage(b, FB, n, M)
        if folder != 'struct_foundation':
            framing_stage(b, n, M)
        if folder in ('struct_walls', 'struct_complete'):
            purlin_stage(b, n, M)
        if folder == 'struct_complete':
            roof_stage(roof, n, M)
        extras = [FB.finish()]
        if roof.bm.verts:
            extras.append(roof.finish())
        else:
            roof.bm.free()
        obj = b.finish()
        marker = bpy.data.objects.new('FrontMarker', None)
        marker.location = (0.0, -dd / 2 - 0.8, 0.05)
        bpy.context.collection.objects.link(marker)
        bpy.ops.object.select_all(action='DESELECT')
        for o in [obj, marker] + extras:
            o.select_set(True)
        bpy.context.view_layer.objects.active = obj
        out = os.path.join(sfolder, stage_id + '.glb')
        bpy.ops.export_scene.gltf(filepath=out, export_format='GLB', use_selection=True, export_yup=True)
        tris = sum(len(p.vertices) - 2 for p in obj.data.polygons) + sum(sum(len(p.vertices) - 2 for p in e.data.polygons) for e in extras)
        d['models'] = [{'file': stage_id + '.glb', 'format': 'glb', 'dimensions_m': {'x': round(wd, 2), 'y': d['category_fields']['dimensions_m']['height'], 'z': round(dd, 2)}, 'triangles': tris}]
        json.dump(d, open(mpath, 'w', encoding='utf-8'), indent=2)
        print('stage', stage_id, tris, 'tris ->', out)


if __name__ == '__main__':
    argv = sys.argv
    names = argv[argv.index('--') + 1:] if '--' in argv else list(SHELTERS)
    for sid in names:
        build(sid)
