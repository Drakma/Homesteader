#!/usr/bin/env python3
"""
meshy_tree_clutter_pipeline.py
Automated pipeline for generating Meshy 3D assets, refining textures, downloading
model formats (GLB, OBJ, FBX, MTL), creating 128x128 compliant icons, and updating
the Homesteader item directories.
"""

import os
import sys
import time
import json
import shutil
import urllib.request
from PIL import Image

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import meshy_client

# tools/ sits at the repo root, so one level up is the project root.
HOMESTEADER_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(HOMESTEADER_ROOT, "assets")
UE5_ICON_DIR = os.path.join(HOMESTEADER_ROOT, "Homesteader", "Content", "Homesteader", "UI", "Icons")

# Batch 1: Mature Trees & Variants
BATCH_TREES = [
    {
        "item_id": "tree_birch_tall",
        "category": "logging",
        "model_prefix": "SM_Tree_Birch_Tall",
        "prompt": "Stylized low-poly white birch tree, slender white bark trunk with dark markings, bright lime green faceted leaves, 3d game asset",
        "negative_prompt": "blurry, hyperrealistic, deformed, flat"
    },
    {
        "item_id": "tree_pine_tall",
        "category": "logging",
        "model_prefix": "SM_Tree_Pine_Tall",
        "prompt": "Stylized low-poly evergreen pine tree, conical tiered needle foliage, dark brown sturdy trunk, 3d game asset",
        "negative_prompt": "blurry, hyperrealistic, deformed, flat"
    },
    {
        "item_id": "tree_maple",
        "category": "logging",
        "model_prefix": "SM_Tree_Maple",
        "prompt": "Stylized low-poly sugar maple tree, broad rounded crown, fiery vibrant orange and red foliage, sturdy brown trunk, 3d game asset",
        "negative_prompt": "blurry, hyperrealistic, deformed, flat"
    },
    {
        "item_id": "tree_apple_large",
        "category": "logging",
        "model_prefix": "SM_Tree_Apple_Large",
        "prompt": "Stylized low-poly apple tree, spreading orchard canopy, small bright red apples on green leaves, gnarled trunk, 3d game asset",
        "negative_prompt": "blurry, hyperrealistic, deformed, flat"
    },
    {
        "item_id": "tree_willow_large",
        "category": "logging",
        "model_prefix": "SM_Tree_Willow_Large",
        "prompt": "Stylized low-poly weeping willow tree, sweeping drooping vine branches, soft sage green, thick trunk, 3d game asset",
        "negative_prompt": "blurry, hyperrealistic, deformed, flat"
    },
    {
        "item_id": "tree_poplar_columnar",
        "category": "logging",
        "model_prefix": "SM_Tree_Poplar_Columnar",
        "prompt": "Stylized low-poly columnar poplar tree, tall slender vertical crown, yellow-green foliage, straight trunk, 3d game asset",
        "negative_prompt": "blurry, hyperrealistic, deformed, flat"
    },
    {
        "item_id": "tree_oak_autumn",
        "category": "logging",
        "model_prefix": "SM_Tree_Oak_Autumn",
        "prompt": "Stylized low-poly autumn oak tree, sprawling golden amber foliage, sturdy brown trunk with root flare, 3d game asset",
        "negative_prompt": "blurry, hyperrealistic, deformed, flat"
    },
    {
        "item_id": "tree_dead_snag",
        "category": "logging",
        "model_prefix": "SM_Tree_Dead_Snag",
        "prompt": "Stylized low-poly weathered dead tree snag, barkless hollow grey-brown trunk, broken bare branch spurs, 3d game asset",
        "negative_prompt": "blurry, hyperrealistic, deformed, flat"
    }
]

