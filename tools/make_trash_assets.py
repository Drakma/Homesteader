"""
Builds the TRASH set in headless Blender: free, local, low-poly (no Meshy). Docs: docs/TRASH.md.

    blender --background --python tools/make_trash_assets.py
    python tools/render_icon_from_model.py assets/<category>/<id>/<id>.glb assets/<category>/<id>/<id>.png        (the three items)
    python tools/generate_unity_asset_catalog.py ; python tools/package_catalog_as_mods.py

  waste_garbage_bag_full        a full black garbage bag, tied at the neck (not for sale: the game makes them)
  waste_trash_bin_wheeled       the big wheeled bin with a hinged lid, a handle and two wheels at the back; a container that holds FOUR full bags, pushed like a wheelbarrow
  vehicle_trash_truck           the weekly trash truck (the fuel truck's chassis, cab and wheels, a rear-loading refuse body); it empties the bins in the pickup zone

Conventions: 1 unit = 1 m, pivot at the centre of the footprint, ground at z = 0. The bin's handle and wheels are at +x (like a wheelbarrow's handles: WheelbarrowPush), the truck's nose is +y.
"""
import json
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_fuel_truck as ft  # noqa: E402
import make_simple_props as props  # noqa: E402

ROOT = props.ROOT
T = Matrix.Translation

BAG, BIN, TRUCK = 'waste_garbage_bag_full', 'waste_trash_bin_wheeled', 'vehicle_trash_truck'


def frustum(K, x0, x1, y0, y1, z0, z1, top_in, m):
    """A box that narrows towards the top by `top_in` on every side (a bin's body)."""
    b = [K.bm.verts.new(c) for c in ((x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0))]
    t = [K.bm.verts.new(c) for c in ((x0 - top_in, y0 - top_in, z1), (x1 + top_in, y0 - top_in, z1), (x1 + top_in, y1 + top_in, z1), (x0 - top_in, y1 + top_in, z1))]
    i = K.mi(m)
    K.bm.faces.new(b[::-1]).material_index = i
    K.bm.faces.new(t).material_index = i
    for k in range(4):
        j = (k + 1) % 4
        K.bm.faces.new((b[k], b[j], t[j], t[k])).material_index = i


# ------------------------------------------------------------------------------------------------------------------------------------- the bag

def bag():
    K = props.Kit()
    black = props.mat('GarbageBag', (0.05, 0.05, 0.06), 0.35)
    tie = props.mat('BagTie', (0.85, 0.85, 0.2), 0.6)
    # a bulging, slightly slumped bag: a profile (radius, height) turned round, gathered into a neck at the top
    profile = [(0.0, 0.0), (0.12, 0.0), (0.2, 0.05), (0.24, 0.16), (0.25, 0.27), (0.22, 0.37), (0.15, 0.44), (0.07, 0.49), (0.035, 0.52), (0.04, 0.55), (0.0, 0.55)]
    K.lathe(profile, black, seg=14)
    K.tube((0.0, 0.0, 0.5), (0.0, 0.0, 0.525), 0.05, 0.05, tie, sides=8)                       # the tie
    for a in (0.5, 2.6):                                                                       # the two ears of the knot
        K.tube((0.0, 0.0, 0.53), (0.09 * math.cos(a), 0.09 * math.sin(a), 0.62), 0.018, 0.006, black, sides=5)
    return K.done(BAG)


# ------------------------------------------------------------------------------------------------------------------------------------- the bin

