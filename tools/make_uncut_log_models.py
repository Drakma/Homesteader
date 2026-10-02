"""
Builds the uncut log models (assets/materials/mat_log_<species>_uncut_<small|medium|long>/<id>.glb) in headless Blender and
points each manifest at its model. Free and local: a tapered, bark-rough cylinder lying along X with a few cut branch
stubs, one 128 px texture (bark on the left half, end grain with rings on the right), under 400 triangles each.
Pivot: centred, resting on the ground (Y_min = 0).

  blender --background --python tools/make_uncut_log_models.py
"""
import json
import math
import os
import random
import sys

import bpy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAT = os.path.join(ROOT, 'assets', 'materials')

# species: (bark colour, end-grain colour, birch-style marks)
SPECIES = {
    'oak': ((0.25, 0.19, 0.13), (0.62, 0.46, 0.28), False),
    'birch': ((0.86, 0.84, 0.78), (0.78, 0.65, 0.45), True),
    'maple': ((0.36, 0.30, 0.25), (0.75, 0.58, 0.40), False),
    'pine': ((0.38, 0.22, 0.14), (0.82, 0.65, 0.40), False),
    'poplar': ((0.50, 0.48, 0.40), (0.80, 0.72, 0.55), False),
    'willowood': ((0.33, 0.30, 0.20), (0.70, 0.60, 0.42), False),
}
# size: (length m, radius m, branch stubs)
SIZES = {'small': (1.3, 0.13, 2), 'medium': (2.4, 0.17, 3), 'long': (4.0, 0.21, 4)}
SIDES, RINGS = 12, 8


