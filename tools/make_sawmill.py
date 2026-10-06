"""
Builds the stationary sawmill (assets/vehicles/vehicle_sawmill_stationary) as a GLB in headless Blender: free, local, low-poly (no Meshy), detailed with painted pictures
(tools/sawmill_pictures.py): the maker's plate, the engine's cover, the fuel tank's label, hazard stickers, the ruler along the bed.

    python tools/sawmill_pictures.py
    blender --background --python tools/make_sawmill.py
    python tools/render_icon_from_model.py assets/vehicles/vehicle_sawmill_stationary/vehicle_sawmill_stationary.glb assets/vehicles/vehicle_sawmill_stationary/vehicle_sawmill_stationary.png

A gasoline-powered sawmill: a 6 m bed (an uncut log of 4 m on its cradles, with a metre of clear track at each end) with a saw carriage that rides on two rails along it.
Three named parts, which Sawmill.cs finds by name: "Frame" (the bed, the rails, the legs), "SawCarriage" (the gantry, the engine, the handles: it travels along x, from where it
stands at home to its mirror at the other end) and "SawBlade" (a child of the carriage, at its axis: it spins about its own local z in the game).

Conventions: 1 unit = 1 m, the ground at z = 0, centred on x and y, the track along x, the FRONT (where the lumber comes out) facing -y.
"""
import json
import math
import os
import sys

import bpy
from mathutils import Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_simple_props as props  # noqa: E402    (Kit, mat, save)
from make_internet import fq, bq, tq, lq, rq, pictures, E  # noqa: E402

VEH = os.path.join(props.ROOT, 'assets', 'vehicles')
ITEM = 'vehicle_sawmill_stationary'
T = Matrix.Translation
mat = props.mat
S = 0.7                   # how much slimmer and lower than first modelled: the TRACK keeps its length (a 4 m log and a metre each end), everything across and up is scaled
HOME_X = -2.55            # the carriage's rest place; it travels to +2.55 (the log lies between -2.0 and 2.0)
BLADE_Z = 1.15


def RXd(deg):
    return Matrix.Rotation(math.radians(deg), 4, 'X')


