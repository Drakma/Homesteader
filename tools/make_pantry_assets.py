"""
Builds the PANTRY staples (assets/ingredients/<id>/): flour, sugar, salt, yeast, baking powder, butter. Free and local (no Meshy).
Each is a modern grocery package standing upright with a large printed label (front and back) in its own colour.

    python tools/make_pantry_assets.py            (paints the labels with PIL, then runs Blender on this same file; writes the GLBs, manifests, READMEs)
    python tools/render_icon_from_model.py assets/ingredients/<id>/<id>.glb assets/ingredients/<id>/<id>.png

Models are metres, Z up in Blender, bottom at z = 0, the label faces -Y (glTF +Z), under 5,000 triangles.
"""
import json
import math
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, 'tools')
OUT = os.path.join(ROOT, 'assets', 'ingredients')
TEX = os.path.join(ROOT, 'assets', '_scratch', 'pantry')

CREAM = (0.97, 0.95, 0.88)
# id: shape, name, label lines, sub line, package colour, ink colour, kg, price, description, size (see build), processing, next
ITEMS = {
    'ingredient_flour': dict(shape='bag', name='All-Purpose Flour', lines=['FLOUR'], sub='ALL PURPOSE', color=(0.13, 0.30, 0.74), ink=(0.09, 0.2, 0.52),
                             kg=2.27, price=14, size=(0.12, 0.075, 0.24), proc='bake', nxt='food_bread',
                             desc='Milled wheat flour in a paper bag. The base of bread, biscuits and most baking.'),
    'ingredient_sugar': dict(shape='bag', name='Granulated Sugar', lines=['SUGAR'], sub='GRANULATED', color=(0.93, 0.34, 0.60), ink=(0.66, 0.12, 0.40),
                             kg=2.27, price=12, size=(0.12, 0.07, 0.22), proc='none', nxt='',
                             desc='White granulated sugar in a paper bag. For baking, jam and sweetening.'),
    'ingredient_salt': dict(shape='carton', name='Table Salt', lines=['SALT'], sub='TABLE SALT', color=(0.10, 0.58, 0.40), ink=(0.05, 0.36, 0.24),
                            kg=0.74, price=4, size=(0.09, 0.06, 0.15), proc='none', nxt='',
                            desc='Fine table salt in a carton with a pour spout. Seasons and preserves.'),
    'ingredient_yeast': dict(shape='jar', name='Active Dry Yeast', lines=['YEAST'], sub='ACTIVE DRY', color=(0.96, 0.52, 0.10), ink=(0.62, 0.28, 0.02),
                             kg=0.11, price=8, size=(0.055, 0.055, 0.085), proc='none', nxt='',
                             desc='Active dry baking yeast in a small jar. Makes bread rise and ferments beer.'),
    'ingredient_baking_powder': dict(shape='tin', name='Baking Powder', lines=['BAKING', 'POWDER'], sub='DOUBLE ACTING', color=(0.85, 0.15, 0.17), ink=(0.62, 0.08, 0.1),
                                     kg=0.23, price=6, size=(0.08, 0.08, 0.1), proc='none', nxt='',
                                     desc='Double-acting baking powder in a tin. Raises quick breads, biscuits and cakes.'),
    'ingredient_butter': dict(shape='slab', name='Butter', lines=['BUTTER'], sub='UNSALTED', color=(1.0, 0.88, 0.22), ink=(0.62, 0.45, 0.0),
                              kg=0.45, price=10, size=(0.13, 0.055, 0.05), proc='none', nxt='',
                              desc='A carton of unsalted butter. For baking, frying and spreading.'),
}


