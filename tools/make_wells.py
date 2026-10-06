#!/usr/bin/env python3
"""
make_wells.py
Builds, in code (no paid generation), the electric drilled wells (docs/WELLS.md):
  - two buildable structures, water_well_concrete (a concrete wellhead) and water_well_wooden (a wooden well house), each in three stages:
    drill (the bore and its casing), pump (the pump set on its drop pipe, the cable coiled), wellhead (the finished head and the post its sub panel mounts on);
  - the three submersible pumps that replace every earlier one: 1/2 HP (1400 L/h), 3/4 HP (2300 L/h), 1 HP (2900 L/h);
  - the well sub panel (electricity_panel_well_sub): fitted on a finished wellhead, wired with AC wire to a breaker box, it powers the pump.
The pump stage asks for the pump, PVC drop pipe and Romex by the well's DEPTH (recipe lines with per_depth_m: quantity + per_depth_m x depth, the depth read from the
water table where the well stands).
Node convention: the complete wellhead has an empty "PanelMount" (on the front of its post, the sub panel's back on it, front towards Blender -Y = the game's +z).
Run:  python tools/make_wells.py [--install]
"""
import copy
import json
import os
import shutil
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WATER = os.path.join(ROOT, "assets", "water")
ELEC = os.path.join(ROOT, "assets", "electricity")
STRUCT = os.path.join(ROOT, "assets", "structures")
WORK = os.path.join(ROOT, "assets", "_scratch", "wells")

# pump id: (name, hp label, flow L/h, running watts, length m, price, weight kg)
PUMPS = {
    "water_pump_submersible_half_hp": ("1/2 HP Submersible Well Pump", "1/2 HP", 1400, 900, 0.78, 420, 9.0),
    "water_pump_submersible_three_quarter_hp": ("3/4 HP Submersible Well Pump", "3/4 HP", 2300, 1200, 0.90, 560, 11.0),
    "water_pump_submersible_1hp": ("1 HP Submersible Well Pump", "1 HP", 2900, 1500, 1.02, 690, 13.0),
}
SUBPANEL = "electricity_panel_well_sub"
WELLS = {
    "water_well_concrete": ("Drilled Well (Concrete Wellhead)", "concrete",
                            "An electric drilled well: a submersible pump down the bore, a PVC drop pipe bringing the water up and a concrete wellhead on top. "
                            "Fit a well sub panel on its post and wire that to a breaker box with AC wire to run the pump; pipe it to a tank with PVC pipe."),
    "water_well_wooden": ("Drilled Well (Wooden Well House)", "wooden",
                          "An electric drilled well: a submersible pump down the bore, a PVC drop pipe bringing the water up and a small wooden well house over the head. "
                          "Fit a well sub panel on its post and wire that to a breaker box with AC wire to run the pump; pipe it to a tank with PVC pipe."),
}
STAGES = ["drill", "pump", "wellhead"]
AGES = [(0, 33), (33, 66), (66, 100)]
FOOTPRINT = 2
OLD = ["water_well_head_concrete", "water_well_head_wooden", "water_pump_submersible_3hp", "waste_pump_submersible_deep"]

SHOVELS = ["tool_shovel", "tool_shovel_round_point", "tool_shovel_trenching", "tool_pickaxe"]
WRENCHES = ["tool_wrench_pipe", "tool_wrench_adjustable"]
SAWS = ["tool_saw_hand", "tool_circular_saw_corded", "tool_circular_saw_cordless", "tool_miter_saw"]
DRILLS = ["tool_drill_corded", "tool_drill_cordless_basic", "tool_drill_cordless_pro", "tool_impact_driver_cordless"]
HAMMERS = ["tool_hammer", "tool_hammer_claw", "tool_hammer_club"]
MIXERS = ["tool_wheelbarrow", "tool_plastic_wheelbarrow", "tool_steel_wheelbarrow", "tool_cement_mixer"]
TROWELS = ["tool_trowel_hand"]
CUTTERS = ["tool_wire_cutters"]


