"""
Builds the CANNING containers (assets/kitchen/<id>/): the juice bottles, peanut butter jars and jam jars the Meals List fills. Free and local (no Meshy).
Each is a LIQUID CONTAINER (manifest `liquid_container`: a capacity in litres and the liquid tag it takes) sold empty: a meal fills it and what is in it stays with it
(it is kept in the toolbar, in a cabinet or on a shelf, not used up). Labels are printed round the glass, in the product's own colour.

    python tools/make_canning_assets.py            (paints the labels with PIL, then runs Blender on this same file; writes the GLBs, manifests, READMEs)
    python tools/render_icon_from_model.py assets/kitchen/<id>/<id>.glb assets/kitchen/<id>/<id>.png
Afterwards: python tools/make_kitchen_assets.py --storage ; python tools/generate_unity_asset_catalog.py ; python tools/package_catalog_as_mods.py
"""
import json
import math
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, 'tools')
OUT = os.path.join(ROOT, 'assets', 'kitchen')
TEX = os.path.join(ROOT, 'assets', '_scratch', 'canning')
NL = chr(10)

CREAM = (0.97, 0.95, 0.88)
# id: shape, name, description, capacity L, empty kg, price, size (r, h) m, liquid tag, label lines, label sub, label colour, ink colour, lid colour
ITEMS = {
    'kitchen_juice_bottle_1l': dict(shape='bottle', name='Juice Bottle', cap=1.0, kg=0.35, price=3, size=(0.043, 0.26), tag='#juice', lines=['JUICE'], sub='FRESH PRESSED',
                                    color=(0.98, 0.58, 0.10), ink=(0.62, 0.30, 0.02), lid=(0.85, 0.22, 0.10),
                                    desc='An empty glass bottle with a screw cap, for fresh juice. Fill it at the juicer.'),
    'kitchen_juice_bottle_2l': dict(shape='bottle', name='Large Juice Bottle', cap=2.0, kg=0.6, price=5, size=(0.056, 0.31), tag='#juice', lines=['JUICE'], sub='FAMILY BOTTLE',
                                    color=(0.98, 0.58, 0.10), ink=(0.62, 0.30, 0.02), lid=(0.85, 0.22, 0.10),
                                    desc='An empty large glass bottle with a screw cap, for fresh juice. Fill it at the juicer.'),
    'kitchen_cream_bottle_500ml': dict(shape='bottle', name='Cream Bottle', cap=0.5, kg=0.25, price=3, size=(0.036, 0.2), tag='liquid_cream', lines=['CREAM'], sub='FRESH',
                                       color=(0.96, 0.94, 0.82), ink=(0.30, 0.45, 0.70), lid=(0.30, 0.45, 0.70),
                                       desc='An empty glass bottle with a screw cap, for cream. Skim it from milk at the blender.'),
    'kitchen_syrup_bottle_500ml': dict(shape='bottle', name='Maple Syrup Bottle', cap=0.5, kg=0.25, price=3, size=(0.036, 0.2), tag='liquid_maple_syrup', lines=['MAPLE', 'SYRUP'], sub='PURE',
                                       color=(0.78, 0.45, 0.12), ink=(0.40, 0.20, 0.04), lid=(0.55, 0.28, 0.08),
                                       desc='An empty glass bottle with a screw cap, for maple syrup. Boil sap down on the stove to fill it.'),
    # SOLD FULL (liquid_container.filled_with): the farm supplies we have no animal, hive, tap or grove for yet are bought at the grocer
    'kitchen_milk_jug_4l': dict(shape='bottle', name='Milk Jug', cap=3.8, kg=0.2, price=5, size=(0.07, 0.27), tag='#drink', filled='liquid_milk', lines=['MILK'], sub='WHOLE',
                                color=(0.92, 0.95, 0.99), ink=(0.20, 0.35, 0.65), lid=(0.20, 0.35, 0.65),
                                desc='A jug of fresh whole milk, sold full. When it is empty it is a jug you can refill with a drink.'),
    'kitchen_goat_milk_jug_2l': dict(shape='bottle', name='Goat Milk Jug', cap=2.0, kg=0.15, price=6, size=(0.055, 0.24), tag='#drink', filled='liquid_goat_milk', lines=['GOAT', 'MILK'], sub='FRESH',
                                     color=(0.94, 0.97, 0.90), ink=(0.30, 0.50, 0.25), lid=(0.30, 0.50, 0.25),
                                     desc='A jug of fresh goat milk, sold full.'),
    'kitchen_honey_jar_350ml': dict(shape='jar', name='Honey Jar', cap=0.35, kg=0.2, price=7, size=(0.045, 0.105), tag='liquid_honey', filled='liquid_honey', lines=['HONEY'], sub='RAW',
                                    color=(0.98, 0.72, 0.12), ink=(0.55, 0.32, 0.02), lid=(0.85, 0.50, 0.05),
                                    desc='A jar of raw honey, sold full.'),
    'kitchen_olive_oil_bottle_750ml': dict(shape='bottle', name='Olive Oil Bottle', cap=0.75, kg=0.3, price=9, size=(0.04, 0.27), tag='liquid_olive_oil', filled='liquid_olive_oil', lines=['OLIVE', 'OIL'], sub='EXTRA VIRGIN',
                                           color=(0.55, 0.68, 0.22), ink=(0.20, 0.30, 0.06), lid=(0.20, 0.30, 0.06),
                                           desc='A bottle of extra virgin olive oil, sold full. It is a cooking oil.'),
    'kitchen_maple_sap_jug_4l': dict(shape='bottle', name='Maple Sap Jug', cap=4.0, kg=0.2, price=6, size=(0.07, 0.27), tag='liquid_maple_sap', filled='liquid_maple_sap', lines=['MAPLE', 'SAP'], sub='RAW',
                                     color=(0.86, 0.80, 0.62), ink=(0.45, 0.30, 0.08), lid=(0.55, 0.28, 0.08),
                                     desc='A jug of clear maple sap, sold full. Boil it down on the stove for maple syrup.'),
    'kitchen_jar_peanut_butter_450g': dict(shape='jar', name='Peanut Butter Jar', cap=0.41, kg=0.2, price=2, size=(0.045, 0.105), tag='liquid_peanut_butter', lines=['PEANUT', 'BUTTER'], sub='SMOOTH',
                                           color=(0.80, 0.55, 0.22), ink=(0.45, 0.27, 0.06), lid=(0.55, 0.12, 0.10),
                                           desc='An empty wide-mouth jar with a lid, for peanut butter. Fill it at the blender.'),
    'kitchen_jar_peanut_butter_900g': dict(shape='jar', name='Large Peanut Butter Jar', cap=0.82, kg=0.32, price=3, size=(0.058, 0.135), tag='liquid_peanut_butter', lines=['PEANUT', 'BUTTER'], sub='SMOOTH',
                                           color=(0.80, 0.55, 0.22), ink=(0.45, 0.27, 0.06), lid=(0.55, 0.12, 0.10),
                                           desc='An empty large wide-mouth jar with a lid, for peanut butter. Fill it at the blender.'),
    'kitchen_jar_walnut_butter_450g': dict(shape='jar', name='Walnut Butter Jar', cap=0.41, kg=0.2, price=2, size=(0.045, 0.105), tag='liquid_walnut_butter', lines=['WALNUT', 'BUTTER'], sub='SMOOTH',
                                    color=(0.62, 0.5, 0.36), ink=(0.3, 0.2, 0.1), lid=(0.18, 0.38, 0.24),
                                    desc='An empty wide-mouth jar with a lid, for walnut butter. Fill it at the blender.'),
    'kitchen_jar_walnut_butter_900g': dict(shape='jar', name='Large Walnut Butter Jar', cap=0.82, kg=0.32, price=3, size=(0.058, 0.135), tag='liquid_walnut_butter', lines=['WALNUT', 'BUTTER'], sub='SMOOTH',
                                    color=(0.62, 0.5, 0.36), ink=(0.3, 0.2, 0.1), lid=(0.18, 0.38, 0.24),
                                    desc='An empty large wide-mouth jar with a lid, for walnut butter. Fill it at the blender.'),
    'kitchen_jar_pecan_butter_450g': dict(shape='jar', name='Pecan Butter Jar', cap=0.41, kg=0.2, price=2, size=(0.045, 0.105), tag='liquid_pecan_butter', lines=['PECAN', 'BUTTER'], sub='SMOOTH',
                                    color=(0.74, 0.38, 0.2), ink=(0.4, 0.16, 0.05), lid=(0.15, 0.25, 0.5),
                                    desc='An empty wide-mouth jar with a lid, for pecan butter. Fill it at the blender.'),
    'kitchen_jar_pecan_butter_900g': dict(shape='jar', name='Large Pecan Butter Jar', cap=0.82, kg=0.32, price=3, size=(0.058, 0.135), tag='liquid_pecan_butter', lines=['PECAN', 'BUTTER'], sub='SMOOTH',
                                    color=(0.74, 0.38, 0.2), ink=(0.4, 0.16, 0.05), lid=(0.15, 0.25, 0.5),
                                    desc='An empty large wide-mouth jar with a lid, for pecan butter. Fill it at the blender.'),
    'kitchen_jar_hazelnut_butter_450g': dict(shape='jar', name='Hazelnut Butter Jar', cap=0.41, kg=0.2, price=2, size=(0.045, 0.105), tag='liquid_hazelnut_butter', lines=['HAZELNUT', 'BUTTER'], sub='SMOOTH',
                                    color=(0.56, 0.32, 0.18), ink=(0.3, 0.15, 0.06), lid=(0.8, 0.62, 0.18),
                                    desc='An empty wide-mouth jar with a lid, for hazelnut butter. Fill it at the blender.'),
    'kitchen_jar_hazelnut_butter_900g': dict(shape='jar', name='Large Hazelnut Butter Jar', cap=0.82, kg=0.32, price=3, size=(0.058, 0.135), tag='liquid_hazelnut_butter', lines=['HAZELNUT', 'BUTTER'], sub='SMOOTH',
                                    color=(0.56, 0.32, 0.18), ink=(0.3, 0.15, 0.06), lid=(0.8, 0.62, 0.18),
                                    desc='An empty large wide-mouth jar with a lid, for hazelnut butter. Fill it at the blender.'),
    'kitchen_oil_bottle_sunflower_750ml': dict(shape='bottle', name='Sunflower Oil Bottle', cap=0.75, kg=0.4, price=3, size=(0.038, 0.25), tag='liquid_sunflower_oil', lines=['SUNFLOWER', 'OIL'], sub='PURE',
                                     color=(0.98, 0.8, 0.12), ink=(0.62, 0.45, 0.0), lid=(0.95, 0.65, 0.05),
                                     desc='An empty glass bottle with a screw cap, for sunflower oil. Fill it at the oil press.'),
    'kitchen_oil_bottle_sunflower_2l': dict(shape='bottle', name='Large Sunflower Oil Bottle', cap=2.0, kg=0.6, price=5, size=(0.056, 0.31), tag='liquid_sunflower_oil', lines=['SUNFLOWER', 'OIL'], sub='PURE',
                                     color=(0.98, 0.8, 0.12), ink=(0.62, 0.45, 0.0), lid=(0.95, 0.65, 0.05),
                                     desc='An empty large glass bottle with a screw cap, for sunflower oil. Fill it at the oil press.'),
    'kitchen_oil_bottle_soybean_750ml': dict(shape='bottle', name='Soybean Oil Bottle', cap=0.75, kg=0.4, price=3, size=(0.038, 0.25), tag='liquid_soybean_oil', lines=['SOYBEAN', 'OIL'], sub='PURE',
                                     color=(0.58, 0.74, 0.25), ink=(0.28, 0.42, 0.06), lid=(0.3, 0.55, 0.15),
                                     desc='An empty glass bottle with a screw cap, for soybean oil. Fill it at the oil press.'),
    'kitchen_oil_bottle_soybean_2l': dict(shape='bottle', name='Large Soybean Oil Bottle', cap=2.0, kg=0.6, price=5, size=(0.056, 0.31), tag='liquid_soybean_oil', lines=['SOYBEAN', 'OIL'], sub='PURE',
                                     color=(0.58, 0.74, 0.25), ink=(0.28, 0.42, 0.06), lid=(0.3, 0.55, 0.15),
                                     desc='An empty large glass bottle with a screw cap, for soybean oil. Fill it at the oil press.'),
    'kitchen_oil_bottle_canola_750ml': dict(shape='bottle', name='Canola Oil Bottle', cap=0.75, kg=0.4, price=3, size=(0.038, 0.25), tag='liquid_canola_oil', lines=['CANOLA', 'OIL'], sub='PURE',
                                     color=(0.95, 0.85, 0.20), ink=(0.30, 0.45, 0.05), lid=(0.35, 0.60, 0.15),
                                     desc='An empty glass bottle with a screw cap, for canola oil. Fill it at the oil press.'),
    'kitchen_oil_bottle_canola_2l': dict(shape='bottle', name='Large Canola Oil Bottle', cap=2.0, kg=0.6, price=5, size=(0.056, 0.31), tag='liquid_canola_oil', lines=['CANOLA', 'OIL'], sub='PURE',
                                     color=(0.95, 0.85, 0.20), ink=(0.30, 0.45, 0.05), lid=(0.35, 0.60, 0.15),
                                     desc='An empty large glass bottle with a screw cap, for canola oil. Fill it at the oil press.'),
    'kitchen_oil_bottle_corn_750ml': dict(shape='bottle', name='Corn Oil Bottle', cap=0.75, kg=0.4, price=3, size=(0.038, 0.25), tag='liquid_corn_oil', lines=['CORN', 'OIL'], sub='PURE',
                                     color=(0.96, 0.66, 0.1), ink=(0.6, 0.36, 0.02), lid=(0.85, 0.5, 0.05),
                                     desc='An empty glass bottle with a screw cap, for corn oil. Fill it at the oil press.'),
    'kitchen_oil_bottle_corn_2l': dict(shape='bottle', name='Large Corn Oil Bottle', cap=2.0, kg=0.6, price=5, size=(0.056, 0.31), tag='liquid_corn_oil', lines=['CORN', 'OIL'], sub='PURE',
                                     color=(0.96, 0.66, 0.1), ink=(0.6, 0.36, 0.02), lid=(0.85, 0.5, 0.05),
                                     desc='An empty large glass bottle with a screw cap, for corn oil. Fill it at the oil press.'),
    'kitchen_oil_bottle_cottonseed_750ml': dict(shape='bottle', name='Cottonseed Oil Bottle', cap=0.75, kg=0.4, price=3, size=(0.038, 0.25), tag='liquid_cottonseed_oil', lines=['COTTON', 'SEED OIL'], sub='PURE',
                                     color=(0.9, 0.86, 0.76), ink=(0.5, 0.42, 0.28), lid=(0.6, 0.5, 0.35),
                                     desc='An empty glass bottle with a screw cap, for cottonseed oil. Fill it at the oil press.'),
    'kitchen_oil_bottle_cottonseed_2l': dict(shape='bottle', name='Large Cottonseed Oil Bottle', cap=2.0, kg=0.6, price=5, size=(0.056, 0.31), tag='liquid_cottonseed_oil', lines=['COTTON', 'SEED OIL'], sub='PURE',
                                     color=(0.9, 0.86, 0.76), ink=(0.5, 0.42, 0.28), lid=(0.6, 0.5, 0.35),
                                     desc='An empty large glass bottle with a screw cap, for cottonseed oil. Fill it at the oil press.'),
    'kitchen_oil_bottle_peanut_750ml': dict(shape='bottle', name='Peanut Oil Bottle', cap=0.75, kg=0.4, price=3, size=(0.038, 0.25), tag='liquid_peanut_oil', lines=['PEANUT', 'OIL'], sub='PURE',
                                     color=(0.74, 0.46, 0.18), ink=(0.42, 0.22, 0.05), lid=(0.55, 0.3, 0.08),
                                     desc='An empty glass bottle with a screw cap, for peanut oil. Fill it at the oil press.'),
    'kitchen_oil_bottle_peanut_2l': dict(shape='bottle', name='Large Peanut Oil Bottle', cap=2.0, kg=0.6, price=5, size=(0.056, 0.31), tag='liquid_peanut_oil', lines=['PEANUT', 'OIL'], sub='PURE',
                                     color=(0.74, 0.46, 0.18), ink=(0.42, 0.22, 0.05), lid=(0.55, 0.3, 0.08),
                                     desc='An empty large glass bottle with a screw cap, for peanut oil. Fill it at the oil press.'),
    'kitchen_oil_bottle_flax_750ml': dict(shape='bottle', name='Flaxseed Oil Bottle', cap=0.75, kg=0.4, price=3, size=(0.038, 0.25), tag='liquid_flax_oil', lines=['FLAXSEED', 'OIL'], sub='PURE',
                                     color=(0.34, 0.5, 0.76), ink=(0.15, 0.25, 0.5), lid=(0.2, 0.3, 0.6),
                                     desc='An empty glass bottle with a screw cap, for flaxseed oil. Fill it at the oil press.'),
    'kitchen_oil_bottle_flax_2l': dict(shape='bottle', name='Large Flaxseed Oil Bottle', cap=2.0, kg=0.6, price=5, size=(0.056, 0.31), tag='liquid_flax_oil', lines=['FLAXSEED', 'OIL'], sub='PURE',
                                     color=(0.34, 0.5, 0.76), ink=(0.15, 0.25, 0.5), lid=(0.2, 0.3, 0.6),
                                     desc='An empty large glass bottle with a screw cap, for flaxseed oil. Fill it at the oil press.'),
    'kitchen_oil_bottle_vegetable_750ml': dict(shape='bottle', name='Vegetable Oil Bottle', cap=0.75, kg=0.4, price=3, size=(0.038, 0.25), tag='liquid_vegetable_oil', lines=['VEGETABLE', 'OIL'], sub='PURE',
                                     color=(0.92, 0.55, 0.08), ink=(0.55, 0.28, 0.0), lid=(0.8, 0.12, 0.1),
                                     desc='An empty glass bottle with a screw cap, for vegetable oil (blended from the pressed oils). Fill it at the oil press.'),
    'kitchen_oil_bottle_vegetable_2l': dict(shape='bottle', name='Large Vegetable Oil Bottle', cap=2.0, kg=0.6, price=5, size=(0.056, 0.31), tag='liquid_vegetable_oil', lines=['VEGETABLE', 'OIL'], sub='PURE',
                                     color=(0.92, 0.55, 0.08), ink=(0.55, 0.28, 0.0), lid=(0.8, 0.12, 0.1),
                                     desc='An empty large glass bottle with a screw cap, for vegetable oil (blended from the pressed oils). Fill it at the oil press.'),
    'kitchen_jar_jam_350ml': dict(shape='jar', name='Jam Jar', cap=0.35, kg=0.18, price=2, size=(0.04, 0.095), tag='#jam', lines=['JAM'], sub='HOMEMADE',
                                  color=(0.78, 0.12, 0.22), ink=(0.50, 0.05, 0.12), lid=(0.85, 0.80, 0.70),
                                  desc='An empty small glass jar with a lid, for jam. Fill it on the stove.'),
    'kitchen_jar_jam_900ml': dict(shape='jar', name='Large Jam Jar', cap=0.9, kg=0.3, price=3, size=(0.056, 0.14), tag='#jam', lines=['JAM'], sub='HOMEMADE',
                                  color=(0.78, 0.12, 0.22), ink=(0.50, 0.05, 0.12), lid=(0.85, 0.80, 0.70),
                                  desc='An empty large glass jar with a lid, for jam. Fill it on the stove.'),
}


