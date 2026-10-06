"""
Builds the Romex (NM cable) items as GLBs in headless Blender: free, local, low-poly. Three gauges, two sizes each, all lying on their side:

    blender --background --python tools/make_romex.py

  small   a 15 m coil: the cable wound in a flat ring (every wrap shows), four ties round it and a paper label band
  large   a 75 m spool: two plywood flanges with a hub and bolts, the cable wound between them (every wrap shows), a label on the top flange,
          the loose end of the cable

It writes assets/building/<id>/<id>.glb, the manifest (an existing one keeps its name, price and the rest; only the model entry and the dimensions
change, and `romex_m`, the length) and the README. The icons are rendered afterwards with tools/render_icon_from_model.py. The equivalencies
(~romex_14_2, ~romex_12_2, ~romex_10_3, counted in metres: unit "m") are saved through the kit, see ROMEX below for the members.

Conventions: 1 unit = 1 m, pivot at the centre of the footprint, ground at z = 0.
"""
import json
import math
import os

import bmesh
import bpy
from mathutils import Matrix, Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(ROOT, 'assets', 'building')
SEG = 20

SMALL_M, LARGE_M = 15, 75

# gauge: (label, jacket colour, cable width, what it is for, {size: (id, weight kg, price, stack)})
ROMEX = {
    '14_2': ('Romex 14-2', (0.93, 0.93, 0.9), 0.010, 'lighting circuits', {
        'small': ('building_romex_14_2_spool_small', 2.0, 16, 10),
        'large': ('building_romex_14_2_spool', 9.0, 70, 4)}),
    '12_2': ('Romex 12-2', (0.95, 0.8, 0.12), 0.011, 'outlet circuits', {
        'small': ('item_spool_romex_12_2', 3.0, 14, 10),
        'large': ('spool_wire_romex_12_2', 15.0, 60, 3)}),
    '10_3': ('Romex 10-3', (0.92, 0.45, 0.1), 0.014, 'heavy circuits (dryers, ranges, water heaters)', {
        'small': ('building_romex_10_3_spool_small', 3.5, 28, 10),
        'large': ('building_romex_10_3_spool', 16.0, 130, 4)}),
}


def material(name, rgb, rough=0.7):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*rgb, 1.0)
    b.inputs['Roughness'].default_value = rough
    return m


class Mesh:
    def __init__(self):
        self.bm = bmesh.new()
        self.mats = []

    def mi(self, m):
        if m not in self.mats:
            self.mats.append(m)
        return self.mats.index(m)

    def lathe(self, profile, m, closed=True):
        """Turns a profile [(r, z), ...] round the vertical axis. `closed`: the last point joins the first (a ring's cross-section)."""
        i = self.mi(m)
        rings = [[self.bm.verts.new((r * math.cos(2 * math.pi * k / SEG), r * math.sin(2 * math.pi * k / SEG), z)) for k in range(SEG)] for r, z in profile]
        n = len(rings)
        for a in range(n if closed else n - 1):
            b = (a + 1) % n
            for k in range(SEG):
                j = (k + 1) % SEG
                f = self.bm.faces.new((rings[a][k], rings[a][j], rings[b][j], rings[b][k]))
                f.material_index = i

    def box(self, size, matrix, m):
        i = self.mi(m)
        r = bmesh.ops.create_cube(self.bm, size=1.0)
        for v in r['verts']:
            v.co = matrix @ Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
        for f in set(f for v in r['verts'] for f in v.link_faces):
            f.material_index = i

    def radial_box(self, angle, r0, r1, width, z0, z1, m):
        """A box lying along a radius: from r0 to r1, `width` across, z0 to z1."""
        mat = Matrix.Rotation(angle, 4, 'Z') @ Matrix.Translation(((r0 + r1) / 2, 0.0, (z0 + z1) / 2))
        self.box((r1 - r0, width, z1 - z0), mat, m)

    def cylinder(self, r, z0, z1, m, sides=8, at=(0.0, 0.0)):
        i = self.mi(m)
        lo = [self.bm.verts.new((at[0] + r * math.cos(2 * math.pi * k / sides), at[1] + r * math.sin(2 * math.pi * k / sides), z0)) for k in range(sides)]
        hi = [self.bm.verts.new((v.co.x, v.co.y, z1)) for v in lo]
        for k in range(sides):
            j = (k + 1) % sides
            self.bm.faces.new((lo[k], lo[j], hi[j], hi[k])).material_index = i
        self.bm.faces.new(hi).material_index = i

    def finish(self, name):
        bmesh.ops.recalc_face_normals(self.bm, faces=self.bm.faces[:])
        me = bpy.data.meshes.new(name)
        self.bm.to_mesh(me)
        self.bm.free()
        for m in self.mats:
            me.materials.append(m)
        o = bpy.data.objects.new(name, me)
        bpy.context.collection.objects.link(o)
        return o


