"""
The fixtures that bring a well's water into a building and let it out (docs/WELLS.md, "Into the building"):

  water_inlet_house     the building's water inlet: a white PVC riser out of the ground to a ball valve with a blue lever and an elbow into the wall,
                        on a wall bracket. Mounted on the OUTSIDE of a building and piped (pipe wrench, PVC pipe) to a tank, a filter or a well, it gives
                        the building water.
  water_spigot_outdoor  an outdoor spigot (a hose bib): a brass tap on a wall plate. Mounted on the outside of a building with water, a right click with a
                        bucket, jug or watering can in hand fills it (raw or clean: it is for the garden and the animals).
  water_faucet_indoor   an indoor utility faucet: a chrome spout and two handles on a wall plate. Mounted inside, it fills a container with CLEAN water only.

    blender --background --python tools/make_water_fixtures.py
    python tools/set_wiring_data.py ; python tools/render_icon_from_model.py <glb> <png>   (done by this script for the icons)

Convention for a wall item (docs/ATTACHED_ITEMS.md): the back against the wall at y = 0, the front facing -y, the bottom at z = 0, centred on x.
"""
import json
import math
import os
import subprocess
import sys

import bpy
from mathutils import Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_simple_props as props  # noqa: E402    (Kit, mat, save)

ASSETS = os.path.join(props.ROOT, 'assets')
T = Matrix.Translation
mat = props.mat
INLET, SPIGOT, FAUCET = 'water_inlet_house', 'water_spigot_outdoor', 'water_faucet_indoor'


def inlet():
    """Three parts, like the wall entry for wire (Assets/Scripts/Growth/AttachedObject.cs ApplyThrough): "Plate" (the wall plate with a pipe stub and a ball valve,
    copied by the game onto the far side of the wall so the inside has one too), "Pipe" (the sleeve through the wall, 0.25 m long towards +y, stretched to the
    wall's thickness) and "Riser" (the line up out of the ground into the plate: the outside only)."""
    pvc = mat('PVC', (0.93, 0.93, 0.9), 0.5)
    dark = mat('Bracket', (0.12, 0.12, 0.13), 0.55)
    brass = mat('ValveBrass', (0.8, 0.62, 0.25), 0.35)
    blue = mat('ValveLever', (0.1, 0.3, 0.8), 0.5)
    r = 0.017
    cz = 0.36                                                               # where the pipe goes through the wall
    P = props.Kit()
    P.bx((0.16, 0.008, 0.16), (0, -0.004, cz), dark)                        # the wall plate
    P.tube((0, -0.008, cz), (0, -0.07, cz), r, r, pvc, 10)                  # the stub out of the wall
    P.lathe([(r * 1.3, -0.03), (r * 1.8, -0.022), (r * 1.8, 0.022), (r * 1.3, 0.03)], brass, 10, T((0, -0.06, cz)) @ Matrix.Rotation(math.pi / 2, 4, 'X'))   # the ball valve
    P.bx((0.11, 0.008, 0.022), (0.04, -0.06 - r * 1.8 - 0.006, cz), blue)   # its lever (open: in line)
    P.tube((0, -0.07, cz), (0, -0.085, cz), r * 1.05, r * 1.05, pvc, 10, None, pvc)
    plate = P.done('Plate')
    S = props.Kit()
    S.tube((0, 0.0, cz), (0, 0.25, cz), r * 1.25, r * 1.25, pvc, 10, pvc, pvc)   # the sleeve through the wall
    pipe = S.done('Pipe')
    R = props.Kit()
    y = -0.07
    R.tube((0, y, 0.0), (0, y, cz - 0.06), r, r, pvc, 10, pvc)               # up out of the ground
    R.path([(0, y, cz - 0.06), (0, y, cz - 0.02), (0, y - 0.012, cz), (0, -0.085, cz)], r, pvc, 10)   # and the elbow into the valve's end
    R.bx((0.05, 0.06, 0.012), (0, -0.035, cz * 0.4), dark)                   # a clamp to the wall
    riser = R.done('Riser')
    return [plate, pipe, riser]


def spigot():
    K = props.Kit()
    plate = mat('Plate', (0.85, 0.84, 0.8), 0.6)
    brass = mat('Brass', (0.8, 0.62, 0.25), 0.3)
    red = mat('Handle', (0.7, 0.12, 0.08), 0.5)
    K.bx((0.12, 0.012, 0.12), (0, -0.006, 0.06), plate)
    K.tube((0, -0.012, 0.06), (0, -0.07, 0.06), 0.013, 0.013, brass, 10)                    # the body out of the wall
    K.path([(0, -0.07, 0.06), (0, -0.09, 0.055), (0, -0.095, 0.03)], 0.011, brass, 8)       # the spout, down
    K.lathe([(0.012, 0.0), (0.012, 0.012), (0.0, 0.014)], brass, 8, T((0, -0.095, 0.03)) @ Matrix.Rotation(math.pi, 4, 'X'))
    K.tube((0, -0.06, 0.075), (0, -0.06, 0.1), 0.006, 0.006, brass, 6)                       # the stem
    K.lathe([(0.0, 0.0), (0.028, 0.0), (0.028, 0.008), (0.0, 0.01)], red, 12, T((0, -0.06, 0.1)))   # the round handle
    return K.done(SPIGOT)