def stage_plan(kind):
    """(recipe, tool groups, work clips) of each stage."""
    drill = ([], [SHOVELS], ["Dig", "Hoe"])
    pump = ([
        {"item_id": "~well_pump", "quantity": 1},
        {"item_id": "~pipe_pvc_one_inch", "quantity": 1, "per_depth_m": 0.34},   # a 3 m length per 3 m of depth, and one for the head
        {"item_id": "~romex_12_2", "quantity": 5, "per_depth_m": 1},             # a metre of cable per metre of depth, and 5 m to the head
        {"item_id": "~pvc_cement_can", "quantity": 1},
    ], [WRENCHES, SAWS, CUTTERS], ["Fixing_Kneeling_RT", "Push_RT"])
    if kind == "concrete":
        head = ([
            {"section": "Concrete", "mode": "any", "items": [
                {"section": "Bagged concrete mix", "mode": "all", "items": [
                    {"item_id": "~concrete_mix", "quantity": 4}, {"item_id": "~water", "quantity": 4}]},
                {"section": "Mix your own: 1 cement, 2 sand, 3 aggregate", "mode": "all", "items": [
                    {"item_id": "~cement", "quantity": 1}, {"item_id": "~sand", "quantity": 0.03}, {"item_id": "~gravel", "quantity": 0.05}, {"item_id": "~water", "quantity": 4}]},
            ]},
            {"item_id": "~lumber_post_4x4", "quantity": 1},
        ], [SHOVELS, MIXERS, TROWELS], ["Dig", "Fixing_Kneeling_RT"])
    else:
        head = ([
            {"item_id": "~lumber_2x6", "quantity": 8},
            {"item_id": "~lumber_post_4x4", "quantity": 1},
            {"item_id": "~sheet_plywood_cdx", "quantity": 1},
            {"item_id": "~deck_screws", "quantity": 60},
        ], [SAWS, DRILLS, HAMMERS], ["Fixing_Kneeling_RT", "Push_RT"])
    return [drill, pump, head]


# ------------------------------------------------------------------ Blender