def frame():
    K = props.Kit()
    green = mat('SawmillGreen', (0.1, 0.34, 0.2), 0.55)
    dark = mat('SawmillDark', (0.12, 0.13, 0.15), 0.55)
    steel = mat('SawmillRail', (0.66, 0.68, 0.7), 0.35)
    wood = mat('SawmillWood', (0.74, 0.58, 0.36), 0.85)
    yellow = mat('SawmillYellow', (0.9, 0.72, 0.1), 0.5)
    xs = (-2.75, -1.4, 0.0, 1.4, 2.75)
    for x in xs:
        for sy in (-1, 1):
            K.bx((0.1, 0.1, 0.3), (x, sy * 0.62, 0.15), green)                          # the inner legs
            K.bx((0.22, 0.22, 0.012), (x, sy * 0.62, 0.006), dark)
            K.bx((0.1, 0.1, 0.76), (x, sy * 0.86, 0.38), green)                         # the outer legs, up to the carriage rails
            K.bx((0.22, 0.22, 0.012), (x, sy * 0.86, 0.006), dark)
            K.bx((0.1, 0.24, 0.08), (x, sy * 0.74, 0.37), green)                        # and the arm that ties them to the bed beam
        K.bx((0.1, 1.38, 0.1), (x, 0.0, 0.33), green)                                   # cross members
    for sy in (-1, 1):
        K.bx((6.0, 0.14, 0.2), (0.0, sy * 0.62, 0.38), green)                           # the two bed beams
        K.bx((5.8, 0.1, 0.08), (0.0, sy * 0.33, 0.48), steel)                           # the bed rails the cradles stand on
        K.bx((6.2, 0.1, 0.07), (0.0, sy * 0.86, 0.80), steel)                           # the carriage rails
        K.bx((6.2, 0.05, 0.016), (0.0, sy * 0.86, 0.843), mat('SawmillRailTop', (0.82, 0.84, 0.86), 0.25))
    for x in (-1.9, -0.65, 0.65, 1.9):                                                  # the cradles: two boards in a V on a block
        K.bx((0.2, 0.14, 0.1), (x, 0.0, 0.56), green)
        for sy in (-1, 1):
            K.bx((0.16, 0.5, 0.05), (x, sy * 0.27, 0.64), wood, RXd(sy * 40))
    for x in (-1.2, 1.2):                                                               # the log dogs on the back side: a post, an arm and a screw
        K.bx((0.08, 0.08, 0.55), (x, 0.55, 0.755), green)
        K.bx((0.07, 0.3, 0.05), (x, 0.4, 0.98), green)
        K.tube((x, 0.26, 0.98), (x, 0.26, 0.82), 0.02, 0.02, steel, 8, steel, dark)
        K.bx((0.09, 0.07, 0.02), (x, 0.26, 0.81), dark)
    K.bx((0.06, 0.8, 0.46), (-2.04, 0.0, 0.72), dark)                                    # the log stop at the home end
    K.bx((0.04, 1.5, 0.4), (3.02, 0.0, 0.4), green)                                      # an end panel, with the maker's plate
    K.bx((0.5, 0.04, 0.04), (3.0, 0.0, 0.62), yellow)                                    # and a bumper beam for the carriage
    for sx in (-1, 1):
        K.bx((0.12, 0.12, 0.06), (sx * 3.02, 0.86, 0.84), yellow)                        # the carriage's end stops on the rails
        K.bx((0.12, 0.12, 0.06), (sx * 3.02, -0.86, 0.84), yellow)
    obj = K.done('Frame')
    return pictures(obj,
                    ('sm_ruler', [fq(-2.95, 2.95, 0.32, 0.44, -0.62 - 0.07 - E)]),          # the scale on the front bed beam
                    ('sm_plate', [rq(-0.4, 0.4, 0.26, 0.56, 3.04 + E)]),                      # the maker's plate on the end panel
                    ('sm_stop', [lq(-0.35, 0.35, 0.55, 0.9, -2.07 - E)]))


