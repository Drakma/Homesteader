"""
Builds the market cargo truck (assets/vehicles/vehicle_market_cargo_truck) in headless Blender: free, local, low-poly (no Meshy).

    blender --background --python tools/make_cargo_truck.py
    python tools/render_icon_from_model.py assets/vehicles/vehicle_market_cargo_truck/vehicle_market_cargo_truck.glb \
        assets/vehicles/vehicle_market_cargo_truck/vehicle_market_cargo_truck.png

The fuel truck's chassis, cab, lights and wheels (tools/make_fuel_truck.py: the four SEPARATE wheels Wheel_FL / FR / RL / RR with their origin on the hub,
and the FrontMarker empty at the nose, so the game drives it the same way) with an OPEN flatbed behind the cab: a plank deck, low stake sides with posts,
a headboard behind the cab and a drop tailgate, a pair of rope-tied crates and a bale on the bed for show, and a green stripe along the cab. It collects what
the player sells in the Market app (Assets/Scripts/World/MarketPickup.cs).

Conventions: 1 unit = 1 m, ground at z = 0, the nose towards +y.
"""
import json
import math
import os
import sys

import bpy
from mathutils import Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_fuel_truck as ft  # noqa: E402    (mat, wheel and the dimensions)
import make_simple_props as props  # noqa: E402

ITEM = 'vehicle_market_cargo_truck'
FOLDER = os.path.join(ft.VEHICLES, ITEM)
T = Matrix.Translation

BED_Y0, BED_Y1 = -3.05, 1.0            # the bed runs from behind the cab to the tail
BED_Z = 0.95                            # the deck's top
SIDE_H = 0.42                           # the stake sides


