"""_sweep_text_to_3d.py - bulk text-to-3D sweep via Tripo3D API.

For every standalone-object item in the asset catalog, reads the
display_name from <category>/<item>/<item>.json, builds a short
natural-language prompt, and requests a GLB mesh from Tripo3D's text
endpoint (v3/generation/text-to-model in their openapi).

Usage:
    python _sweep_text_to_3d.py
    python _sweep_text_to_3d.py --limit 5
    python _sweep_text_to_3d.py --categories structures,farming
    python _sweep_text_to_3d.py --dry-run

BUDGET CONTROL:
    Reads TRIPO_BUDGET_USD env var, default $0 (so without budgeting,
    dry-run only). Stop the loop when cumulative spend >= cap.

API KEY:
    Reads TRIPO_API_KEY env var. Required for non-dry runs.

OUTPUT:
    Writes <category>/<item>_v1.glb into assets/, plus
    _sweep_log.json with task IDs, durations, URLs.
"""

import argparse
import json
import os
import time
import shutil
import sys
from typing import Dict, List

import requests

PROJ = r"C:\Users\casey\Desktop\Homesteader"
ASSETS = os.path.join(PROJ, "assets")

TIPO_BASE = "https://openapi.tripo3d.ai/v3"

# Tripo3D's per-mesh cost as of 2026: 10 credits × $0.01 = $0.10 per mesh
# (their credit is $0.01, and each generation consumes 10 credits).
COST_PER_MESH_USD = 0.10
POLL_INTERVAL_SECONDS = 4.0
MAX_POLL_TIME_SECONDS = 240.0

# Faithful render of the asset name as a single-subject prompt, with
# light style hinting for low-poly faceted. Keep this short - Tripo3D's
# text encoder prefers <= 60 tokens.
PROMPT_TEMPLATE = (
    "a 3D model of {name}, low-poly faceted style, simple geometry, "
    "stylized game asset, single object, no surroundings"
)

# Categories we consider sweepable for text-to-3D. We skip things that
# are abstract (e.g. ingredients, textures, modules) where a coherent
# model would be misleading.
SWEEP_CATEGORIES = [
    "structures",   # 18 items
    "farming",      # 13 crops/seeds - crops work; seeds are abstract
    "ranching",     # 26 animals + accessories
    "fishing",      # 19 rods, lures, fish
    "fuel",         # 17 items
    "electricity",  # panels, batteries
    "water",        # pumps, cisterns
    "waste",        # bins, compost
    "internet",     # routers, dishes
    "food",         # loaves, cartons
    "appliances",   # standalone appliances
    "vehicles",     # standalone vehicles
]


def list_items(category: str) -> List[Dict]:
    """Return [{id, name, prompt, manifest}, ...] for a category folder.

    Each item is its own folder containing <item>.json (the group manifest).
    Items whose id starts with 'seed_' are seeds - we drop them.
    """
    cat_dir = os.path.join(ASSETS, category)
    if not os.path.isdir(cat_dir):
        return []
    out = []
    for entry in sorted(os.listdir(cat_dir)):
        if entry.startswith("_"):
            continue
        if entry.startswith("seed_"):
            # Seeds are abstract global identifiers, not single objects.
            continue
        path = os.path.join(cat_dir, entry, f"{entry}.json")
        if not os.path.isfile(path):
            continue
        try:
            d = json.load(open(path, encoding="utf-8"))
        except Exception:
            continue
        name = d.get("name", entry.replace("_", " ").title())
        prompt = PROMPT_TEMPLATE.format(name=name)
        out.append({
            "id": entry,
            "name": name,
            "category": category,
            "prompt": prompt,
            "manifest_path": path,
        })
    return out


def _auth_headers(api_key: str) -> Dict[str, str]:
    return {"Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"}


def submit_text_to_model(api_key: str, prompt: str,
                         timeout: float = 60.0) -> str:
    """POST to v3/generation/text-to-model. Returns the task_id."""
    url = f"{TIPO_BASE}/generation/text-to-model"
    body = {"prompt": prompt,
            "model_version": "v3.0-20250101"}
    r = requests.post(url, headers=_auth_headers(api_key),
                      json=body, timeout=timeout)
    r.raise_for_status()
    j = r.json()
    if "task_id" not in j:
        raise RuntimeError(f"no task_id in response: {j}")
    return j["task_id"]


def poll_task(api_key: str, task_id: str,
              poll_interval: float = POLL_INTERVAL_SECONDS,
              max_time: float = MAX_POLL_TIME_SECONDS) -> Dict:
    """Poll until status is success/failed, then return the result JSON."""
    url = f"{TIPO_BASE}/generation/task/{task_id}"
    deadline = time.time() + max_time
    last_status = None
    while time.time() < deadline:
        r = requests.get(url, headers=_auth_headers(api_key), timeout=30)
        r.raise_for_status()
        j = r.json()
        # Tripo3D uses .data.status in newer API revisions.
        # Older revisions: {'status': 'success', 'model_url': ...}
        status = j.get("data", {}).get("status",
                 j.get("status", "unknown"))
        if last_status != status:
            print(f"  task {task_id[:8]}... status={status}")
            last_status = status
        if status == "success":
            return j
        if status in ("failed", "error", "cancelled"):
            raise RuntimeError(f"task {task_id} failed: {j}")
        time.sleep(poll_interval)
    raise TimeoutError(f"poll timeout after {max_time}s for task {task_id}")


