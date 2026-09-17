#!/usr/bin/env python3
"""
Homesteader Master Asset Kit Local HTTP Server with API Support
Serves static assets and provides REST API endpoints for asset management:
- POST /api/delete-asset: Permanently deletes an asset directory from disk.
"""

import os
import re
import sys
import time
import json
import shutil
import subprocess
import urllib.request
import urllib.parse
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
import regen_icons

# Windows' default console codepage (cp1252) can't encode most emoji, and
# category/item icons routinely contain them (see handle_add_category etc.).
# Without this, a plain print() of anything containing an emoji - which
# happens inside several request handlers' own success/debug logging -
# raises UnicodeEncodeError INSIDE the handler's try block, turning what
# would have been a successful save into a 500 error response. errors=
# "replace" makes printing merely cosmetically lossy (unprintable chars
# become "?") instead of crashing the request that triggered it.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8088
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INDEX_HTML_PATH = os.path.join(BASE_DIR, "index.html")


def read_embedded_catalog():
    """Parses and returns index.html's embedded `const ALL_ITEMS = [...]`
    array as a plain Python list of dicts. Read-only counterpart to
    patch_embedded_catalog/remove_items_from_embedded_catalog/
    rename_item_in_embedded_catalog - used wherever a handler needs to know
    what's in the snapshot (e.g. checking a category is truly empty, or
    finding ghost entries whose folder no longer exists) without duplicating
    the marker-parsing logic each time. Returns [] if anything about the
    literal's shape looks unexpected, rather than raising - callers should
    treat that the same as "nothing to report", not crash a request over it."""
    try:
        with open(INDEX_HTML_PATH, "r", encoding="utf-8") as f:
            content = f.read()
        marker = "const ALL_ITEMS = "
        start = content.index(marker)
        array_start = start + len(marker)
        end_of_line = content.index("\n", start)
        array_text = content[array_start:end_of_line]
        if not array_text.endswith("];"):
            return []
        return json.loads(array_text[:-1])
    except Exception as e:
        print(f"Warning: failed to read embedded catalog: {e}")
        return []


def resolve_reference_asset(category, item_id):
    """Validates an optional 'match style to this existing asset' reference
    (see the Request New Asset dialog's Reference Asset field). Returns
    (category, item_id) normalized if it's a real asset on disk, else None
    - silently dropped rather than failing the whole request, since the
    frontend already resolved it against a live item list before
    submitting; a stale/bad reference by the time of submission is a soft
    problem, not a reason to block someone's asset request."""
    if not category or not item_id:
        return None
    category = category.strip().lower()
    item_id = item_id.strip().lower()
    if category not in ALLOWED_CATEGORIES:
        return None
    if not os.path.isdir(os.path.join(BASE_DIR, category, item_id)):
        return None
    return (category, item_id)


def build_catalog_entry(category, item_id):
    """Builds one embedded-catalog-shaped entry (id/name/category/
    description/icon/models/best_model/model_format/has_3d/properties/
    growth/utilities/rigging/plugin_metadata/manifest) straight from the
    item's real manifest file on disk. Used by /api/catalog-entry so the
    frontend can live-patch a freshly created/updated item into its
    in-memory ALL_ITEMS without a full page reload - previously this same
    shape had to be hand-built ad hoc (and only from a Python one-off
    script, never from a page the browser could call) every time a new
    asset needed adding to the catalog. Returns None if the manifest is
    missing or unreadable."""
    item_dir = os.path.join(BASE_DIR, category, item_id)
    manifest_path = os.path.join(item_dir, f"{item_id}.json")
    if not os.path.isfile(manifest_path):
        return None
    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
    except Exception as e:
        print(f"Warning: failed to read manifest for {category}/{item_id}: {e}")
        return None

    icon_rel = f"{category}/{item_id}/{manifest.get('icon', '')}" if manifest.get("icon") else None
    models = []
    best_model = None
    best_model_rank = -1
    model_format = None
    for m in manifest.get("models", []):
        rel = f"{category}/{item_id}/{m['file']}"
        entry = {"file": m["file"], "format": m.get("format"), "path": rel}
        if m.get("description"):
            entry["description"] = m["description"]
        models.append(entry)
        # Prefer an animated ("_walk"/"_run") file over a merely rigged one,
        # and a rigged one over a plain mesh, as the "primary" model shown by
        # default - the most impressive available version wins, since the
        # viewer now plays back any animation it finds. Falls back to the
        # first model if nothing more specific exists.
        fname_lower = m["file"].lower()
        if any(k in fname_lower for k in ("_walk", "_run")):
            rank = 3
        elif "_rigged" in fname_lower:
            rank = 2
        else:
            rank = 1
        if rank > best_model_rank:
            best_model = rel
            model_format = m.get("format")
            best_model_rank = rank

    return {
        "id": manifest.get("id", item_id),
        "name": manifest.get("name", item_id),
        "category": manifest.get("category", category),
        "description": manifest.get("description", ""),
        "icon": icon_rel,
        "models": models,
        "best_model": best_model,
        "model_format": model_format,
        "has_3d": bool(models),
        "properties": manifest.get("properties", {}),
        "dimensions": manifest.get("dimensions", {}),
        "growth": manifest.get("growth", {}),
        "utilities": manifest.get("utilities", {}),
        "rigging": manifest.get("rigging", {}),
        "plugin_metadata": manifest.get("plugin_metadata", {}),
        "manifest": manifest
    }


def build_full_catalog():
    """Walks every category folder on disk and builds a fresh catalog entry
    (via build_catalog_entry) for each item found - the live counterpart to
    the old baked `const ALL_ITEMS = [...]` snapshot in index.html. Backing
    this from disk on every call (rather than a cached/baked copy) means an
    item's manifest is the only source of truth: nothing can go stale after
    a create/edit/move/delete, because there is no separate snapshot left to
    fall out of sync. Skips any directory entry that isn't itself a folder,
    and any folder whose manifest is missing/unreadable (build_catalog_entry
    already returns None for those - not an error, just not a real item)."""
    items = []
    for category in sorted(ALLOWED_CATEGORIES):
        cat_dir = os.path.join(BASE_DIR, category)
        if not os.path.isdir(cat_dir):
            continue
        for item_id in sorted(os.listdir(cat_dir)):
            if not os.path.isdir(os.path.join(cat_dir, item_id)):
                continue
            entry = build_catalog_entry(category, item_id)
            if entry is not None:
                items.append(entry)
    return items


_catalog_cache = {"items": None, "built_at": 0.0}
CATALOG_CACHE_TTL_SECONDS = 10


def invalidate_catalog_cache():
    """Drops the in-process cache of build_full_catalog()'s result, so the
    next /api/catalog request rebuilds it from disk. Called by every code
    path INSIDE this server process that changes an item's category, id,
    name, icon, models, or growth data (create/delete/move/rename/
    growth-group edits) - since /api/catalog is now the single source of
    truth for the frontend's ALL_ITEMS, invalidating unconditionally here
    is simpler and safer than trying to hand-patch just the affected
    fields (the old approach, back when this data was baked into
    index.html as a literal).

    This alone doesn't cover changes made by an external process writing
    directly to a manifest file on disk (e.g. a Claude session running its
    own one-off script instead of calling this server's API) - those can't
    reach into this process's memory to invalidate the cache. That's what
    CATALOG_CACHE_TTL_SECONDS is for: get_cached_catalog() also rebuilds
    once the cache is older than the TTL, regardless of whether anyone
    called this function, so external writes still show up within a
    bounded delay instead of requiring a server restart."""
    _catalog_cache["items"] = None


def get_cached_catalog():
    """Returns the cached full catalog, rebuilding it (build_full_catalog)
    when the cache has been invalidated, has never been built, or is older
    than CATALOG_CACHE_TTL_SECONDS. A full disk walk + per-item manifest
    read takes a few seconds at the current catalog size, which is too
    slow to redo on every page load - caching keeps /api/catalog fast,
    while the TTL (on top of explicit invalidation) bounds how stale it
    can ever get without reintroducing the old baked-snapshot bug, where
    staleness had no ceiling at all short of someone noticing and manually
    re-patching it."""
    age = time.time() - _catalog_cache["built_at"]
    if _catalog_cache["items"] is None or age > CATALOG_CACHE_TTL_SECONDS:
        _catalog_cache["items"] = build_full_catalog()
        _catalog_cache["built_at"] = time.time()
    return _catalog_cache["items"]


def patch_embedded_catalog(item_updates):
    """Legacy name kept for its many existing call sites (growth-group
    save/delete, etc.) - now just invalidates the live catalog cache
    instead of patching a baked HTML snapshot. item_updates is unused; the
    next /api/catalog call rebuilds everything fresh from disk regardless
    of which fields actually changed."""
    if item_updates:
        invalidate_catalog_cache()


def apply_moves_to_embedded_catalog(moved):
    """Legacy name kept for its call sites in the move-asset/move-batch
    handlers - now just invalidates the live catalog cache."""
    if moved:
        invalidate_catalog_cache()


def remove_items_from_embedded_catalog(items_to_remove):
    """Legacy name kept for its call sites in the delete-asset handlers -
    now just invalidates the live catalog cache."""
    if items_to_remove:
        invalidate_catalog_cache()


def rename_item_in_embedded_catalog(category, old_id, new_id, new_name):
    """Legacy name kept for its call site in the rename-asset handler -
    now just invalidates the live catalog cache."""
    invalidate_catalog_cache()
KIT_CONFIG_PATH = os.path.join(BASE_DIR, "kit_config.json")
MATERIAL_TAGS_PATH = os.path.join(BASE_DIR, "_schemas", "material_tags.json")
WATCHER_HEARTBEAT_PATH = os.path.join(BASE_DIR, "_asset_requests", "watcher_heartbeat.json")
WATCHER_STALE_AFTER_SECONDS = 15
ASSET_REQUESTS_DIR = os.path.join(BASE_DIR, "_asset_requests")
ASSET_REQUESTS_PENDING = os.path.join(ASSET_REQUESTS_DIR, "pending")
ASSET_REQUESTS_IN_PROGRESS = os.path.join(ASSET_REQUESTS_DIR, "in_progress")
ASSET_REQUESTS_DONE = os.path.join(ASSET_REQUESTS_DIR, "done")
ASSET_REQUESTS_BATCHES = os.path.join(ASSET_REQUESTS_DIR, "batches")
APPROVALS_DIR = os.path.join(ASSET_REQUESTS_DIR, "approvals")
CREATIVE_CLAW_BALANCE_PATH = os.path.join(BASE_DIR, "creative_claw_balance.json")
MESHY_BASE_URL = "https://api.meshy.ai"


