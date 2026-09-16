#!/usr/bin/env python3
import os
import time
import json
import urllib.request
import shutil
from PIL import Image

API_KEY = "msy_mUvsQRtfvX2levWkmugKy3nFHSp3Yyf0Y4Cx"
ASSETS_LOGGING = r"C:\Users\casey\Desktop\Homesteader\assets\logging"
MESHY_DOWNLOADS = r"C:\Users\casey\Desktop\Homesteader\HUD\meshy_output\refine_downloads"
os.makedirs(MESHY_DOWNLOADS, exist_ok=True)

# 29 Preview Tasks
ITEMS = [
    # 7 Bagged Saplings
    {"item_id": "sapling_oak", "preview_id": "01a0a263-6d83-73d6-ae27-930b9d5b68aa", "fbx_name": "SM_Sapling_Oak.fbx", "known_refine_id": "01a0a26d-b1ca-71db-9139-59d7014305da"},
    {"item_id": "sapling_birch", "preview_id": "01a0a263-8243-736e-8282-a7ec5f177734", "fbx_name": "SM_Sapling_Birch.fbx", "known_refine_id": "01a0a26d-d603-769e-8049-ca1608cd8356"},
    {"item_id": "sapling_pine", "preview_id": "01a0a263-99ee-7014-bd8c-5c15e92cf222", "fbx_name": "SM_Sapling_Pine.fbx"},
    {"item_id": "sapling_maple", "preview_id": "01a0a263-aeb4-70a3-a75f-0dcfb7d3a7ef", "fbx_name": "SM_Sapling_Maple.fbx"},
    {"item_id": "sapling_apple", "preview_id": "01a0a263-c33e-7363-827d-39c086cec7c1", "fbx_name": "SM_Sapling_Apple.fbx"},
    {"item_id": "sapling_willow", "preview_id": "01a0a263-d554-7234-b543-6b010c302078", "fbx_name": "SM_Sapling_Willow.fbx"},
    {"item_id": "sapling_poplar", "preview_id": "01a0a263-ed0c-706e-a68e-9604c7d551aa", "fbx_name": "SM_Sapling_Poplar.fbx"},

    # 7 Small Trees
    {"item_id": "tree_oak_small", "preview_id": "01a0a21a-b888-74ac-9bd1-5d3deb5e3ee8", "fbx_name": "SM_Tree_Oak_Small.fbx"},
    {"item_id": "tree_birch_small", "preview_id": "01a0a220-1bee-7576-86b2-cb3a7fb00e9f", "fbx_name": "SM_Tree_Birch_Small.fbx"},
    {"item_id": "tree_pine_small", "preview_id": "01a0a220-2c31-7379-8043-881e468ab656", "fbx_name": "SM_Tree_Pine_Small.fbx"},
    {"item_id": "tree_maple_small", "preview_id": "01a0a220-3e78-7013-ab79-ab99d945a5ee", "fbx_name": "SM_Tree_Maple_Small.fbx"},
    {"item_id": "tree_apple_small", "preview_id": "01a0a226-cf19-7088-a482-77e3cb2e6ec9", "fbx_name": "SM_Tree_Apple_Small.fbx"},
    {"item_id": "tree_willow_small", "preview_id": "01a0a226-f4a3-74ff-a3c4-9b41e5b82f7a", "fbx_name": "SM_Tree_Willow_Small.fbx"},
    {"item_id": "tree_poplar_small", "preview_id": "01a0a227-1d81-716b-8487-98ff2f9c688e", "fbx_name": "SM_Tree_Poplar_Small.fbx"},

    # 7 Medium Trees
    {"item_id": "tree_oak_medium", "preview_id": "01a0a220-5150-742c-b3a1-77c4686d649c", "fbx_name": "SM_Tree_Oak_Medium.fbx"},
    {"item_id": "tree_birch_medium", "preview_id": "01a0a220-64f5-7029-8789-d64fdbe39774", "fbx_name": "SM_Tree_Birch_Medium.fbx"},
    {"item_id": "tree_pine_medium", "preview_id": "01a0a220-76f9-7671-88ca-938367b8fa23", "fbx_name": "SM_Tree_Pine_Medium.fbx"},
    {"item_id": "tree_maple_medium", "preview_id": "01a0a220-8c35-74d9-9956-6c21a4c680e1", "fbx_name": "SM_Tree_Maple_Medium.fbx"},
    {"item_id": "tree_apple_medium", "preview_id": "01a0a226-e113-7688-8da6-1b0f3917a4de", "fbx_name": "SM_Tree_Apple_Medium.fbx"},
    {"item_id": "tree_willow_medium", "preview_id": "01a0a227-0973-76e4-bca1-69f67ab62a1e", "fbx_name": "SM_Tree_Willow_Medium.fbx"},
    {"item_id": "tree_poplar_medium", "preview_id": "01a0a227-2ff7-7316-84d8-21cdfe8ed971", "fbx_name": "SM_Tree_Poplar_Medium.fbx"},

    # 8 Stumps (Species map to small, medium, large)
    {"item_id": "stump_oak", "preview_id": "01a0a227-92cb-74a7-a1fc-c72cf5fe4bad", "species": "oak", "is_stump_species": True},
    {"item_id": "stump_birch", "preview_id": "01a0a227-a765-7785-aed8-9d856b06e9f8", "species": "birch", "is_stump_species": True},
    {"item_id": "stump_pine", "preview_id": "01a0a227-bab2-7610-b4b4-959317ad7695", "species": "pine", "is_stump_species": True},
    {"item_id": "stump_maple", "preview_id": "01a0a227-cba3-71f7-af06-65e583ab6c4b", "species": "maple", "is_stump_species": True},
    {"item_id": "stump_apple", "preview_id": "01a0a227-e171-70c6-9d3e-915252141f69", "species": "apple", "is_stump_species": True},
    {"item_id": "stump_willow", "preview_id": "01a0a227-f721-71b3-afe7-c99bd2bcfeec", "species": "willow", "is_stump_species": True},
    {"item_id": "stump_poplar", "preview_id": "01a0a228-09e7-76e7-aa73-bd709a4ee4b9", "species": "poplar", "is_stump_species": True},
    {"item_id": "flora_tree_stump", "preview_id": "01a0a228-1beb-774f-8e00-d5e54a51746e", "fbx_name": "SM_Flora_Tree_Stump.fbx"}
]

