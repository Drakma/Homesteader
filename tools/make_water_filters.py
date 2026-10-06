"""
Builds the four wall-mounted water filters as GLBs in headless Blender: free, local, low-poly (no Meshy).

    blender --background --python tools/make_water_filters.py
    python tools/render_icon_from_model.py assets/water/<id>/<id>.glb assets/water/<id>/<id>.png

  water_filter                       a single cartridge filter: a black head with two ports on a wall bracket, a ribbed blue sump under it
  water_filter_spin_down_sediment    a spin-down sediment filter: a brass head, a clear bowl with the steel screen showing inside, a flush valve underneath
  water_sterilizer_uv_chamber        a UV steriliser: a stainless chamber lying along the wall in two clips, a port at each end, the lamp's cap and
                                     its lead up to a ballast box with a status lamp
  water_filter_reverse_osmosis       a reverse osmosis unit: a white bracket with three cartridge sumps hanging from it, the membrane housing and a
                                     post filter lying across the top, a gauge, and the coloured tubes between them

All four mount on a wall, inside or out (properties.attach_surface: wall, attach_side: either), and keep their `wire_role: water_filter`: they are
piped into a water line like before (docs/WELLS.md). Every item is already in the kit: only the model entry, the dimensions, the mounting
properties and the README are written.

Convention for a wall item (docs/ATTACHED_ITEMS.md): the back against the wall at y = 0, the front facing -y, the bottom at z = 0, centred on x.
"""
import json
import math
import os
import sys

import bpy
from mathutils import Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_simple_props as props  # noqa: E402    (Kit, mat, save, RX)

WATER = os.path.join(props.ROOT, 'assets', 'water')
T = Matrix.Translation
mat = props.mat
OUT = Matrix.Rotation(math.pi / 2, 4, 'X')            # turns a lathe's axis (z) to point out of the wall (-y)


def bracket(K, w, h, z0, m, screws):
    """A plate on the wall with a screw in each corner."""
    K.bx((w, 0.005, h), (0, -0.0025, z0 + h / 2), m)
    for sx in (-1, 1):
        for z in (z0 + 0.02, z0 + h - 0.02):
            K.lathe([(0.007, 0.0), (0.007, 0.003), (0.0, 0.004)], screws, 6, T((sx * (w / 2 - 0.02), -0.005, z)) @ OUT)


def sump(K, x, y, z_top, r, length, m, ribs=5):
    """A cartridge housing hanging from z_top: ribbed for grip low down, a hex boss on the bottom."""
    prof = [(r * 0.96, 0.0), (r * 0.96, -length * 0.45)]
    for k in range(ribs):
        z = -length * 0.5 - k * length * 0.07
        prof += [(r, z), (r, z - length * 0.03), (r * 0.93, z - length * 0.045)]
    prof += [(r * 0.9, -length * 0.9), (r * 0.5, -length * 0.96), (r * 0.5, -length), (0.0, -length)]
    K.lathe(prof, m, 14, T((x, y, z_top)))


def cartridge():
    K = props.Kit()
    plate = mat('FilterBracket', (0.8, 0.81, 0.83), 0.4)
    screws = mat('FilterScrew', (0.45, 0.46, 0.48), 0.4)
    head = mat('FilterHead', (0.1, 0.1, 0.12), 0.5)
    blue = mat('FilterSump', (0.12, 0.36, 0.78), 0.3)
    brass = mat('FilterBrass', (0.8, 0.62, 0.25), 0.35)
    red = mat('ReliefButton', (0.85, 0.12, 0.1), 0.5)
    r, L = 0.05, 0.26
    y = -0.07
    H = L + 0.1
    bracket(K, 0.16, 0.12, H - 0.12, plate, screws)
    K.bx((0.1, -y, 0.012), (0, y / 2, H - 0.012), plate)                                     # the arm the head hangs under
    zt = H - 0.07
    K.lathe([(r * 1.12, -0.012), (r * 1.12, 0.02), (r, 0.045), (r * 0.6, 0.052), (0.0, 0.052)], head, 14, T((0, y, zt)))
    for s in (-1, 1):
        K.tube((s * r * 0.8, y, zt + 0.02), (s * (r + 0.035), y, zt + 0.02), 0.02, 0.02, head, 8)
        K.tube((s * (r + 0.035), y, zt + 0.02), (s * (r + 0.055), y, zt + 0.02), 0.016, 0.016, brass, 8, None, brass)
    K.lathe([(0.009, 0.052), (0.009, 0.064), (0.0, 0.064)], red, 8, T((0, y - 0.02, zt)))
    sump(K, 0, y, zt - 0.01, r, L, blue)
    return K.done('filter')