def faucet():
    K = props.Kit()
    plate = mat('Plate', (0.92, 0.92, 0.9), 0.4)
    chrome = mat('Chrome', (0.82, 0.83, 0.85), 0.15)
    blue = mat('Cold', (0.12, 0.3, 0.8), 0.4)
    red = mat('Hot', (0.75, 0.12, 0.08), 0.4)
    K.bx((0.26, 0.012, 0.1), (0, -0.006, 0.05), plate)
    for sx, m in ((-0.08, blue), (0.08, red)):
        K.tube((sx, -0.012, 0.05), (sx, -0.05, 0.05), 0.012, 0.012, chrome, 8)
        K.bx((0.05, 0.016, 0.014), (sx, -0.055, 0.06), m)                                    # lever handles
    K.tube((-0.08, -0.04, 0.05), (0.08, -0.04, 0.05), 0.012, 0.012, chrome, 8)
    K.path([(0, -0.04, 0.05), (0, -0.06, 0.09), (0, -0.13, 0.1), (0, -0.16, 0.06)], 0.01, chrome, 8)   # the gooseneck
    return K.done(FAUCET)


def export(obj, folder, item):
    objs = obj if isinstance(obj, list) else [obj]
    pts = [o.matrix_world @ v.co for o in objs for v in o.data.vertices]
    dims = [round(max(p[i] for p in pts) - min(p[i] for p in pts), 3) for i in range(3)]
    tris = sum(len(p.vertices) - 2 for o in objs for p in o.data.polygons)
    os.makedirs(folder, exist_ok=True)
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    obj = objs[0]
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.gltf(filepath=os.path.join(folder, item + '.glb'), export_format='GLB', use_selection=True, export_yup=True)
    return dims, tris


def manifest(item, name, desc, side, role, price, kg):
    src = os.path.join(ASSETS, 'water', 'water_pressuretank_well', 'water_pressuretank_well.json')
    m = json.load(open(src, encoding='utf-8'))
    m.update({'id': item, 'icon': item + '.png', 'name': name, 'description': desc, 'category': 'water'})
    for k in ('liquid_container',):
        m.pop(k, None)
    pr = m['properties']
    pr.update({'weight_kg': kg, 'base_value': price, 'max_stack_size': 5, 'placeable': False, 'attach_surface': 'wall', 'attach_side': side,
               'wire_role': role, 'stores': ['depot'], 'is_buyable': True})
    cf = m.setdefault('category_fields', {})
    cf['capacity_l'] = 0
    cf['power_draw_w'] = 0
    return m


def build(item, fn, name, desc, side, role, price, kg):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    obj = fn()
    folder = os.path.join(ASSETS, 'water', item)
    dims, tris = export(obj, folder, item)
    path = os.path.join(folder, item + '.json')
    m = json.load(open(path, encoding='utf-8')) if os.path.exists(path) else manifest(item, name, desc, side, role, price, kg)
    if item == INLET:
        m['properties']['attach_through'] = True   # through the wall, like the wire entry: the plate shows on both sides
        m['description'] = desc
    m['properties']['footprint'] = '%.2fm W x %.2fm D x %.2fm H' % (dims[0], dims[1], dims[2])
    m['models'] = [{'file': item + '.glb', 'format': 'glb', 'dimensions_m': {'x': dims[0], 'y': dims[2], 'z': dims[1]}, 'triangles': tris}]
    m['category_fields'] = dict(m.get('category_fields') or {}, dimensions_m={'width': round(dims[0], 2), 'depth': round(dims[1], 2), 'height': round(dims[2], 2)})
    props.save(path, json.dumps(m, indent=2))
    props.save(os.path.join(folder, 'README.md'), '# %s\n\n%s\n\nProcedural model (tools/make_water_fixtures.py), %d triangles. Mounts on a wall (%s side); '
               '`wire_role: %s`. See docs/WELLS.md.\n' % (m['name'], m['description'], tris, side, role))
    print(item, tris, 'tris', dims)


def main():
    build(INLET, inlet, 'Building Water Inlet',
          'Brings water into a building: a ball valve with a blue lever on a PVC riser, on a wall bracket. Mount it on the OUTSIDE of a building (left click a wall '
          'with it in hand): it goes THROUGH the wall, with a valve on the inside too. Then pipe it to a tank, a filter or a well with PVC pipe and a pipe '
          'wrench. The building then has water at its spigots and faucets.',
          'exterior', 'water_inlet', 38, 1.2)
    build(SPIGOT, spigot, 'Outdoor Spigot',
          'A brass hose bib on a wall plate. Mount it on the outside of a building that has water; a right click with a bucket, jug or watering can in hand fills '
          'it. It gives whatever water the building is supplied with, raw or filtered.', 'exterior', 'water_spigot', 18, 0.4)
    build(FAUCET, faucet, 'Utility Faucet',
          'A chrome utility faucet with hot and cold levers. Mount it inside a building that has water; a right click with a bucket, jug or watering can in hand '
          'fills it with whatever water the building is supplied with: raw unless it comes through the sediment, carbon and UV filters.', 'interior', 'water_spigot', 45, 0.9)


if __name__ == '__main__':
    main()
