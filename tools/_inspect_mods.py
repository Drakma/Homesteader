import os
import json

root = r"C:\Users\casey\Desktop\Homesteader\mods"
mods = [d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d))]
print(f"Total mods: {len(mods)}")
for m in sorted(mods):
    m_dir = os.path.join(root, m)
    manifest = os.path.join(m_dir, "mod.json")
    if os.path.exists(manifest):
        with open(manifest, "r", encoding="utf-8") as f:
            d = json.load(f)
            assets_count = 0
            assets_path = os.path.join(m_dir, "assets")
            if os.path.exists(assets_path):
                for cat in os.listdir(assets_path):
                    cat_p = os.path.join(assets_path, cat)
                    if os.path.isdir(cat_p):
                        assets_count += len([x for x in os.listdir(cat_p) if os.path.isdir(os.path.join(cat_p, x))])
            print(f"  {m}: name='{d.get('name')}', assets={assets_count}")