def paint(item):
    """The label wrap texture (system Python: PIL): the panel in the middle, the product's colour round it."""
    from PIL import Image, ImageDraw, ImageFont
    d = ITEMS[item]
    body = tuple(int(c * 255) for c in d['color'])
    ink = tuple(int(c * 255) for c in d['ink'])
    cream = tuple(int(c * 255) for c in CREAM)
    W, H = 1536, 640
    im = Image.new('RGB', (W, H), body)
    dr = ImageDraw.Draw(im)
    font = lambda s: ImageFont.truetype('arialbd.ttf', s)
    px0, px1, py0, py1 = W // 2 - 330, W // 2 + 330, 70, H - 70
    dr.rounded_rectangle((px0, py0, px1, py1), radius=40, fill=cream, outline=ink, width=10)
    pw = px1 - px0 - 190
    sizes = []
    for line in d['lines']:
        s = 260
        while dr.textlength(line, font=font(s)) > pw:
            s -= 4
        sizes.append(min(s, 200 if len(d['lines']) > 1 else 260))
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
    dr.rectangle((0, 0, W, 34), fill=ink)
    dr.rectangle((0, H - 34, W, H), fill=ink)
    os.makedirs(TEX, exist_ok=True)
    im.save(os.path.join(TEX, item + '.png'))