STATE_FILE = r"C:\Users\casey\Desktop\Homesteader\assets\refine_state.json"

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_state(st):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(st, f, indent=2)

def trigger_refine(preview_id):
    url = "https://api.meshy.ai/openapi/v2/text-to-3d"
    payload = {
        "mode": "refine",
        "preview_task_id": preview_id,
        "texture_resolution": "2k",
        "remove_lighting": True,
        "target_formats": ["fbx"]
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
    )
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        return res.get("result")

def get_task_info(task_id):
    url = f"https://api.meshy.ai/openapi/v2/text-to-3d/{task_id}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {API_KEY}"})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def make_128_icon(alpha_url, dest_icon_path):
    tmp_path = dest_icon_path + ".tmp.png"
    urllib.request.urlretrieve(alpha_url, tmp_path)
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
    state = load_state()
    print("=== STEP 1: Launching Refine Tasks ===")
    for item in ITEMS:
        iid = item["item_id"]
        if iid in state and "refine_id" in state[iid]:
            continue
        
        if "known_refine_id" in item:
            refine_id = item["known_refine_id"]
        else:
            refine_id = trigger_refine(item["preview_id"])
            print(f"Triggered refine for {iid} -> {refine_id}")
            time.sleep(0.3)
        state[iid] = {
            "item_id": iid,
            "preview_id": item["preview_id"],
            "refine_id": refine_id,
            "status": "IN_PROGRESS"
        }
        save_state(state)
        
    print(f"\nAll {len(ITEMS)} refine tasks active! Monitoring status...")
    save_state(state)

if __name__ == "__main__":
    main()

