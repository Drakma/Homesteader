#!/usr/bin/env python
"""Push one asset from the kit into the game, in the 'homesteader' namespace mod.

  python tools/push_to_game.py <category> <item_id>

Every kit asset belongs to the 'homesteader' namespace, and the project layout is Namespace / Category / Asset folder:

    Homesteader/mods/homesteader/mod.json
    Homesteader/mods/homesteader/<category>/<item_id>/...     the asset folder (model, icon, manifest, stages)
    Homesteader/mods/homesteader/ai/<item_id>.json            only for an animal that carries its own AI

This is a full mod update, not just a file copy: it copies the asset (skipping unchanged files), makes sure mod.json
declares the category (and animal_ai when needed), bumps mod.json's patch version and date, writes an animal's own AI,
and refreshes the in-game asset list (icon + Resources/AssetCatalog.json). A folder switched off with '.disabled' in
the Mods app is left alone and reported. The game reads mods when Play starts, so restart Play.

tools/package_catalog_as_mods.py does the same for the whole catalog at once.
"""
import io
import json
import os
import re
import shutil
import sys
import time
from contextlib import redirect_stdout

TOOLS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(TOOLS)
sys.path.insert(0, TOOLS)

import package_catalog_as_mods as pk  # noqa: E402

NO_SUFFIX = ("water", "waste", "electricity", "internet", "logging", "farming", "fishing", "ranching")


def content_type(category):
    """The mod content type for a category folder (same mapping the core packager uses)."""
    return category if category in NO_SUFFIX else category.rstrip("s")


def _bump(version):
    m = re.match(r"^(\d+)\.(\d+)\.(\d+)$", version or "")
    return f"{m.group(1)}.{m.group(2)}.{int(m.group(3)) + 1}" if m else "1.0.1"


def push_item(category, item_id):
    category = (category or "").strip().lower()
    item_id = (item_id or "").strip().lower()
    if not category or not item_id or ".." in item_id or "/" in item_id or "\\" in item_id:
        raise ValueError("bad category or item id")
    if category.startswith("_") or category in pk.EXCLUDED_CATEGORIES:
        raise ValueError(f"'{category}' is not packaged into the game")
    src = os.path.join(pk.SRC_ASSETS_DIR, category, item_id)
    if not os.path.isdir(src):
        raise FileNotFoundError(f"asset folder not found: {category}/{item_id}")

    mod_dir = os.path.join(pk.MODS_DIR, pk.NAMESPACE)
    mj_path = os.path.join(mod_dir, "mod.json")
    if not os.path.isfile(mj_path):
        raise RuntimeError("the homesteader mod does not exist yet; run tools/package_catalog_as_mods.py once first")

    cat_dst = os.path.join(mod_dir, category)
    if os.path.isdir(cat_dst + ".disabled") or os.path.isdir(os.path.join(cat_dst, item_id + ".disabled")):
        return {"pushed": False, "notes": [f"{category}/{item_id} is switched off in the Mods app (.disabled); enable it first"]}

    manifest = {}
    mp = os.path.join(src, item_id + ".json")
    if os.path.isfile(mp):
        with open(mp, encoding="utf-8") as f:
            manifest = json.load(f)

    notes = []
    dst = os.path.join(cat_dst, item_id)
    if os.path.isdir(dst):
        shutil.rmtree(dst)      # replace it so a file removed from the asset does not linger in the mod
    os.makedirs(dst, exist_ok=True)
    pk.copy_tree_incremental(src, dst)
    files = sum(len(fs) for _r, _d, fs in os.walk(dst))
    notes.append(f"mod folder: mods/{pk.NAMESPACE}/{category}/{item_id}/ ({files} files)")

    with open(mj_path, encoding="utf-8") as f:
        mod = json.load(f)
    contents = mod.setdefault("contents", [])
    if not any(c.get("path") == category for c in contents):
        contents.append({"type": content_type(category), "path": category, "group": category})
        notes.append(f"mod.json: added the '{category}' content entry")

    ai = (manifest.get("category_fields") or {}).get("ai")
    if isinstance(ai, dict) and ai.get("behaviors") is not None:
        ai = dict(ai)
        ai.setdefault("id", item_id + "_ai")
        if not ai.get("applies_to"):
            ai["applies_to"] = [item_id]
        os.makedirs(os.path.join(mod_dir, "ai"), exist_ok=True)
        with open(os.path.join(mod_dir, "ai", item_id + ".json"), "w", encoding="utf-8") as f:
            json.dump(ai, f, indent=2)
        if not any(c.get("type") == "animal_ai" for c in contents):
            contents.append({"type": "animal_ai", "path": "ai/*.json"})
        notes.append(f"animal AI: ai/{item_id}.json")

    mod["version"] = _bump(mod.get("version"))
    mod["date"] = time.strftime("%Y-%m-%d")
    with open(mj_path, "w", encoding="utf-8") as f:
        json.dump(mod, f, indent=2)
    notes.append(f"mod.json: version {mod['version']}")

    # in-game asset list: icon + catalog
    icons = os.path.join(ROOT, "Homesteader", "Assets", "Resources", "Icons")
    icon_src = os.path.join(src, item_id + ".png")
    if os.path.isfile(icon_src) and os.path.isdir(icons):
        shutil.copy2(icon_src, os.path.join(icons, item_id + ".png"))
    import generate_unity_asset_catalog as gen
    with redirect_stdout(io.StringIO()):
        gen.main()
    notes.append("in-game asset list refreshed")

    return {"pushed": True, "mod_id": pk.NAMESPACE, "version": mod["version"], "files": files, "notes": notes,
            "message": f"Pushed to the '{pk.NAMESPACE}' mod. Restart Play (Unity re-reads mods when Play starts)."}


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    print(json.dumps(push_item(sys.argv[1], sys.argv[2]), indent=2))
