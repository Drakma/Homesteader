"""
Builds the fuel delivery truck (assets/vehicles/vehicle_delivery_fuel_truck) in headless Blender: free, local, low-poly (no Meshy).

    python tools/case_labels.py                                   (paints the FUEL sticker)
    blender --background --python tools/make_fuel_truck.py
    python tools/render_icon_from_model.py assets/vehicles/vehicle_delivery_fuel_truck/vehicle_delivery_fuel_truck.glb \
        assets/vehicles/vehicle_delivery_fuel_truck/vehicle_delivery_fuel_truck.png

The delivery box van (tools/make_boxvan.py) with a tank where the box was: the same chassis, cab, lights, mirrors and four SEPARATE wheels
(Wheel_FL / FR / RL / RR, origin on the hub, so the game can spin them) and the same FrontMarker empty at the nose. Behind the cab: an oval white
tank with dished ends on three saddles, the van's orange stripe as a band round it, a catwalk along the top with two manway hatches, a ladder up
the back, a hose cabinet with a reel on the left side, fenders over the rear wheels, and a FUEL sticker on each side (a picture).

A new item gets its manifest from vehicle_delivery_boxvan; an item that is already in the kit keeps its name, price and the rest.

Conventions: 1 unit = 1 m, ground at z = 0, the nose towards +y (as the van).
"""
import json
import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import case_labels  # noqa: E402
import make_simple_props as props  # noqa: E402    (Kit, save)

ITEM = 'vehicle_delivery_fuel_truck'
VAN = 'vehicle_delivery_boxvan'
VEHICLES = os.path.join(props.ROOT, 'assets', 'vehicles')
FOLDER = os.path.join(VEHICLES, ITEM)
T = Matrix.Translation

WIDTH, HEIGHT = 2.2, 2.75
WHEEL_R, WHEEL_W = 0.42, 0.3
FRONT_AXLE_Y, REAR_AXLE_Y = 2.1, -1.9
TANK_Y0, TANK_Y1, TANK_RX, TANK_RZ = -3.0, 1.0, 1.05, 0.82
TANK_ZC = 0.95 + TANK_RZ
TANK_L = 9000


def mat(name, rgb, rough=0.5, metal=0.0, emit=None):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*rgb, 1.0)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    if emit:
        b.inputs['Emission Color'].default_value = (*emit, 1.0)
        b.inputs['Emission Strength'].default_value = 1.5
    return m


