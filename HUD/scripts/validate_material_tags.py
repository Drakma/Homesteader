#!/usr/bin/env python3
"""Validate assets/_schemas/material_tags.json: every member item_id listed
under a tag must be a real, existing catalog item somewhere in assets/.

Usage:
  py -3 validate_material_tags.py
"""
import glob
import json
import os

ASSETS_ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "assets")
TAGS_PATH = os.path.join(ASSETS_ROOT, "_schemas", "material_tags.json")


def all_real_item_ids():
    ids = set()
    for path in glob.glob(os.path.join(ASSETS_ROOT, "*", "*", "*.json")):
        # skip non-category dirs like _asset_requests, _schemas, _pipeline_stats
        parts = path.replace("\\", "/").split("/")
        cat = parts[-3]
        if cat.startswith("_"):
            continue
        item_id = os.path.splitext(os.path.basename(path))[0]
        ids.add(item_id)
    return ids


def main():
    with open(TAGS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    real_ids = all_real_item_ids()
    errors = 0
    for tag, members in data.get("tags", {}).items():
        for item_id in members:
            if item_id not in real_ids:
                print(f"[FAIL] #{tag} -> '{item_id}' does not exist as a real catalog item")
                errors += 1

    total_tags = len(data.get("tags", {}))
    if errors == 0:
        print(f"All {total_tags} tags resolve to real items.")
    else:
        print(f"\n{errors} broken tag reference(s) across {total_tags} tags.")
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
