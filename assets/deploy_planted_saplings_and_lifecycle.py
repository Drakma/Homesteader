#!/usr/bin/env python3
import os
import json
import urllib.request
import shutil
from PIL import Image

API_KEY = "msy_mUvsQRtfvX2levWkmugKy3nFHSp3Yyf0Y4Cx"
ASSETS_LOGGING = r"C:\Users\casey\Desktop\Homesteader\assets\logging"

planted_tasks = {
    'oak': '01a0a1d2-dc85-7689-83d8-14da681d6866',
    'birch': '01a0a1d2-e166-71c5-9577-07df6ff6ea83',
    'pine': '01a0a1d2-e643-7212-9d27-5176ce3a795f',
    'maple': '01a0a1d2-eb25-76aa-9f6d-84e0accb67d5',
    'apple': '01a0a1d2-f025-73be-8a5e-ea20dc69232f',
    'willow': '01a0a1d2-f505-7085-9a58-110ab17e9737',
    'poplar': '01a0a1d2-f9e4-7690-aed0-0c3b90debf5b'
}

def make_128_icon(url, dest_icon_path):
    tmp_path = dest_icon_path + ".tmp.png"
    urllib.request.urlretrieve(url, tmp_path)
    img = Image.open(tmp_path).convert("RGBA")
    bbox = img.getbbox()
    if bbox:
        img = img.crop(bbox)
    w, h = img.size
    scale = min(104 / w, 104 / h)
    new_w = max(1, int(round(w * scale)))
    new_h = max(1, int(round(h * scale)))
    resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    
    final_img = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
    final_img.paste(resized, ((128 - new_w) // 2, (128 - new_h) // 2), resized)
    final_img.save(dest_icon_path, "PNG")
    if os.path.exists(tmp_path):
        os.remove(tmp_path)

def main():
    print("=== DEPLOYING PLANTED SAPLINGS & 1:1 TEXTURED ICONS ===")
    
    for species, task_id in planted_tasks.items():
        item_id = f"planted_sapling_{species}"
        item_dir = os.path.join(ASSETS_LOGGING, item_id)
        os.makedirs(item_dir, exist_ok=True)
        
        # 1. Fetch task info from Meshy
        req = urllib.request.Request(f"https://api.meshy.ai/openapi/v2/text-to-3d/{task_id}", headers={"Authorization": f"Bearer {API_KEY}"})
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            
        thumb_url = data.get("alpha_thumbnail_url") or data.get("thumbnail_url")
        icon_path = os.path.join(item_dir, f"{item_id}.png")
        make_128_icon(thumb_url, icon_path)
        
        # Ensure non-FBX models removed
        for f in os.listdir(item_dir):
            if f.lower().endswith(('.obj', '.mtl', '.glb', '.stl', '.usdz')):
                os.remove(os.path.join(item_dir, f))
                
        # Manifest
        fbx_name = f"SM_PlantedSapling{species.capitalize()}.fbx"
        json_path = os.path.join(item_dir, f"{item_id}.json")
        if os.path.exists(json_path):
            with open(json_path, "r", encoding="utf-8") as jf:
                d = json.load(jf)
        else:
            d = {
                "$schema": "https://homesteader.game/schemas/item_v1.json",
                "id": item_id,
                "name": f"Planted Sapling {species.capitalize()}",
                "category": "logging",
                "description": f"Young in-ground {species} sapling growing in a soil mound.",
                "icon": f"{item_id}.png"
            }
        d["models"] = [{"file": fbx_name, "format": "fbx"}]
        # Set growth stage 1 to planted_sapling_<species>
        if "growth" in d and "stages" in d["growth"]:
            for st in d["growth"]["stages"]:
                if st.get("stage") == 1:
                    st["item_id"] = item_id
                    st["name"] = "planted_sapling"
        with open(json_path, "w", encoding="utf-8") as jf:
            json.dump(d, jf, indent=2)
            
        print(f"  [DEPLOYED] {item_id}: {fbx_name} + 128x128 textured icon")
        
    # 2. Update generic tree_sapling to match planted_sapling_oak
    print("\nUpdating generic tree_sapling to match planted_sapling_oak...")
    tree_sap_dir = os.path.join(ASSETS_LOGGING, "tree_sapling")
    oak_planted_dir = os.path.join(ASSETS_LOGGING, "planted_sapling_oak")
    shutil.copyfile(os.path.join(oak_planted_dir, "SM_PlantedSaplingOak.fbx"), os.path.join(tree_sap_dir, "SM_Tree_Sapling.fbx"))
    shutil.copyfile(os.path.join(oak_planted_dir, "planted_sapling_oak.png"), os.path.join(tree_sap_dir, "tree_sapling.png"))
    
    sap_json = os.path.join(tree_sap_dir, "tree_sapling.json")
    with open(sap_json, "r", encoding="utf-8") as jf:
        d = json.load(jf)
    d["models"] = [{"file": "SM_Tree_Sapling.fbx", "format": "fbx"}]
    if "growth" in d and "stages" in d["growth"]:
        for st in d["growth"]["stages"]:
            if st.get("stage") == 1:
                st["item_id"] = "planted_sapling_oak"
                st["name"] = "planted_sapling"
    with open(sap_json, "w", encoding="utf-8") as jf:
        json.dump(d, jf, indent=2)
    print("  [SYNCED] tree_sapling -> SM_Tree_Sapling.fbx (planted oak sapling) + icon")
    
    # 3. Update all tree species growth stages across small, medium, and large
    print("\nUpdating tree lifecycle stages in all tree manifests...")
    all_species = ['oak', 'birch', 'pine', 'maple', 'apple', 'willow', 'poplar']
    updated_manifests = 0
    for s in all_species:
        for suffix in ['small', 'medium', 'large', 'tall', 'columnar', '']:
            item_name = f"tree_{s}_{suffix}" if suffix else f"tree_{s}"
            item_dir = os.path.join(ASSETS_LOGGING, item_name)
            if not os.path.exists(item_dir):
                continue
            mf = os.path.join(item_dir, f"{item_name}.json")
            if not os.path.exists(mf):
                continue
            try:
                with open(mf, "r", encoding="utf-8") as jf:
                    data = json.load(jf)
                if "growth" in data and "stages" in data["growth"]:
                    for st in data["growth"]["stages"]:
                        if st.get("stage") == 1:
                            st["item_id"] = f"planted_sapling_{s}"
                            st["name"] = "planted_sapling"
                    with open(mf, "w", encoding="utf-8") as jf:
                        json.dump(data, jf, indent=2)
                    updated_manifests += 1
            except Exception as e:
                print(f"Error on {mf}: {e}")
                
    print(f"Synchronized {updated_manifests} tree manifests to link Stage 1 -> planted_sapling_<species>.")

if __name__ == "__main__":
    main()