def wheel(name, x, y, tire, rim):
    """As the van's: a tyre whose origin is the hub, with the hub cap as its child."""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    sides = 14
    a_ring = [bm.verts.new((-WHEEL_W / 2, math.cos(2 * math.pi * i / sides) * WHEEL_R, math.sin(2 * math.pi * i / sides) * WHEEL_R)) for i in range(sides)]
    b_ring = [bm.verts.new((WHEEL_W / 2, v.co.y, v.co.z)) for v in a_ring]
    for i in range(sides):
        j = (i + 1) % sides
        bm.faces.new((a_ring[i], a_ring[j], b_ring[j], b_ring[i]))
    bm.faces.new(b_ring)
    bm.faces.new(a_ring[::-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(me)
    bm.free()
    me.materials.append(tire)
    o = bpy.data.objects.new(name, me)
    o.location = (x, y, WHEEL_R)
    bpy.context.collection.objects.link(o)
    hm = bpy.data.meshes.new(name + '_hub')
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = (v.co.x * (WHEEL_W + 0.02), v.co.y * 0.24, v.co.z * 0.24)
    bm.to_mesh(hm)
    bm.free()
    hm.materials.append(rim)
    hub = bpy.data.objects.new(name + '_hub', hm)
    hub.parent = o
    bpy.context.collection.objects.link(hub)
    return o


def tank(K, white, stripe):
    """An oval tank along y with dished ends, and the stripe as a band round its middle."""
    seg, dish = 20, 0.28
    length = TANK_Y1 - TANK_Y0
    prof = [(math.sin(a), dish * (1 - math.cos(a))) for a in [math.pi / 2 * k / 4 for k in range(5)]]
    prof = [(r, y) for r, y in prof] + [(r, length - y) for r, y in reversed(prof)]
    rings = []
    for r, y in prof:
        if r < 1e-6:
            rings.append([K.bm.verts.new((0.0, TANK_Y0 + y, TANK_ZC))])
        else:
            rings.append([K.bm.verts.new((r * TANK_RX * math.cos(2 * math.pi * k / seg), TANK_Y0 + y, TANK_ZC + r * TANK_RZ * math.sin(2 * math.pi * k / seg))) for k in range(seg)])
    mi = K.mi(white)
    for a in range(len(rings) - 1):
        ra, rb = rings[a], rings[a + 1]
        for k in range(seg):
            j = (k + 1) % seg
            if len(ra) == 1:
                f = K.bm.faces.new((ra[0], rb[j], rb[k]))
            elif len(rb) == 1:
                f = K.bm.faces.new((ra[k], ra[j], rb[0]))
            else:
                f = K.bm.faces.new((ra[k], ra[j], rb[j], rb[k]))
            f.material_index = mi
    si = K.mi(stripe)                                                    # the orange band: a ring a hair bigger than the tank
    for y0, y1 in ((TANK_Y0 + length * 0.42, TANK_Y0 + length * 0.58),):
        a_ring = [K.bm.verts.new((1.004 * TANK_RX * math.cos(2 * math.pi * k / seg), y0, TANK_ZC + 1.004 * TANK_RZ * math.sin(2 * math.pi * k / seg))) for k in range(seg)]
        b_ring = [K.bm.verts.new((v.co.x, y1, v.co.z)) for v in a_ring]
        for k in range(seg):
            j = (k + 1) % seg
            K.bm.faces.new((a_ring[k], a_ring[j], b_ring[j], b_ring[k])).material_index = si


def sticker(obj, name, y_mid, height, steps=4):
    """The picture `name` wrapped on both sides of the oval tank, at its widest, and joined to `obj`."""
    path = os.path.join(case_labels.LABELS, name + '.png')
    if not os.path.exists(path):
        print('no sticker painted:', name, '(python tools/case_labels.py)')
        return obj
    m = bpy.data.materials.new('TankSticker')
    m.use_nodes = True
    tex = m.node_tree.nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(path)
    tex.image.pack()
    m.node_tree.links.new(tex.outputs['Color'], m.node_tree.nodes['Principled BSDF'].inputs['Base Color'])
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new('UVMap')
    width = height * case_labels.ASPECT
    span = math.asin(min(0.95, height / 2 / TANK_RZ)) * 2
    for side in (-1, 1):                                                 # -1: the -x side, 1: the +x side
        yl, yr = (y_mid + width / 2, y_mid - width / 2) if side < 0 else (y_mid - width / 2, y_mid + width / 2)      # the reader's left and right
        for k in range(steps):
            a0, a1 = -span / 2 + span * k / steps, -span / 2 + span * (k + 1) / steps
            at = lambda y, a: (side * 1.006 * TANK_RX * math.cos(a), y, TANK_ZC + 1.006 * TANK_RZ * math.sin(a))
            f = bm.faces.new([bm.verts.new(q) for q in (at(yl, a0), at(yr, a0), at(yr, a1), at(yl, a1))])
            for loop, t in zip(f.loops, ((0, k / steps), (1, k / steps), (1, (k + 1) / steps), (0, (k + 1) / steps))):
                loop[uv].uv = t
    me = bpy.data.meshes.new('sticker')
    bm.to_mesh(me)
    bm.free()
    me.materials.append(m)
    lab = bpy.data.objects.new('sticker', me)
    bpy.context.collection.objects.link(lab)
    if not obj.data.uv_layers:
        obj.data.uv_layers.new(name='UVMap')
    bpy.ops.object.select_all(action='DESELECT')
    lab.select_set(True)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.join()
    return obj


def build():
    white = mat('VanWhite', (0.93, 0.94, 0.95), 0.4)
    cream = mat('VanCab', (0.88, 0.9, 0.92), 0.45)
    dark = mat('VanDark', (0.16, 0.17, 0.19), 0.7, 0.3)
    glass = mat('VanGlass', (0.1, 0.16, 0.22), 0.1)
    stripe = mat('VanStripe', (0.88, 0.5, 0.18), 0.5)
    tire = mat('VanTire', (0.06, 0.06, 0.07), 0.9)
    rim = mat('VanRim', (0.7, 0.72, 0.75), 0.4, 0.8)
    red = mat('VanTail', (0.8, 0.08, 0.06), 0.4, 0.0, (0.8, 0.05, 0.03))
    yellow = mat('VanHead', (1.0, 0.92, 0.6), 0.3, 0.0, (1.0, 0.9, 0.5))
    steel = mat('TruckSteel', (0.66, 0.67, 0.69), 0.35, 0.5)
    hose = mat('TruckHose', (0.05, 0.05, 0.055), 0.8)
    K = props.Kit()
    hw = WIDTH / 2
    B = lambda x0, x1, y0, y1, z0, z1, m: K.bx((x1 - x0, y1 - y0, z1 - z0), ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), m)
    along_x = Matrix(((0, 0, 1, 0), (1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 0, 1)))
    # the van's chassis, cab, glass, bumpers, lights and mirrors
    B(-hw + 0.12, hw - 0.12, -3.0, 3.05, 0.45, 0.85, dark)
    K.prism([(1.2, 0.8), (3.05, 0.8), (3.05, 1.45), (2.55, 2.25), (1.2, 2.25)], WIDTH - 0.08, T((-hw + 0.04, 0, 0)) @ along_x, cream)
    B(-hw + 0.02, -hw + 0.07, 1.55, 2.45, 1.35, 2.05, glass)
    B(hw - 0.07, hw - 0.02, 1.55, 2.45, 1.35, 2.05, glass)
    K.prism([(2.58, 1.5), (2.97, 1.5), (2.57, 2.17), (2.48, 2.17)], WIDTH - 0.36, T((-hw + 0.18, 0, 0)) @ along_x, glass)
    B(-hw + 0.05, hw - 0.05, 3.0, 3.2, 0.5, 0.95, dark)
    B(-hw + 0.05, hw - 0.05, -3.25, -3.05, 0.5, 0.95, dark)
    B(-hw + 0.2, -hw + 0.55, 3.04, 3.12, 1.0, 1.25, yellow)
    B(hw - 0.55, hw - 0.2, 3.04, 3.12, 1.0, 1.25, yellow)
    B(-hw + 0.1, -hw + 0.3, -3.27, -3.24, 0.6, 0.9, red)
    B(hw - 0.3, hw - 0.1, -3.27, -3.24, 0.6, 0.9, red)
    B(-hw - 0.18, -hw + 0.02, 2.5, 2.62, 1.55, 1.95, dark)
    B(hw - 0.02, hw + 0.18, 2.5, 2.62, 1.55, 1.95, dark)
    B(-hw + 0.2, hw - 0.2, 1.08, 1.2, 0.85, 2.3, dark)                                   # a headboard between the cab and the tank
    # the tank on three saddles
    tank(K, white, stripe)
    for y in (TANK_Y0 + 0.5, (TANK_Y0 + TANK_Y1) / 2, TANK_Y1 - 0.5):
        B(-TANK_RX * 0.72, TANK_RX * 0.72, y - 0.08, y + 0.08, 0.85, TANK_ZC - TANK_RZ * 0.6, dark)
    # the catwalk along the top, two manway hatches on it, a ladder up the back
    top = TANK_ZC + TANK_RZ
    B(-0.3, 0.3, TANK_Y0 + 0.35, TANK_Y1 - 0.35, top - 0.02, top + 0.02, dark)
    for sx in (-1, 1):
        B(sx * 0.3 - 0.015, sx * 0.3 + 0.015, TANK_Y0 + 0.35, TANK_Y1 - 0.35, top + 0.02, top + 0.07, steel)
    for y in (TANK_Y0 + 1.1, TANK_Y1 - 1.1):
        K.lathe([(0.24, top + 0.02), (0.24, top + 0.1), (0.2, top + 0.14), (0.0, top + 0.15)], steel, 12, T((0, y, 0)))
        K.bx((0.06, 0.1, 0.03), (0.22, y, top + 0.11), dark)
    ly = TANK_Y0 - 0.02
    for sx in (-1, 1):
        K.tube((sx * 0.22, ly - 0.12, 0.95), (sx * 0.22, ly + 0.2, top + 0.05), 0.02, 0.02, steel, 6)
    for k in range(6):
        t = (k + 0.5) / 6
        K.tube((-0.22, ly - 0.12 + 0.32 * t, 0.95 + (top - 0.9) * t), (0.22, ly - 0.12 + 0.32 * t, 0.95 + (top - 0.9) * t), 0.014, 0.014, steel, 5)
    # the hose cabinet on the left side, low, with its reel and the hose
    cy0, cy1 = -0.9, 0.3
    B(-hw - 0.02, -hw + 0.3, cy0, cy1, 0.55, 1.05, dark)
    K.lathe([(0.2, 0.0), (0.2, 0.05), (0.09, 0.06), (0.0, 0.06)], hose, 12, T((-hw - 0.02, (cy0 + cy1) / 2 - 0.2, 0.8)) @ Matrix.Rotation(-math.pi / 2, 4, 'Y'))
    K.lathe([(0.07, 0.06), (0.07, 0.075), (0.0, 0.075)], steel, 8, T((-hw - 0.02, (cy0 + cy1) / 2 - 0.2, 0.8)) @ Matrix.Rotation(-math.pi / 2, 4, 'Y'))
    K.path([(-hw - 0.07, (cy0 + cy1) / 2, 0.72), (-hw - 0.09, cy1 - 0.25, 0.66), (-hw - 0.08, cy1 - 0.12, 0.86)], 0.022, hose, 6)
    K.bx((0.05, 0.16, 0.05), (-hw - 0.08, cy1 - 0.1, 0.9), steel)                             # the nozzle
    # fenders over the rear wheels, and a pair of marker lights on the tank's rear
    for sx in (-1, 1):
        x0, x1 = (sx * hw - 0.02, sx * (hw - 0.34)) if sx > 0 else (sx * (hw - 0.34), sx * hw + 0.02)
        B(min(x0, x1), max(x0, x1), REAR_AXLE_Y - 0.55, REAR_AXLE_Y + 0.55, 0.88, 0.93, dark)
        B(sx * 0.6 - 0.06, sx * 0.6 + 0.06, TANK_Y0 - 0.02, TANK_Y0 + 0.02, TANK_ZC - 0.05, TANK_ZC + 0.05, red)
    body = K.done('Body')
    body = sticker(body, 'tank_fuel', TANK_Y0 + (TANK_Y1 - TANK_Y0) * 0.22, 0.5)
    body.name = 'Body'
    for nm, x, y in (('Wheel_FL', -hw + 0.15, FRONT_AXLE_Y), ('Wheel_FR', hw - 0.15, FRONT_AXLE_Y), ('Wheel_RL', -hw + 0.15, REAR_AXLE_Y), ('Wheel_RR', hw - 0.15, REAR_AXLE_Y)):
        wheel(nm, x, y, tire, rim)
    marker = bpy.data.objects.new('FrontMarker', None)
    marker.location = (0.0, 3.2, 1.0)
    bpy.context.collection.objects.link(marker)


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
        m = json.load(open(os.path.join(VEHICLES, VAN, VAN + '.json'), encoding='utf-8'))
        m.update({'id': ITEM, 'icon': ITEM + '.png', 'name': 'Fuel Delivery Truck',
                  'description': 'A white tank truck with an orange band: the delivery van with a fuel tank in place of the box, a hose reel on the side and a ladder up the back.'})
        m['properties'].update({'weight_kg': 5200.0, 'base_value': 62000.0})
        m['category_fields'] = dict(m.get('category_fields') or {}, cargo_capacity_m3=0)
        m['liquid_container'] = {'capacity_l': TANK_L, 'accepts': ['#liquid_fuel']}
    m['models'] = [{'file': ITEM + '.glb', 'format': 'glb', 'dimensions_m': {'x': WIDTH, 'y': round(height, 2), 'z': 6.45}, 'triangles': tris}]
    m['category_fields'] = dict(m.get('category_fields') or {}, dimensions_m={'width': WIDTH, 'depth': 6.45, 'height': round(height, 2)})
    props.save(path, json.dumps(m, indent=2))
    props.save(os.path.join(FOLDER, 'README.md'), '# %s (`%s`)\n\n%s\n\nProcedural model (tools/make_fuel_truck.py), %d triangles. Built like the delivery box van: the four '
               'wheels are separate objects named `Wheel_FL`, `Wheel_FR`, `Wheel_RL`, `Wheel_RR` with their origin on the hub, and an empty named `FrontMarker` sits at '
               'the nose, so the game can drive it the same way. The FUEL sticker on the tank is a picture (tools/case_labels.py).\n' % (m['name'], ITEM, m['description'], tris))
    print('truck', ITEM, '|', tris, 'tris | height', round(height, 2))


if __name__ == '__main__':
    main()
