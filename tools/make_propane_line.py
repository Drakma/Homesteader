"""
The parts of a propane line (docs/WIRING.md, "Propane"): the house connector's model, and the manifests of the pipe and the connector.

    blender --background --python tools/make_propane_line.py                       (the connector; writes the pipe's manifest when it is new)
    (the pipe's model and its stacks of 10 and 20 were built by tools/make_material_stacks.py, single_pipe, while the items were still in the building
     category as pipe_propane; they have since been moved to fuel as fuel_pipe_propane*, which that script does not reach)
    python tools/set_wiring_data.py                                                (wire_role / wire_kind / wire_length_m on all of them, and on the tanks)
    python tools/render_icon_from_model.py <glb> <png>                             (each of them)

  fuel_pipe_propane               a 3 m length of charcoal grey propane pipe with a yellow gas line down it (model: make_material_stacks.py)
  fuel_propane_fill_post          the fill post: a post in the ground with a fill valve, a gauge and a yellow hose; piped to a tank, a right click with a
                                  portable propane tank in hand fills that tank (Assets/Scripts/Growth/PropaneFill.cs)
  fuel_propane_house_connector    the house connector: a riser up to a shut-off valve with a yellow lever, a regulator, and an elbow into the wall,
                                  on a wall bracket. Mounted on the OUTSIDE of a building and piped to a propane tank it gives the building propane.

A propane line is joined like a wire (right click a tank, then a connector) but with the pipe wrench in hand, and it is made of propane pipe: it
runs along the walls of a building and underground everywhere else.

Convention for a wall item (docs/ATTACHED_ITEMS.md): the back against the wall at y = 0, the front facing -y, the bottom at z = 0, centred on x.
"""
import json
import math
import os
import sys

import bpy
from mathutils import Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_simple_props as props  # noqa: E402    (Kit, mat, save)

ASSETS = os.path.join(props.ROOT, 'assets')
T = Matrix.Translation
mat = props.mat
CHARCOAL = (0.2, 0.21, 0.23)
PIPE, CONNECTOR, FILL_POST = 'fuel_pipe_propane', 'fuel_propane_house_connector', 'fuel_propane_fill_post'


def connector():
    K = props.Kit()
    pipe = mat('PropanePipe', CHARCOAL, 0.45)
    dark = mat('PropaneBracket', (0.12, 0.12, 0.13), 0.55)
    body = mat('RegulatorBody', (0.6, 0.61, 0.63), 0.4)
    red = mat('RegulatorCap', (0.75, 0.1, 0.08), 0.5)
    brass = mat('ValveBrass', (0.8, 0.62, 0.25), 0.35)
    yellow = mat('ValveLever', (0.95, 0.78, 0.08), 0.5)
    W, H = 0.2, 0.44
    y = -0.06                                                             # the line stands this far off the wall
    r = 0.015
    K.bx((W, 0.006, H * 0.86), (0, -0.003, H * 0.5), dark)                   # the wall bracket, with its four screws
    for sx in (-1, 1):
        for z in (H * 0.12, H * 0.88):
            K.lathe([(0.008, 0.0), (0.008, 0.003), (0.0, 0.004)], body, 6, T((sx * W * 0.38, -0.006, z)) @ Matrix.Rotation(math.pi / 2, 4, 'X'))
    K.tube((0, y, 0.0), (0, y, H * 0.3), r, r, pipe, 10, pipe)               # the riser from the ground
    # the shut-off valve: a brass body on the riser, the lever in line with the pipe (open)
    vz = H * 0.34
    K.lathe([(r * 1.3, -0.03), (r * 1.7, -0.02), (r * 1.7, 0.02), (r * 1.3, 0.03)], brass, 10, T((0, y, vz)))
    K.lathe([(0.008, 0.0), (0.008, 0.02), (0.0, 0.02)], brass, 8, T((0, y - r * 1.7, vz)) @ Matrix.Rotation(math.pi / 2, 4, 'X'))
    K.bx((0.02, 0.008, 0.13), (0, y - r * 1.7 - 0.024, vz + 0.045), yellow)
    K.bx((0.026, 0.012, 0.03), (0, y - r * 1.7 - 0.024, vz), yellow)
    K.tube((0, y, vz + 0.03), (0, y, H * 0.56), r, r, pipe, 10)
    # the regulator: a round body facing out, its red vent cap, the adjusting screw
    rz = H * 0.66
    reg = T((0, y + 0.02, rz)) @ Matrix.Rotation(math.pi / 2, 4, 'X')
    K.lathe([(0.0, -0.02), (0.05, -0.02), (0.06, 0.0), (0.06, 0.03), (0.045, 0.045), (0.02, 0.05), (0.0, 0.05)], body, 14, reg)
    K.lathe([(0.02, 0.05), (0.02, 0.075), (0.0, 0.078)], red, 10, reg)
    K.tube((0.045, y, rz), (0.075, y, rz), 0.008, 0.008, brass, 6, None, brass)                # the vent
    K.tube((0, y, rz + 0.055), (0, y, H * 0.9), r, r, pipe, 10)
    K.path([(0, y, H * 0.9), (0, y, H * 0.95), (0, y + 0.02, H * 0.975), (0, 0.0, H * 0.975)], r, pipe, 10)      # the elbow into the wall
    K.lathe([(r * 2.2, 0.0), (r * 2.2, 0.006), (r, 0.008)], dark, 10, T((0, -0.008, H * 0.975)) @ Matrix.Rotation(-math.pi / 2, 4, 'X'))      # the wall plate round it
    for z in (H * 0.14, H * 0.5):                                             # two clamps hold the line to the bracket
        K.bx((0.05, -y, 0.014), (0, y / 2, z), dark)
    return K.done(CONNECTOR)


