"""_summarize_sweep.py - read sweep_log.json and print per-category stats.

Usage:
    python _summarize_sweep.py
"""

import json
import os
import sys
from collections import defaultdict

PROJ = r"C:\Users\casey\Desktop\Homesteader"
LOG_PATH = os.path.join(PROJ, "assets", "_sweep_log.json")

if not os.path.isfile(LOG_PATH):
    print(f"[summary] no log at {LOG_PATH}")
    sys.exit(1)

log = json.load(open(LOG_PATH, encoding="utf-8"))
items = log.get("items", [])
print(f"== Sweep summary ({len(items)} items, "
      f"${log.get('spent_usd', 0):.2f} of ${log.get('budget_usd', 0):.2f}) ==")

by_cat = defaultdict(list)
for it in items:
    by_cat[it.get("category", "?")].append(it)

for cat in sorted(by_cat.keys()):
    batch = by_cat[cat]
    succ = sum(1 for i in batch if i.get("status") == "success")
    err = sum(1 for i in batch if i.get("status") == "error")
    dry = sum(1 for i in batch if i.get("status") == "dry-run")
    print(f"  {cat:<14}  total={len(batch):3d}  success={succ:3d}  "
          f"error={err:3d}  dry-run={dry:3d}")

print("\n== Sample errors ==")
for i, it in enumerate(items):
    if it.get("status") == "error":
        print(f"  {it['category']}/{it['id']}: {it.get('error', '?')}")