def texture(name, bark, end, marks):
    n = 128
    img = bpy.data.images.new(name, n, n, alpha=False)
    rnd = random.Random(name)
    streak = [rnd.uniform(0.75, 1.15) for _ in range(n)]
    px = []
    for y in range(n):
        for x in range(n):
            u, v = x / n, y / n
            if u < 0.5:
                k = streak[(x * 3) % n] * (0.9 + 0.2 * math.sin(v * 40 + x * 0.7))
                c = [min(1.0, ch * k) for ch in bark]
                if marks and (y // 5) % 4 == 0 and (x // 9) % 3 != 1:
                    c = [ch * 0.35 for ch in c]
            else:
                d = math.hypot(u - 0.75, v - 0.5) / 0.24
                ring = 0.82 + 0.18 * math.sin(d * 22)
                c = [ch * ring for ch in end] if d <= 1.0 else [ch * 0.6 for ch in bark]
            px += [c[0], c[1], c[2], 1.0]
    img.pixels = px
    img.pack()
    return img


def build(item_id, species, size):
    bark, end, marks = SPECIES[species]
    length, radius, stubs = SIZES[size]
    rnd = random.Random(item_id)
    verts, uvs, faces = [], [], []

    def add(co, uv):
        verts.append(co)
        uvs.append(uv)
        return len(verts) - 1

    # side wall: RINGS+1 rings of SIDES+1 verts (the seam repeats so the UV can wrap)
    grid = []
    for r in range(RINGS + 1):
        t = r / RINGS
        x = -length / 2 + length * t
        taper = 1.0 - 0.12 * t
        row = []
        for s in range(SIDES + 1):
            a = 2 * math.pi * (s % SIDES) / SIDES
            wob = 1.0 + (rnd.uniform(-0.06, 0.06) if s % SIDES == (s if s < SIDES else 0) else 0)
            rr = radius * taper * wob
            row.append(add((x, math.cos(a) * rr, radius + math.sin(a) * rr), (0.5 * s / SIDES, t)))
        grid.append(row)
    for r in range(RINGS):
        for s in range(SIDES):
            a, b, c, d = grid[r][s], grid[r][s + 1], grid[r + 1][s + 1], grid[r + 1][s]
            faces.append((a, b, c, d))

    # end caps
    for x, taper, flip in ((-length / 2, 1.0, True), (length / 2, 0.88, False)):
        centre = add((x, 0.0, radius), (0.75, 0.5))
        ring = []
        for s in range(SIDES):
            a = 2 * math.pi * s / SIDES
            ring.append(add((x, math.cos(a) * radius * taper, radius + math.sin(a) * radius * taper),
                            (0.75 + 0.24 * math.cos(a), 0.5 + 0.48 * math.sin(a))))
        for s in range(SIDES):
            p, q = ring[s], ring[(s + 1) % SIDES]
            faces.append((centre, q, p) if flip else (centre, p, q))

    # cut branch stubs: short tapered 6-sided tubes standing off the side
    for i in range(stubs):
        along = -length / 2 + length * (0.2 + 0.6 * (i + rnd.random() * 0.5) / max(1, stubs))
        ang = rnd.uniform(0, 2 * math.pi)
        dy, dz = math.cos(ang), math.sin(ang)
        base_r, tip_r, out = 0.035, 0.026, 0.11
        px, py, pz = along, dy * radius * 0.92, radius + dz * radius * 0.92
        # an orthonormal frame across the stub (its axis is (0, dy, dz))
        ux, uy, uz = 1.0, 0.0, 0.0
        vx, vy, vz = 0.0, -dz, dy
        base, tip = [], []
        for s in range(6):
            a = 2 * math.pi * s / 6
            ca, sa = math.cos(a), math.sin(a)
            bx, by, bz = ux * ca + vx * sa, uy * ca + vy * sa, uz * ca + vz * sa
            base.append(add((px + bx * base_r, py + by * base_r, pz + bz * base_r), (0.1, 0.1)))
            tip.append(add((px + bx * tip_r + 0.0, py + by * tip_r + dy * out, pz + bz * tip_r + dz * out), (0.12, 0.12)))
        cap = add((px, py + dy * out, pz + dz * out), (0.75, 0.5))
        for s in range(6):
            n = (s + 1) % 6
            faces.append((base[s], base[n], tip[n], tip[s]))
            faces.append((tip[s], tip[n], cap))

    mesh = bpy.data.meshes.new(item_id)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    uv = mesh.uv_layers.new(name='UVMap')
    for poly in mesh.polygons:
        for li in poly.loop_indices:
            uv.data[li].uv = uvs[mesh.loops[li].vertex_index]
    for poly in mesh.polygons:
        poly.use_smooth = True
    obj = bpy.data.objects.new(item_id, mesh)
    bpy.context.collection.objects.link(obj)

    mat = bpy.data.materials.new(item_id)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes['Principled BSDF']
    tex = mat.node_tree.nodes.new('ShaderNodeTexImage')
    tex.image = texture(item_id, bark, end, marks)
    mat.node_tree.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = 0.95
    mesh.materials.append(mat)
    return obj


def main():
    count = 0
    for species in SPECIES:
        for size in SIZES:
            item_id = f'mat_log_{species}_uncut_{size}'
            folder = os.path.join(MAT, item_id)
            manifest = os.path.join(folder, item_id + '.json')
            if not os.path.exists(manifest):
                print('skip (no manifest):', item_id)
                continue
            for o in list(bpy.data.objects):
                bpy.data.objects.remove(o, do_unlink=True)
            obj = build(item_id, species, size)
            bpy.context.view_layer.objects.active = obj
            obj.select_set(True)
            out = os.path.join(folder, item_id + '.glb')
            bpy.ops.export_scene.gltf(filepath=out, export_format='GLB', use_selection=True, export_yup=True)
            tris = sum(len(p.vertices) - 2 for p in obj.data.polygons)
            d = json.load(open(manifest, encoding='utf-8'))
            L, R, _ = SIZES[size]
            d['models'] = [{'file': item_id + '.glb', 'format': 'glb',
                            'dimensions_m': {'x': round(L, 2), 'y': round(R * 2.2, 2), 'z': round(R * 2.2, 2)}, 'triangles': tris}]
            json.dump(d, open(manifest, 'w', encoding='utf-8'), indent=2)
            print('ok', item_id, tris, 'tris')
            count += 1
    print('models built:', count)


main()