# ------------------------------------------------------------------ Blender side

def build(item):
    import bpy
    import bmesh
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

    glass = bpy.data.materials.new(item + '_glass')
    glass.use_nodes = True
    b = glass.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.78, 0.92, 0.88, 1.0)
    b.inputs['Roughness'].default_value = 0.08
    b.inputs['Alpha'].default_value = 0.38
    try:
        glass.surface_render_method = 'BLENDED'
    except Exception:
        pass
    lid_m = L.material(item + '_lid', d['lid'], 0.35, 0.5)
    label_m = bpy.data.materials.new(item + '_label')
    label_m.use_nodes = True
    bsdf = label_m.node_tree.nodes['Principled BSDF']
    bsdf.inputs['Roughness'].default_value = 0.6
    node = label_m.node_tree.nodes.new('ShaderNodeTexImage')
    node.image = bpy.data.images.load(os.path.join(TEX, item + '.png'))
    label_m.node_tree.links.new(node.outputs['Color'], bsdf.inputs['Base Color'])

    def cyl(r0, r1, z0, z1, m, label=False, seg=40, caps=True):
        before = set(bm.faces)
        ring0 = [bm.verts.new((r0 * math.cos(2 * math.pi * k / seg), r0 * math.sin(2 * math.pi * k / seg), z0)) for k in range(seg)]
        ring1 = [bm.verts.new((r1 * math.cos(2 * math.pi * k / seg), r1 * math.sin(2 * math.pi * k / seg), z1)) for k in range(seg)]
        side = [bm.faces.new((ring0[k], ring0[(k + 1) % seg], ring1[(k + 1) % seg], ring1[k])) for k in range(seg)]
        ends = []
        if caps:
            ends.append(bm.faces.new(ring1[::-1]))
            ends.append(bm.faces.new(ring0))
        new = [f for f in bm.faces if f not in before]
        bmesh.ops.recalc_face_normals(bm, faces=new)
        for f in side:
            f.smooth = True
            f.material_index = mi(label_m if label else m)
            us = []
            for lp in f.loops:
                a = math.atan2(lp.vert.co.y, lp.vert.co.x)                           # -pi/2 is the front (-Y)
                us.append(((a + math.pi / 2) / (2 * math.pi) + 0.5 + 35.0 / 360.0) % 1.0)   # the panel is turned 35 degrees toward the icon camera
            if max(us) - min(us) > 0.5:
                us = [u + 1.0 if u < 0.5 else u for u in us]
            for lp, u in zip(f.loops, us):
                lp[uv].uv = (u, (lp.vert.co.z - z0) / (z1 - z0)) if label else (0.0, 0.0)
        for f in ends:
            f.material_index = mi(m)
            for lp in f.loops:
                lp[uv].uv = (0.0, 0.0)

    r, h = d['size']
    if d['shape'] == 'bottle':
        cyl(r, r, 0.0, h * 0.58, glass, label=True)                      # the body, the label round it
        cyl(r, r * 0.36, h * 0.58, h * 0.80, glass)                      # the shoulder
        cyl(r * 0.36, r * 0.36, h * 0.80, h * 0.93, glass)               # the neck
        cyl(r * 0.43, r * 0.43, h * 0.93, h, lid_m, seg=20)              # the screw cap
    else:
        cyl(r, r, 0.0, h * 0.84, glass, label=True)                      # the jar, the label round it
        cyl(r * 0.96, r * 0.96, h * 0.84, h * 0.88, glass)               # the glass above the label
        cyl(r * 1.04, r * 1.04, h * 0.88, h, lid_m)                      # the lid
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
    write_manifest(item, tris, dims)
    print('built', item, tris, 'tris', '%.3f x %.3f x %.3f' % dims, 'zmin %.4f' % lo.z)


