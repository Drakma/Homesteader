"""
Builds the large harvest sack (tool_harvest_sack_large): a burlap sack with a rope-tied neck and a wide strap that goes over the shoulder.
Free and local (headless Blender, no Meshy).

    python tools/make_harvest_sack.py        (runs Blender on this same file, then renders the icon)
"""
import math
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'assets', 'tools', 'tool_harvest_sack_large', 'tool_harvest_sack_large.glb')


def build():
    import bpy
    import bmesh
    from mathutils import Vector
    bpy.ops.wm.read_factory_settings(use_empty=True)

    def mat(name, rgb, rough=0.95):
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        b = m.node_tree.nodes['Principled BSDF']
        b.inputs['Base Color'].default_value = (rgb[0], rgb[1], rgb[2], 1)
        b.inputs['Roughness'].default_value = rough
        return m

    burlap, rope, strap = mat('Burlap', (0.80, 0.58, 0.28)), mat('Rope', (0.45, 0.33, 0.18)), mat('Strap', (0.30, 0.20, 0.10), 0.85)

    def obj(name, bm, m):
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        bm.free()
        o = bpy.data.objects.new(name, me)
        bpy.context.collection.objects.link(o)
        o.data.materials.append(m)
        for p in me.polygons:
            p.use_smooth = True
        return o

    # body: a lathe of a bulging sack, a little flat (wider than deep), gathered at the neck
    prof = [(0.0, 0.0), (0.12, 0.0), (0.19, 0.03), (0.21, 0.14), (0.205, 0.30), (0.18, 0.46), (0.12, 0.58), (0.06, 0.66), (0.04, 0.70), (0.065, 0.76), (0.085, 0.82), (0.0, 0.83)]
    seg = 16
    bm = bmesh.new()
    rings = []
    for r, z in prof:
        ring = []
        for k in range(seg):
            a = 2 * math.pi * k / seg
            wob = 1.0 + 0.04 * math.sin(3 * a + z * 9)
            ring.append(bm.verts.new((math.cos(a) * r * wob * 0.8, math.sin(a) * r * wob, z)))
        rings.append(ring)
    for i in range(len(rings) - 1):
        for k in range(seg):
            a, b, c, d = rings[i][k], rings[i][(k + 1) % seg], rings[i + 1][(k + 1) % seg], rings[i + 1][k]
            try:
                bm.faces.new((a, b, c, d))
            except ValueError:
                pass
    bm.faces.new(rings[0][::-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj('Body', bm, burlap)

    # rope around the neck
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=12, radius1=0.062, radius2=0.062, depth=0.035, matrix=__import__('mathutils').Matrix.Translation((0, 0, 0.705)))
    obj('Rope', bm, rope)

    # strap: a flat band from the neck, looping out and round to the side of the sack (a shoulder loop), as a swept ring of boxes
    bm = bmesh.new()
    n = 24
    pts = []
    for i in range(n + 1):
        t = i / n
        a = math.pi * t
        pts.append(Vector((0.0, -0.20 + 0.40 * t * 0 - 0.22 * math.sin(a) * 0.0, 0)))
    # loop in the XZ plane at y = 0 side: starts at the left of the neck, arcs up and over, ends at the right of the neck
    path = []
    for i in range(n + 1):
        a = math.pi * i / n
        path.append(Vector((math.cos(a) * 0.19, 0.0, 0.30 + math.sin(a) * 0.90)))
    th = 0.012
    prev = None
    for i, p in enumerate(path):
        tang = (path[min(i + 1, n)] - path[max(i - 1, 0)]).normalized()
        nrm = Vector((tang.z, 0, -tang.x)).normalized()
        side = Vector((0, 1, 0))
        w = 0.040 + 0.040 * math.sin(math.pi * i / n) ** 6   # a wider padded section over the shoulder
        cs = [p + side * w + nrm * th, p - side * w + nrm * th, p - side * w - nrm * th, p + side * w - nrm * th]
        vs = [bm.verts.new(c) for c in cs]
        if prev:
            for k in range(4):
                bm.faces.new((prev[k], prev[(k + 1) % 4], vs[(k + 1) % 4], vs[k]))
        prev = vs
    # leather patches where the strap is stitched to the sack
    for sx in (-1, 1):
        bmesh.ops.create_cube(bm, size=1.0, matrix=__import__('mathutils').Matrix.Translation((sx * 0.19, 0.0, 0.32)) @ __import__('mathutils').Matrix.Diagonal((0.05, 0.16, 0.12, 1.0)))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj('Strap', bm, strap)

    # export
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB', use_selection=True, export_yup=True)
    tris = sum(len(o.data.polygons) * (2 if True else 1) for o in bpy.data.objects)
    print('TRIS_APPROX', tris)


if __name__ == '__main__':
    if 'bpy' in sys.modules or any('blender' in a.lower() for a in sys.argv[:1]):
        build()
    else:
        import glob
        cands = glob.glob(r'C:\Program Files\Blender Foundation\Blender *\blender.exe')
        exe = sorted(cands)[-1] if cands else 'blender'
        subprocess.check_call([exe, '-b', '--python', os.path.abspath(__file__)])
        subprocess.check_call([sys.executable, os.path.join(ROOT, 'tools', 'render_icon_from_model.py'), OUT, OUT[:-4] + '.png'])
