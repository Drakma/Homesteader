"""_sweep_image_to_3d.py - bulk image-to-3D sweep via Tripo3D API.

For every standalone-object item that has an existing icon
(assets/<category>/<group>/<group>.png), upload that PNG to Tripo3D's
image-to-model endpoint and write back <group>_v1.glb in the same
folder.

This is the higher-quality path for items where an icon already exists;
text-to-3D is fine for items that don't have a representative icon
yet.

Usage:
    python _sweep_image_to_3d.py
    python _sweep_image_to_3d.py --limit 5
    python _sweep_image_to_3d.py --dry-run

KEY/BUDGET:
    Same env vars as _sweep_text_to_3d.py: TRIPO_API_KEY, TRIPO_BUDGET_USD.

OUTPUT:
    Writes <category>/<item>_v1.glb and appends entries to
    assets/_sweep_log.json (shared with text-to-3D).
"""

import argparse
import json
import os
import shutil
import time
from typing import Dict, List
import requests

PROJ = r"C:\Users\casey\Desktop\Homesteader"
ASSETS = os.path.join(PROJ, "assets")
TIPO_BASE = "https://openapi.tripo3d.ai/v3"
COST_PER_MESH_USD = 0.10
POLL_INTERVAL_SECONDS = 4.0
MAX_POLL_TIME_SECONDS = 240.0

SWEEP_CATEGORIES = [
    "structures", "farming", "ranching", "fishing", "fuel",
    "electricity", "water", "waste", "internet", "food",
    "appliances", "vehicles",
]

# Tripo3D requires the image to be encoded as base64 data URI in body
# (their openapi spec accepts either presigned upload or inline data).
# Inline data is easier in batch contexts since we don't need a backend.


def list_items_with_icons(category: str) -> List[Dict]:
    """Return items in <category> that have a real icon PNG (not just a
    group manifest)."""
    cat_dir = os.path.join(ASSETS, category)
    if not os.path.isdir(cat_dir):
        return []
    out = []
    for entry in sorted(os.listdir(cat_dir)):
        if entry.startswith("_") or entry.startswith("seed_"):
            continue
        group_dir = os.path.join(cat_dir, entry)
        manifest = os.path.join(group_dir, f"{entry}.json")
        if not os.path.isfile(manifest):
            continue
        try:
            d = json.load(open(manifest, encoding="utf-8"))
        except Exception:
            continue
        icon_name = d.get("icon", f"{entry}.png")
        icon_path = os.path.join(group_dir, icon_name)
        if not os.path.isfile(icon_path):
            continue
        out.append({
            "id": entry,
            "name": d.get("name", entry.replace("_", " ").title()),
            "category": category,
            "manifest_path": manifest,
            "icon_path": icon_path,
        })
    return out


def _auth_headers(api_key: str) -> Dict[str, str]:
    return {"Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"}


def submit_image_to_model(api_key: str, image_path: str,
                          timeout: float = 60.0) -> str:
    """POST base64 inline image. Returns task_id."""
    import base64
    url = f"{TIPO_BASE}/generation/image-to-model"
    with open(image_path, "rb") as f:
        img_bytes = f.read()
    data_uri = ("data:image/png;base64,"
                + base64.b64encode(img_bytes).decode("ascii"))
    body = {"image": data_uri, "model_version": "v3.0-20250101"}
    r = requests.post(url, headers=_auth_headers(api_key),
                      json=body, timeout=timeout)
    r.raise_for_status()
    j = r.json()
    if "task_id" not in j:
        raise RuntimeError(f"no task_id in response: {j}")
    return j["task_id"]


def poll_task(api_key: str, task_id: str, **kw) -> Dict:
    """Same polling strategy as text-to-3D."""
    url = f"{TIPO_BASE}/generation/task/{task_id}"
    deadline = time.time() + kw.get("max_time", MAX_POLL_TIME_SECONDS)
    poll_interval = kw.get("poll_interval", POLL_INTERVAL_SECONDS)
    while time.time() < deadline:
        r = requests.get(url, headers=_auth_headers(api_key), timeout=30)
        r.raise_for_status()
        j = r.json()
        status = j.get("data", {}).get("status",
                 j.get("status", "unknown"))
        if status == "success":
            return j
        if status in ("failed", "error", "cancelled"):
            raise RuntimeError(f"task {task_id} failed: {j}")
        time.sleep(poll_interval)
    raise TimeoutError(f"poll timeout for task {task_id}")


def download_glb(url: str, out_path: str, timeout: float = 60.0):
    with requests.get(url, stream=True, timeout=timeout) as f:
        f.raise_for_status()
        with open(out_path, "wb") as f2:
            shutil.copyfileobj(f.raw, f2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--categories", default="")
    ap.add_argument("--out", default=ASSETS)
    ap.add_argument("--log", default=os.path.join(ASSETS, "_sweep_log.json"))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    api_key = os.environ.get("TRIPO_API_KEY", "")
    budget = float(os.environ.get("TRIPO_BUDGET_USD", "0"))
    if not args.dry_run and not api_key:
        print("[tripo-img] TRIPO_API_KEY not set; running in dry-run mode.")
        args.dry_run = True
    if args.dry_run:
        print("[tripo-img] DRY RUN - no actual API calls will be made.")

    categories = (args.categories.split(",") if args.categories
                  else SWEEP_CATEGORIES)

    items = []
    for cat in categories:
        items.extend(list_items_with_icons(cat))
    if args.limit:
        items = items[: args.limit]
    print(f"[tripo-img] queue size: {len(items)} items")

    log = {"items": [], "budget_usd": budget, "spent_usd": 0.0}
    if os.path.isfile(args.log):
        try:
            log = json.load(open(args.log, encoding="utf-8"))
        except Exception:
            pass

    for i, it in enumerate(items, start=1):
        if (log["spent_usd"] + COST_PER_MESH_USD > budget
                and not args.dry_run):
            print(f"[tripo-img] budget cap reached; stopping.")
            break

        cat_out_dir = os.path.join(args.out, it["category"])
        os.makedirs(cat_out_dir, exist_ok=True)
        glb_path = os.path.join(cat_out_dir, f"{it['id']}_v1.glb")
        if os.path.isfile(glb_path):
            print(f"[tripo-img] {i}/{len(items)} {it['category']}/{it['id']} "
                  f"already has glb - skip")
            continue

        print(f"[tripo-img] {i}/{len(items)} "
              f"{it['category']}/{it['id']} icon={it['icon_path']}")

        if args.dry_run:
            log["items"].append({
                "id": it["id"], "category": it["category"],
                "name": it["name"], "icon": it["icon_path"],
                "status": "dry-run",
            })
            continue

        try:
            t0 = time.time()
            task_id = submit_image_to_model(api_key, it["icon_path"])
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
                "name": it["name"], "icon": it["icon_path"],
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
                "name": it["name"], "icon": it["icon_path"],
                "status": "error", "error": f"{type(e).__name__}: {e}",
            })

        with open(args.log, "w", encoding="utf-8") as f:
            json.dump(log, f, indent=2, sort_keys=True)

    print(f"[tripo-img] done. spent=${log['spent_usd']:.2f}")


if __name__ == "__main__":
    main()
