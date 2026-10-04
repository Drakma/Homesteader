"""
Builds three procedural vehicles in headless Blender (free, no Meshy credits), in the style of make_boxvan.py:
  vehicle_pickup_old_lightblue  an old, faded light blue single cab pickup with a little rust
  vehicle_pickup_new_black      a new black, raised double cab pickup (lift kit, big tires)
  vehicle_utv_camo              a camo side by side utility vehicle (UTV)
Each has a joined 'Body', four SEPARATE wheels named Wheel_FL/FR/RL/RR (origin on the hub, so the game can spin them) and an empty
'FrontMarker' at the nose. +Y is the front, +Z is up (the glTF export turns this into Unity's axes). Writes the GLB, manifest and README;
render the icons afterwards:

    python tools/make_pickups_utv.py            (generates the camo texture, then runs Blender)
    python tools/render_icon_from_model.py <glb> <png>   for each vehicle
"""
import json
import math
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VEHICLES = os.path.join(ROOT, 'assets', 'vehicles')
CAMO_PNG = os.path.join(ROOT, 'assets', '_scratch', 'camo_woodland.png')


def make_camo_png():
    import numpy as np
    from PIL import Image
    rng = np.random.default_rng(7)
    n = 256
    def noise(scale, seed):
        r = np.random.default_rng(seed)
        g = r.random((n // scale + 2, n // scale + 2))
        im = Image.fromarray((g * 255).astype('uint8')).resize((n, n), Image.BICUBIC)
        return np.asarray(im) / 255.0
    a = 0.6 * noise(32, 1) + 0.4 * noise(16, 2)
    b = 0.6 * noise(32, 3) + 0.4 * noise(12, 4)
    img = np.zeros((n, n, 3))
    img[:] = (0.36, 0.38, 0.22)                      # olive base
    img[a > 0.55] = (0.22, 0.27, 0.16)               # dark green
    img[b > 0.62] = (0.45, 0.35, 0.22)               # tan
    img[(a < 0.3) & (b < 0.4)] = (0.12, 0.12, 0.09)  # near black
    os.makedirs(os.path.dirname(CAMO_PNG), exist_ok=True)
    Image.fromarray((img * 255).astype('uint8')).save(CAMO_PNG)


# ---------------------------------------------------------------------------------------------------------- Blender side
def blender_main():
    import bmesh
    import bpy

    def mat(name, rgb, rough=0.5, metal=0.0, emit=None, image=None):
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        b = m.node_tree.nodes['Principled BSDF']
        b.inputs['Base Color'].default_value = (*rgb, 1.0)
        b.inputs['Roughness'].default_value = rough
        b.inputs['Metallic'].default_value = metal
        if emit:
            b.inputs['Emission Color'].default_value = (*emit, 1.0)
            b.inputs['Emission Strength'].default_value = 1.5
        if image:
            b.inputs['Base Color'].default_value = (1.0, 1.0, 1.0, 1.0)   # the colour factor multiplies the texture
            t = m.node_tree.nodes.new('ShaderNodeTexImage')
            t.image = bpy.data.images.load(image)
            uvn = m.node_tree.nodes.new('ShaderNodeUVMap')
            uvn.uv_map = 'UVMap'
            m.node_tree.links.new(uvn.outputs['UV'], t.inputs['Vector'])   # an explicit UV map, or the exporter writes texCoord -1
            m.node_tree.links.new(t.outputs['Color'], b.inputs['Base Color'])
        return m

    def finish(bm, name, material):
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        bm.free()
        me.materials.append(material)
        o = bpy.data.objects.new(name, me)
        bpy.context.collection.objects.link(o)
        return o

    from mathutils import Vector

    Z = [0.0]   # a height added to every box / prism / cylinder: lifts a body above its axles

    def box(name, x0, x1, y0, y1, z0, z1, material, bevel=0.0, seg=1):
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        for v in bm.verts:
            v.co.x = x0 + (v.co.x + 0.5) * (x1 - x0)
            v.co.y = y0 + (v.co.y + 0.5) * (y1 - y0)
            v.co.z = Z[0] + z0 + (v.co.z + 0.5) * (z1 - z0)
        if bevel > 0:
            bmesh.ops.bevel(bm, geom=bm.edges[:], offset=bevel, segments=seg, affect='EDGES')
        return finish(bm, name, material)

    def prism(name, profile_yz, x0, x1, material):
        """A side profile (y, z points in order) extruded across x0..x1."""
        bm = bmesh.new()
        left = [bm.verts.new((x0, y, Z[0] + z)) for y, z in profile_yz]
        right = [bm.verts.new((x1, y, Z[0] + z)) for y, z in profile_yz]
        bm.faces.new(left[::-1])
        bm.faces.new(right)
        n = len(profile_yz)
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((left[i], left[j], right[j], right[i]))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        return finish(bm, name, material)

    def cyl_y(name, cx, cz, radius, y0, y1, sides, material):
        """A cylinder along the length of the vehicle (headlights, pipes)."""
        bm = bmesh.new()
        ra, rb = [], []
        for i in range(sides):
            a = 2 * math.pi * i / sides
            ra.append(bm.verts.new((cx + math.cos(a) * radius, y0, Z[0] + cz + math.sin(a) * radius)))
            rb.append(bm.verts.new((cx + math.cos(a) * radius, y1, Z[0] + cz + math.sin(a) * radius)))
        for i in range(sides):
            j = (i + 1) % sides
            bm.faces.new((ra[i], ra[j], rb[j], rb[i]))
        bm.faces.new(rb[::-1])
        bm.faces.new(ra)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        return finish(bm, name, material)

    def cyl_x_into(bm, radius, x0, x1, sides):
        ra, rb = [], []
        for i in range(sides):
            a = 2 * math.pi * i / sides
            ra.append(bm.verts.new((x0, math.cos(a) * radius, math.sin(a) * radius)))
            rb.append(bm.verts.new((x1, math.cos(a) * radius, math.sin(a) * radius)))
        for i in range(sides):
            j = (i + 1) % sides
            bm.faces.new((ra[i], ra[j], rb[j], rb[i]))
        bm.faces.new(rb)
        bm.faces.new(ra[::-1])

    def rbox(bm, cx, cy, cz, sx, sy, sz, ang):
        """A box centred at (cx, cy, cz) in a frame that is then turned by `ang` about the x axis (lugs, spokes)."""
        res = bmesh.ops.create_cube(bm, size=1.0)
        ca, sa = math.cos(ang), math.sin(ang)
        for v in res['verts']:
            x = cx + v.co.x * sx
            y = cy + v.co.y * sy
            z = cz + v.co.z * sz
            v.co = (x, y * ca - z * sa, y * sa + z * ca)

    def outward(bm):
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        total = 0.0
        for f in bm.faces:
            c = f.calc_center_median()
            total += f.normal.dot(Vector((0.0, c.y, c.z)))
        if total < 0:
            bmesh.ops.reverse_faces(bm, faces=bm.faces[:])

    def tire_obj(name, radius, width, sides, material, lugs=0, lug_h=0.04, lug_w=0.07):
        bm = bmesh.new()
        h = width / 2
        prof = [(-h, radius * 0.6), (-h, radius * 0.9), (-h * 0.82, radius * 0.985), (h * 0.82, radius * 0.985), (h, radius * 0.9), (h, radius * 0.6)]
        rings = []
        for x, r in prof:
            rings.append([bm.verts.new((x, math.cos(2 * math.pi * i / sides) * r, math.sin(2 * math.pi * i / sides) * r)) for i in range(sides)])
        for k in range(len(prof) - 1):
            for i in range(sides):
                j = (i + 1) % sides
                bm.faces.new((rings[k][i], rings[k][j], rings[k + 1][j], rings[k + 1][i]))
        outward(bm)
        for i in range(lugs):
            rbox(bm, 0.0, 0.0, radius * 0.985 + lug_h * 0.4, width * 0.92, lug_w, lug_h * 2.0, 2 * math.pi * i / lugs)
        return finish(bm, name, material)

    def rim_obj(name, radius, width, out, material, spokes=6, sides=16):
        bm = bmesh.new()
        h = width / 2
        cyl_x_into(bm, radius, -h, h, sides)
        xo = out * (h + 0.012)
        for i in range(spokes):
            rbox(bm, xo, 0.0, radius * 0.5, 0.024, radius * 0.16, radius * 0.9, 2 * math.pi * i / spokes)
        cyl_x_into(bm, radius * 0.2, min(out * h, out * (h + 0.04)), max(out * h, out * (h + 0.04)), 8)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        return finish(bm, name, material)

    def wheels(hw, front_y, rear_y, radius, width, tire_m, rim_m, sides=22, inset=0.1, lugs=0, lug_h=0.04, lug_w=0.07,
               white=None, spokes=6, rim_frac=0.6):
        for nm, x, y in (('Wheel_FL', -hw + inset, front_y), ('Wheel_FR', hw - inset, front_y),
                         ('Wheel_RL', -hw + inset, rear_y), ('Wheel_RR', hw - inset, rear_y)):
            out = -1 if x < 0 else 1
            w = tire_obj(nm, radius, width, sides, tire_m, lugs, lug_h, lug_w)
            w.location = (x, y, radius)   # origin = the hub
            r = rim_obj(nm + '_rim', radius * rim_frac, width * 0.9, out, rim_m, spokes)
            r.parent = w
            r.location = (0, 0, 0)
            if white:
                bm = bmesh.new()
                cyl_x_into(bm, radius * 0.86, min(out * (width / 2 - 0.002), out * (width / 2 + 0.004)),
                           max(out * (width / 2 - 0.002), out * (width / 2 + 0.004)), sides)
                bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
                ww = finish(bm, nm + '_white', white)
                ww.parent = w
                ww.location = (0, 0, 0)

    def arch(name, sx, y, zc, r, hw, material, width=0.13, depth=0.09):
        """A half ring over a wheel, standing proud of the body side: the fender flare."""
        outer, inner = [], []
        n = 10
        for i in range(n + 1):
            a = math.pi * (0.05 + 0.9 * i / n)
            outer.append((y + math.cos(a) * (r + 0.04 + width), zc + math.sin(a) * (r + 0.04 + width)))
            inner.append((y + math.cos(a) * (r + 0.04), zc + math.sin(a) * (r + 0.04)))
        xa, xb = sx * (hw - 0.03), sx * (hw + depth)
        return prism(name, outer + inner[::-1], min(xa, xb), max(xa, xb), material)

    def well(name, sx, y, zc, r, hw, material):
        """The dark wheel well: a patch on the body side behind the wheel."""
        xa, xb = sx * (hw - 0.02), sx * (hw + 0.012)
        return box(name, min(xa, xb), max(xa, xb), y - r - 0.06, y + r + 0.06, zc - r * 0.55, zc + r + 0.06, material)

    def camo_uv(body):
        """After the join: one UV layer on the body, the camo faces box mapped (every face projects along its dominant axis, the pattern
        repeating about every 1.2 m), everything else left at 0."""
        bm = bmesh.new()
        bm.from_mesh(body.data)
        layer = bm.loops.layers.uv.verify()
        bm.normal_update()
        idx = [i for i, m in enumerate(body.data.materials) if m.name == 'Camo']
        for f in bm.faces:
            if f.material_index not in idx:
                continue
            n = f.normal
            ax = max(range(3), key=lambda i: abs(n[i]))
            u, v = [(1, 2), (0, 2), (0, 1)][ax]
            for lo in f.loops:
                lo[layer].uv = (lo.vert.co[u] / 1.2, lo.vert.co[v] / 1.2)
        bm.to_mesh(body.data)
        bm.free()

    def join(objs, name):
        bpy.ops.object.select_all(action='DESELECT')
        for o in objs:
            o.select_set(True)
        bpy.context.view_layer.objects.active = objs[0]
        bpy.ops.object.join()
        body = bpy.context.view_layer.objects.active
        body.name = name
        return body

    def marker(y, z):
        m = bpy.data.objects.new('FrontMarker', None)
        m.location = (0.0, y, z)
        bpy.context.collection.objects.link(m)

    def export(item):
        bpy.ops.object.select_all(action='SELECT')
        folder = os.path.join(VEHICLES, item)
        os.makedirs(folder, exist_ok=True)
        out = os.path.join(folder, item + '.glb')
        bpy.ops.export_scene.gltf(filepath=out, export_format='GLB', use_selection=True, export_yup=True)
        tris = sum(len(p.vertices) - 2 for o in bpy.data.objects if o.type == 'MESH' for p in o.data.polygons)
        print('model:', out, tris, 'tris')
        assert tris <= 10000, item + ' is over the 10000 triangle budget'
        return tris

    # ----------------------------------------------------------------------------------------------- old light blue pickup
    def old_pickup():
        bpy.ops.wm.read_factory_settings(use_empty=True)
        Z[0] = 0.0
        paint = mat('PaintBlue', (0.50, 0.71, 0.80), 0.7)
        paint2 = mat('PaintBlueFaded', (0.62, 0.78, 0.85), 0.8)
        rust = mat('Rust', (0.45, 0.22, 0.1), 0.95)
        chrome = mat('Chrome', (0.75, 0.77, 0.8), 0.3, 0.9)
        dark = mat('Dark', (0.12, 0.12, 0.13), 0.7, 0.2)
        glass = mat('Glass', (0.12, 0.2, 0.25), 0.1)
        tire = mat('Tire', (0.07, 0.07, 0.08), 0.95)
        steel = mat('SteelRim', (0.55, 0.58, 0.6), 0.6, 0.6)
        white = mat('WhiteWall', (0.88, 0.88, 0.84), 0.9)
        red = mat('Tail', (0.7, 0.08, 0.05), 0.4, 0.0, (0.7, 0.05, 0.03))
        amber = mat('Marker', (0.9, 0.55, 0.1), 0.4, 0.0, (0.9, 0.5, 0.05))
        lamp = mat('Lamp', (1.0, 0.95, 0.7), 0.3, 0.0, (1.0, 0.9, 0.55))
        wood = mat('BedWood', (0.42, 0.29, 0.16), 0.9)
        plate = mat('Plate', (0.9, 0.9, 0.85), 0.6)
        hw = 0.92
        fy, ry, R = 1.55, -1.6, 0.4
        p = []
        p.append(box('Chassis', -hw + 0.15, hw - 0.15, -2.55, 2.45, 0.4, 0.7, dark))
        p.append(box('Skid', -0.4, 0.4, -1.0, 1.0, 0.3, 0.45, dark))
        # hood and fenders
        p.append(box('Hood', -hw + 0.05, hw - 0.05, 0.85, 2.45, 0.62, 1.12, paint, bevel=0.07, seg=2))
        p.append(box('HoodSeam', -0.012, 0.012, 0.9, 2.4, 1.115, 1.13, dark))
        p.append(box('HoodRidge', -0.18, 0.18, 1.0, 2.3, 1.12, 1.16, paint2, bevel=0.03))
        p.append(box('GrilleBack', -hw + 0.28, hw - 0.28, 2.43, 2.49, 0.72, 1.02, dark))
        for k in range(9):
            xk = -0.4 + 0.1 * k
            p.append(box('Slat', xk - 0.012, xk + 0.012, 2.49, 2.53, 0.74, 1.0, chrome))
        p.append(box('GrilleBar', -hw + 0.3, hw - 0.3, 2.49, 2.54, 0.86, 0.89, chrome))
        p.append(box('GrilleFrame', -hw + 0.24, hw - 0.24, 2.47, 2.52, 1.0, 1.06, chrome, bevel=0.01))
        p.append(box('Ornament', -0.03, 0.03, 2.2, 2.4, 1.14, 1.2, chrome, bevel=0.01))
        p.append(box('FrontBumper', -hw, hw, 2.45, 2.64, 0.45, 0.68, chrome, bevel=0.04, seg=2))
        p.append(box('BumperGuardL', -0.5, -0.4, 2.62, 2.7, 0.5, 0.66, chrome, bevel=0.015))
        p.append(box('BumperGuardR', 0.4, 0.5, 2.62, 2.7, 0.5, 0.66, chrome, bevel=0.015))
        p.append(box('RearBumper', -hw, hw, -2.67, -2.48, 0.45, 0.68, chrome, bevel=0.04, seg=2))
        p.append(box('PlateF', -0.2, 0.2, 2.56, 2.58, 0.58, 0.7, plate))
        p.append(box('PlateR', -0.2, 0.2, -2.55, -2.53, 0.8, 0.92, plate))
        for s in (-1, 1):
            p.append(cyl_y('Headlight%d' % s, s * 0.6, 0.9, 0.13, 2.42, 2.5, 14, lamp))
            p.append(cyl_y('Bezel%d' % s, s * 0.6, 0.9, 0.165, 2.40, 2.46, 14, chrome))
            p.append(box('Marker%d' % s, s * (hw + 0.005) - 0.012, s * (hw + 0.005) + 0.012, 2.2, 2.35, 0.88, 0.96, amber))
            p.append(box('Taillight%d' % s, s * (hw - 0.14) - 0.07, s * (hw - 0.14) + 0.07, -2.53, -2.46, 0.95, 1.2, red, bevel=0.01))
            p.append(box('MirrorArm%d' % s, s * (hw + 0.02) - 0.015, s * (hw + 0.14) + 0.015, 0.55, 0.6, 1.3, 1.34, chrome))
            p.append(box('Mirror%d' % s, s * (hw + 0.12) - 0.03, s * (hw + 0.17) + 0.03, 0.5, 0.66, 1.3, 1.62, dark, bevel=0.015))
        # cab: lower body, greenhouse, doors
        p.append(box('CabBody', -hw + 0.03, hw - 0.03, -0.55, 0.9, 0.62, 1.12, paint, bevel=0.06, seg=2))
        p.append(prism('Greenhouse', [(-0.55, 1.12), (0.9, 1.12), (0.58, 1.78), (-0.45, 1.78), (-0.55, 1.7)], -hw + 0.08, hw - 0.08, paint2))
        p.append(prism('RoofCap', [(-0.5, 1.77), (0.6, 1.77), (0.58, 1.8), (-0.46, 1.8)], -hw + 0.04, hw - 0.04, paint, ))
        p.append(prism('WindscreenGlass', [(0.86, 1.14), (0.9, 1.14), (0.57, 1.72), (0.52, 1.72)], -hw + 0.16, hw - 0.16, glass))
        p.append(box('WindscreenFrame', -hw + 0.12, hw - 0.12, 0.5, 0.6, 1.72, 1.78, chrome))
        p.append(box('RearGlass', -hw + 0.3, hw - 0.3, -0.56, -0.5, 1.2, 1.62, glass))
        for s in (-1, 1):
            xs = s * (hw - 0.07)
            p.append(box('SideGlass%d' % s, xs - 0.02, xs + 0.02, -0.35, 0.62, 1.2, 1.66, glass))
            p.append(box('VentGlass%d' % s, xs - 0.02, xs + 0.02, 0.62, 0.78, 1.2, 1.62, glass))
            p.append(box('GlassTrim%d' % s, xs - 0.025, xs + 0.025, -0.38, 0.8, 1.16, 1.2, chrome))
            xd = s * (hw - 0.01)
            p.append(box('DoorSeamF%d' % s, xd - 0.008, xd + 0.008, 0.62, 0.65, 0.62, 1.12, dark))
            p.append(box('DoorSeamB%d' % s, xd - 0.008, xd + 0.008, -0.48, -0.45, 0.62, 1.12, dark))
            p.append(box('DoorSeamT%d' % s, xd - 0.008, xd + 0.008, -0.48, 0.65, 1.11, 1.13, dark))
            p.append(box('DoorHandle%d' % s, xd - 0.02, xd + 0.02, -0.28, -0.12, 1.0, 1.05, chrome, bevel=0.01))
            p.append(box('Rocker%d' % s, xd - 0.015, xd + 0.015, -0.5, 0.85, 0.56, 0.62, dark))
        # bed: planks, step side walls, fender humps, front wall, tailgate
        p.append(box('BedFloor', -hw + 0.1, hw - 0.1, -2.5, -0.55, 0.62, 0.76, dark))
        for k in range(8):
            xk = -hw + 0.14 + k * 0.215
            p.append(box('Plank', xk, xk + 0.2, -2.46, -0.6, 0.76, 0.795, wood))
        for s in (-1, 1):
            xs = s * (hw - 0.08)
            p.append(box('BedSide%d' % s, xs - 0.06, xs + 0.06, -2.5, -0.55, 0.72, 1.25, paint, bevel=0.03, seg=2))
            p.append(box('BedCap%d' % s, xs - 0.075, xs + 0.075, -2.5, -0.55, 1.25, 1.29, paint2, bevel=0.015))
            p.append(box('Hump%d' % s, s * (hw - 0.3) - 0.2, s * (hw - 0.3) + 0.2, -1.95, -1.25, 0.76, 1.0, paint, bevel=0.05, seg=2))
            for yk in (-2.3, -1.6, -0.8):
                p.append(box('Pocket%d' % s, xs - 0.07, xs + 0.07, yk - 0.04, yk + 0.04, 1.25, 1.3, dark))
        p.append(box('BedFront', -hw + 0.14, hw - 0.14, -0.7, -0.55, 0.72, 1.3, paint, bevel=0.02))
        p.append(box('Tailgate', -hw + 0.12, hw - 0.12, -2.54, -2.45, 0.72, 1.2, paint2, bevel=0.02))
        p.append(box('TailgateHandle', -0.2, 0.2, -2.57, -2.54, 1.08, 1.14, chrome))
        p.append(box('TailgateRib', -hw + 0.3, hw - 0.3, -2.555, -2.54, 0.85, 0.95, paint, bevel=0.01))
        p.append(box('Antenna', -hw + 0.12, -hw + 0.135, 0.9, 0.925, 1.12, 2.1, chrome))
        # fender flares and wells over all four wheels
        for s in (-1, 1):
            for nm, y in (('F', fy), ('R', ry)):
                p.append(well('Well%s%d' % (nm, s), s, y, R, R, hw, dark))
                p.append(arch('Flare%s%d' % (nm, s), s, y, R, R, hw, paint, width=0.1, depth=0.07))
        # rust: patches along the lower edges, the tailgate and a fender
        p.append(box('Rust1', -hw - 0.005, -hw + 0.01, -2.3, -1.6, 0.56, 0.7, rust))
        p.append(box('Rust2', hw - 0.01, hw + 0.005, 1.4, 2.2, 0.6, 0.78, rust))
        p.append(box('Rust3', -0.6, -0.1, -2.56, -2.54, 0.78, 0.95, rust))
        p.append(box('Rust4', -hw - 0.005, -hw + 0.01, 0.2, 0.7, 0.58, 0.72, rust))
        p.append(box('Rust5', hw - 0.01, hw + 0.005, -0.4, 0.3, 0.58, 0.66, rust))
        p.append(box('Rust6', 0.2, 0.7, 1.5, 2.0, 1.12, 1.135, rust))
        p.append(box('Rust7', hw - 0.02, hw + 0.004, -1.0, -0.7, 0.9, 1.1, rust))
        join(p, 'Body')
        wheels(hw, fy, ry, R, 0.26, tire, steel, sides=24, inset=0.08, white=white, spokes=0, rim_frac=0.62)
        marker(2.7, 0.9)
        return export('vehicle_pickup_old_lightblue')

    # ----------------------------------------------------------------------------------------------- new raised double cab
    def new_pickup():
        bpy.ops.wm.read_factory_settings(use_empty=True)
        LIFT = 0.34
        paint = mat('PaintBlack', (0.025, 0.027, 0.03), 0.25, 0.4)
        trim = mat('Trim', (0.1, 0.1, 0.11), 0.5, 0.2)
        chrome = mat('Chrome', (0.7, 0.72, 0.75), 0.25, 0.9)
        glass = mat('Glass', (0.05, 0.08, 0.11), 0.05)
        tire = mat('Tire', (0.04, 0.04, 0.05), 0.9)
        rim = mat('AlloyRim', (0.5, 0.52, 0.55), 0.3, 0.9)
        red = mat('Tail', (0.75, 0.05, 0.04), 0.3, 0.0, (0.8, 0.04, 0.03))
        lamp = mat('Lamp', (0.9, 0.95, 1.0), 0.2, 0.0, (0.8, 0.9, 1.0))
        amber = mat('Amber', (1.0, 0.6, 0.1), 0.3, 0.0, (1.0, 0.55, 0.05))
        spring = mat('Spring', (0.8, 0.12, 0.05), 0.5, 0.3)
        hw = 1.05
        fy, ry, R = 2.05, -1.95, 0.58
        p = []
        # chassis, axles, shocks, exhaust: the parts the lift shows (not lifted)
        Z[0] = 0.0
        for s in (-1, 1):
            p.append(box('Rail', s * (hw - 0.42) - 0.07, s * (hw - 0.42) + 0.07, -3.0, 3.0, 0.5, 0.82, trim))
            for nm, y in (('F', fy), ('R', ry)):
                p.append(box('Shock%s%d' % (nm, s), s * (hw - 0.5) - 0.035, s * (hw - 0.5) + 0.035, y + 0.14, y + 0.21, 0.62, 1.02, spring))
                p.append(box('ShockMount%s%d' % (nm, s), s * (hw - 0.5) - 0.06, s * (hw - 0.5) + 0.06, y + 0.12, y + 0.23, 1.0, 1.06, trim))
            p.append(box('Leaf%d' % s, s * (hw - 0.42) - 0.05, s * (hw - 0.42) + 0.05, ry - 0.7, ry + 0.7, 0.66, 0.72, trim))
        for nm, y in (('F', fy), ('R', ry)):
            p.append(box('Axle' + nm, -hw + 0.28, hw - 0.28, y - 0.09, y + 0.09, 0.52, 0.64, trim))
            p.append(box('Diff' + nm, -0.22, 0.22, y - 0.2, y + 0.2, 0.38, 0.66, trim, bevel=0.04, seg=2))
        p.append(box('Driveshaft', -0.04, 0.04, ry, fy, 0.56, 0.64, trim))
        p.append(box('Skid', -0.5, 0.5, fy - 0.9, fy - 0.2, 0.36, 0.44, trim))
        p.append(cyl_y('Exhaust', hw - 0.45, 0.52, 0.055, -3.12, -0.3, 10, chrome))
        p.append(cyl_y('ExhaustTip', hw - 0.45, 0.52, 0.075, -3.12, -2.95, 10, chrome))
        Z[0] = LIFT
        # lower body and hood
        p.append(box('LowerBody', -hw, hw, -2.95, 2.95, 0.55, 0.92, paint, bevel=0.06, seg=2))
        p.append(prism('Hood', [(1.15, 0.85), (2.85, 0.85), (2.97, 1.05), (2.92, 1.3), (1.15, 1.34)], -hw + 0.02, hw - 0.02, paint))
        p.append(box('HoodScoop', -0.3, 0.3, 1.5, 2.2, 1.34, 1.42, paint, bevel=0.04, seg=2))
        p.append(box('HoodSeam', -0.01, 0.01, 1.2, 2.9, 1.33, 1.345, trim))
        p.append(box('GrilleBlock', -hw + 0.22, hw - 0.22, 2.9, 3.0, 0.8, 1.26, trim, bevel=0.015))
        for k in range(5):
            zk = 0.9 + 0.09 * k
            p.append(box('GrilleBar%d' % k, -hw + 0.28, hw - 0.28, 2.99, 3.03, zk, zk + 0.045, chrome))
        p.append(box('FrontBumper', -hw + 0.02, hw - 0.02, 2.82, 3.06, 0.5, 0.82, trim, bevel=0.045, seg=2))
        p.append(box('Winch', -0.25, 0.25, 3.04, 3.14, 0.58, 0.72, chrome, bevel=0.02))
        p.append(box('Fairlead', -0.2, 0.2, 3.1, 3.16, 0.64, 0.68, trim))
        # brush guard
        for sx in (-0.5, 0.5):
            p.append(box('GuardPost', sx - 0.03, sx + 0.03, 3.02, 3.1, 0.82, 1.4, chrome))
        p.append(box('GuardTop', -0.53, 0.53, 3.04, 3.12, 1.36, 1.42, chrome))
        p.append(box('GuardMid', -0.53, 0.53, 3.04, 3.12, 0.98, 1.03, chrome))
        p.append(box('RearBumper', -hw + 0.02, hw - 0.02, -3.06, -2.85, 0.5, 0.84, chrome, bevel=0.03, seg=2))
        p.append(box('RearStep', -0.5, 0.5, -3.1, -3.04, 0.82, 0.88, trim))
        p.append(box('Hitch', -0.07, 0.07, -3.24, -2.95, 0.58, 0.7, trim))
        for s in (-1, 1):
            p.append(box('Headlight%d' % s, s * (hw - 0.3) - 0.22, s * (hw - 0.3) + 0.22, 2.9, 3.0, 1.0, 1.2, lamp, bevel=0.01))
            p.append(box('DRL%d' % s, s * (hw - 0.3) - 0.2, s * (hw - 0.3) + 0.2, 2.93, 3.01, 0.95, 0.98, lamp))
            p.append(box('Fog%d' % s, s * (hw - 0.5) - 0.07, s * (hw - 0.5) + 0.07, 2.92, 3.08, 0.55, 0.68, amber))
            p.append(box('Taillight%d' % s, s * (hw - 0.1) - 0.09, s * (hw - 0.1) + 0.09, -2.97, -2.9, 1.0, 1.42, red, bevel=0.01))
            p.append(box('MirrorArm%d' % s, s * (hw + 0.02) - 0.02, s * (hw + 0.18) + 0.02, 1.0, 1.05, 1.5, 1.56, trim))
            p.append(box('Mirror%d' % s, s * (hw + 0.14) - 0.05, s * (hw + 0.2) + 0.05, 0.95, 1.18, 1.46, 1.8, paint, bevel=0.02, seg=2))
            p.append(box('Step%d' % s, s * (hw + 0.05) - 0.12, s * (hw + 0.05) + 0.12, -0.85, 1.05, 0.5, 0.58, trim, bevel=0.015))
            for yb in (-0.6, 0.7):
                p.append(box('StepBracket%d' % s, s * (hw - 0.05) - 0.02, s * (hw + 0.05) + 0.02, yb - 0.04, yb + 0.04, 0.58, 0.9, trim))
        # double cab: a long shell, a windscreen and two glass panes a side, four door seams and handles
        p.append(prism('Cab', [(-1.15, 0.9), (1.1, 0.9), (1.05, 1.34), (0.5, 1.95), (-0.85, 1.95), (-1.15, 1.45)], -hw + 0.04, hw - 0.04, paint))
        p.append(prism('Windscreen', [(1.0, 1.36), (1.06, 1.36), (0.5, 1.9), (0.44, 1.88)], -hw + 0.14, hw - 0.14, glass))
        p.append(box('RoofRack', -0.7, 0.7, -0.7, 0.35, 1.95, 1.99, trim))
        p.append(box('LightBar', -0.6, 0.6, 0.35, 0.47, 1.9, 2.02, lamp, bevel=0.015))
        p.append(box('Fin', -0.04, 0.04, -0.9, -0.7, 1.95, 2.05, trim, bevel=0.01))
        for s in (-1, 1):
            xs = s * (hw - 0.05)
            p.append(box('GlassFront%d' % s, xs - 0.02, xs + 0.02, 0.1, 0.92, 1.42, 1.86, glass))
            p.append(box('GlassRear%d' % s, xs - 0.02, xs + 0.02, -0.98, 0.0, 1.42, 1.82, glass))
            p.append(box('GlassQuarter%d' % s, xs - 0.02, xs + 0.02, -1.08, -1.0, 1.5, 1.7, glass))
            xd = s * (hw - 0.025)
            for yk in (1.02, 0.03, -1.02):
                p.append(box('Seam%d' % s, xd - 0.01, xd + 0.01, yk - 0.012, yk + 0.012, 0.9, 1.88, trim))
            p.append(box('SeamSill%d' % s, xd - 0.01, xd + 0.01, -1.02, 1.02, 0.9, 0.915, trim))
            p.append(box('HandleF%d' % s, xd - 0.02, xd + 0.02, 0.1, 0.32, 1.28, 1.33, chrome, bevel=0.01))
            p.append(box('HandleR%d' % s, xd - 0.02, xd + 0.02, -0.92, -0.7, 1.28, 1.33, chrome, bevel=0.01))
            p.append(box('Flap%d' % s, xd - 0.015, xd + 0.015, -2.0, -1.78, 1.05, 1.3, trim, bevel=0.01))
        p.append(box('BackGlass', -hw + 0.3, hw - 0.3, -1.2, -1.14, 1.5, 1.82, glass))
        p.append(box('BrakeLight', -0.4, 0.4, -1.2, -1.15, 1.9, 1.95, red))
        # short bed
        p.append(box('BedFloor', -hw + 0.1, hw - 0.1, -3.0, -1.15, 0.7, 0.86, trim))
        for s in (-1, 1):
            xs = s * (hw - 0.04)
            p.append(box('BedSide%d' % s, xs - 0.06, xs + 0.06, -3.0, -1.15, 0.8, 1.38, paint, bevel=0.03, seg=2))
            p.append(box('BedCap%d' % s, xs - 0.08, xs + 0.08, -3.0, -1.15, 1.38, 1.43, trim, bevel=0.015))
            p.append(box('Hump%d' % s, s * (hw - 0.34) - 0.24, s * (hw - 0.34) + 0.24, ry - 0.45, ry + 0.45, 0.86, 1.12, trim, bevel=0.05, seg=2))
            p.append(box('TieDown%d' % s, xs - 0.05, xs + 0.05, -2.2, -2.1, 1.0, 1.06, chrome))
        p.append(box('BedFront', -hw + 0.1, hw - 0.1, -1.32, -1.15, 0.8, 1.46, paint, bevel=0.02))
        p.append(box('Tailgate', -hw + 0.08, hw - 0.08, -3.04, -2.94, 0.8, 1.38, paint, bevel=0.02, seg=2))
        p.append(box('TailgateHandle', -0.18, 0.18, -3.07, -3.04, 1.2, 1.26, chrome))
        p.append(box('TailgateBadge', -0.3, 0.3, -3.06, -3.04, 1.0, 1.08, chrome))
        # fender flares and wells (the wheel centre is below the lifted body)
        for s in (-1, 1):
            for nm, y in (('F', fy), ('R', ry)):
                p.append(well('Well%s%d' % (nm, s), s, y, R - LIFT, R, hw, trim))
                p.append(arch('Flare%s%d' % (nm, s), s, y, R - LIFT, R, hw, trim, width=0.15, depth=0.12))
        Z[0] = 0.0
        join(p, 'Body')
        wheels(hw, fy, ry, R, 0.34, tire, rim, sides=28, inset=0.1, lugs=22, lug_h=0.035, lug_w=0.12, spokes=7, rim_frac=0.58)
        marker(3.2, 1.0)
        return export('vehicle_pickup_new_black')

    # ----------------------------------------------------------------------------------------------- camo side by side UTV
    def utv():
        bpy.ops.wm.read_factory_settings(use_empty=True)
        Z[0] = 0.0
        camo = mat('Camo', (0.35, 0.37, 0.22), 0.8, image=CAMO_PNG)
        dark = mat('Dark', (0.08, 0.08, 0.09), 0.7, 0.3)
        cage = mat('Cage', (0.04, 0.04, 0.05), 0.5, 0.5)
        seat = mat('Seat', (0.1, 0.1, 0.09), 0.9)
        belt = mat('Belt', (0.5, 0.18, 0.08), 0.8)
        glass = mat('LightBar', (0.9, 0.95, 1.0), 0.2, 0.0, (0.9, 0.95, 1.0))
        red = mat('Tail', (0.75, 0.05, 0.04), 0.3, 0.0, (0.8, 0.04, 0.03))
        metal = mat('Metal', (0.55, 0.57, 0.6), 0.4, 0.9)
        tire = mat('Tire', (0.05, 0.05, 0.05), 0.95)
        rim = mat('BeadlockRim', (0.12, 0.12, 0.13), 0.5, 0.6)
        hw = 0.78
        fy, ry, R = 0.95, -0.95, 0.36
        p = []
        p.append(box('Frame', -hw + 0.18, hw - 0.18, -1.45, 1.4, 0.32, 0.5, dark))
        p.append(box('Skid', -0.4, 0.4, -1.2, 1.25, 0.26, 0.34, metal, bevel=0.015))
        # suspension: two arms and a shock each wheel
        for s in (-1, 1):
            for nm, y in (('F', fy), ('R', ry)):
                for za in (0.34, 0.5):
                    p.append(box('Arm%s%d' % (nm, s), s * 0.42 if s > 0 else -(hw - 0.12), (hw - 0.12) if s > 0 else -0.42, y - 0.2, y + 0.2, za, za + 0.035, dark))
                p.append(box('Shock%s%d' % (nm, s), s * (hw - 0.3) - 0.03, s * (hw - 0.3) + 0.03, y + 0.1, y + 0.16, 0.42, 0.85, red))
        # nose, hood, bumper, winch, lights
        p.append(prism('Hood', [(0.65, 0.5), (1.55, 0.5), (1.6, 0.72), (1.35, 0.98), (0.65, 1.0)], -hw + 0.08, hw - 0.08, camo))
        p.append(box('Grille', -0.3, 0.3, 1.58, 1.62, 0.55, 0.75, dark))
        p.append(box('FrontBumper', -hw + 0.1, hw - 0.1, 1.52, 1.68, 0.35, 0.55, cage, bevel=0.025, seg=2))
        for sx in (-0.35, 0.35):
            p.append(box('BumperStay', sx - 0.025, sx + 0.025, 1.4, 1.68, 0.55, 0.9, cage))
        p.append(box('Winch', -0.18, 0.18, 1.6, 1.75, 0.38, 0.5, metal, bevel=0.02))
        p.append(box('LightBar', -hw + 0.3, hw - 0.3, 1.2, 1.28, 1.02, 1.1, glass, bevel=0.01))
        for s in (-1, 1):
            p.append(cyl_y('Headlight%d' % s, s * 0.5, 0.78, 0.09, 1.55, 1.63, 12, glass))
        # floor tub, doors, seats (bucket seats with bolsters, headrests and belts), dash
        p.append(box('Floor', -hw + 0.1, hw - 0.1, -0.55, 0.7, 0.45, 0.58, camo))
        for s in (-1, 1):
            xs = s * 0.34
            p.append(box('Door%d' % s, s * (hw - 0.04) - 0.04, s * (hw - 0.04) + 0.04, -0.35, 0.55, 0.55, 0.98, camo, bevel=0.02))
            p.append(box('DoorBar%d' % s, s * (hw - 0.04) - 0.025, s * (hw - 0.04) + 0.025, -0.35, 0.55, 0.98, 1.04, cage))
            p.append(box('DoorHandle%d' % s, s * (hw - 0.02) - 0.02, s * (hw - 0.02) + 0.02, -0.15, 0.05, 0.85, 0.9, metal))
            p.append(box('SeatBase%d' % s, xs - 0.24, xs + 0.24, -0.35, 0.15, 0.58, 0.72, seat, bevel=0.035, seg=2))
            p.append(box('SeatBack%d' % s, xs - 0.24, xs + 0.24, -0.46, -0.32, 0.7, 1.22, seat, bevel=0.035, seg=2))
            p.append(box('Bolster%d' % s, xs - 0.26, xs - 0.2, -0.46, -0.1, 0.7, 1.1, seat, bevel=0.02))
            p.append(box('BolsterB%d' % s, xs + 0.2, xs + 0.26, -0.46, -0.1, 0.7, 1.1, seat, bevel=0.02))
            p.append(box('Headrest%d' % s, xs - 0.13, xs + 0.13, -0.5, -0.38, 1.22, 1.38, seat, bevel=0.03, seg=2))
            p.append(box('Belt%d' % s, xs - 0.05 + 0.08, xs + 0.01 + 0.08, -0.33, -0.28, 0.75, 1.3, belt))
            p.append(box('Fender%d' % s, s * (hw - 0.02) - 0.1, s * (hw - 0.02) + 0.1, 0.9, 1.5, 0.62, 0.95, camo, bevel=0.03, seg=2))
            p.append(box('RearFender%d' % s, s * (hw - 0.02) - 0.1, s * (hw - 0.02) + 0.1, -1.35, -0.75, 0.62, 0.95, camo, bevel=0.03, seg=2))
            p.append(box('Taillight%d' % s, s * (hw - 0.15) - 0.07, s * (hw - 0.15) + 0.07, -1.5, -1.45, 0.7, 0.85, red))
            p.append(box('Pedal%d' % s, xs - 0.07 + 0.0, xs + 0.07, 0.3, 0.36, 0.5, 0.62, metal))
            p.append(box('Mirror%d' % s, s * (hw + 0.1) - 0.03, s * (hw + 0.14) + 0.03, 0.68, 0.8, 1.2, 1.38, dark, bevel=0.015))
            p.append(box('MirrorArm%d' % s, s * (hw - 0.1) - 0.015, s * (hw + 0.1) + 0.015, 0.68, 0.7, 1.28, 1.31, cage))
        p.append(box('Dash', -hw + 0.12, hw - 0.12, 0.45, 0.7, 0.62, 1.0, dark, bevel=0.035, seg=2))
        p.append(box('GaugePod', -0.5, -0.15, 0.4, 0.5, 0.98, 1.1, dark, bevel=0.02))
        p.append(box('Screen', -0.46, -0.2, 0.38, 0.41, 1.0, 1.08, glass))
        p.append(box('SteeringColumn', -0.4, -0.3, 0.1, 0.5, 0.9, 0.98, cage))
        p.append(box('SteeringWheel', -0.55, -0.15, 0.1, 0.2, 0.96, 1.0, cage, bevel=0.015))
        p.append(box('Shifter', -0.05, 0.05, 0.1, 0.16, 0.6, 0.85, metal))
        p.append(box('GrabBar', 0.15, 0.62, 0.42, 0.48, 1.0, 1.04, metal))
        # cargo bed: floor, walls with tie-downs, tailgate with hinges and latches
        p.append(box('BedFloor', -hw + 0.1, hw - 0.1, -1.45, -0.7, 0.5, 0.6, dark))
        for s in (-1, 1):
            p.append(box('BedWall%d' % s, s * (hw - 0.12) - 0.04, s * (hw - 0.12) + 0.04, -1.45, -0.7, 0.58, 0.95, camo, bevel=0.015))
            p.append(box('BedRail%d' % s, s * (hw - 0.12) - 0.05, s * (hw - 0.12) + 0.05, -1.45, -0.7, 0.95, 0.99, cage))
            for yk in (-1.3, -0.9):
                p.append(box('TieDown%d' % s, s * (hw - 0.12) - 0.05, s * (hw - 0.12) + 0.05, yk - 0.04, yk + 0.04, 0.9, 0.96, metal))
            p.append(box('Hinge%d' % s, s * 0.5 - 0.05, s * 0.5 + 0.05, -1.5, -1.47, 0.6, 0.7, metal))
            p.append(box('Latch%d' % s, s * 0.5 - 0.04, s * 0.5 + 0.04, -1.5, -1.47, 0.88, 0.94, metal))
        p.append(box('BedBack', -hw + 0.12, hw - 0.12, -1.48, -1.42, 0.58, 0.95, camo, bevel=0.015))
        p.append(box('BedFront', -hw + 0.12, hw - 0.12, -0.75, -0.7, 0.58, 1.0, camo))
        p.append(box('Hitch', -0.05, 0.05, -1.65, -1.4, 0.34, 0.42, metal))
        # roll cage: posts, roof rails, cross bars, door bars, roof rack
        for sx in (-1, 1):
            for y, top in ((0.62, 1.95), (-0.5, 1.95)):
                p.append(box('Post', sx * (hw - 0.1) - 0.03, sx * (hw - 0.1) + 0.03, y - 0.03, y + 0.03, 0.9 if y > 0 else 0.7, top, cage, bevel=0.008))
            p.append(box('RoofRail', sx * (hw - 0.1) - 0.03, sx * (hw - 0.1) + 0.03, -0.53, 0.65, 1.92, 1.98, cage))
            p.append(box('DoorBar', sx * (hw - 0.1) - 0.03, sx * (hw - 0.1) + 0.03, -0.5, 0.62, 1.2, 1.25, cage))
            p.append(box('Brace', sx * (hw - 0.1) - 0.03, sx * (hw - 0.1) + 0.03, 0.55, 0.85, 1.0, 1.06, cage))
            p.append(box('RearStay', sx * (hw - 0.1) - 0.03, sx * (hw - 0.1) + 0.03, -0.75, -0.5, 1.7, 1.76, cage))
        p.append(box('Roof', -hw + 0.04, hw - 0.04, -0.6, 0.72, 1.97, 2.03, camo, bevel=0.02, seg=2))
        for k in range(4):
            yk = -0.4 + 0.3 * k
            p.append(box('RackBar', -hw + 0.1, hw - 0.1, yk - 0.015, yk + 0.015, 2.03, 2.07, cage))
        p.append(box('CrossBar', -hw + 0.1, hw - 0.1, -0.53, -0.47, 1.4, 1.46, cage))
        p.append(box('FrontCross', -hw + 0.1, hw - 0.1, 0.59, 0.65, 1.4, 1.46, cage))
        # fenders over the wheels
        for s in (-1, 1):
            for nm, y in (('F', fy), ('R', ry)):
                p.append(arch('Flare%s%d' % (nm, s), s, y, R, R, hw, camo, width=0.09, depth=0.08))
        camo_uv(join(p, 'Body'))
        wheels(hw, fy, ry, R, 0.26, tire, rim, sides=24, inset=0.12, lugs=14, lug_h=0.045, lug_w=0.07, spokes=5, rim_frac=0.6)
        marker(1.75, 0.6)
        return export('vehicle_utv_camo')

    out = {'old': old_pickup(), 'new': new_pickup(), 'utv': utv()}
    print('TRIS', json.dumps(out))


def write_manifests(tris):
    templates = {
        'vehicle_pickup_old_lightblue': dict(
            src='vehicle_pickup_old_red', name='Old Light Blue Pickup Truck',
            desc='An old light blue pickup truck with faded paint and a little rust. It still runs.',
            value=3600, dims=(1.84, 5.3, 1.8), fields=dict(vehicle_type='pickup', fuel_type='gasoline', seats=3, cargo_capacity_m3=1.3,
                                                          top_speed_kmh=140, tank_capacity_l=80), tri=tris['old']),
        'vehicle_pickup_new_black': dict(
            src='vehicle_pickup_new_silver', name='New Black Double Cab Pickup (Raised)',
            desc='A new black double cab pickup on a lift kit with big knobby tires, a brush guard and a winch. Room for five and a short bed.',
            value=46000, dims=(2.3, 6.3, 2.35), fields=dict(vehicle_type='pickup', fuel_type='gasoline', seats=5, cargo_capacity_m3=1.5,
                                                             top_speed_kmh=180, tank_capacity_l=98), tri=tris['new']),
        'vehicle_utv_camo': dict(
            src='vehicle_pickup_old_red', name='Camo Side by Side UTV',
            desc='A camouflage side by side utility vehicle: two seats, a roll cage and a small cargo bed. Goes where a truck cannot.',
            value=18500, dims=(1.56, 3.2, 2.03), fields=dict(vehicle_type='utv', fuel_type='gasoline', seats=2, cargo_capacity_m3=0.4,
                                                            top_speed_kmh=95, tank_capacity_l=30), tri=tris['utv']),
    }
    for item, t in templates.items():
        folder = os.path.join(VEHICLES, item)
        d = json.load(open(os.path.join(VEHICLES, t['src'], t['src'] + '.json'), encoding='utf-8'))
        d['id'] = item
        d['name'] = t['name']
        d['description'] = t['desc']
        d['icon'] = item + '.png'
        d['properties']['base_value'] = t['value']
        d['properties']['stores'] = ['vehicles']
        d['models'] = [{'file': item + '.glb', 'format': 'glb', 'dimensions_m': {'x': t['dims'][0], 'y': t['dims'][2], 'z': t['dims'][1]},
                        'triangles': t['tri']}]
        cf = d['category_fields']
        cf.update(t['fields'])
        cf['dimensions_m'] = {'width': t['dims'][0], 'depth': t['dims'][1], 'height': t['dims'][2]}
        cf['fuel_consumption_l_per_min'] = 0.005
        json.dump(d, open(os.path.join(folder, item + '.json'), 'w', encoding='utf-8'), indent=2)
        with open(os.path.join(folder, 'README.md'), 'w', encoding='utf-8') as f:
            f.write(f"""# {t['name']} (`{item}`)

![Icon]({item}.png)

## Overview
- **Category**: `vehicles`
- **Item Identifier**: `{item}`

## Description
{t['desc']}

Built in code (`tools/make_pickups_utv.py`), low poly. The four wheels are separate objects named `Wheel_FL`, `Wheel_FR`, `Wheel_RL`, `Wheel_RR`
with their origin on the hub; an empty named `FrontMarker` sits at the nose.

## Asset Files & Links
- **Plugin Manifest (JSON)**: [{item}.json]({item}.json)
- **Model (GLB, {t['tri']} triangles)**: [{item}.glb]({item}.glb)
- **Icon (PNG)**: [{item}.png]({item}.png)
""")


if __name__ == '__main__':
    try:
        import bpy  # noqa: F401  (running inside Blender)
        blender_main()
    except ImportError:
        make_camo_png()
        res = subprocess.run(['blender', '--background', '--python', os.path.abspath(__file__)], capture_output=True, text=True)
        line = [l for l in res.stdout.splitlines() if l.startswith('TRIS ')]
        print(res.stdout[-1500:])
        if not line:
            print(res.stderr[-1500:])
            sys.exit(1)
        write_manifests(json.loads(line[0][5:]))