def spin_down():
    K = props.Kit()
    plate = mat('FilterBracket', (0.8, 0.81, 0.83), 0.4)
    screws = mat('FilterScrew', (0.45, 0.46, 0.48), 0.4)
    brass = mat('FilterBrass', (0.8, 0.62, 0.25), 0.35)
    bowl = mat('ClearBowl', (0.78, 0.88, 0.93), 0.12)
    screen = mat('SteelScreen', (0.55, 0.57, 0.6), 0.35)
    red = mat('FlushHandle', (0.8, 0.12, 0.1), 0.5)
    blue = mat('BowlCollar', (0.12, 0.36, 0.78), 0.35)
    r, L = 0.04, 0.2
    y = -0.065
    H = L + 0.13
    bracket(K, 0.12, 0.1, H - 0.1, plate, screws)
    zt = H - 0.05
    K.lathe([(r * 1.1, -0.02), (r * 1.15, 0.0), (r * 1.15, 0.03), (r * 0.7, 0.045), (0.0, 0.045)], brass, 12, T((0, y, zt)))       # the head
    K.tube((0, y, zt + 0.012), (0, 0.0, zt + 0.012), 0.012, 0.012, brass, 8)                                              # held off the wall by a stud
    for s in (-1, 1):
        K.tube((s * r, y, zt + 0.012), (s * (r + 0.05), y, zt + 0.012), 0.017, 0.017, brass, 8, None, brass)
        K.lathe([(0.022, 0.0), (0.022, 0.014)], brass, 6, T((s * (r + 0.02), y, zt + 0.012)) @ props.RX)                      # the union nut
    K.lathe([(r * 1.16, -0.02), (r * 1.16, -0.045)], blue, 12, T((0, y, zt)))                                              # the collar that holds the bowl
    K.lathe([(r, -0.045), (r, -L * 0.85), (r * 0.7, -L * 0.97), (r * 0.3, -L)], bowl, 12, T((0, y, zt)))                         # the clear bowl
    K.lathe([(r * 0.62, -0.05), (r * 0.62, -L * 0.82), (0.0, -L * 0.82)], screen, 10, T((0, y, zt)))                           # the screen inside it
    for k in range(5):
        K.lathe([(r * 0.64, -0.06 - k * L * 0.15), (r * 0.64, -0.066 - k * L * 0.15)], brass, 10, T((0, y, zt)))               # its bands
    zb = zt - L
    K.lathe([(r * 0.3, 0.0), (r * 0.36, -0.012), (r * 0.36, -0.03), (r * 0.2, -0.04), (r * 0.2, -0.055)], brass, 8, T((0, y, zb)))      # the flush valve
    K.bx((0.05, 0.008, 0.012), (0.012, y - 0.016, zb - 0.02), red)
    return K.done('filter')


def uv():
    K = props.Kit()
    steel = mat('UvChamber', (0.74, 0.75, 0.77), 0.25)
    steel.node_tree.nodes['Principled BSDF'].inputs['Metallic'].default_value = 0.6
    clip = mat('UvClip', (0.2, 0.2, 0.22), 0.5)
    cap = mat('UvLampCap', (0.08, 0.08, 0.09), 0.6)
    white = mat('UvBallast', (0.93, 0.93, 0.91), 0.45)
    lamp = mat('UvStatus', (0.3, 0.5, 1.0), 0.3)
    brass = mat('FilterBrass', (0.8, 0.62, 0.25), 0.35)
    label = mat('UvLabel', (0.2, 0.35, 0.75), 0.6)
    L, r = 0.5, 0.045
    y = -0.07
    zc = 0.09
    K.lathe([(0.0, 0.0), (r * 0.9, 0.0), (r, 0.01), (r, L - 0.01), (r * 0.9, L), (0.0, L)], steel, 14, T((-L / 2, y, zc)) @ props.RX)
    K.lathe([(r * 1.005, L * 0.38), (r * 1.005, L * 0.62)], label, 14, T((-L / 2, y, zc)) @ props.RX)                           # the maker's band
    for s in (-1, 1):                                                                                                # the two wall clips, and a port near each end
        x = s * L * 0.3
        K.bx((0.03, -y - r * 0.2, 0.02), (x, (y + r * 0.2) / 2, zc), clip)
        K.lathe([(r + 0.004, -0.015), (r + 0.004, 0.015)], clip, 14, T((x, y, zc)) @ props.RX)
        K.bx((0.05, 0.004, 0.07), (x, -0.002, zc), clip)
        px = s * (L / 2 - 0.05)
        K.tube((px, y, zc), (px, y, zc - s * (r + 0.04)), 0.016, 0.016, steel, 8)                                       # in at the bottom of one end, out at the top of the other
        K.lathe([(0.021, 0.0), (0.021, 0.014)], brass, 6, T((px, y, zc - s * (r + 0.04) + (0.0 if s > 0 else -0.014))))
    K.lathe([(r * 0.75, 0.0), (r * 0.75, 0.04), (r * 0.5, 0.05), (0.0, 0.05)], cap, 12, T((L / 2, y, zc)) @ props.RX)            # the lamp's cap
    bz = zc + 0.17                                                                                                   # the ballast, above the chamber
    K.bx((0.16, 0.045, 0.09), (0.1, -0.0225, bz), white)
    K.bx((0.14, 0.004, 0.07), (0.1, -0.047, bz), mat('UvBallastFace', (0.82, 0.83, 0.85), 0.5))
    K.lathe([(0.008, 0.0), (0.008, 0.004), (0.0, 0.005)], lamp, 8, T((0.15, -0.049, bz + 0.015)) @ OUT)
    K.path([(L / 2 + 0.05, y, zc), (L / 2 + 0.08, y + 0.01, zc + 0.05), (L / 2 + 0.02, y + 0.03, bz - 0.02), (0.18, -0.03, bz - 0.02)], 0.005, cap, 5)       # the lamp lead
    return K.done('uv')


