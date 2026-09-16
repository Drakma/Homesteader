#!/usr/bin/env python3
import os
import json
import urllib.request
import shutil
from PIL import Image

tasks = {
    'tree_birch_small': {
        'task_id': '01a0a220-1bee-7576-86b2-cb3a7fb00e9f',
        'fbx_folder': '20260914_175330_stylized-low-poly-small-young_01a0a220',
        'fbx_name': 'SM_Tree_Birch_Small.fbx'
    },
    'tree_pine_small': {
        'task_id': '01a0a220-2c31-7379-8043-881e468ab656',
        'fbx_folder': '20260914_175334_stylized-low-poly-small-young_01a0a220',
        'fbx_name': 'SM_Tree_Pine_Small.fbx'
    },
    'tree_maple_small': {
        'task_id': '01a0a220-3e78-7013-ab79-ab99d945a5ee',
        'fbx_folder': '20260914_175339_stylized-low-poly-small-young_01a0a220',
        'fbx_name': 'SM_Tree_Maple_Small.fbx'
    },
    'tree_oak_medium': {
        'task_id': '01a0a220-5150-742c-b3a1-77c4686d649c',
        'fbx_folder': '20260914_175344_stylized-low-poly-medium-half_01a0a220',
        'fbx_name': 'SM_Tree_Oak_Medium.fbx'
    },
    'tree_birch_medium': {
        'task_id': '01a0a220-64f5-7029-8789-d64fdbe39774',
        'fbx_folder': '20260914_175349_stylized-low-poly-medium-half_01a0a220',
        'fbx_name': 'SM_Tree_Birch_Medium.fbx'
    },
    'tree_pine_medium': {
        'task_id': '01a0a220-76f9-7671-88ca-938367b8fa23',
        'fbx_folder': '20260914_175354_stylized-low-poly-medium-half_01a0a220',
        'fbx_name': 'SM_Tree_Pine_Medium.fbx'
    }
}

ASSETS_DIR = r"C:\Users\casey\Desktop\Homesteader\assets\logging"
MESHY_OUT = r"C:\Users\casey\Desktop\Homesteader\HUD\meshy_output"
API_KEY = "msy_mUvsQRtfvX2levWkmugKy3nFHSp3Yyf0Y4Cx"

def main():
    for item_id, info in tasks.items():
        item_dir = os.path.join(ASSETS_DIR, item_id)
        os.makedirs(item_dir, exist_ok=True)
        
        # Copy FBX
        src_fbx = os.path.join(MESHY_OUT, info['fbx_folder'], 'preview.fbx')
        dest_fbx = os.path.join(item_dir, info['fbx_name'])
        shutil.copyfile(src_fbx, dest_fbx)
        
        # Remove old non-FBX models
        for f in os.listdir(item_dir):
            if f.endswith(('.obj', '.mtl', '.glb', '.stl', '.usdz')):
                os.remove(os.path.join(item_dir, f))
                
        # Fetch task status from API for alpha thumbnail URL
        t_id = info['task_id']
        req = urllib.request.Request(f"https://api.meshy.ai/openapi/v2/text-to-3d/{t_id}", headers={"Authorization": f"Bearer {API_KEY}"})
        try:
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                alpha_url = data.get('alpha_thumbnail_url') or data.get('thumbnail_url')
                
                if alpha_url:
                    tmp_raw = os.path.join(item_dir, 'tmp_alpha.png')
                    urllib.request.urlretrieve(alpha_url, tmp_raw)
                    
                    img = Image.open(tmp_raw).convert('RGBA')
                    bbox = img.getbbox()
                    if bbox:
                        img = img.crop(bbox)
                    w, h = img.size
                    scale = min(104 / w, 104 / h)
                    new_w = max(1, int(round(w * scale)))
                    new_h = max(1, int(round(h * scale)))
                    resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                    
                    final_img = Image.new('RGBA', (128, 128), (0, 0, 0, 0))
                    final_img.paste(resized, ((128 - new_w) // 2, (128 - new_h) // 2), resized)
                    icon_path = os.path.join(item_dir, f"{item_id}.png")
                    final_img.save(icon_path, 'PNG')
                    os.remove(tmp_raw)
                    print(f"Deployed {item_id}: FBX ({os.path.getsize(dest_fbx):,} bytes) + 128x128 icon")
        except Exception as e:
            print(f"Error fetching {item_id}: {e}")
            
        # Update json
        json_path = os.path.join(item_dir, f"{item_id}.json")
        d = {}
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as jf:
                d = json.load(jf)
        d['models'] = [{'file': info['fbx_name'], 'format': 'fbx'}]
        with open(json_path, 'w', encoding='utf-8') as jf:
            json.dump(d, jf, indent=2)

if __name__ == "__main__":
    main()