def _find_meshy_api_key():
    """Reads MESHY_API_KEY from the env, falling back to the same key already
    configured for the meshy MCP server in .mcp.json, so it isn't
    retyped/duplicated into a third source file."""
    env_key = os.environ.get("MESHY_API_KEY")
    if env_key:
        return env_key
    mcp_config_path = os.path.join(os.path.dirname(BASE_DIR), ".mcp.json")
    try:
        with open(mcp_config_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        return cfg.get("mcpServers", {}).get("meshy", {}).get("env", {}).get("MESHY_API_KEY")
    except Exception:
        return None


def fetch_meshy_balance():
    """Live balance check against Meshy's REST API. Server-side only, so the
    key never reaches the browser."""
    api_key = _find_meshy_api_key()
    if not api_key:
        raise RuntimeError("MESHY_API_KEY not found (env var or .mcp.json)")
    req = urllib.request.Request(
        f"{MESHY_BASE_URL}/openapi/v1/balance",
        headers={"Authorization": f"Bearer {api_key}", "Accept": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=8) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data.get("balance", 0)


def load_creative_claw_balance():
    """Creative Claw has no local API key server.py can use directly (it's
    reached only through the MCP connector inside a Claude session), so its
    balance can't be live-polled here. This file is written by that session
    whenever it checks the balance via the get_credits_balance MCP tool -
    treat it as 'last known', not live."""
    if not os.path.exists(CREATIVE_CLAW_BALANCE_PATH):
        return None
    try:
        with open(CREATIVE_CLAW_BALANCE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


CLAUDE_USAGE_CACHE_PATH = os.path.join(os.path.expanduser("~"), ".claude", "vscode-claude-status-cache.json")


def load_claude_usage():
    """Genuinely live: the 'long-kudo.vscode-claude-status' VSCode extension
    (if installed) writes its own 5h/7d rate-limit utilization + reset
    timestamps to this cache file every time it polls, independent of this
    server or any particular Claude session. No token/credential is read or
    needed - just the numeric usage snapshot it already wrote to disk."""
    if not os.path.exists(CLAUDE_USAGE_CACHE_PATH):
        return None
    try:
        with open(CLAUDE_USAGE_CACHE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        usage = data.get("usageData") or {}
        return {
            "utilization_5h": usage.get("utilization5h"),
            "reset_5h_at": usage.get("reset5hAt"),
            "utilization_7d": usage.get("utilization7d"),
            "reset_7d_at": usage.get("reset7dAt"),
            "limit_status": usage.get("limitStatus"),
            "cache_updated_at": data.get("updatedAt")
        }
    except Exception:
        return None


_cached_hub_info = {"port": None, "csrf": None}


def find_agy_hub_port():
    """Finds the local Antigravity hub port and session CSRF token."""
    if _cached_hub_info["port"]:
        port = _cached_hub_info["port"]
        try:
            req = urllib.request.Request(f"http://127.0.0.1:{port}/", headers={"User-Agent": "AssetKit"})
            with urllib.request.urlopen(req, timeout=0.5) as resp:
                if resp.status == 200:
                    html = resp.read().decode("utf-8", errors="ignore")
                    match = re.search(r'"csrfToken":"([^"]+)"', html)
                    if match:
                        _cached_hub_info["csrf"] = match.group(1)
                        return port, _cached_hub_info["csrf"]
        except Exception:
            _cached_hub_info["port"] = None
            _cached_hub_info["csrf"] = None

    port = None
    try:
        cmd = 'wmic process where "name=\'agy.exe\'" get commandline /format:csv'
        out = subprocess.check_output(cmd, shell=True, text=True, errors="ignore")
        for line in out.splitlines():
            m = re.search(r'--hub[_-]?port[=\s]+(\d+)', line)
            if m:
                port = int(m.group(1))
                break
    except Exception:
        pass

    if not port:
        cli_log = os.path.join(os.path.expanduser("~"), ".gemini", "antigravity", "cli.log")
        if os.path.exists(cli_log):
            try:
                with open(cli_log, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()[-50:]
                    for line in reversed(lines):
                        m = re.search(r'--hub[_-]?port[=\s]+(\d+)', line)
                        if m:
                            port = int(m.group(1))
                            break
            except Exception:
                pass

    if not port:
        return None, None

    try:
        req = urllib.request.Request(f"http://127.0.0.1:{port}/", headers={"User-Agent": "AssetKit"})
        with urllib.request.urlopen(req, timeout=1.0) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
            match = re.search(r'"csrfToken":"([^"]+)"', html)
            if match:
                csrf = match.group(1)
                _cached_hub_info["port"] = port
                _cached_hub_info["csrf"] = csrf
                return port, csrf
    except Exception:
        pass

    return None, None


def load_gemini_usage():
    """Genuinely live: queries the local Antigravity (agy.exe) daemon for
    current model quotas (Gemini Flash, Gemini Pro, Claude Thinking, etc.),
    remaining percentages, and reset timestamps."""
    from datetime import datetime
    port, csrf = find_agy_hub_port()
    if not port or not csrf:
        return None

    try:
        url = f"http://127.0.0.1:{port}/exa.language_server_pb.LanguageServerService/GetUserStatus"
        payload = json.dumps({
            "wrapper_data": {},
            "metadata": {"ide_name": "antigravity", "extension_name": "antigravity", "locale": "en"}
        }).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "X-Codeium-Csrf-Token": csrf,
                "Connect-Protocol-Version": "1"
            }
        )

        with urllib.request.urlopen(req, timeout=2.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        user_status = data.get("userStatus") or data.get("user_status") or {}
        tier_info = user_status.get("userTier") or {}
        model_configs = (
            user_status.get("cascadeModelConfigData", {}).get("clientModelConfigs")
            or user_status.get("cascade_model_config_data", {}).get("client_model_configs")
            or []
        )

        models = []
        flash_model = None
        pro_model = None

        for m in model_configs:
            label = m.get("label", "")
            mid = m.get("modelId", "")
            qinfo = m.get("quotaInfo") or {}
            remaining_frac = qinfo.get("remainingFraction")
            if remaining_frac is not None:
                pct = round(remaining_frac * 100)
                reset_time = qinfo.get("resetTime")
                reset_ts = None
                if reset_time:
                    try:
                        reset_ts = int(datetime.fromisoformat(reset_time.replace("Z", "+00:00")).timestamp())
                    except Exception:
                        pass
                entry = {
                    "label": label,
                    "model_id": mid,
                    "remaining_percent": pct,
                    "remaining_fraction": remaining_frac,
                    "reset_time": reset_time,
                    "reset_timestamp": reset_ts
                }
                models.append(entry)
                if "flash" in label.lower() and not flash_model:
                    flash_model = entry
                elif "pro" in label.lower() and not pro_model:
                    pro_model = entry

        return {
            "online": True,
            "port": port,
            "tier_name": tier_info.get("name", "Google AI Pro"),
            "models": models,
            "flash": flash_model,
            "pro": pro_model
        }
    except Exception as e:
        return {"online": False, "error": str(e)}


def load_watcher_status():
    """Unlike the Claude usage cache, this one CAN be live: watch_asset_requests.py
    writes a heartbeat file on every poll cycle, so server.py can just check
    freshness directly rather than trusting a self-reported status."""
    if not os.path.exists(WATCHER_HEARTBEAT_PATH):
        return {"online": False, "reason": "not started"}
    try:
        with open(WATCHER_HEARTBEAT_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        last_beat = data.get("ts", 0)
        age = time.time() - last_beat
        online = age <= WATCHER_STALE_AFTER_SECONDS
        return {"online": online, "age_seconds": round(age, 1)}
    except Exception as e:
        return {"online": False, "reason": str(e)}


BUILTIN_CATEGORIES = {
    "farming", "ranching", "logging", "fishing", "building",
    "structures", "tools", "electricity", "water", "waste",
    "internet", "hud", "ground", "food", "fuel", "materials", "ingredients"
}

BUILTIN_PREFIX_STRIP = [
    "electricity_", "electric_", "water_", "waste_", "sewage_", "net_", "internet_",
    "animal_fish_", "ingredient_fillet_", "fishing_", "machinery_", "struct_", "tool_",
    "seed_", "crop_", "food_", "ingredient_", "fuel_", "mat_bale_", "mat_pelt_", "mat_wool_", "mat_",
    "tree_", "tile_", "clutter_", "hud_", "building_", "animal_"
]


def load_kit_config():
    """User-added categories, subfolders, and growth groups, persisted
    alongside the catalog. Built-in categories/taxonomy stay hardcoded; this
    file only ever holds what the "Add Category" / "Add Subfolder" /
    "Growth Groups" UI has created."""
    if not os.path.exists(KIT_CONFIG_PATH):
        return {"categories": {}, "subfolders": {}, "growth_groups": {}}
    try:
        with open(KIT_CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
    except Exception:
        return {"categories": {}, "subfolders": {}, "growth_groups": {}}
    cfg.setdefault("categories", {})
    cfg.setdefault("subfolders", {})
    cfg.setdefault("growth_groups", {})
    return cfg


def save_kit_config(cfg):
    with open(KIT_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)


def load_material_tags():
    """The tag registry (assets/_schemas/material_tags.json) - virtual/fake
    assets that stand in for a list of interchangeable real items in a
    recipe (see structures.schema.json's construction_recipe). Referenced
    in a recipe's item_id as '#tag_name'."""
    if not os.path.exists(MATERIAL_TAGS_PATH):
        return {"_readme": "", "tags": {}}
    try:
        with open(MATERIAL_TAGS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return {"_readme": "", "tags": {}}
    data.setdefault("tags", {})
    return data


def save_material_tags(data):
    with open(MATERIAL_TAGS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def get_prefix_strip_list():
    """Prefixes stripped when computing an item's naming "stem" during a
    move/rename. Custom categories' registered prefixes are added on top of
    the built-in list, longest-first so a more specific prefix always wins
    over a shorter one that happens to be a substring of it."""
    cfg = load_kit_config()
    custom = [f"{v['prefix']}_" for v in cfg["categories"].values() if v.get("prefix")]
    combined = list(dict.fromkeys(custom + BUILTIN_PREFIX_STRIP))
    combined.sort(key=len, reverse=True)
    return combined


def get_custom_category_prefix(category):
    cfg = load_kit_config()
    entry = cfg["categories"].get(category)
    return entry.get("prefix") if entry else None


# ALLOWED_CATEGORIES starts from the built-ins and is extended in place
# whenever a custom category is added, so no restart is needed.
ALLOWED_CATEGORIES = set(BUILTIN_CATEGORIES)
ALLOWED_CATEGORIES.update(load_kit_config()["categories"].keys())

def compute_target_id_for_category(current_id, target_category):
    current_id = current_id.strip().lower()

    # Strip known category prefixes (longest first; includes any custom
    # category prefixes registered via "Add Category")
    PREFIX_STRIP = get_prefix_strip_list()

    stem = current_id
    for p in PREFIX_STRIP:
        if stem.startswith(p):
            stem = stem[len(p):]
            break

    stem = stem.strip("_")
    if not stem:
        stem = current_id

    # Canonical prefixes according to Homesteader Taxonomy
    if target_category == "food":
        if "fillet" in stem:
            clean_stem = stem.replace("fillet_", "").replace("_fillet", "").strip("_")
            new_id = f"ingredient_fillet_{clean_stem}"
        elif any(x in stem for x in ["beef", "chicken", "pork", "meat", "egg", "milk", "wheat", "herb"]):
            new_id = f"ingredient_{stem}"
        else:
            new_id = f"food_{stem}"
    elif target_category == "fuel":
        new_id = f"fuel_{stem}"
    elif target_category == "materials":
        if any(x in stem for x in ["bale", "hay", "straw", "silage"]):
            clean_stem = stem.replace("bale_", "").strip("_")
            new_id = f"mat_bale_{clean_stem}"
        elif any(x in stem for x in ["pelt"]):
            clean_stem = stem.replace("pelt_", "").strip("_")
            new_id = f"mat_pelt_{clean_stem}"
        else:
            new_id = f"mat_{stem}"
    elif target_category == "ingredients":
        if "fillet" in stem:
            clean_stem = stem.replace("fillet_", "").replace("_fillet", "").strip("_")
            new_id = f"ingredient_fillet_{clean_stem}"
        else:
            new_id = f"ingredient_{stem}"
    elif target_category == "electricity":
        new_id = f"electricity_{stem}"
    elif target_category == "water":
        new_id = f"water_{stem}"
    elif target_category == "waste":
        new_id = f"waste_{stem}"
    elif target_category == "internet":
        new_id = f"net_{stem}"
    elif target_category == "structures":
        new_id = f"struct_{stem}"
    elif target_category == "tools":
        new_id = f"tool_{stem}"
    elif target_category == "logging":
        if any(x in stem for x in ["tree", "sapling", "stump", "branch", "leaf"]):
            new_id = f"tree_{stem}"
        elif any(x in stem for x in ["log", "lumber", "wood", "timber", "firewood"]):
            new_id = f"mat_{stem}"
        else:
            new_id = f"tree_{stem}"
    elif target_category == "fishing":
        fish_species = ["bass", "catfish", "crappie", "salmon", "trout", "walleye", "fish"]
        if any(sp in stem for sp in fish_species):
            if "fillet" in stem:
                clean_stem = stem.replace("fillet_", "").replace("_fillet", "").strip("_")
                new_id = f"ingredient_fillet_{clean_stem}"
            else:
                clean_stem = stem.replace("fish_", "").replace("_fish", "").strip("_")
                new_id = f"animal_fish_{clean_stem}"
        else:
            new_id = f"fishing_{stem}"
    elif target_category == "farming":
        if "seed" in stem:
            clean_stem = stem.replace("seed_", "").replace("_seed", "").strip("_")
            new_id = f"seed_{clean_stem}"
        elif "crop" in stem:
            clean_stem = stem.replace("crop_", "").replace("_crop", "").strip("_")
            new_id = f"crop_{clean_stem}"
        elif any(stem == x or stem.startswith(x + "_") for x in ["apple", "carrot", "corn", "potato", "pumpkin", "strawberry", "tomato", "truffle"]):
            new_id = f"food_{stem}"
        elif any(stem == x or stem.startswith(x + "_") for x in ["wheat", "cotton", "sunflower", "herb", "herbs"]):
            new_id = f"ingredient_{stem}"
        else:
            new_id = f"crop_{stem}"
    elif target_category == "ranching":
        livestock = ["chicken", "cow", "pig", "sheep", "goat"]
        if any(x in stem for x in ["bale", "hay", "straw", "silage"]):
            clean_stem = stem.replace("bale_", "").strip("_")
            new_id = f"mat_bale_{clean_stem}"
        elif any(x in stem for x in ["wool", "fleece"]):
            new_id = f"mat_{stem}"
        elif any(x in stem for x in ["pelt", "leather"]):
            new_id = f"mat_{stem}"
        elif any(x in stem for x in ["meat", "beef", "pork", "egg", "milk"]):
            new_id = f"ingredient_{stem}"
        elif any(a in stem for a in livestock):
            new_id = f"animal_{stem}"
        else:
            new_id = f"animal_{stem}"
    elif target_category == "ground":
        if any(x in stem for x in ["tile", "dirt", "grass", "sand", "stone", "terrain", "ground", "path"]):
            clean_stem = stem.replace("tile_", "").strip("_")
            new_id = f"tile_{clean_stem}"
        else:
            clean_stem = stem.replace("clutter_", "").strip("_")
            new_id = f"clutter_{clean_stem}"
    elif target_category == "building":
        new_id = f"building_{stem}"
    elif target_category == "hud":
        new_id = f"hud_{stem}"
    else:
        # Custom (non-built-in) category: use its registered asset prefix
        # if one was set when the category was created, else fall back to
        # the category name itself.
        custom_prefix = get_custom_category_prefix(target_category)
        new_id = f"{custom_prefix or target_category}_{stem}"

    # Clean double underscores
    while "__" in new_id:
        new_id = new_id.replace("__", "_")
    new_id = new_id.strip("_")

    return new_id


def move_single_asset_on_disk(category, item_id, target_category):
    if category not in ALLOWED_CATEGORIES or target_category not in ALLOWED_CATEGORIES:
        raise ValueError(f"Invalid category: {category} -> {target_category}")
    if ".." in item_id or "/" in item_id or "\\" in item_id:
        raise ValueError(f"Invalid item_id: {item_id}")

    old_dir = os.path.join(BASE_DIR, category, item_id)
    if not os.path.exists(old_dir) or not os.path.isdir(old_dir):
        raise FileNotFoundError(f"Asset folder not found: {category}/{item_id}")

    new_id = compute_target_id_for_category(item_id, target_category)

    # Ensure collision-free directory name
    target_cat_dir = os.path.join(BASE_DIR, target_category)
    os.makedirs(target_cat_dir, exist_ok=True)

    candidate_id = new_id
    counter = 2
    while os.path.exists(os.path.join(target_cat_dir, candidate_id)):
        candidate_id = f"{new_id}_{counter}"
        counter += 1
    new_id = candidate_id

    new_dir = os.path.join(target_cat_dir, new_id)
    print(f"[MOVE ASSET] {category}/{item_id} -> {target_category}/{new_id}")

    # 1. Move directory
    shutil.move(old_dir, new_dir)

    # 2. Rename files prefixed with item_id.*
    renamed_files_map = {}
    for fname in list(os.listdir(new_dir)):
        if fname.startswith(f"{item_id}."):
            ext = fname[len(item_id):]
            new_fname = f"{new_id}{ext}"
            old_fpath = os.path.join(new_dir, fname)
            new_fpath = os.path.join(new_dir, new_fname)
            if os.path.exists(new_fpath) and old_fpath != new_fpath:
                os.remove(new_fpath)
            os.rename(old_fpath, new_fpath)
            renamed_files_map[fname] = new_fname

    # 3. Update manifest JSON
    manifest_file = os.path.join(new_dir, f"{new_id}.json")
    if not os.path.exists(manifest_file):
        manifest_file = os.path.join(new_dir, f"{item_id}.json")

    new_name = None
    if os.path.exists(manifest_file):
        try:
            with open(manifest_file, "r", encoding="utf-8") as f:
                manifest = json.load(f)

            manifest["id"] = new_id
            manifest["category"] = target_category
            manifest["icon"] = f"{new_id}.png"
            new_name = manifest.get("name", new_id.replace("_", " ").title())

            # Update models list if any model file was renamed
            if "models" in manifest and isinstance(manifest["models"], list):
                for m in manifest["models"]:
                    if isinstance(m, dict):
                        m_file = m.get("file", "")
                        if m_file in renamed_files_map:
                            m["file"] = renamed_files_map[m_file]

            # Update stages if referencing item_id
            if "growth" in manifest and isinstance(manifest["growth"], dict):
                stages = manifest["growth"].get("stages", [])
                for st in stages:
                    if isinstance(st, dict) and st.get("item_id") == item_id:
                        st["item_id"] = new_id
                curr_st = manifest["growth"].get("current_stage")
                if isinstance(curr_st, dict) and curr_st.get("item_id") == item_id:
                    curr_st["item_id"] = new_id

            with open(os.path.join(new_dir, f"{new_id}.json"), "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2)
            if manifest_file != os.path.join(new_dir, f"{new_id}.json") and os.path.exists(manifest_file):
                os.remove(manifest_file)
        except Exception as e:
            print(f"Warning updating manifest JSON: {e}")

    # 4. If OBJ references renamed MTL file, update mtllib line
    for old_fname, new_fname in renamed_files_map.items():
        if old_fname.endswith(".obj"):
            obj_path = os.path.join(new_dir, new_fname)
            try:
                with open(obj_path, "r", encoding="utf-8", errors="ignore") as f:
                    obj_text = f.read()
                if f"{item_id}.mtl" in obj_text:
                    obj_text = obj_text.replace(f"{item_id}.mtl", f"{new_id}.mtl")
                    with open(obj_path, "w", encoding="utf-8") as f:
                        f.write(obj_text)
            except Exception as e:
                print(f"Warning updating OBJ: {e}")

    # 5. Update README.md if present
    readme_path = os.path.join(new_dir, "README.md")
    if os.path.exists(readme_path):
        try:
            with open(readme_path, "r", encoding="utf-8") as f:
                readme_text = f.read()
            readme_text = readme_text.replace(f"{item_id}.png", f"{new_id}.png")
            readme_text = readme_text.replace(f"{item_id}.json", f"{new_id}.json")
            readme_text = readme_text.replace(f"#{item_id}", f"#{new_id}")
            readme_text = readme_text.replace(f"`{item_id}`", f"`{new_id}`")
            readme_text = readme_text.replace(f"assets/{category}/", f"assets/{target_category}/")
            with open(readme_path, "w", encoding="utf-8") as f:
                f.write(readme_text)
        except Exception as e:
            print(f"Warning updating README.md: {e}")

    return {
        "old_id": item_id,
        "new_id": new_id,
        "old_category": category,
        "target_category": target_category,
        "new_name": new_name or new_id.replace("_", " ").title(),
        "icon": f"{target_category}/{new_id}/{new_id}.png"
    }


def set_item_species(category, item_id, species):
    """Tags an existing item's manifest with a growth species so it groups
    into that species' lifecycle subfolder in the asset kit UI. Only ever
    touches an item that already exists on disk — never creates one."""
    if category not in ALLOWED_CATEGORIES:
        raise ValueError(f"Invalid category: {category}")
    if ".." in item_id or "/" in item_id or "\\" in item_id:
        raise ValueError(f"Invalid item_id: {item_id}")
    if not species or not re.match(r"^[a-z0-9_]+$", species):
        raise ValueError(f"Invalid species: {species!r} (lowercase letters, numbers, underscores only)")

    item_dir = os.path.join(BASE_DIR, category, item_id)
    if not os.path.isdir(item_dir):
        raise FileNotFoundError(f"Asset folder not found: {category}/{item_id}")

    manifest_file = os.path.join(item_dir, f"{item_id}.json")
    if not os.path.exists(manifest_file):
        raise FileNotFoundError(f"Manifest not found: {category}/{item_id}/{item_id}.json")

    with open(manifest_file, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    growth = manifest.get("growth") or {}
    growth["is_growable"] = True
    growth["species"] = species
    growth.setdefault("growth_type", growth.get("growth_type") or "generic")
    growth.setdefault("max_age", growth.get("max_age"))
    growth.setdefault("time_unit", growth.get("time_unit") or "days")
    growth.setdefault("total_stages", growth.get("total_stages") or 0)
    growth.setdefault("current_stage", growth.get("current_stage"))
    growth.setdefault("stages", growth.get("stages") or [])
    manifest["growth"] = growth

    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    return manifest


def assign_item_to_subfolder(category, item_id, target_category, species):
    """Moves an item into target_category (if it isn't already there) and
    tags it with the given growth species, so it groups into that species'
    subfolder. Mirrors move_single_asset_on_disk's category-move semantics,
    then layers the species tag on top in a second, focused write."""
    working_category = category
    working_id = item_id
    moved = None

    if target_category and target_category != category:
        moved = move_single_asset_on_disk(category, item_id, target_category)
        working_category = target_category
        working_id = moved["new_id"]

    manifest = set_item_species(working_category, working_id, species)

    return {
        "old_id": item_id,
        "old_category": category,
        "new_id": working_id,
        "category": working_category,
        "target_category": working_category,
        "moved": moved is not None,
        "species": species,
        "new_name": manifest.get("name"),
        "growth": manifest.get("growth"),
        "icon": f"{working_category}/{working_id}/{working_id}.png"
    }


NEUTRAL_GROWTH = {
    "is_growable": False, "growth_type": None, "species": None,
    "max_age": None, "time_unit": None, "total_stages": 0,
    "current_stage": None, "stages": []
}


def find_items_with_species(species_key):
    """Scans every category for items currently tagged with this species
    (growth.species == species_key), regardless of what the persisted group
    definition says. Used to self-heal: any item tagged with a species that
    isn't in the new stage list gets its growth data cleared, so removing a
    stage from a group (or deleting the group outright) can't leave a
    dangling species tag on an item the UI no longer shows as part of it."""
    found = []
    for cat in ALLOWED_CATEGORIES:
        cat_dir = os.path.join(BASE_DIR, cat)
        if not os.path.isdir(cat_dir):
            continue
        for item_id in os.listdir(cat_dir):
            manifest_path = os.path.join(cat_dir, item_id, f"{item_id}.json")
            if not os.path.isfile(manifest_path):
                continue
            try:
                with open(manifest_path, "r", encoding="utf-8") as f:
                    manifest = json.load(f)
            except Exception:
                continue
            if (manifest.get("growth") or {}).get("species") == species_key:
                found.append((cat, item_id))
    return found


def find_items_with_species_in_embedded_catalog(species_key):
    """Same idea as find_items_with_species, but scans index.html's baked-in
    ALL_ITEMS snapshot instead of the real manifest files on disk. The two
    can diverge (e.g. a group that was only ever baked into the snapshot by
    an earlier build/edit and never actually written to kit_config.json or
    the real manifests) - a delete that only clears disk-truth orphans would
    silently leave that stale entry in the snapshot forever. Reading and
    patching by category+id keeps this in sync however it got out of sync."""
    try:
        with open(INDEX_HTML_PATH, "r", encoding="utf-8") as f:
            content = f.read()
        marker = "const ALL_ITEMS = "
        start = content.index(marker)
        array_start = start + len(marker)
        end_of_line = content.index("\n", start)
        array_text = content[array_start:end_of_line]
        if not array_text.endswith("];"):
            return []
        items = json.loads(array_text[:-1])
        return [
            (it.get("category"), it.get("id"))
            for it in items
            if (it.get("growth") or {}).get("species") == species_key
        ]
    except Exception as e:
        print(f"Warning: failed to scan embedded catalog for species '{species_key}': {e}")
        return []


def clear_item_growth(category, item_id):
    manifest_path = os.path.join(BASE_DIR, category, item_id, f"{item_id}.json")
    if not os.path.isfile(manifest_path):
        return
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    manifest["growth"] = dict(NEUTRAL_GROWTH)
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)


def remove_growth_group(species_key):
    """Deletes a growth group entirely: clears growth data on every member
    item, then removes the group + its matching subfolder entry."""
    orphans = find_items_with_species(species_key)
    for cat, item_id in orphans:
        clear_item_growth(cat, item_id)

    cfg = load_kit_config()
    cfg["growth_groups"].pop(species_key, None)
    cfg["subfolders"].pop(species_key, None)
    save_kit_config(cfg)

    # Union with whatever the embedded index.html snapshot still thinks is
    # tagged with this species - the snapshot can hold entries that never
    # actually existed on disk/in kit_config.json (e.g. baked in by an
    # earlier build), so disk-truth orphans alone can miss them entirely.
    embedded_orphans = find_items_with_species_in_embedded_catalog(species_key)
    all_orphans = {(c, i) for c, i in orphans} | {(c, i) for c, i in embedded_orphans}
    patch_embedded_catalog([
        {"category": c, "item_id": i, "growth": dict(NEUTRAL_GROWTH)} for c, i in all_orphans
    ])

    return {"species": species_key, "cleared_items": [{"category": c, "item_id": i} for c, i in orphans]}


def save_growth_group(species_key, group_def):
    """Creates/updates a growth group: a named lifecycle (e.g. "cattle") with
    1-10 ordered stages, each pointing at an existing item. Writes the full
    stages array + current_stage into every member item's own manifest
    (matching the hand-authored convention already used by animal_cow_adult
    etc.), and persists the group definition + a matching subfolder entry so
    the sidebar's species-subfolder UI picks it up immediately."""
    if not species_key or not re.match(r"^[a-z][a-z0-9_]*$", species_key):
        raise ValueError("Growth group key must start with a letter and contain only lowercase letters, numbers, and underscores.")

    name = group_def.get("name", "").strip()
    icon = group_def.get("icon", "").strip() or "🌱"
    category = group_def.get("category", "").strip().lower()
    growth_type = group_def.get("growth_type", "").strip() or "generic"
    max_age = group_def.get("max_age")
    time_unit = group_def.get("time_unit", "").strip() or "days"
    stages_in = group_def.get("stages", [])

    if not name:
        raise ValueError("Growth group name is required.")
    if category not in ALLOWED_CATEGORIES:
        raise ValueError(f"Invalid category: {category}")
    if not isinstance(max_age, (int, float)) or max_age <= 0:
        raise ValueError("max_age must be a positive number.")
    if not isinstance(stages_in, list) or not (1 <= len(stages_in) <= 10):
        raise ValueError("A growth group needs 1 to 10 stages.")

    resolved_stages = []
    for i, st in enumerate(stages_in, start=1):
        st_item_id = st.get("item_id", "").strip().lower()
        st_category = st.get("category", "").strip().lower()
        st_name = st.get("name", "").strip() or f"stage {i}"
        age_min = st.get("age_min")
        age_max = st.get("age_max")

        if not st_item_id or not st_category:
            raise ValueError(f"Stage {i} is missing an item.")
        if st_category not in ALLOWED_CATEGORIES:
            raise ValueError(f"Stage {i}: invalid category '{st_category}'")
        if not os.path.isdir(os.path.join(BASE_DIR, st_category, st_item_id)):
            raise FileNotFoundError(f"Stage {i}: asset not found: {st_category}/{st_item_id}")
        if not isinstance(age_min, (int, float)) or not isinstance(age_max, (int, float)) or age_min < 0 or age_max <= age_min:
            raise ValueError(f"Stage {i}: age_min/age_max must be numbers with age_max > age_min.")

        resolved_stages.append({
            "stage": i, "name": st_name, "item_id": st_item_id,
            "category": st_category, "age_min": age_min, "age_max": age_max
        })

    total_stages = len(resolved_stages)
    # Public stages array matches the existing item_v1 schema (no "category"
    # field - other manifests only ever reference sibling stages by item_id).
    public_stages = [
        {"stage": s["stage"], "name": s["name"], "item_id": s["item_id"], "age_min": s["age_min"], "age_max": s["age_max"]}
        for s in resolved_stages
    ]

    # Orphan cleanup: any item still tagged with this species from a previous
    # save (or a stage the caller just removed) but not in the new stage list
    # gets its growth data cleared, so removing a stage from the group also
    # removes that item from it - it doesn't just stay silently tagged.
    new_members = {(s["category"], s["item_id"]) for s in resolved_stages}
    prior_members = {(c, i) for c, i in find_items_with_species(species_key)} \
        | {(c, i) for c, i in find_items_with_species_in_embedded_catalog(species_key)}
    cleared_items = []
    for cat, item_id in prior_members:
        if (cat, item_id) not in new_members:
            clear_item_growth(cat, item_id)
            cleared_items.append({"category": cat, "item_id": item_id})

    updated_items = []
    for s in resolved_stages:
        manifest_path = os.path.join(BASE_DIR, s["category"], s["item_id"], f"{s['item_id']}.json")
        if not os.path.exists(manifest_path):
            raise FileNotFoundError(f"Manifest not found: {s['category']}/{s['item_id']}")
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        manifest["growth"] = {
            "is_growable": True,
            "growth_type": growth_type,
            "species": species_key,
            "max_age": max_age,
            "time_unit": time_unit,
            "total_stages": total_stages,
            "current_stage": {
                "stage": s["stage"], "name": s["name"],
                "age_min": s["age_min"], "age_max": s["age_max"]
            },
            "stages": public_stages
        }

        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

        updated_items.append({
            "category": s["category"], "item_id": s["item_id"],
            "stage": s["stage"], "growth": manifest["growth"]
        })

    cfg = load_kit_config()
    cfg["growth_groups"][species_key] = {
        "name": name, "icon": icon, "category": category,
        "growth_type": growth_type, "max_age": max_age, "time_unit": time_unit,
        "stages": public_stages
    }
    cfg["subfolders"][species_key] = {"name": name, "icon": icon, "category": category}
    save_kit_config(cfg)

    patch_embedded_catalog(
        [{"category": u["category"], "item_id": u["item_id"], "growth": u["growth"]} for u in updated_items]
        + [{"category": c["category"], "item_id": c["item_id"], "growth": dict(NEUTRAL_GROWTH)} for c in cleared_items]
    )

    return {
        "species": species_key,
        "group": cfg["growth_groups"][species_key],
        "updated_items": updated_items,
        "cleared_items": cleared_items
    }


# Category -> reasonable default growth_type for an auto-created group, since
# a stage-set request (see handle_request_asset_stages) never asks the user
# for one up front. Falls back to "generic" for anything not listed.
AUTO_GROWTH_TYPE_BY_CATEGORY = {
    "ranching": "animal", "farming": "crop", "logging": "tree", "fishing": "animal",
}


def maybe_autocreate_growth_group(request_group_id):
    """Called every time a stage-set request (handle_request_asset_stages)
    finishes generating. Once every stage in the set has reported status
    'done' with a created_item_id, auto-assembles them into a growth group
    via save_growth_group - so 'request Corn with 4 stages' ends with a
    working, browsable growth group with no separate manual step. Ages are
    an even 30-day-per-stage default (editable afterward via Edit Stages,
    same as any hand-built group) since the request UI never collects them.

    Returns the created group dict on success, or None if the set isn't
    fully done yet or auto-creation isn't possible (missing item_id, no
    such folder on disk, etc - logged but never raised, since this is a
    best-effort convenience on top of the always-available manual flow)."""
    if not request_group_id:
        return None
    try:
        members = []
        for folder in (ASSET_REQUESTS_PENDING, ASSET_REQUESTS_IN_PROGRESS, ASSET_REQUESTS_DONE):
            if not os.path.isdir(folder):
                continue
            for fname in os.listdir(folder):
                if not fname.endswith(".json"):
                    continue
                try:
                    with open(os.path.join(folder, fname), "r", encoding="utf-8") as f:
                        req = json.load(f)
                except Exception:
                    continue
                if req.get("request_group_id") == request_group_id:
                    members.append(req)

        if not members:
            return None

        total_stages = members[0].get("total_stages")
        if not total_stages or len(members) != total_stages:
            return None  # not all stage requests exist yet (shouldn't happen, but don't half-build a group)

        if not all(m.get("status") == "done" and m.get("created_item_id") for m in members):
            return None  # still waiting on other stages

        members.sort(key=lambda m: m.get("stage_number", 0))
        base_name = members[0].get("base_name") or members[0].get("name", "").split(" - ")[0]
        category = members[0].get("category")

        # User-supplied group metadata (from the dedicated Request Growth
        # Group dialog) wins over the crude auto-inferred defaults below -
        # it's duplicated onto every stage's request_data at request time,
        # so members[0] always has it when it was provided at all.
        species_key = re.sub(r"[^a-z0-9]+", "_", base_name.lower()).strip("_") or f"group_{request_group_id}"
        icon = members[0].get("group_icon") or "🌱"
        growth_type = members[0].get("group_growth_type") or AUTO_GROWTH_TYPE_BY_CATEGORY.get(category, "generic")
        time_unit = members[0].get("group_time_unit") or "days"
        stage_span_days = 30
        group_max_age = members[0].get("group_max_age") or (total_stages * stage_span_days)

        stages = []
        for m in members:
            item_id = m["created_item_id"]
            if not os.path.isdir(os.path.join(BASE_DIR, category, item_id)):
                print(f"Warning: auto growth-group skipped - {category}/{item_id} not found on disk")
                return None
            # A stage's own user-supplied age_min/age_max (set per-stage in
            # the Request Growth Group dialog) wins; otherwise fall back to
            # the even 30-day-per-stage default, same as before.
            age_min = m.get("age_min")
            age_max = m.get("age_max")
            if age_min is None:
                age_min = (m["stage_number"] - 1) * stage_span_days
            if age_max is None:
                age_max = m["stage_number"] * stage_span_days
            stages.append({
                "category": category,
                "item_id": item_id,
                "name": m.get("stage_name", "").lower() or f"stage {m.get('stage_number')}",
                "age_min": age_min,
                "age_max": age_max,
            })

        result = save_growth_group(species_key, {
            "name": base_name,
            "icon": icon,
            "category": category,
            "growth_type": growth_type,
            "max_age": group_max_age,
            "time_unit": time_unit,
            "stages": stages,
        })

        print(f"[AUTO GROWTH GROUP] Assembled '{base_name}' ({species_key}) from {total_stages} finished stage(s)")
        return result

    except Exception as e:
        print(f"Warning: failed to auto-create growth group for '{request_group_id}': {e}")
        return None


class AssetKitHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE_DIR, **kwargs)

    def translate_path(self, path):
        translated = super().translate_path(path)
        if not os.path.exists(translated) and os.path.basename(path) == "T_Homesteader_Palette.png":
            palette_fallback = os.path.join(BASE_DIR, "textures", "palettes", "T_Homesteader_Palette.png")
            if os.path.exists(palette_fallback):
                return palette_fallback
        return translated

    def end_headers(self):
        # Enable CORS and disable caching for live dev. The no-store header
        # was previously just a comment with no code behind it - assets
        # replaced on disk (e.g. a regenerated model/icon at the same path)
        # would keep being served stale from the browser's cache until a
        # hard refresh. This makes every response actually non-cacheable.
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS, DELETE")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def do_GET(self):
        if self.path == "/api/catalog":
            self.handle_get_catalog()
            return
        if self.path == "/api/kit-config":
            self.handle_get_kit_config()
            return
        if self.path == "/api/ping":
            self.handle_ping()
            return
        if self.path == "/api/meshy-balance":
            self.handle_meshy_balance()
            return
        if self.path == "/api/creative-claw-balance":
            self.handle_creative_claw_balance()
            return
        if self.path == "/api/claude-usage":
            self.handle_claude_usage()
            return
        if self.path == "/api/gemini-usage":
            self.handle_gemini_usage()
            return
        if self.path == "/api/watcher-status":
            self.handle_watcher_status()
            return
        if self.path == "/api/asset-requests":
            self.handle_list_asset_requests()
            return
        if self.path == "/api/growth-groups":
            self.handle_get_growth_groups()
            return
        if self.path == "/api/material-tags":
            self.handle_get_material_tags()
            return
        if self.path.startswith("/api/schemas?") or self.path == "/api/schemas":
            self.handle_get_schemas()
            return
        if self.path.startswith("/api/schema/validate?") or self.path == "/api/schema/validate":
            self.handle_validate_schema()
            return
        if self.path.startswith("/api/schema?") or self.path == "/api/schema":
            self.handle_get_schema()
            return
        if self.path == "/api/ghost-entries":
            self.handle_get_ghost_entries()
            return
        if self.path.startswith("/api/catalog-entry?") or self.path == "/api/catalog-entry":
            self.handle_get_catalog_entry()
            return
        if self.path.startswith("/api/item-files?") or self.path == "/api/item-files":
            self.handle_get_item_files()
            return
        if self.path == "/api/pending-approvals":
            self.handle_list_pending_approvals()
            return
        if self.path.startswith("/api/approval-status?"):
            self.handle_get_approval_status()
            return
        super().do_GET()

    def handle_ping(self):
        self.send_json_response({"success": True, "status": "online"}, 200)

    def handle_meshy_balance(self):
        try:
            balance = fetch_meshy_balance()
            self.send_json_response({"success": True, "balance": balance}, 200)
        except Exception as e:
            self.send_json_response({"success": False, "error": str(e)}, 502)

    def handle_creative_claw_balance(self):
        data = load_creative_claw_balance()
        if data is None:
            self.send_json_response({"success": False, "error": "No balance recorded yet"}, 404)
            return
        self.send_json_response({"success": True, **data}, 200)

    def handle_claude_usage(self):
        data = load_claude_usage()
        if data is None:
            self.send_json_response({"success": False, "error": "vscode-claude-status-cache.json not found — install/enable the 'Claude Status' VSCode extension"}, 404)
            return
        self.send_json_response({"success": True, **data}, 200)

    def handle_gemini_usage(self):
        data = load_gemini_usage()
        if data is None or not data.get("online"):
            err = data.get("error") if data else "Antigravity/Gemini daemon not detected or offline"
            self.send_json_response({"success": False, "error": err}, 404)
            return
        self.send_json_response({"success": True, **data}, 200)

    def handle_watcher_status(self):
        data = load_watcher_status()
        self.send_json_response({"success": True, **data}, 200)

    def handle_get_ghost_entries(self):
        """Lists every embedded-catalog entry whose folder no longer exists
        on disk - 'in the index without a folder', per the status-bar
        notification. This is a live scan (not cached), so it always
        reflects the real current state of both index.html and disk."""
        try:
            ghosts = []
            for it in read_embedded_catalog():
                category = it.get("category", "")
                item_id = it.get("id", "")
                if not os.path.isdir(os.path.join(BASE_DIR, category, item_id)):
                    ghosts.append({"category": category, "id": item_id, "name": it.get("name", item_id)})
            self.send_json_response({"success": True, "ghosts": ghosts, "count": len(ghosts)}, 200)
        except Exception as e:
            print(f"Error scanning for ghost entries: {e}")
            self.send_json_response({"success": False, "error": str(e)}, 500)

    def handle_get_catalog(self):
        """Returns the full catalog, built live from every item's manifest
        on disk (build_full_catalog) - the frontend fetches this once on
        page load to populate its in-memory ALL_ITEMS, replacing the old
        `const ALL_ITEMS = [...]` snapshot that used to be baked directly
        into index.html. Disk is now the only source of truth: there is no
        separate snapshot for a create/edit/move/delete to leave stale."""
        try:
            items = get_cached_catalog()
            self.send_json_response({"success": True, "items": items, "count": len(items)}, 200)
        except Exception as e:
            print(f"Error building full catalog: {e}")
            self.send_json_response({"success": False, "error": str(e)}, 500)

    def handle_invalidate_catalog_cache(self):
        """Lets an external process that just wrote directly to manifest
        files on disk (e.g. a Claude session's own one-off script, or
        watch_asset_requests.py finishing a batch) force /api/catalog to
        rebuild on its very next call, instead of waiting out the TTL.
        Cheap and safe to call any time - worst case it's a no-op rebuild
        a few seconds early."""
        invalidate_catalog_cache()
        self.send_json_response({"success": True}, 200)

    def handle_get_catalog_entry(self):
        """Returns one freshly-built catalog entry for category+id (query
        params). Lets the frontend live-patch a newly created/updated item
        into its in-memory ALL_ITEMS the moment a queued request finishes,
        instead of requiring a full page reload to see it - see
        checkForCompletedBatches in index.html, which calls this for every
        item in a batch as soon as all of them report done."""
        try:
            query = urllib.parse.urlparse(self.path).query
            params = urllib.parse.parse_qs(query)
            category = (params.get("category", [""])[0]).strip().lower()
            item_id = (params.get("id", [""])[0]).strip().lower()

            if not category or not item_id:
                self.send_json_response({"success": False, "error": "Missing category or id"}, 400)
                return

            entry = build_catalog_entry(category, item_id)
            if entry is None:
                self.send_json_response({"success": False, "error": f"Asset not found: {category}/{item_id}"}, 404)
                return

            self.send_json_response({"success": True, "entry": entry}, 200)
        except Exception as e:
            print(f"Error building catalog entry: {e}")
            self.send_json_response({"success": False, "error": str(e)}, 500)

    def handle_get_item_files(self):
        """Lists every file physically present in an item's folder (models,
        textures, icon, manifest, README, anything else), with size and a
        browser-fetchable relative path - lets the item modal show a
        complete on-disk file listing rather than only what the manifest's
        models[] array happens to mention."""
        try:
            query = urllib.parse.urlparse(self.path).query
            params = urllib.parse.parse_qs(query)
            category = (params.get("category", [""])[0]).strip().lower()
            item_id = (params.get("id", [""])[0]).strip().lower()

            if not category or not item_id:
                self.send_json_response({"success": False, "error": "Missing category or id"}, 400)
                return
            if category not in ALLOWED_CATEGORIES:
                self.send_json_response({"success": False, "error": f"Invalid category: {category}"}, 400)
                return

            item_dir = os.path.join(BASE_DIR, category, item_id)
            if not os.path.isdir(item_dir):
                self.send_json_response({"success": False, "error": f"Asset not found: {category}/{item_id}"}, 404)
                return

            files = []
            for fname in sorted(os.listdir(item_dir)):
                fpath = os.path.join(item_dir, fname)
                if not os.path.isfile(fpath):
                    continue
                files.append({
                    "name": fname,
                    "size": os.path.getsize(fpath),
                    "path": f"{category}/{item_id}/{fname}"
                })

            self.send_json_response({"success": True, "files": files, "folder": f"{category}/{item_id}"}, 200)
        except Exception as e:
            print(f"Error listing item files: {e}")
            self.send_json_response({"success": False, "error": str(e)}, 500)

    def handle_client_error(self):
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            data = json.loads(body)
            print(f"\n[CLIENT JS ERROR] {data.get('message')} (Line {data.get('line')}:{data.get('col')})")
            if data.get("stack"):
                print(f"Stack trace:\n{data['stack']}")
            self.send_json_response({"success": True}, 200)
        except Exception as e:
            self.send_json_response({"success": False, "error": str(e)}, 500)

    def do_POST(self):
        if self.path == "/api/client-error":
            self.handle_client_error()
        elif self.path == "/api/delete-asset":
            self.handle_delete_asset()
        elif self.path == "/api/delete-batch":
            self.handle_delete_batch()
        elif self.path == "/api/rename-asset":
            self.handle_rename_asset()
        elif self.path == "/api/move-asset":
            self.handle_move_asset()
        elif self.path == "/api/move-batch":
            self.handle_move_batch()
        elif self.path == "/api/assign-subfolder":
            self.handle_assign_subfolder()
        elif self.path == "/api/assign-subfolder-batch":
            self.handle_assign_subfolder_batch()
        elif self.path == "/api/add-category":
            self.handle_add_category()
        elif self.path == "/api/save-material-tag":
            self.handle_save_material_tag()
        elif self.path == "/api/schema/save":
            self.handle_save_schema()
        elif self.path == "/api/delete-material-tag":
            self.handle_delete_material_tag()
        elif self.path == "/api/edit-category-prefix":
            self.handle_edit_category_prefix()
        elif self.path == "/api/delete-category":
            self.handle_delete_category()
        elif self.path == "/api/delete-ghost-entries":
            self.handle_delete_ghost_entries()
        elif self.path == "/api/request-approval":
            self.handle_request_approval()
        elif self.path == "/api/approve-approval":
            self.handle_approve_approval()
        elif self.path == "/api/deny-approval":
            self.handle_deny_approval()
        elif self.path == "/api/add-subfolder":
            self.handle_add_subfolder()
        elif self.path == "/api/request-asset":
            self.handle_request_asset()
        elif self.path == "/api/request-asset-stages":
            self.handle_request_asset_stages()
        elif self.path == "/api/request-rigging":
            self.handle_request_rigging()
        elif self.path == "/api/request-rigging-batch":
            self.handle_request_rigging_batch()
        elif self.path == "/api/request-regenerate-model":
            self.handle_request_regenerate_model()
        elif self.path == "/api/request-regenerate-model-batch":
            self.handle_request_regenerate_model_batch()
        elif self.path == "/api/request-icon":
            self.handle_request_icon()
        elif self.path == "/api/open-item-folder":
            self.handle_open_item_folder()
        elif self.path == "/api/finalize-asset-requests":
            self.handle_finalize_asset_requests()
        elif self.path == "/api/update-asset-request":
            self.handle_update_asset_request()
        elif self.path == "/api/delete-asset-request":
            self.handle_delete_asset_request()
        elif self.path == "/api/delete-all-asset-requests":
            self.handle_delete_all_asset_requests()
        elif self.path == "/api/creative-claw-balance":
            self.handle_update_creative_claw_balance()
        elif self.path == "/api/invalidate-catalog-cache":
            self.handle_invalidate_catalog_cache()
        elif self.path == "/api/growth-groups":
            self.handle_save_growth_group()
        elif self.path == "/api/save-manifest":
            self.handle_save_manifest()
        elif self.path == "/api/regen-icons":
            self.handle_regen_icons()
        elif self.path == "/api/regen-icon":
            self.handle_regen_icon()
        else:
            self.send_error(404, "Unknown API endpoint")

    def handle_delete_asset(self):
        try:
            content_len = int(self.headers.get("Content-Length", 0))
            post_body = self.rfile.read(content_len)
            data = json.loads(post_body.decode("utf-8"))
            
            category = data.get("category", "").strip().lower()
            item_id = data.get("item_id", "").strip().lower()

            if not category or not item_id:
                self.send_json_response({"success": False, "error": "Missing category or item_id"}, 400)
                return

            if category not in ALLOWED_CATEGORIES:
                self.send_json_response({"success": False, "error": f"Invalid category: {category}"}, 400)
                return

            # Prevent directory traversal
            if ".." in item_id or "/" in item_id or "\\" in item_id:
                self.send_json_response({"success": False, "error": "Invalid item_id"}, 400)
                return

            target_dir = os.path.join(BASE_DIR, category, item_id)
            if not os.path.exists(target_dir) or not os.path.isdir(target_dir):
                self.send_json_response({"success": False, "error": f"Asset folder not found: {category}/{item_id}"}, 404)
                return

            print(f"[DELETE REQUEST] Permanently deleting: {target_dir}")
            shutil.rmtree(target_dir, ignore_errors=False)

            remove_items_from_embedded_catalog([{"category": category, "item_id": item_id}])

            # Trigger background or fast catalog README update
            try:
                update_script = os.path.join(BASE_DIR, "update_catalog_readme.py")
                if os.path.exists(update_script):
                    subprocess.Popen([sys.executable, update_script])
            except Exception as e:
                print(f"Warning updating README: {e}")

            self.send_json_response({
                "success": True,
                "message": f"Asset '{item_id}' in '{category}' was permanently deleted from disk.",
                "item_id": item_id,
                "category": category
            }, 200)

        except Exception as e:
            print(f"Error deleting asset: {e}")
            self.send_json_response({"success": False, "error": str(e)}, 500)

    def handle_delete_batch(self):
        try:
            content_len = int(self.headers.get("Content-Length", 0))
            post_body = self.rfile.read(content_len)
            data = json.loads(post_body.decode("utf-8"))

            items = data.get("items", [])
            if not items or not isinstance(items, list):
                self.send_json_response({"success": False, "error": "No items provided for batch deletion"}, 400)
                return

            deleted = []
            errors = []

            for it in items:
                cat = it.get("category", "").strip().lower()
                iid = it.get("id", it.get("item_id", "")).strip().lower()
                if not cat or not iid or cat not in ALLOWED_CATEGORIES:
                    errors.append(f"Invalid item: {cat}/{iid}")
                    continue

                if ".." in iid or "/" in iid or "\\" in iid:
                    errors.append(f"Invalid path traversal: {cat}/{iid}")
                    continue

                target_dir = os.path.join(BASE_DIR, cat, iid)
                if os.path.exists(target_dir) and os.path.isdir(target_dir):
                    try:
                        shutil.rmtree(target_dir, ignore_errors=False)
                        deleted.append({"category": cat, "item_id": iid})
                    except Exception as e:
                        errors.append(f"Failed to delete {cat}/{iid}: {str(e)}")
                else:
                    errors.append(f"Not found: {cat}/{iid}")

            print(f"[BATCH DELETE] Permanently deleted {len(deleted)} assets from disk. Errors: {len(errors)}")

            remove_items_from_embedded_catalog(deleted)

            # Update catalog README once in background
            try:
                update_script = os.path.join(BASE_DIR, "update_catalog_readme.py")
                if os.path.exists(update_script):
                    subprocess.Popen([sys.executable, update_script])
            except Exception as e:
                print(f"Warning updating README: {e}")

            self.send_json_response({
                "success": True,
                "message": f"Successfully deleted {len(deleted)} assets from disk.",
                "deleted_count": len(deleted),
                "deleted": deleted,
                "errors": errors
            }, 200)

        except Exception as e:
            print(f"Error in batch delete: {e}")
            self.send_json_response({"success": False, "error": str(e)}, 500)

    def handle_rename_asset(self):
        try:
            content_len = int(self.headers.get("Content-Length", 0))
            post_body = self.rfile.read(content_len)
            data = json.loads(post_body.decode("utf-8"))
            
            category = data.get("category", "").strip().lower()
            old_id = data.get("old_id", "").strip().lower()
            new_id = data.get("new_id", "").strip().lower()
            new_name = data.get("new_name", "").strip()

            if not category or not old_id or not new_id or not new_name:
                self.send_json_response({"success": False, "error": "Missing category, old_id, new_id, or new_name"}, 400)
                return

            if category not in ALLOWED_CATEGORIES:
                self.send_json_response({"success": False, "error": f"Invalid category: {category}"}, 400)
                return

            import re
            if not re.match(r"^[a-z0-9_\-]+$", new_id):
                self.send_json_response({"success": False, "error": "Item ID must contain only lowercase letters, numbers, underscores, and hyphens."}, 400)
                return

            # Prevent directory traversal
            if ".." in old_id or "/" in old_id or "\\" in old_id or ".." in new_id or "/" in new_id or "\\" in new_id:
                self.send_json_response({"success": False, "error": "Invalid characters in item_id"}, 400)
                return

            old_dir = os.path.join(BASE_DIR, category, old_id)
            if not os.path.exists(old_dir) or not os.path.isdir(old_dir):
                self.send_json_response({"success": False, "error": f"Asset folder not found: {category}/{old_id}"}, 404)
                return

            new_dir = os.path.join(BASE_DIR, category, new_id)
            if new_id != old_id and os.path.exists(new_dir):
                self.send_json_response({"success": False, "error": f"Target asset '{category}/{new_id}' already exists."}, 409)
                return

            print(f"[RENAME REQUEST] {category}/{old_id} -> {category}/{new_id} ('{new_name}')")

            # 1. Rename directory on disk if ID changed
            if new_id != old_id:
                os.rename(old_dir, new_dir)
                target_dir = new_dir
            else:
                target_dir = old_dir

            # 2. Rename files prefixed with old_id inside the folder
            renamed_files_map = {}
            if new_id != old_id:
                for fname in list(os.listdir(target_dir)):
                    if fname.startswith(f"{old_id}."):
                        ext = fname[len(old_id):]
                        new_fname = f"{new_id}{ext}"
                        old_fpath = os.path.join(target_dir, fname)
                        new_fpath = os.path.join(target_dir, new_fname)
                        if os.path.exists(new_fpath) and old_fpath != new_fpath:
                            os.remove(new_fpath)
                        os.rename(old_fpath, new_fpath)
                        renamed_files_map[fname] = new_fname

            # 3. Update manifest JSON
            manifest_file = os.path.join(target_dir, f"{new_id}.json")
            if not os.path.exists(manifest_file):
                manifest_file = os.path.join(target_dir, f"{old_id}.json")

            if os.path.exists(manifest_file):
                try:
                    with open(manifest_file, "r", encoding="utf-8") as f:
                        manifest = json.load(f)

                    manifest["id"] = new_id
                    manifest["name"] = new_name
                    manifest["icon"] = f"{new_id}.png"

                    # Update models list if any model file was renamed
                    if "models" in manifest and isinstance(manifest["models"], list):
                        for m in manifest["models"]:
                            if isinstance(m, dict):
                                m_file = m.get("file", "")
                                if m_file in renamed_files_map:
                                    m["file"] = renamed_files_map[m_file]

                    # Update stages if referencing old_id
                    if "growth" in manifest and isinstance(manifest["growth"], dict):
                        stages = manifest["growth"].get("stages", [])
                        for st in stages:
                            if isinstance(st, dict) and st.get("item_id") == old_id:
                                st["item_id"] = new_id
                        curr_st = manifest["growth"].get("current_stage")
                        if isinstance(curr_st, dict) and curr_st.get("item_id") == old_id:
                            curr_st["item_id"] = new_id

                    with open(manifest_file, "w", encoding="utf-8") as f:
                        json.dump(manifest, f, indent=2)
                except Exception as e:
                    print(f"Warning updating manifest JSON: {e}")

            rename_item_in_embedded_catalog(category, old_id, new_id, new_name)

            # 4. If OBJ references renamed MTL file, update mtllib line
            for old_fname, new_fname in renamed_files_map.items():
                if old_fname.endswith(".obj"):
                    obj_path = os.path.join(target_dir, new_fname)
                    try:
                        with open(obj_path, "r", encoding="utf-8", errors="ignore") as f:
                            obj_text = f.read()
                        if f"{old_id}.mtl" in obj_text:
                            obj_text = obj_text.replace(f"{old_id}.mtl", f"{new_id}.mtl")
                            with open(obj_path, "w", encoding="utf-8") as f:
                                f.write(obj_text)
                    except Exception as e:
                        print(f"Warning updating OBJ: {e}")

            # 5. Update README.md if present
            readme_path = os.path.join(target_dir, "README.md")
            if os.path.exists(readme_path):
                try:
                    with open(readme_path, "r", encoding="utf-8") as f:
                        readme_text = f.read()
                    readme_text = readme_text.replace(f"{old_id}.png", f"{new_id}.png")
                    readme_text = readme_text.replace(f"{old_id}.json", f"{new_id}.json")
                    readme_text = readme_text.replace(f"#{old_id}", f"#{new_id}")
                    readme_text = readme_text.replace(f"`{old_id}`", f"`{new_id}`")
                    with open(readme_path, "w", encoding="utf-8") as f:
                        f.write(readme_text)
                except Exception as e:
                    print(f"Warning updating README.md: {e}")

            # 6. Trigger catalog update in background
            try:
                update_script = os.path.join(BASE_DIR, "update_catalog_readme.py")
                if os.path.exists(update_script):
                    subprocess.Popen([sys.executable, update_script])
            except Exception as e:
                print(f"Warning running catalog update: {e}")

            self.send_json_response({
                "success": True,
                "message": f"Asset '{old_id}' was successfully renamed to '{new_name}' ({new_id}).",
                "category": category,
                "old_id": old_id,
                "new_id": new_id,
                "new_name": new_name,
                "icon": f"{category}/{new_id}/{new_id}.png"
            }, 200)

        except Exception as e:
            print(f"Error renaming asset: {e}")
            self.send_json_response({"success": False, "error": str(e)}, 500)

    def handle_move_asset(self):
        try:
            content_len = int(self.headers.get("Content-Length", 0))
            post_body = self.rfile.read(content_len)
            data = json.loads(post_body.decode("utf-8")) if content_len > 0 else {}

            category = data.get("category", "").strip().lower()
            item_id = data.get("item_id", "").strip().lower()
            target_category = data.get("target_category", "").strip().lower()

            if not category or not item_id or not target_category:
                self.send_json_response({"success": False, "error": "Missing category, item_id, or target_category"}, 400)
                return

            if category not in ALLOWED_CATEGORIES or target_category not in ALLOWED_CATEGORIES:
                self.send_json_response({"success": False, "error": f"Invalid category: {category} -> {target_category}"}, 400)
                return

            if category == target_category:
                self.send_json_response({"success": False, "error": f"Asset is already in category '{target_category}'"}, 400)
                return

            res = move_single_asset_on_disk(category, item_id, target_category)
            apply_moves_to_embedded_catalog([res])

            # Trigger background catalog README update
            try:
                update_script = os.path.join(BASE_DIR, "update_catalog_readme.py")
                if os.path.exists(update_script):
                    subprocess.Popen([sys.executable, update_script])
            except Exception as e:
                print(f"Warning running catalog update: {e}")

            self.send_json_response({
                "success": True,
                "message": f"Asset '{item_id}' moved to '{target_category}' as '{res['new_id']}'.",
                **res
            }, 200)

        except Exception as e:
            print(f"Error moving asset: {e}")
            self.send_json_response({"success": False, "error": str(e)}, 500)

    def handle_move_batch(self):
        try:
            content_len = int(self.headers.get("Content-Length", 0))
            post_body = self.rfile.read(content_len)
            data = json.loads(post_body.decode("utf-8")) if content_len > 0 else {}

            items = data.get("items", [])
            target_category = data.get("target_category", "").strip().lower()

            if not items or not isinstance(items, list) or not target_category:
                self.send_json_response({"success": False, "error": "Missing items or target_category"}, 400)
                return

            if target_category not in ALLOWED_CATEGORIES:
                self.send_json_response({"success": False, "error": f"Invalid target_category: {target_category}"}, 400)
                return

            moved = []
            errors = []

            for item in items:
                cat = item.get("category", "").strip().lower()
                iid = item.get("id") or item.get("item_id", "")
                iid = iid.strip().lower()

                if not cat or not iid or cat == target_category:
                    continue

                try:
                    res = move_single_asset_on_disk(cat, iid, target_category)
                    moved.append(res)
                except Exception as ex:
                    errors.append({"item_id": iid, "category": cat, "error": str(ex)})

            apply_moves_to_embedded_catalog(moved)

            try:
                update_script = os.path.join(BASE_DIR, "update_catalog_readme.py")
                if os.path.exists(update_script):
                    subprocess.Popen([sys.executable, update_script])
            except Exception as e:
                print(f"Warning running catalog update: {e}")

            self.send_json_response({
                "success": True,
                "message": f"Successfully moved {len(moved)} assets to '{target_category}'.",
                "moved_count": len(moved),
                "moved": moved,
                "errors": errors,
                "target_category": target_category
            }, 200)

        except Exception as e:
            print(f"Error in batch move: {e}")
            self.send_json_response({"success": False, "error": str(e)}, 500)

    def handle_assign_subfolder(self):
        try:
            content_len = int(self.headers.get("Content-Length", 0))
            post_body = self.rfile.read(content_len)
            data = json.loads(post_body.decode("utf-8")) if content_len > 0 else {}

            category = data.get("category", "").strip().lower()
            item_id = data.get("item_id", "").strip().lower()
            target_category = data.get("target_category", "").strip().lower()
            species = data.get("species", "").strip().lower()

            if not category or not item_id or not species:
                self.send_json_response({"success": False, "error": "Missing category, item_id, or species"}, 400)
                return

            if category not in ALLOWED_CATEGORIES or (target_category and target_category not in ALLOWED_CATEGORIES):
                self.send_json_response({"success": False, "error": f"Invalid category: {category} -> {target_category}"}, 400)
                return

            res = assign_item_to_subfolder(category, item_id, target_category, species)

            try:
                update_script = os.path.join(BASE_DIR, "update_catalog_readme.py")
                if os.path.exists(update_script):
                    subprocess.Popen([sys.executable, update_script])
            except Exception as e:
                print(f"Warning running catalog update: {e}")

            self.send_json_response({
                "success": True,
                "message": f"Asset '{item_id}' assigned to species '{species}'" + (f" and moved to '{target_category}'" if res["moved"] else "") + ".",
                **res
            }, 200)

        except Exception as e:
            print(f"Error assigning subfolder: {e}")
            self.send_json_response({"success": False, "error": str(e)}, 500)

    def handle_assign_subfolder_batch(self):
        try:
            content_len = int(self.headers.get("Content-Length", 0))
            post_body = self.rfile.read(content_len)
            data = json.loads(post_body.decode("utf-8")) if content_len > 0 else {}

            items = data.get("items", [])
            target_category = data.get("target_category", "").strip().lower()
            species = data.get("species", "").strip().lower()

            if not items or not isinstance(items, list) or not target_category or not species:
                self.send_json_response({"success": False, "error": "Missing items, target_category, or species"}, 400)
                return

            if target_category not in ALLOWED_CATEGORIES:
                self.send_json_response({"success": False, "error": f"Invalid target_category: {target_category}"}, 400)
                return

            assigned = []
            errors = []

            for item in items:
                cat = item.get("category", "").strip().lower()
                iid = item.get("id") or item.get("item_id", "")
                iid = iid.strip().lower()

                if not cat or not iid:
                    continue

                try:
                    res = assign_item_to_subfolder(cat, iid, target_category, species)
                    assigned.append(res)
                except Exception as ex:
                    errors.append({"item_id": iid, "category": cat, "error": str(ex)})

            try:
                update_script = os.path.join(BASE_DIR, "update_catalog_readme.py")
                if os.path.exists(update_script):
                    subprocess.Popen([sys.executable, update_script])
            except Exception as e:
                print(f"Warning running catalog update: {e}")

            self.send_json_response({
                "success": True,
                "message": f"Successfully assigned {len(assigned)} assets to the '{species}' subfolder.",
                "assigned_count": len(assigned),
                "assigned": assigned,
                "errors": errors,
                "target_category": target_category,
                "species": species
            }, 200)

        except Exception as e:
            print(f"Error in batch subfolder assign: {e}")
            self.send_json_response({"success": False, "error": str(e)}, 500)

    def handle_get_kit_config(self):
        try:
            cfg = load_kit_config()
            self.send_json_response({"success": True, **cfg}, 200)
        except Exception as e:
            print(f"Error loading kit config: {e}")
            self.send_json_response({"success": False, "error": str(e)}, 500)

    def handle_add_category(self):
        try:
            content_len = int(self.headers.get("Content-Length", 0))
            post_body = self.rfile.read(content_len)
            data = json.loads(post_body.decode("utf-8")) if content_len > 0 else {}

            key = data.get("key", "").strip().lower()
            name = data.get("name", "").strip()
            icon = data.get("icon", "").strip() or "📁"
            desc = data.get("desc", "").strip()
            prefix = data.get("prefix", "").strip().lower()

            if not key or not name or not prefix:
                self.send_json_response({"success": False, "error": "Missing key, name, or asset prefix"}, 400)
                return

            slug_re = r"^[a-z][a-z0-9_]*$"
            if not re.match(slug_re, key):
                self.send_json_response({"success": False, "error": "Category key must start with a letter and contain only lowercase letters, numbers, and underscores."}, 400)
                return
            if not re.match(slug_re, prefix):
                self.send_json_response({"success": False, "error": "Asset prefix must start with a letter and contain only lowercase letters, numbers, and underscores."}, 400)
                return

            cfg = load_kit_config()
            if key in ALLOWED_CATEGORIES or key in cfg["categories"]:
                self.send_json_response({"success": False, "error": f"Category '{key}' already exists."}, 409)
                return

            cat_dir = os.path.join(BASE_DIR, key)
            os.makedirs(cat_dir, exist_ok=True)

            cfg["categories"][key] = {"name": name, "icon": icon, "desc": desc, "prefix": prefix}
            save_kit_config(cfg)
            ALLOWED_CATEGORIES.add(key)

            print(f"[ADD CATEGORY] {key} (prefix='{prefix}_') -> {cat_dir}")

            self.send_json_response({
                "success": True,
                "message": f"Category '{name}' created with asset prefix '{prefix}_'.",
                "key": key,
                "category": cfg["categories"][key]
            }, 200)

        except Exception as e:
            print(f"Error adding category: {e}")
            self.send_json_response({"success": False, "error": str(e)}, 500)

    def handle_get_material_tags(self):
        self.send_json_response({"success": True, **load_material_tags()}, 200)

    def handle_get_schemas(self):
        """Lists category and base schema files in assets/_schemas/ with detail."""
        try:
            query = urllib.parse.urlparse(self.path).query
            params = urllib.parse.parse_qs(query)
            include_all = params.get("all", ["0"])[0] in ("1", "true")
            schemas_dir = os.path.join(BASE_DIR, "_schemas")
            names = []
            details = []
            if os.path.isdir(schemas_dir):
                for fname in os.listdir(schemas_dir):
                    if not fname.endswith(".schema.json"):
                        continue
                    name = fname[:-len(".schema.json")]
                    if name.startswith("_") and not include_all:
                        continue
                    names.append(name)
                    try:
                        fpath = os.path.join(schemas_dir, fname)
                        with open(fpath, "r", encoding="utf-8") as sf:
                            sdata = json.load(sf)
                        details.append({
                            "name": name,
                            "category": sdata.get("category", name),
                            "target": sdata.get("target", "category_fields"),
                            "field_count": len(sdata.get("fields", {})),
                            "note": sdata.get("note", "")
                        })
                    except Exception:
                        details.append({"name": name, "category": name, "target": "category_fields", "field_count": 0, "note": ""})
            names.sort()
            details.sort(key=lambda x: (0 if x["name"].startswith("_") else 1, x["name"]))
            self.send_json_response({"success": True, "schemas": names, "details": details}, 200)
        except Exception as e:
            self.send_json_response({"success": False, "error": str(e)}, 500)

    def handle_get_schema(self):
        """Fetches the full JSON payload for one schema by name."""
        try:
            query = urllib.parse.urlparse(self.path).query
            params = urllib.parse.parse_qs(query)
            name = (params.get("name", [""])[0]).strip().lower()
            if not name:
                self.send_json_response({"success": False, "error": "Missing schema name"}, 400)
                return
            safe_name = os.path.basename(name)
            fpath = os.path.join(BASE_DIR, "_schemas", f"{safe_name}.schema.json")
            if not os.path.exists(fpath):
                self.send_json_response({"success": False, "error": f"Schema not found: {safe_name}"}, 404)
                return
            with open(fpath, "r", encoding="utf-8") as f:
                schema_data = json.load(f)
            self.send_json_response({"success": True, "name": safe_name, "schema": schema_data}, 200)
        except Exception as e:
            self.send_json_response({"success": False, "error": str(e)}, 500)

    def handle_save_schema(self):
        """Saves/updates a schema file in assets/_schemas/<name>.schema.json."""
        try:
            content_len = int(self.headers.get("Content-Length", 0))
            post_body = self.rfile.read(content_len)
            data = json.loads(post_body.decode("utf-8")) if content_len > 0 else {}

            name = (data.get("name") or "").strip().lower()
            schema_data = data.get("schema")

            if not name or not isinstance(schema_data, dict):
                self.send_json_response({"success": False, "error": "Missing schema name or schema body"}, 400)
                return

            safe_name = "".join(c for c in name if c.isalnum() or c in ("_", "-"))
            if not safe_name:
                self.send_json_response({"success": False, "error": "Invalid schema name"}, 400)
                return

            if "fields" not in schema_data or not isinstance(schema_data["fields"], dict):
                self.send_json_response({"success": False, "error": "Schema must contain a 'fields' object"}, 400)
                return

            schemas_dir = os.path.join(BASE_DIR, "_schemas")
            os.makedirs(schemas_dir, exist_ok=True)
            fpath = os.path.join(schemas_dir, f"{safe_name}.schema.json")

            with open(fpath, "w", encoding="utf-8") as f:
                json.dump(schema_data, f, indent=2, ensure_ascii=False)
                f.write("\n")

            self.send_json_response({"success": True, "name": safe_name}, 200)
        except Exception as e:
            self.send_json_response({"success": False, "error": str(e)}, 500)

    def handle_validate_schema(self):
        """Runs compliance checks on all item manifests in a category against schemas."""
        try:
            query = urllib.parse.urlparse(self.path).query
            params = urllib.parse.parse_qs(query)
            category = (params.get("category", [""])[0]).strip().lower()
            if not category:
                self.send_json_response({"success": False, "error": "Missing category"}, 400)
                return

            schemas_dir = os.path.join(BASE_DIR, "_schemas")
            schemas = []
            if os.path.isdir(schemas_dir):
                for base_name in sorted(os.listdir(schemas_dir)):
                    if base_name.startswith("_base") and base_name.endswith(".schema.json"):
                        try:
                            with open(os.path.join(schemas_dir, base_name), "r", encoding="utf-8") as bf:
                                schemas.append(json.load(bf))
                        except Exception:
                            pass
                cat_file = os.path.join(schemas_dir, f"{category}.schema.json")
                if os.path.exists(cat_file):
                    try:
                        with open(cat_file, "r", encoding="utf-8") as cf:
                            schemas.append(json.load(cf))
                    except Exception:
                        pass

            cat_dir = os.path.join(BASE_DIR, category)
            if not os.path.isdir(cat_dir):
                self.send_json_response({
                    "success": True,
                    "category": category,
                    "total_items": 0,
                    "passed_count": 0,
                    "failed_count": 0,
                    "failed_items": []
                }, 200)
                return

            py_types = {"object": dict, "string": str, "number": (int, float), "boolean": bool, "array": list}

            def check_val(val, spec, path_str):
                errs = []
                exp = spec.get("type") if isinstance(spec, dict) else spec
                py_t = py_types.get(exp)
                if py_t is None:
                    return errs
                if not isinstance(val, py_t) or (isinstance(val, bool) and py_t is not bool):
                    errs.append(f"{path_str}: expected {exp}, got {type(val).__name__}")
                    return errs
                if exp == "number" and isinstance(spec, dict):
                    if "min" in spec and val < spec["min"]:
                        errs.append(f"{path_str}: {val} < min {spec['min']}")
                    if "max" in spec and val > spec["max"]:
                        errs.append(f"{path_str}: {val} > max {spec['max']}")
                if exp == "object" and isinstance(spec, dict) and "properties" in spec:
                    for p_name, p_type in spec["properties"].items():
                        if p_name not in val:
                            errs.append(f"{path_str}.{p_name}: missing")
                        else:
                            errs.extend(check_val(val[p_name], p_type, f"{path_str}.{p_name}"))
                return errs

            def val_item(manifest, schema):
                errs = []
                tgt_key = schema.get("target", "category_fields")
                tgt = manifest.get(tgt_key, {})
                for f_name, f_spec in schema.get("fields", {}).items():
                    if f_name not in tgt:
                        if f_spec.get("required"):
                            errs.append(f"{tgt_key}.{f_name}: missing (required)")
                        continue
                    errs.extend(check_val(tgt[f_name], f_spec, f"{tgt_key}.{f_name}"))
                return errs

            total_items = 0
            passed_items = 0
            failed_items = []

            for item_id in sorted(os.listdir(cat_dir)):
                item_folder = os.path.join(cat_dir, item_id)
                if not os.path.isdir(item_folder):
                    continue
                m_file = os.path.join(item_folder, f"{item_id}.json")
                if not os.path.isfile(m_file):
                    m_file = os.path.join(item_folder, "manifest.json")
                if not os.path.isfile(m_file):
                    continue

                total_items += 1
                try:
                    with open(m_file, "r", encoding="utf-8") as mf:
                        manifest = json.load(mf)
                except Exception as ex:
                    failed_items.append({"id": item_id, "name": item_id, "errors": [f"Invalid JSON: {ex}"]})
                    continue

                item_errs = []
                for s in schemas:
                    item_errs.extend(val_item(manifest, s))

                if item_errs:
                    failed_items.append({
                        "id": item_id,
                        "name": manifest.get("name", item_id),
                        "errors": item_errs
                    })
                else:
                    passed_items += 1

            self.send_json_response({
                "success": True,
                "category": category,
                "total_items": total_items,
                "passed_count": passed_items,
                "failed_count": len(failed_items),
                "failed_items": failed_items
            }, 200)
        except Exception as e:
            self.send_json_response({"success": False, "error": str(e)}, 500)

    def handle_save_material_tag(self):
        """Create or update (full replace) one tag - {tag_name, members: [item_ids]}.
        Every member must be a real, existing catalog item; a tag can't
        reference another tag (no nested tags, keeps resolution a single
        flat lookup)."""
        try:
            content_len = int(self.headers.get("Content-Length", 0))
            post_body = self.rfile.read(content_len)
            data = json.loads(post_body.decode("utf-8")) if content_len > 0 else {}

            tag_name = data.get("tag_name", "").strip().lower()
            members = data.get("members", [])

            if not tag_name:
                self.send_json_response({"success": False, "error": "Missing tag_name"}, 400)
                return
            if not re.match(r"^[a-z][a-z0-9_]*$", tag_name):
                self.send_json_response({"success": False, "error": "Tag name must start with a letter and contain only lowercase letters, numbers, and underscores."}, 400)
                return
            if not isinstance(members, list) or not members:
                self.send_json_response({"success": False, "error": "members must be a non-empty list of item ids"}, 400)
                return

            real_ids = {item["id"] for item in get_cached_catalog()}
            bad = [m for m in members if not isinstance(m, str) or m.startswith("#") or m not in real_ids]
            if bad:
                self.send_json_response({"success": False, "error": f"Not real catalog items: {', '.join(bad)}"}, 400)
                return

            data_store = load_material_tags()
            is_new = tag_name not in data_store["tags"]
            data_store["tags"][tag_name] = members
            save_material_tags(data_store)

            print(f"[{'ADD' if is_new else 'UPDATE'} TAG] #{tag_name} -> {members}")
            self.send_json_response({
                "success": True,
                "message": f"Tag '#{tag_name}' saved with {len(members)} member(s).",
                "tag_name": tag_name,
                "members": members
            }, 200)

        except Exception as e:
            print(f"Error saving material tag: {e}")
            self.send_json_response({"success": False, "error": str(e)}, 500)

    def handle_delete_material_tag(self):
        try:
            content_len = int(self.headers.get("Content-Length", 0))
            post_body = self.rfile.read(content_len)
            data = json.loads(post_body.decode("utf-8")) if content_len > 0 else {}

            tag_name = data.get("tag_name", "").strip().lower()
            data_store = load_material_tags()
            if tag_name not in data_store["tags"]:
                self.send_json_response({"success": False, "error": f"Tag '#{tag_name}' does not exist."}, 404)
                return

            del data_store["tags"][tag_name]
            save_material_tags(data_store)

            print(f"[DELETE TAG] #{tag_name}")
            self.send_json_response({"success": True, "message": f"Tag '#{tag_name}' deleted."}, 200)

        except Exception as e:
            print(f"Error deleting material tag: {e}")
            self.send_json_response({"success": False, "error": str(e)}, 500)

    def handle_edit_category_prefix(self):
        """Full edit for a custom (non-built-in) category: name, icon, desc,
        and/or asset prefix - any subset of fields present in the body is
        updated, the rest left alone. Built-in categories use per-content-
        type conditional prefixing (see compute_target_id_for_category) that
        a single prefix string can't represent, so this refuses to touch
        them regardless of which fields are being edited."""
        try:
            content_len = int(self.headers.get("Content-Length", 0))
            post_body = self.rfile.read(content_len)
            data = json.loads(post_body.decode("utf-8")) if content_len > 0 else {}

            key = data.get("key", "").strip().lower()
            if not key:
                self.send_json_response({"success": False, "error": "Missing key"}, 400)
                return

            cfg = load_kit_config()
            if key not in cfg["categories"]:
                self.send_json_response({"success": False, "error": f"'{key}' isn't a custom category (built-in categories use content-based prefixing, not a single editable prefix)."}, 400)
                return

            cat = cfg["categories"][key]

            if "prefix" in data:
                prefix = data["prefix"].strip().lower()
                if not prefix or not re.match(r"^[a-z][a-z0-9_]*$", prefix):
                    self.send_json_response({"success": False, "error": "Asset prefix must start with a letter and contain only lowercase letters, numbers, and underscores."}, 400)
                    return
                cat["prefix"] = prefix
            if "name" in data:
                name = data["name"].strip()
                if not name:
                    self.send_json_response({"success": False, "error": "Name cannot be empty."}, 400)
                    return
                cat["name"] = name
            if "icon" in data:
                cat["icon"] = data["icon"].strip() or "📁"
            if "desc" in data:
                cat["desc"] = data["desc"].strip()

            save_kit_config(cfg)

            print(f"[EDIT CATEGORY] {key} -> {cat}")

            self.send_json_response({
                "success": True,
                "message": f"Category '{key}' updated.",
                "key": key,
                "category": cat
            }, 200)

        except Exception as e:
            print(f"Error editing category: {e}")
            self.send_json_response({"success": False, "error": str(e)}, 500)

    def handle_delete_category(self):
        """Deletes a custom category, but only if it's genuinely empty - no
        item folders on disk under it AND no leftover embedded-catalog
        entries referencing it (the latter would itself be exactly the kind
        of ghost entry the new status-bar notification exists to catch, so
        this refuses to create one). Built-in categories can never be
        deleted."""
        try:
            content_len = int(self.headers.get("Content-Length", 0))
            post_body = self.rfile.read(content_len)
            data = json.loads(post_body.decode("utf-8")) if content_len > 0 else {}

            key = data.get("key", "").strip().lower()
            if not key:
                self.send_json_response({"success": False, "error": "Missing key"}, 400)
                return

            cfg = load_kit_config()
            if key not in cfg["categories"]:
                self.send_json_response({"success": False, "error": f"'{key}' isn't a custom category and can't be deleted."}, 400)
                return

            cat_dir = os.path.join(BASE_DIR, key)
            disk_items = []
            if os.path.isdir(cat_dir):
                for item_id in os.listdir(cat_dir):
                    item_dir = os.path.join(cat_dir, item_id)
                    if os.path.isdir(item_dir) and os.path.isfile(os.path.join(item_dir, f"{item_id}.json")):
                        disk_items.append(item_id)

            catalog_items = [it.get("id") for it in read_embedded_catalog() if it.get("category") == key]

            if disk_items or catalog_items:
                total = len(set(disk_items) | set(catalog_items))
                self.send_json_response({
                    "success": False,
                    "error": f"Category '{key}' isn't empty ({total} asset(s) still reference it) - move or delete them first."
                }, 409)
                return

            del cfg["categories"][key]
            cfg["subfolders"] = {k: v for k, v in cfg["subfolders"].items() if v.get("category") != key}
            cfg["growth_groups"] = {k: v for k, v in cfg["growth_groups"].items() if v.get("category") != key}
            save_kit_config(cfg)
            ALLOWED_CATEGORIES.discard(key)

            if os.path.isdir(cat_dir):
                try:
                    os.rmdir(cat_dir)  # only succeeds if truly empty - never force-removes stray files
                except OSError:
                    pass

            print(f"[DELETE CATEGORY] {key}")

            self.send_json_response({"success": True, "message": f"Category '{key}' deleted.", "key": key}, 200)

        except Exception as e:
            print(f"Error deleting category: {e}")
            self.send_json_response({"success": False, "error": str(e)}, 500)

    def handle_delete_ghost_entries(self):
        """Removes the given (category, id) entries from the embedded
        catalog. Meant only for entries a ghost-entry scan already confirmed
        have no folder on disk - this doesn't re-check that itself, so it
        will happily remove a real entry if told to; the frontend only ever
        calls this with ids it got back from /api/ghost-entries."""
        try:
            content_len = int(self.headers.get("Content-Length", 0))
            post_body = self.rfile.read(content_len)
            data = json.loads(post_body.decode("utf-8")) if content_len > 0 else {}

            items = data.get("items", [])
            if not isinstance(items, list) or not items:
                self.send_json_response({"success": False, "error": "No items provided"}, 400)
                return

            to_remove = [{"category": it.get("category"), "item_id": it.get("id")} for it in items if it.get("category") and it.get("id")]
            remove_items_from_embedded_catalog(to_remove)

            print(f"[GHOST CLEANUP] Removed {len(to_remove)} ghost entr{'y' if len(to_remove) == 1 else 'ies'} from the catalog")
            self.send_json_response({"success": True, "removed_count": len(to_remove)}, 200)

        except Exception as e:
            print(f"Error deleting ghost entries: {e}")
            self.send_json_response({"success": False, "error": str(e)}, 500)

    def handle_request_approval(self):
        """Lets a Claude session post a spend-approval request (title, a
        plan description, and a structured cost breakdown) for the user to
        approve/deny from inside the asset kit UI, instead of only ever
        asking in the chat transcript. The session is expected to poll
        /api/approval-status for the id this returns until it's no longer
        'pending', rather than assuming approval - posting the request is
        not itself approval to spend anything."""
        try:
            content_len = int(self.headers.get("Content-Length", 0))
            post_body = self.rfile.read(content_len)
            data = json.loads(post_body.decode("utf-8")) if content_len > 0 else {}

            title = (data.get("title") or "").strip()
            plan = data.get("plan") or []
            cost = data.get("cost") or {}

            if not title:
                self.send_json_response({"success": False, "error": "Missing title"}, 400)
                return
            if not isinstance(plan, list):
                self.send_json_response({"success": False, "error": "plan must be a list of step strings"}, 400)
                return

            os.makedirs(APPROVALS_DIR, exist_ok=True)
            approval_id = f"{int(time.time())}_{re.sub(r'[^a-z0-9]+', '_', title.lower()).strip('_') or 'approval'}"
            record = {
                "id": approval_id,
                "title": title,
                "plan": plan,
                "cost": cost,
                "status": "pending",
                "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            }
            with open(os.path.join(APPROVALS_DIR, f"{approval_id}.json"), "w", encoding="utf-8") as f:
                json.dump(record, f, indent=2)

            print(f"[APPROVAL REQUESTED] {approval_id} -> {title}")
            self.send_json_response({"success": True, "approval": record}, 200)

        except Exception as e:
            print(f"Error requesting approval: {e}")
            self.send_json_response({"success": False, "error": str(e)}, 500)

    def handle_list_pending_approvals(self):
        try:
            approvals = []
            if os.path.isdir(APPROVALS_DIR):
                for fname in os.listdir(APPROVALS_DIR):
                    if not fname.endswith(".json"):
                        continue
                    try:
                        with open(os.path.join(APPROVALS_DIR, fname), "r", encoding="utf-8") as f:
                            record = json.load(f)
                        if record.get("status") == "pending":
                            approvals.append(record)
                    except Exception:
                        continue
            approvals.sort(key=lambda a: a.get("created_at", ""))
            self.send_json_response({"success": True, "approvals": approvals}, 200)
        except Exception as e:
            print(f"Error listing pending approvals: {e}")
            self.send_json_response({"success": False, "error": str(e)}, 500)

    def handle_get_approval_status(self):
        try:
            query = urllib.parse.urlparse(self.path).query
            params = urllib.parse.parse_qs(query)
            approval_id = (params.get("id", [""])[0]).strip()
            if not approval_id:
                self.send_json_response({"success": False, "error": "Missing id"}, 400)
                return
            path = os.path.join(APPROVALS_DIR, f"{approval_id}.json")
            if not os.path.isfile(path):
                self.send_json_response({"success": False, "error": f"No approval found with id '{approval_id}'"}, 404)
                return
            with open(path, "r", encoding="utf-8") as f:
                record = json.load(f)
            self.send_json_response({"success": True, "approval": record}, 200)
        except Exception as e:
            print(f"Error getting approval status: {e}")
            self.send_json_response({"success": False, "error": str(e)}, 500)

    def _resolve_approval(self, new_status):
        content_len = int(self.headers.get("Content-Length", 0))
        post_body = self.rfile.read(content_len)
        data = json.loads(post_body.decode("utf-8")) if content_len > 0 else {}

        approval_id = (data.get("id") or "").strip()
        if not approval_id:
            self.send_json_response({"success": False, "error": "Missing id"}, 400)
            return
        path = os.path.join(APPROVALS_DIR, f"{approval_id}.json")
        if not os.path.isfile(path):
            self.send_json_response({"success": False, "error": f"No approval found with id '{approval_id}'"}, 404)
            return

        with open(path, "r", encoding="utf-8") as f:
            record = json.load(f)
        record["status"] = new_status
        record["resolved_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        # Only meaningful on an "approved" resolution: "icon_only" tells the
        # processing session to skip 3D model generation entirely for this
        # plan (icons still get made) - not every requested item ends up
        # needing a model. Defaults to "full" (the original behavior) when
        # not specified, so older/unaware callers are unaffected.
        mode = (data.get("mode") or "").strip().lower()
        if new_status == "approved" and mode:
            record["approved_mode"] = mode
        with open(path, "w", encoding="utf-8") as f:
            json.dump(record, f, indent=2)

        print(f"[APPROVAL {new_status.upper()}] {approval_id}")
        self.send_json_response({"success": True, "approval": record}, 200)

    def handle_approve_approval(self):
        try:
            self._resolve_approval("approved")
        except Exception as e:
            print(f"Error approving: {e}")
            self.send_json_response({"success": False, "error": str(e)}, 500)

    def handle_deny_approval(self):
        try:
            self._resolve_approval("denied")
        except Exception as e:
            print(f"Error denying: {e}")
            self.send_json_response({"success": False, "error": str(e)}, 500)

    def handle_add_subfolder(self):
        try:
            content_len = int(self.headers.get("Content-Length", 0))
            post_body = self.rfile.read(content_len)
            data = json.loads(post_body.decode("utf-8")) if content_len > 0 else {}

            key = data.get("key", "").strip().lower()
            name = data.get("name", "").strip()
            icon = data.get("icon", "").strip() or "🌱"
            category = data.get("category", "").strip().lower()

            if not key or not name or not category:
                self.send_json_response({"success": False, "error": "Missing key, name, or category"}, 400)
                return

            if not re.match(r"^[a-z][a-z0-9_]*$", key):
                self.send_json_response({"success": False, "error": "Subfolder key must start with a letter and contain only lowercase letters, numbers, and underscores."}, 400)
                return

            if category not in ALLOWED_CATEGORIES:
                self.send_json_response({"success": False, "error": f"Invalid category: {category}"}, 400)
                return

            cfg = load_kit_config()
            if key in cfg["subfolders"]:
                self.send_json_response({"success": False, "error": f"Subfolder '{key}' already exists."}, 409)
                return

            cfg["subfolders"][key] = {"name": name, "icon": icon, "category": category}
            save_kit_config(cfg)

            print(f"[ADD SUBFOLDER] {key} -> category '{category}'")

            self.send_json_response({
                "success": True,
                "message": f"Subfolder '{name}' added under '{category}'.",
                "key": key,
                "subfolder": cfg["subfolders"][key]
            }, 200)

        except Exception as e:
            print(f"Error adding subfolder: {e}")
            self.send_json_response({"success": False, "error": str(e)}, 500)

    def handle_request_asset(self):
        """Queues a request for a new asset (name/category/description) that
        a Claude session picks up separately - see watch_asset_requests.py.
        This never generates anything itself and never spends credits; it
        just writes a pending request file for a human-in-the-loop session
        to notice, cost out, and (with approval) act on."""
        try:
            content_len = int(self.headers.get("Content-Length", 0))
            post_body = self.rfile.read(content_len)
            data = json.loads(post_body.decode("utf-8")) if content_len > 0 else {}

            name = data.get("name", "").strip()
            category = data.get("category", "").strip().lower()
            description = data.get("description", "").strip()
            notes = data.get("notes", "").strip()

            if not name or not category or not description:
                self.send_json_response({"success": False, "error": "Missing name, category, or description"}, 400)
                return

            if category not in ALLOWED_CATEGORIES:
                self.send_json_response({"success": False, "error": f"Invalid category: {category}"}, 400)
                return

            os.makedirs(ASSET_REQUESTS_PENDING, exist_ok=True)

            slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_") or "asset"
            request_id = f"{int(time.time())}_{slug}"
            request_path = os.path.join(ASSET_REQUESTS_PENDING, f"{request_id}.json")

            request_data = {
                "id": request_id,
                "name": name,
                "category": category,
                "schema": (data.get("schema") or "").strip().lower(),
                "pipeline": (data.get("pipeline") or "free").strip().lower(),
                "description": description,
                "notes": notes,
                "status": "pending",
                "requested_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "also_rig": bool(data.get("also_rig")),
                "rig_type": (data.get("rig_type") or "human").strip().lower()
            }
            if data.get("no_model"):
                request_data["no_model"] = True
            extra_animations = data.get("extra_animations")
            if extra_animations:
                request_data["extra_animations"] = [a.strip() for a in extra_animations if a and a.strip()]
            ref = resolve_reference_asset(data.get("reference_category"), data.get("reference_item_id"))
            if ref:
                request_data["reference_category"] = ref[0]
                request_data["reference_item_id"] = ref[1]

            with open(request_path, "w", encoding="utf-8") as f:
                json.dump(request_data, f, indent=2)

            print(f"[ASSET REQUEST] {request_id} -> {name} ({category}){' + rigging' if request_data['also_rig'] else ''}")

            self.send_json_response({
                "success": True,
                "message": f"Requested '{name}' — a Claude session watching the queue will pick it up.",
                "request": request_data
            }, 200)

        except Exception as e:
            print(f"Error requesting asset: {e}")
            self.send_json_response({"success": False, "error": str(e)}, 500)

    def handle_request_asset_stages(self):
        """Like handle_request_asset, but for a set of linked stage requests
        submitted together (e.g. 'Corn' with 4 growth stages) instead of one
        asset. Creates one pending request per stage, all sharing a
        request_group_id and a common base_name/category, so they naturally
        batch together on the next Finalize and a Claude session can wire
        them into a growth group once generated. Still never generates
        anything or spends credits itself."""
        try:
            content_len = int(self.headers.get("Content-Length", 0))
            post_body = self.rfile.read(content_len)
            data = json.loads(post_body.decode("utf-8")) if content_len > 0 else {}

            base_name = data.get("base_name", "").strip()
            category = data.get("category", "").strip().lower()
            base_description = data.get("description", "").strip()
            notes = data.get("notes", "").strip()
            stages_in = data.get("stages", [])

            # Optional group-level metadata (icon/growth_type/max_age/
            # time_unit) - when the request came from the dedicated Request
            # Growth Group dialog rather than the generic multi-stage
            # toggle, these override maybe_autocreate_growth_group's crude
            # auto-inferred defaults once every stage finishes.
            group_icon = (data.get("icon") or "").strip() or None
            group_growth_type = (data.get("growth_type") or "").strip() or None
            group_max_age = data.get("max_age")
            if not isinstance(group_max_age, (int, float)) or group_max_age <= 0:
                group_max_age = None
            group_time_unit = (data.get("time_unit") or "").strip() or None

            if not base_name or not category or not base_description:
                self.send_json_response({"success": False, "error": "Missing base_name, category, or description"}, 400)
                return
            if category not in ALLOWED_CATEGORIES:
                self.send_json_response({"success": False, "error": f"Invalid category: {category}"}, 400)
                return
            if not isinstance(stages_in, list) or not (2 <= len(stages_in) <= 10):
                self.send_json_response({"success": False, "error": "A stage set needs 2 to 10 stages."}, 400)
                return

            resolved_stages = []
            for i, st in enumerate(stages_in, start=1):
                st_name = (st.get("name") or "").strip()
                if not st_name:
                    self.send_json_response({"success": False, "error": f"Stage {i} is missing a name."}, 400)
                    return
                st_desc = (st.get("description") or "").strip() or f"{base_description} ({st_name} growth stage)"
                stage_entry = {"name": st_name, "description": st_desc}
                # Per-stage reference (e.g. a real baby-goat photo for the
                # "Baby" stage vs an adult-goat photo for "Adult") - falls
                # back to the shared top-level reference_category/
                # reference_item_id below when a stage doesn't specify its
                # own, so the old single-reference behavior still works.
                st_ref = resolve_reference_asset(st.get("reference_category"), st.get("reference_item_id"))
                if st_ref:
                    stage_entry["reference_category"], stage_entry["reference_item_id"] = st_ref
                for age_key in ("age_min", "age_max"):
                    val = st.get(age_key)
                    if isinstance(val, (int, float)) and val >= 0:
                        stage_entry[age_key] = val
                resolved_stages.append(stage_entry)

            os.makedirs(ASSET_REQUESTS_PENDING, exist_ok=True)

            base_slug = re.sub(r"[^a-z0-9]+", "_", base_name.lower()).strip("_") or "asset"
            request_group_id = f"group_{int(time.time())}_{base_slug}"
            requested_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            created = []

            for i, st in enumerate(resolved_stages, start=1):
                stage_slug = re.sub(r"[^a-z0-9]+", "_", st["name"].lower()).strip("_") or f"stage{i}"
                request_id = f"{int(time.time())}_{i}_{base_slug}_{stage_slug}"
                request_path = os.path.join(ASSET_REQUESTS_PENDING, f"{request_id}.json")

                request_data = {
                    "id": request_id,
                    "name": f"{base_name} - {st['name']}",
                    "category": category,
                    "schema": (data.get("schema") or "").strip().lower(),
                    "pipeline": (data.get("pipeline") or "free").strip().lower(),
                    "description": st["description"],
                    "notes": notes,
                    "status": "pending",
                    "requested_at": requested_at,
                    "request_group_id": request_group_id,
                    "base_name": base_name,
                    "stage_number": i,
                    "total_stages": len(resolved_stages),
                    "stage_name": st["name"],
                    "create_models": bool(data.get("create_models", True)),
                    "no_model": not bool(data.get("create_models", True)) or bool(data.get("no_model")),
                    "also_rig": bool(data.get("also_rig")),
                    "rig_type": (data.get("rig_type") or "human").strip().lower()
                }
                if group_icon:
                    request_data["group_icon"] = group_icon
                if group_growth_type:
                    request_data["group_growth_type"] = group_growth_type
                if group_max_age:
                    request_data["group_max_age"] = group_max_age
                if group_time_unit:
                    request_data["group_time_unit"] = group_time_unit
                if "age_min" in st:
                    request_data["age_min"] = st["age_min"]
                if "age_max" in st:
                    request_data["age_max"] = st["age_max"]
                extra_animations = data.get("extra_animations")
                if extra_animations:
                    request_data["extra_animations"] = [a.strip() for a in extra_animations if a and a.strip()]
                # This stage's own reference wins; otherwise fall back to a
                # shared top-level reference_category/reference_item_id
                # (the old single-reference behavior from the generic
                # multi-stage toggle on Request New Asset).
                if "reference_category" in st:
                    request_data["reference_category"] = st["reference_category"]
                    request_data["reference_item_id"] = st["reference_item_id"]
                else:
                    ref = resolve_reference_asset(data.get("reference_category"), data.get("reference_item_id"))
                    if ref:
                        request_data["reference_category"] = ref[0]
                        request_data["reference_item_id"] = ref[1]

                with open(request_path, "w", encoding="utf-8") as f:
                    json.dump(request_data, f, indent=2)
                created.append(request_data)

            print(f"[ASSET REQUEST SET] {request_group_id} -> {base_name} ({category}), {len(created)} stage(s)")

            self.send_json_response({
                "success": True,
                "message": f"Requested '{base_name}' as {len(created)} linked stages — a Claude session watching the queue will pick them up.",
                "request_group_id": request_group_id,
                "requests": created
            }, 200)

        except Exception as e:
            print(f"Error requesting asset stage set: {e}")
            self.send_json_response({"success": False, "error": str(e)}, 500)

    def _queue_asset_action_request(self, action, category, item_id, rig_type=None, reference=None, extra_animations=None, prompt=None):
        """Shared by rigging, regenerate-model, and regenerate-icon requests:
        all act on an EXISTING asset (unlike handle_request_asset/_stages,
        which create a new one), so they only need category+item_id, not a
        description - there's nothing to generate a prompt for by default,
        the item already exists. rig_type (human/bipedal_animal/quadruped/
        vehicle/other) is only meaningful for action='rig' - the rigging
        step (Blender's Mixamo add-on for humanoids, a standard quadruped
        skeleton otherwise) has no distinct mode per type, but this lets the
        processing Claude session set a sensible height and flag a likely-
        poor fit (quadruped/vehicle) before rigging it blindly. reference
        (category, item_id) tuple is only
        meaningful for action='regenerate_icon' - an optional "match style
        to this existing asset" pick, same convention as a new-asset
        request's Reference Asset field. prompt is also only meaningful for
        action='regenerate_icon' - free-text instructions for what should
        change (e.g. "make it darker, add rust") folded into the request's
        description so the processing session actually sees it, instead of
        just re-describing the existing asset with no direction. Returns
        the created request_data dict, or raises ValueError with a
        user-facing message on bad input."""
        if not category or not item_id:
            raise ValueError("Missing category or item_id")
        if category not in ALLOWED_CATEGORIES:
            raise ValueError(f"Invalid category: {category}")
        if not os.path.isdir(os.path.join(BASE_DIR, category, item_id)):
            raise ValueError(f"Asset not found: {category}/{item_id}")

        os.makedirs(ASSET_REQUESTS_PENDING, exist_ok=True)
        request_id = f"{int(time.time())}_{action}_{item_id}"
        request_path = os.path.join(ASSET_REQUESTS_PENDING, f"{request_id}.json")

        label = {"rig": "Rigging", "regenerate_model": "Regenerate Model", "regenerate_icon": "Regenerate Icon"}.get(action, action)
        prompt = (prompt or "").strip()
        if prompt:
            description = f"{label} request for existing asset {category}/{item_id} - user instructions: {prompt}"
        else:
            description = f"{label} request for existing asset {category}/{item_id} - no new generation prompt needed, act directly on the existing model."
        request_data = {
            "id": request_id,
            "name": f"{label}: {item_id}",
            "category": category,
            "description": description,
            "notes": "",
            "status": "pending",
            "requested_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "action": action,
            "target_category": category,
            "target_item_id": item_id
        }
        if action == "rig":
            request_data["rig_type"] = (rig_type or "human").strip().lower()
            if extra_animations:
                request_data["extra_animations"] = [a.strip() for a in extra_animations if a and a.strip()]
        if action == "regenerate_icon" and prompt:
            request_data["prompt"] = prompt
        if action == "regenerate_icon" and reference:
            request_data["reference_category"], request_data["reference_item_id"] = reference
        with open(request_path, "w", encoding="utf-8") as f:
            json.dump(request_data, f, indent=2)
        print(f"[ASSET ACTION REQUEST] {request_id} -> {action} on {category}/{item_id}" + (f" (rig_type={request_data.get('rig_type')})" if action == "rig" else ""))
        return request_data

    def handle_request_rigging(self):
        try:
            content_len = int(self.headers.get("Content-Length", 0))
            post_body = self.rfile.read(content_len)
            data = json.loads(post_body.decode("utf-8")) if content_len > 0 else {}
            req = self._queue_asset_action_request("rig", data.get("category", "").strip().lower(), data.get("item_id", "").strip().lower(), data.get("rig_type"), extra_animations=data.get("extra_animations"))
            self.send_json_response({"success": True, "message": f"Rigging requested for '{req['target_item_id']}' — a Claude session watching the queue will pick it up.", "request": req}, 200)
        except ValueError as e:
            self.send_json_response({"success": False, "error": str(e)}, 400)
        except Exception as e:
            print(f"Error requesting rigging: {e}")
            self.send_json_response({"success": False, "error": str(e)}, 500)

    def handle_request_regenerate_model(self):
        try:
            content_len = int(self.headers.get("Content-Length", 0))
            post_body = self.rfile.read(content_len)
            data = json.loads(post_body.decode("utf-8")) if content_len > 0 else {}
            req = self._queue_asset_action_request("regenerate_model", data.get("category", "").strip().lower(), data.get("item_id", "").strip().lower())
            self.send_json_response({"success": True, "message": f"Model regeneration requested for '{req['target_item_id']}' — a Claude session watching the queue will pick it up.", "request": req}, 200)
        except ValueError as e:
            self.send_json_response({"success": False, "error": str(e)}, 400)
        except Exception as e:
            print(f"Error requesting model regeneration: {e}")
            self.send_json_response({"success": False, "error": str(e)}, 500)

    def handle_request_regenerate_model_batch(self):
        try:
            content_len = int(self.headers.get("Content-Length", 0))
            post_body = self.rfile.read(content_len)
            data = json.loads(post_body.decode("utf-8")) if content_len > 0 else {}
            items = data.get("items", [])
            if not isinstance(items, list) or not items:
                self.send_json_response({"success": False, "error": "No items provided"}, 400)
                return

            created, errors = [], []
            for it in items:
                try:
                    cat = (it.get("category") or "").strip().lower()
                    item_id = (it.get("id") or it.get("item_id") or "").strip().lower()
                    created.append(self._queue_asset_action_request(
                        "regenerate_model", cat, item_id
                    ))
                except ValueError as e:
                    errors.append(str(e))

            print(f"[ASSET ACTION REQUEST BATCH] regenerate_model -> {len(created)} queued, {len(errors)} error(s)")
            self.send_json_response({
                "success": True,
                "message": f"Model generation requested for {len(created)} asset(s)" + (f" ({len(errors)} skipped)" if errors else ""),
                "requests": created,
                "errors": errors
            }, 200)
        except Exception as e:
            print(f"Error requesting batch model generation: {e}")
            self.send_json_response({"success": False, "error": str(e)}, 500)

    def handle_request_icon(self):
        try:
            content_len = int(self.headers.get("Content-Length", 0))
            post_body = self.rfile.read(content_len)
            data = json.loads(post_body.decode("utf-8")) if content_len > 0 else {}
            reference = resolve_reference_asset(data.get("reference_category", "").strip().lower(), data.get("reference_item_id", "").strip().lower())
            req = self._queue_asset_action_request("regenerate_icon", data.get("category", "").strip().lower(), data.get("item_id", "").strip().lower(), reference=reference, prompt=data.get("prompt"))
            self.send_json_response({"success": True, "message": f"New icon requested for '{req['target_item_id']}' — a Claude session watching the queue will pick it up.", "request": req}, 200)
        except ValueError as e:
            self.send_json_response({"success": False, "error": str(e)}, 400)
        except Exception as e:
            print(f"Error requesting icon: {e}")
            self.send_json_response({"success": False, "error": str(e)}, 500)

    def handle_open_item_folder(self):
        """Opens an item's folder in Windows Explorer - a local-only dev
        convenience (this server only ever binds to localhost), not exposed
        to anything untrusted."""
        try:
            content_len = int(self.headers.get("Content-Length", 0))
            post_body = self.rfile.read(content_len)
            data = json.loads(post_body.decode("utf-8")) if content_len > 0 else {}
            category = (data.get("category") or "").strip().lower()
            item_id = (data.get("item_id") or "").strip().lower()

            if not category or not item_id:
                self.send_json_response({"success": False, "error": "Missing category or item_id"}, 400)
                return
            if category not in ALLOWED_CATEGORIES:
                self.send_json_response({"success": False, "error": f"Invalid category: {category}"}, 400)
                return

            item_dir = os.path.join(BASE_DIR, category, item_id)
            if not os.path.isdir(item_dir):
                self.send_json_response({"success": False, "error": f"Asset not found: {category}/{item_id}"}, 404)
                return

            subprocess.Popen(["explorer", os.path.normpath(item_dir)])
            self.send_json_response({"success": True}, 200)
        except Exception as e:
            print(f"Error opening item folder: {e}")
            self.send_json_response({"success": False, "error": str(e)}, 500)

    def handle_request_rigging_batch(self):
        try:
            content_len = int(self.headers.get("Content-Length", 0))
            post_body = self.rfile.read(content_len)
            data = json.loads(post_body.decode("utf-8")) if content_len > 0 else {}
            items = data.get("items", [])
            if not isinstance(items, list) or not items:
                self.send_json_response({"success": False, "error": "No items provided"}, 400)
                return

            rig_type = data.get("rig_type")
            extra_animations = data.get("extra_animations")
            created, errors = [], []
            for it in items:
                try:
                    created.append(self._queue_asset_action_request(
                        "rig", (it.get("category") or "").strip().lower(), (it.get("id") or it.get("item_id") or "").strip().lower(), rig_type, extra_animations=extra_animations
                    ))
                except ValueError as e:
                    errors.append(str(e))

            print(f"[ASSET ACTION REQUEST BATCH] rig -> {len(created)} queued, {len(errors)} error(s)")
            self.send_json_response({
                "success": True,
                "message": f"Rigging requested for {len(created)} asset(s)" + (f" ({len(errors)} skipped)" if errors else ""),
                "requests": created,
                "errors": errors
            }, 200)
        except Exception as e:
            print(f"Error requesting batch rigging: {e}")
            self.send_json_response({"success": False, "error": str(e)}, 500)

    def handle_list_asset_requests(self):
        try:
            requests = []
            for status, folder in (
                ("pending", ASSET_REQUESTS_PENDING),
                ("in_progress", ASSET_REQUESTS_IN_PROGRESS),
                ("done", ASSET_REQUESTS_DONE),
            ):
                if not os.path.isdir(folder):
                    continue
                for fname in os.listdir(folder):
                    if not fname.endswith(".json"):
                        continue
                    try:
                        with open(os.path.join(folder, fname), "r", encoding="utf-8") as f:
                            data = json.load(f)
                        data["status"] = data.get("status", status)
                        requests.append(data)
                    except Exception:
                        continue

            requests.sort(key=lambda r: r.get("requested_at", ""), reverse=True)
            self.send_json_response({"success": True, "requests": requests}, 200)

        except Exception as e:
            print(f"Error listing asset requests: {e}")
            self.send_json_response({"success": False, "error": str(e)}, 500)

    def handle_update_asset_request(self):
        """Lets a Claude session processing a finalized batch report fine-
        grained progress on one request: a human-readable 'step' (e.g.
        'generating icon via FLUX', 'generating 3D mesh via Hunyuan3D-2'),
        a credits_used cost-tracking dict (always zero under the current
        free pipeline, kept for backward compatibility with older request
        records), and - when the request is actually finished - a status
        transition that physically moves the request file into
        in_progress/ or done/ so the queue folders reflect real progress,
        not just a status field nobody ever changes.

        Body: {id, step?, credits_used?: {...}, status?: "in_progress"|
        "done", error?}. Only fields present in the body are touched;
        credits_used is merged key-by-key (pass the running total, not a
        delta)."""
        try:
            content_len = int(self.headers.get("Content-Length", 0))
            post_body = self.rfile.read(content_len)
            data = json.loads(post_body.decode("utf-8")) if content_len > 0 else {}

            request_id = data.get("id", "").strip()
            if not request_id:
                self.send_json_response({"success": False, "error": "Missing id"}, 400)
                return

            fname = f"{request_id}.json"
            current_folder = None
            for folder in (ASSET_REQUESTS_PENDING, ASSET_REQUESTS_IN_PROGRESS, ASSET_REQUESTS_DONE):
                if os.path.isfile(os.path.join(folder, fname)):
                    current_folder = folder
                    break

            if current_folder is None:
                self.send_json_response({"success": False, "error": f"No request found with id '{request_id}'"}, 404)
                return

            with open(os.path.join(current_folder, fname), "r", encoding="utf-8") as f:
                req = json.load(f)

            if "step" in data:
                req["step"] = data["step"]
            if "error" in data:
                req["error"] = data["error"]
            if "item_id" in data and data["item_id"]:
                # The real catalog item id this request produced - lets a
                # finished stage-set auto-assemble into a growth group (see
                # maybe_autocreate_growth_group) without a Claude session
                # having to separately call /api/growth-groups by hand.
                req["created_item_id"] = data["item_id"].strip().lower()
            if "credits_used" in data and isinstance(data["credits_used"], dict):
                existing = req.get("credits_used") or {}
                existing.update(data["credits_used"])
                req["credits_used"] = existing

            new_folder = current_folder
            if "status" in data:
                status = data["status"]
                if status not in ("pending", "queued", "in_progress", "done"):
                    self.send_json_response({"success": False, "error": f"Invalid status: {status}"}, 400)
                    return
                req["status"] = status
                if status == "in_progress":
                    new_folder = ASSET_REQUESTS_IN_PROGRESS
                elif status == "done":
                    new_folder = ASSET_REQUESTS_DONE
                    req["completed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

            with open(os.path.join(current_folder, fname), "w", encoding="utf-8") as f:
                json.dump(req, f, indent=2)

            if new_folder != current_folder:
                os.makedirs(new_folder, exist_ok=True)
                shutil.move(os.path.join(current_folder, fname), os.path.join(new_folder, fname))

            print(f"[REQUEST UPDATE] {request_id} -> status={req.get('status')} step={req.get('step')!r}")

            autocreated_group = None
            if req.get("status") == "done" and req.get("request_group_id"):
                autocreated_group = maybe_autocreate_growth_group(req["request_group_id"])

            response = {"success": True, "request": req}
            if autocreated_group:
                response["autocreated_growth_group"] = autocreated_group
            self.send_json_response(response, 200)

        except Exception as e:
            print(f"Error updating asset request: {e}")
            self.send_json_response({"success": False, "error": str(e)}, 500)

    def handle_delete_asset_request(self):
        """Removes one request from the queue (any status/folder). This only
        ever touches the request .json file - it never deletes anything the
        request produced, since a request and the real asset it may have
        generated are two separate things by the time this is used."""
        try:
            content_len = int(self.headers.get("Content-Length", 0))
            post_body = self.rfile.read(content_len)
            data = json.loads(post_body.decode("utf-8")) if content_len > 0 else {}

            request_id = data.get("id", "").strip()
            if not request_id:
                self.send_json_response({"success": False, "error": "Missing id"}, 400)
                return

            fname = f"{request_id}.json"
            for folder in (ASSET_REQUESTS_PENDING, ASSET_REQUESTS_IN_PROGRESS, ASSET_REQUESTS_DONE):
                path = os.path.join(folder, fname)
                if os.path.isfile(path):
                    os.remove(path)
                    print(f"[REQUEST DELETE] {request_id}")
                    self.send_json_response({"success": True, "id": request_id}, 200)
                    return

            self.send_json_response({"success": False, "error": f"No request found with id '{request_id}'"}, 404)

        except Exception as e:
            print(f"Error deleting asset request: {e}")
            self.send_json_response({"success": False, "error": str(e)}, 500)

    def handle_delete_all_asset_requests(self):
        """Clears requests from the queue in one shot. By default (or with
        {"scope": "all"}) this covers pending/in_progress/done; pass
        {"scope": "done"} to only clear completed requests and leave
        anything still pending/in_progress untouched. Same scope caveat as
        the single-delete: only the request records are removed, never
        anything already generated from them."""
        try:
            content_len = int(self.headers.get("Content-Length", 0))
            post_body = self.rfile.read(content_len) if content_len > 0 else b""
            data = json.loads(post_body.decode("utf-8")) if post_body else {}
            scope = (data.get("scope") or "all").strip().lower()

            folders = (ASSET_REQUESTS_DONE,) if scope == "done" else (
                ASSET_REQUESTS_PENDING, ASSET_REQUESTS_IN_PROGRESS, ASSET_REQUESTS_DONE
            )

            deleted = 0
            for folder in folders:
                if not os.path.isdir(folder):
                    continue
                for fname in os.listdir(folder):
                    if fname.endswith(".json"):
                        os.remove(os.path.join(folder, fname))
                        deleted += 1

            print(f"[REQUEST DELETE ALL] Cleared {deleted} request(s) (scope={scope})")
            self.send_json_response({"success": True, "deleted_count": deleted}, 200)

        except Exception as e:
            print(f"Error clearing asset requests: {e}")
            self.send_json_response({"success": False, "error": str(e)}, 500)

    def handle_update_creative_claw_balance(self):
        """Lets a Claude session push a freshly-known Creative Claw balance
        (e.g. the creditsRemaining field returned directly by generate_image)
        so the status bar doesn't keep showing a stale number between
        sessions. Still not truly live-polled - Creative Claw has no public
        balance endpoint server.py can hit on its own - but this at least
        updates on every real data point a session actually has, instead of
        requiring a manual file edit."""
        try:
            content_len = int(self.headers.get("Content-Length", 0))
            post_body = self.rfile.read(content_len)
            data = json.loads(post_body.decode("utf-8")) if content_len > 0 else {}

            balance = data.get("balance")
            if not isinstance(balance, (int, float)):
                self.send_json_response({"success": False, "error": "Missing/invalid balance"}, 400)
                return

            record = {
                "balance": balance,
                "checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "note": data.get("note", "Updated by a Claude session from a live tool response (generate_image/estimate_generation), not truly live-polled by server.py.")
            }
            with open(CREATIVE_CLAW_BALANCE_PATH, "w", encoding="utf-8") as f:
                json.dump(record, f, indent=2)

            print(f"[CREATIVE CLAW BALANCE] Updated to {balance}")
            self.send_json_response({"success": True, **record}, 200)

        except Exception as e:
            print(f"Error updating creative claw balance: {e}")
            self.send_json_response({"success": False, "error": str(e)}, 500)

    def handle_finalize_asset_requests(self):
        """Moves every currently-pending request into a single 'queued' batch.
        Requests sit untouched here until the user explicitly finalizes -
        then a watching Claude session generates all their icons together
        as one contact-sheet image for N items and crops individual icons
        back out, still falling back to per-item 3D model generation where
        that genuinely can't be batched. See watch_asset_requests.py."""
        try:
            if not os.path.isdir(ASSET_REQUESTS_PENDING):
                self.send_json_response({"success": False, "error": "No pending requests"}, 400)
                return

            pending_files = [f for f in os.listdir(ASSET_REQUESTS_PENDING) if f.endswith(".json")]
            if not pending_files:
                self.send_json_response({"success": False, "error": "No pending requests to finalize"}, 400)
                return

            batch_id = f"batch_{int(time.time())}"
            finalized_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            batch_items = []

            for fname in pending_files:
                path = os.path.join(ASSET_REQUESTS_PENDING, fname)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                except Exception:
                    continue
                if data.get("status") != "pending":
                    continue
                data["status"] = "queued"
                data["batch_id"] = batch_id
                data["finalized_at"] = finalized_at
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
                batch_items.append(data)

            if not batch_items:
                self.send_json_response({"success": False, "error": "No pending requests to finalize"}, 400)
                return

            os.makedirs(ASSET_REQUESTS_BATCHES, exist_ok=True)
            batch_path = os.path.join(ASSET_REQUESTS_BATCHES, f"{batch_id}.json")
            with open(batch_path, "w", encoding="utf-8") as f:
                json.dump({
                    "batch_id": batch_id,
                    "finalized_at": finalized_at,
                    "items": batch_items
                }, f, indent=2)

            print(f"[FINALIZE BATCH] {batch_id} -> {len(batch_items)} request(s)")

            self.send_json_response({
                "success": True,
                "message": f"Queued {len(batch_items)} request(s) as {batch_id}.",
                "batch_id": batch_id,
                "count": len(batch_items)
            }, 200)

        except Exception as e:
            print(f"Error finalizing asset requests: {e}")
            self.send_json_response({"success": False, "error": str(e)}, 500)

    def handle_get_growth_groups(self):
        try:
            cfg = load_kit_config()
            self.send_json_response({"success": True, "growth_groups": cfg["growth_groups"]}, 200)
        except Exception as e:
            print(f"Error loading growth groups: {e}")
            self.send_json_response({"success": False, "error": str(e)}, 500)

    def handle_save_growth_group(self):
        try:
            content_len = int(self.headers.get("Content-Length", 0))
            post_body = self.rfile.read(content_len)
            data = json.loads(post_body.decode("utf-8")) if content_len > 0 else {}

            species = data.get("species", "").strip().lower()
            if not species:
                self.send_json_response({"success": False, "error": "Missing species key"}, 400)
                return

            try:
                update_script = os.path.join(BASE_DIR, "update_catalog_readme.py")
            except Exception:
                update_script = None

            if data.get("delete"):
                result = remove_growth_group(species)
                if update_script and os.path.exists(update_script):
                    subprocess.Popen([sys.executable, update_script])
                print(f"[GROWTH GROUP] {species} deleted -> {len(result['cleared_items'])} item(s) cleared")
                self.send_json_response({
                    "success": True,
                    "message": f"Growth group '{species}' deleted; {len(result['cleared_items'])} item(s) reverted to non-growable.",
                    **result
                }, 200)
                return

            result = save_growth_group(species, data)

            if update_script and os.path.exists(update_script):
                subprocess.Popen([sys.executable, update_script])

            print(f"[GROWTH GROUP] {species} -> {len(result['updated_items'])} stage(s) updated")

            self.send_json_response({
                "success": True,
                "message": f"Growth group '{result['group']['name']}' saved with {len(result['updated_items'])} stage(s).",
                **result
            }, 200)

        except (ValueError, FileNotFoundError) as e:
            self.send_json_response({"success": False, "error": str(e)}, 400)
        except Exception as e:
            print(f"Error saving growth group: {e}")
            self.send_json_response({"success": False, "error": str(e)}, 500)

    def handle_save_manifest(self):
        """Freeform manifest editor: lets the UI add/edit/delete any field in
        an item's <item_id>.json. 'id' and 'category' are structural (they
        must match the folder the file actually lives in, or every other
        endpoint that reads this manifest breaks) so they're force-corrected
        back to the real values rather than trusted from the request - use
        Rename/Move for those instead."""
        try:
            content_len = int(self.headers.get("Content-Length", 0))
            post_body = self.rfile.read(content_len)
            data = json.loads(post_body.decode("utf-8")) if content_len > 0 else {}

            category = data.get("category", "").strip().lower()
            item_id = data.get("item_id", "").strip().lower()
            manifest = data.get("manifest")

            if not category or not item_id:
                self.send_json_response({"success": False, "error": "Missing category or item_id"}, 400)
                return
            if category not in ALLOWED_CATEGORIES:
                self.send_json_response({"success": False, "error": f"Invalid category: {category}"}, 400)
                return
            if ".." in item_id or "/" in item_id or "\\" in item_id:
                self.send_json_response({"success": False, "error": "Invalid item_id"}, 400)
                return
            if not isinstance(manifest, dict):
                self.send_json_response({"success": False, "error": "manifest must be a JSON object"}, 400)
                return

            item_dir = os.path.join(BASE_DIR, category, item_id)
            if not os.path.isdir(item_dir):
                self.send_json_response({"success": False, "error": f"Asset folder not found: {category}/{item_id}"}, 404)
                return

            manifest["id"] = item_id
            manifest["category"] = category

            manifest_path = os.path.join(item_dir, f"{item_id}.json")
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2)

            try:
                update_script = os.path.join(BASE_DIR, "update_catalog_readme.py")
                if os.path.exists(update_script):
                    subprocess.Popen([sys.executable, update_script])
            except Exception as e:
                print(f"Warning running catalog update: {e}")

            print(f"[SAVE MANIFEST] {category}/{item_id}")

            self.send_json_response({
                "success": True,
                "message": f"Manifest for '{item_id}' saved.",
                "category": category,
                "item_id": item_id,
                "manifest": manifest
            }, 200)

        except Exception as e:
            print(f"Error saving manifest: {e}")
            self.send_json_response({"success": False, "error": str(e)}, 500)

    def handle_regen_icon(self):
        try:
            content_len = int(self.headers.get("Content-Length", 0))
            post_body = self.rfile.read(content_len)
            data = json.loads(post_body.decode("utf-8")) if content_len > 0 else {}

            category = data.get("category", "").strip().lower()
            item_id = data.get("item_id", "").strip().lower()

            if not category or not item_id or category not in ALLOWED_CATEGORIES:
                self.send_json_response({"success": False, "error": "Invalid category or item_id"}, 400)
                return

            if ".." in item_id or "/" in item_id or "\\" in item_id:
                self.send_json_response({"success": False, "error": "Invalid path traversal"}, 400)
                return

            ok, msg = regen_icons.regen_icon(category, item_id)
            if ok:
                self.send_json_response({
                    "success": True,
                    "message": msg,
                    "category": category,
                    "item_id": item_id,
                    "icon_url": f"{category}/{item_id}/{item_id}.png"
                }, 200)
            else:
                self.send_json_response({"success": False, "error": msg}, 400)
        except Exception as e:
            print(f"Error regenerating icon: {e}")
            self.send_json_response({"success": False, "error": str(e)}, 500)

    def handle_regen_icons(self):
        try:
            content_len = int(self.headers.get("Content-Length", 0))
            post_body = self.rfile.read(content_len)
            data = json.loads(post_body.decode("utf-8")) if content_len > 0 else {}

            is_all = data.get("all", False)
            target_cat = data.get("category")
            items = data.get("items", [])

            if is_all or (not items and not target_cat):
                results = regen_icons.regen_all(target_category=target_cat)
            elif items:
                results = regen_icons.regen_batch(items)
            elif target_cat:
                results = regen_icons.regen_all(target_category=target_cat)
            else:
                results = []

            successes = sum(1 for r in results if r.get("success"))
            self.send_json_response({
                "success": True,
                "total": len(results),
                "success_count": successes,
                "results": results
            }, 200)
        except Exception as e:
            print(f"Error in batch regen icons: {e}")
            self.send_json_response({"success": False, "error": str(e)}, 500)

    def send_json_response(self, obj, status_code=200):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

class ReusableThreadingServer(ThreadingHTTPServer):
    allow_reuse_address = True

def main():
    server_address = ("", PORT)
    httpd = ReusableThreadingServer(server_address, AssetKitHandler)
    print("=" * 60)
    print(f"  Homesteader Asset Kit Server running on port {PORT}")
    print(f"  Directory: {BASE_DIR}")
    print(f"  URL: http://localhost:{PORT}/index.html")
    print("  API: POST /api/delete-asset (Enabled)")
    print("=" * 60)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer shutting down gracefully.")
        httpd.server_close()

if __name__ == "__main__":
    main()

