#!/usr/bin/env python3
"""
make_wall_batteries.py
Builds, in code (no paid generation), the wall-mounted home batteries: 5, 10 and 20 kWh (GLB, label textures, icons, manifests).
Run:  python tools/make_wall_batteries.py
Wall item convention (docs/ATTACHED_ITEMS.md): the BACK is the plane y = 0 (Blender) and it sticks out towards -y (the game's +z), bottom at z = 0, centred on x.
"""
import json
import os
import shutil
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ELEC = os.path.join(ROOT, "assets", "electricity")
WORK = os.path.join(ROOT, "assets", "_scratch", "wall_batteries")

# id: (kwh, width, height, depth, weight kg, price, continuous watts)
UNITS = {
    "electricity_battery_wall_power_5kwh": (5, 0.55, 0.85, 0.14, 55.0, 3200, 3000),
    "electricity_battery_wall_power_10kwh": (10, 0.65, 1.10, 0.15, 100.0, 6000, 5000),
    "electricity_battery_wall_power_20kwh": (20, 0.75, 1.45, 0.17, 190.0, 11000, 10000),
}


def font(size, bold=True):
    from PIL import ImageFont
    for f in (r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf",):
        if os.path.exists(f):
            return ImageFont.truetype(f, size)
    return ImageFont.load_default()


def make_textures():
    from PIL import Image, ImageDraw
    os.makedirs(WORK, exist_ok=True)
    for uid, (kwh, w, h, d, kg, price, watts) in UNITS.items():
        W, H = 768, 384
        img = Image.new("RGB", (W, H), (22, 24, 28))
        dr = ImageDraw.Draw(img)
        dr.text((40, 120), "%d" % kwh, font=font(190), fill=(245, 247, 250), anchor="lm")
        tx = 40 + dr.textlength("%d" % kwh, font=font(190)) + 16
        dr.text((tx, 150), "kWh", font=font(86), fill=(120, 205, 150), anchor="lm")
        dr.text((40, 270), "HOME BATTERY", font=font(54), fill=(210, 214, 220), anchor="lm")
        dr.text((40, 330), "LiFePO4  51.2V  %.1f kW" % (watts / 1000.0), font=font(40, False), fill=(150, 156, 165), anchor="lm")
        dr.rectangle([0, 0, W, 12], fill=(60, 200, 120))
        dr.rectangle([2, 2, W - 3, H - 3], outline=(70, 74, 82), width=4)
        img.save(os.path.join(WORK, uid + "_label.png"))


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

    def cylinder(name, radius, length, centre, mat, segments=10):
        bm = bmesh.new()
        bm.loops.layers.uv.verify()
        bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segments, radius1=radius, radius2=radius, depth=length)
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
    for uid, (kwh, w, h, d, kg, price, watts) in UNITS.items():
        reset()
        shell = material("Shell", (0.90, 0.91, 0.93), 0.2, 0.35)
        face = material("Face", (0.07, 0.075, 0.085), 0.4, 0.25)
        label = material("Label", (1, 1, 1), 0.0, 0.4, tex=os.path.join(WORK, uid + "_label.png"))
        led = material("Led", (0.2, 0.9, 0.45), 0.0, 0.4)
        dark = material("Dark", (0.03, 0.03, 0.035), 0.3, 0.5)
        metal = material("Metal", (0.62, 0.64, 0.67), 0.9, 0.35)
        yellow = material("Isolator", (0.95, 0.75, 0.05), 0.0, 0.5)
        red = material("Red", (0.75, 0.08, 0.06), 0.0, 0.5)
        foot = 0.14                       # the wiring box under the unit
        body_h = h - foot
        parts = []
        parts.append(box("Shell", (w, d, body_h), (0, -d / 2, foot + body_h / 2), shell, 0.02))
        parts.append(box("Face", (w - 0.05, 0.006, body_h - 0.05), (0, -d - 0.001, foot + body_h / 2), face, 0.012))
        # the printed label, high on the face
        lw = w * 0.62
        parts.append(quad_front("Label", w * 0.07, foot + body_h * 0.78, lw, lw * 0.5, -d - 0.0045, label))
        # status strip(s) down the left of the face
        strips = 2 if kwh >= 20 else 1
        for i in range(strips):
            parts.append(box("Led%d" % i, (0.012, 0.004, body_h * 0.5), (-w / 2 + 0.055 + i * 0.03, -d - 0.005, foot + body_h * 0.4), led))
        # vents along the top edge
        for i in range(3 if kwh < 20 else 5):
            parts.append(box("Vent%d" % i, (w * 0.5, 0.004, 0.008), (0, -d - 0.004, foot + body_h - 0.028 - i * 0.016), dark))
        # the wiring box: an isolator and cable glands going down
        parts.append(box("WiringBox", (w * 0.78, d * 0.9, foot - 0.01), (0, -d * 0.55, (foot - 0.01) / 2 + 0.01), metal, 0.01))
        parts.append(box("IsolatorPlate", (0.07, 0.012, 0.06), (w * 0.26, -d * 0.55 - d * 0.45 - 0.006, foot * 0.5), dark, 0.003))
        parts.append(box("IsolatorKnob", (0.05, 0.016, 0.03), (w * 0.26, -d - 0.008 + 0.0, foot * 0.5), yellow, 0.004))
        for i, x in enumerate((-w * 0.22, -w * 0.12, -w * 0.02)):
            parts.append(cylinder("Gland%d" % i, 0.014, 0.03, (x, -d * 0.55, 0.0), dark, 10))
            parts.append(box("GlandNut%d" % i, (0.036, 0.036, 0.008), (x, -d * 0.55, 0.014), metal, 0.002))
        # the wall bracket along the back
        parts.append(box("Bracket", (w * 0.8, 0.012, 0.04), (0, 0.006, foot + body_h - 0.06), metal, 0.002))
        parts.append(box("BracketLow", (w * 0.8, 0.012, 0.04), (0, 0.006, foot + 0.05), metal, 0.002))
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
    base_p = os.path.join(ELEC, "electricity_battery_wall_power_10kwh", "electricity_battery_wall_power_10kwh.json")
    base = json.load(open(base_p, encoding="utf-8"))
    for uid, (kwh, w, h, d, kg, price, watts) in UNITS.items():
        folder = os.path.join(ELEC, uid)
        os.makedirs(folder, exist_ok=True)
        p = os.path.join(folder, uid + ".json")
        m = json.load(open(p, encoding="utf-8")) if os.path.exists(p) else json.loads(json.dumps(base))
        m["id"] = uid
        m["name"] = "Wall Power Battery, " + {5: "Small", 10: "Medium", 20: "Large"}[kwh]
        m["icon"] = uid + ".png"
        m["description"] = (f"A {kwh} kWh LiFePO4 home battery that mounts on a building's wall (inside or outside): aim at a wall of a finished building and left click. "
                            f"{watts / 1000:.0f} kW continuous.")
        pr = m["properties"]
        pr["weight_kg"] = kg
        pr["base_value"] = price
        pr["max_stack_size"] = 1
        pr["placeable"] = False
        pr["attach_surface"] = "wall"
        pr["attach_side"] = "either"
        pr["footprint"] = f"{w:.2f}m W x {d:.2f}m D x {h:.2f}m H"
        m["models"] = [{"file": uid + ".glb", "format": "glb", "dimensions_m": {"x": w, "y": h, "z": d}, "triangles": int(tris[uid])}]
        m["utilities"]["battery"] = {"metric": f"{kwh} kWh LiFePO4 (51.2 V), {watts / 1000:g} kW continuous, about 6,000 cycles, 96% round trip",
                                     "details": f"{kwh} kWh LiFePO4 (51.2 V), {watts / 1000:g} kW continuous, about 6,000 cycles, 96% round trip"}
        m["category_fields"]["dimensions_m"] = {"width": w, "depth": d, "height": h}
        m["category_fields"]["max_power_w"] = watts
        for f in os.listdir(folder):
            if f.endswith((".obj", ".mtl")) or (f.endswith(".glb") and f != uid + ".glb"):
                os.remove(os.path.join(folder, f))
        retry(shutil.copy, os.path.join(out, uid + ".glb"), os.path.join(folder, uid + ".glb"))
        retry(shutil.copy, os.path.join(WORK, uid + ".png"), os.path.join(folder, uid + ".png"))
        text = (json.dumps(m, indent=2, ensure_ascii=False) + "\n").replace("\n", "\r\n")
        retry(lambda: open(p, "w", encoding="utf-8", newline="").write(text))
        retry(lambda: open(os.path.join(folder, "README.md"), "w", encoding="utf-8", newline="").write(
            f"# {m['name']}\n\n**Item ID:** `{uid}`  \n**Category:** `electricity`  \n**Icon:** ![{m['name']}]({uid}.png)\n\n{m['description']}\n"))


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
    if "--install" in sys.argv:
        install(out)
        print("installed")


if __name__ == "__main__":
    main()
