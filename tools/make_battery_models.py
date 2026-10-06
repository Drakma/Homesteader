#!/usr/bin/env python3
"""
make_battery_models.py
Builds, in code (no paid generation), the GLB models, label textures and icons for:
  - 12 V batteries: LiFePO4, AGM and NMC (1200 Wh class)
  - 48 V 3U rack-mount batteries: LiFePO4, AGM and NMC
  - an empty 18U battery rack that takes six rack batteries (they show as real models in their slots: container.slot_pitch_m)
Run:  python tools/make_battery_models.py   (textures, Blender export, then icons are rendered by the caller)
Conventions: GLB, metres, pivot at the bottom centre; the front faces -y in Blender (the game's +z).
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(ROOT, "assets", "_scratch", "batteries")

RACK_U = 0.1334          # 3U: the pitch of one rack battery
MODULE_H = 0.129         # a 3U module (a hair under 3U, so neighbours do not touch)
MODULE_W, MODULE_D = 0.483, 0.45
SLOT_START = 0.09        # height of the first slot above the bottom of the rack's model
SLOTS = 6

BATT12 = {
    # id: (name, w, d, h, body rgb, lid rgb, accent rgb, chemistry text, volts/Ah text, energy text, handle kind)
    "electricity_battery_12v_lifepo4_1200wh": ("12V LiFePO4 1200Wh Battery", 0.33, 0.17, 0.21, (0.10, 0.11, 0.14), (0.17, 0.18, 0.22), (30, 100, 210), "LiFePO4", "12.8V 100Ah", "1280Wh", "recess"),
    "electricity_battery_12v_agm_1200wh": ("12V AGM 1200Wh Battery", 0.33, 0.17, 0.22, (0.04, 0.04, 0.045), (0.20, 0.20, 0.21), (230, 150, 20), "AGM DEEP CYCLE", "12V 100Ah", "1200Wh", "bar"),
    "electricity_battery_12v_nmc_1200wh": ("12V NMC 1200Wh Battery", 0.30, 0.17, 0.19, (0.80, 0.82, 0.84), (0.50, 0.52, 0.55), (40, 170, 90), "NMC LI-ION", "11.1V 108Ah", "1200Wh", "recess"),
}
RACKMOD = {
    # id: (name, accent rgb, body rgb, chemistry, volts/Ah, energy)
    "electricity_battery_rack_lifepo4_48v": ("48V LiFePO4 Rack Battery", (30, 100, 210), (0.12, 0.14, 0.20), "LiFePO4", "51.2V 100Ah", "5.12 kWh"),
    "electricity_battery_rack_agm_48v": ("48V AGM Rack Battery", (230, 150, 20), (0.05, 0.05, 0.05), "AGM", "48V 100Ah", "4.8 kWh"),
    "electricity_battery_rack_nmc_48v": ("48V NMC Rack Battery", (40, 170, 90), (0.70, 0.72, 0.74), "NMC", "46.8V 105Ah", "4.9 kWh"),
}
RACK_ID = "electricity_battery_rack_empty"


def font(size, bold=True):
    from PIL import ImageFont
    for f in (r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf", r"C:\Windows\Fonts\segoeuib.ttf"):
        if os.path.exists(f):
            return ImageFont.truetype(f, size)
    return ImageFont.load_default()


def make_textures():
    from PIL import Image, ImageDraw
    os.makedirs(WORK, exist_ok=True)
    for bid, (name, w, d, h, body, lid, accent, chem, va, wh, _hk) in BATT12.items():
        W, H = 768, 512
        light = sum(body) > 1.5
        img = Image.new("RGB", (W, H), (236, 236, 232) if not light else (250, 250, 250))
        dr = ImageDraw.Draw(img)
        dr.rectangle([0, 0, W, 120], fill=accent)
        dr.text((W // 2, 62), chem, font=font(66), fill=(255, 255, 255), anchor="mm")
        dr.text((28, 200), va, font=font(80), fill=(20, 20, 20), anchor="lm")
        dr.text((28, 292), wh + "  DEEP CYCLE", font=font(50, False), fill=(40, 40, 40), anchor="lm")
        dr.rectangle([0, 372, W, H], fill=(245, 200, 20))
        dr.text((W // 2, 442), "CAUTION  HIGH CURRENT", font=font(52), fill=(20, 20, 20), anchor="mm")
        dr.rectangle([2, 2, W - 3, H - 3], outline=(60, 60, 60), width=5)
        img.save(os.path.join(WORK, bid + "_label.png"))
    for rid, (name, accent, body, chem, va, kwh) in RACKMOD.items():
        W, H = 1024, 500
        img = Image.new("RGB", (W, H), (28, 30, 34))
        dr = ImageDraw.Draw(img)
        dr.rectangle([0, 0, 24, H], fill=accent)
        dr.text((70, 80), chem, font=font(110), fill=(255, 255, 255), anchor="lm")
        dr.text((70, 195), va, font=font(66), fill=(220, 224, 230), anchor="lm")
        dr.text((70, 275), kwh + "  48V RACK", font=font(52, False), fill=(190, 196, 205), anchor="lm")
        # a state-of-charge bar: five lit cells
        for i in range(5):
            x0 = 70 + i * 120
            dr.rectangle([x0, 350, x0 + 100, 420], fill=(60, 200, 90) if i < 4 else (40, 60, 44))
        dr.text((W - 40, 460), "SOC", font=font(40, False), fill=(150, 156, 165), anchor="rm")
        dr.rectangle([2, 2, W - 3, H - 3], outline=(80, 84, 92), width=4)
        img.save(os.path.join(WORK, rid + "_label.png"))


def blender_main(out_dir):
    import bpy
    import bmesh
    import math
    from mathutils import Matrix, Vector

    def reset():
        bpy.ops.wm.read_factory_settings(use_empty=True)

    def material(name, rgb, metallic=0.0, rough=0.5, tex=None):
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        b = m.node_tree.nodes["Principled BSDF"]
        b.inputs["Base Color"].default_value = (rgb[0], rgb[1], rgb[2], 1.0)
        b.inputs["Metallic"].default_value = metallic
        b.inputs["Roughness"].default_value = rough
        if tex:
            node = m.node_tree.nodes.new("ShaderNodeTexImage")
            node.image = bpy.data.images.load(tex)
            uvn = m.node_tree.nodes.new("ShaderNodeUVMap")
            uvn.uv_map = "UVMap"
            m.node_tree.links.new(uvn.outputs["UV"], node.inputs["Vector"])
            m.node_tree.links.new(node.outputs["Color"], b.inputs["Base Color"])
        return m

    def put(name, bm, mat):
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        bm.free()
        while len(me.uv_layers) > 1:
            me.uv_layers.remove(me.uv_layers[len(me.uv_layers) - 1])
        if len(me.uv_layers) == 1:
            me.uv_layers[0].name = "UVMap"
        ob = bpy.data.objects.new(name, me)
        bpy.context.collection.objects.link(ob)
        me.materials.append(mat)
        return ob

    def box(name, size, centre, mat, bevel=0.0):
        bm = bmesh.new()
        bm.loops.layers.uv.verify()
        bmesh.ops.create_cube(bm, size=1.0)
        for v in bm.verts:
            v.co.x *= size[0]
            v.co.y *= size[1]
            v.co.z *= size[2]
        if bevel > 0:
            bmesh.ops.bevel(bm, geom=list(bm.verts) + list(bm.edges) + list(bm.faces), offset=bevel, offset_type='OFFSET', segments=1, profile=0.5, affect='EDGES')
        for v in bm.verts:
            v.co += Vector(centre)
        return put(name, bm, mat)

    def cylinder(name, radius, length, axis, centre, mat, segments=10):
        bm = bmesh.new()
        bm.loops.layers.uv.verify()
        bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segments, radius1=radius, radius2=radius, depth=length)
        if axis == "x":
            bmesh.ops.transform(bm, matrix=Matrix.Rotation(math.pi / 2, 4, 'Y'), verts=bm.verts)
        elif axis == "y":
            bmesh.ops.transform(bm, matrix=Matrix.Rotation(math.pi / 2, 4, 'X'), verts=bm.verts)
        for v in bm.verts:
            v.co += Vector(centre)
        return put(name, bm, mat)

    def quad_front(name, cx, cz, w, h, y, mat):
        """A textured quad facing the front (-y)."""
        bm = bmesh.new()
        vs = [bm.verts.new(c) for c in [(cx - w / 2, y, cz - h / 2), (cx + w / 2, y, cz - h / 2), (cx + w / 2, y, cz + h / 2), (cx - w / 2, y, cz + h / 2)]]
        f = bm.faces.new(vs)
        uv = bm.loops.layers.uv.new("UVMap")
        for loop, (u, v) in zip(f.loops, [(0, 0), (1, 0), (1, 1), (0, 1)]):
            loop[uv].uv = (u, v)
        return put(name, bm, mat)

    def export(objs, path):
        bpy.ops.object.select_all(action='DESELECT')
        for o in objs:
            o.select_set(True)
        bpy.context.view_layer.objects.active = objs[0]
        bpy.ops.object.join()
        bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True, export_apply=True, export_yup=True)

    def tris():
        return sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in bpy.data.objects if o.type == 'MESH')

    results = {}
    red = (0.75, 0.05, 0.05)
    black = (0.03, 0.03, 0.035)

    # ---------------------------------------------------------------- 12 V batteries
    for bid, (name, w, d, h, body, lid, accent, chem, va, wh, hk) in BATT12.items():
        reset()
        mb = material("Case", body, 0.0, 0.55)
        ml = material("Lid", lid, 0.0, 0.5)
        mlabel = material("Label", (1, 1, 1), 0.0, 0.6, tex=os.path.join(WORK, bid + "_label.png"))
        macc = material("Accent", tuple(c / 255.0 for c in accent), 0.0, 0.5)
        mred = material("Red", red, 0.0, 0.5)
        mblk = material("Black", black, 0.0, 0.5)
        mmet = material("Terminal", (0.7, 0.72, 0.75), 0.9, 0.3)
        parts = []
        lid_h = h * 0.12
        parts.append(box("Case", (w, d, h - lid_h), (0, 0, (h - lid_h) / 2), mb, 0.008))
        parts.append(box("Lid", (w * 0.97, d * 0.96, lid_h), (0, 0, h - lid_h / 2), ml, 0.004))
        parts.append(quad_front("Label", 0, h * 0.42, w * 0.80, h * 0.50, -d / 2 - 0.0008, mlabel))
        parts.append(box("AccentBand", (w * 0.97, 0.003, 0.012), (0, -d / 2 - 0.0015, h - lid_h - 0.008), macc))
        for sx, mat in ((-1, mred), (1, mblk)):
            x = sx * w * 0.30
            parts.append(box("Cap%d" % sx, (0.036, 0.036, 0.012), (x, d * 0.18, h + 0.006), mat, 0.003))
            parts.append(cylinder("Post%d" % sx, 0.010, 0.02, "z", (x, d * 0.18, h + 0.02), mmet, 8))
            parts.append(cylinder("Nut%d" % sx, 0.0075, 0.006, "z", (x, d * 0.18, h + 0.033), mmet, 6))
        if hk == "bar":
            for sx in (-1, 1):
                parts.append(box("HandlePost%d" % sx, (0.014, 0.014, 0.035), (sx * w * 0.18, -d * 0.12, h + 0.0175), mb, 0.002))
            parts.append(box("HandleBar", (w * 0.36 + 0.014, 0.018, 0.014), (0, -d * 0.12, h + 0.042), mb, 0.003))
        else:
            for sx in (-1, 1):
                parts.append(box("Grip%d" % sx, (0.006, d * 0.45, 0.03), (sx * (w / 2 + 0.001), 0, h * 0.68), mb, 0.002))
        export(parts, os.path.join(out_dir, bid + ".glb"))
        results[bid] = tris()

    # ---------------------------------------------------------------- 3U rack batteries (pivot: bottom centre, front -y)
    W, D, H = MODULE_W, MODULE_D, MODULE_H
    for rid, (name, accent, body, chem, va, kwh) in RACKMOD.items():
        reset()
        mb = material("Case", body, 0.2, 0.5)
        mfront = material("Front", (0.12, 0.13, 0.15), 0.3, 0.45)
        mlabel = material("Label", (1, 1, 1), 0.0, 0.5, tex=os.path.join(WORK, rid + "_label.png"))
        macc = material("Accent", tuple(c / 255.0 for c in accent), 0.0, 0.5)
        mred = material("Red", red, 0.0, 0.5)
        mblk = material("Black", black, 0.0, 0.5)
        mmet = material("Metal", (0.7, 0.72, 0.75), 0.9, 0.3)
        morange = material("Switch", (0.95, 0.45, 0.05), 0.0, 0.5)
        parts = []
        parts.append(box("Body", (W - 0.046, D, H - 0.006), (0, 0, H / 2), mb, 0.004))
        parts.append(box("FrontPanel", (W, 0.012, H), (0, -D / 2 - 0.006, H / 2), mfront, 0.002))
        parts.append(box("AccentStripe", (W - 0.02, 0.002, 0.006), (0, -D / 2 - 0.013, H - 0.008), macc))
        parts.append(quad_front("Label", -0.0735, H * 0.47, 0.215, 0.092, -D / 2 - 0.0135, mlabel))
        for sx in (-1, 1):
            for zf in (0.2, 0.8):
                parts.append(cylinder("EarHole", 0.0045, 0.002, "y", (sx * (W / 2 - 0.0095), -D / 2 - 0.0125, H * zf), mblk, 8))
            # a handle at each ear: a bar on two standoffs
            hx = sx * (W / 2 - 0.026)
            parts.append(box("Handle", (0.012, 0.012, 0.074), (hx, -D / 2 - 0.036, H / 2), mmet, 0.002))
            for zz in (H * 0.12, H * 0.88):
                parts.append(box("Standoff", (0.012, 0.026, 0.012), (hx, -D / 2 - 0.025, zz), mmet, 0.001))
        # terminals, comms and the breaker on the right of the front
        for x, mat in ((0.075, mred), (0.118, mblk)):
            parts.append(cylinder("Socket", 0.0105, 0.010, "y", (x, -D / 2 - 0.017, H * 0.64), mblk, 10))
            parts.append(cylinder("Ring", 0.0135, 0.004, "y", (x, -D / 2 - 0.0135, H * 0.64), mat, 10))
        parts.append(box("Breaker", (0.034, 0.012, 0.024), (0.165, -D / 2 - 0.018, H * 0.64), mblk, 0.002))
        parts.append(box("BreakerToggle", (0.014, 0.008, 0.012), (0.165, -D / 2 - 0.026, H * 0.66), morange, 0.001))
        for x in (0.075, 0.105, 0.135):
            parts.append(box("Port", (0.024, 0.006, 0.012), (x, -D / 2 - 0.015, H * 0.26), mblk, 0.001))
        parts.append(box("Vent", (W * 0.5, 0.004, 0.01), (-0.04, D / 2 + 0.001, H * 0.5), mblk))   # a rear vent slot
        export(parts, os.path.join(out_dir, rid + ".glb"))
        results[rid] = tris()

    # ---------------------------------------------------------------- the empty rack (18U, six 3U slots)
    reset()
    frame = material("Frame", (0.05, 0.055, 0.06), 0.3, 0.45)
    steel = material("Rails", (0.58, 0.60, 0.63), 0.8, 0.4)
    grill = material("Vent", (0.02, 0.02, 0.02), 0.2, 0.6)
    wheel = material("Wheel", (0.03, 0.03, 0.03), 0.0, 0.7)
    RW, RD = 0.60, 0.56
    base_top = SLOT_START
    post_h = 0.80
    top_z = base_top + post_h
    parts = []
    parts.append(box("BasePlate", (RW, RD, 0.03), (0, 0, base_top - 0.015), frame, 0.004))
    for sx in (-1, 1):
        for sy in (-1, 1):
            parts.append(box("Post", (0.04, 0.04, post_h), (sx * (RW / 2 - 0.02), sy * (RD / 2 - 0.02), base_top + post_h / 2), frame, 0.003))
            parts.append(box("Fork", (0.02, 0.045, 0.03), (sx * (RW / 2 - 0.05), sy * (RD / 2 - 0.05), 0.045), frame, 0.002))
            parts.append(cylinder("Wheel", 0.03, 0.022, "x", (sx * (RW / 2 - 0.05), sy * (RD / 2 - 0.05), 0.03), wheel, 10))
    # top and bottom ties, and the vented top
    for z in (base_top + 0.02, top_z - 0.02):
        for sy in (-1, 1):
            parts.append(box("TieX", (RW - 0.08, 0.03, 0.03), (0, sy * (RD / 2 - 0.02), z), frame, 0.002))
        for sx in (-1, 1):
            parts.append(box("TieY", (0.03, RD - 0.08, 0.03), (sx * (RW / 2 - 0.02), 0, z), frame, 0.002))
    parts.append(box("Top", (RW, RD, 0.03), (0, 0, top_z + 0.015), frame, 0.004))
    for i in range(6):
        parts.append(box("Slot", (0.04, RD * 0.55, 0.004), (-0.22 + i * 0.088, 0, top_z + 0.0305), grill))
    # front mounting rails (behind the front panels' ears)
    for sx in (-1, 1):
        parts.append(box("MountRail", (0.03, 0.012, post_h - 0.04), (sx * 0.2465, -0.222, base_top + post_h / 2), steel, 0.001))
        parts.append(box("RearRail", (0.03, 0.012, post_h - 0.04), (sx * 0.2465, 0.222, base_top + post_h / 2), steel, 0.001))
    # a support angle under every slot, both sides
    for k in range(SLOTS + 1):
        z = base_top + k * RACK_U - 0.004
        for sx in (-1, 1):
            parts.append(box("Angle", (0.016, 0.44, 0.008), (sx * 0.2265, 0, z + 0.004 if k == 0 else z), steel))
    export(parts, os.path.join(out_dir, RACK_ID + ".glb"))
    results[RACK_ID] = tris()

    with open(os.path.join(out_dir, "tris.txt"), "w") as f:
        for k, v in results.items():
            f.write("%s %d\n" % (k, v))


def find_blender():
    for p in (r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe", r"C:\Program Files\Blender Foundation\Blender 4.3\blender.exe", "blender"):
        if os.path.exists(p) or p == "blender":
            return p
    return "blender"


def main():
    if "--blender" in sys.argv:
        blender_main(sys.argv[sys.argv.index("--") + 1])
        return
    make_textures()
    out = os.path.join(WORK, "glb")
    os.makedirs(out, exist_ok=True)
    r = subprocess.run([find_blender(), "--background", "--python", os.path.abspath(__file__), "--", out, "--blender"], capture_output=True, text=True)
    print((r.stdout + r.stderr)[-1200:])
    print(open(os.path.join(out, "tris.txt")).read())


if __name__ == "__main__":
    main()
