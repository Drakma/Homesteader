"""
Builds the fuel pumps, the fuel cans and the firewood bundles as GLBs in headless Blender: free, local, low-poly (no Meshy).

    blender --background --python tools/make_fuel_props.py                 (all of them)
    blender --background --python tools/make_fuel_props.py -- fuel_pump_gas ...
    python tools/render_icon_from_model.py assets/fuel/<id>/<id>.glb assets/fuel/<id>/<id>.png

  fuel_pump_gas / fuel_pump_diesel                   a yard fuel pump on a concrete island: a painted cabinet with a louvred lower door, a head with
                                                     a name plate, a hose looped to a nozzle hung in its holster. No screens, no buttons. Red: gas, green: diesel.
  small_gas_fuel_container / large_gas_fuel_container        a slim red plastic fuel can, the spout to the left
  fuel_small_diesel_container / fuel_large_diesel_container  the same cans in green
  fuel_steel_drum_200l                               a blue 200 L steel drum: rolling hoops, chimes, a lid with two bungs, a hazard label
  fuel_firewood_bundle_<species>                     a split log tied tight with two strings (birch has its black marks): birch, maple, oak, pine, poplar, willow (the trees that
                                                     bear no fruit)

An item that is already in the kit keeps its name, price and the rest (only the model entry and the dimensions change). The firewood bundles
are new: their manifests are written from BUNDLES below.

Conventions: 1 unit = 1 m, pivot at the centre of the footprint, ground at z = 0.
"""
import json
import math
import os
import random
import sys

import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_simple_props as props  # noqa: E402    (Kit, mat, save, SPECIES, log_mats)

FUEL = os.path.join(props.ROOT, 'assets', 'fuel')
T = Matrix.Translation
mat = props.mat
props.SPECIES.setdefault('poplar', ((0.6, 0.61, 0.54), (0.92, 0.86, 0.68), (0.8, 0.7, 0.5), None))


# -------------------------------------------------------------------------------------------------------------------------------------- pumps

