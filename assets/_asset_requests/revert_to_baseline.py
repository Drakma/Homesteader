import os
import shutil
import json
import sys

# This file lives in assets/_asset_requests/, so two levels up is assets/.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REQ_DIR = os.path.join(BASE_DIR, "_asset_requests")
SNAPSHOT_FILE = os.path.join(REQ_DIR, "baseline_snapshot_pre_test.json")

def find_new_items():
    if not os.path.isfile(SNAPSHOT_FILE):
        print("Error: No baseline snapshot found.")
        return [], []
    
    with open(SNAPSHOT_FILE, "r", encoding="utf-8") as f:
        baseline = json.load(f)
    
    new_asset_dirs = []
    new_request_files = []
    
    # 1. Check for new item folders in categories
    for cat, old_items in baseline["categories"].items():
        cat_dir = os.path.join(BASE_DIR, cat)
        if os.path.isdir(cat_dir):
            curr_items = set(os.listdir(cat_dir))
            added = curr_items - set(old_items)
            for item in added:
                new_asset_dirs.append(os.path.join(cat_dir, item))
                
    # 2. Check for new requests/batches
    for sub in ["pending", "in_progress", "done", "batches"]:
        folder = os.path.join(REQ_DIR, sub)
        old_files = set(baseline.get(f"{sub}_requests", baseline.get(sub, [])))
        if os.path.isdir(folder):
            curr_files = set(os.listdir(folder))
            added = curr_files - old_files
            for f in added:
                new_request_files.append(os.path.join(folder, f))
                
    return new_asset_dirs, new_request_files

def list_diff():
    new_dirs, new_reqs = find_new_items()
    print("=== NEW ASSET FOLDERS CREATED SINCE BASELINE ===")
    if not new_dirs:
        print("  (None)")
    else:
        for d in new_dirs:
            print(f"  + {d}")
            
    print("\n=== NEW REQUEST FILES / BATCHES CREATED SINCE BASELINE ===")
    if not new_reqs:
        print("  (None)")
    else:
        for r in new_reqs:
            print(f"  + {r}")

def revert():
    new_dirs, new_reqs = find_new_items()
    print(f"Reverting {len(new_dirs)} asset folders and {len(new_reqs)} request files...")
    for d in new_dirs:
        if os.path.isdir(d):
            print(f"Deleting folder: {d}")
            shutil.rmtree(d, ignore_errors=True)
    for r in new_reqs:
        if os.path.isfile(r):
            print(f"Deleting request: {r}")
            os.remove(r)
    print("Reversion complete. Running catalog updater...")
    catalog_script = os.path.join(BASE_DIR, "update_catalog_readme.py")
    if os.path.isfile(catalog_script):
        os.system(f'python "{catalog_script}"')

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--revert":
        revert()
    else:
        list_diff()