def paint(item):
    """The label texture (system Python: PIL). Boxes: one portrait face. Round packs: a full wrap, the front panel in the middle."""
    from PIL import Image, ImageDraw, ImageFont
    d = ITEMS[item]
    body = tuple(int(c * 255) for c in d['color'])
    ink = tuple(int(c * 255) for c in d['ink'])
    cream = tuple(int(c * 255) for c in CREAM)
    wrap = d['shape'] in ('jar', 'tin')
    lying = d['shape'] == 'slab'                     # a carton on its side: a landscape label, the lettering along its length
    W, H = (1536, 640) if wrap else ((1300, 520) if lying else (640, 1000))
    im = Image.new('RGB', (W, H), body)
    dr = ImageDraw.Draw(im)
    font = lambda s: ImageFont.truetype('arialbd.ttf', s)
    if wrap:
        px0, px1 = W // 2 - 330, W // 2 + 330        # the front panel (a quarter of the wrap)
        py0, py1 = 70, H - 70
    elif lying:
        px0, px1, py0, py1 = 150, W - 150, 50, H - 50
    else:
        px0, px1, py0, py1 = 50, W - 50, 170, H - 170
    dr.rounded_rectangle((px0, py0, px1, py1), radius=40, fill=cream, outline=ink, width=10)
    # the lines of the name, as large as the panel allows
    pw = px1 - px0 - 80
    sizes = []
    for line in d['lines']:
        s = 260
        while dr.textlength(line, font=font(s)) > pw:
            s -= 4
        sizes.append(min(s, 200 if len(d['lines']) > 1 else (190 if lying else 260)))
    sub_s = 52
    while dr.textlength(d['sub'], font=font(sub_s)) > pw:
        sub_s -= 2
    total = sum(sizes) + 24 * (len(sizes) - 1) + 40 + sub_s
    y = (py0 + py1) / 2 - total / 2 - 10
    cx = (px0 + px1) / 2
    for line, s in zip(d['lines'], sizes):
        dr.text((cx - dr.textlength(line, font=font(s)) / 2, y), line, fill=ink, font=font(s))
        y += s + 24
    y += 16
    dr.line((cx - pw / 3, y, cx + pw / 3, y), fill=body, width=8)
    dr.text((cx - dr.textlength(d['sub'], font=font(sub_s)) / 2, y + 18), d['sub'], fill=ink, font=font(sub_s))
    if lying:                                                                # a band at each end of the carton
        dr.rectangle((0, 0, 100, H), fill=ink)
        dr.rectangle((W - 100, 0, W, H), fill=ink)
    elif not wrap:                                                           # a band across the top and the bottom
        dr.rectangle((0, 0, W, 90), fill=ink)
        dr.rectangle((0, H - 90, W, H), fill=ink)
    else:
        dr.rectangle((0, 0, W, 34), fill=ink)
        dr.rectangle((0, H - 34, W, H), fill=ink)
    os.makedirs(TEX, exist_ok=True)
    im.save(os.path.join(TEX, item + '.png'))


# ------------------------------------------------------------------ Blender side