# Batch 2: Ground Clutter Props
BATCH_CLUTTER = [
    {
        "item_id": "clutter_acorns",
        "category": "ground",
        "model_prefix": "SM_Clutter_Acorns",
        "prompt": "Stylized low-poly cluster of fallen acorns with caps on ground, warm brown, 3d game asset prop",
        "negative_prompt": "blurry, hyperrealistic, deformed, flat"
    },
    {
        "item_id": "clutter_branch",
        "category": "ground",
        "model_prefix": "SM_Clutter_Branch",
        "prompt": "Stylized low-poly fallen tree branch on ground, weathered wood bark, small broken twigs, 3d game asset prop",
        "negative_prompt": "blurry, hyperrealistic, deformed, flat"
    },
    {
        "item_id": "clutter_cattails",
        "category": "ground",
        "model_prefix": "SM_Clutter_Cattails",
        "prompt": "Stylized low-poly wetland cattails, tall green reeds with brown cylinder heads, 3d game asset prop",
        "negative_prompt": "blurry, hyperrealistic, deformed, flat"
    },
    {
        "item_id": "clutter_dirt_clump",
        "category": "ground",
        "model_prefix": "SM_Clutter_Dirt_Clump",
        "prompt": "Stylized low-poly excavated dirt clump with small pebbles and soil chunks, earthy brown, 3d game asset prop",
        "negative_prompt": "blurry, hyperrealistic, deformed, flat"
    },
    {
        "item_id": "clutter_grass_tuft",
        "category": "ground",
        "model_prefix": "SM_Clutter_Grass_Tuft",
        "prompt": "Stylized low-poly wild grass tuft cluster, fresh vibrant green blades, 3d game asset prop",
        "negative_prompt": "blurry, hyperrealistic, deformed, flat"
    },
    {
        "item_id": "clutter_leaves",
        "category": "ground",
        "model_prefix": "SM_Clutter_Leaves",
        "prompt": "Stylized low-poly scatter pile of fallen autumn leaves, red orange yellow leaves, 3d game asset prop",
        "negative_prompt": "blurry, hyperrealistic, deformed, flat"
    },
    {
        "item_id": "clutter_pebbles",
        "category": "ground",
        "model_prefix": "SM_Clutter_Pebbles",
        "prompt": "Stylized low-poly cluster of smooth rounded river pebbles, assorted grey stone, 3d game asset prop",
        "negative_prompt": "blurry, hyperrealistic, deformed, flat"
    },
    {
        "item_id": "clutter_pinecones",
        "category": "ground",
        "model_prefix": "SM_Clutter_Pinecones",
        "prompt": "Stylized low-poly cluster of brown evergreen pinecones on ground, textured scales, 3d game asset prop",
        "negative_prompt": "blurry, hyperrealistic, deformed, flat"
    },
    {
        "item_id": "clutter_tall_grass",
        "category": "ground",
        "model_prefix": "SM_Clutter_Tall_Grass",
        "prompt": "Stylized low-poly tall prairie grass bunch, dried golden wheat and green stalks, 3d game asset prop",
        "negative_prompt": "blurry, hyperrealistic, deformed, flat"
    },
    {
        "item_id": "clutter_twigs",
        "category": "ground",
        "model_prefix": "SM_Clutter_Twigs",
        "prompt": "Stylized low-poly kindling twigs and small sticks pile on ground, dry wood branches, 3d game asset prop",
        "negative_prompt": "blurry, hyperrealistic, deformed, flat"
    }
]

