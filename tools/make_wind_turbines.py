#!/usr/bin/env python3
"""
make_wind_turbines.py
Builds, in code (no paid generation), full-size small wind turbines with a MOVING head (200 W and 500 W metal, 100 W wooden), as a KIT item (a crate) and as the
four construction-stage models of a buildable structure (docs/WIND_TURBINES.md): foundation (the base plate), mast (the node Mast is raised), head (the node Yaw is
hoisted), complete (the node Rotor is fitted and spins).
Node convention read by Assets/Scripts/Growth/WindTurbine.cs and BuildMotionView.cs:
    Base/Tower  the static footing / mast
    Mast        the mast alone in the mast stage, its origin the foot (build_motion tilt_up raises it)
    Yaw         an empty at the top of the mast: it turns about the vertical axis to face INTO the wind (build_motion lift hoists it); its children go with it
    Nacelle     the generator housing, tail boom and tail fin (child of Yaw)
    Rotor       hub and blades, its origin at the hub, spinning about its local Z axis in the game (Blender -Y is the front; build_motion spin_up fits and spins it)
Run:  python tools/make_wind_turbines.py [--install]     (--install also writes the kit items, the structures, their stages and icons)
"""
import copy
import json
import os
import shutil
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ELEC = os.path.join(ROOT, "assets", "electricity")
STRUCT = os.path.join(ROOT, "assets", "structures")
WORK = os.path.join(ROOT, "assets", "_scratch", "wind")

# structure id: (name, kind, watts, mast height m, rotor radius m, blades, kit weight kg, kit price, kit id, kit crate length m, description)
TURBINES = {
    "wind_turbine_200w_metal": ("200W Metal Wind Turbine", "metal200", 200, 3.2, 0.60, 3, 30.0, 520, "electricity_wind_kit_200w_metal", 1.7,
                                "A 200 watt, three-blade wind turbine on a 3 m galvanized steel mast. The tail fin turns it into the wind and the blades spin with it."),
    "wind_turbine_500w_metal": ("500W Metal Wind Turbine", "metal500", 500, 4.6, 0.85, 3, 55.0, 1100, "electricity_wind_kit_500w_metal", 2.0,
                                "A 500 watt, three-blade wind turbine on a 4.5 m galvanized steel mast with a furling tail. It turns into the wind and the blades spin with it."),
    "wind_turbine_100w_wood": ("100W Wooden Wind Turbine", "wood100", 100, 2.7, 0.55, 3, 28.0, 260, "electricity_wind_kit_100w_wood", 1.5,
                               "A 100 watt homestead wind turbine: wooden blades and tail vane on a treated wooden post. It turns into the wind and the blades spin with it."),
}
STAGES = ["foundation", "mast", "head", "complete"]
AGES = [(0, 25), (25, 50), (50, 75), (75, 100)]
FOOTPRINT = 2

SHOVELS = ["tool_shovel", "tool_shovel_round_point", "tool_shovel_trenching", "tool_pickaxe"]
WRENCHES = ["tool_wrench_adjustable", "tool_wrench_pipe"]
DRILLS = ["tool_drill_corded", "tool_drill_cordless_basic", "tool_drill_cordless_pro", "tool_impact_driver_cordless"]
HAMMERS = ["tool_hammer", "tool_hammer_claw", "tool_hammer_club"]
SAWS = ["tool_saw_hand", "tool_circular_saw_corded", "tool_circular_saw_cordless", "tool_miter_saw"]


def stage_plan(sid):
    """(recipe, tool groups, work clips, model motion) of each stage. No building materials at all: the KIT is used up when its work site is placed (properties.builds_structure)."""
    kit = TURBINES[sid][8]
    wood = TURBINES[sid][1].startswith("wood")
    if wood:
        return [
            ([], [SHOVELS, HAMMERS], ["Dig", "Hoe"], ""),
            ([], [SAWS, HAMMERS, WRENCHES], ["Chop_Tree_RT", "Push_RT"], "tilt_up"),
            ([], [WRENCHES, DRILLS], ["Fixing_Kneeling_RT", "Push_RT"], "lift"),
            ([], [WRENCHES, DRILLS], ["Fixing_Kneeling_RT"], "spin_up"),
        ]
    return [
        ([], [SHOVELS, WRENCHES], ["Dig", "Hoe"], ""),
        ([], [WRENCHES, DRILLS], ["Push_RT", "Fixing_Kneeling_RT"], "tilt_up"),
        ([], [WRENCHES, DRILLS], ["Fixing_Kneeling_RT", "Push_RT"], "lift"),
        ([], [WRENCHES, DRILLS], ["Fixing_Kneeling_RT"], "spin_up"),
    ]