def bin_():
    K = props.Kit()
    K.smooth = False
    green = props.mat('BinGreen', (0.12, 0.32, 0.2), 0.55)
    lid = props.mat('BinLid', (0.1, 0.27, 0.17), 0.5)
    black = props.mat('BinBlack', (0.05, 0.05, 0.06), 0.8)
    grey = props.mat('BinGrey', (0.55, 0.57, 0.6), 0.4)
    x0, x1, y0, y1, h = -0.34, 0.3, -0.27, 0.27, 0.92            # the body: the foot, the rim at 0.92 m (the lid is on top)
    frustum(K, x0 + 0.04, x1 - 0.04, y0 + 0.03, y1 - 0.03, 0.08, h, 0.05, green)
    K.bx((x1 - x0 + 0.02, y1 - y0 + 0.02, 0.04), ((x0 + x1) / 2, 0.0, h + 0.02), lid)         # the lid
    K.bx((0.04, y1 - y0 + 0.06, 0.05), (x1 + 0.025, 0.0, h + 0.02), lid)                       # its hinge edge at the back
    K.bx((0.04, y1 - y0 - 0.08, 0.025), (x0 - 0.01, 0.0, h + 0.035), lid)                      # the lip at the front
    # the handle: a bar across the back of the lid on two posts, within reach of a pusher standing behind
    for sy in (-1, 1):
        K.bx((0.05, 0.035, 0.12), (x1 + 0.05, sy * 0.2, h - 0.04), black)
    K.bx((0.05, y1 - y0 - 0.1, 0.035), (x1 + 0.08, 0.0, h + 0.03), black)
    # the two wheels and the axle at the back foot
    for sy in (-1, 1):
        K.tube((x1 - 0.04, sy * (y1 - 0.02), 0.1), (x1 - 0.04, sy * (y1 + 0.05), 0.1), 0.1, 0.1, black, sides=14, cap0=black, cap1=black)
        K.tube((x1 - 0.04, sy * (y1 + 0.05), 0.1), (x1 - 0.04, sy * (y1 + 0.056), 0.1), 0.04, 0.04, grey, sides=8, cap1=grey)
    K.tube((x1 - 0.04, y0, 0.1), (x1 - 0.04, y1, 0.1), 0.012, 0.012, grey, sides=6)
    # two ribs on the sides so the big flat faces read as moulded plastic, and a stripe across the front
    for sy in (-1, 1):
        K.bx((x1 - x0 - 0.2, 0.012, 0.03), ((x0 + x1) / 2, sy * (y1 - 0.02), 0.6), green)
    return K.done(BIN)


# ------------------------------------------------------------------------------------------------------------------------------------- the truck

BODY_Y0, BODY_Y1 = -3.1, 1.0
BODY_Z = 0.95