def fill_post():
    """The fill post: a steel post in a concrete footing, the line up its side to a fill valve with a red handwheel and a gauge, a yellow hose looped to its
    nozzle on a hook, and a PROPANE plate at the top (a picture). Stands in the ground: pivot at the centre of its footing, z = 0."""
    import case_labels
    K = props.Kit()
    pipe = mat('PropanePipe', CHARCOAL, 0.45)
    post = mat('FillPost', (0.16, 0.17, 0.19), 0.5)
    concrete = mat('FillFooting', (0.6, 0.59, 0.56), 0.95)
    brass = mat('ValveBrass', (0.8, 0.62, 0.25), 0.35)
    red = mat('FillHandwheel', (0.78, 0.1, 0.08), 0.5)
    yellow = mat('FillHose', (0.95, 0.78, 0.08), 0.6)
    black = mat('FillGrip', (0.06, 0.06, 0.07), 0.7)
    white = mat('GaugeFace', (0.93, 0.93, 0.9), 0.4)
    steel = mat('FillSteel', (0.62, 0.63, 0.65), 0.35)
    H = 1.15
    K.bx((0.34, 0.34, 0.05), (0, 0, 0.025), concrete)
    K.bx((0.26, 0.26, 0.03), (0, 0, 0.065), concrete)
    K.bx((0.08, 0.08, H), (0, 0, H / 2), post)
    K.bx((0.095, 0.095, 0.012), (0, 0, H + 0.006), steel)
    y = -0.065                                                            # the line runs up the front of the post
    r = 0.015
    K.tube((0, y, 0.0), (0, y, 0.86), r, r, pipe, 10, pipe)
    for z in (0.25, 0.6):
        K.bx((0.06, 0.03, 0.014), (0, y + 0.02, z), steel)                    # clamps
    # the fill valve: a brass block, the handwheel on its front, the gauge above it
    vz = 0.9
    K.bx((0.07, 0.06, 0.08), (0, y, vz), brass)
    K.lathe([(0.008, 0.0), (0.008, 0.03), (0.0, 0.03)], steel, 6, T((0, y - 0.03, vz)) @ Matrix.Rotation(math.pi / 2, 4, 'X'))
    wheel = T((0, y - 0.06, vz)) @ Matrix.Rotation(math.pi / 2, 4, 'X')
    K.lathe([(0.045 + 0.007 * math.cos(a), 0.007 * math.sin(a)) for a in [math.pi / 2 * k for k in range(4)]], red, 12, wheel, closed=True)
    for k in range(3):
        a = k * math.pi / 3
        K.box((0.09, 0.008, 0.008), T((0, y - 0.06, vz)) @ Matrix.Rotation(a, 4, 'Y'), red)
    K.tube((0, y, vz + 0.04), (0, y, vz + 0.075), 0.006, 0.006, brass, 6)
    gauge = T((0, y - 0.012, vz + 0.105)) @ Matrix.Rotation(math.pi / 2, 4, 'X')
    K.lathe([(0.032, -0.012), (0.036, 0.0), (0.036, 0.012), (0.03, 0.014)], steel, 12, gauge)
    K.lathe([(0.03, 0.0145), (0.0, 0.0145)], white, 12, gauge)
    K.bx((0.003, 0.002, 0.024), (0.006, y - 0.0275, vz + 0.11), red, Matrix.Rotation(-0.5, 4, 'Y'))       # the needle
    # the hose: out of the side of the valve, a loop down and back up to the hook on the post, ending in the fill nozzle
    out = (0.035, y, vz - 0.01)
    K.tube(out, (0.06, y, vz - 0.01), 0.012, 0.012, brass, 8)
    hose = [(0.06, y, vz - 0.01), (0.11, y, vz - 0.06), (0.15, y + 0.02, 0.62), (0.14, y + 0.04, 0.36), (0.07, y + 0.05, 0.24), (-0.02, y + 0.03, 0.26),
            (-0.1, y + 0.02, 0.4), (-0.13, y + 0.02, 0.6), (-0.115, y + 0.02, 0.74)]
    K.path(hose, 0.013, yellow, 7)
    K.tube((-0.115, y + 0.02, 0.74), (-0.1, y + 0.02, 0.83), 0.017, 0.017, black, 8, black)                 # the nozzle's hand grip
    K.tube((-0.1, y + 0.02, 0.83), (-0.094, y + 0.02, 0.87), 0.02, 0.02, brass, 10, brass, brass)          # its coupling nut
    K.tube((-0.094, y + 0.02, 0.87), (-0.09, y + 0.02, 0.895), 0.011, 0.011, brass, 8, None, black)
    K.bx((0.07, 0.012, 0.012), (-0.075, y + 0.03, 0.8), steel)                                              # the hook it hangs on
    K.bx((0.012, 0.012, 0.04), (-0.108, y + 0.03, 0.815), steel)
    # the plate at the top, facing the front
    pw = 0.3
    ph = pw / case_labels.ASPECT
    pz = H - 0.02 - ph / 2
    K.bx((pw + 0.016, 0.006, ph + 0.016), (0, -0.044, pz), steel)
    obj = K.done(FILL_POST)
    yy = -0.0475
    return case_labels.add_flat(obj, 'tank_propane', [[(-pw / 2, yy, pz - ph / 2), (pw / 2, yy, pz - ph / 2), (pw / 2, yy, pz + ph / 2), (-pw / 2, yy, pz + ph / 2)]])


