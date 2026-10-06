#!/usr/bin/env python3
"""
make_inverter_models.py
Builds, in code (no paid generation), the wall-mounted hybrid inverters: 3 kW, 5 kW and 10 kW (GLB, textures, icons, manifests). The detail is in TEXTURES: a printed front
(LCD readout of the AC output, load, battery and solar, buttons, status LEDs, rating plate, port and terminal labels), a fan grille and a brushed light shell; the geometry is the
body, side heatsink fins, top vents, a bottom connection panel with glands and the DC isolator.
Wall item convention (docs/ATTACHED_ITEMS.md): the BACK is the plane y = 0 (Blender), it sticks out towards -y (the game's +z), bottom at z = 0, centred on x.
Run:  python tools/make_inverter_models.py [--render] [--install]
"""
import copy
import json
import os
import random
import shutil
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ELEC = os.path.join(ROOT, "assets", "electricity")
WORK = os.path.join(ROOT, "assets", "_scratch", "inverter")

# id: (name, kw, width, height, depth, weight kg, price, fins per side, accent rgb)
UNITS = {
    "electricity_inverter_hybrid_3kw": ("Hybrid Inverter, Small", 3, 0.45, 0.55, 0.18, 20.0, 600, 5, (40, 150, 220)),
    "electricity_inverter_hybrid_5kw": ("Hybrid Inverter, Medium", 5, 0.50, 0.65, 0.20, 32.0, 1100, 6, (60, 180, 110)),
    "electricity_inverter_hybrid_10kw": ("Hybrid Inverter, Large", 10, 0.60, 0.80, 0.24, 55.0, 2400, 8, (230, 140, 40)),
}
OLD = ("electricity_inverter_hybrid_3000w",)


def font(size, bold=True):
    from PIL import ImageFont
    f = "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"
    return ImageFont.truetype(f, size) if os.path.exists(f) else ImageFont.load_default()


def mono(size):
    from PIL import ImageFont
    f = "C:/Windows/Fonts/consolab.ttf"
    return ImageFont.truetype(f, size) if os.path.exists(f) else font(size)