def font(size, bold=True):
    from PIL import ImageFont
    f = "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"
    return ImageFont.truetype(f, size) if os.path.exists(f) else ImageFont.load_default()


def make_textures():
    from PIL import Image, ImageDraw
    os.makedirs(WORK, exist_ok=True)
    for sid, (name, kind, watts, H, R, nb, kg, price, kit, klen, desc) in TURBINES.items():
        W, Hh = 1024, 256
        wood = kind.startswith("wood")
        img = Image.new("RGB", (W, Hh), (176, 140, 96) if wood else (205, 170, 120))
        d = ImageDraw.Draw(img)
        d.rectangle([0, 0, 16, Hh], fill=(40, 120, 200) if not wood else (110, 70, 30))
        d.text((50, 70), "%d W" % watts, font=font(120), fill=(30, 30, 30), anchor="lm")
        d.text((330, 60), "WIND TURBINE KIT", font=font(70), fill=(30, 30, 30), anchor="lm")
        d.text((330, 130), "WOODEN BLADES AND POST" if wood else "STEEL MAST  3 BLADE", font=font(40, False), fill=(60, 60, 60), anchor="lm")
        d.text((50, 215), "HEAVY  KEEP DRY  ASSEMBLE ON SITE", font=font(34, False), fill=(60, 60, 60), anchor="lm")
        d.rectangle([2, 2, W - 3, Hh - 3], outline=(80, 60, 40), width=5)
        img.save(os.path.join(WORK, kit + "_label.png"))