def wraps(r, z0, z1, pitch, depth, outward=True):
    """A zigzag up a side of the winding: one ridge per wrap of cable (the points of a lathe profile, from z0 to z1)."""
    n = max(2, round(abs(z1 - z0) / pitch))
    pts = []
    for k in range(n):
        za = z0 + (z1 - z0) * k / n
        zb = z0 + (z1 - z0) * (k + 1) / n
        pts.append((r, za + (zb - za) * 0.15))
        pts.append((r, za + (zb - za) * 0.85))
        if k < n - 1:
            pts.append((r - depth if outward else r + depth, zb))
    return pts


def rows(z, r0, r1, pitch, depth):
    """The same across the top of the winding, from r0 to r1: one ridge per row of cable."""
    n = max(2, round(abs(r1 - r0) / pitch))
    pts = []
    for k in range(n):
        ra = r0 + (r1 - r0) * k / n
        rb = r0 + (r1 - r0) * (k + 1) / n
        pts.append((ra + (rb - ra) * 0.15, z))
        pts.append((ra + (rb - ra) * 0.85, z))
        if k < n - 1:
            pts.append((rb, z - depth))
    return pts


def coil(name, jacket, cable):
    """The small one: a flat ring of cable lying on the ground, tied in four places, with a label band."""
    M = Mesh()
    wire = material('RomexJacket', jacket, 0.55)
    tie = material('Tie', (0.1, 0.1, 0.11), 0.6)
    paper = material('Label', (0.96, 0.95, 0.9), 0.85)
    ink = material('LabelInk', tuple(c * 0.55 for c in jacket) if sum(jacket) < 2.4 else (0.15, 0.2, 0.4), 0.8)
    copper = material('Copper', (0.78, 0.45, 0.2), 0.35)
    rin, rout = cable * 7.5, cable * 7.5 + cable * 6.2
    h = cable * 0.62 * 7                                    # seven wraps of flat cable high
    d = cable * 0.22
    prof = [(rin, 0.0), (rout, 0.0)] + wraps(rout, 0.0, h, cable * 0.62, d) + rows(h, rout, rin, cable, d)[::1] + wraps(rin, h, 0.0, cable * 0.62, d, outward=False)
    M.lathe(prof, wire)
    for k in range(4):                                       # the ties
        a = math.pi / 4 + k * math.pi / 2
        M.radial_box(a, rin - 0.003, rout + 0.003, 0.012, -0.0005, h + 0.003, tie)
    M.radial_box(0.0, rin - 0.004, rout + 0.004, rout * 0.62, -0.0005, h + 0.004, paper)      # the label band
    M.radial_box(0.0, rin + (rout - rin) * 0.2, rout - (rout - rin) * 0.2, rout * 0.4, h + 0.004, h + 0.0055, ink)
    # the loose end: a short length leaving the ring along a tangent, bare copper at its tip
    a = math.radians(200)
    t = Matrix.Rotation(a, 4, 'Z') @ Matrix.Translation((rout - cable * 0.5, -0.05, h - cable * 0.5))
    M.box((cable, 0.1, cable * 0.55), t, wire)
    t2 = Matrix.Rotation(a, 4, 'Z') @ Matrix.Translation((rout - cable * 0.5, -0.108, h - cable * 0.5))
    M.box((cable * 0.5, 0.016, cable * 0.2), t2, copper)
    return M.finish(name)