def write_manifest(item, tris, dims):
    d = ITEMS[item]
    w, dp, h = dims
    m = {
        '$schema': 'https://homesteader.game/schemas/item_v1.json',
        'id': item, 'name': d['name'], 'category': 'kitchen', 'description': d['desc'], 'icon': item + '.png',
        'properties': {
            'weight_kg': d['kg'], 'max_stack_size': 20, 'base_value': d['price'], 'is_consumable': False,
            'footprint': '%.2fm W x %.2fm D x %.2fm H' % (w, dp, h),
            'happiness_modifier': 0, 'thirst_restore': 0, 'energy_restore': 0, 'stamina_restore': 0, 'wellness_modifier': 0,
            'placeable': True, 'is_buyable': True, 'stores': ['grocer'], 'sale_unit': 'ea',
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
        'category_fields': {'dimensions_m': {'width': round(w, 3), 'depth': round(dp, 3), 'height': round(h, 3)}, 'kitchen_kind': 'accessory', 'finish': 'glass', 'power_draw_w': 0},
        'liquid_container': dict({'capacity_l': d['cap'], 'accepts': [d['tag']]}, **({'filled_with': d['filled'], 'filled_l': d['cap']} if d.get('filled') else {})),
    }
    with open(os.path.join(OUT, item, item + '.json'), 'w', encoding='utf-8', newline=NL) as f:
        json.dump(m, f, indent=2, ensure_ascii=False)
        f.write(NL)
    with open(os.path.join(OUT, item, 'README.md'), 'w', encoding='utf-8', newline=NL) as f:
        f.write('# %s' % d['name'] + NL + NL + d['desc'] + NL + NL + 'A liquid container: it holds %s L of one liquid (%s) and keeps what is in it. Procedural model (tools/make_canning_assets.py), %d triangles.' % (d['cap'], d['tag'], tris) + NL)


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
