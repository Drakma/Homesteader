#!/usr/bin/env python3
import os
import sys
import time
import json
import urllib.request
import shutil
from PIL import Image

API_KEY = "msy_mUvsQRtfvX2levWkmugKy3nFHSp3Yyf0Y4Cx"
ASSETS_LOGGING = r"C:\Users\casey\Desktop\Homesteader\assets\logging"
STATE_FILE = r"C:\Users\casey\Desktop\Homesteader\assets\refine_state.json"
CACHE_DIR = r"C:\Users\casey\Desktop\Homesteader\scratch\meshy_output\refined_assets"
os.makedirs(CACHE_DIR, exist_ok=True)

def get_task_status(task_id):
    url = f"https://api.meshy.ai/openapi/v2/text-to-3d/{task_id}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {API_KEY}"})
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"Error fetching status for {task_id}: {e}")
        return None

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

def deploy_single_asset(item_id, fbx_url, icon_url, fbx_filename):
    item_dir = os.path.join(ASSETS_LOGGING, item_id)
    os.makedirs(item_dir, exist_ok=True)
    
    # Download FBX
    dest_fbx = os.path.join(item_dir, fbx_filename)
    tmp_fbx = os.path.join(CACHE_DIR, f"{item_id}_{fbx_filename}")
    urllib.request.urlretrieve(fbx_url, tmp_fbx)
    shutil.copyfile(tmp_fbx, dest_fbx)
    
    # Remove old non-FBX models
    for f in os.listdir(item_dir):
        if f.lower().endswith(('.obj', '.mtl', '.glb', '.stl', '.usdz')):
            os.remove(os.path.join(item_dir, f))
            
    # Download and format Icon
    dest_icon = os.path.join(item_dir, f"{item_id}.png")
    make_128_icon(icon_url, dest_icon)
    
    # Update manifest
    json_path = os.path.join(item_dir, f"{item_id}.json")
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as jf:
            d = json.load(jf)
    else:
        d = {
            "$schema": "https://homesteader.game/schemas/item_v1.json",
            "id": item_id,
            "name": item_id.replace("_", " ").title(),
            "category": "logging",
            "description": "Textured logging asset in Homesteader simulation.",
            "icon": f"{item_id}.png"
        }
    d["models"] = [{"file": fbx_filename, "format": "fbx"}]
    with open(json_path, "w", encoding="utf-8") as jf:
        json.dump(d, jf, indent=2)
        
    print(f"  [DEPLOYED] {item_id}: {fbx_filename} ({os.path.getsize(dest_fbx):,} bytes) + 128x128 textured icon")

def deploy_stump_species(species, fbx_url, icon_url):
    for size in ['small', 'medium', 'large']:
        item_id = f"stump_{species}_{size}"
        fbx_name = f"SM_Stump_{species.capitalize()}_{size.capitalize()}.fbx"
        deploy_single_asset(item_id, fbx_url, icon_url, fbx_name)

def main():
    print("=== MONITORING 29 MESHY TEXTURING REFINE TASKS ===")
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        state = json.load(f)
        
    completed_ids = set()
    for item_id, info in state.items():
        if info.get("deployed"):
            completed_ids.add(item_id)
            
    start_time = time.time()
    while len(completed_ids) < len(state):
        remaining = [k for k in state if k not in completed_ids]
        print(f"\n--- Checking {len(remaining)} pending tasks ({len(completed_ids)}/{len(state)} completed) ---")
        
        for item_id in remaining:
            info = state[item_id]
            refine_id = info["refine_id"]
            data = get_task_status(refine_id)
            if not data:
                continue
                
            status = data.get("status")
            progress = data.get("progress", 0)
            
            if status == "SUCCEEDED":
                print(f"\n>>> Task SUCCEEDED for {item_id} (refine_id: {refine_id})! Deploying...")
                model_urls = data.get("model_urls", {})
                fbx_url = model_urls.get("fbx")
                icon_url = data.get("alpha_thumbnail_url") or data.get("thumbnail_url")
                
                if not fbx_url:
                    print(f"Warning: No FBX URL for {item_id}, available: {model_urls.keys()}")
                    continue
                    
                if item_id.startswith("stump_"):
                    species = item_id.replace("stump_", "")
                    deploy_stump_species(species, fbx_url, icon_url)
                elif item_id == "flora_tree_stump":
                    deploy_single_asset(item_id, fbx_url, icon_url, "SM_Flora_Tree_Stump.fbx")
                elif item_id.startswith("sapling_"):
                    species = item_id.replace("sapling_", "")
                    fbx_name = f"SM_Sapling_{species.capitalize()}.fbx"
                    deploy_single_asset(item_id, fbx_url, icon_url, fbx_name)
                    if species == "oak":
                        deploy_single_asset("tree_sapling", fbx_url, icon_url, "SM_Tree_Sapling.fbx")
                elif item_id.startswith("tree_"):
                    # tree_<species>_<size>
                    parts = item_id.split("_")
                    species = parts[1]
                    size = parts[2]
                    fbx_name = f"SM_Tree_{species.capitalize()}_{size.capitalize()}.fbx"
                    deploy_single_asset(item_id, fbx_url, icon_url, fbx_name)
                    
                info["deployed"] = True
                info["status"] = "SUCCEEDED"
                completed_ids.add(item_id)
                with open(STATE_FILE, "w", encoding="utf-8") as f:
                    json.dump(state, f, indent=2)
            elif status == "FAILED":
                print(f"Error: Task FAILED for {item_id}: {data.get('task_error')}")
                completed_ids.add(item_id)
            else:
                print(f"  {item_id}: {status} ({progress}%)", end=" | ")
                
            time.sleep(0.2)
            
        if len(completed_ids) < len(state):
            print(f"\nWaiting 20 seconds before next poll... (Elapsed: {int(time.time() - start_time)}s)")
            time.sleep(20)
            
    print("\nAll 29 texturing tasks completed and deployed successfully!")

if __name__ == "__main__":
    main()

