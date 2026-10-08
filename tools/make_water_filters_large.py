"""
Builds two LARGE water treatment units as GLBs in headless Blender (free, local, low-poly, no Meshy), and writes their manifests:

    blender --background --python tools/make_water_filters_large.py
    python tools/render_icon_from_model.py assets/water/<id>/<id>.glb assets/water/<id>/<id>.png
Afterwards: python tools/generate_unity_asset_catalog.py ; python tools/package_catalog_as_mods.py

  water_filter_reverse_osmosis_whole_house   a floor-standing whole-house reverse osmosis skid: a steel frame, a booster pump, three pre-filter sumps, two membrane housings, a gauge and the
                                             coloured tubes between them. About 3,000 gallons a day of clean water (470 L/h) and it wastes half of what it takes in (recovery 50 %).
  water_filter_spin_down_sediment_large      a 2 inch spin-down sediment filter on a steel stand: a big clear bowl under a brass head with two 2 inch ports, a flush valve. 9,000 L/h.

Both stand on the floor (placeable, wire_role water_filter) and are piped into a water line like the wall filters (docs/WELLS.md, docs/WATER_FLOW.md).
Convention: centred on x and y, the bottom at z = 0, the front facing -y.
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

ITEMS = {
    'water_filter_reverse_osmosis_whole_house': dict(
        base='water_filter_reverse_osmosis', name='Whole-House Reverse Osmosis System', kg=55.0, price=2400.0, flow=470, recovery=50, stage='carbon',
        desc='A floor-standing whole-house reverse osmosis system: a booster pump, three pre-filters and two membrane housings on a steel frame. It makes about 3,000 gallons (11,000 L) of clean water a day, '
             'and rejects about a liter to the drain for every liter it makes. Pipe the line through it.'),
    'water_filter_spin_down_sediment_large': dict(
        base='water_filter_spin_down_sediment', name='Large Spin-Down Sediment Filter', kg=9.0, price=180.0, flow=9000, recovery=None, stage='sediment',
        desc='A 2 inch spin-down sediment filter on a steel stand: a big clear bowl, a brass head and a flush valve. It takes the sand and grit out of a well line at pump flow rates. Pipe the line through it.'),
}


def ro_whole_house():
    K = props.Kit()
    steel = mat('SkidSteel', (0.35, 0.37, 0.4), 0.45)
    dark = mat('SkidPlate', (0.16, 0.17, 0.19), 0.5)
    white = mat('MembraneHousing', (0.92, 0.93, 0.95), 0.3)
    blue = mat('PreFilterSump', (0.12, 0.36, 0.78), 0.3)
    cap = mat('EndCap', (0.1, 0.1, 0.12), 0.5)
    motor = mat('PumpMotor', (0.12, 0.28, 0.6), 0.4)
    brass = mat('SkidBrass', (0.8, 0.62, 0.25), 0.35)
    red = mat('FeedTube', (0.75, 0.12, 0.1), 0.5)
    clear = mat('ProductTube', (0.7, 0.85, 0.95), 0.2)
    W, D, H = 0.72, 0.38, 1.18
    K.bx((W, D, 0.04), (0, 0, 0.02), dark)                                              # the base plate
    for sx in (-1, 1):
        for sy in (-1, 1):
            K.bx((0.04, 0.04, H - 0.04), (sx * (W / 2 - 0.03), sy * (D / 2 - 0.03), 0.04 + (H - 0.04) / 2), steel)   # the four posts
    for z in (0.5, H - 0.02):
        for sy in (-1, 1):
            K.bx((W - 0.04, 0.03, 0.03), (0, sy * (D / 2 - 0.03), z), steel)             # the rails, front and back
    K.bx((W - 0.04, 0.12, 0.04), (0, 0, 0.74), dark)                                     # the head plate the sumps hang from
    for k, x in enumerate((-0.25, -0.1, 0.05)):                                           # three pre-filter sumps
        prof = [(0.062, 0.0), (0.062, -0.38), (0.055, -0.43), (0.03, -0.44), (0.0, -0.44)]
        K.lathe(prof, blue, 12, T((x, -0.02, 0.74)))
        K.lathe([(0.04, 0.0), (0.04, 0.03), (0.0, 0.03)], cap, 10, T((x, -0.02, 0.74)))
    for k, x in enumerate((0.22, 0.34)):                                                   # two membrane housings standing on the base
        K.lathe([(0.052, 0.04), (0.052, 1.02), (0.0, 1.02)], white, 12, T((x, 0.04, 0.0)))
        K.lathe([(0.056, 0.04), (0.056, 0.1), (0.0, 0.1)], cap, 10, T((x, 0.04, 0.0)))
        K.lathe([(0.056, 0.96), (0.056, 1.02), (0.0, 1.02)], cap, 10, T((x, 0.04, 0.0)))
    K.lathe([(0.07, 0.0), (0.07, 0.3), (0.0, 0.3)], motor, 12, T((-0.2, 0.05, 0.04)) @ props.RX)   # the booster pump's motor, lying down
    K.lathe([(0.085, 0.0), (0.085, 0.09), (0.0, 0.09)], brass, 12, T((-0.2, 0.05 + 0.3, 0.04)) @ props.RX)   # and its head
    K.lathe([(0.045, 0.0), (0.045, 0.016), (0.0, 0.016)], steel, 14, T((0.0, -0.2, 0.96)) @ props.RX)       # the gauge on the front rail
    K.tube((-0.25, -0.02, 0.3), (-0.25, -0.02, 0.74), 0.012, 0.012, red, 6)               # the feed tube up to the sumps
    K.tube((0.05, -0.02, 0.74), (0.22, 0.04, 0.9), 0.012, 0.012, clear, 6)                # the product tube across to the membranes
    K.tube((0.22, 0.04, 0.1), (0.34, 0.04, 0.1), 0.012, 0.012, clear, 6)
    return K.done('filter')


def spin_down_large():
    K = props.Kit()
    steel = mat('StandSteel', (0.35, 0.37, 0.4), 0.45)
    brass = mat('FilterBrass', (0.8, 0.62, 0.25), 0.35)
    bowl = mat('ClearBowl', (0.78, 0.88, 0.93), 0.12)
    screen = mat('SteelScreen', (0.55, 0.57, 0.6), 0.35)
    red = mat('FlushHandle', (0.8, 0.12, 0.1), 0.5)
    blue = mat('BowlCollar', (0.12, 0.36, 0.78), 0.35)
    r, L = 0.09, 0.42
    zt = 0.7
    for k in range(3):                                                                    # a steel stand: three legs and a ring
        a = k * 2 * math.pi / 3
        K.tube((math.cos(a) * 0.13, math.sin(a) * 0.13, 0.0), (math.cos(a) * 0.1, math.sin(a) * 0.1, zt - L + 0.12), 0.012, 0.012, steel, 6)
    K.lathe([(0.13, 0.0), (0.13, 0.012), (0.0, 0.012)], steel, 14, T((0, 0, zt - L + 0.1)))
    K.lathe([(r * 1.1, -0.03), (r * 1.15, 0.0), (r * 1.15, 0.06), (r * 0.7, 0.09), (0.0, 0.09)], brass, 14, T((0, 0, zt)))          # the head
    for s in (-1, 1):
        K.tube((s * r, 0, zt + 0.03), (s * (r + 0.1), 0, zt + 0.03), 0.035, 0.035, brass, 10, None, brass)                          # the two 2 inch ports
        K.lathe([(0.045, 0.0), (0.045, 0.02)], brass, 8, T((s * (r + 0.04), 0, zt + 0.03)) @ props.RX)
    K.lathe([(r * 1.16, -0.03), (r * 1.16, -0.07)], blue, 14, T((0, 0, zt)))                                                      # the collar
    K.lathe([(r, -0.07), (r, -L * 0.88), (r * 0.7, -L * 0.97), (r * 0.3, -L)], bowl, 14, T((0, 0, zt)))                           # the clear bowl
    K.lathe([(r * 0.62, -0.08), (r * 0.62, -L * 0.84), (0.0, -L * 0.84)], screen, 10, T((0, 0, zt)))                              # the screen inside
    for k in range(5):
        K.lathe([(r * 0.64, -0.1 - k * L * 0.15), (r * 0.64, -0.106 - k * L * 0.15)], brass, 10, T((0, 0, zt)))
    zb = zt - L
    K.lathe([(r * 0.3, 0.0), (r * 0.36, -0.014), (r * 0.36, -0.034), (r * 0.2, -0.046), (r * 0.2, -0.062)], brass, 8, T((0, 0, zb)))   # the flush valve
    K.bx((0.06, 0.01, 0.014), (0.016, -0.02, zb - 0.026), red)
    return K.done('filter')


BUILD = {'water_filter_reverse_osmosis_whole_house': ro_whole_house, 'water_filter_spin_down_sediment_large': spin_down_large}


def main():
    for item, d in ITEMS.items():
        folder = os.path.join(WATER, item)
        os.makedirs(folder, exist_ok=True)
        bpy.ops.wm.read_factory_settings(use_empty=True)
        obj = BUILD[item]()
        obj.name = item
        pts = [v.co for v in obj.data.vertices]
        lo = [min(p[i] for p in pts) for i in range(3)]
        hi = [max(p[i] for p in pts) for i in range(3)]
        obj.data.transform(T((-(lo[0] + hi[0]) / 2, -(lo[1] + hi[1]) / 2, -lo[2])))     # centred on x and y, the bottom at z = 0
        dims = [round(hi[i] - lo[i], 3) for i in range(3)]
        tris = sum(len(p.vertices) - 2 for p in obj.data.polygons)
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.export_scene.gltf(filepath=os.path.join(folder, item + '.glb'), export_format='GLB', use_selection=True, export_yup=True)
        base = json.load(open(os.path.join(WATER, d['base'], d['base'] + '.json'), encoding='utf-8'))
        m = json.loads(json.dumps(base))
        m['id'], m['name'], m['description'], m['icon'] = item, d['name'], d['desc'], item + '.png'
        p = m['properties']
        p.update({'weight_kg': d['kg'], 'base_value': d['price'], 'max_stack_size': 1, 'placeable': True, 'footprint': '%.2fm W x %.2fm D x %.2fm H' % (dims[0], dims[1], dims[2]),
                  'flow_lph': d['flow'], 'filter_stage': d['stage'], 'wire_role': 'water_filter', 'is_buyable': True, 'stores': ['voltvision'], 'sale_unit': 'ea', 'store_category': 'Water Treatment'})
        for k in ('attach_surface', 'attach_side'):
            p.pop(k, None)
        if d['recovery']:
            p['filter_recovery_pct'] = d['recovery']
        else:
            p.pop('filter_recovery_pct', None)
        m['models'] = [{'file': item + '.glb', 'format': 'glb', 'dimensions_m': {'x': dims[0], 'y': dims[2], 'z': dims[1]}, 'triangles': tris}]
        cf = m['category_fields']
        cf['dimensions_m'] = {'width': round(dims[0], 2), 'depth': round(dims[1], 2), 'height': round(dims[2], 2)}
        cf['max_flow_rate_lpm'] = round(d['flow'] / 60.0, 1)
        cf['max_filter_throughput_lpm'] = round(d['flow'] / 60.0, 1)
        props.save(os.path.join(folder, item + '.json'), json.dumps(m, indent=2))
        props.save(os.path.join(folder, 'README.md'), '# %s\n\n%s\n\nProcedural model (tools/make_water_filters_large.py), %d triangles, %.2f x %.2f x %.2f m. Stands on the floor; '
                   '`wire_role: water_filter`, %d L/h%s. See docs/WATER_FLOW.md.\n' % (d['name'], d['desc'], tris, dims[0], dims[1], dims[2], d['flow'],
                                                                                      ', recovery %d %%' % d['recovery'] if d['recovery'] else ''))
        print('built', item, '|', tris, 'tris |', dims)


if __name__ == '__main__':
    main()
