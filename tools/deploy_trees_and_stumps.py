#!/usr/bin/env python3
import os
import json
import urllib.request
import shutil
from PIL import Image

ASSETS_DIR = r"C:\Users\casey\Desktop\Homesteader\assets\logging"
MESHY_OUT = r"C:\Users\casey\Desktop\Homesteader\scratch\meshy_output"
API_KEY = "msy_mUvsQRtfvX2levWkmugKy3nFHSp3Yyf0Y4Cx"

tree_tasks = {
    'tree_apple_small': {
        'task_id': '01a0a226-cf19-7088-a482-77e3cb2e6ec9',
        'folder': '20260914_180049_stylized-low-poly-small-young_01a0a226',
        'fbx_name': 'SM_Tree_Apple_Small.fbx'
    },
    'tree_apple_medium': {
        'task_id': '01a0a226-e113-7688-8da6-1b0f3917a4de',
        'folder': '20260914_180054_stylized-low-poly-medium-half_01a0a226',
        'fbx_name': 'SM_Tree_Apple_Medium.fbx'
    },
    'tree_willow_small': {
        'task_id': '01a0a226-f4a3-74ff-a3c4-9b41e5b82f7a',
        'folder': '20260914_180059_stylized-low-poly-small-young_01a0a226',
        'fbx_name': 'SM_Tree_Willow_Small.fbx'
    },
    'tree_willow_medium': {
        'task_id': '01a0a227-0973-76e4-bca1-69f67ab62a1e',
        'folder': '20260914_180104_stylized-low-poly-medium-half_01a0a227',
        'fbx_name': 'SM_Tree_Willow_Medium.fbx'
    },
    'tree_poplar_small': {
        'task_id': '01a0a227-1d81-716b-8487-98ff2f9c688e',
        'folder': '20260914_180110_stylized-low-poly-small-young_01a0a227',
        'fbx_name': 'SM_Tree_Poplar_Small.fbx'
    },
    'tree_poplar_medium': {
        'task_id': '01a0a227-2ff7-7316-84d8-21cdfe8ed971',
        'folder': '20260914_180114_stylized-low-poly-medium-half_01a0a227',
        'fbx_name': 'SM_Tree_Poplar_Medium.fbx'
    }
}

stump_species_tasks = {
    'oak': {
        'task_id': '01a0a227-92cb-74a7-a1fc-c72cf5fe4bad',
        'folder': '20260914_180140_stylized-low-poly-cut-oak-tree_01a0a227'
    },
    'birch': {
        'task_id': '01a0a227-a765-7785-aed8-9d856b06e9f8',
        'folder': '20260914_180145_stylized-low-poly-cut-white-bi_01a0a227'
    },
    'pine': {
        'task_id': '01a0a227-bab2-7610-b4b4-959317ad7695',
        'folder': '20260914_180150_stylized-low-poly-cut-evergree_01a0a227'
    },
    'maple': {
        'task_id': '01a0a227-cba3-71f7-af06-65e583ab6c4b',
        'folder': '20260914_180154_stylized-low-poly-cut-sugar-ma_01a0a227'
    },
    'apple': {
        'task_id': '01a0a227-e171-70c6-9d3e-915252141f69',
        'folder': '20260914_180201_stylized-low-poly-cut-apple-or_01a0a227'
    },
    'willow': {
        'task_id': '01a0a227-f721-71b3-afe7-c99bd2bcfeec',
        'folder': '20260914_180205_stylized-low-poly-cut-weeping_01a0a227'
    },
    'poplar': {
        'task_id': '01a0a228-09e7-76e7-aa73-bd709a4ee4b9',
        'folder': '20260914_180210_stylized-low-poly-cut-columnar_01a0a228'
    }
}

flora_stump_task = {
    'flora_tree_stump': {
        'task_id': '01a0a228-1beb-774f-8e00-d5e54a51746e',
        'folder': '20260914_180215_stylized-low-poly-weathered-an_01a0a228',
        'fbx_name': 'SM_Flora_Tree_Stump.fbx'
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

def deploy_item(item_id, src_fbx, fbx_name, alpha_url):
    item_dir = os.path.join(ASSETS_DIR, item_id)
    os.makedirs(item_dir, exist_ok=True)
    
    dest_fbx = os.path.join(item_dir, fbx_name)
    shutil.copyfile(src_fbx, dest_fbx)
    
    # Remove old non-FBX models
    for f in os.listdir(item_dir):
        if f.endswith(('.obj', '.mtl', '.glb', '.stl', '.usdz')):
            os.remove(os.path.join(item_dir, f))
            
    # Icon
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
            "description": "Standard logging asset used in the Homesteader simulation.",
            "icon": f"{item_id}.png",
            "properties": {
                "weight_kg": 5.0,
                "max_stack_size": 99,
                "base_value": 10.0,
                "is_consumable": False,
                "footprint": "1x1"
            }
        }
    d["models"] = [{"file": fbx_name, "format": "fbx"}]
    with open(json_path, "w", encoding="utf-8") as jf:
        json.dump(d, jf, indent=2)
        
    print(f"Deployed {item_id}: {fbx_name} ({os.path.getsize(dest_fbx):,} bytes) + 128x128 icon")

def main():
    print("=== Deploying Small & Medium Trees ===")
    for item_id, info in tree_tasks.items():
        src_fbx = os.path.join(MESHY_OUT, info['folder'], 'preview.fbx')
        alpha_url = get_alpha_url(info['task_id'])
        deploy_item(item_id, src_fbx, info['fbx_name'], alpha_url)
        
    print("\n=== Deploying Species Stumps (Small, Medium, Large) ===")
    for sp, info in stump_species_tasks.items():
        src_fbx = os.path.join(MESHY_OUT, info['folder'], 'preview.fbx')
        alpha_url = get_alpha_url(info['task_id'])
        for size in ['small', 'medium', 'large']:
            item_id = f"stump_{sp}_{size}"
            fbx_name = f"SM_Stump_{sp.capitalize()}_{size.capitalize()}.fbx"
            deploy_item(item_id, src_fbx, fbx_name, alpha_url)
            
    print("\n=== Deploying Flora Tree Stump ===")
    for item_id, info in flora_stump_task.items():
        src_fbx = os.path.join(MESHY_OUT, info['folder'], 'preview.fbx')
        alpha_url = get_alpha_url(info['task_id'])
        deploy_item(item_id, src_fbx, info['fbx_name'], alpha_url)
        
    print("\nAll trees and stumps successfully deployed!")

if __name__ == "__main__":
    main()

