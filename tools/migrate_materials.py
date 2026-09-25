#!/usr/bin/env python3
"""
migrate_materials.py
Migrates all mat_* assets from existing categories (building, farming, logging, ranching)
into assets/materials/ and updates their plugin manifests (<item_id>.json).
"""

import os
import shutil
import json

ASSETS_DIR = r"C:\Users\casey\Desktop\Homesteader\assets"
MATERIALS_DIR = os.path.join(ASSETS_DIR, "materials")
os.makedirs(MATERIALS_DIR, exist_ok=True)

moved_count = 0
categories_to_scan = ["building", "farming", "logging", "ranching", "structures", "tools", "electricity", "water", "waste", "internet", "food", "fuel"]

print("Scanning for mat_* assets to migrate to assets/materials/...")

for cat in categories_to_scan:
    cat_dir = os.path.join(ASSETS_DIR, cat)
    if not os.path.isdir(cat_dir):
        continue
    for item_id in sorted(os.listdir(cat_dir)):
        if not item_id.startswith("mat_"):
            continue
        src_path = os.path.join(cat_dir, item_id)
        if not os.path.isdir(src_path):
            continue
        dst_path = os.path.join(MATERIALS_DIR, item_id)
        
        if os.path.exists(dst_path):
            print(f"Warning: Destination {dst_path} already exists! Skipping.")
            continue
            
        print(f"Moving {cat}/{item_id} -> materials/{item_id}")
        shutil.move(src_path, dst_path)
        moved_count += 1
        
        # Update manifest
        json_path = os.path.join(dst_path, f"{item_id}.json")
        if os.path.exists(json_path):
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    manifest = json.load(f)
                manifest["category"] = "materials"
                manifest["icon"] = f"{item_id}.png"
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(manifest, f, indent=2)
            except Exception as e:
                print(f"  Error updating manifest for {item_id}: {e}")

print(f"\nMigration complete. Moved {moved_count} assets to {MATERIALS_DIR}.")