def blender_main(out_dir):
    import bpy
    import bmesh
    import math
    from mathutils import Vector

    results = {}

    def reset():
        bpy.ops.wm.read_factory_settings(use_empty=True)

    def material(name, rgb, metallic=0.0, rough=0.6):
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        b = m.node_tree.nodes.get("Principled BSDF")
        b.inputs["Base Color"].default_value = (rgb[0], rgb[1], rgb[2], 1.0)
        b.inputs["Metallic"].default_value = metallic
        b.inputs["Roughness"].default_value = rough
        return m

    def put(name, bm, mat):
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        bm.free()
        ob = bpy.data.objects.new(name, me)
        bpy.context.collection.objects.link(ob)
        me.materials.append(mat)
        return ob

    def box(name, size, centre, mat):
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        for v in bm.verts:
            v.co = Vector((v.co.x * size[0] + centre[0], v.co.y * size[1] + centre[1], v.co.z * size[2] + centre[2]))
        return put(name, bm, mat)

    def cyl(name, r, h, base, mat, seg=16, r2=None):
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r if r2 is None else r2, depth=h)
        for v in bm.verts:
            v.co = Vector((v.co.x + base[0], v.co.y + base[1], v.co.z + base[2] + h / 2))
        return put(name, bm, mat)

    def torus(name, R, r, centre, mat):
        bm = bmesh.new()
        segs, rings = 18, 6
        verts = []
        for i in range(segs):
            a = 2 * math.pi * i / segs
            ring = []
            for j in range(rings):
                b = 2 * math.pi * j / rings
                x = (R + r * math.cos(b)) * math.cos(a)
                y = (R + r * math.cos(b)) * math.sin(a)
                z = r * math.sin(b)
                ring.append(bm.verts.new((x + centre[0], y + centre[1], z + centre[2])))
            verts.append(ring)
        for i in range(segs):
            for j in range(rings):
                a, b2 = verts[i][j], verts[(i + 1) % segs][j]
                c, d = verts[(i + 1) % segs][(j + 1) % rings], verts[i][(j + 1) % rings]
                bm.faces.new((a, b2, c, d))
        return put(name, bm, mat)

    def empty(name, loc):
        ob = bpy.data.objects.new(name, None)
        ob.location = loc
        bpy.context.collection.objects.link(ob)
        return ob

    def tris():
        n = 0
        for ob in bpy.context.scene.objects:
            if ob.type == 'MESH':
                for p in ob.data.polygons:
                    n += len(p.vertices) - 2
        return n

    def export(path):
        bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=False, export_apply=True, export_yup=True)

    # ---------------------------------------------------------------- pumps (standing on their end, the cable coiled beside)
    for pid, (_, hp, flow, watts, L, _p, _kg) in PUMPS.items():
        reset()
        steel = material("Stainless", (0.78, 0.80, 0.82), 0.9, 0.3)
        dark = material("Dark", (0.08, 0.08, 0.09), 0.2, 0.5)
        band = material("Label", (0.10, 0.32, 0.70), 0.0, 0.5)
        cable = material("Cable", (0.15, 0.15, 0.16), 0.0, 0.6)
        r = 0.05
        cyl("Body", r, L * 0.55, (0, 0, 0.04), steel)
        cyl("Intake", r * 0.95, 0.06, (0, 0, 0.04 + L * 0.55), dark)
        cyl("Motor", r, L * 0.40, (0, 0, 0.10 + L * 0.55), steel)
        cyl("Foot", r * 0.8, 0.04, (0, 0, 0), dark)
        cyl("Band", r * 1.02, 0.08, (0, 0, 0.04 + L * 0.25), band)
        cyl("Outlet", r * 0.45, 0.06, (0, 0, 0.10 + L * 0.95), dark)
        torus("Coil", 0.12, 0.012, (0.20, 0, 0.015), cable)
        torus("Coil2", 0.12, 0.012, (0.20, 0, 0.04), cable)
        export(os.path.join(out_dir, pid + ".glb"))
        results[pid] = tris()

    # ---------------------------------------------------------------- the sub panel (wall item convention: back y = 0, front towards -y, bottom z = 0)
    reset()
    grey = material("Enclosure", (0.60, 0.62, 0.64), 0.5, 0.45)
    dark = material("Dark", (0.06, 0.06, 0.07), 0.2, 0.5)
    lab = material("Label", (0.92, 0.75, 0.12), 0.0, 0.5)
    box("Box", (0.22, 0.10, 0.30), (0, -0.05, 0.15), grey)
    box("Door", (0.19, 0.008, 0.26), (0, -0.104, 0.15), grey)
    box("Label", (0.10, 0.004, 0.04), (0, -0.110, 0.24), lab)
    cyl("Gland", 0.018, 0.04, (0, -0.05, -0.04), dark)
    box("Handle", (0.015, 0.012, 0.05), (0.07, -0.112, 0.15), dark)
    export(os.path.join(out_dir, SUBPANEL + ".glb"))
    results[SUBPANEL] = tris()

    # ---------------------------------------------------------------- the wells, stage by stage
    for wid, (_, kind, _d) in WELLS.items():
        for si, st in enumerate(STAGES):
            reset()
            steel = material("Casing", (0.36, 0.37, 0.39), 0.8, 0.45)
            dirt = material("Spoil", (0.36, 0.27, 0.18), 0.0, 0.95)
            pvc = material("PVC", (0.93, 0.93, 0.90), 0.0, 0.5)
            cable = material("Cable", (0.85, 0.82, 0.70), 0.0, 0.6)
            conc = material("Concrete", (0.66, 0.65, 0.62), 0.0, 0.9)
            wood = material("Wood", (0.55, 0.38, 0.22), 0.0, 0.8)
            post = material("Post", (0.45, 0.32, 0.19), 0.0, 0.8)
            cyl("Casing", 0.08, 0.55, (0, 0, -0.05), steel)
            if si == 0:
                cyl("Spoil", 0.75, 0.10, (0, 0, 0), dirt, 12, 0.45)
                box("Pile", (0.6, 0.5, 0.25), (0.65, 0.55, 0.12), dirt)
            if si >= 1:
                cyl("Cap", 0.095, 0.06, (0, 0, 0.50), steel)
                cyl("Drop", 0.018, 0.30, (0, 0, 0.56), pvc)
                box("Tee", (0.30, 0.04, 0.04), (0.15, 0, 0.84), pvc)
                if si == 1:
                    torus("Coil", 0.22, 0.015, (0.55, 0.40, 0.02), cable)
                    torus("Coil2", 0.22, 0.015, (0.55, 0.40, 0.05), cable)
                    for k in range(3):
                        box("PipeStack", (1.4, 0.03, 0.03), (-0.2, 0.62 + k * 0.035, 0.015), pvc)   # lengths of drop pipe lying ready
            if si == 2:
                if kind == "concrete":
                    cyl("Collar", 0.50, 0.40, (0, 0, 0), conc, 20)
                    cyl("Top", 0.46, 0.04, (0, 0, 0.40), conc, 20)
                else:
                    for x in (-0.48, 0.48):
                        box("Side", (0.04, 1.0, 0.8), (x, 0, 0.4), wood)
                    for y in (-0.48, 0.48):
                        box("End", (0.92, 0.04, 0.8), (0, y, 0.4), wood)
                    box("Lid", (1.05, 1.05, 0.05), (0, 0, 0.83), wood)
                # the post the sub panel mounts on, at the front right, its face towards -y
                box("PanelPost", (0.09, 0.09, 1.25), (0.75, -0.55, 0.625), post)
                empty("PanelMount", (0.75, -0.60, 0.72))
            export(os.path.join(out_dir, "%s_%d.glb" % (wid, si + 1)))
            results["%s_%d" % (wid, si + 1)] = tris()

    with open(os.path.join(out_dir, "tris.txt"), "w") as f:
        for k, v in results.items():
            f.write("%s %d\n" % (k, v))