def pump(rgb):
    K = props.Kit()
    paint = mat('PumpPaint', rgb, 0.4)
    shade = mat('PumpPaintShade', tuple(c * 0.7 for c in rgb), 0.45)
    white = mat('PumpPanel', (0.92, 0.92, 0.9), 0.45)
    steel = mat('PumpTrim', (0.62, 0.63, 0.65), 0.35)
    dark = mat('PumpDark', (0.08, 0.08, 0.09), 0.7)
    concrete = mat('PumpIsland', (0.6, 0.59, 0.56), 0.95)
    w, d = 0.52, 0.36
    base = 0.12
    # the island, with a bevelled edge
    K.bx((0.9, 0.62, base * 0.6), (0, 0, base * 0.3), concrete)
    K.bx((0.82, 0.54, base * 0.4), (0, 0, base * 0.8), concrete)
    # the cabinet: a plinth, the lower door (white, louvred), a trim band, the painted upper body
    K.bx((w + 0.02, d + 0.02, 0.06), (0, 0, base + 0.03), dark)
    z0 = base + 0.06
    K.bx((w, d, 0.62), (0, 0, z0 + 0.31), white)
    for k in range(6):                                                    # louvres in the door
        K.bx((w * 0.6, 0.006, 0.014), (0, -d / 2 - 0.002, z0 + 0.12 + k * 0.035), dark, Matrix.Rotation(0.5, 4, 'X'))
    K.bx((w * 0.86, 0.004, 0.56), (0, -d / 2 - 0.001, z0 + 0.31), mat('PumpDoor', (0.86, 0.86, 0.84), 0.45))
    K.bx((0.016, 0.012, 0.07), (w * 0.36, -d / 2 - 0.008, z0 + 0.42), steel)             # the door handle
    K.lathe([(0.012, 0.0), (0.012, 0.004), (0.0, 0.004)], steel, 8, T((w * 0.36, -d / 2 - 0.003, z0 + 0.52)) @ Matrix.Rotation(math.pi / 2, 4, 'X'))      # its lock
    z1 = z0 + 0.62
    K.bx((w + 0.016, d + 0.016, 0.03), (0, 0, z1 + 0.015), steel)
    z2 = z1 + 0.03
    K.bx((w, d, 0.5), (0, 0, z2 + 0.25), paint)
    for s in (-1, 1):                                                     # pressed corner posts
        for t in (-1, 1):
            K.bx((0.03, 0.03, 1.12), (s * (w / 2 - 0.006), t * (d / 2 - 0.006), z0 + 0.56), shade)
    # the head: a name plate front and back (plain: a white plate with a colour stripe), under a stepped cap
    z3 = z2 + 0.5
    K.bx((w + 0.016, d + 0.016, 0.025), (0, 0, z3 + 0.0125), steel)
    K.bx((w + 0.04, d + 0.04, 0.2), (0, 0, z3 + 0.125), paint)
    for s in (-1, 1):
        K.bx((w * 0.8, 0.006, 0.13), (0, s * (d / 2 + 0.021), z3 + 0.125), white)
        K.bx((w * 0.8, 0.008, 0.03), (0, s * (d / 2 + 0.022), z3 + 0.085), shade)
    K.bx((w + 0.08, d + 0.08, 0.03), (0, 0, z3 + 0.24), steel)
    K.bx((w, d, 0.03), (0, 0, z3 + 0.27), paint)
    # a round emblem on the upper body, front and back
    for s in (-1, 1):
        mx = T((0, s * (d / 2 + 0.001), z2 + 0.27)) @ Matrix.Rotation(-s * math.pi / 2, 4, 'X')
        K.lathe([(0.11, 0.0), (0.11, 0.006), (0.095, 0.008), (0.0, 0.008)], white, 16, mx)
        K.lathe([(0.075, 0.0085), (0.06, 0.0085)], shade, 16, mx)
    # the nozzle side (+x): a holster, the nozzle hanging in it, the hose from low on the cabinet looping down and up
    hx = w / 2
    hz = z2 + 0.3
    K.bx((0.05, 0.11, 0.16), (hx + 0.025, 0, hz), dark)                                # the holster
    K.bx((0.07, 0.13, 0.02), (hx + 0.035, 0, hz - 0.08), steel)
    grip = Vector((hx + 0.1, 0, hz + 0.02))
    K.box((0.05, 0.05, 0.17), T(grip) @ Matrix.Rotation(-0.25, 4, 'Y'), paint)                 # the nozzle's body and guard
    K.box((0.012, 0.03, 0.13), T(grip + Vector((0.045, 0, -0.01))) @ Matrix.Rotation(-0.25, 4, 'Y'), steel)
    K.tube(grip + Vector((-0.02, 0, 0.08)), Vector((hx + 0.035, 0, hz + 0.19)), 0.014, 0.012, steel, 8, None, steel)      # the spout, tucked into the holster
    out = Vector((hx, 0.1, z0 + 0.5))
    K.lathe([(0.03, 0.0), (0.03, 0.02), (0.022, 0.03)], steel, 8, T(out) @ Matrix.Rotation(math.pi / 2, 4, 'Y'))
    pts = [out + Vector((0.02, 0, 0)), out + Vector((0.1, 0.01, -0.06)), Vector((hx + 0.17, 0.09, z0 + 0.12)), Vector((hx + 0.2, 0.03, base + 0.16)),
           Vector((hx + 0.21, -0.05, z0 + 0.2)), Vector((hx + 0.18, -0.03, hz - 0.3)), Vector((hx + 0.14, -0.005, hz - 0.12)), grip + Vector((0.02, 0, -0.085))]
    K.path(pts, 0.016, dark, 7)
    o = K.done('pump')
    o.data.transform(Matrix.Scale(-1, 4, (1, 0, 0)))        # mirrored: the hose and nozzle on the left (-x), the side the icon shows
    o.data.flip_normals()
    return o


# --------------------------------------------------------------------------------------------------------------------------------------- cans