def reverse_osmosis():
    K = props.Kit()
    plate = mat('RoBracket', (0.93, 0.93, 0.91), 0.45)
    screws = mat('FilterScrew', (0.45, 0.46, 0.48), 0.4)
    head = mat('RoHead', (0.9, 0.9, 0.88), 0.4)
    white = mat('RoSump', (0.95, 0.95, 0.93), 0.35)
    blue = mat('RoSumpBlue', (0.12, 0.36, 0.78), 0.3)
    cap = mat('RoCap', (0.12, 0.3, 0.62), 0.4)
    gauge = mat('GaugeFace', (0.93, 0.93, 0.9), 0.4)
    dark = mat('RoDark', (0.1, 0.1, 0.12), 0.5)
    tubes = [mat('RoTubeBlue', (0.15, 0.4, 0.85), 0.5), mat('RoTubeRed', (0.8, 0.15, 0.12), 0.5), mat('RoTubeYellow', (0.9, 0.75, 0.1), 0.5)]
    W, r, L = 0.42, 0.045, 0.27
    y = -0.075
    H = L + 0.22
    bracket(K, W, 0.26, H - 0.26, plate, screws)
    K.bx((W, -y + r * 0.3, 0.012), (0, (y - r * 0.3) / 2, H - 0.2), plate)                      # the shelf the heads hang under
    zt = H - 0.21
    xs = (-W * 0.32, 0.0, W * 0.32)
    for k, x in enumerate(xs):                                                             # the three cartridge stages
        K.lathe([(r * 1.12, -0.012), (r * 1.12, 0.006)], head, 14, T((x, y, zt)))
        sump(K, x, y, zt - 0.01, r, L, white if k else blue)
    zm = H - 0.11                                                                           # the membrane housing lying across the top, a cap on each end
    K.lathe([(0.0, 0.0), (0.036, 0.0), (0.036, W * 0.86), (0.0, W * 0.86)], white, 12, T((-W * 0.43, y + 0.01, zm)) @ props.RX)
    for s in (-1, 1):
        K.lathe([(0.04, -0.012), (0.04, 0.012)], cap, 12, T((s * W * 0.43, y + 0.01, zm)) @ props.RX)
    zp = H - 0.035                                                                          # the post filter, above it
    K.lathe([(0.0, 0.0), (0.022, 0.0), (0.022, W * 0.5), (0.0, W * 0.5)], white, 10, T((-W * 0.25, y + 0.02, zp)) @ props.RX)
    for s in (-1, 1):
        K.lathe([(0.025, -0.008), (0.025, 0.008)], cap, 10, T((s * W * 0.25, y + 0.02, zp)) @ props.RX)
    for x, z in ((-W * 0.36, zm), (W * 0.36, zm), (0.0, zp)):                                 # clips holding the two to the bracket
        K.bx((0.02, -y, 0.014), (x, y / 2, z), plate)
    g = T((W * 0.36, y - 0.02, H - 0.17)) @ OUT                                             # a pressure gauge on the front
    K.lathe([(0.028, -0.01), (0.03, 0.0), (0.03, 0.008), (0.026, 0.01)], dark, 12, g)
    K.lathe([(0.026, 0.0105), (0.0, 0.0105)], gauge, 12, g)
    # the tubes: stage to stage along the front, up to the membrane, over to the post filter
    K.path([(xs[0] + r, y - r * 0.6, zt + 0.02), (xs[1] - r, y - r * 0.6, zt + 0.02)], 0.005, tubes[0], 5)
    K.path([(xs[1] + r, y - r * 0.6, zt + 0.02), (xs[2] - r, y - r * 0.6, zt + 0.02)], 0.005, tubes[0], 5)
    K.path([(xs[2], y - r * 0.5, zt + 0.006), (xs[2] + 0.02, y - 0.05, zt + 0.05), (W * 0.45, y - 0.02, zm)], 0.005, tubes[1], 5)
    K.path([(-W * 0.45, y - 0.02, zm), (-W * 0.47, y - 0.03, zm + 0.04), (-W * 0.27, y, zp)], 0.005, tubes[2], 5)
    K.path([(-W * 0.45, y - 0.01, zm), (-W * 0.5, y - 0.02, zt - 0.05), (-W * 0.5, y, 0.02)], 0.005, dark, 5)             # the drain line, down the side
    return K.done('ro')