def truck():
    cab = ft.mat('CabWhite', (0.93, 0.94, 0.95), 0.4)
    green = ft.mat('RefuseGreen', (0.12, 0.38, 0.24), 0.45)
    dark = ft.mat('Chassis', (0.16, 0.17, 0.19), 0.7, 0.3)
    glass = ft.mat('Glass', (0.1, 0.16, 0.22), 0.1)
    steel = ft.mat('Steel', (0.66, 0.67, 0.69), 0.35, 0.5)
    hopper = ft.mat('Hopper', (0.26, 0.28, 0.3), 0.6, 0.4)
    tire = ft.mat('Tire', (0.06, 0.06, 0.07), 0.9)
    rim = ft.mat('Rim', (0.7, 0.72, 0.75), 0.4, 0.8)
    red = ft.mat('Tail', (0.8, 0.08, 0.06), 0.4, 0.0, (0.8, 0.05, 0.03))
    amber = ft.mat('Beacon', (1.0, 0.6, 0.05), 0.3, 0.0, (1.0, 0.55, 0.02))
    yellow = ft.mat('Head', (1.0, 0.92, 0.6), 0.3, 0.0, (1.0, 0.9, 0.5))
    K = props.Kit()
    hw = ft.WIDTH / 2
    B = lambda x0, x1, y0, y1, z0, z1, m: K.bx((x1 - x0, y1 - y0, z1 - z0), ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), m)
    along_x = Matrix(((0, 0, 1, 0), (1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 0, 1)))
    # the chassis, the cab, the glass, the bumpers, lights and mirrors (as the cargo truck)
    B(-hw + 0.12, hw - 0.12, -3.0, 3.05, 0.45, 0.85, dark)
    K.prism([(1.2, 0.8), (3.05, 0.8), (3.05, 1.45), (2.55, 2.25), (1.2, 2.25)], ft.WIDTH - 0.08, T((-hw + 0.04, 0, 0)) @ along_x, cab)
    B(-hw + 0.02, -hw + 0.07, 1.55, 2.45, 1.35, 2.05, glass)
    B(hw - 0.07, hw - 0.02, 1.55, 2.45, 1.35, 2.05, glass)
    K.prism([(2.58, 1.5), (2.97, 1.5), (2.57, 2.17), (2.48, 2.17)], ft.WIDTH - 0.36, T((-hw + 0.18, 0, 0)) @ along_x, glass)
    B(-hw + 0.04, hw - 0.04, 1.16, 3.04, 0.78, 0.9, green)                                   # a green stripe along the cab's lower edge
    B(-hw + 0.05, hw - 0.05, 3.0, 3.2, 0.5, 0.95, dark)
    B(-hw + 0.2, -hw + 0.55, 3.04, 3.12, 1.0, 1.25, yellow)
    B(hw - 0.55, hw - 0.2, 3.04, 3.12, 1.0, 1.25, yellow)
    B(-hw - 0.18, -hw + 0.02, 2.5, 2.62, 1.55, 1.95, dark)
    B(hw - 0.02, hw + 0.18, 2.5, 2.62, 1.55, 1.95, dark)
    B(-0.2, 0.2, 1.6, 1.85, 2.25, 2.33, amber)                                               # the beacon on the cab roof
    # the refuse body behind the cab: a long green box with a rounded roof, a steel loading hopper at the back and the lift arms
    K.prism([(BODY_Y0, BODY_Z), (BODY_Y1, BODY_Z), (BODY_Y1, 2.35), (BODY_Y1 - 0.3, 2.7), (BODY_Y0 + 0.9, 2.7), (BODY_Y0 + 0.2, 2.5), (BODY_Y0, 2.15)],
            ft.WIDTH - 0.16, T((-hw + 0.08, 0, 0)) @ along_x, green)
    B(-hw + 0.14, hw - 0.14, BODY_Y0 - 0.55, BODY_Y0 + 0.05, BODY_Z + 0.05, 1.75, hopper)      # the hopper: the tipping step at the back
    B(-hw + 0.2, hw - 0.2, BODY_Y0 - 0.58, BODY_Y0 - 0.5, BODY_Z + 0.75, 1.8, steel)           # its raised back panel
    B(-hw + 0.2, hw - 0.2, BODY_Y0 - 0.65, BODY_Y0 - 0.45, BODY_Z + 0.05, BODY_Z + 0.2, steel)   # the rear step
    for sx in (-1, 1):
        B(sx * (hw - 0.5) - 0.05, sx * (hw - 0.5) + 0.05, BODY_Y0 - 0.45, BODY_Y0 + 0.05, 1.2, 2.0, steel)    # a lift arm either side
        B(sx * (hw - 0.32), sx * (hw - 0.22), BODY_Y0 - 0.3, BODY_Y0 + 0.9, 1.1, 1.18, steel)               # a rail along each side of the body
    B(-hw + 0.1, -hw + 0.3, BODY_Y0 - 0.62, BODY_Y0 - 0.58, 1.05, 1.3, red)
    B(hw - 0.3, hw - 0.1, BODY_Y0 - 0.62, BODY_Y0 - 0.58, 1.05, 1.3, red)
    for sx in (-1, 1):                                                                       # fenders over the rear wheels
        x0, x1 = (sx * hw - 0.02, sx * (hw - 0.34)) if sx > 0 else (sx * (hw - 0.34), sx * hw + 0.02)
        B(min(x0, x1), max(x0, x1), ft.REAR_AXLE_Y - 0.55, ft.REAR_AXLE_Y + 0.55, 0.88, 0.93, dark)
    K.done('Body')
    for nm, x, y in (('Wheel_FL', -hw + 0.15, ft.FRONT_AXLE_Y), ('Wheel_FR', hw - 0.15, ft.FRONT_AXLE_Y), ('Wheel_RL', -hw + 0.15, ft.REAR_AXLE_Y), ('Wheel_RR', hw - 0.15, ft.REAR_AXLE_Y)):
        ft.wheel(nm, x, y, tire, rim)
    marker = bpy.data.objects.new('FrontMarker', None)
    marker.location = (0.0, 3.2, 1.0)
    bpy.context.collection.objects.link(marker)


# ------------------------------------------------------------------------------------------------------------------------------------- items

def export(folder, item, objs):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    os.makedirs(folder, exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=os.path.join(folder, item + '.glb'), export_format='GLB', use_selection=True, export_yup=True)
    meshes = [o for o in objs if o.type == 'MESH']
    pts = [o.matrix_world @ v.co for o in meshes for v in o.data.vertices]
    dims = [round(max(p[i] for p in pts) - min(p[i] for p in pts), 3) for i in range(3)]
    tris = sum(len(p.vertices) - 2 for o in meshes for p in o.data.polygons)
    return dims, tris


