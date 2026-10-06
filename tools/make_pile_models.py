"""
Procedural, TEXTURED models for the bulk material piles (sand, gravel, dirt, mulch, bedding stone, manure; tiny / small / medium / large) as GLBs in headless
Blender: low-poly lumpy heaps with a seamless texture (tools/make_pile_textures.py), pivot at the ground in the middle, sized by the manifest's dimensions_m.
The tiny pile is the start of a heap (2 shovelfuls); a pile grows through small, medium and large as material is added (see docs/PILES.md).

    python tools/make_pile_textures.py
    blender --background --python tools/make_pile_models.py
    python tools/make_pile_models.py --manifests        (afterwards: makes the tiny items, writes models[] into the manifests)
    python tools/render_icon_from_model.py <the tiny glb> <the tiny png>                       (icons of the tiny piles; the others keep their art)
"""
import json
import math
import os
import random

try:
    import bmesh
    import bpy
except ImportError:   # plain python: only --manifests is used
    bmesh = bpy = None

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, 'assets')
TEX = os.path.join(ASSETS, '_scratch', 'pile_tex')

# material -> (folder, id prefix, name, roughness, faceted)
MATERIALS = {
    'sand': ('materials', 'mat_pile_sand_', 'Sand', 1.0, False),
    'gravel': ('materials', 'mat_pile_gravel_', 'Gravel', 0.95, True),
    'dirt': ('materials', 'mat_pile_dirt_', 'Dirt', 1.0, False),
    'mulch': ('materials', 'mat_pile_mulch_', 'Mulch', 1.0, True),
    'bedding_stone': ('materials', 'mat_pile_bedding_stone_', 'Bedding Stone', 0.9, True),
    'manure': ('waste', 'waste_pile_manure_', 'Manure', 1.0, False),
}
SIZES = ['tiny', 'small', 'medium', 'large']
TINY_DIMS = {'width': 0.35, 'depth': 0.35, 'height': 0.14}
TILE_M = 0.8       # metres of ground one texture tile covers


def find_manifest(folder, item):
    return os.path.join(ASSETS, folder, item, item + '.json')


def uvs(me):
    """Cylinder-ish UVs: round the heap (angle x radius) on the sides, planar on top, so the texture does not smear on steep faces."""
    layer = me.uv_layers.new(name='UVMap')
    for poly in me.polygons:
        c = poly.center
        n = poly.normal
        ang_c = math.atan2(c.y, c.x)
        for li in poly.loop_indices:
            v = me.vertices[me.loops[li].vertex_index].co
            if abs(n.z) > 0.65:
                u, w = v.x / TILE_M, v.y / TILE_M
            else:
                a = math.atan2(v.y, v.x)
                while a - ang_c > math.pi:
                    a -= 2 * math.pi
                while a - ang_c < -math.pi:
                    a += 2 * math.pi
                r = max(0.15, math.hypot(c.x, c.y))
                u, w = a * r / TILE_M, v.z / TILE_M
            layer.data[li].uv = (u, w)


def build(item, key, dims, rough, faceted, seed):
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    rnd = random.Random(seed)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=3, radius=1.0)
    w, d, h = dims['width'], dims['depth'], dims['height']
    jitter = 0.16 if faceted else 0.08
    for v in bm.verts:
        x, y, z = v.co
        zz = max(z, 0.0)
        r = 1.0 + (rnd.random() - 0.5) * jitter + 0.10 * math.sin(3.1 * x + 1.7 * y) * math.cos(2.3 * y)
        v.co.x = x * r * w / 2
        v.co.y = y * r * d / 2
        v.co.z = zz * (0.92 + (rnd.random() - 0.5) * jitter * 0.8) * h
    for v in bm.verts:
        if v.co.z <= 0.0001:
            v.co.z = 0.0
    me = bpy.data.meshes.new(item)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = not faceted
    uvs(me)
    m = bpy.data.materials.new(item)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes['Principled BSDF']
    bsdf.inputs['Roughness'].default_value = rough
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(os.path.join(TEX, key + '.png'))
    tex.extension = 'REPEAT'
    nt.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    me.materials.append(m)
    o = bpy.data.objects.new(item, me)
    bpy.context.collection.objects.link(o)
    return o, len(me.polygons)


def dims_for(folder, prefix, size):
    if size == 'tiny':
        return dict(TINY_DIMS)
    m = json.load(open(find_manifest(folder, prefix + size), encoding='utf-8'))
    return m['category_fields']['dimensions_m']


def main():
    seed = 11
    for key, (folder, prefix, name, rough, faceted) in MATERIALS.items():
        for size in SIZES:
            item = prefix + size
            dims = dims_for(folder, prefix, size)
            o, tris = build(item, key, dims, rough, faceted, seed)
            seed += 1
            bpy.ops.object.select_all(action='DESELECT')
            o.select_set(True)
            bpy.context.view_layer.objects.active = o
            out_dir = os.path.join(ASSETS, folder, item)
            os.makedirs(out_dir, exist_ok=True)
            bpy.ops.export_scene.gltf(filepath=os.path.join(out_dir, item + '.glb'), export_format='GLB', use_selection=True, export_yup=True,
                                      export_image_format='JPEG', export_jpeg_quality=85)
            print('PILE', item, tris)


def write_manifests():
    import copy
    import sys
    sys.path.insert(0, os.path.join(ROOT, 'tools'))
    import asset_references as ar
    for key, (folder, prefix, name, rough, faceted) in MATERIALS.items():
        small = json.load(open(find_manifest(folder, prefix + 'small'), encoding='utf-8'))
        for size in SIZES:
            item = prefix + size
            mp = find_manifest(folder, item)
            if size == 'tiny' and not os.path.isfile(mp):
                m = copy.deepcopy(small)
                m['id'] = item
                m['name'] = 'Tiny %s Pile' % name
                m['description'] = 'The start of a heap of %s (2 shovelfuls). It grows as more is added.' % name.lower()
                m['icon'] = item + '.png'
                m['properties']['weight_kg'] = round(small['properties']['weight_kg'] * 0.2, 2)
                m['properties']['base_value'] = max(1, round(small['properties'].get('base_value', 4) * 0.2, 2))
                m['category_fields']['dimensions_m'] = dict(TINY_DIMS)
                os.makedirs(os.path.dirname(mp), exist_ok=True)
                open(mp, 'w', encoding='utf-8', newline='\n').write(json.dumps(m, indent=2, ensure_ascii=False) + '\n')
                open(os.path.join(os.path.dirname(mp), 'README.md'), 'w', encoding='utf-8', newline='\n').write('# %s\n\n%s\n' % (m['name'], m['description']))
                print('made', item)
            t = open(mp, encoding='utf-8').read()
            m = json.loads(t)
            dims = m['category_fields']['dimensions_m']
            m['models'] = [{'file': item + '.glb', 'format': 'glb', 'dimensions_m': {'x': dims['width'], 'y': dims['height'], 'z': dims['depth']}}]
            ar._dump_like(mp, t, m)
    print('manifests written')


if __name__ == '__main__':
    import sys
    if '--manifests' in sys.argv:
        write_manifests()
    else:
        main()