def fuel_can(w, d, h, rgb):
    """A slim plastic fuel can: pressed side panels with a cross, a handle moulded over the top, the spout at the left (-x) end."""
    K = props.Kit()
    body = mat('FuelCan', rgb, 0.45)
    dark = mat('FuelCanPanel', tuple(c * 0.78 for c in rgb), 0.5)
    yellow = mat('Spout', (0.95, 0.78, 0.1), 0.5)
    black = mat('SpoutCap', (0.07, 0.07, 0.08), 0.6)
    c = min(w, h) * 0.08
    hb = h * 0.8
    side = [(w / 2 - c, 0.0), (-w / 2 + c, 0.0), (-w / 2, c), (-w / 2, hb - c * 2), (-w / 2 + c * 2.5, hb), (w / 2 - c, hb), (w / 2, hb - c), (w / 2, c)]
    K.prism(side[::-1], d, T((0, d / 2, 0)) @ Matrix.Rotation(math.pi / 2, 4, 'X'), body)
    for s in (-1, 1):                                                    # the pressed panels
        K.bx((w * 0.62, 0.005, hb * 0.5), (0, s * (d / 2 + 0.002), hb * 0.48), dark)
        K.bx((w * 0.5, 0.007, hb * 0.07), (0, s * (d / 2 + 0.003), hb * 0.48), body, Matrix.Rotation(0.6, 4, 'Y'))
        K.bx((w * 0.5, 0.007, hb * 0.07), (0, s * (d / 2 + 0.003), hb * 0.48), body, Matrix.Rotation(-0.6, 4, 'Y'))
    for z in (hb * 0.12, hb * 0.86):                                     # a rib round the can, low and high
        K.bx((w * 0.96, d + 0.006, hb * 0.03), (0, 0, z), dark)
    g = h * 0.045                                                        # the handle
    K.bx((g, d * 0.6, h - hb), (w * 0.32, 0, hb + (h - hb) / 2 - g / 2), body)
    K.bx((g, d * 0.6, (h - hb) * 0.7), (-w * 0.1, 0, hb + (h - hb) * 0.35), body)
    K.bx((w * 0.42 + g, d * 0.6, g), (w * 0.11, 0, h - g), body)
    p0 = Vector((-w / 2 + c * 1.6, 0, hb - c * 0.8))                     # the spout
    n = Vector((-0.75, 0, 0.66)).normalized()
    K.tube(p0 - n * 0.02, p0 + n * (h * 0.14), d * 0.26, d * 0.22, black, 10, None, black)
    K.tube(p0 + n * (h * 0.14), p0 + n * (h * 0.32), d * 0.15, d * 0.11, yellow, 10, None, black)
    K.lathe([(d * 0.14, 0.0), (d * 0.14, 0.012), (0.0, 0.012)], black, 8, T((w * 0.36, 0, hb)))       # the vent cap
    return K.done('can')


def drum():
    """A 200 L steel drum: two rolling hoops pressed into the wall, a rolled chime top and bottom, a recessed lid with the big and the small bung,
    a yellow hazard label and a stencilled band."""
    K = props.Kit()
    blue = mat('DrumPaint', (0.08, 0.2, 0.5), 0.4)
    shade = mat('DrumPaintShade', (0.06, 0.15, 0.4), 0.45)
    steel = mat('DrumChime', (0.6, 0.62, 0.65), 0.3)
    bung = mat('DrumBung', (0.75, 0.76, 0.78), 0.3)
    label = mat('DrumLabel', (0.95, 0.8, 0.12), 0.6)
    dark = mat('DrumLabelInk', (0.08, 0.08, 0.09), 0.6)
    r, h = 0.29, 0.88
    prof = [(0.0, 0.012), (r - 0.012, 0.012), (r - 0.006, 0.0), (r + 0.004, 0.0), (r + 0.006, 0.012), (r, 0.022)]
    for z in (h / 3, 2 * h / 3):                                         # the rolling hoops
        prof += [(r, z - 0.03), (r + 0.011, z - 0.012), (r + 0.011, z + 0.012), (r, z + 0.03)]
    prof += [(r, h - 0.022)]
    K.lathe(prof, blue, 24)
    K.lathe([(r, h - 0.022), (r + 0.006, h - 0.012), (r + 0.004, h), (r - 0.006, h), (r - 0.012, h - 0.016)], steel, 24)                 # the top chime
    K.lathe([(r - 0.012, h - 0.016), (r * 0.5, h - 0.02), (0.0, h - 0.018)], shade, 24)                                                 # the lid, set down inside it
    K.lathe([(r - 0.006, 0.0005), (r + 0.004, 0.0005), (r + 0.006, 0.012)], steel, 24)                                                  # the bottom chime
    for x, rb in ((r * 0.6, 0.038), (-r * 0.6, 0.02)):                   # the 2 inch and the 3/4 inch bung
        mx = T((x, 0.0, h - 0.02))
        K.lathe([(rb * 1.35, 0.0), (rb * 1.35, 0.006), (rb, 0.008), (rb, 0.016), (0.0, 0.016)], bung, 8, mx)
        K.bx((rb * 1.1, rb * 0.3, 0.004), (x, 0.0, h - 0.002), steel)
    for z in (h / 6, h / 2, 5 * h / 6):                                  # a seam down the side
        K.bx((0.003, 0.012, h / 3 - 0.08), (-r - 0.0005, 0.0, z), shade)
    for k in range(7):                                                   # the hazard label: a curved yellow panel with a black diamond
        a = math.radians(-102 + k * 4)
        K.box((0.002, 2 * (r + 0.001) * math.sin(math.radians(2)) * 1.04, 0.2), Matrix.Rotation(a, 4, 'Z') @ T((r + 0.0012, 0.0, h * 0.5)), label)
    K.box((0.002, 0.075, 0.075), Matrix.Rotation(math.radians(-90), 4, 'Z') @ T((r + 0.0026, 0.0, h * 0.52)) @ Matrix.Rotation(math.pi / 4, 4, 'X'), dark)
    K.lathe([(r + 0.0008, h * 0.86), (r + 0.0008, h * 0.9)], mat('DrumBand', (0.92, 0.92, 0.9), 0.5), 24)                               # a white band under the top chime
    return K.done('drum')