def spool(name, jacket, cable):
    """The large one: a plywood spool lying on its side, wound full."""
    M = Mesh()
    wire = material('RomexJacket', jacket, 0.55)
    ply = material('SpoolPlywood', (0.72, 0.56, 0.36), 0.85)
    edge = material('SpoolEdge', (0.5, 0.38, 0.24), 0.9)
    hub = material('SpoolHub', (0.2, 0.2, 0.22), 0.6)
    steel = material('Bolt', (0.6, 0.62, 0.65), 0.4)
    paper = material('Label', (0.96, 0.95, 0.9), 0.85)
    ink = material('LabelInk', tuple(c * 0.55 for c in jacket) if sum(jacket) < 2.4 else (0.15, 0.2, 0.4), 0.8)
    copper = material('Copper', (0.78, 0.45, 0.2), 0.35)
    R = cable * 20                                          # flange radius
    t = 0.016                                               # flange thickness
    H = cable * 0.62 * 22 + 2 * t                           # 22 wraps between the flanges
    hole = R * 0.16
    core = R * 0.42
    rw = R * 0.88                                           # the winding nearly fills the spool
    d = cable * 0.22
    for z0 in (0.0, H - t):                                 # the flanges, with the arbor hole
        M.lathe([(hole, z0), (R, z0), (R, z0 + t), (hole, z0 + t)], ply)
        M.lathe([(R - 0.0005, z0 + t * 0.3), (R + 0.0015, z0 + t * 0.3), (R + 0.0015, z0 + t * 0.7), (R - 0.0005, z0 + t * 0.7)], edge)      # the ply line round the rim
    M.lathe([(hole, t), (hole, H - t)], hub, closed=False)                 # the arbor tube
    M.lathe([(core, t)] + wraps(rw, t, H - t, cable * 0.62, d) + [(core, H - t)], wire, closed=False)
    # the top flange: a hub plate, four bolts and a label
    M.lathe([(hole, H), (hole * 2.1, H), (hole * 2.1, H + 0.004), (hole, H + 0.004)], hub)
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        M.cylinder(0.007, H, H + 0.007, steel, sides=6, at=(R * 0.62 * math.cos(a), R * 0.62 * math.sin(a)))
    M.radial_box(-math.pi / 2, R * 0.42, R * 0.9, R * 0.62, H, H + 0.0015, paper)
    M.radial_box(-math.pi / 2, R * 0.52, R * 0.72, R * 0.5, H + 0.0015, H + 0.003, ink)
    # the loose end: out of the winding along a tangent, bare copper at its tip
    a = math.radians(140)
    zc = t + (H - 2 * t) * 0.5
    m1 = Matrix.Rotation(a, 4, 'Z') @ Matrix.Translation((rw - cable * 0.3, -0.07, zc))
    M.box((cable * 0.55, 0.14, cable), m1, wire)
    m2 = Matrix.Rotation(a, 4, 'Z') @ Matrix.Translation((rw - cable * 0.3, -0.15, zc))
    M.box((cable * 0.2, 0.02, cable * 0.5), m2, copper)
    return M.finish(name)


def write(item, obj, label, gauge, size, length, use, weight, price, stack):
    me = obj.data
    pts = [v.co for v in me.vertices]
    lo = [min(p[i] for p in pts) for i in range(3)]
    hi = [max(p[i] for p in pts) for i in range(3)]
    me.transform(Matrix.Translation((-(lo[0] + hi[0]) / 2, -(lo[1] + hi[1]) / 2, -lo[2])))
    dims = [hi[i] - lo[i] for i in range(3)]
    tris = sum(len(p.vertices) - 2 for p in me.polygons)
    folder = os.path.join(BUILD, item)
    os.makedirs(folder, exist_ok=True)
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.gltf(filepath=os.path.join(folder, item + '.glb'), export_format='GLB', use_selection=True, export_yup=True)

    kind = 'Coil' if size == 'small' else 'Spool'
    name = '%s %s' % (label, kind)                      # (no length in the name: the kit shows it from romex_m)
    desc = ('A %d m coil of %s NM cable for %s.' if size == 'small' else 'A %d m spool of %s NM cable for %s.') % (length, label.split(' ')[1], use)
    manifest = os.path.join(folder, item + '.json')
    if os.path.exists(manifest):
        m = json.load(open(manifest, encoding='utf-8'))
    else:
        m = json.load(open(os.path.join(BUILD, 'building_romex_14_2_spool', 'building_romex_14_2_spool.json'), encoding='utf-8'))
        m['id'] = item
        m['icon'] = item + '.png'
    m['name'] = name
    m['description'] = desc
    m['properties'].update({'weight_kg': weight, 'base_value': price, 'max_stack_size': stack})
    m['models'] = [{'file': item + '.glb', 'format': 'glb', 'dimensions_m': {'x': round(dims[0], 3), 'y': round(dims[2], 3), 'z': round(dims[1], 3)}, 'triangles': tris}]
    m.pop('dimensions', None)
    m['category_fields'] = dict(m.get('category_fields') or {}, dimensions_m={'width': round(dims[0], 2), 'depth': round(dims[1], 2), 'height': round(dims[2], 2)})
    with open(manifest, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(m, f, indent=2)
    with open(os.path.join(folder, 'README.md'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('# %s\n\n%s\n\nProcedural model (tools/make_romex.py), lying on its side, %d triangles. Counts as %d m in the `~romex_%s` equivalency.\n'
                % (name, desc, tris, length, gauge))
    print('romex', item, '|', name, '|', tris, 'tris', '%.3f %.3f %.3f' % tuple(dims))


def main():
    for gauge, (label, jacket, cable, use, sizes) in ROMEX.items():
        for size, (item, weight, price, stack) in sizes.items():
            bpy.ops.wm.read_factory_settings(use_empty=True)
            obj = coil(item, jacket, cable) if size == 'small' else spool(item, jacket, cable)
            write(item, obj, label, gauge, size, SMALL_M if size == 'small' else LARGE_M, use, weight, price, stack)


if __name__ == '__main__':
    main()