# Batch 3: Planted In-Ground Saplings
BATCH_PLANTED_SAPLINGS = [
    {
        "item_id": "planted_sapling_oak",
        "category": "logging",
        "model_prefix": "SM_PlantedSaplingOak",
        "prompt": "Stylized low-poly young planted oak sapling growing in small dirt mound, slender stem with fresh green lobed leaves, 3d game asset",
        "negative_prompt": "blurry, hyperrealistic, deformed, flat"
    },
    {
        "item_id": "planted_sapling_birch",
        "category": "logging",
        "model_prefix": "SM_PlantedSaplingBirch",
        "prompt": "Stylized low-poly young planted birch sapling growing in small dirt mound, slender white bark stem with fresh lime green leaves, 3d game asset",
        "negative_prompt": "blurry, hyperrealistic, deformed, flat"
    },
    {
        "item_id": "planted_sapling_pine",
        "category": "logging",
        "model_prefix": "SM_PlantedSaplingPine",
        "prompt": "Stylized low-poly young planted pine seedling sapling growing in small dirt mound, small evergreen needle shoot, 3d game asset",
        "negative_prompt": "blurry, hyperrealistic, deformed, flat"
    },
    {
        "item_id": "planted_sapling_maple",
        "category": "logging",
        "model_prefix": "SM_PlantedSaplingMaple",
        "prompt": "Stylized low-poly young planted sugar maple sapling growing in small dirt mound, slender stem with tender orange-red maple leaves, 3d game asset",
        "negative_prompt": "blurry, hyperrealistic, deformed, flat"
    },
    {
        "item_id": "planted_sapling_apple",
        "category": "logging",
        "model_prefix": "SM_PlantedSaplingApple",
        "prompt": "Stylized low-poly young planted apple fruit tree sapling growing in small dirt mound, slender shoot with tender green leaves, 3d game asset",
        "negative_prompt": "blurry, hyperrealistic, deformed, flat"
    },
    {
        "item_id": "planted_sapling_willow",
        "category": "logging",
        "model_prefix": "SM_PlantedSaplingWillow",
        "prompt": "Stylized low-poly young planted weeping willow sapling growing in small dirt mound, slender stem with drooping tender leaves, 3d game asset",
        "negative_prompt": "blurry, hyperrealistic, deformed, flat"
    },
    {
        "item_id": "planted_sapling_poplar",
        "category": "logging",
        "model_prefix": "SM_PlantedSaplingPoplar",
        "prompt": "Stylized low-poly young planted columnar poplar sapling growing in small dirt mound, upright slender vertical shoot with yellow-green leaves, 3d game asset",
        "negative_prompt": "blurry, hyperrealistic, deformed, flat"
    }
]