def build():
    cab = ft.mat('Cab', (0.2, 0.42, 0.28), 0.45)
    cream = ft.mat('CabTrim', (0.92, 0.93, 0.94), 0.45)
    dark = ft.mat('Chassis', (0.16, 0.17, 0.19), 0.7, 0.3)
    glass = ft.mat('Glass', (0.1, 0.16, 0.22), 0.1)
    plank = ft.mat('Planks', (0.62, 0.46, 0.28), 0.85)
    wood = ft.mat('Stakes', (0.45, 0.32, 0.2), 0.85)
    steel = ft.mat('Steel', (0.66, 0.67, 0.69), 0.35, 0.5)
    rope = ft.mat('Rope', (0.8, 0.72, 0.5), 0.9)
    crate = ft.mat('Crate', (0.7, 0.55, 0.33), 0.8)
    hay = ft.mat('Hay', (0.85, 0.72, 0.3), 0.9)
    tire = ft.mat('Tire', (0.06, 0.06, 0.07), 0.9)
    rim = ft.mat('Rim', (0.7, 0.72, 0.75), 0.4, 0.8)
    red = ft.mat('Tail', (0.8, 0.08, 0.06), 0.4, 0.0, (0.8, 0.05, 0.03))
    yellow = ft.mat('Head', (1.0, 0.92, 0.6), 0.3, 0.0, (1.0, 0.9, 0.5))
    K = props.Kit()
    hw = ft.WIDTH / 2
    B = lambda x0, x1, y0, y1, z0, z1, m: K.bx((x1 - x0, y1 - y0, z1 - z0), ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), m)
    along_x = Matrix(((0, 0, 1, 0), (1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 0, 1)))
    # the chassis, cab, glass, bumpers, lights and mirrors (as the fuel truck, the cab painted green)
    B(-hw + 0.12, hw - 0.12, -3.0, 3.05, 0.45, 0.85, dark)
    K.prism([(1.2, 0.8), (3.05, 0.8), (3.05, 1.45), (2.55, 2.25), (1.2, 2.25)], ft.WIDTH - 0.08, T((-hw + 0.04, 0, 0)) @ along_x, cab)
    B(-hw + 0.02, -hw + 0.07, 1.55, 2.45, 1.35, 2.05, glass)
    B(hw - 0.07, hw - 0.02, 1.55, 2.45, 1.35, 2.05, glass)
    K.prism([(2.58, 1.5), (2.97, 1.5), (2.57, 2.17), (2.48, 2.17)], ft.WIDTH - 0.36, T((-hw + 0.18, 0, 0)) @ along_x, glass)
    B(-hw + 0.04, hw - 0.04, 1.16, 3.04, 0.78, 0.84, cream)                                  # a pale stripe along the cab's lower edge
    B(-hw + 0.05, hw - 0.05, 3.0, 3.2, 0.5, 0.95, dark)
    B(-hw + 0.05, hw - 0.05, -3.25, -3.05, 0.5, 0.95, dark)
    B(-hw + 0.2, -hw + 0.55, 3.04, 3.12, 1.0, 1.25, yellow)
    B(hw - 0.55, hw - 0.2, 3.04, 3.12, 1.0, 1.25, yellow)
    B(-hw + 0.1, -hw + 0.3, -3.27, -3.24, 0.6, 0.9, red)
    B(hw - 0.3, hw - 0.1, -3.27, -3.24, 0.6, 0.9, red)
    B(-hw - 0.18, -hw + 0.02, 2.5, 2.62, 1.55, 1.95, dark)
    B(hw - 0.02, hw + 0.18, 2.5, 2.62, 1.55, 2.05 - 0.1, dark)
    # the open bed: a frame, the plank deck, the headboard behind the cab, stake sides and a drop tailgate
    B(-hw + 0.04, hw - 0.04, BED_Y0, BED_Y1, 0.85, BED_Z - 0.06, dark)
    n = 11
    for k in range(n):                                                                         # planks across the deck
        y0 = BED_Y0 + (BED_Y1 - BED_Y0) * k / n
        y1 = BED_Y0 + (BED_Y1 - BED_Y0) * (k + 1) / n - 0.012
        B(-hw + 0.05, hw - 0.05, y0, y1, BED_Z - 0.06, BED_Z, plank)
    B(-hw + 0.1, hw - 0.1, BED_Y1 - 0.06, BED_Y1 + 0.02, BED_Z, BED_Z + 1.0, dark)            # the headboard
    for sx in (-1, 1):
        x0, x1 = (sx * hw - 0.02, sx * (hw - 0.06)) if sx > 0 else (sx * (hw - 0.06), sx * hw + 0.02)
        for rail_z in (BED_Z + 0.18, BED_Z + SIDE_H - 0.06):
            B(min(x0, x1), max(x0, x1), BED_Y0 + 0.1, BED_Y1 - 0.08, rail_z, rail_z + 0.06, plank)   # two boards a side
        for k in range(6):                                                                     # the stake posts
            y = BED_Y0 + 0.08 + (BED_Y1 - BED_Y0 - 0.2) * k / 5
            B(min(x0, x1) - (0.0 if sx < 0 else 0.0), max(x0, x1), y - 0.04, y + 0.04, BED_Z - 0.04, BED_Z + SIDE_H, wood)
    B(-hw + 0.08, hw - 0.08, BED_Y0 - 0.06, BED_Y0 + 0.01, BED_Z + 0.02, BED_Z + SIDE_H - 0.02, plank)   # the tailgate, hinged up
    for sx in (-1, 1):
        B(sx * (hw - 0.14) - 0.02, sx * (hw - 0.14) + 0.02, BED_Y0 - 0.075, BED_Y0 - 0.055, BED_Z + 0.04, BED_Z + 0.14, steel)   # its latches
    # a load for show: two crates roped together and a bale, so it reads as a market truck
    B(-0.7, 0.0, -0.9, -0.1, BED_Z, BED_Z + 0.5, crate)
    B(-0.7, 0.0, -0.9, -0.1, BED_Z + 0.5, BED_Z + 0.58, plank)
    B(0.05, 0.75, -0.95, -0.2, BED_Z, BED_Z + 0.45, crate)
    K.bx((0.7, 0.04, 0.04), (-0.35, -0.5, BED_Z + 0.62), rope)
    B(-0.7, 0.7, 0.05, 0.75, BED_Z, BED_Z + 0.5, hay)
    # fenders over the rear wheels
    for sx in (-1, 1):
        x0, x1 = (sx * hw - 0.02, sx * (hw - 0.34)) if sx > 0 else (sx * (hw - 0.34), sx * hw + 0.02)
        B(min(x0, x1), max(x0, x1), ft.REAR_AXLE_Y - 0.55, ft.REAR_AXLE_Y + 0.55, 0.88, 0.93, dark)
    K.done('Body')
    for nm, x, y in (('Wheel_FL', -hw + 0.15, ft.FRONT_AXLE_Y), ('Wheel_FR', hw - 0.15, ft.FRONT_AXLE_Y), ('Wheel_RL', -hw + 0.15, ft.REAR_AXLE_Y), ('Wheel_RR', hw - 0.15, ft.REAR_AXLE_Y)):
        ft.wheel(nm, x, y, tire, rim)
    marker = bpy.data.objects.new('FrontMarker', None)
    marker.location = (0.0, 3.2, 1.0)
    bpy.context.collection.objects.link(marker)
    _ = (math, T)


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    build()
    os.makedirs(FOLDER, exist_ok=True)
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.export_scene.gltf(filepath=os.path.join(FOLDER, ITEM + '.glb'), export_format='GLB', use_selection=True, export_yup=True)
    tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in bpy.data.objects if o.type == 'MESH')
    height = max((o.matrix_world @ v.co).z for o in bpy.data.objects if o.type == 'MESH' for v in o.data.vertices)
    path = os.path.join(FOLDER, ITEM + '.json')
    if os.path.exists(path):
        m = json.load(open(path, encoding='utf-8'))
    else:
        m = json.load(open(os.path.join(ft.VEHICLES, ft.VAN, ft.VAN + '.json'), encoding='utf-8'))
        m.update({'id': ITEM, 'icon': ITEM + '.png', 'name': 'Market Cargo Truck',
                  'description': 'An open-bed stake truck. It comes the morning after you sell goods in the Market app, loads what you left in the pickup zone and pays '
                                 'you for it.'})
        m['properties'].update({'weight_kg': 4200.0, 'base_value': 58000.0, 'is_buyable': False, 'stores': []})
        m['category_fields'] = dict(m.get('category_fields') or {}, cargo_capacity_m3=14)
    m['models'] = [{'file': ITEM + '.glb', 'format': 'glb', 'dimensions_m': {'x': ft.WIDTH, 'y': round(height, 2), 'z': 6.45}, 'triangles': tris}]
    m['category_fields'] = dict(m.get('category_fields') or {}, dimensions_m={'width': ft.WIDTH, 'depth': 6.45, 'height': round(height, 2)})
    props.save(path, json.dumps(m, indent=2))
    props.save(os.path.join(FOLDER, 'README.md'), '# %s (`%s`)\n\n%s\n\nProcedural model (tools/make_cargo_truck.py), %d triangles. Built like the fuel truck: the four '
               'wheels are separate objects named `Wheel_FL`, `Wheel_FR`, `Wheel_RL`, `Wheel_RR` with their origin on the hub, and an empty named `FrontMarker` sits at '
               'the nose, so the game drives it the same way. See docs/MARKET.md.\n' % (m['name'], ITEM, m['description'], tris))
    print('truck', ITEM, '|', tris, 'tris | height', round(height, 2))


if __name__ == '__main__':
    main()