def make_textures():
    from PIL import Image, ImageDraw
    os.makedirs(WORK, exist_ok=True)
    random.seed(5)
    shell = Image.new("RGB", (512, 512), (206, 210, 216))
    px = shell.load()
    for y in range(512):
        v = random.randint(-7, 7)
        for x in range(512):
            c = 206 + v + random.randint(-3, 3)
            px[x, y] = (c, c + 3, c + 8)
    shell.save(os.path.join(WORK, "shell.png"))
    fin = Image.new("RGB", (256, 256), (150, 154, 162))
    fp = fin.load()
    for y in range(256):
        v = random.randint(-6, 6)
        for x in range(256):
            c = 150 + v + random.randint(-3, 3)
            fp[x, y] = (c, c + 2, c + 8)
    fin.save(os.path.join(WORK, "fin.png"))

    for uid, (name, kw, w, h, d, kg, price, fins, accent) in UNITS.items():
        W = 1024
        H = int(W * (h - 0.02) / (w - 0.02))
        img = Image.new("RGB", (W, H), (20, 22, 26))
        dr = ImageDraw.Draw(img)
        s = W / 1024.0
        dr.rectangle([0, 0, W - 1, H - 1], outline=(80, 84, 92), width=6)
        dr.rectangle([0, 0, W, int(H * 0.075)], fill=accent)
        dr.text((W // 2, int(H * 0.038)), "HOMESTEAD HYBRID INVERTER", font=font(int(52 * s)), fill=(255, 255, 255), anchor="mm")
        # the LCD
        lx0, ly0, lx1, ly1 = int(W * 0.07), int(H * 0.10), int(W * 0.93), int(H * 0.36)
        dr.rectangle([lx0 - 10, ly0 - 10, lx1 + 10, ly1 + 10], fill=(8, 9, 11))
        dr.rectangle([lx0, ly0, lx1, ly1], fill=(16, 48, 66))
        green = (130, 230, 255)
        dim = (70, 140, 170)
        rows = (("PV", "%.1f kW" % (kw * 0.62)), ("BAT", "52.4 V  %d%%" % 87), ("LOAD", "%.2f kW" % (kw * 0.44)), ("AC OUT", "230 V  50 Hz"))
        for i, (a, b) in enumerate(rows):
            y = ly0 + 22 + i * (ly1 - ly0 - 30) / 4.0
            dr.text((lx0 + 26, y), a, font=mono(int(40 * s)), fill=dim, anchor="la")
            dr.text((lx1 - 26, y), b, font=mono(int(46 * s)), fill=green, anchor="ra")
        # buttons
        for i, label in enumerate(("ESC", "UP", "DOWN", "OK")):
            cx = int(W * (0.16 + i * 0.23))
            cy = int(H * 0.435)
            dr.ellipse([cx - 46, cy - 46, cx + 46, cy + 46], fill=(40, 44, 52), outline=(96, 102, 114), width=5)
            dr.text((cx, cy), {"ESC": "x", "UP": "^", "DOWN": "v", "OK": "OK"}[label], font=font(int(42 * s)), fill=(220, 224, 232), anchor="mm")
            dr.text((cx, cy + 68), label, font=font(int(26 * s), False), fill=(150, 156, 168), anchor="mm")
        # status LEDs
        leds = (("PV", (60, 220, 100)), ("BAT", (60, 220, 100)), ("GRID", (60, 140, 230)), ("INV", (60, 220, 100)), ("FAULT", (90, 50, 40)))
        for i, (label, col) in enumerate(leds):
            cx = int(W * (0.12 + i * 0.19))
            cy = int(H * 0.53)
            dr.ellipse([cx - 15, cy - 15, cx + 15, cy + 15], fill=col, outline=(30, 30, 30), width=3)
            dr.text((cx, cy + 36), label, font=font(int(24 * s)), fill=(190, 196, 208), anchor="mm")
        # the fan grille
        gx0, gy0, gx1, gy1 = int(W * 0.12), int(H * 0.585), int(W * 0.88), int(H * 0.725)
        dr.rectangle([gx0, gy0, gx1, gy1], fill=(12, 13, 15), outline=(70, 74, 82), width=3)
        for yy in range(gy0 + 10, gy1 - 6, 14):
            dr.line([(gx0 + 12, yy), (gx1 - 12, yy)], fill=(40, 44, 50), width=5)
        # the rating plate
        px0, py0, px1, py1 = int(W * 0.07), int(H * 0.745), int(W * 0.93), int(H * 0.855)
        dr.rectangle([px0, py0, px1, py1], fill=(206, 208, 212))
        dr.text((px0 + 24, (py0 + py1) // 2), "%d kW" % kw, font=font(int(86 * s)), fill=(20, 20, 20), anchor="lm")
        dr.text((px1 - 24, py0 + 32), "ON-GRID / OFF-GRID / HYBRID", font=font(int(30 * s)), fill=(30, 30, 30), anchor="rm")
        dr.text((px1 - 24, py1 - 28), "PV 500 V   BAT 48 V   %d kVA" % kw, font=font(int(30 * s), False), fill=(50, 50, 50), anchor="rm")
        # the connection row
        ty = int(H * 0.905)
        labels = ("PV", "BATT", "AC IN", "AC OUT", "COM")
        cols = ((220, 90, 40), (220, 60, 50), (60, 130, 220), (60, 190, 100), (150, 150, 160))
        for i, (t, c) in enumerate(zip(labels, cols)):
            cx = int(W * (0.12 + i * 0.19))
            dr.rectangle([cx - 56, ty - 21, cx + 56, ty + 21], fill=c)
            dr.text((cx, ty), t, font=font(int(30 * s)), fill=(255, 255, 255), anchor="mm")
        dr.text((W // 2, int(H * 0.965)), "ISOLATE ALL SOURCES BEFORE SERVICE", font=font(int(26 * s), False), fill=(150, 156, 168), anchor="mm")
        img.save(os.path.join(WORK, uid + "_front.png"))


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
            bmesh.ops.bevel(bm, geom=list(bm.verts) + list(bm.edges) + list(bm.faces), offset=bevel, offset_type='OFFSET', segments=2, profile=0.5, affect='EDGES')
        for v in bm.verts:
            v.co += Vector(centre)
        return put(name, bm, mat)

    def cylinder(name, radius, length, centre, mat, segments=10, axis="z"):
        bm = bmesh.new()
        bm.loops.layers.uv.verify()
        bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segments, radius1=radius, radius2=radius, depth=length)
        if axis == "y":
            bmesh.ops.transform(bm, matrix=Matrix.Rotation(math.pi / 2, 4, 'X'), verts=bm.verts)
        for v in bm.verts:
            v.co += Vector(centre)
        return put(name, bm, mat)

    def quad_front(name, cx, cz, w, h, y, mat):
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
    for uid, (name, kw, w, h, d, kg, price, fins, accent) in UNITS.items():
        reset()
        shell = material("Shell", (1, 1, 1), 0.5, 0.45, tex=os.path.join(WORK, "shell.png"))
        finm = material("Heatsink", (1, 1, 1), 0.6, 0.5, tex=os.path.join(WORK, "fin.png"))
        front = material("Front", (1, 1, 1), 0.1, 0.3, tex=os.path.join(WORK, uid + "_front.png"))
        dark = material("Dark", (0.03, 0.03, 0.035), 0.3, 0.5)
        redm = material("Isolator", (0.85, 0.12, 0.08), 0.0, 0.5)
        yellow = material("IsolatorKnob", (0.95, 0.78, 0.05), 0.0, 0.5)
        accm = material("Accent", tuple(c / 255.0 for c in accent), 0.0, 0.5)
        foot = 0.09                                    # the connection panel below the main body
        body_h = h - foot
        parts = []
        parts.append(box("Shell", (w * 0.80, d * 0.9, body_h), (0, -d * 0.45, foot + body_h / 2), shell, 0.008))
        parts.append(box("FrontFrame", (w * 0.80 + 0.004, 0.002, body_h + 0.004), (0, -d * 0.9, foot + body_h / 2), dark, 0.001))
        parts.append(quad_front("Front", 0, foot + body_h / 2, w * 0.80 - 0.014, body_h - 0.016, -d * 0.9 - 0.0025, front))
        parts.append(box("AccentStrip", (w * 0.80, 0.004, 0.008), (0, -d * 0.9 - 0.0015, foot + body_h - 0.002), accm))
        # heatsink fins down both sides
        fin_h = body_h * 0.86
        span = w * 0.095
        for sx in (-1, 1):
            parts.append(box("FinBase", (0.006, d * 0.9, fin_h), (sx * (w * 0.40 + 0.003), -d * 0.45, foot + body_h * 0.5), finm, 0.001))
            for i in range(fins):
                fz = foot + body_h * 0.5 - fin_h / 2 + (i + 0.5) * fin_h / fins
                parts.append(box("Fin", (span, d * 0.86, 0.0055), (sx * (w * 0.40 + 0.006 + span / 2), -d * 0.45, fz), finm))
        # top vents
        for i in range(4):
            parts.append(box("Vent", (w * 0.5, d * 0.5, 0.004), (0, -d * 0.45, foot + body_h + 0.001 + 0.0), dark) if False else
                         box("Vent%d" % i, (w * 0.5, 0.012, 0.004), (0, -d * 0.2 - i * d * 0.16, foot + body_h + 0.0005), dark))
        # the connection panel: a lower box with the glands and the DC isolator
        parts.append(box("ConnBox", (w * 0.80, d * 0.86, foot - 0.012), (0, -d * 0.45, (foot - 0.012) / 2 + 0.012), dark, 0.005))
        n = 6
        for i in range(n):
            x = (-0.38 + i * 0.76 / (n - 1)) * w * 0.80
            parts.append(cylinder("Gland%d" % i, 0.0105, 0.022, (x * 0.9, -d * 0.45, 0.001), dark, 8))
        parts.append(box("IsolatorPlate", (0.085, 0.012, 0.075), (w * 0.28, -d * 0.9 - 0.004, foot * 0.55), redm, 0.003))
        parts.append(box("IsolatorKnob", (0.06, 0.02, 0.028), (w * 0.28, -d * 0.9 - 0.014, foot * 0.55), yellow, 0.004))
        # the wall bracket
        parts.append(box("Bracket", (w * 0.7, 0.012, 0.045), (0, 0.006, foot + body_h - 0.07), shell, 0.002))
        parts.append(box("BracketLow", (w * 0.7, 0.012, 0.045), (0, 0.006, foot + 0.06), shell, 0.002))
        export(parts, os.path.join(out_dir, uid + ".glb"))
        results[uid] = tris()

    with open(os.path.join(out_dir, "tris.txt"), "w") as f:
        for k, v in results.items():
            f.write("%s %d\n" % (k, v))


def find_blender():
    for p in (r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe", "blender"):
        if os.path.exists(p) or p == "blender":
            return p
    return "blender"


def retry(fn, *a):
    for _ in range(30):
        try:
            return fn(*a)
        except OSError:
            time.sleep(1.5)
    raise SystemExit("io failed")


def install(out):
    tris = dict(l.split() for l in open(os.path.join(out, "tris.txt")).read().strip().splitlines())
    base = json.load(open(os.path.join(ELEC, "electricity_inverter_hybrid_3000w", "electricity_inverter_hybrid_3000w.json"), encoding="utf-8"))
    for uid, (name, kw, w, h, d, kg, price, fins, accent) in UNITS.items():
        folder = os.path.join(ELEC, uid)
        os.makedirs(folder, exist_ok=True)
        m = copy.deepcopy(base)
        m["id"] = uid
        m["name"] = name
        m["icon"] = uid + ".png"
        m["description"] = ("A %d kW hybrid inverter: it turns the battery bank's direct current into household power, takes solar and the grid or a generator, and charges the batteries. "
                            "It has a finned heat sink, a fan grille, an LCD readout and a DC isolator. It mounts on a building's wall: aim at a wall of a finished building and left click." % kw)
        pr = m["properties"]
        pr["weight_kg"] = kg
        pr["base_value"] = price
        pr["max_stack_size"] = 5
        pr["placeable"] = False
        pr["attach_surface"] = "wall"
        pr["attach_side"] = "either"
        pr["stores"] = ["voltvision"]
        pr["sale_unit"] = "ea"
        pr["footprint"] = "%.2fm W x %.2fm D x %.2fm H" % (w, d, h)
        m["models"] = [{"file": uid + ".glb", "format": "glb", "dimensions_m": {"x": w, "y": h, "z": d}, "triangles": int(tris[uid])}]
        text = "Inverts battery power to AC: %d kW continuous (hybrid: solar, grid or generator in)" % kw
        m["utilities"]["electricity"] = {"metric": text, "details": text}
        m["category_fields"]["dimensions_m"] = {"width": w, "depth": d, "height": h}
        m["category_fields"]["max_power_w"] = kw * 1000
        for f in os.listdir(folder):
            if f.endswith((".obj", ".mtl")) or (f.endswith(".glb") and f != uid + ".glb"):
                os.remove(os.path.join(folder, f))
        retry(shutil.copy, os.path.join(out, uid + ".glb"), os.path.join(folder, uid + ".glb"))
        png = os.path.join(WORK, uid + ".png")
        if os.path.exists(png):
            retry(shutil.copy, png, os.path.join(folder, uid + ".png"))
        text = (json.dumps(m, indent=2, ensure_ascii=False) + "\n").replace("\n", "\r\n")
        retry(lambda: open(os.path.join(folder, uid + ".json"), "w", encoding="utf-8", newline="").write(text))
        retry(lambda: open(os.path.join(folder, "README.md"), "w", encoding="utf-8", newline="").write(
            "# %s\n\n**Item ID:** `%s`  \n**Category:** `electricity`  \n**Icon:** ![%s](%s.png)\n\n%s\n" % (name, uid, name, uid, m["description"])))
    for old in OLD:
        dd = os.path.join(ELEC, old)
        if os.path.isdir(dd):
            shutil.rmtree(dd)


def main():
    if "--blender" in sys.argv:
        blender_main(sys.argv[sys.argv.index("--") + 1])
        return
    make_textures()
    out = os.path.join(WORK, "glb")
    os.makedirs(out, exist_ok=True)
    r = subprocess.run([find_blender(), "--background", "--python", os.path.abspath(__file__), "--", out, "--blender"], capture_output=True, text=True)
    print((r.stdout + r.stderr)[-800:])
    print(open(os.path.join(out, "tris.txt")).read())
    if "--render" in sys.argv:
        for uid in UNITS:
            subprocess.run([sys.executable, os.path.join(ROOT, "tools", "render_icon_from_model.py"), os.path.join(out, uid + ".glb"), os.path.join(WORK, uid + ".png")], check=True, capture_output=True)
    if "--install" in sys.argv:
        install(out)
        print("installed")


if __name__ == "__main__":
    main()
