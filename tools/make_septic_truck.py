"""
Builds the septic pump truck (the "honey pot" truck, assets/vehicles/vehicle_septic_pump_truck) in headless Blender: free, local, low-poly (no Meshy).

    blender --background --python tools/make_septic_truck.py
    python tools/render_icon_from_model.py assets/vehicles/vehicle_septic_pump_truck/vehicle_septic_pump_truck.glb \
        assets/vehicles/vehicle_septic_pump_truck/vehicle_septic_pump_truck.png

The fuel truck's chassis, cab, lights and wheels (tools/make_fuel_truck.py: the four SEPARATE wheels Wheel_FL / FR / RL / RR with their origin on the hub, and the
FrontMarker empty at the nose, so the game drives it the same way) with a dark steel vacuum tank: a green band round it, the vacuum pump and its oil catch
on the front of the tank, a rack of big black suction hose along the left side, a rear dump valve and a manway on top. It pumps out septic tanks
(Assets/Scripts/World/SepticPumpOut.cs, ordered as a Septic Pump-Out in the Tank You app).

Conventions: 1 unit = 1 m, ground at z = 0, the nose towards +y.
"""
import json
import math
import os
import sys

import bpy
from mathutils import Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_fuel_truck as ft  # noqa: E402    (mat, wheel, tank and the dimensions)
import make_simple_props as props  # noqa: E402

ITEM = 'vehicle_septic_pump_truck'
FOLDER = os.path.join(ft.VEHICLES, ITEM)
T = Matrix.Translation