# ------------------------------------------------------------------------------------------------------------------------------------ firewood

def bundle(species, seed):
    """A log split into six and tied back together tight with two strings and a carrying loop: bark outside, the splits showing on the ends.
    Birch gets its black marks."""
    K, rnd = props.Kit(), random.Random(seed)
    bark, wood, heart, marks = props.log_mats(species)
    twine = mat('Twine', (0.82, 0.68, 0.42), 0.9)
    r, L, gap = 0.125, 0.4, 0.003
    third = math.pi / 3
    pts = [(0.0, 0.0)] + [(r * math.cos(third * k / 4), r * math.sin(third * k / 4)) for k in range(5)]
    sides = [wood] + [bark] * 4 + [wood]
    along_x = Matrix(((0, 0, 1, 0), (1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 0, 1)))
    zc = r + gap
    for k in range(6):
        ln = L * rnd.uniform(0.94, 1.0)
        x0 = rnd.uniform(-0.008, 0.008) - ln / 2
        roll = third * k + 0.2
        K.prism(pts, ln, T((x0, 0, zc)) @ Matrix.Rotation(roll, 4, 'X') @ T((0, gap * math.cos(third / 2), gap * math.sin(third / 2))) @ along_x,
                heart if k % 3 == 0 else wood, sides)
        if marks:                                                        # the dark dashes across birch bark
            for _ in range(5):
                a = roll + rnd.uniform(0.12, third - 0.12)
                K.box((rnd.uniform(0.006, 0.012), 0.003, rnd.uniform(0.02, 0.045)),
                      T((x0 + ln * rnd.uniform(0.08, 0.92), 0, zc)) @ Matrix.Rotation(a, 4, 'X') @ T((0, r + gap - 0.0005, 0)), marks)
    ring = r + gap + 0.003
    for x in (-L * 0.26, L * 0.26):
        K.lathe([(ring + 0.004 * math.cos(a), 0.004 * math.sin(a)) for a in [math.pi / 2 * k for k in range(4)]], twine, 16, T((x, 0, zc)) @ props.RX, closed=True)
    K.path([(-L * 0.26, 0, zc + ring), (-L * 0.12, 0, zc + ring + 0.04), (L * 0.12, 0, zc + ring + 0.04), (L * 0.26, 0, zc + ring)], 0.004, twine, 5)       # the carrying loop
    o = K.done('bundle')
    o.data.transform(T((0, 0, -min(v.co.z for v in o.data.vertices))))
    return o