def blender_main(out_dir):
    import bpy
    import bmesh
    import math
    from mathutils import Matrix, Vector

    def reset():
        bpy.ops.wm.read_factory_settings(use_empty=True)

    def material(name, rgb, metallic=0.0, rough=0.5):
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        b = m.node_tree.nodes["Principled BSDF"]
        b.inputs["Base Color"].default_value = (rgb[0], rgb[1], rgb[2], 1.0)
        b.inputs["Metallic"].default_value = metallic
        b.inputs["Roughness"].default_value = rough
        return m

    def tex_material(name, path):
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        b = m.node_tree.nodes["Principled BSDF"]
        b.inputs["Roughness"].default_value = 0.8
        node = m.node_tree.nodes.new("ShaderNodeTexImage")
        node.image = bpy.data.images.load(path)
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

    def tube(name, r1, r2, length, axis, centre, mat, seg=12):
        """A cylinder / cone: radius r1 at the low end of its axis, r2 at the high end."""
        bm = bmesh.new()
        bm.loops.layers.uv.verify()
        bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=seg, radius1=r1, radius2=r2, depth=length)
        if axis == "x":
            bmesh.ops.transform(bm, matrix=Matrix.Rotation(math.pi / 2, 4, 'Y'), verts=bm.verts)
        elif axis == "y":
            bmesh.ops.transform(bm, matrix=Matrix.Rotation(-math.pi / 2, 4, 'X'), verts=bm.verts)
        for v in bm.verts:
            v.co += Vector(centre)
        return put(name, bm, mat)

    def strut(name, p0, p1, thick, mat):
        a, b = Vector(p0), Vector(p1)
        d = b - a
        ob = box(name, (thick, thick, d.length), (0, 0, 0), mat)
        ob.data.transform(d.to_track_quat('Z', 'Y').to_matrix().to_4x4())
        ob.data.transform(Matrix.Translation((a + b) / 2))
        return ob

    def blade(name, R, r0, chords, twists, thick, mat):
        """A tapered, twisted blade along +z from radius r0 to R; chord along x, thickness along y."""
        bm = bmesh.new()
        radii = [r0, r0 + 0.25 * (R - r0), r0 + 0.6 * (R - r0), R]
        rings = []
        for s, c, tw in zip(radii, chords, twists):
            a = math.radians(tw)
            ca, sa = math.cos(a), math.sin(a)
            ring = []
            for (x, y) in ((-0.30 * c, 0.0), (0.05 * c, thick * c), (0.70 * c, 0.0), (0.05 * c, -thick * c)):
                ring.append(bm.verts.new((x * ca - y * sa, x * sa + y * ca, s)))
            rings.append(ring)
        for k in range(len(rings) - 1):
            for i in range(4):
                bm.faces.new((rings[k][i], rings[k][(i + 1) % 4], rings[k + 1][(i + 1) % 4], rings[k + 1][i]))
        bm.faces.new(rings[0])
        bm.faces.new(list(reversed(rings[-1])))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        return put(name, bm, mat)

    def quad_top(name, cx, cy, w, l, z, mat):
        bm = bmesh.new()
        vs = [bm.verts.new(c) for c in [(cx - w / 2, cy - l / 2, z), (cx + w / 2, cy - l / 2, z), (cx + w / 2, cy + l / 2, z), (cx - w / 2, cy + l / 2, z)]]
        f = bm.faces.new(vs)
        uv = bm.loops.layers.uv.new("UVMap")
        for loop, (u, v) in zip(f.loops, [(0, 0), (1, 0), (1, 1), (0, 1)]):
            loop[uv].uv = (u, v)
        return put(name, bm, mat)

    def join(objs):
        bpy.ops.object.select_all(action='DESELECT')
        for o in objs:
            o.select_set(True)
        bpy.context.view_layer.objects.active = objs[0]
        bpy.ops.object.join()
        return objs[0]

    def tris():
        return sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in bpy.data.objects if o.type == 'MESH')

    results = {}

    def export(path_name):
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.export_scene.gltf(filepath=os.path.join(out_dir, path_name + ".glb"), export_format='GLB', use_selection=True, export_apply=True, export_yup=True)
        results[path_name] = tris()

    def build(sid, stage):
        """One turbine up to a construction stage: 1 foundation, 2 mast, 3 head, 4 complete."""
        name, kind, watts, H, R, nb, kg, price, kit, klen, desc = TURBINES[sid]
        reset()
        wood = kind.startswith("wood")
        big = kind == "metal500"
        galv = material("Mast", (0.62, 0.65, 0.68), 0.85, 0.4)
        dark = material("Dark", (0.04, 0.04, 0.045), 0.4, 0.5)
        white = material("Housing", (0.88, 0.90, 0.92), 0.3, 0.35)
        steel = material("Steel", (0.55, 0.57, 0.60), 0.9, 0.35)
        concrete = material("Concrete", (0.58, 0.58, 0.56), 0.0, 0.9)
        timber = material("Timber", (0.52, 0.36, 0.20), 0.0, 0.85)
        blade_mat = material("Blade", (0.62, 0.45, 0.27) if wood else (0.86, 0.88, 0.90), 0.0 if wood else 0.2, 0.7 if wood else 0.3)
        fin_mat = material("Fin", (0.72, 0.58, 0.38) if wood else ((0.15, 0.35, 0.8) if big else (0.92, 0.45, 0.1)), 0.0, 0.5)
        stripe = material("Stripe", (0.9, 0.1, 0.08), 0.0, 0.5)
        green = material("Cable", (0.03, 0.03, 0.035), 0.0, 0.6)

        # the mast: a base (the footing), the mast itself, and extras that come with the head (the post's braces)
        tb, tm, tx = [], [], []
        if wood:
            post = 0.14
            tb.append(tube("Collar", 0.26, 0.26, 0.06, "z", (0, 0, 0.03), concrete, 14))
            tm.append(box("Junction", (0.14, 0.06, 0.18), (0, -post / 2 - 0.03, 0.9), dark, 0.004))
            tm.append(box("Post", (post, post, H), (0, 0, H / 2), timber, 0.006))
            tm.append(box("TopPlate", (0.22, 0.22, 0.012), (0, 0, H + 0.006), steel, 0.002))
            for sx in (-1, 1):
                for sy in (-1, 1):
                    tm.append(tube("TopBolt", 0.009, 0.009, 0.02, "z", (sx * 0.08, sy * 0.08, H + 0.02), steel, 6))
            tm.append(tube("Conduit", 0.012, 0.012, H - 1.0, "z", (0, -post / 2 - 0.012, 1.0 + (H - 1.0) / 2), green, 8))
            for sx, sy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                tx.append(strut("Brace", (sx * 0.62, sy * 0.62, 0.06), (sx * post * 0.5, sy * post * 0.5, 1.15), 0.06, timber))
                tx.append(box("BraceBracket", (0.06, 0.06, 0.012), (sx * post * 0.5 + sx * 0.012, sy * post * 0.5 + sy * 0.012, 1.15), steel))
        else:
            r_b, r_t = (0.058, 0.040) if not big else (0.080, 0.055)
            fl = 0.34 if not big else 0.42
            tb.append(box("Flange", (fl, fl, 0.022), (0, 0, 0.011), steel, 0.003))
            for sx, sy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                tb.append(strut("Gusset", (sx * (r_b + 0.09), sy * (r_b + 0.09), 0.02), (sx * r_b, sy * r_b, 0.22), 0.016, steel))
            for sx in (-1, 1):
                for sy in (-1, 1):
                    tb.append(tube("Bolt", 0.010, 0.010, 0.045, "z", (sx * (fl / 2 - 0.035), sy * (fl / 2 - 0.035), 0.044), steel, 6))
                    tb.append(tube("Nut", 0.016, 0.016, 0.012, "z", (sx * (fl / 2 - 0.035), sy * (fl / 2 - 0.035), 0.036), steel, 6))
            tm.append(box("Junction", (0.20, 0.09, 0.26), (0, -(r_b + 0.06), 0.55), dark, 0.005))
            tm.append(tube("Mast", r_b, r_t, H, "z", (0, 0, H / 2), galv, 14))
            tm.append(tube("Conduit", 0.014, 0.014, H - 0.7, "z", (0, -(r_b + 0.02), 0.68 + (H - 0.7) / 2), green, 8))
            for z in (1.0, 2.0, H - 0.4):
                tm.append(box("Clamp", (0.05, 0.03, 0.02), (0, -(r_b + 0.01), z), steel, 0.002))
            tm.append(tube("TopCap", r_t + 0.012, r_t + 0.012, 0.02, "z", (0, 0, H + 0.01), steel, 14))

        if stage == 1:
            for ob in tm + tx:
                bpy.data.objects.remove(ob, do_unlink=True)    # not built yet
            join(tb).name = "Base"
        elif stage == 2:
            for ob in tx:
                bpy.data.objects.remove(ob, do_unlink=True)
            join(tb).name = "Base"
            join(tm).name = "Mast"        # its origin is the foot of the mast: it is raised about it
        else:
            join(tb + tm + tx).name = "Tower"

        if stage >= 3:
            # the head (turns into the wind)
            z0 = 0.15 if not big else 0.19
            hl = 0.34 if not big else 0.48
            hr = 0.075 if not big else 0.11
            yfront = -(0.04 + hl / 2)
            na = []
            na.append(tube("YawTube", 0.05 if big else 0.04, 0.05 if big else 0.04, 0.12, "z", (0, 0, 0.06), steel, 12))
            na.append(box("YawSaddle", (0.12 if big else 0.09, 0.2 if big else 0.16, 0.05), (0, 0.0, z0 - hr - 0.02), steel, 0.004))
            if wood:
                na.append(tube("Can", 0.07, 0.07, 0.26, "y", (0, -0.02, z0), dark, 14))
                na.append(tube("CanRear", 0.07, 0.03, 0.08, "y", (0, 0.15, z0), dark, 14))
            else:
                na.append(tube("Housing", hr, hr, hl, "y", (0, -0.04, z0), white, 16))
                na.append(tube("HousingRear", hr, hr * 0.35, 0.12 if not big else 0.16, "y", (0, 0.04 + hl / 2 + 0.06, z0), white, 16))
                for i in range(3):
                    na.append(tube("Rib%d" % i, hr + 0.005, hr + 0.005, 0.014, "y", (0, -0.04 - hl / 2 + 0.07 + i * 0.05, z0), steel, 16))
            boom_len = 0.9 if not big else 1.3
            boom_y = 0.04 + hl / 2 + 0.1 + boom_len / 2
            bt = 0.04 if not wood else 0.05
            na.append(box("Boom", (bt, boom_len, bt), (0, boom_y, z0), timber if wood else galv, 0.003))
            fy = boom_y + boom_len / 2 - 0.1
            fl_y, fl_z = (0.32, 0.34) if not big else (0.50, 0.52)
            if wood:
                fl_y, fl_z = 0.30, 0.34
            na.append(box("Fin", (0.014, fl_y, fl_z), (0, fy, z0 + fl_z * 0.40), fin_mat, 0.004))
            if not wood:
                na.append(box("FinStripe", (0.0155, fl_y, 0.05), (0, fy, z0 + fl_z * 0.78), stripe))
            if big:
                na.append(tube("FurlHinge", 0.025, 0.025, 0.14, "z", (0, 0.04 + hl / 2 + 0.17, z0), steel, 10))
                na.append(box("FurlStop", (0.04, 0.03, 0.03), (0, 0.04 + hl / 2 + 0.2, z0 + 0.08), steel, 0.002))
            nacelle = join(na)
            nacelle.name = "Nacelle"

            rotor = None
            if stage >= 4:
                # the rotor (spins)
                ro = []
                hub_r = 0.055 if not big else 0.085
                if wood:
                    for dy in (-0.012, 0.03):
                        ro.append(tube("HubPlate", 0.075, 0.075, 0.01, "y", (0, dy, 0), steel, 16))
                    for k in range(6):
                        a = math.radians(k * 60)
                        ro.append(tube("HubBolt", 0.006, 0.006, 0.05, "y", (math.sin(a) * 0.055, 0.009, math.cos(a) * 0.055), steel, 6))
                else:
                    ro.append(tube("Hub", hub_r, hub_r, 0.07 if not big else 0.10, "y", (0, 0, 0), dark, 14))
                ro.append(tube("Nose", 0.008, hub_r, 0.11 if not big else 0.16, "y", (0, -(0.04 if not big else 0.06) - (0.11 if not big else 0.16) / 2, 0), steel if wood else white, 14))
                chords = [0.13, 0.15, 0.12, 0.05] if not big else [0.18, 0.21, 0.17, 0.07]
                if wood:
                    chords = [0.12, 0.15, 0.12, 0.07]
                twists = [28, 18, 9, 3]
                thick = 0.09 if not wood else 0.17
                for k in range(nb):
                    b = blade("Blade%d" % k, R, hub_r * 0.9, chords, twists, thick, blade_mat)
                    b.data.transform(Matrix.Rotation(math.radians(k * 360.0 / nb), 4, 'Y'))
                    ro.append(b)
                rotor = join(ro)
                rotor.name = "Rotor"

            yaw = bpy.data.objects.new("Yaw", None)
            yaw.empty_display_type = 'PLAIN_AXES'
            yaw.location = (0, 0, H + (0.012 if wood else 0.02))
            bpy.context.collection.objects.link(yaw)
            bpy.context.view_layer.update()
            inv = yaw.matrix_world.inverted()
            nacelle.location = yaw.location
            kids = [nacelle]
            if rotor is not None:
                rotor.location = (0, yfront - 0.02, yaw.location.z + z0)
                kids.append(rotor)
            for ob in kids:
                ob.parent = yaw
                ob.matrix_parent_inverse = inv
        export("%s_%d" % (sid, stage))

    def build_kit(sid):
        """The kit as an item: a long strapped crate with a printed label."""
        name, kind, watts, H, R, nb, kg, price, kit, klen, desc = TURBINES[sid]
        reset()
        wood = kind.startswith("wood")
        card = material("Crate", (0.55, 0.40, 0.24) if wood else (0.80, 0.66, 0.46), 0.0, 0.9)
        slat = material("Slat", (0.58, 0.44, 0.28), 0.0, 0.9)
        strap = material("Strap", (0.10, 0.25, 0.60), 0.0, 0.5)
        label = tex_material("Label", os.path.join(WORK, kit + "_label.png"))
        w, h = 0.34, 0.24
        parts = [box("Crate", (w, klen, h - 0.04), (0, 0, 0.04 + (h - 0.04) / 2), card, 0.008)]
        for sy in (-1, 1):
            parts.append(box("Runner", (w * 0.9, 0.07, 0.04), (0, sy * (klen / 2 - 0.2), 0.02), slat, 0.003))
        for yy in (-klen * 0.3, klen * 0.3):
            parts.append(box("StrapBand", (w + 0.008, 0.03, h - 0.03), (0, yy, 0.04 + (h - 0.04) / 2), strap))
        if wood:
            for k in range(-2, 3):
                parts.append(box("Plank", (w + 0.004, 0.006, h - 0.045), (0, k * klen * 0.18, 0.04 + (h - 0.04) / 2), slat))
        lab = quad_top("Label", 0, 0, 0.60, 0.15, h + 0.0005, label)
        lab.data.transform(Matrix.Rotation(math.pi / 2, 4, 'Z'))   # the strip runs along the crate (its length is y)
        parts.append(lab)
        join(parts)
        export(kit)

    for sid in TURBINES:
        for stage in (1, 2, 3, 4):
            build(sid, stage)
        build_kit(sid)

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


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def write_json(p, d, crlf=True):
    text = json.dumps(d, indent=2, ensure_ascii=False) + "\n"
    if crlf:
        text = text.replace("\n", "\r\n")
    retry(lambda: open(p, "w", encoding="utf-8", newline="").write(text))