def export(obj, folder, item):
    pts = [v.co for v in obj.data.vertices]
    dims = [round(max(p[i] for p in pts) - min(p[i] for p in pts), 3) for i in range(3)]
    tris = sum(len(p.vertices) - 2 for p in obj.data.polygons)
    os.makedirs(folder, exist_ok=True)
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.gltf(filepath=os.path.join(folder, item + '.glb'), export_format='GLB', use_selection=True, export_yup=True)
    return dims, tris


def build_fill_post():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    obj = fill_post()
    obj.name = FILL_POST
    folder = os.path.join(ASSETS, 'fuel', FILL_POST)
    dims, tris = export(obj, folder, FILL_POST)
    path = os.path.join(folder, FILL_POST + '.json')
    if os.path.exists(path):
        m = json.load(open(path, encoding='utf-8'))
    else:
        m = new_manifest('fuel_propane_18l', FILL_POST, 'Propane Fill Post',
                         'A post set in the ground with a fill valve, a gauge and a yellow hose, for filling portable propane tanks. Pipe it to a big propane tank with '
                         'propane pipe and a pipe wrench, then right click it with a portable tank in hand to fill that tank.',
                         {'weight_kg': 18.0, 'base_value': 140, 'max_stack_size': 1, 'placeable': True, 'wire_role': 'propane_filler', 'stores': ['depot']},
                         drop=('liquid_container',))
        m['category_fields'] = dict(m.get('category_fields') or {}, fuel_type='propane', capacity_l=0)
    m['models'] = [{'file': FILL_POST + '.glb', 'format': 'glb', 'dimensions_m': {'x': dims[0], 'y': dims[2], 'z': dims[1]}, 'triangles': tris}]
    m['category_fields'] = dict(m.get('category_fields') or {}, dimensions_m={'width': round(dims[0], 2), 'depth': round(dims[1], 2), 'height': round(dims[2], 2)})
    props.save(path, json.dumps(m, indent=2))
    props.save(os.path.join(folder, 'README.md'), '# %s\n\n%s\n\nProcedural model (tools/make_propane_line.py), %d triangles, %.2f x %.2f x %.2f m. '
               '`wire_role: propane_filler`. See docs/WIRING.md.\n' % (m['name'], m['description'], tris, *dims))
    print('fill post', FILL_POST, '|', tris, 'tris |', dims)