# species: (kg, price, burn minutes)
BUNDLES = {'birch': (15.0, 8, 5400), 'maple': (17.0, 10, 6000), 'oak': (18.0, 10, 6300), 'pine': (13.0, 7, 4200), 'poplar': (12.0, 6, 3900), 'willow': (12.0, 6, 4000)}
RED, GREEN = (0.78, 0.08, 0.06), (0.1, 0.42, 0.16)
ITEMS = {
    'fuel_pump_gas': (lambda: pump((0.74, 0.08, 0.06)), 'A red yard pump on a concrete island: louvred door, name plate, hose and nozzle.'),
    'fuel_pump_diesel': (lambda: pump((0.1, 0.4, 0.16)), 'A green yard pump on a concrete island: louvred door, name plate, hose and nozzle.'),
    'small_gas_fuel_container': (lambda: fuel_can(0.26, 0.11, 0.33, RED), 'A slim red plastic fuel can, the spout at the left.'),
    'large_gas_fuel_container': (lambda: fuel_can(0.36, 0.15, 0.46, RED), 'A slim red plastic fuel can, the spout at the left.'),
    'fuel_small_diesel_container': (lambda: fuel_can(0.26, 0.11, 0.33, GREEN), 'The small fuel can in green.'),
    'fuel_large_diesel_container': (lambda: fuel_can(0.36, 0.15, 0.46, GREEN), 'The large fuel can in green.'),
}
ITEMS['fuel_steel_drum_200l'] = (drum, 'A blue 200 L steel drum: rolling hoops, chimes, a recessed lid with two bungs, a hazard label.')
for _n, _s in enumerate(BUNDLES):
    ITEMS['fuel_firewood_bundle_' + _s] = ((lambda s=_s, n=_n: bundle(s, n + 3)), 'A log split in six and tied back together tight with two strings and a carrying loop.')


def new_bundle_manifest(item):
    species = item.rsplit('_', 1)[1]
    kg, price, burn = BUNDLES[species]
    src = None
    for cand in ('fuel_firewood_bundle_tied', 'fuel_firewood_bundle_birch'):
        p = os.path.join(FUEL, cand, cand + '.json')
        if os.path.exists(p):
            src = json.load(open(p, encoding='utf-8'))
            break
    m = json.loads(json.dumps(src))
    m.update({'id': item, 'icon': item + '.png', 'name': '%s Firewood Bundle' % species.capitalize(),
              'description': 'A tied bundle of split %s firewood.' % species})
    m['properties'].update({'weight_kg': kg, 'base_value': price, 'max_stack_size': 10, 'placeable': True})
    m['category_fields'] = dict(m.get('category_fields') or {}, fuel_type='wood', burn_minutes_per_item=burn)
    return m


def main():
    only = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    for item, (build, note) in ITEMS.items():
        if only and item not in only:
            continue
        bpy.ops.wm.read_factory_settings(use_empty=True)
        obj = build()
        folder = os.path.join(FUEL, item)
        path = os.path.join(folder, item + '.json')
        if os.path.exists(path):
            m = json.load(open(path, encoding='utf-8'))
        elif item.startswith('fuel_firewood_bundle_'):
            m = new_bundle_manifest(item)
        else:
            print('SKIP (not in the kit)', item)
            continue
        os.makedirs(folder, exist_ok=True)
        pts = [v.co for v in obj.data.vertices]
        dims = [round(max(p[i] for p in pts) - min(p[i] for p in pts), 3) for i in range(3)]
        tris = sum(len(p.vertices) - 2 for p in obj.data.polygons)
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.export_scene.gltf(filepath=os.path.join(folder, item + '.glb'), export_format='GLB', use_selection=True, export_yup=True)
        m['models'] = [{'file': item + '.glb', 'format': 'glb', 'dimensions_m': {'x': dims[0], 'y': dims[2], 'z': dims[1]}, 'triangles': tris}]
        m['category_fields'] = dict(m.get('category_fields') or {}, dimensions_m={'width': round(dims[0], 2), 'depth': round(dims[1], 2), 'height': round(dims[2], 2)})
        props.save(path, json.dumps(m, indent=2))
        props.save(os.path.join(folder, 'README.md'), '# %s\n\n%s\n\nProcedural model (tools/make_fuel_props.py), %d triangles, %.2f x %.2f x %.2f m. %s\n'
                   % (m['name'], m.get('description', ''), tris, *dims, note))
        print('fuel', item, '|', m['name'], '|', tris, 'tris |', dims)


if __name__ == '__main__':
    main()