def render_icon(glb, png):
    subprocess.run([sys.executable, os.path.join(ROOT, "tools", "render_icon_from_model.py"), glb, png], check=True, capture_output=True)


def install(out):
    tris = dict(l.split() for l in open(os.path.join(out, "tris.txt")).read().strip().splitlines())
    kit_tpl = load(os.path.join(ELEC, "electricity_turbine_wind_400w", "electricity_turbine_wind_400w.json"))
    cabin_group = load(os.path.join(STRUCT, "small_cabin", "small_cabin.json"))
    cabin_stage = load(os.path.join(STRUCT, "small_cabin", "stages", "struct_walls", "struct_walls_small_cabin.json"))
    kc_path = os.path.join(ROOT, "assets", "kit_config.json")
    kc = load(kc_path)
    for sid, (name, kind, watts, H, R, nb, kg, price, kit, klen, desc) in TURBINES.items():
        # ---------------------------------------------------------------- the kit item
        kdir = os.path.join(ELEC, kit)
        os.makedirs(kdir, exist_ok=True)
        km = copy.deepcopy(kit_tpl)
        km["id"] = kit
        km["name"] = name + " Kit"
        km["description"] = ("A kit with every part of a %s, shipped in a crate. Left click the ground with it to lay out the work site (R turns it), then build it in four "
                             "stages (footing, mast, head, blades) with the tools each one asks for. It cannot be made from building materials." % name.lower())
        km["icon"] = kit + ".png"
        pr = km["properties"]
        pr["weight_kg"] = kg
        pr["base_value"] = price
        pr["max_stack_size"] = 1
        pr["placeable"] = True
        pr["stores"] = ["voltvision"]
        pr["sale_unit"] = "kit"
        pr["builds_structure"] = sid
        pr["footprint"] = "0.34m W x %.2fm L x 0.24m H" % klen
        km["models"] = [{"file": kit + ".glb", "format": "glb", "dimensions_m": {"x": 0.34, "y": 0.24, "z": klen}, "triangles": int(tris[kit])}]
        text = "Builds a turbine that generates up to %d W (wind dependent)" % watts
        km["utilities"]["electricity"] = {"metric": text, "details": text}
        km["category_fields"]["dimensions_m"] = {"width": 0.34, "depth": klen, "height": 0.24}
        km["category_fields"]["max_power_w"] = 0
        for f in os.listdir(kdir):
            if f.endswith((".obj", ".mtl")) or (f.endswith(".glb") and f != kit + ".glb"):
                os.remove(os.path.join(kdir, f))
        retry(shutil.copy, os.path.join(out, kit + ".glb"), os.path.join(kdir, kit + ".glb"))
        render_icon(os.path.join(kdir, kit + ".glb"), os.path.join(kdir, kit + ".png"))
        write_json(os.path.join(kdir, kit + ".json"), km)
        retry(lambda: open(os.path.join(kdir, "README.md"), "w", encoding="utf-8", newline="").write(
            "# %s\n\n**Item ID:** `%s`  \n**Category:** `electricity`  \n**Icon:** ![%s](%s.png)\n\n%s\n" % (km["name"], kit, km["name"], kit, km["description"])))

        # ---------------------------------------------------------------- the structure (blueprint) and its four stages
        gdir = os.path.join(STRUCT, sid)
        group = copy.deepcopy(cabin_group)
        group["id"] = sid
        group["name"] = name
        group["icon"] = sid + ".png"
        group["description"] = desc + " Sold as a KIT only (the kit starts the work site); built in four stages with the tools each one asks for."
        gp = group["properties"]
        gp["base_value"] = 25
        gp["is_buyable"] = False       # the kit is how it is bought
        gp["stores"] = []
        group["category_fields"] = {"max_power_w": watts}
        g = group["growth"]
        g["species"] = sid
        g["stages"] = []
        plan = stage_plan(sid)
        heights = [0.3, H + 0.1, H + 0.6, round(H + R + 0.3, 2)]
        for i, stname in enumerate(STAGES):
            folder = "struct_" + stname
            item_id = "%s_%s" % (folder, sid)
            sdir = os.path.join(gdir, "stages", folder)
            os.makedirs(sdir, exist_ok=True)
            recipe, tools, clips, motion = plan[i]
            m = copy.deepcopy(cabin_stage)
            m["id"] = item_id
            m["name"] = "%s - %s" % (name, stname.capitalize())
            m["description"] = "The %s construction phase of the %s." % (stname, name.lower())
            m["icon"] = item_id + ".png"
            m["properties"]["weight_kg"] = 100.0 * (i + 1)
            m["properties"]["base_value"] = 0
            cf = m["category_fields"]
            cf["dimensions_m"] = {"width": FOOTPRINT, "depth": FOOTPRINT, "height": heights[i]}
            cf["interior_area_m2"] = 0
            cf["room_count"] = 0
            cf["construction_recipe"] = copy.deepcopy(recipe)
            cf["required_tools"] = copy.deepcopy(tools)
            cf["build_clips"] = clips
            cf["build_motion"] = motion
            m["models"] = [{"file": item_id + ".glb", "format": "glb", "dimensions_m": {"x": FOOTPRINT, "y": heights[i], "z": FOOTPRINT}, "triangles": int(tris["%s_%d" % (sid, i + 1)])}]
            for f in os.listdir(sdir):
                if f.endswith((".obj", ".mtl")) or (f.endswith(".glb") and f != item_id + ".glb"):
                    os.remove(os.path.join(sdir, f))
            retry(shutil.copy, os.path.join(out, "%s_%d.glb" % (sid, i + 1)), os.path.join(sdir, item_id + ".glb"))
            render_icon(os.path.join(sdir, item_id + ".glb"), os.path.join(sdir, item_id + ".png"))
            write_json(os.path.join(sdir, item_id + ".json"), m)
            retry(lambda: open(os.path.join(sdir, "README.md"), "w", encoding="utf-8", newline="").write("# %s\n\nProcedural model (tools/make_wind_turbines.py).\n" % m["name"]))
            g["stages"].append({"stage": i + 1, "name": stname, "age_min": AGES[i][0], "age_max": AGES[i][1], "resource": "stages/%s/" % folder, "model": "",
                                "icon": item_id + ".png", "construction_recipe": copy.deepcopy(recipe), "required_tools": copy.deepcopy(tools),
                                "build_clips": clips, "build_motion": motion})
        g["total_stages"] = 4
        g["icon_stage"] = 4
        g["max_age"] = 100
        write_json(os.path.join(gdir, sid + ".json"), group)
        retry(shutil.copy, os.path.join(gdir, "stages", "struct_complete", "struct_complete_%s.png" % sid), os.path.join(gdir, sid + ".png"))
        kc["subfolders"][sid] = {"name": name, "icon": "", "category": "structures"}
        kc["growth_groups"][sid] = {"name": name, "icon": "", "category": "structures", "growth_type": "percent", "max_age": 100, "time_unit": "percent",
                                    "stages": [{"stage": i + 1, "name": n, "item_id": "struct_%s_%s" % (n, sid), "age_min": AGES[i][0], "age_max": AGES[i][1]} for i, n in enumerate(STAGES)]}
    write_json(kc_path, kc, crlf=False)
    # the first version's finished-turbine items are replaced by the kits and structures
    for old in ("electricity_turbine_wind_200w_metal", "electricity_turbine_wind_500w_metal", "electricity_turbine_wind_100w_wood"):
        d = os.path.join(ELEC, old)
        if os.path.isdir(d):
            shutil.rmtree(d)


def main():
    if "--blender" in sys.argv:
        blender_main(sys.argv[sys.argv.index("--") + 1])
        return
    make_textures()
    out = os.path.join(WORK, "glb")
    os.makedirs(out, exist_ok=True)
    r = subprocess.run([find_blender(), "--background", "--python", os.path.abspath(__file__), "--", out, "--blender"], capture_output=True, text=True)
    print((r.stdout + r.stderr)[-1500:])
    print(open(os.path.join(out, "tris.txt")).read())
    if "--install" in sys.argv:
        install(out)
        print("installed")


if __name__ == "__main__":
    main()
