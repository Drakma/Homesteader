#!/usr/bin/env python3
# Verifies the _read_glb_summary fix in mesh2motion_mcp.py against real files.
# Before the fix this returned "first GLB chunk is not JSON" for every valid GLB.

import importlib.util
import os
import sys

TOOLS = r"C:\Users\casey\Desktop\Homesteader\tools"
sys.path.insert(0, TOOLS)

spec = importlib.util.spec_from_file_location(
    "mesh2motion_mcp", os.path.join(TOOLS, "mesh2motion_mcp.py")
)
mod = importlib.util.module_from_spec(spec)
# Import executes module scope only (mcp.run is guarded by __main__).
spec.loader.exec_module(mod)

CASES = [
    r"C:\Users\casey\Desktop\Homesteader\assets\peds\peds_old_farmer\peds_old_farmer.glb",
    r"C:\Users\casey\Desktop\Homesteader\assets\peds\peds_old_farmer\peds_old_farmer_Rigged.glb",
    r"C:\Users\casey\Desktop\Homesteader\tools\mesh2motion\static\rigs\rig-human.glb",
    r"C:\Users\casey\Desktop\Homesteader\tools\mesh2motion\static\animations\human-base-animations.glb",
]

failures = 0
for path in CASES:
    summary = mod._read_glb_summary(path)
    ok = summary.get("valid_glb")
    if not ok:
        failures += 1
    print("=" * 78)
    print(os.path.basename(path))
    print("  valid_glb       : " + str(ok))
    if not ok:
        print("  ERROR           : " + str(summary.get("error")))
        continue
    print("  animations      : " + str(summary.get("animation_count")))
    print("  animation_names : " + str(summary.get("animation_names")))
    print("  skins           : " + str(summary.get("skin_count")))
    print("  joints          : " + str(summary.get("joint_count")))
    print("  meshes          : " + str(summary.get("mesh_count")))

print("=" * 78)
print("parsed OK: " + str(len(CASES) - failures) + "/" + str(len(CASES)))