def format_compliant_icon(src_img_path, dest_icon_path, max_dim=104):
    img = Image.open(src_img_path).convert("RGBA")
    bbox = img.getbbox()
    if not bbox:
        raise ValueError("Image is completely transparent!")
    cropped = img.crop(bbox)
    w, h = cropped.size
    scale = float(max_dim) / max(w, h)
    nw = max(1, int(w * scale))
    nh = max(1, int(h * scale))
    scaled = cropped.resize((nw, nh), Image.Resampling.LANCZOS)

    icon = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
    offset = ((128 - nw) // 2, (128 - nh) // 2)
    icon.paste(scaled, offset, scaled)
    icon.save(dest_icon_path, "PNG")
    return dest_icon_path

def process_batch(items, scratch_base_dir):
    print(f"\n==========================================")
    print(f"Submitting {len(items)} preview tasks in batch...")
    print(f"==========================================")

    preview_tasks = []
    for item in items:
        item_id = item["item_id"]
        category = item["category"]
        prompt = item["prompt"]
        neg = item.get("negative_prompt", "")

        print(f"Submitting preview for {item_id}...")
        payload = {
            "mode": "preview",
            "prompt": prompt,
            "negative_prompt": neg,
            "ai_model": "meshy-6",
            "model_type": "standard",
            "origin_at": "bottom",
            "alpha_thumbnail": True,
            "target_formats": ["glb", "obj", "fbx"]
        }
        res = meshy_client._request("/openapi/v2/text-to-3d", method="POST", data=payload)
        task_id = res.get("result")
        print(f"  -> Task ID: {task_id}")
        preview_tasks.append((item, task_id))
        time.sleep(1) # brief pacing

    print(f"\nWaiting for all {len(preview_tasks)} previews to finish...")
    completed_previews = []
    for item, task_id in preview_tasks:
        print(f"Waiting for preview of {item['item_id']} ({task_id})...")
        t = meshy_client.wait_for_task("text-to-3d", task_id, timeout_sec=360, poll_interval=6)
        completed_previews.append((item, t))
        print(f"  Preview done for {item['item_id']}!")

    print(f"\nSubmitting refine tasks for all {len(completed_previews)} items...")
    refine_tasks = []
    for item, prev_task in completed_previews:
        item_id = item["item_id"]
        prev_id = prev_task["id"]
        print(f"Submitting refine for {item_id} (preview: {prev_id})...")
        res = meshy_client._request("/openapi/v2/text-to-3d", method="POST", data={"mode": "refine", "preview_task_id": prev_id})
        ref_id = res.get("result")
        print(f"  -> Refine Task ID: {ref_id}")
        refine_tasks.append((item, ref_id))
        time.sleep(1)

    print(f"\nWaiting for all {len(refine_tasks)} refines to finish...")
    for item, ref_id in refine_tasks:
        item_id = item["item_id"]
        category = item["category"]
        prefix = item["model_prefix"]

        print(f"Waiting for refine of {item_id} ({ref_id})...")
        ref_task = meshy_client.wait_for_task("text-to-3d", ref_id, timeout_sec=360, poll_interval=6)
        print(f"  Refine done for {item_id}!")

        # Download and deploy
        dest_dir = os.path.join(ASSETS_DIR, category, item_id)
        os.makedirs(dest_dir, exist_ok=True)
        item_scratch = os.path.join(scratch_base_dir, item_id)
        os.makedirs(item_scratch, exist_ok=True)

        print(f"Downloading models for {item_id}...")
        downloaded = meshy_client.download_model_files(ref_task, item_scratch, prefix)

        # Download thumbnail
        thumb_url = ref_task.get("alpha_thumbnail_url") or ref_task.get("thumbnail_url")
        thumb_path = os.path.join(item_scratch, "preview.png")
        if thumb_url:
            urllib.request.urlretrieve(thumb_url, thumb_path)

        # Copy models to asset directory
        for p in downloaded:
            ext = os.path.splitext(p)[1]
            dest_f = os.path.join(dest_dir, f"{prefix}{ext}")
            shutil.copy2(p, dest_f)
            print(f"  Deployed {ext} to {dest_f}")

        # Generate and save icon
        icon_path = os.path.join(dest_dir, f"{item_id}.png")
        if os.path.exists(thumb_path):
            format_compliant_icon(thumb_path, icon_path)
            print(f"  Created 128x128 icon: {icon_path}")

            # Sync to UE5
            ue5_cat = os.path.join(UE5_ICON_DIR, category)
            if os.path.exists(ue5_cat):
                shutil.copy2(icon_path, os.path.join(ue5_cat, f"{item_id}.png"))
                print(f"  Synced to UE5: {ue5_cat}")

    print(f"\nBatch processing complete!")

if __name__ == "__main__":
    balance = meshy_client.get_balance()
    print(f"Meshy Asset Pipeline. Current Balance: {balance} credits.")

    # scratch/ lives at the repo root (see tools/README.md). It was previously
    # written under HUD/, which no longer exists.
    scratch_dir = os.path.join(HOMESTEADER_ROOT, "scratch", "meshy_output")
    os.makedirs(scratch_dir, exist_ok=True)
    
    mode = sys.argv[1] if len(sys.argv) > 1 else "trees"
    if mode == "trees":
        # Process the 8 remaining trees
        process_batch(BATCH_TREES, scratch_dir)
    elif mode == "clutter":
        # Process the 10 clutter props
        process_batch(BATCH_CLUTTER, scratch_dir)
    elif mode == "saplings":
        # Process the 7 planted saplings
        process_batch(BATCH_PLANTED_SAPLINGS, scratch_dir)
    elif mode == "all":
        process_batch(BATCH_TREES, scratch_dir)
        process_batch(BATCH_CLUTTER, scratch_dir)
        process_batch(BATCH_PLANTED_SAPLINGS, scratch_dir)
    else:
        print(f"Unknown mode: {mode}")


