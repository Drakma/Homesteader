#!/usr/bin/env python3
import os
import json
import urllib.request
import shutil
from PIL import Image

ASSETS_DIR = r"C:\Users\casey\Desktop\Homesteader\assets\logging"
MESHY_OUT = r"C:\Users\casey\Desktop\Homesteader\HUD\meshy_output"
API_KEY = "msy_mUvsQRtfvX2levWkmugKy3nFHSp3Yyf0Y4Cx"

sapling_tasks = {
    'sapling_oak': {
        'task_id': '01a0a263-6d83-73d6-ae27-930b9d5b68aa',
        'folder': '20260914_190702_stylized-low-poly-young-nurser_01a0a263',
        'fbx_name': 'SM_Sapling_Oak.fbx'
    },
    'sapling_birch': {
        'task_id': '01a0a263-8243-736e-8282-a7ec5f177734',
        'folder': '20260914_190707_stylized-low-poly-young-nurser_01a0a263',
        'fbx_name': 'SM_Sapling_Birch.fbx'
    },
    'sapling_pine': {
        'task_id': '01a0a263-99ee-7014-bd8c-5c15e92cf222',
        'folder': '20260914_190713_stylized-low-poly-young-nurser_01a0a263',
        'fbx_name': 'SM_Sapling_Pine.fbx'
    },
    'sapling_maple': {
        'task_id': '01a0a263-aeb4-70a3-a75f-0dcfb7d3a7ef',
        'folder': '20260914_190719_stylized-low-poly-young-nurser_01a0a263',
        'fbx_name': 'SM_Sapling_Maple.fbx'
    },
    'sapling_apple': {
        'task_id': '01a0a263-c33e-7363-827d-39c086cec7c1',
        'folder': '20260914_190724_stylized-low-poly-young-nurser_01a0a263',
        'fbx_name': 'SM_Sapling_Apple.fbx'
    },
    'sapling_willow': {
        'task_id': '01a0a263-d554-7234-b543-6b010c302078',
        'folder': '20260914_190729_stylized-low-poly-young-nurser_01a0a263',
        'fbx_name': 'SM_Sapling_Willow.fbx'
    },
    'sapling_poplar': {
        'task_id': '01a0a263-ed0c-706e-a68e-9604c7d551aa',
        'folder': '20260914_190735_stylized-low-poly-young-nurser_01a0a263',
        'fbx_name': 'SM_Sapling_Poplar.fbx'
    }
}

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

def get_alpha_url(task_id):
    req = urllib.request.Request(f"https://api.meshy.ai/openapi/v2/text-to-3d/{task_id}", headers={"Authorization": f"Bearer {API_KEY}"})
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        return data.get("alpha_thumbnail_url") or data.get("thumbnail_url")

def deploy_sapling(item_id, info):
    item_dir = os.path.join(ASSETS_DIR, item_id)
    os.makedirs(item_dir, exist_ok=True)
    
    src_fbx = os.path.join(MESHY_OUT, info['folder'], 'preview.fbx')
    dest_fbx = os.path.join(item_dir, info['fbx_name'])
    shutil.copyfile(src_fbx, dest_fbx)
    
    # Remove old non-FBX models
    for f in os.listdir(item_dir):
        if f.endswith(('.obj', '.mtl', '.glb', '.stl', '.usdz')):
            os.remove(os.path.join(item_dir, f))
            
    # Icon
    alpha_url = get_alpha_url(info['task_id'])
    icon_path = os.path.join(item_dir, f"{item_id}.png")
    make_128_icon(alpha_url, icon_path)
    
    # Update manifest
    json_path = os.path.join(item_dir, f"{item_id}.json")
    d = {}
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as jf:
            d = json.load(jf)
    else:
        d = {
            "$schema": "https://homesteader.game/schemas/item_v1.json",
            "id": item_id,
            "name": item_id.replace("_", " ").title(),
            "category": "logging",
            "description": "Bagged nursery tree sapling in burlap root ball.",
            "icon": f"{item_id}.png",
            "properties": {
                "weight_kg": 2.5,
                "max_stack_size": 20,
                "base_value": 15.0,
                "is_consumable": False,
                "footprint": "1x1"
            }
        }
    d["models"] = [{"file": info['fbx_name'], 'format': 'fbx'}]
    with open(json_path, "w", encoding="utf-8") as jf:
        json.dump(d, jf, indent=2)
        
    print(f"Deployed {item_id}: {info['fbx_name']} ({os.path.getsize(dest_fbx):,} bytes) + 128x128 icon")

def main():
    print("=== Deploying Bagged Nursery Saplings ===")
    for item_id, info in sapling_tasks.items():
        deploy_sapling(item_id, info)
    print("\nAll bagged saplings successfully deployed!")

if __name__ == "__main__":
    main()