def manifest(folder, item, template, patch, dims, tris, note):
    m = json.load(open(template, encoding='utf-8'))
    m = json.loads(json.dumps(m))
    m['id'] = item
    m['icon'] = item + '.png'
    for k, v in patch.items():
        if v is None:
            m.pop(k, None)
        elif k == 'properties':
            for pk in list(m['properties']):
                if pk in ('store_category', 'stores', 'sale_unit', 'is_buyable', 'placeable', 'display_weight', 'footprint'):
                    m['properties'].pop(pk, None)
            m['properties'].update(v)
        else:
            m[k] = v
    m['models'] = [{'file': item + '.glb', 'format': 'glb', 'dimensions_m': {'x': dims[0], 'y': dims[2], 'z': dims[1]}, 'triangles': int(tris)}]
    m['category_fields'] = dict(m.get('category_fields') or {}, dimensions_m={'width': dims[0], 'depth': dims[1], 'height': dims[2]})
    props.save(os.path.join(folder, item + '.json'), json.dumps(m, indent=2))
    props.save(os.path.join(folder, 'README.md'), '# %s (`%s`)\n\n%s\n\nProcedural model (tools/make_trash_assets.py), %d triangles. %s See docs/TRASH.md.\n' % (m['name'], item, m['description'], tris, note))
    print('item', item, tris, 'tris', dims)


def main():
    waste_t = os.path.join(ROOT, 'assets', 'waste', 'waste_riser_septic_lid', 'waste_riser_septic_lid.json')
    veh_t = os.path.join(ROOT, 'assets', 'vehicles', 'vehicle_market_cargo_truck', 'vehicle_market_cargo_truck.json')
    base_props = {'is_buyable': True, 'stores': ['depot'], 'store_category': 'Waste', 'sale_unit': 'ea'}

    bpy.ops.wm.read_factory_settings(use_empty=True)
    o = bag()
    folder = os.path.join(ROOT, 'assets', 'waste', BAG)
    dims, tris = export(folder, BAG, [o])
    manifest(folder, BAG, waste_t, {
        'name': 'Full Garbage Bag', 'description': 'A full, tied garbage bag. Put it in a wheeled trash bin and put the bin out in the pickup zone: a bag left out is not collected.',
        'properties': {'weight_kg': 9.0, 'max_stack_size': 8, 'base_value': 2, 'is_consumable': False, 'is_buyable': False, 'stores': []},   # not for sale: bags are made by the game
        'container': None}, dims, tris, 'A bag is trash for the weekly truck; the Market does not buy it.')

    bpy.ops.wm.read_factory_settings(use_empty=True)
    o = bin_()
    folder = os.path.join(ROOT, 'assets', 'waste', BIN)
    dims, tris = export(folder, BIN, [o])
    manifest(folder, BIN, waste_t, {
        'name': 'Wheeled Trash Bin', 'description': 'A big wheeled trash bin with a hinged lid and a handle. It holds four full garbage bags. Push it by the handle to the pickup zone '
                                                    'before the trash truck comes: only bins in the zone are emptied.',
        'properties': dict(base_props, weight_kg=14.0, max_stack_size=1, base_value=65, is_consumable=False, placeable=True),
        'container': {'capacity_kg': 40, 'max_items': 4, 'stacking_limit': 1, 'accepts': [BAG], 'show_fill': False, 'single_type': False, 'pushable': True}},
             dims, tris, 'Handle and wheels at +x, like a wheelbarrow, so it is pushed the same way.')

    bpy.ops.wm.read_factory_settings(use_empty=True)
    truck()
    folder = os.path.join(ROOT, 'assets', 'vehicles', TRUCK)
    objs = list(bpy.data.objects)
    dims, tris = export(folder, TRUCK, objs)
    manifest(folder, TRUCK, veh_t, {
        'name': 'Trash Truck', 'description': 'The weekly trash truck. It comes once a week to the pickup zone, empties the wheeled trash bins standing there and charges the weekly fee.',
        'properties': {'weight_kg': 9800.0, 'base_value': 112000.0, 'is_buyable': False, 'stores': []}}, dims, tris,
             'Built like the cargo truck: four separate wheels Wheel_FL / FR / RL / RR (origin on the hub) and a FrontMarker empty at the nose.')


if __name__ == '__main__':
    main()
