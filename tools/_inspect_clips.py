"""Inspect the male ped's rigged FBX plus the Walk/Run clips for retargeting."""
import bpy
import os

PED = r"C:\Users\casey\Desktop\Homesteader\assets\peds\peds_male_farmer"
RIGGED = os.path.join(PED, "SKM_Peds_Male_Farmer_Rigged.fbx")
CLIPS = [
    ("Walk", os.path.join(PED, "SKM_Peds_Male_Farmer_Walk.fbx")),
    ("Run", os.path.join(PED, "SKM_Peds_Male_Farmer_Run.fbx")),
]


def action_curves(act):
    """Blender 5.x moved fcurves into slots/layers; 4.x had them on the Action."""
    if hasattr(act, "fcurves") and len(getattr(act, "fcurves", [])):
        return list(act.fcurves)
    out = []
    for layer in getattr(act, "layers", []):
        for strip in getattr(layer, "strips", []):
            for cb in getattr(strip, "channelbags", []):
                out.extend(list(getattr(cb, "fcurves", [])))
    return out


def summarize(tag, path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    if not os.path.isfile(path):
        print("[clip] %-6s MISSING %s" % (tag, path))
        return
    bpy.ops.import_scene.fbx(filepath=path)
    arms = [o for o in bpy.context.scene.objects if o.type == "ARMATURE"]
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    print("[clip] %-6s file=%s" % (tag, os.path.basename(path)))
    print("[clip] %-6s armatures=%d meshes=%d" % (tag, len(arms), len(meshes)))
    for a in arms:
        print("[clip] %-6s armature '%s' bones=%d" % (tag, a.name, len(a.data.bones)))
        ad = a.animation_data
        if ad and ad.action:
            act = ad.action
            curves = action_curves(act)
            print("[clip] %-6s ACTION '%s' frames=%s..%s curves=%d"
                  % (tag, act.name, act.frame_range[0], act.frame_range[1], len(curves)))
            paths = sorted({fc.data_path.split('"')[1] for fc in curves if '"' in fc.data_path})
            print("[clip] %-6s animated bones=%d e.g. %s" % (tag, len(paths), paths[:6]))
        else:
            print("[clip] %-6s NO action on armature" % tag)
        print("[clip] %-6s has mr_control_rig tag: %s" % (tag, "mr_control_rig" in a.data.keys()))
        names = [b.name for b in a.data.bones]
        mixamo = [n for n in names if n.lower().startswith("mixamorig")]
        print("[clip] %-6s mixamorig-prefixed bone names: %d" % (tag, len(mixamo)))
        print("[clip] %-6s first bones: %s" % (tag, names[:8]))


for tag, path in [("RIG", RIGGED)] + CLIPS:
    summarize(tag, path)

print("[clip] DONE")