def build(item):
    import bpy
    import bmesh
    from mathutils import Vector
    sys.path.insert(0, TOOLS)
    import kitchen_lib as L
    d = ITEMS[item]
    L.reset_scene()
    for m in list(bpy.data.materials):
        bpy.data.materials.remove(m)
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new('UVMap')
    mats = []

    def mi(m):
        if m not in mats:
            mats.append(m)
        return mats.index(m)

    def shade(rgb, k):
        return tuple(min(1.0, c * k) for c in rgb)

    body_m = L.material(item + '_body', d['color'], 0.55, 0.0)
    dark_m = L.material(item + '_dark', shade(d['color'], 0.7), 0.55, 0.0)
    white_m = L.material(item + '_white', (0.93, 0.93, 0.92), 0.5, 0.0)
    ink_m = L.material(item + '_ink', (0.08, 0.08, 0.09), 0.5, 0.0)
    metal_m = L.material(item + '_metal', (0.75, 0.76, 0.78), 0.35, 0.9)
    label_m = bpy.data.materials.new(item + '_label')
    label_m.use_nodes = True
    bsdf = label_m.node_tree.nodes['Principled BSDF']
    bsdf.inputs['Roughness'].default_value = 0.6
    node = label_m.node_tree.nodes.new('ShaderNodeTexImage')
    node.image = bpy.data.images.load(os.path.join(TEX, item + '.png'))
    label_m.node_tree.links.new(node.outputs['Color'], bsdf.inputs['Base Color'])

    def box(x0, x1, y0, y1, z0, z1, m, label=False, pinch=None, bevel=0.0):
        before = set(bm.faces)
        res = bmesh.ops.create_cube(bm, size=1.0)
        ym = (y0 + y1) / 2
        for v in res['verts']:
            v.co.x = x0 + (v.co.x + 0.5) * (x1 - x0)
            v.co.y = y0 + (v.co.y + 0.5) * (y1 - y0)
            v.co.z = z0 + (v.co.z + 0.5) * (z1 - z0)
            if pinch is not None and v.co.z > (z0 + z1) / 2:
                v.co.y = ym + (v.co.y - ym) * pinch
        if bevel > 0:
            edges = list({e for v in res['verts'] for e in v.link_edges})
            bmesh.ops.bevel(bm, geom=edges, offset=bevel, offset_type='OFFSET', segments=2, profile=0.5, affect='EDGES')
        new = [f for f in bm.faces if f not in before]
        bmesh.ops.recalc_face_normals(bm, faces=new)
        for f in new:
            front, back = f.normal.y < -0.95, f.normal.y > 0.95
            if label and (front or back):
                f.material_index = mi(label_m)
                for lp in f.loops:
                    u = (lp.vert.co.x - x0) / (x1 - x0)
                    lp[uv].uv = ((1 - u) if back else u, (lp.vert.co.z - z0) / (z1 - z0))
            else:
                f.material_index = mi(m)
                for lp in f.loops:
                    lp[uv].uv = (0.0, 0.0)

    def cyl(cx, cy, r0, r1, z0, z1, m, label=False, seg=40, caps=True):
        before = set(bm.faces)
        ring0 = [bm.verts.new((cx + r0 * math.cos(2 * math.pi * k / seg), cy + r0 * math.sin(2 * math.pi * k / seg), z0)) for k in range(seg)]
        ring1 = [bm.verts.new((cx + r1 * math.cos(2 * math.pi * k / seg), cy + r1 * math.sin(2 * math.pi * k / seg), z1)) for k in range(seg)]
        side = []
        for k in range(seg):
            j = (k + 1) % seg
            side.append(bm.faces.new((ring0[k], ring0[j], ring1[j], ring1[k])))
        ends = []
        if caps and r1 > 1e-6:
            ends.append(bm.faces.new(ring1[::-1]))
        if caps:
            ends.append(bm.faces.new(ring0))
        new = [f for f in bm.faces if f not in before]
        bmesh.ops.recalc_face_normals(bm, faces=new)
        for f in side:
            f.smooth = True
            f.material_index = mi(label_m if label else m)
            us = []
            for lp in f.loops:
                a = math.atan2(lp.vert.co.y - cy, lp.vert.co.x - cx)                # -pi/2 is the front (-Y)
                us.append(((a + math.pi / 2) / (2 * math.pi) + 0.5) % 1.0)
            if max(us) - min(us) > 0.5:
                us = [u + 1.0 if u < 0.5 else u for u in us]
            for lp, u in zip(f.loops, us):
                lp[uv].uv = (u, (lp.vert.co.z - z0) / (z1 - z0)) if label else (0.0, 0.0)
        for f in ends:
            f.material_index = mi(m)
            for lp in f.loops:
                lp[uv].uv = (0.0, 0.0)

    w, dp, h = d['size']
    shape = d['shape']
    if shape == 'bag':                                                         # a paper bag: the body, a tapered gusset, a crimped fold
        bh = h * 0.80
        box(-w / 2, w / 2, -dp / 2, dp / 2, 0.0, bh, body_m, label=True, bevel=0.004)
        box(-w / 2, w / 2, -dp / 2, dp / 2, bh, bh + h * 0.12, body_m, pinch=0.18)
        box(-w / 2, w / 2, -dp * 0.09, dp * 0.09, bh + h * 0.12, h, dark_m, bevel=0.002)
    elif shape == 'carton':                                                    # a carton with a lid flap; salt also gets a pour spout
        spout = item == 'ingredient_salt'
        bh = h - (0.018 if spout else 0.0)
        box(-w / 2, w / 2, -dp / 2, dp / 2, 0.0, bh, body_m, label=True, bevel=0.003)
        box(-w / 2 + 0.003, w / 2 - 0.003, -dp / 2 + 0.003, dp / 2 - 0.003, bh - 0.012, bh, dark_m)
        if spout:
            cyl(0.0, 0.0, 0.017, 0.012, bh, h, metal_m, seg=20)
    elif shape == 'slab':                                                      # a carton lying on its side, a folded seam along the top
        box(-w / 2, w / 2, -dp / 2, dp / 2, 0.0, h, body_m, label=True, bevel=0.003)
        box(-w / 2 + 0.004, w / 2 - 0.004, -0.003, 0.003, h, h + 0.0012, dark_m)
    elif shape == 'jar':                                                     # a jar: label body, shoulder, neck, lid
        r = w / 2
        cyl(0, 0, r, r, 0.0, h * 0.70, body_m, label=True)
        cyl(0, 0, r, r * 0.8, h * 0.70, h * 0.78, white_m)
        cyl(0, 0, r * 0.8, r * 0.8, h * 0.78, h * 0.86, white_m)
        cyl(0, 0, r * 0.86, r * 0.86, h * 0.86, h, dark_m)
    elif shape == 'tin':                                                       # a tin: label body, metal rim and lid with a ring
        r = w / 2
        cyl(0, 0, r, r, 0.0, h * 0.04, metal_m)
        cyl(0, 0, r, r, h * 0.04, h * 0.92, body_m, label=True)
        cyl(0, 0, r * 1.01, r * 1.01, h * 0.92, h * 0.96, metal_m)
        cyl(0, 0, r * 0.92, r * 0.92, h * 0.96, h, white_m)
    me = bpy.data.meshes.new(item)
    bm.to_mesh(me)
    for m in mats:
        me.materials.append(m)
    tris = sum(len(p.vertices) - 2 for p in me.polygons)
    bm.free()
    obj = bpy.data.objects.new(item, me)
    bpy.context.collection.objects.link(obj)
    lo, hi = L.bounds(obj)
    dims = (hi.x - lo.x, hi.y - lo.y, hi.z - lo.z)
    folder = os.path.join(OUT, item)
    os.makedirs(folder, exist_ok=True)
    L.export_glb(obj, os.path.join(folder, item + '.glb'))
    write_manifest(item, tris, dims, lo.z)
    print('built', item, tris, 'tris', '%.3f x %.3f x %.3f' % dims, 'zmin %.4f' % lo.z)


