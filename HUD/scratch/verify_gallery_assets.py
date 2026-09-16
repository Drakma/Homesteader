import json
import os
import re

hud_root = r"c:\Users\casey\Desktop\Homesteader\HUD"
index_path = os.path.join(hud_root, "index.html")
with open(index_path, "r", encoding="utf-8") as f:
    html = f.read()

# Extract ALL_ITEM_ICONS
m = re.search(r"const ALL_ITEM_ICONS = (\[.*?\]);", html, re.DOTALL)
if not m:
    print("Could not find ALL_ITEM_ICONS")
else:
    icons = json.loads(m.group(1))
    print(f"Checking {len(icons)} item icons in ALL_ITEM_ICONS...")
    missing = []
    for item in icons:
        iid = item["id"]
        path = os.path.join(hud_root, "assets", "items", f"{iid}.png")
        if not os.path.exists(path):
            missing.append((iid, path))
    if missing:
        print(f"ERROR: {len(missing)} missing item icons!")
        for iid, p in missing[:10]:
            print(f"  Missing: {iid} -> {p}")
    else:
        print("ALL item icon PNGs exist!")

# Check models in each category
model_arrays = [
    ("GROUND_ASSETS", "assets/ground/models", "assets/ground/icons"),
    ("BUILDING_ASSETS", "assets/building/structures", "assets/building/icons"),
    ("FOLIAGE_ASSETS", "assets/foliage/models", "assets/foliage/icons"),
    ("UTILITY_ASSETS", "assets/utilities/models", "assets/utilities/icons"),
    ("RANCHING_ASSETS", "assets/ranching/models", "assets/ranching/icons"),
    ("FARMING_ASSETS", "assets/farming/models", "assets/farming/icons"),
    ("TOOLS_ASSETS", "assets/tools/models", "assets/tools/icons"),
    ("MATERIALS_ASSETS", "assets/building/models", "assets/building/icons"),
    ("LOGGING_ASSETS", "assets/logging/models", "assets/logging/icons"),
    ("FISHING_ASSETS", "assets/fishing/models", "assets/fishing/icons"),
]

total_models_checked = 0
total_missing = 0
for var_name, model_dir, icon_dir in model_arrays:
    m = re.search(rf"const {var_name} = (\[.*?\]);", html, re.DOTALL)
    if not m:
        print(f"Could not find {var_name}")
        continue
    items = json.loads(m.group(1))
    total_models_checked += len(items)
    for it in items:
        mid = it["id"]
        obj_p = os.path.join(hud_root, model_dir, f"{mid}.obj")
        mtl_p = os.path.join(hud_root, model_dir, f"{mid}.mtl")
        icon_p = os.path.join(hud_root, icon_dir, f"{mid}.png")
        for p, desc in [(obj_p, "OBJ"), (mtl_p, "MTL"), (icon_p, "Icon")]:
            if not os.path.exists(p):
                print(f"Missing {var_name} asset {mid} ({desc}) at {p}")
                total_missing += 1

print(f"Checked {total_models_checked} 3D model entries in index.html across all 10 galleries. Total missing files: {total_missing}")