def build():
    white = ft.mat('CabWhite', (0.93, 0.94, 0.95), 0.4)
    cream = ft.mat('Cab', (0.92, 0.93, 0.94), 0.45)
    dark = ft.mat('Chassis', (0.16, 0.17, 0.19), 0.7, 0.3)
    glass = ft.mat('Glass', (0.1, 0.16, 0.22), 0.1)
    tankm = ft.mat('VacuumTank', (0.28, 0.3, 0.32), 0.45, 0.5)
    band = ft.mat('Band', (0.15, 0.45, 0.2), 0.5)
    tire = ft.mat('Tire', (0.06, 0.06, 0.07), 0.9)
    rim = ft.mat('Rim', (0.7, 0.72, 0.75), 0.4, 0.8)
    red = ft.mat('Tail', (0.8, 0.08, 0.06), 0.4, 0.0, (0.8, 0.05, 0.03))
    yellow = ft.mat('Head', (1.0, 0.92, 0.6), 0.3, 0.0, (1.0, 0.9, 0.5))
    steel = ft.mat('Steel', (0.66, 0.67, 0.69), 0.35, 0.5)
    hose = ft.mat('Hose', (0.05, 0.05, 0.055), 0.8)
    pump = ft.mat('PumpRed', (0.65, 0.12, 0.08), 0.5)
    K = props.Kit()
    hw = ft.WIDTH / 2
    B = lambda x0, x1, y0, y1, z0, z1, m: K.bx((x1 - x0, y1 - y0, z1 - z0), ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), m)
    along_x = Matrix(((0, 0, 1, 0), (1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 0, 1)))
    # the chassis, cab, glass, bumpers, lights and mirrors (as the fuel truck)
    B(-hw + 0.12, hw - 0.12, -3.0, 3.05, 0.45, 0.85, dark)
    K.prism([(1.2, 0.8), (3.05, 0.8), (3.05, 1.45), (2.55, 2.25), (1.2, 2.25)], ft.WIDTH - 0.08, T((-hw + 0.04, 0, 0)) @ along_x, cream)
    B(-hw + 0.02, -hw + 0.07, 1.55, 2.45, 1.35, 2.05, glass)
    B(hw - 0.07, hw - 0.02, 1.55, 2.45, 1.35, 2.05, glass)
    K.prism([(2.58, 1.5), (2.97, 1.5), (2.57, 2.17), (2.48, 2.17)], ft.WIDTH - 0.36, T((-hw + 0.18, 0, 0)) @ along_x, glass)
    B(-hw + 0.05, hw - 0.05, 3.0, 3.2, 0.5, 0.95, dark)
    B(-hw + 0.05, hw - 0.05, -3.25, -3.05, 0.5, 0.95, dark)
    B(-hw + 0.2, -hw + 0.55, 3.04, 3.12, 1.0, 1.25, yellow)
    B(hw - 0.55, hw - 0.2, 3.04, 3.12, 1.0, 1.25, yellow)
    B(-hw + 0.1, -hw + 0.3, -3.27, -3.24, 0.6, 0.9, red)
    B(hw - 0.3, hw - 0.1, -3.27, -3.24, 0.6, 0.9, red)
    B(-hw - 0.18, -hw + 0.02, 2.5, 2.62, 1.55, 1.95, dark)
    B(hw - 0.02, hw + 0.18, 2.5, 2.62, 1.55, 1.95, dark)
    # the vacuum tank on its saddles, a green band, a manway on top
    ft.tank(K, tankm, band)
    for y in (ft.TANK_Y0 + 0.5, (ft.TANK_Y0 + ft.TANK_Y1) / 2, ft.TANK_Y1 - 0.5):
        B(-ft.TANK_RX * 0.72, ft.TANK_RX * 0.72, y - 0.08, y + 0.08, 0.85, ft.TANK_ZC - ft.TANK_RZ * 0.6, dark)
    top = ft.TANK_ZC + ft.TANK_RZ
    K.lathe([(0.26, top - 0.04), (0.26, top + 0.08), (0.22, top + 0.12), (0.0, top + 0.13)], steel, 14, T((0, ft.TANK_Y0 + 1.2, 0)))
    # the vacuum pump and its oil catch on the front of the tank, between it and the cab
    B(-0.55, 0.15, 1.02, 1.18, 0.88, 1.5, pump)
    K.tube((0.35, 1.1, 0.9), (0.35, 1.1, 1.55), 0.13, 0.13, steel, 12, steel, steel)
    K.path([(-0.2, 1.1, 1.5), (-0.2, 1.1, 1.9), (-0.2, 0.9, 2.05)], 0.05, steel, 8)
    # the suction hose: lengths racked along the left side, the end over the rear
    for k in range(3):
        z = 0.95 + k * 0.13
        K.tube((-hw - 0.08, ft.TANK_Y0 + 0.3, z), (-hw - 0.08, ft.TANK_Y1 - 0.3, z), 0.06, 0.06, hose, 10, hose, hose)
    for y in (ft.TANK_Y0 + 0.5, ft.TANK_Y1 - 0.5):
        B(-hw - 0.18, -hw + 0.02, y - 0.03, y + 0.03, 0.85, 1.35, dark)
    # the rear dump valve and its handle, the rear lights
    K.tube((0, ft.TANK_Y0 + 0.05, ft.TANK_ZC - 0.5), (0, ft.TANK_Y0 - 0.35, ft.TANK_ZC - 0.5), 0.09, 0.09, steel, 12, steel, steel)
    B(-0.03, 0.03, ft.TANK_Y0 - 0.3, ft.TANK_Y0 - 0.24, ft.TANK_ZC - 0.5, ft.TANK_ZC - 0.2, pump)
    for sx in (-1, 1):
        x0, x1 = (sx * hw - 0.02, sx * (hw - 0.34)) if sx > 0 else (sx * (hw - 0.34), sx * hw + 0.02)
        B(min(x0, x1), max(x0, x1), ft.REAR_AXLE_Y - 0.55, ft.REAR_AXLE_Y + 0.55, 0.88, 0.93, dark)
        B(sx * 0.6 - 0.06, sx * 0.6 + 0.06, ft.TANK_Y0 - 0.02, ft.TANK_Y0 + 0.02, ft.TANK_ZC - 0.05, ft.TANK_ZC + 0.05, red)
    K.done('Body')
    for nm, x, y in (('Wheel_FL', -hw + 0.15, ft.FRONT_AXLE_Y), ('Wheel_FR', hw - 0.15, ft.FRONT_AXLE_Y), ('Wheel_RL', -hw + 0.15, ft.REAR_AXLE_Y), ('Wheel_RR', hw - 0.15, ft.REAR_AXLE_Y)):
        ft.wheel(nm, x, y, tire, rim)
    marker = bpy.data.objects.new('FrontMarker', None)
    marker.location = (0.0, 3.2, 1.0)
    bpy.context.collection.objects.link(marker)
    _ = white


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
        m = json.load(open(os.path.join(ft.VEHICLES, ft.ITEM, ft.ITEM + '.json'), encoding='utf-8'))
        m.update({'id': ITEM, 'icon': ITEM + '.png', 'name': 'Septic Pump Truck',
                  'description': 'The honey pot truck: a vacuum tank on a truck chassis, with its pump, racks of black suction hose and a dump valve at the back. It comes '
                                 'to pump out septic tanks (a Septic Pump-Out in the Tank You app).'})
        m['properties'].update({'weight_kg': 6800.0, 'base_value': 95000.0, 'is_buyable': False, 'stores': []})
        m['liquid_container'] = {'capacity_l': ft.TANK_L, 'accepts': ['liquid_sewage']}
    m['models'] = [{'file': ITEM + '.glb', 'format': 'glb', 'dimensions_m': {'x': ft.WIDTH, 'y': round(height, 2), 'z': 6.45}, 'triangles': tris}]
    m['category_fields'] = dict(m.get('category_fields') or {}, dimensions_m={'width': ft.WIDTH, 'depth': 6.45, 'height': round(height, 2)})
    props.save(path, json.dumps(m, indent=2))
    props.save(os.path.join(FOLDER, 'README.md'), '# %s (`%s`)\n\n%s\n\nProcedural model (tools/make_septic_truck.py), %d triangles. Built on the fuel truck: the four '
               'wheels are separate objects named `Wheel_FL`, `Wheel_FR`, `Wheel_RL`, `Wheel_RR` with their origin on the hub, and an empty named `FrontMarker` sits at '
               'the nose, so the game drives it the same way. See docs/SEPTIC.md.\n' % (m['name'], ITEM, m['description'], tris))
    print('truck', ITEM, '|', tris, 'tris | height', round(height, 2))


if __name__ == '__main__':
    main()
