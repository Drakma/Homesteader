#!/usr/bin/env python3
# Self-test for tools/retarget_to_mecanim.py.
#
# Unity itself is the only thing that can confirm an avatar builds without red
# bones. What CAN be tested here is the part that actually carries risk: that
# every Unity humanoid bone the avatar needs is mapped to a bone that exists in
# the rig, and that no mapping points at a nonexistent bone.

import importlib.util
import json
import os
import struct
import sys

TOOLS = r"C:\Users\casey\Desktop\Homesteader\tools"
sys.path.insert(0, TOOLS)

spec = importlib.util.spec_from_file_location(
    "retarget_to_mecanim", os.path.join(TOOLS, "retarget_to_mecanim.py")
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

RIGGED = r"C:\Users\casey\Desktop\Homesteader\mesh_output\rigged\peds_old_farmer_animated.glb"

failures = []


def check(label, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + label + (("  - " + detail) if detail else ""))
    if not ok:
        failures.append(label)


print("=" * 78)
print("retarget_to_mecanim self-test")
print("=" * 78)

doc = mod.read_glb_json(RIGGED)
bones = mod.rig_bone_names(doc)
human_table, unmapped = mod.build_human_table(bones)
mapped_unity = {u for _, u in human_table}
bone_set = set(bones)

check("rig has 66 joints", len(bones) == 66, "got " + str(len(bones)))

# 1. Every required Unity humanoid bone must be mapped.
missing = [b for b in mod.REQUIRED if b not in mapped_unity]
check("all required humanoid bones mapped", not missing, ", ".join(missing))

# 2. Every mapping must point at a bone that actually exists in the rig.
nonexistent = [rig for rig, _ in human_table if rig not in bone_set]
check("no mapping references a missing bone", not nonexistent,
      ", ".join(nonexistent))

# 3. No duplicate Unity names (a duplicate would confuse the importer).
unity_names = [u for _, u in human_table]
dupes = sorted({n for n in unity_names if unity_names.count(n) > 1})
check("no duplicate Unity bone names", not dupes, ", ".join(dupes))

# 4. Every rig bone is either mapped or knowingly a non-humanoid helper.
#    Leaves appear BOTH as bare "_leaf" and side-suffixed "_leaf_l"/"_leaf_r",
#    so the predicate has to accept either form.
def is_leaf_like(name):
    if name == "root":
        return True
    return ("_leaf" in name) or name.startswith("ball_leaf")


leaf_like = [b for b in unmapped if not is_leaf_like(b)]
check("unmapped bones are only leaves/helpers", not leaf_like,
      ", ".join(leaf_like))

# 5. Left/right symmetry: every left bone must have a right counterpart.
lr_broken = []
for rig, _ in human_table:
    if rig.endswith("_l"):
        if rig[:-2] + "_r" not in bone_set:
            lr_broken.append(rig)
check("left bones have right counterparts", not lr_broken, ", ".join(lr_broken))

# 6. The generated .meta must declare Humanoid + Create From This Model.
meta = mod.meta_text("0" * 32, human_table, "test.glb")
check("meta sets animationType: 2", "  animationType: 2" in meta)
check("meta sets avatarSetup: 1", "  avatarSetup: 1" in meta)
check("meta enables animation import", "  importAnimation: 1" in meta)
check("meta has one boneName per mapping",
      meta.count("    - boneName: ") == len(human_table),
      str(meta.count("    - boneName: ")) + " vs " + str(len(human_table)))

# 7. Animations survived the whole pipeline.
anim_names = [a.get("name") for a in (doc.get("animations") or [])]
check("four clips present", len(anim_names) == 4, ", ".join(anim_names))
for want in ["Walk", "Sprint", "Walk_Carry", "Idle_A"]:
    check("clip " + want, want in anim_names)

print("=" * 78)
print("mapped bones    :", len(human_table))
print("unmapped (leaf) :", len(unmapped))
if failures:
    print("RESULT: " + str(len(failures)) + " FAILED")
    sys.exit(1)
print("RESULT: all checks passed")