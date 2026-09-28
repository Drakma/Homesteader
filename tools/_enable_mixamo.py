"""Enable the Mixamo rig addon and report whether its operators are usable."""
import addon_utils

MOD = "bl_ext.blender_org.mixamo_rig"

print("[mixamo] before: %s" % (addon_utils.check(MOD),))
try:
    ok = addon_utils.enable(MOD, default_set=True, persistent=True)
    print("[mixamo] enable() returned: %s" % (ok,))
except Exception as e:
    print("[mixamo] enable FAILED: %s: %s" % (type(e).__name__, e))

print("[mixamo] after: %s" % (addon_utils.check(MOD),))

import bpy
ops = [o for o in dir(bpy.ops.mr)] if hasattr(bpy.ops, "mr") else []
print("[mixamo] bpy.ops.mr has mr namespace: %s" % bool(ops))
for name in ("make_rig", "import_anim_to_rig", "bake_anim", "add_rig", "clear_pose"):
    try:
        print("[mixamo]   mr.%-20s present=%s" % (name, hasattr(bpy.ops.mr, name)))
    except Exception as e:
        print("[mixamo]   mr.%s -> %s" % (name, e))

print("[mixamo] DONE")