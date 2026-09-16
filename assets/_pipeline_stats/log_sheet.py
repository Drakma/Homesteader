#!/usr/bin/env python3
"""Append one icon-sheet generation result to icon_sheet_stats.json, so we
can empirically find the sheet size with the best defect-rate/cost tradeoff
(user request, 2026-09-15: "keep track of which number of items per sheet
has the most errors... find the perfect amount to keep costs as low as
possible").

Usage:
  py -3 log_sheet.py --items 8 --technique style_anchor --background magenta \
      --defects "" --notes "Group A: water heaters/fridges/dishwashers/sinks"

--defects is a comma-separated list of short tags, e.g.:
  not_low_poly, wrong_facing, extraction_fragmentation, text_on_sheet,
  wrong_item_count, wrong_camera_angle, other:<description>
Leave --defects empty (or omit) for a clean sheet.
"""
import argparse
import json
import os
import time

STATS_PATH = os.path.join(os.path.dirname(__file__), "icon_sheet_stats.json")


def load():
    if not os.path.exists(STATS_PATH):
        return {"records": []}
    with open(STATS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save(data):
    with open(STATS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--items", type=int, required=True, help="items requested on this sheet")
    ap.add_argument("--technique", required=True, choices=["text_only", "style_anchor"])
    ap.add_argument("--background", required=True, choices=["dark_slate", "magenta"])
    ap.add_argument("--defects", default="", help="comma-separated defect tags, empty = clean")
    ap.add_argument("--notes", default="")
    ap.add_argument("--sheet-id", default=None)
    args = ap.parse_args()

    defect_list = [d.strip() for d in args.defects.split(",") if d.strip()]

    data = load()
    record = {
        "date": time.strftime("%Y-%m-%d"),
        "sheet_id": args.sheet_id or f"sheet_{int(time.time())}",
        "items_requested": args.items,
        "technique": args.technique,
        "background": args.background,
        "defects": defect_list,
        "defect_count": len(defect_list),
        "clean": len(defect_list) == 0,
        "notes": args.notes,
    }
    data["records"].append(record)
    save(data)
    print(f"Logged: {record['sheet_id']} - {args.items} items, {args.technique}/{args.background}, "
          f"{'CLEAN' if record['clean'] else f'{len(defect_list)} defect(s): ' + ', '.join(defect_list)}")

    # Quick running summary by (items, technique, background)
    from collections import defaultdict
    buckets = defaultdict(lambda: {"sheets": 0, "clean": 0, "total_defects": 0})
    for r in data["records"]:
        key = (r["items_requested"], r["technique"], r["background"])
        b = buckets[key]
        b["sheets"] += 1
        b["clean"] += 1 if r["clean"] else 0
        b["total_defects"] += r["defect_count"]
    print("\nRunning summary (items, technique, background) -> sheets / clean / total defects:")
    for key in sorted(buckets):
        b = buckets[key]
        print(f"  {key} -> {b['sheets']} sheets, {b['clean']} clean, {b['total_defects']} total defects")


if __name__ == "__main__":
    main()
