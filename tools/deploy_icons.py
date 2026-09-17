#!/usr/bin/env python3
"""
Deploy validated 128x128 item icons to all required Homesteader asset locations:
  assets/items/<name>.png
  assets/items/<category>/<subcategory>/<name>.png
  assets/<category>/<subcategory>/<name>.png
  Homesteader/Content/Homesteader/UI/Icons/<name>.png
  Homesteader/Content/Homesteader/UI/Icons/<category>/<subcategory>/<name>.png

Usage: python deploy_icons.py <source_dir> <mapping.json>
mapping.json: {"item_name": ["category", "subcategory"], ...}
"""
import sys
import os
import shutil
import json

HUD_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GAME_ROOT = os.path.join(os.path.dirname(HUD_ROOT), "Homesteader")


def deploy(src_dir, mapping):
    targets_written = 0
    skipped = []
    for name, (category, subcategory) in mapping.items():
        src = os.path.join(src_dir, f"{name}.png")
        if not os.path.exists(src):
            skipped.append(name)
            continue
        dests = [
            os.path.join(HUD_ROOT, "assets", "items", f"{name}.png"),
            os.path.join(HUD_ROOT, "assets", "items", category, subcategory, f"{name}.png"),
            os.path.join(HUD_ROOT, "assets", category, subcategory, f"{name}.png"),
            os.path.join(GAME_ROOT, "Content", "Homesteader", "UI", "Icons", f"{name}.png"),
            os.path.join(GAME_ROOT, "Content", "Homesteader", "UI", "Icons", category, subcategory, f"{name}.png"),
        ]
        for d in dests:
            os.makedirs(os.path.dirname(d), exist_ok=True)
            shutil.copy2(src, d)
            targets_written += 1
    print(f"Deployed {len(mapping) - len(skipped)} items x 5 locations = {targets_written} files written")
    if skipped:
        print(f"SKIPPED (missing source png): {skipped}")


if __name__ == "__main__":
    src_dir = sys.argv[1]
    mapping_path = sys.argv[2]
    with open(mapping_path) as f:
        mapping = json.load(f)
    deploy(src_dir, mapping)