def new_manifest(src_id, item, name, desc, props_update, category=None, drop=()):
    src = [p for p in (os.path.join(ASSETS, c, src_id, src_id + '.json') for c in os.listdir(ASSETS)) if os.path.exists(p)][0]
    m = json.load(open(src, encoding='utf-8'))
    m.update({'id': item, 'icon': item + '.png', 'name': name, 'description': desc})
    if category:
        m['category'] = category
    for k in drop:
        m.pop(k, None)
        m['properties'].pop(k, None)
    m['properties'].update(props_update)
    return m


def main():
    # the pipe: its manifest only (its model and its stacks come from make_material_stacks.py)
    folder = os.path.join(ASSETS, 'fuel', PIPE)
    path = os.path.join(folder, PIPE + '.json')
    if not os.path.exists(path):
        os.makedirs(folder, exist_ok=True)
        m = new_manifest('pipe_pvc_one_inch', PIPE, 'Propane Pipe',
                         'A 3 m length of charcoal grey coated steel pipe for a propane line. With a pipe wrench in hand, right click a propane tank and then a house '
                         'connector to lay it: it runs along the walls of a building and underground everywhere else.',
                         {'weight_kg': 4.5, 'base_value': 16, 'max_stack_size': 10, 'placeable': True, 'wire_kind': 'propane', 'wire_length_m': 3.0})
        m['models'] = []
        props.save(path, json.dumps(m, indent=2))
        props.save(os.path.join(folder, 'README.md'), '# Propane Pipe\n\n%s\n' % m['description'])
        print('manifest', PIPE)
    # the house connector
    bpy.ops.wm.read_factory_settings(use_empty=True)
    obj = connector()
    folder = os.path.join(ASSETS, 'fuel', CONNECTOR)
    os.makedirs(folder, exist_ok=True)
    pts = [v.co for v in obj.data.vertices]
    dims = [round(max(p[i] for p in pts) - min(p[i] for p in pts), 3) for i in range(3)]
    tris = sum(len(p.vertices) - 2 for p in obj.data.polygons)
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.gltf(filepath=os.path.join(folder, CONNECTOR + '.glb'), export_format='GLB', use_selection=True, export_yup=True)
    path = os.path.join(folder, CONNECTOR + '.json')
    if os.path.exists(path):
        m = json.load(open(path, encoding='utf-8'))
    else:
        m = new_manifest('fuel_propane_18l', CONNECTOR, 'Propane House Connector',
                         'The connection that brings propane into a building: a shut-off valve with a yellow lever and a regulator on a wall bracket. Mount it on the '
                         'OUTSIDE of a building (left click a wall with it in hand), then pipe it to a propane tank with propane pipe and a pipe wrench.',
                         {'weight_kg': 3.5, 'base_value': 85, 'max_stack_size': 5, 'placeable': False, 'attach_surface': 'wall', 'attach_side': 'exterior',
                          'wire_role': 'propane_connector', 'stores': ['depot']}, drop=('liquid_container',))
        m['category_fields'] = dict(m.get('category_fields') or {}, fuel_type='propane', capacity_l=0)
    m['properties']['footprint'] = '%.2fm W x %.2fm D x %.2fm H' % (dims[0], dims[1], dims[2])
    m['models'] = [{'file': CONNECTOR + '.glb', 'format': 'glb', 'dimensions_m': {'x': dims[0], 'y': dims[2], 'z': dims[1]}, 'triangles': tris}]
    m['category_fields'] = dict(m.get('category_fields') or {}, dimensions_m={'width': round(dims[0], 2), 'depth': round(dims[1], 2), 'height': round(dims[2], 2)})
    props.save(path, json.dumps(m, indent=2))
    props.save(os.path.join(folder, 'README.md'), '# %s\n\n%s\n\nProcedural model (tools/make_propane_line.py), %d triangles, %.2f x %.2f x %.2f m. Mounts on a wall '
               '(exterior side); `wire_role: propane_connector`. See docs/WIRING.md.\n' % (m['name'], m['description'], tris, *dims))
    print('connector', CONNECTOR, '|', tris, 'tris |', dims)
    build_fill_post()


if __name__ == '__main__':
    main()