def carriage():
    K = props.Kit()
    green = mat('SawmillGreen', (0.1, 0.34, 0.2), 0.55)
    dark = mat('SawmillDark', (0.12, 0.13, 0.15), 0.55)
    steel = mat('SawmillRail', (0.66, 0.68, 0.7), 0.35)
    red = mat('EngineRed', (0.72, 0.1, 0.08), 0.5)
    rubber = mat('GripRubber', (0.06, 0.06, 0.065), 0.8)
    alu = mat('EngineAluminium', (0.62, 0.64, 0.66), 0.4)
    yellow = mat('TankYellow', (0.9, 0.74, 0.12), 0.5)
    for sy in (-1, 1):
        y = sy * 0.86
        K.bx((0.7, 0.14, 0.1), (0.0, y, 0.935), green)                                   # the bogie on each rail
        for xw in (-0.28, 0.28):
            K.tube((xw, y - 0.06, 0.895), (xw, y + 0.06, 0.895), 0.06, 0.06, dark, 10, dark, dark)   # its wheels
        K.bx((0.14, 0.14, 1.1), (0.0, y, 1.485), green)                                  # the upright
        for sx in (-1, 1):
            K.tube((sx * 0.32, y, 0.99), (sx * 0.07, y, 1.45), 0.025, 0.025, green, 6, green, green)   # the braces
    K.bx((0.16, 2.0, 0.16), (0.0, 0.0, 2.04), green)                                      # the top beam across
    K.bx((0.16, 0.2, 0.92), (0.0, 0.0, 1.58), dark)                                       # the saw head's mast
    K.tube((0.0, -0.13, BLADE_Z), (0.0, 0.13, BLADE_Z), 0.05, 0.05, steel, 10, steel, steel)   # the arbor the blade turns on
    # the blade guard: a plate on the back side and a band over the top half
    guard = [(0.5 * math.cos(math.pi * k / 12), 0.5 * math.sin(math.pi * k / 12)) for k in range(13)]
    K.prism(guard, 0.02, T((0.0, 0.1, BLADE_Z)) @ Matrix.Rotation(math.pi / 2, 4, 'X'), dark)
    for k in range(12):
        a = math.pi * (k + 0.5) / 12
        K.box((0.27, 0.16, 0.02), T((0.5 * math.cos(a), 0.02, BLADE_Z + 0.5 * math.sin(a))) @ Matrix.Rotation(-(a + math.pi / 2), 4, 'Y'), dark)
    # the engine: on a plate on the top beam, behind the mast
    K.bx((0.62, 0.5, 0.04), (0.0, 0.62, 2.14), dark)
    K.bx((0.42, 0.3, 0.24), (0.0, 0.62, 2.28), alu)                                       # the crankcase
    K.bx((0.22, 0.22, 0.14), (-0.1, 0.62, 2.43), alu)                                     # the cylinder head
    for k in range(5):
        K.bx((0.26, 0.26, 0.012), (-0.1, 0.62, 2.38 + k * 0.026), alu)                    # its cooling fins
    K.bx((0.4, 0.28, 0.05), (0.0, 0.62, 2.425), red)                                      # the red cover
    K.tube((0.21, 0.62, 2.30), (0.31, 0.62, 2.30), 0.1, 0.1, red, 12, red, dark)          # the pull start housing
    K.path([(0.31, 0.62, 2.30), (0.42, 0.62, 2.30), (0.46, 0.62, 2.22)], 0.007, dark, 6)   # its rope and handle
    K.bx((0.05, 0.05, 0.03), (0.46, 0.62, 2.2), rubber)
    K.tube((-0.14, 0.78, 2.3), (-0.14, 1.0, 2.3), 0.05, 0.05, alu, 10, alu, dark)         # the muffler
    K.tube((-0.14, 1.0, 2.3), (-0.14, 1.0, 2.16), 0.025, 0.025, alu, 6)
    K.tube((0.1, 0.62, 2.45), (0.1, 0.62, 2.53), 0.07, 0.07, dark, 10, dark, dark)        # the air cleaner
    K.bx((0.4, 0.2, 0.2), (0.0, 0.28, 2.28), yellow)                                      # the fuel tank in front of it
    K.tube((0.14, 0.28, 2.38), (0.14, 0.28, 2.43), 0.03, 0.03, dark, 8, dark, dark)       # its cap
    K.tube((0.0, 0.47, 2.2), (0.0, 0.14, 1.2), 0.045, 0.045, dark, 8, dark, dark)         # the drive cover from the engine down to the arbor
    for sy in (-1, 1):                                                                    # the push handle: arms to a cross bar with grips
        K.tube((0.07, sy * 0.86, 1.3), (0.62, sy * 0.86, 1.3), 0.022, 0.022, steel, 8, steel, steel)
    K.tube((0.62, -0.86, 1.3), (0.62, 0.86, 1.3), 0.024, 0.024, steel, 8, steel, steel)
    for sy in (-1, 1):
        K.tube((0.62, sy * 0.58, 1.3), (0.62, sy * 0.86, 1.3), 0.032, 0.032, rubber, 8, rubber, rubber)
    obj = K.done('SawCarriage')
    return pictures(obj,
                    ('sm_engine', [tq(-0.18, 0.18, 0.49, 0.75, 2.45 + E)]),
                    ('sm_tank', [fq(-0.16, 0.16, 2.21, 2.35, 0.18 - E)]),
                    ('sm_hazard', [fq(-0.075, 0.075, 1.5, 1.6, -0.1 - E)]))