def write_manifest(item, tris, dims, zmin):
    d = ITEMS[item]
    w, dp, h = dims
    path = os.path.join(OUT, item, item + '.json')
    m = {
        '$schema': 'https://homesteader.game/schemas/item_v1.json',
        'id': item, 'name': d['name'], 'category': 'ingredients', 'description': d['desc'], 'icon': item + '.png',
        'properties': {
            'weight_kg': d['kg'], 'max_stack_size': 20, 'base_value': d['price'], 'is_consumable': False, 'footprint': None,
            'happiness_modifier': 0, 'thirst_restore': 0, 'energy_restore': 0, 'stamina_restore': 0, 'wellness_modifier': 0,
            'is_buyable': True, 'stores': ['grocer'], 'sale_unit': 'ea',
        },
        'models': [{'file': item + '.glb', 'format': 'glb', 'dimensions_m': {'x': round(w, 3), 'y': round(h, 3), 'z': round(dp, 3)}, 'triangles': int(tris)}],
        'utilities': {
            'water': {'metric': 'None (unplumbed / dry)', 'details': 'None (unplumbed / dry)'},
            'electricity': {'metric': 'None (passive / unpowered)', 'details': 'None (passive / unpowered)'},
            'sewage': {'metric': 'None (no waste discharge)', 'details': 'None (no waste discharge)'},
            'battery': {'metric': 'None (no internal battery)', 'details': 'None (no internal battery)'},
            'internet': {'metric': 'None (offline / non-networked)', 'details': 'None (offline / non-networked)'},
        },
        'growth': {'is_growable': False, 'growth_type': None, 'species': None, 'max_age': None, 'time_unit': None, 'total_stages': 0, 'current_stage': None, 'stages': []},
        'plugin_metadata': {'version': '1.0.0', 'author': 'Homesteader Core', 'compatible_api': 'v1'},
        'category_fields': {'dimensions_m': {'width': round(w, 3), 'depth': round(dp, 3), 'height': round(h, 3)}, 'processing_method': d['proc'], 'next_item_id': d['nxt']},
    }
    nl = chr(10)
    with open(path, 'w', encoding='utf-8', newline=nl) as f:
        json.dump(m, f, indent=2, ensure_ascii=False)
        f.write(nl)
    with open(os.path.join(OUT, item, 'README.md'), 'w', encoding='utf-8', newline=nl) as f:
        f.write('# %s' % d['name'] + nl + nl + d['desc'] + nl + nl + 'Procedural model (tools/make_pantry_assets.py), %d triangles, %.3f x %.3f x %.3f m, label printed front and back.' % (tris, w, dp, h) + nl)


if __name__ == '__main__':
    try:
        import bpy  # noqa: F401
        inside = True
    except ImportError:
        inside = False
    if inside:
        for it in sys.argv[sys.argv.index('--') + 1:]:
            build(it)
    else:
        items = [i for i in sys.argv[1:] if i in ITEMS] or list(ITEMS)
        for it in items:
            paint(it)
        subprocess.run(['blender', '--background', '--python', os.path.abspath(__file__), '--'] + items, check=True)
