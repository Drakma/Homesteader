#!/usr/bin/env python3
"""
run_batch.py
Processes the 6 queued assets through the 100% Free pipeline sequentially.
"""

import os
import sys
import subprocess

BASE_DIR = r"C:\Users\casey\Desktop\Homesteader\assets"
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from process_queued_batch import process_item

ITEMS = [
    {
        "req_id": "1789516880_wooden_well_head",
        "item_id": "water_well_head_wooden",
        "category": "water",
        "name": "Wooden Well Head",
        "description": "Rustic wooden well head casing with a water pipe coming out the side and turning down into the ground.",
        "prompt": "A 3D low-poly faceted render of a rustic wooden well head casing with a metal pipe coming out of the side and turning downwards into the ground, facing toward the left. Solid magenta #FF00FF background, isometric 3/4 front view, floating in empty space.",
        "caption": "rustic wooden well head casing with plumbing pipe",
        "weight_kg": 45.0,
        "max_stack": 1,
        "base_value": 75.0,
        "dimensions_m": {"x": 1.2, "y": 1.2, "z": 1.5}
    },
    {
        "req_id": "1789516852_concrete_well_head",
        "item_id": "water_well_head_concrete",
        "category": "water",
        "name": "Concrete Well Head",
        "description": "Large concrete well head with a steel pipe coming out of the center and turning down into the ground.",
        "prompt": "A 3D low-poly faceted render of a large round concrete well head casing with a steel water pipe coming out of the middle and turning down into the ground, facing toward the left. Solid magenta #FF00FF background, isometric 3/4 front view, floating in empty space.",
        "caption": "concrete well head casing with steel water pipe",
        "weight_kg": 150.0,
        "max_stack": 1,
        "base_value": 120.0,
        "dimensions_m": {"x": 1.4, "y": 1.4, "z": 1.2}
    },
    {
        "req_id": "1789516752_small_submersible_well_pump",
        "item_id": "water_pump_submersible_1hp",
        "category": "water",
        "name": "Small Submersible Well Pump",
        "description": "1 HP compact stainless steel submersible deep well pump with heavy-duty electrical cord coiled beside it.",
        "prompt": "A 3D low-poly faceted render of a 1HP compact stainless steel submersible well water pump cylinder with power cord coiled neatly beside it, facing toward the left. Solid magenta #FF00FF background, isometric 3/4 front view, floating in empty space.",
        "caption": "1hp stainless steel submersible well pump with coiled wire",
        "weight_kg": 12.0,
        "max_stack": 5,
        "base_value": 180.0,
        "dimensions_m": {"x": 0.4, "y": 0.4, "z": 0.9}
    },
    {
        "req_id": "1789516738_large_submerisible_well_pump",
        "item_id": "water_pump_submersible_3hp",
        "category": "water",
        "name": "Large Submersible Well Pump",
        "description": "3 HP commercial stainless steel submersible well pump with heavy gauge wire cord coiled next to it.",
        "prompt": "A 3D low-poly faceted render of a 3HP heavy duty stainless steel submersible deep well water pump cylinder with electrical cable cord neatly coiled rolled up next to it, facing toward the left. Solid magenta #FF00FF background, isometric 3/4 front view, floating in empty space.",
        "caption": "3hp commercial submersible well pump with cable roll",
        "weight_kg": 24.0,
        "max_stack": 5,
        "base_value": 350.0,
        "dimensions_m": {"x": 0.5, "y": 0.5, "z": 1.2}
    },
    {
        "req_id": "1789516900_mature_oak_tree",
        "item_id": "tree_mature_oak",
        "category": "logging",
        "name": "Mature Oak Tree",
        "description": "Mature growth stage of the oak tree (~18m height), completing the 4-stage oak tree lifecycle.",
        "prompt": "A 3D low-poly faceted render of a tall mature deciduous oak tree with spreading crown and dense leafy green foliage, thick rugged brown trunk, facing toward the left. Solid magenta #FF00FF background, isometric 3/4 front view, floating in empty space.",
        "caption": "mature oak tree hardwood timber deciduous low poly",
        "weight_kg": 1200.0,
        "max_stack": 1,
        "base_value": 450.0,
        "dimensions_m": {"x": 14.0, "y": 14.0, "z": 18.0}
    },
    {
        "req_id": "1789594701_female_farmer",
        "item_id": "peds_female_farmer",
        "category": "peds",
        "name": "Female Farmer",
        "description": "Female farmer NPC in modern rural work clothing (denim overalls, plaid workshirt, sturdy boots), rigged with Humanoid skeleton and walk/run cycles.",
        "prompt": "A 3D low-poly faceted render of a female farmer character in modern clothing, wearing denim overalls, plaid shirt, and boots, facing toward the left of the frame, standing in neutral T-pose or A-pose. Solid magenta #FF00FF background, isometric 3/4 front view, floating in empty space, clean polygonal planes.",
        "caption": "female farmer character in denim overalls low poly game character",
        "is_rigged": True,
        "weight_kg": 65.0,
        "max_stack": 1,
        "base_value": 0.0,
        "dimensions_m": {"x": 0.6, "y": 0.4, "z": 1.7}
    }
]

def main():
    print(f"Starting batch generation of {len(ITEMS)} items via 100% Free Pipeline...")
    results = {}
    for item in ITEMS:
        success = process_item(item)
        results[item["item_id"]] = success

    print("\n========================================================")
    print("BATCH PROCESSING SUMMARY")
    print("========================================================")
    for k, v in results.items():
        print(f"  {k}: {'SUCCESS' if v else 'FAILED'}")

    print("\nUpdating master catalog...")
    catalog_script = os.path.join(BASE_DIR, "update_catalog_readme.py")
    if os.path.exists(catalog_script):
        subprocess.run([sys.executable, catalog_script])
    print("Done!")

if __name__ == "__main__":
    main()

