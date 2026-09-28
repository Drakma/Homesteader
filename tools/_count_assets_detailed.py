import os
import json

root = r"C:\Users\casey\Desktop\Homesteader"
assets_dir = os.path.join(root, "assets")

excluded_cats = {"ground", "hud", "hud_kit", "peds"}
categories = [d for d in os.listdir(assets_dir) 
              if os.path.isdir(os.path.join(assets_dir, d)) 
              and not d.startswith("_") 
              and d not in excluded_cats
              and d != "models_legacy"
              and d != "textures"]

stats = {
    "total_items": 0,
    "png_icons": 0,
    "json_manifests": 0,
    "models": 0, # fbx, obj, glb, gltf
    "model_exts": {}
}

model_exts = {".fbx", ".obj", ".glb", ".gltf"}

for cat in categories:
    cat_dir = os.path.join(assets_dir, cat)
    for it in os.listdir(cat_dir):
        it_dir = os.path.join(cat_dir, it)
        if not os.path.isdir(it_dir):
            continue
        # Check if group
        manifest = os.path.join(it_dir, f"{it}.json")
        is_group = False
        if os.path.exists(manifest):
            try:
                with open(manifest, "r", encoding="utf-8") as f:
                    d = json.load(f)
                    if "stages" in d or "growth_group" in d or d.get("type") in ("growth_group", "structure_group"):
                        is_group = True
            except Exception:
                pass
        if os.path.exists(os.path.join(it_dir, "stages")):
            is_group = True
        if is_group:
            continue

        stats["total_items"] += 1
        for f in os.listdir(it_dir):
            ext = os.path.splitext(f)[1].lower()
            if ext == ".png":
                stats["png_icons"] += 1
            elif ext == ".json":
                stats["json_manifests"] += 1
            elif ext in model_exts:
                stats["models"] += 1
                stats["model_exts"][ext] = stats["model_exts"].get(ext, 0) + 1

print("Regular items stats across all target categories:")
print(stats)
