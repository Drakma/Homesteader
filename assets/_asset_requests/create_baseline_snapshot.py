import os
import json
import time

base_dir = r"C:\Users\casey\Desktop\Homesteader\assets"
req_dir = os.path.join(base_dir, "_asset_requests")

snapshot = {
    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "epoch": time.time(),
    "pending_requests": sorted(os.listdir(os.path.join(req_dir, "pending"))),
    "batches": sorted(os.listdir(os.path.join(req_dir, "batches"))),
    "done_requests": sorted(os.listdir(os.path.join(req_dir, "done"))),
    "in_progress": sorted(os.listdir(os.path.join(req_dir, "in_progress"))),
    "categories": {}
}

total_items = 0
for cat in sorted(os.listdir(base_dir)):
    cat_dir = os.path.join(base_dir, cat)
    if os.path.isdir(cat_dir) and not cat.startswith("_"):
        items = sorted(os.listdir(cat_dir))
        snapshot["categories"][cat] = items
        total_items += len(items)

out_file = os.path.join(req_dir, "baseline_snapshot_pre_test.json")
with open(out_file, "w", encoding="utf-8") as f:
    json.dump(snapshot, f, indent=2)

print(f"Snapshot successfully saved: {total_items} existing items indexed across {len(snapshot['categories'])} categories.")