# ------------------------------------------------------------------ install

def find_blender():
    for p in [shutil.which("blender"), r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"]:
        if p and os.path.exists(p):
            return p
    raise SystemExit("blender not found")


def retry(fn, *a):
    for i in range(8):
        try:
            return fn(*a)
        except OSError:
            time.sleep(0.5)
    return fn(*a)


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def write_json(p, d, crlf=True):
    text = json.dumps(d, indent=2, ensure_ascii=False) + "\n"
    if crlf:
        text = text.replace("\n", "\r\n")
    retry(lambda: open(p, "wb").write(text.encode("utf-8")))


def render_icon(glb, png):
    subprocess.run([sys.executable, os.path.join(ROOT, "tools", "render_icon_from_model.py"), glb, png], check=True, capture_output=True)


def readme(d, title, item_id, cat, desc):
    retry(lambda: open(os.path.join(d, "README.md"), "w", encoding="utf-8", newline="").write(
        "# %s\n\n**Item ID:** `%s`  \n**Category:** `%s`  \n**Icon:** ![%s](%s.png)\n\n%s\n" % (title, item_id, cat, title, item_id, desc)))


def clean(d, keep):
    for f in os.listdir(d):
        if f.endswith((".obj", ".mtl")) or (f.endswith(".glb") and f != keep):
            os.remove(os.path.join(d, f))


def install(out):
    tris = dict(l.split() for l in open(os.path.join(out, "tris.txt")).read().strip().splitlines())
    pump_tpl = load(os.path.join(WATER, "water_pump_submersible_1hp", "water_pump_submersible_1hp.json"))
    panel_tpl = load(os.path.join(ELEC, "electricity_panel_breaker_subpanel", "electricity_panel_breaker_subpanel.json"))
    cabin_group = load(os.path.join(STRUCT, "small_cabin", "small_cabin.json"))
    cabin_stage = load(os.path.join(STRUCT, "small_cabin", "stages", "struct_walls", "struct_walls_small_cabin.json"))

    # ---------------------------------------------------------------- pumps
    for pid, (name, hp, flow, watts, L, price, kg) in PUMPS.items():
        d = os.path.join(WATER, pid)
        os.makedirs(d, exist_ok=True)
        m = copy.deepcopy(pump_tpl)
        m["id"] = pid
        m["name"] = name
        m["icon"] = pid + ".png"
        m["description"] = ("A %s stainless submersible well pump: it lifts up to %d liters an hour (the well's own yield may be less). It goes down a drilled well "
                            "when the pump stage is built, and runs on the well's sub panel (%d W)." % (hp, flow, watts))
        pr = m["properties"]
        pr["weight_kg"] = kg
        pr["base_value"] = price
        pr["max_stack_size"] = 1
        pr["placeable"] = True
        pr["is_buyable"] = True
        pr["flow_lph"] = flow
        m["category_fields"]["power_draw_w"] = watts
        m["category_fields"]["dimensions_m"] = {"width": 0.34, "depth": 0.24, "height": round(L + 0.06, 2)}
        m["models"] = [{"file": pid + ".glb", "format": "glb", "dimensions_m": {"x": 0.34, "y": round(L + 0.06, 2), "z": 0.24}, "triangles": int(tris[pid])}]
        clean(d, pid + ".glb")
        retry(shutil.copy, os.path.join(out, pid + ".glb"), os.path.join(d, pid + ".glb"))
        render_icon(os.path.join(d, pid + ".glb"), os.path.join(d, pid + ".png"))
        write_json(os.path.join(d, pid + ".json"), m)
        readme(d, name, pid, "water", m["description"])

    # ---------------------------------------------------------------- the sub panel
    d = os.path.join(ELEC, SUBPANEL)
    os.makedirs(d, exist_ok=True)
    m = copy.deepcopy(panel_tpl)
    m["id"] = SUBPANEL
    m["name"] = "Well Pump Sub Panel"
    m["icon"] = SUBPANEL + ".png"
    m["description"] = ("A small weatherproof sub panel for a well pump. Fit it on a finished well (left or right click the well with it in hand), then wire it to a "
                        "building's breaker box with AC wire (the cable is buried) to run the pump.")
    pr = m["properties"]
    pr["weight_kg"] = 3.0
    pr["base_value"] = 85
    pr["max_stack_size"] = 5
    pr["placeable"] = False
    pr["is_buyable"] = True
    pr["wire_role"] = "ac_panel"
    pr.pop("attach_surface", None)
    pr.pop("attach_side", None)
    pr.pop("provides_power", None)
    m["category_fields"]["dimensions_m"] = {"width": 0.22, "depth": 0.11, "height": 0.30}
    m["category_fields"]["max_power_w"] = 3600
    m["models"] = [{"file": SUBPANEL + ".glb", "format": "glb", "dimensions_m": {"x": 0.22, "y": 0.30, "z": 0.11}, "triangles": int(tris[SUBPANEL])}]
    m.pop("lights", None)
    clean(d, SUBPANEL + ".glb")
    retry(shutil.copy, os.path.join(out, SUBPANEL + ".glb"), os.path.join(d, SUBPANEL + ".glb"))
    render_icon(os.path.join(d, SUBPANEL + ".glb"), os.path.join(d, SUBPANEL + ".png"))
    write_json(os.path.join(d, SUBPANEL + ".json"), m)
    readme(d, m["name"], SUBPANEL, "electricity", m["description"])

    # ---------------------------------------------------------------- the wells
    kc_path = os.path.join(ROOT, "assets", "kit_config.json")
    kc = load(kc_path)
    for wid, (name, kind, desc) in WELLS.items():
        gdir = os.path.join(STRUCT, wid)
        group = copy.deepcopy(cabin_group)
        group["id"] = wid
        group["name"] = name
        group["icon"] = wid + ".png"
        group["description"] = desc + " The pump stage asks for pipe and cable by the well's depth (hover the blueprint over a spot to see the depth and the most it can give)."
        gp = group["properties"]
        gp["base_value"] = 150
        gp["is_buyable"] = True
        gp["stores"] = ["nail_it"] if "nail_it" in json.dumps(cabin_group) else gp.get("stores", [])
        gp["attach_item"] = SUBPANEL
        gp["is_well"] = True
        g = group["growth"]
        g["species"] = wid
        g["stages"] = []
        plan = stage_plan(kind)
        heights = [0.5, 0.9, 1.25]
        for i, stname in enumerate(STAGES):
            folder = "struct_" + stname
            item_id = "%s_%s" % (folder, wid)
            sdir = os.path.join(gdir, "stages", folder)
            os.makedirs(sdir, exist_ok=True)
            recipe, tools, clips = plan[i]
            sm = copy.deepcopy(cabin_stage)
            sm["id"] = item_id
            sm["name"] = "%s - %s" % (name, stname.capitalize())
            sm["description"] = "The %s phase of the %s." % (stname, name.lower())
            sm["icon"] = item_id + ".png"
            sm["properties"]["weight_kg"] = 50.0 * (i + 1)
            sm["properties"]["base_value"] = 0
            cf = sm["category_fields"]
            cf["dimensions_m"] = {"width": FOOTPRINT, "depth": FOOTPRINT, "height": heights[i]}
            cf["interior_area_m2"] = 0
            cf["room_count"] = 0
            cf["construction_recipe"] = copy.deepcopy(recipe)
            cf["required_tools"] = copy.deepcopy(tools)
            cf["build_clips"] = clips
            cf["build_motion"] = ""
            sm["models"] = [{"file": item_id + ".glb", "format": "glb", "dimensions_m": {"x": FOOTPRINT, "y": heights[i], "z": FOOTPRINT},
                             "triangles": int(tris["%s_%d" % (wid, i + 1)])}]
            clean(sdir, item_id + ".glb")
            retry(shutil.copy, os.path.join(out, "%s_%d.glb" % (wid, i + 1)), os.path.join(sdir, item_id + ".glb"))
            render_icon(os.path.join(sdir, item_id + ".glb"), os.path.join(sdir, item_id + ".png"))
            write_json(os.path.join(sdir, item_id + ".json"), sm)
            retry(lambda: open(os.path.join(sdir, "README.md"), "w", encoding="utf-8", newline="").write("# %s\n\nProcedural model (tools/make_wells.py).\n" % sm["name"]))
            g["stages"].append({"stage": i + 1, "name": stname, "age_min": AGES[i][0], "age_max": AGES[i][1], "resource": "stages/%s/" % folder, "model": "",
                                "icon": item_id + ".png", "construction_recipe": copy.deepcopy(recipe), "required_tools": copy.deepcopy(tools),
                                "build_clips": clips, "build_motion": ""})
        g["total_stages"] = 3
        g["icon_stage"] = 3
        g["max_age"] = 100
        write_json(os.path.join(gdir, wid + ".json"), group)
        retry(shutil.copy, os.path.join(gdir, "stages", "struct_wellhead", "struct_wellhead_%s.png" % wid), os.path.join(gdir, wid + ".png"))
        readme(gdir, name, wid, "structures", group["description"])
        kc["subfolders"][wid] = {"name": name, "icon": "", "category": "structures"}
        kc["growth_groups"][wid] = {"name": name, "icon": "", "category": "structures", "growth_type": "percent", "max_age": 100, "time_unit": "percent",
                                    "stages": [{"stage": i + 1, "name": n, "item_id": "struct_%s_%s" % (n, wid), "age_min": AGES[i][0], "age_max": AGES[i][1]} for i, n in enumerate(STAGES)]}
    write_json(kc_path, kc, crlf=False)

    # ---------------------------------------------------------------- the pumps are one equivalency (any of them sets a well's pump)
    ep = os.path.join(ROOT, "assets", "_schemas", "equivalencies.json")
    eq = load(ep)
    eq["equivalencies"]["well_pump"] = {"unit": "pcs", "label": "Submersible Well Pump", "members": [{"item": p, "value": 1} for p in PUMPS]}
    write_json(ep, eq, crlf=False)

    # ---------------------------------------------------------------- what they replace
    for old in OLD:
        for cat in ("water", "waste"):
            dd = os.path.join(ROOT, "assets", cat, old)
            if os.path.isdir(dd):
                shutil.rmtree(dd)


def main():
    if "--blender" in sys.argv:
        blender_main(sys.argv[sys.argv.index("--") + 1])
        return
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