# item: (builder, the description, what the model is)
FILTERS = {
    'water_filter': (cartridge, 'A cartridge sediment filter on a wall bracket: a first, coarse stage for a water line. Mount it on a wall and pipe the line through it.',
                     'A black head with two ports under a wall bracket, a ribbed blue sump.'),
    'water_filter_spin_down_sediment': (spin_down, 'A reusable spin-down sediment filter with a clear bowl and a flush valve. Mount it on a wall and pipe the line through it.',
                                        'A brass head on a wall plate, a clear bowl with the steel screen inside, a flush valve with a red handle.'),
    'water_sterilizer_uv_chamber': (uv, 'A UV steriliser: water runs through a stainless chamber past an ultraviolet lamp, the last stage for drinking water. Mount it on a wall '
                                        'and pipe the line through it.',
                                    'A stainless chamber along the wall in two clips, a port at each end, the lamp cap and its lead to a ballast box.'),
    'water_filter_reverse_osmosis': (reverse_osmosis, 'A multi-stage reverse osmosis drinking water system. Mount it on a wall and pipe the line through it.',
                                     'Three cartridge sumps under a white bracket, the membrane housing and a post filter across the top, a gauge and coloured tubes.'),
}
WATER_FIELDS = {'power_draw_w': 0, 'capacity_l': 0, 'max_flow_rate_lpm': 0, 'water_usage_lpm': 0, 'is_connected': False, 'max_filter_throughput_lpm': 0, 'max_roof_proximity_m': 0}


def main():
    for item, (build, desc, note) in FILTERS.items():
        folder = os.path.join(WATER, item)
        path = os.path.join(folder, item + '.json')
        if not os.path.exists(path):
            print('SKIP (not in the kit)', item)
            continue
        bpy.ops.wm.read_factory_settings(use_empty=True)
        obj = build()
        obj.name = item
        pts = [v.co for v in obj.data.vertices]
        lo = [min(p[i] for p in pts) for i in range(3)]
        hi = [max(p[i] for p in pts) for i in range(3)]
        obj.data.transform(T((-(lo[0] + hi[0]) / 2, -hi[1], -lo[2])))          # centred on x, the back on the wall (y = 0), the bottom at z = 0
        dims = [round(hi[i] - lo[i], 3) for i in range(3)]
        tris = sum(len(p.vertices) - 2 for p in obj.data.polygons)
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.export_scene.gltf(filepath=os.path.join(folder, item + '.glb'), export_format='GLB', use_selection=True, export_yup=True)
        m = json.load(open(path, encoding='utf-8'))
        if not m.get('description') or 'Standard water asset' in m['description'] or len(m['description']) < 60:
            m['description'] = desc
        p = m['properties']
        p.update({'placeable': False, 'attach_surface': 'wall', 'attach_side': 'either', 'footprint': '%.2fm W x %.2fm D x %.2fm H' % (dims[0], dims[1], dims[2])})
        m['models'] = [{'file': item + '.glb', 'format': 'glb', 'dimensions_m': {'x': dims[0], 'y': dims[2], 'z': dims[1]}, 'triangles': tris}]
        m.pop('dimensions', None)
        cf = {k: v for k, v in (m.get('category_fields') or {}).items() if k in WATER_FIELDS or k == 'dimensions_m'}      # (the steriliser came over from electricity with that category's fields)
        for k, v in WATER_FIELDS.items():
            cf.setdefault(k, v)
        cf['dimensions_m'] = {'width': round(dims[0], 2), 'depth': round(dims[1], 2), 'height': round(dims[2], 2)}
        m['category_fields'] = cf
        props.save(path, json.dumps(m, indent=2))
        props.save(os.path.join(folder, 'README.md'), '# %s\n\n%s\n\nProcedural model (tools/make_water_filters.py), %d triangles, %.2f x %.2f x %.2f m. %s Mounts on a wall, '
                   'either side; `wire_role: water_filter`. See docs/WELLS.md.\n' % (m['name'], m['description'], tris, *dims, note))
        print('filter', item, '|', tris, 'tris |', dims)


if __name__ == '__main__':
    main()