def download_glb(url: str, out_path: str, timeout: float = 60.0):
    with requests.get(url, stream=True, timeout=timeout) as r:
        r.raise_for_status()
        with open(out_path, "wb") as f:
            shutil.copyfileobj(r.raw, f)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--categories", default="",
                    help="comma-separated override; default = SWEEP_CATEGORIES")
    ap.add_argument("--out", default=os.path.join(PROJ, "assets"))
    ap.add_argument("--log", default=os.path.join(PROJ, "assets",
                                                  "_sweep_log.json"))
    ap.add_argument("--dry-run", action="store_true",
                    help="list items and prompts, no API calls")
    args = ap.parse_args()

    api_key = os.environ.get("TRIPO_API_KEY", "")
    budget = float(os.environ.get("TRIPO_BUDGET_USD", "0"))
    if not args.dry_run and not api_key:
        print("[tripo] TRIPO_API_KEY not set; running in dry-run mode.")
        args.dry_run = True
    if args.dry_run:
        print("[tripo] DRY RUN - no actual API calls will be made.")

    categories = (args.categories.split(",") if args.categories
                  else SWEEP_CATEGORIES)

    # Build item list.
    items = []
    for cat in categories:
        items.extend(list_items(cat))
    if args.limit:
        items = items[: args.limit]
    print(f"[tripo] queue size: {len(items)} items across "
          f"{len(categories)} categories")
    print(f"[tripo] budget cap: ${budget:.2f} "
          f"({int(budget / COST_PER_MESH_USD)} meshes)")

    # Load existing log if any.
    log = {"items": [], "budget_usd": budget, "spent_usd": 0.0}
    if os.path.isfile(args.log):
        try:
            log = json.load(open(args.log, encoding="utf-8"))
        except Exception:
            pass

    # Walk the queue.
    for i, it in enumerate(items, start=1):
        # Spend cap.
        if log["spent_usd"] + COST_PER_MESH_USD > budget and not args.dry_run:
            print(f"[tripo] budget cap reached at item {i}; stopping.")
            break
        cat_out_dir = os.path.join(args.out, it["category"])
        os.makedirs(cat_out_dir, exist_ok=True)
        glb_path = os.path.join(cat_out_dir, f"{it['id']}_v1.glb")
        # Skip already-done.
        if os.path.isfile(glb_path):
            print(f"[tripo] {i:3d}/{len(items)} {it['category']}/{it['id']} "
                  f"already has glb - skip")
            continue

        print(f"[tripo] {i:3d}/{len(items)} {it['category']}/{it['id']} "
              f"name={it['name']!r}")
        print(f"        prompt: {it['prompt']!r}")

        if args.dry_run:
            log["items"].append({
                "id": it["id"], "category": it["category"],
                "name": it["name"], "prompt": it["prompt"],
                "status": "dry-run",
            })
            continue

        try:
            t0 = time.time()
            task_id = submit_text_to_model(api_key, it["prompt"])
            res = poll_task(api_key, task_id)
            dt = time.time() - t0
            data = res.get("data", res)
            model_url = (data.get("model_url")
                         or data.get("output_url")
                         or res.get("model_url"))
            if not model_url:
                raise RuntimeError(f"no model_url in result: {res}")
            download_glb(model_url, glb_path)

            log["spent_usd"] += COST_PER_MESH_USD
            log["items"].append({
                "id": it["id"], "category": it["category"],
                "name": it["name"], "prompt": it["prompt"],
                "task_id": task_id, "model_url": model_url,
                "glb_path": glb_path, "duration_sec": round(dt, 1),
                "status": "success",
            })
            print(f"        -> {glb_path} "
                  f"(task {task_id[:8]}... {dt:.1f}s; "
                  f"spent=${log['spent_usd']:.2f})")
        except Exception as e:
            print(f"        ERROR: {type(e).__name__}: {e}")
            log["items"].append({
                "id": it["id"], "category": it["category"],
                "name": it["name"], "prompt": it["prompt"],
                "status": "error", "error": f"{type(e).__name__}: {e}",
            })

        # Per-item log flush, so a crash mid-sweep keeps progress.
        with open(args.log, "w", encoding="utf-8") as f:
            json.dump(log, f, indent=2, sort_keys=True)

    print(f"[tripo] done. spent=${log['spent_usd']:.2f} of "
          f"${budget:.2f} cap; log -> {args.log}")


if __name__ == "__main__":
    main()