def blade():
    """The blade as it hangs, centred on its own origin, the disc in the x z plane (it turns about its own y in Blender, z in the game)."""
    K = props.Kit()
    steel = mat('BladeSteel', (0.78, 0.8, 0.82), 0.25)
    dark = mat('BladeHub', (0.2, 0.2, 0.22), 0.5)
    K.lathe([(0.0, -0.003), (0.44, -0.003), (0.44, 0.003), (0.0, 0.003)], steel, 28, props.RY)   # the disc
    for k in range(28):                                                                          # its teeth
        a = 2 * math.pi * k / 28
        K.box((0.05, 0.012, 0.016), T((0.455 * math.cos(a), 0.0, 0.455 * math.sin(a))) @ Matrix.Rotation(-a - 0.5, 4, 'Y'), steel)
    K.tube((0.0, -0.025, 0.0), (0.0, 0.025, 0.0), 0.09, 0.09, dark, 12, dark, dark)                # the hub and its washers
    K.tube((0.0, -0.035, 0.0), (0.0, 0.035, 0.0), 0.035, 0.035, steel, 8, steel, steel)
    return K.done('SawBlade')


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    fr = frame()
    car = carriage()
    bl = blade()
    fr.data.transform(Matrix.Diagonal((1.0, S, S, 1.0)))        # the frame: as long as it was, narrower and lower
    car.data.transform(Matrix.Scale(S, 4))                       # the carriage and the blade: smaller all round (they ride on the scaled rails)
    bl.data.transform(Matrix.Scale(S, 4))
    car.location = (HOME_X, 0.0, 0.0)
    bl.parent = car
    bl.location = (0.0, 0.0, BLADE_Z * S)
    bpy.context.view_layer.update()
    objs = [fr, car, bl]
    pts = [o.matrix_world @ v.co for o in objs for v in o.data.vertices]
    lo = [min(p[i] for p in pts) for i in range(3)]
    hi = [max(p[i] for p in pts) for i in range(3)]
    dims = [round(hi[i] - lo[i], 3) for i in range(3)]
    tris = sum(len(p.vertices) - 2 for o in objs for p in o.data.polygons)
    assert lo[2] > -0.003, lo
    folder = os.path.join(VEH, ITEM)
    for f in os.listdir(folder):                                                           # the old OBJ model
        if f.lower().endswith(('.obj', '.mtl')) or (f.lower().endswith('.glb') and f != ITEM + '.glb'):
            os.remove(os.path.join(folder, f))
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = fr
    bpy.ops.export_scene.gltf(filepath=os.path.join(folder, ITEM + '.glb'), export_format='GLB', use_selection=True, export_yup=True)
    path = os.path.join(folder, ITEM + '.json')
    m = json.load(open(path, encoding='utf-8'))
    p = m['properties']
    p.update({'placeable': True, 'sawmill': True, 'footprint': '%.2fm W x %.2fm D x %.2fm H' % (dims[0], dims[1], dims[2])})
    m['description'] = ('A gasoline powered stationary sawmill: a 6 m bed with a saw carriage on rails. Left click it with an uncut log in hand to lay the log on the track, then right '
                        'click it, choose the lumber you want and the carriage makes three passes. The cut lumber is stacked beside it. It runs on gasoline: pour a can into its tank (right click it with the can in hand); a cut burns half a liter.')
    m['models'] = [{'file': ITEM + '.glb', 'format': 'glb', 'dimensions_m': {'x': dims[0], 'y': dims[2], 'z': dims[1]}, 'triangles': tris}]
    m['liquid_container'] = {'capacity_l': 20, 'accepts': ['liquid_gasoline']}   # its tank: gasoline, a can poured into it (Sawmill.cs)
    cf = m.setdefault('category_fields', {})
    cf.update({'fuel_type': 'gasoline', 'tank_capacity_l': 20, 'fuel_consumption_l_per_min': 0.1, 'dimensions_m': {'width': round(dims[1], 2), 'depth': round(dims[0], 2), 'height': round(dims[2], 2)}})
    props.save(path, json.dumps(m, indent=2))
    props.save(os.path.join(folder, 'README.md'), '# %s\n\n%s\n\nProcedural model (tools/make_sawmill.py), %d triangles, %.2f x %.2f x %.2f m, detail painted (tools/sawmill_pictures.py). Parts the game '
               'finds by name: `Frame`, `SawCarriage` (travels along x from its home end to the mirror of it) and `SawBlade` (spins). See docs/SAWMILL.md.\n' % (m['name'], m['description'], tris, *dims))
    print('sawmill', tris, 'tris |', dims, '| carriage home x', HOME_X)


if __name__ == '__main__':
    main()
