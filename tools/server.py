#!/usr/bin/env python3
"""
Homesteader Master Asset Kit Local HTTP Server with API Support
Serves static assets and provides REST API endpoints for asset management:
- POST /api/delete-asset: Permanently deletes an asset directory from disk.
"""

import os
import re
import sys
import struct
import time
import json
import datetime
import shutil
import subprocess
import urllib.request
import urllib.parse
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
import regen_icons
import animal_ai
import light_emitter
import push_to_game
import trash_store
try:
    # The guide list lives in the MCP server (the canonical "which docs are
    # authoritative" source). Importing it means adding a guide there makes it
    # appear in the Docs panel automatically, instead of maintaining a second
    # list here that could drift.
    from asset_kit_mcp import GUIDE_FILES, ACTIVE_GUIDES
except Exception as _guide_import_err:  # pragma: no cover - defensive
    print(f"Warning: could not import guide list from asset_kit_mcp: {_guide_import_err}")
    GUIDE_FILES = {}
    ACTIVE_GUIDES = []

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
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
BASE_DIR = os.path.join(PROJECT_DIR, "assets")
BIOMES_DIR = os.path.join(BASE_DIR, "biomes")
INDEX_HTML_PATH = os.path.join(BASE_DIR, "index.html")
os.chdir(BASE_DIR)


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


def read_growth_group_manifest(category, item_id):
    """Reads a growth-group asset's own manifest (assets/<cat>/<id>/<id>.json)
    when it declares is_growable. Returns None for ordinary items, so callers
    can cheaply ask 'is this a group?' without parsing twice. The group's
    manifest is AUTHORITATIVE for its own scheme - see growth_group.schema.json
    (kit_config.json was only the one-time migration source for this data)."""
    manifest_path = os.path.join(BASE_DIR, category, item_id, f"{item_id}.json")
    if not os.path.isfile(manifest_path):
        return None
    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
    except Exception:
        return None
    if not manifest.get("is_growable"):
        return None
    return manifest

def resolve_growth_group_model(category, item_id, manifest=None):
    """Returns (relative_model_path, format) for the model that represents a
    growth group as a whole, or None when it can't be resolved.

    A group owns multiple models - one per stage - and the scheme decides
    which is displayed. The group's own catalog/viewer representation uses
    the icon_stage stage (by convention the largest one), so the asset reads
    as its fully-grown self rather than its seed form. Falls back to the
    final stage when icon_stage is absent."""
    if manifest is None:
        manifest = read_growth_group_manifest(category, item_id)
    if not manifest:
        return None
    growth = manifest.get("growth") or {}
    stages = growth.get("stages") or []
    if not stages:
        return None
    icon_stage = growth.get("icon_stage")

    # Try the icon_stage first, then walk DOWN the lifecycle. Not every stage
    # has a mesh on disk - some construction phases and a few tree stages ship
    # only an icon - so a group whose final stage is meshless should still show
    # its best available model rather than appearing to have no 3D at all.
    preferred = next((s for s in stages if s.get("stage") == icon_stage), None)
    ordered = ([preferred] if preferred else []) + sorted(
        (s for s in stages if s is not preferred),
        key=lambda s: s.get("stage") or 0, reverse=True)

    for chosen in ordered:
        resource = (chosen.get("resource") or "").strip()
        model = (chosen.get("model") or "").strip()
        if not resource or not model:
            continue
        rel = f"{category}/{item_id}/{resource}{model}"
        if os.path.isfile(os.path.join(BASE_DIR, *rel.split("/"))):
            return rel, os.path.splitext(model)[1].lstrip(".").lower()
    return None


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
    # A manifest may name the file the viewer should display. Ranking below is a
    # HEURISTIC (prefer the clip-heaviest GLB); an explicit declaration is a
    # decision, so it takes precedence. Without this an item whose only clean
    # static mesh sits beside a clip-heavy rigged GLB can never show the static
    # mesh - the heuristic would always pick the animated one.
    declared_viewer_model = manifest.get("viewer_model")
    for m in manifest.get("models", []):
        rel = f"{category}/{item_id}/{m['file']}"
        entry = {"file": m["file"], "format": m.get("format"), "path": rel}
        if m.get("description"):
            entry["description"] = m["description"]
        models.append(entry)
        # Rank by how many animation clips a file ACTUALLY contains, not by its
        # filename. The old rule ranked "_walk"/"_run" FBXs above GLBs, which
        # was correct when one FBX held one clip - but a GLB is a container and
        # commonly holds every clip at once, so that rule made the viewer load a
        # single-clip FBX (and the FBX path draws no animation buttons at all)
        # while a four-clip GLB sat unused. GLB is the master format: one
        # animated GLB should beat a pile of per-clip FBXs.
        fname_lower = m["file"].lower()
        fmt = (m.get("format") or "").lower()
        is_glb = fmt == "glb" or fname_lower.endswith(".glb")
        # clip_count is filled in below for GLBs; FBX/JPG etc. are unknown here.
        clip_count = count_glb_animation_clips(os.path.join(item_dir, m["file"])) \
            if is_glb else 0
        entry["animation_count"] = clip_count

        if clip_count >= 2:
            rank = 5          # a multi-clip GLB is the ideal viewer payload
        elif clip_count == 1:
            rank = 4          # a single-clip GLB still beats any FBX
        elif any(k in fname_lower for k in ("_walk", "_run")):
            rank = 3          # legacy per-clip FBX, kept as a fallback
        elif "_rigged" in fname_lower:
            rank = 2
        elif is_glb:
            rank = 1.5        # unanimated GLB: standard format, preferred over
                              # a legacy unanimated FBX/OBJ of the same item
        else:
            rank = 1
        if declared_viewer_model and m["file"] == declared_viewer_model:
            rank = 100        # explicit choice outranks every heuristic
        if rank > best_model_rank:
            best_model = rel
            model_format = m.get("format")
            best_model_rank = rank

    # A growth group IS an asset, but its models live in its own stage
    # resource folders rather than a models[] array of its own - the scheme
    # selects which one represents the group. Resolve the icon_stage's model
    # (by convention the largest/most recognisable stage) so the catalog and
    # the 3D viewer have something to show instead of an empty model list.
    growth_group_model = None
    if manifest.get("is_growable"):
        resolved = resolve_growth_group_model(category, item_id, manifest)
        if resolved:
            rel, fmt = resolved
            models = [{"file": os.path.basename(rel), "format": fmt, "path": rel}]
            best_model = rel
            model_format = fmt
            growth_group_model = rel
    return {
        "id": manifest.get("id", item_id),
        "name": manifest.get("name", item_id),
        "category": manifest.get("category", category),
        "description": manifest.get("description", ""),
        "icon": icon_rel,
        "is_growable": bool(manifest.get("is_growable")),
        "growth_group_model": growth_group_model,
        "models": models,
        "best_model": best_model,
        "model_format": model_format,
        "has_3d": bool(models),
        "properties": manifest.get("properties", {}),
        "dimensions": manifest.get("dimensions", {}),
        "growth": manifest.get("growth", {}),
        "spawning": manifest.get("spawning", {}),
        "utilities": manifest.get("utilities", {}),
        "rigging": manifest.get("rigging", {}),
        "plugin_metadata": manifest.get("plugin_metadata", {}),
        "manifest": manifest
    }


def build_stage_entry(category, group_id, stage_resource):
    # Builds a catalog-entry-shaped dict for ONE growth stage.
    #
    # A stage is a resource folder inside its group, not a catalog asset -
    # build_full_catalog() skips the "stages" directory outright, so a stage
    # is never in ALL_ITEMS and /api/catalog-entry cannot resolve it. The
    # stage's own manifest DOES exist at
    # <category>/<group>/<resource>/<stage_id>.json, so build the same entry
    # shape straight from it and let the item modal open a stage exactly like
    # any other asset.
    #
    # stage_resource is the group manifest's per-stage `resource` value
    # (e.g. "stages/struct_framing/"); the manifest inside it names itself, so
    # no id has to be guessed. Returns None when the folder or manifest is
    # missing, matching build_catalog_entry's contract.
    res_dir = os.path.join(BASE_DIR, category, group_id,
                           stage_resource.replace("/", os.sep).strip(os.sep))
    if not os.path.isdir(res_dir):
        return None
    # A stage folder holds exactly one manifest, named after the stage itself.
    manifest_name = None
    for fn in sorted(os.listdir(res_dir)):
        if fn.endswith(".json"):
            manifest_name = fn
            break
    if not manifest_name:
        return None
    stage_id = manifest_name[:-len(".json")]
    try:
        with open(os.path.join(res_dir, manifest_name), "r", encoding="utf-8") as f:
            manifest = json.load(f)
    except Exception as e:
        print(f"Warning: failed to read stage manifest "
              f"{category}/{group_id}/{stage_resource}: {e}")
        return None
    # Paths are relative to the ASSETS root, and carry the group + resource
    # folder segments so the browser can fetch them directly.
    rel_dir = f"{category}/{group_id}/{stage_resource.strip('/')}"
    icon_rel = f"{rel_dir}/{manifest.get('icon')}" if manifest.get("icon") else None
    models = []
    best_model = None
    model_format = None
    for m in manifest.get("models", []):
        if not isinstance(m, dict) or not m.get("file"):
            continue
        rel = f"{rel_dir}/{m['file']}"
        entry = {"file": m["file"], "format": m.get("format"), "path": rel}
        if m.get("description"):
            entry["description"] = m["description"]
        models.append(entry)
        if best_model is None:
            best_model = rel
            model_format = m.get("format")

    return {
        "id": manifest.get("id", stage_id),
        "name": manifest.get("name", stage_id),
        "category": category,
        "description": manifest.get("description", ""),
        "icon": icon_rel,
        "is_growable": False,
        "is_growth_stage": True,
        "growth_group_id": group_id,
        "growth_group_resource": stage_resource,
        "growth_group_model": None,
        "models": models,
        "best_model": best_model,
        "model_format": model_format,
        "has_3d": bool(models),
        "properties": manifest.get("properties", {}),
        "dimensions": manifest.get("dimensions", {}),
        "growth": manifest.get("growth", {}),
        "spawning": manifest.get("spawning", {}),
        "utilities": manifest.get("utilities", {}),
        "rigging": manifest.get("rigging", {}),
        "plugin_metadata": manifest.get("plugin_metadata", {}),
        "manifest": manifest,
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
            if item_id == GROWTH_STAGES_DIRNAME:
                continue
            if not os.path.isdir(os.path.join(cat_dir, item_id)):
                continue
            entry = build_catalog_entry(category, item_id)
            if entry is not None:
                items.append(entry)
    return items


_catalog_cache = {"items": None, "built_at": 0.0}
CATALOG_CACHE_TTL_SECONDS = 10


def item_exists(item_id):
    """True when assets/<category>/<item_id>/<item_id>.json exists for any category."""
    if not item_id or "/" in item_id or "\\" in item_id or ".." in item_id:
        return False
    try:
        for cat in os.listdir(BASE_DIR):
            if os.path.isfile(os.path.join(BASE_DIR, cat, item_id, item_id + ".json")):
                return True
    except OSError:
        pass
    return False


def plantable_group_ids():
    """Ids (and species keys) of every tree/crop growth group in the catalog."""
    ids = set()
    for item in get_cached_catalog():
        m = item.get("manifest") or {}
        g = m.get("growth") or {}
        if m.get("is_growable") and g.get("growth_type") in ("tree", "crop"):
            ids.add(item.get("id"))
            if g.get("species"):
                ids.add(g["species"])
    return ids


def clean_drops(raw, label):
    """Validates a list of { item_id, amount_min, amount_max } drops. Blank rows are dropped.
    Returns (list, None) or (None, error)."""
    out = []
    if raw in (None, ""):
        return out, None
    if not isinstance(raw, list):
        return None, f"{label} must be a list."
    for i, d in enumerate(raw):
        if not isinstance(d, dict):
            return None, f"{label}[{i}] must be an object."
        item_id = str(d.get("item_id") or "").strip()
        if not item_id:
            continue
        if not item_exists(item_id):
            return None, f"{label}[{i}]: unknown item '{item_id}'."
        try:
            lo = int(float(d.get("amount_min") if d.get("amount_min") not in (None, "") else 1))
            hi = int(float(d.get("amount_max") if d.get("amount_max") not in (None, "") else lo))
        except (TypeError, ValueError):
            return None, f"{label}[{i}]: amounts must be whole numbers."
        if lo < 1 or hi < lo:
            return None, f"{label}[{i}]: need 1 <= amount_min <= amount_max."
        out.append({"item_id": item_id, "amount_min": lo, "amount_max": hi})
    return out, None


def harvest_tools_of(y):
    """The harvest-tool list of a yield block: `tools` (list, or comma string), else the legacy
    single `tool`. Returns a de-duplicated list of trimmed ids / '#tags'."""
    raw = y.get("tools")
    if raw in (None, "", []):
        raw = y.get("tool")
    if isinstance(raw, str):
        raw = raw.split(",")
    out = []
    for s in (raw or []):
        s = str(s).strip()
        if s and s not in out:
            out.append(s)
    return out


def check_tool_ref(tool):
    """Validates a harvest-tool reference: an existing item id or an existing '#tag'.
    Returns an error string or None."""
    if tool.startswith("#"):
        if tool[1:] not in load_material_tags().get("tags", {}):
            return f"Unknown tag '{tool}'."
    elif not item_exists(tool):
        return f"Unknown tool item '{tool}'."
    return None


def planter_owner(item_id, exclude_group_id=None):
    """The id of the growth group that already names <item_id> as its planting item, or None."""
    for item in get_cached_catalog():
        m = item.get("manifest") or {}
        if not m.get("is_growable") or item.get("id") == exclude_group_id:
            continue
        planted_by = (((m.get("growth") or {}).get("rules") or {}).get("planting") or {}).get("item_id")
        if planted_by == item_id:
            return item.get("id")
    return None


def check_group_links(manifest, category):
    """Cross-checks for a growth group's own links (planting item, variant models). Returns errors."""
    errs = []
    rules = (manifest.get("growth") or {}).get("rules") or {}
    group_id = manifest.get("id")

    pitem = (rules.get("planting") or {}).get("item_id")
    if isinstance(pitem, str) and pitem.strip():
        if not item_exists(pitem):
            errs.append(f"growth.rules.planting.item_id: unknown item '{pitem}'")
        else:
            other = planter_owner(pitem, group_id)
            if other:
                errs.append(f"growth.rules.planting.item_id: '{pitem}' already plants group '{other}'")

    failure = rules.get("failure") or {}
    variants = [("failure.withered", failure.get("withered")), ("failure.dead", failure.get("dead")),
                ("yield.stump", (rules.get("yield") or {}).get("stump"))]
    if (manifest.get("growth") or {}).get("growth_type") == "tree" and isinstance(failure.get("withered"), dict):
        errs.append("growth.rules.failure.withered: crops only (trees use yield.stump)")
    if (manifest.get("growth") or {}).get("growth_type") == "crop" and isinstance((rules.get("yield") or {}).get("stump"), dict):
        errs.append("growth.rules.yield.stump: trees only")
    for key, v in variants:
        if not isinstance(v, dict):
            continue
        res, mdl = v.get("resource"), v.get("model")
        if not (isinstance(res, str) and isinstance(mdl, str) and res and mdl):
            errs.append(f"growth.rules.{key}: needs both resource and model")
            continue
        path = os.path.join(BASE_DIR, category, group_id, res.replace("/", os.sep), mdl)
        if not os.path.isfile(path):
            errs.append(f"growth.rules.{key}: model not found at {res}{mdl}")
    return errs


RULE_SEASONS = ("spring", "summer", "fall", "winter", "year_round")
RULE_OUT_OF_SEASON = ("pause", "wither", "die")
RULE_WITHER_BEHAVIOR = ("stall", "regress_one_stage", "die")


def sanitize_growth_rules(raw, total_stages, group_id=None, growth_type=None):
    """Validates/normalises a group's growth.rules block against
    growth_group.schema.json. Returns (rules, None) or (None, error).
    Empty sub-blocks and unset fields are dropped, so an all-blank form saves
    as {} ('no rule')."""
    if raw is None:
        return {}, None
    if not isinstance(raw, dict):
        return None, "rules must be an object."

    def num(v, label, lo=None, hi=None, whole=False):
        if v is None or (isinstance(v, str) and not v.strip()):
            return None, None
        try:
            f = float(v)
        except (TypeError, ValueError):
            return None, f"{label} must be a number."
        if lo is not None and f < lo:
            return None, f"{label} must be at least {lo}."
        if hi is not None and f > hi:
            return None, f"{label} must be at most {hi}."
        if whole and not f.is_integer():
            return None, f"{label} must be a whole number."
        return (int(f) if f.is_integer() else f), None

    out = {}

    y = raw.get("yield") or {}
    item_id = str(y.get("item_id") or "").strip()
    # amount_min / amount_max (legacy "amount" still accepted and used for both)
    legacy = y.get("amount")
    raw_min = y.get("amount_min") if y.get("amount_min") not in (None, "") else legacy
    raw_max = y.get("amount_max") if y.get("amount_max") not in (None, "") else legacy
    if item_id or raw_min not in (None, "") or raw_max not in (None, ""):
        if not item_id:
            return None, "yield.item_id is required when a yield amount is set."
        amount_min, err = num(raw_min, "yield.amount_min", 1, None, True)
        if err:
            return None, err
        if amount_min is None:
            return None, "yield.amount_min is required when a yield item is set."
        amount_max, err = num(raw_max, "yield.amount_max", 1, None, True)
        if err:
            return None, err
        if amount_max is None:
            amount_max = amount_min          # a blank max means a fixed yield
        if amount_max < amount_min:
            return None, "yield.amount_max must be at least amount_min."
        yld = {"item_id": item_id, "amount_min": amount_min, "amount_max": amount_max}
        tools = harvest_tools_of(y)
        for tool in tools:
            tool_err = check_tool_ref(tool)
            if tool_err:
                return None, "yield.tools: " + tool_err
        if tools:
            yld["tools"] = tools
        stump = y.get("stump") or {}
        s_res = str(stump.get("resource") or "").strip()
        s_mdl = str(stump.get("model") or "").strip()
        s_icon = str(stump.get("icon") or "").strip()
        if s_res or s_mdl:
            if growth_type != "tree":
                return None, "yield.stump is for tree groups only (crops use failure.withered)."
            if not re.match(r"^(stages/[^/]+|\.\./[a-z0-9_]+)/$", s_res):
                return None, "yield.stump.resource must look like 'stages/<folder>/' or '../<item_id>/'."
            if not s_mdl:
                return None, "yield.stump.model is required when a resource is set."
            yld["stump"] = {"resource": s_res, "model": s_mdl}
            if s_icon:
                yld["stump"]["icon"] = s_icon
        extras, err = clean_drops(y.get("extras"), "yield.extras")
        if err:
            return None, err
        if extras:
            yld["extras"] = extras
        hs, err = num(y.get("harvest_stage"), "yield.harvest_stage", 1, total_stages or None, True)
        if err:
            return None, err
        if hs is not None:
            yld["harvest_stage"] = hs
        if y.get("regrows"):
            rs, err = num(y.get("regrow_stage"), "yield.regrow_stage", 1, total_stages or None, True)
            if err:
                return None, err
            if rs is None:
                return None, "yield.regrow_stage is required when regrows is on."
            if rs >= (hs or total_stages or rs + 1):
                return None, "yield.regrow_stage must be less than the harvest stage."
            yld["regrows"] = True
            yld["regrow_stage"] = rs
        out["yield"] = yld
    elif clean_drops(y.get("extras"), "yield.extras")[0]:
        return None, "yield.item_id is required when extra drops are set."

    fr = raw.get("fruit") or {}
    if fr.get("is_fruiting"):
        if growth_type != "tree":
            return None, "fruit is for tree groups only."
        drops, err = clean_drops(fr.get("drops"), "fruit.drops")
        if err:
            return None, err
        if not drops:
            return None, "fruit.drops needs at least one item when the tree is fruiting."
        fruit = {"is_fruiting": True, "drops": drops}
        fruit_tools = harvest_tools_of(fr)   # what picks it: any ONE of these in the active slot (none = by hand)
        for tool in fruit_tools:
            tool_err = check_tool_ref(tool)
            if tool_err:
                return None, "fruit.tools: " + tool_err
        if fruit_tools:
            fruit["tools"] = fruit_tools
        fs, err = num(fr.get("fruit_stage"), "fruit.fruit_stage", 1, total_stages or None, True)
        if err:
            return None, err
        if fs is not None:
            fruit["fruit_stage"] = fs
        rd, err = num(fr.get("regrow_days"), "fruit.regrow_days", 1, None, False)
        if err:
            return None, err
        fruit["regrow_days"] = rd if rd is not None else 30
        out["fruit"] = fruit

    p = raw.get("planting") or {}
    planting = {}
    seasons = p.get("seasons")
    if isinstance(seasons, str):
        seasons = [s.strip().lower() for s in seasons.split(",") if s.strip()]
    if seasons:
        bad = [s for s in seasons if s not in RULE_SEASONS]
        if bad:
            return None, f"Unknown season(s): {', '.join(bad)}."
        if "year_round" in seasons and len(seasons) > 1:
            return None, "year_round must appear alone in planting.seasons."
        planting["seasons"] = list(dict.fromkeys(seasons))
    biome_ids = p.get("biomes")
    if isinstance(biome_ids, str):
        biome_ids = [b.strip() for b in biome_ids.split(",") if b.strip()]
    if biome_ids:
        if not isinstance(biome_ids, list) or not all(isinstance(b, str) for b in biome_ids):
            return None, "planting.biomes must be a list of biome ids."
        known = {os.path.splitext(f)[0] for f in os.listdir(BIOMES_DIR)
                 if f.endswith(".json")} if os.path.isdir(BIOMES_DIR) else set()
        unknown = [b for b in biome_ids if b not in known]
        if unknown:
            return None, f"Unknown biome(s): {', '.join(unknown)}."
        planting["biomes"] = list(dict.fromkeys(biome_ids))
    for key in ("min_temp_c", "max_temp_c"):
        v, err = num(p.get(key), f"planting.{key}")
        if err:
            return None, err
        if v is not None:
            planting[key] = v
    if ("min_temp_c" in planting and "max_temp_c" in planting
            and planting["max_temp_c"] <= planting["min_temp_c"]):
        return None, "planting.max_temp_c must be greater than min_temp_c."
    pitem = str(p.get("item_id") or "").strip()
    if pitem:
        if not item_exists(pitem):
            return None, f"planting.item_id: unknown item '{pitem}'."
        other = planter_owner(pitem, group_id)
        if other:
            return None, f"planting.item_id: '{pitem}' already plants group '{other}' (one item plants one group)."
        planting["item_id"] = pitem
    if p.get("indoor_ok"):
        planting["indoor_ok"] = True
    if planting:
        out["planting"] = planting

    n = raw.get("needs") or {}
    needs = {}
    v, err = num(n.get("water_interval_days"), "needs.water_interval_days", 1)
    if err:
        return None, err
    if v is not None:
        needs["water_interval_days"] = v
    if n.get("fertilizer_required"):
        needs["fertilizer_required"] = True
    if needs:
        out["needs"] = needs

    f = raw.get("failure") or {}
    failure = {}
    oos = str(f.get("out_of_season") or "").strip()
    if oos:
        if oos not in RULE_OUT_OF_SEASON:
            return None, f"failure.out_of_season must be one of {', '.join(RULE_OUT_OF_SEASON)}."
        if oos != "pause":
            failure["out_of_season"] = oos
    if f.get("frost_kills"):
        failure["frost_kills"] = True
    v, err = num(f.get("drought_days_before_wither"), "failure.drought_days_before_wither", 1)
    if err:
        return None, err
    if v is not None:
        failure["drought_days_before_wither"] = v
    wb = str(f.get("wither_behavior") or "").strip()
    if wb:
        if wb not in RULE_WITHER_BEHAVIOR:
            return None, f"failure.wither_behavior must be one of {', '.join(RULE_WITHER_BEHAVIOR)}."
        if wb != "stall":
            failure["wither_behavior"] = wb
    for key in ("withered", "dead"):
        v = f.get(key) or {}
        res = str(v.get("resource") or "").strip()
        mdl = str(v.get("model") or "").strip()
        icon = str(v.get("icon") or "").strip()
        if res or mdl:
            if key == "withered" and growth_type == "tree":
                return None, "failure.withered is for crop groups only (trees use yield.stump)."
            if not re.match(r"^(stages/[^/]+|\.\./[a-z0-9_]+)/$", res):
                return None, f"failure.{key}.resource must look like 'stages/<folder>/' or '../<item_id>/'."
            if not mdl:
                return None, f"failure.{key}.model is required when a resource is set."
            failure[key] = {"resource": res, "model": mdl}
            if icon:
                failure[key]["icon"] = icon
    if failure:
        out["failure"] = failure

    return out, None


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


def _read_doc_meta(doc_path):
    """Pulls a doc's sidebar entry (title/icon/summary) out of its own
    markdown, so the section list can never drift from the files it lists.

    Reads the leading `# Title` heading, an optional leading emoji, and the
    first body line as a summary. Missing pieces fall back to the filename,
    so a bare markdown file still shows up rather than being skipped.
    """
    fallback = os.path.splitext(os.path.basename(doc_path))[0]
    # "07_status_bar" -> "Status Bar" when there is no heading to use.
    if "_" in fallback:
        fallback_title = fallback.split("_", 1)[-1].replace("_", " ").title()
    else:
        fallback_title = fallback
    meta = {"title": fallback_title, "icon": "\U0001F4C4", "summary": ""}
    try:
        with open(doc_path, "r", encoding="utf-8") as f:
            lines = f.read().split("\n")
    except Exception:
        return meta

    for i, raw in enumerate(lines):
        line = raw.strip()
        if not line:
            continue
        if line.startswith("# "):
            heading = line[2:].strip()
            # Split a leading emoji/symbol off the title when one is present.
            parts = heading.split(" ", 1)
            # Only treat a leading token as an icon when it is genuinely
            # non-word (an emoji/symbol). This must NOT match a real word
            # followed by punctuation, e.g. "Schemas, Biomes & Tags", where
            # str.isalnum() is False only because of the comma.
            if len(parts) == 2 and parts[0] and not any(ch.isalnum() for ch in parts[0]):
                meta["icon"], meta["title"] = parts[0], parts[1].strip()
            else:
                meta["title"] = heading
            # First non-empty, non-heading line after the title is the summary.
            for later in lines[i + 1:]:
                text = later.strip()
                if text and not text.startswith(("#", "|", ">", "+", "-", "<")):
                    meta["summary"] = text
                    break
            break
    return meta


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
# Folder name holding a growth group's per-stage resource folders (models,
# icons, materials). Stage folders are RESOURCES the group's scheme selects
# from - they are not catalog assets themselves, so anything that walks a
# category folder must skip this name or every stage shows up as a
# duplicate item. Shared constant so build_full_catalog and the group
# readers can never disagree about the spelling.
GROWTH_STAGES_DIRNAME = "stages"
WATCHER_HEARTBEAT_PATH = os.path.join(BASE_DIR, "_asset_requests", "watcher_heartbeat.json")
WATCHER_STALE_AFTER_SECONDS = 15
ASSET_REQUESTS_DIR = os.path.join(BASE_DIR, "_asset_requests")
ASSET_REQUESTS_PENDING = os.path.join(ASSET_REQUESTS_DIR, "pending")
ASSET_REQUESTS_IN_PROGRESS = os.path.join(ASSET_REQUESTS_DIR, "in_progress")
ASSET_REQUESTS_DONE = os.path.join(ASSET_REQUESTS_DIR, "done")
ASSET_REQUESTS_BATCHES = os.path.join(ASSET_REQUESTS_DIR, "batches")

# In-app documentation (docs button). Markdown files live beside the catalog
# under assets/_docs/ - not the project-root docs/ folder, which holds the
# developer-facing pipeline/integration guides that this button doesn't show.
DOCS_DIR = os.path.join(BASE_DIR, "_docs")

# Soft-delete (Trash) storage lives in trash_store.py. Deleting an asset moves
# its folder to assets/_trash/ instead of rmtree-ing it, so a restore is a
# plain move back. build_full_catalog() only walks ALLOWED_CATEGORIES, so
# anything parked under _trash/ is invisible to the catalog automatically.
TRASH_DIR = trash_store.trash_dir_for(BASE_DIR)

BIOMES_DIR = os.path.join(BASE_DIR, "biomes")
APPROVALS_DIR = os.path.join(ASSET_REQUESTS_DIR, "approvals")
MESHY_BASE_URL = "https://api.meshy.ai"


def _find_meshy_api_key():
    """Reads MESHY_API_KEY from the env, falling back to the same key already
    configured for the meshy MCP server in .mcp.json, so it isn't
    retyped/duplicated into a third source file."""
    env_key = os.environ.get("MESHY_API_KEY")
    if env_key and not env_key.startswith("${"):
        return env_key
    # The key lives in the gitignored .env now, and .mcp.json holds only the
    # reference "${MESHY_API_KEY}". A raw read of .mcp.json therefore yields the
    # placeholder string, which Meshy rejects as a bad token - surfacing in the
    # UI as a 502 from /api/meshy-balance. Resolve through the shared env_loader
    # so both the .env value and the ${...} indirection work.
    try:
        sys.path.insert(0, os.path.join(PROJECT_DIR, "tools"))
        import env_loader
        env_loader.load_env()
        resolved = os.environ.get("MESHY_API_KEY")
        if resolved and not resolved.startswith("${"):
            return resolved
    except Exception:
        pass
    mcp_config_path = os.path.join(PROJECT_DIR, ".mcp.json")
    try:
        with open(mcp_config_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        value = (cfg.get("mcpServers", {}).get("meshy", {})
                    .get("env", {}).get("MESHY_API_KEY"))
        if value and value.startswith("${") and value.endswith("}"):
            return os.environ.get(value[2:-1].strip())
        return value
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


CLAUDE_USAGE_CACHE_PATH = os.path.join(os.path.expanduser("~"), ".claude", "vscode-claude-status-cache.json")
# Written by a Claude session (POST /api/claude-usage) from the plan limits
# the Claude app reports for the account. No token/credential is involved.
CLAUDE_USAGE_SESSION_PATH = os.path.join(BASE_DIR, "claude_usage.json")


def _iso_to_epoch(value):
    if not value:
        return None
    try:
        return datetime.datetime.fromisoformat(str(value).replace("Z", "+00:00")).timestamp()
    except Exception:
        return None


def _load_vscode_claude_usage():
    """The 'long-kudo.vscode-claude-status' VSCode extension's cache. When it
    can't read real limits it writes all-zero utilization with reset times
    equal to its own write time, so a snapshot whose 5h reset isn't in the
    future of its write time is treated as no data."""
    if not os.path.exists(CLAUDE_USAGE_CACHE_PATH):
        return None
    try:
        with open(CLAUDE_USAGE_CACHE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        usage = data.get("usageData") or {}
        updated = _iso_to_epoch(data.get("updatedAt"))
        reset_5h = usage.get("reset5hAt")
        if updated is None or reset_5h is None or reset_5h <= updated + 1:
            return None
        return {
            "utilization_5h": usage.get("utilization5h"),
            "reset_5h_at": reset_5h,
            "utilization_7d": usage.get("utilization7d"),
            "reset_7d_at": usage.get("reset7dAt"),
            "limit_status": usage.get("limitStatus"),
            "updated_at": updated,
            "source": "VSCode Claude Status extension"
        }
    except Exception:
        return None


def _load_session_claude_usage():
    """Written directly (Write tool, no shell) by the scheduled task and by
    handle_update_claude_usage - raw percent + ISO reset times, exactly as
    client.get_usage's "plan" field reports them, no conversion required from
    the writer. Converted to the same shape as the VSCode source here, at
    read time. Freshness comes from the file's own mtime rather than a field
    inside it, so the writer never has to know the current time."""
    if not os.path.exists(CLAUDE_USAGE_SESSION_PATH):
        return None
    try:
        with open(CLAUDE_USAGE_SESSION_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        pct_5h = data.get("percent_5h")
        pct_7d = data.get("percent_7d")
        if pct_5h is None or pct_7d is None:
            return None
        return {
            "utilization_5h": pct_5h / 100.0,
            "reset_5h_at": _iso_to_epoch(data.get("resets_5h_at")),
            "utilization_7d": pct_7d / 100.0,
            "reset_7d_at": _iso_to_epoch(data.get("resets_7d_at")),
            "limit_status": data.get("plan"),
            "updated_at": os.path.getmtime(CLAUDE_USAGE_SESSION_PATH),
            "source": "Claude session"
        }
    except Exception:
        return None


def read_glb_animation_names(glb_path):
    """Return the animation clip names inside a GLB, or [] if unreadable.

    GLB layout: magic(4) version(4) totalLength(4), then per chunk
    chunkLength(4) chunkType(4) data[N]. The chunk length is at file offset 12
    and the type at 16; reading them in the other order compares the length
    against b'JSON' and rejects every valid file. This only reads the JSON
    chunk header, so it costs no more than the clip list itself.

    Deliberately dependency-free (no pygltflib) and never raises: a corrupt or
    truncated animation file should degrade to an empty list, not break the
    catalog endpoint for every other rig.
    """
    try:
        with open(glb_path, "rb") as fh:
            header = fh.read(12)
            if len(header) < 12 or header[0:4] != b"glTF":
                return []
            chunk_header = fh.read(8)
            if len(chunk_header) < 8:
                return []
            chunk_len = struct.unpack("<I", chunk_header[0:4])[0]
            if chunk_header[4:8] != b"JSON":
                return []
            doc = json.loads(fh.read(chunk_len).decode("utf-8"))
    except Exception:
        return []

    out = []
    for anim in (doc.get("animations") or []):
        name = anim.get("name")
        if name:
            out.append(name)
    return out


def count_glb_animation_clips(glb_path):
    """Number of animation clips inside a GLB, or -1 when it cannot be read.

    Distinct from len(read_glb_animation_names(...)) because that helper
    returns [] both for "readable but unauthored" and for "not a GLB at all".
    For ranking a viewer payload those are the same answer (0 clips), so this
    is a thin wrapper that keeps callers from worrying about the difference.
    """
    if not os.path.isfile(glb_path):
        return -1
    return len(read_glb_animation_names(glb_path))


def load_claude_usage():
    """5h/7d plan utilization from whichever source has the freshest real
    snapshot: the VSCode extension's cache or the file a Claude session
    posts. Returns None when neither has usable data."""
    candidates = [c for c in (_load_vscode_claude_usage(), _load_session_claude_usage()) if c]
    if not candidates:
        return None
    return max(candidates, key=lambda c: c.get("updated_at") or 0)


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


# --- Asset change tracker -------------------------------------------------
# Tracks which cataloged assets have changed on disk since the last time
# `tools/package_catalog_as_mods.py` ran, so the status bar can show a live
# "N changed" count and let the user re-import on demand instead of guessing
# whether mods/ is stale. Mirrors the packager's own category/extension
# rules exactly (same EXCLUDED_CATEGORIES, same VALID_EXTENSIONS) so the
# tracked set always matches what actually gets packaged.
MOD_IMPORT_STATE_PATH = os.path.join(BASE_DIR, "_mod_import_state.json")
TRACKER_EXCLUDED_CATEGORIES = {"ground", "hud", "hud_kit", "peds", "models_legacy", "textures"}
TRACKER_VALID_EXTENSIONS = {
    ".json", ".png", ".jpg", ".jpeg", ".tga",
    ".fbx", ".obj", ".glb", ".gltf", ".mtl",
    ".mat", ".anim", ".controller", ".txt", ".md"
}


def scan_tracked_asset_files():
    """{"<category>/<item_id>/<relative file path>": mtime} for every packaged file."""
    files = {}
    if not os.path.isdir(BASE_DIR):
        return files
    for cat in sorted(os.listdir(BASE_DIR)):
        if cat.startswith("_") or cat in TRACKER_EXCLUDED_CATEGORIES:
            continue
        cat_dir = os.path.join(BASE_DIR, cat)
        if not os.path.isdir(cat_dir):
            continue
        for item in sorted(os.listdir(cat_dir)):
            if item.endswith(".disabled"):
                continue
            item_dir = os.path.join(cat_dir, item)
            if not os.path.isdir(item_dir):
                continue
            for root, _dirs, fnames in os.walk(item_dir):
                for fname in fnames:
                    if os.path.splitext(fname)[1].lower() not in TRACKER_VALID_EXTENSIONS:
                        continue
                    full = os.path.join(root, fname)
                    rel = os.path.relpath(full, BASE_DIR).replace(os.sep, "/")
                    try:
                        files[rel] = os.path.getmtime(full)
                    except OSError:
                        pass
    return files


def load_mod_import_state():
    if not os.path.exists(MOD_IMPORT_STATE_PATH):
        return {"last_import_at": None, "files": {}}
    try:
        with open(MOD_IMPORT_STATE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"last_import_at": None, "files": {}}


def save_mod_import_state(files):
    state = {"last_import_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "files": files}
    with open(MOD_IMPORT_STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f)
    return state


def compute_asset_changes():
    """Returns (items, last_import_at). items is a sorted list of
    {"category", "item_id", "changes": ["added"|"modified"|"deleted", ...]}."""
    state = load_mod_import_state()
    baseline = state.get("files", {})
    current = scan_tracked_asset_files()

    changed = {}  # (category, item_id) -> set of change kinds

    def mark(rel, kind):
        parts = rel.split("/", 2)
        if len(parts) < 2:
            return
        key = (parts[0], parts[1])
        changed.setdefault(key, set()).add(kind)

    for rel, mtime in current.items():
        old = baseline.get(rel)
        if old is None:
            mark(rel, "added")
        elif abs(old - mtime) > 1:
            mark(rel, "modified")
    for rel in baseline:
        if rel not in current:
            mark(rel, "deleted")

    items = [
        {"category": cat, "item_id": item, "changes": sorted(kinds)}
        for (cat, item), kinds in changed.items()
    ]
    items.sort(key=lambda r: (r["category"], r["item_id"]))
    return items, state.get("last_import_at")


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


def rewrite_tag_references(old_name, new_name):
    """After a tag rename: every manifest that names the tag as "#old" (recipe item ids, yield tools, ...) now names
    "#new", in the asset kit (assets/) and the packaged core mod (Homesteader/mods/). The mod copy of the tag registry
    (tags.json) gets the key renamed too. Returns the list of files changed."""
    needle = '"#' + old_name + '"'
    repl = '"#' + new_name + '"'
    repo = os.path.dirname(BASE_DIR)
    changed = []
    for top in (BASE_DIR, os.path.join(repo, "Homesteader", "mods")):
        for dirpath, dirnames, filenames in os.walk(top):
            dirnames[:] = [d for d in dirnames if d not in ("node_modules", ".git", "_asset_requests")]
            for fn in filenames:
                if not fn.endswith(".json"):
                    continue
                path = os.path.join(dirpath, fn)
                if os.path.abspath(path) == os.path.abspath(MATERIAL_TAGS_PATH):
                    continue
                try:
                    with open(path, "r", encoding="utf-8", newline="") as f:
                        text = f.read()
                except Exception:
                    continue
                if fn == "tags.json":
                    try:
                        data = json.loads(text)
                    except Exception:
                        continue
                    tags = data.get("tags")
                    if isinstance(tags, dict) and old_name in tags and new_name not in tags:
                        data["tags"] = {(new_name if k == old_name else k): v for k, v in tags.items()}
                        with open(path, "w", encoding="utf-8", newline="") as f:
                            f.write(json.dumps(data, indent=2, ensure_ascii=False) + ("\n" if text.endswith("\n") else ""))
                        changed.append(path)
                    continue
                if needle in text:
                    with open(path, "w", encoding="utf-8", newline="") as f:
                        f.write(text.replace(needle, repl))
                    changed.append(path)
    return changed


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


def push_growth_group(species_key):
    """Pushes every stage of a growth group into the game as part of the 'homesteader' mod. A
    growth group has no asset folder of its own - it's just the set of catalog items sharing this
    species tag (see save_growth_group) - so "pushing the group" means pushing each member stage
    via push_to_game.push_item, same as the per-item Push to Game button. One member failing (e.g.
    a stage folder switched off with .disabled) doesn't stop the rest."""
    species_key = (species_key or "").strip().lower()
    if not species_key:
        raise ValueError("Missing species key")
    members = find_items_with_species(species_key)
    if not members:
        raise ValueError(f"No member items found for growth group '{species_key}'")

    pushed, skipped, notes = [], [], []
    for cat, item_id in members:
        try:
            result = push_to_game.push_item(cat, item_id)
        except Exception as e:
            skipped.append({"category": cat, "item_id": item_id, "error": str(e)})
            continue
        if result.get("pushed"):
            pushed.append({"category": cat, "item_id": item_id})
        else:
            skipped.append({"category": cat, "item_id": item_id, "notes": result.get("notes")})
        notes.extend(result.get("notes", []))

    message = f"Pushed {len(pushed)}/{len(members)} stage(s) of '{species_key}' into the game."
    if pushed:
        message += " Restart Play (Unity re-reads mods when Play starts)."
    return {"species": species_key, "pushed": pushed, "skipped": skipped, "notes": notes, "message": message}


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
        if self.path.startswith("/api/animations"):
            self.handle_animation_catalog()
            return
        if self.path == "/api/meshy-balance":
            self.handle_meshy_balance()
            return
        if self.path == "/api/claude-usage":
            self.handle_claude_usage()
            return
        if self.path == "/api/watcher-status":
            self.handle_watcher_status()
            return
        if self.path == "/api/asset-changes":
            self.handle_asset_changes()
            return
        if self.path == "/api/asset-requests":
            self.handle_list_asset_requests()
            return
        if self.path == "/api/trash":
            self.handle_list_trash()
            return
        # /api/docs             -> list every doc
        # /api/docs/x.md        -> one doc's markdown (path form)
        # /api/docs?slug=x.md   -> one doc's markdown (query form)
        if self.path == "/api/docs":
            self.handle_list_docs()
            return
        if self.path == "/api/guides":
            self.handle_list_guides()
            return
        if self.path.startswith("/api/guides/") or self.path.startswith("/api/guides?"):
            self.handle_get_guide()
            return
        if self.path.startswith("/api/docs/") or self.path.startswith("/api/docs?"):
            self.handle_get_doc()
            return
        if self.path == "/api/growth-groups":
            self.handle_get_growth_groups()
            return
        if self.path == "/api/material-tags":
            self.handle_get_material_tags()
            return
        if self.path == "/api/biomes" or self.path.startswith("/api/biomes?"):
            self.handle_get_biomes()
            return
        if self.path == "/api/animal-ai" or self.path.startswith("/api/animal-ai?"):
            self.handle_get_animal_ai()
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
        if self.path.startswith("/api/group-stages?"):
            self.handle_group_stages()
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

    def handle_group_stages(self):
        """Lists the stage folders of one growth group (stages/<folder>/) with the model + icon each holds,
        so the group editor can pick a withered / dead / stump version visually."""
        try:
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            category = (q.get("category") or [""])[0].strip().lower()
            group_id = (q.get("group_id") or [""])[0].strip().lower()
            if category not in ALLOWED_CATEGORIES or not group_id or ".." in group_id or "/" in group_id or "\\" in group_id:
                self.send_json_response({"success": False, "error": "bad category or group_id"}, 400)
                return
            stages_dir = os.path.join(BASE_DIR, category, group_id, "stages")
            out = []
            if os.path.isdir(stages_dir):
                for folder in sorted(os.listdir(stages_dir)):
                    if not os.path.isdir(os.path.join(stages_dir, folder)):
                        continue
                    resource = f"stages/{folder}/"
                    entry = build_stage_entry(category, group_id, resource)
                    if not entry or not entry.get("models"):
                        continue
                    models = entry["models"]
                    chosen = next((m for m in models if str(m["file"]).lower().endswith(".glb")), models[0])
                    icon_file = os.path.basename(entry["icon"]) if entry.get("icon") else ""
                    out.append({
                        "resource": resource,
                        "id": entry["id"],
                        "name": entry["name"],
                        "model": chosen["file"],
                        "icon": icon_file,
                        "icon_path": entry.get("icon"),
                    })
            self.send_json_response({"success": True, "stages": out}, 200)
        except Exception as e:
            self.send_json_response({"success": False, "error": str(e)}, 500)

    def handle_ping(self):
        self.send_json_response({"success": True, "status": "online"}, 200)

    def handle_animation_catalog(self):
        """List every animation clip available locally from the Mesh2Motion rigs.

        The rig-request dialogs used to be free-text fields with a note saying
        there was no local catalog to pick from. That is no longer true: the
        Mesh2Motion checkout ships animation GLBs for each rig type, so this
        endpoint reads their glTF JSON chunks and reports the real clip names.

        Supported formats:
          ?rig=human          -> only that rig's clips (also accepts 'all')
          (no query)          -> every rig, grouped by rig, plus a flat sorted
                                 list of unique names for a picker UI.
        """
        try:
            query = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        except Exception:
            query = {}
        want_rig = (query.get("rig", ["all"])[0] or "all").strip().lower()

        anims_dir = os.path.join(PROJECT_DIR, "tools", "mesh2motion", "static", "animations")
        if not os.path.isdir(anims_dir):
            self.send_json_response({
                "success": False,
                "error": "Mesh2Motion animation catalog not found: " + anims_dir,
                "hint": "Clone the Mesh2Motion app into tools/mesh2motion.",
            }, 404)
            return

        rigs = []
        all_names = set()
        for fname in sorted(os.listdir(anims_dir)):
            if not fname.lower().endswith(".glb"):
                continue
            # Filenames look like human-base-animations.glb, fox-animations.glb.
            stem = fname[:-4]
            rig_key = stem.split("-")[0].strip().lower()
            if want_rig not in ("all", "", rig_key):
                continue

            full = os.path.join(anims_dir, fname)
            names = read_glb_animation_names(full)
            all_names.update(names)
            rigs.append({
                "rig": rig_key,
                "file": fname,
                "path": full,
                "clip_count": len(names),
                "clips": names,
            })

        total = sum(r["clip_count"] for r in rigs)
        self.send_json_response({
            "success": True,
            "source": anims_dir,
            "rig_filter": want_rig,
            "rigs": rigs,
            "unique_names": sorted(all_names),
            "unique_count": len(all_names),
            "total_clips": total,
        }, 200)

    def handle_meshy_balance(self):
        try:
            balance = fetch_meshy_balance()
            self.send_json_response({"success": True, "balance": balance}, 200)
        except Exception as e:
            self.send_json_response({"success": False, "error": str(e)}, 502)

    def handle_claude_usage(self):
        data = load_claude_usage()
        if data is None:
            self.send_json_response({"success": False, "error": "No Claude usage recorded yet - a Claude session posts it to /api/claude-usage"}, 404)
            return
        self.send_json_response({"success": True, **data}, 200)

    def handle_watcher_status(self):
        data = load_watcher_status()
        self.send_json_response({"success": True, **data}, 200)

    def handle_asset_changes(self):
        items, last_import_at = compute_asset_changes()
        self.send_json_response({
            "success": True,
            "count": len(items),
            "last_import_at": last_import_at,
            "items": items,
        }, 200)

    def handle_import_mods(self):
        """Runs the same packaging pass a developer would run by hand
        (package_catalog_as_mods.py, update_catalog_readme.py) so mods/ is
        current. mods/ is the ONLY sync target - it lives outside Assets/, so
        Unity's AssetDatabase never touches it, and the Editor already reads
        it live at runtime via a relative path in ModManager.cs (dataPath/../../mods).
        Do NOT also copy into Assets/Mods: that folder IS inside Assets/, so
        Unity's importer would choke trying to import gigabytes of GLBs."""
        try:
            items, _ = compute_asset_changes()
            log = []

            # The game's own item list first (Assets/Resources/AssetCatalog.json: names, stack sizes, containers, fruiting rules ...).
            cat = subprocess.run(
                [sys.executable, os.path.join(SCRIPT_DIR, "generate_unity_asset_catalog.py")],
                capture_output=True, text=True, timeout=180
            )
            log.append(cat.stdout[-500:] if cat.stdout else "")
            if cat.returncode != 0:
                self.send_json_response({
                    "success": False,
                    "error": "generate_unity_asset_catalog.py failed",
                    "details": (cat.stderr or cat.stdout)[-2000:],
                }, 500)
                return

            pkg = subprocess.run(
                [sys.executable, os.path.join(SCRIPT_DIR, "package_catalog_as_mods.py")],
                capture_output=True, text=True, timeout=180
            )
            log.append(pkg.stdout[-2000:] if pkg.stdout else "")
            if pkg.returncode != 0:
                self.send_json_response({
                    "success": False,
                    "error": "package_catalog_as_mods.py failed",
                    "details": (pkg.stderr or pkg.stdout)[-2000:],
                }, 500)
                return

            readme = subprocess.run(
                [sys.executable, os.path.join(SCRIPT_DIR, "update_catalog_readme.py")],
                capture_output=True, text=True, timeout=60
            )
            log.append(readme.stdout[-500:] if readme.stdout else "")

            new_files = scan_tracked_asset_files()
            save_mod_import_state(new_files)

            self.send_json_response({
                "success": True,
                "items_imported": len(items),
                "log": "\n".join(l for l in log if l),
            }, 200)
        except subprocess.TimeoutExpired:
            self.send_json_response({"success": False, "error": "Import timed out"}, 500)
        except Exception as e:
            print(f"Error importing mods: {e}")
            self.send_json_response({"success": False, "error": str(e)}, 500)

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

            # `resource` is set when the caller wants ONE stage of a growth
            # group: `id` is then the group, and the stage is a resource
            # folder inside it rather than a catalog asset of its own.
            resource = (params.get('resource', [''])[0]).strip()
            entry = (build_stage_entry(category, item_id, resource) if resource
                     else build_catalog_entry(category, item_id))
            if entry is None:
                what = f"{category}/{item_id}/{resource}" if resource else f"{category}/{item_id}"
                self.send_json_response({"success": False, "error": f"Asset not found: {what}"}, 404)
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

            # `resource` targets ONE growth stage: `id` is then the group and
            # the stage's files live in the group's own stages/ subfolder.
            resource = (params.get('resource', [''])[0]).strip()
            if resource and (".." in resource or "\\" in resource):
                self.send_json_response({"success": False, "error": "Invalid resource"}, 400)
                return
            item_dir = os.path.join(BASE_DIR, category, item_id)
            if resource:
                item_dir = os.path.join(item_dir, resource.replace("/", os.sep).strip(os.sep))
            if not os.path.isdir(item_dir):
                what = f"{category}/{item_id}/{resource}" if resource else f"{category}/{item_id}"
                self.send_json_response({"success": False, "error": f"Asset not found: {what}"}, 404)
                return
            # Paths are relative to the ASSETS root so the browser can fetch
            # them; for a stage that includes the group + resource segments.
            rel_dir = f"{category}/{item_id}"
            if resource:
                rel_dir += "/" + resource.strip("/")
            files = []
            for fname in sorted(os.listdir(item_dir)):
                fpath = os.path.join(item_dir, fname)
                if not os.path.isfile(fpath):
                    continue
                files.append({
                    "name": fname,
                    "size": os.path.getsize(fpath),
                    "path": f"{rel_dir}/{fname}"
                })

            self.send_json_response({"success": True, "files": files, "folder": rel_dir}, 200)
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
        elif self.path == "/api/trash/restore":
            self.handle_trash_restore()
        elif self.path == "/api/trash/purge":
            self.handle_trash_purge()
        elif self.path == "/api/trash/purge-all":
            self.handle_trash_purge_all()
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
        elif self.path == "/api/save-biome":
            self.handle_save_biome()
        elif self.path == "/api/schema/save":
            self.handle_save_schema()
        elif self.path == "/api/delete-material-tag":
            self.handle_delete_material_tag()
        elif self.path == "/api/rename-material-tag":
            self.handle_rename_material_tag()
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
        elif self.path == "/api/claude-usage":
            self.handle_update_claude_usage()
        elif self.path == "/api/import-mods":
            self.handle_import_mods()
        elif self.path == "/api/invalidate-catalog-cache":
            self.handle_invalidate_catalog_cache()
        elif self.path == "/api/growth-groups":
            self.handle_save_growth_group()
        elif self.path == "/api/save-group-scheme":
            self.handle_save_group_scheme()
        elif self.path == "/api/save-manifest":
            self.handle_save_manifest()
        elif self.path == "/api/save-economy":
            self.handle_save_economy()
        elif self.path == "/api/save-animal-ai":
            self.handle_save_animal_ai()
        elif self.path == "/api/validate-animal-ai":
            self.handle_validate_animal_ai()
        elif self.path == "/api/push-to-game":
            self.handle_push_to_game()
        elif self.path == "/api/push-growth-group":
            self.handle_push_growth_group()
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
            # Soft delete: move the folder into assets/_trash/ rather than
            # rmtree-ing it, so it stays restorable from the status-bar Trash
            # panel. Permanent deletion is now an explicit action there.
            ok, result = trash_store.move_to_trash(BASE_DIR, category, item_id)
            if not ok:
                self.send_json_response({"success": False, "error": result}, 500)
                return
            print(f"[DELETE REQUEST] Moved to trash: {target_dir} -> {result['trash_id']}")

            remove_items_from_embedded_catalog([{"category": category, "item_id": item_id}])

            # Trigger background or fast catalog README update
            try:
                update_script = os.path.join(SCRIPT_DIR, "update_catalog_readme.py")
                if os.path.exists(update_script):
                    subprocess.Popen([sys.executable, update_script])
            except Exception as e:
                print(f"Warning updating README: {e}")

            self.send_json_response({
                "success": True,
                "message": f"Asset '{item_id}' in '{category}' was moved to trash - restore it from the Trash panel.",
                "item_id": item_id,
                "category": category,
                "trash_id": result["trash_id"]
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
                    # Soft delete - see handle_delete_asset.
                    ok, result = trash_store.move_to_trash(BASE_DIR, cat, iid)
                    if ok:
                        deleted.append({"category": cat, "item_id": iid, "trash_id": result["trash_id"]})
                    else:
                        errors.append(f"Failed to trash {cat}/{iid}: {result}")
                else:
                    errors.append(f"Not found: {cat}/{iid}")

            print(f"[BATCH DELETE] Moved {len(deleted)} assets to trash. Errors: {len(errors)}")

            remove_items_from_embedded_catalog(deleted)

            # Update catalog README once in background
            try:
                update_script = os.path.join(SCRIPT_DIR, "update_catalog_readme.py")
                if os.path.exists(update_script):
                    subprocess.Popen([sys.executable, update_script])
            except Exception as e:
                print(f"Warning updating README: {e}")

            self.send_json_response({
                "success": True,
                "message": f"Moved {len(deleted)} assets to trash - restore them from the Trash panel.",
                "deleted_count": len(deleted),
                "deleted": deleted,
                "errors": errors
            }, 200)

        except Exception as e:
            print(f"Error in batch delete: {e}")
            self.send_json_response({"success": False, "error": str(e)}, 500)

    # ------------------------------------------------------------------
    # Docs API - backs the status-bar "Docs" button.
    #
    # Each doc is a markdown file in assets/_docs/, fronted by a tiny heading
    # block (see _read_doc_meta) so the section list can show a title and icon
    # without shipping a separate manifest that could drift from the files.
    # ------------------------------------------------------------------

    def handle_list_docs(self):
        """Lists every markdown file in assets/_docs/, in filename order
        (the numeric prefixes are the intended reading order)."""
        try:
            docs = []
            if os.path.isdir(DOCS_DIR):
                for fname in sorted(os.listdir(DOCS_DIR)):
                    if not fname.lower().endswith(".md"):
                        continue
                    meta = _read_doc_meta(os.path.join(DOCS_DIR, fname))
                    docs.append({
                        "slug": fname,
                        "title": meta["title"],
                        "icon": meta["icon"],
                        "summary": meta["summary"],
                    })
            self.send_json_response({"success": True, "count": len(docs), "docs": docs}, 200)
        except Exception as e:
            print(f"Error listing docs: {e}")
            self.send_json_response({"success": False, "error": str(e)}, 500)

    def handle_get_doc(self):
        """Returns one doc's raw markdown. The slug is basename-only and
        validated, so a crafted path can't escape the docs folder."""
        try:
            query = urllib.parse.urlparse(self.path).query
            params = urllib.parse.parse_qs(query)
            slug = (params.get("slug", [""])[0]).strip()
            if not slug:
                # Allow /api/docs/<filename> as well as ?slug=<filename>.
                slug = os.path.basename(urllib.parse.urlparse(self.path).path)

            if not slug or "/" in slug or "\\" in slug or ".." in slug:
                self.send_json_response({"success": False, "error": "Invalid doc slug"}, 400)
                return
            if not slug.lower().endswith(".md"):
                slug += ".md"

            doc_path = os.path.join(DOCS_DIR, slug)
            if not os.path.isfile(doc_path):
                self.send_json_response({"success": False, "error": f"Doc not found: {slug}"}, 404)
                return
            with open(doc_path, "r", encoding="utf-8") as f:
                markdown = f.read()

            self.send_json_response({"success": True, "slug": slug, "markdown": markdown}, 200)
        except Exception as e:
            print(f"Error reading doc: {e}")
            self.send_json_response({"success": False, "error": str(e)}, 500)

    # ------------------------------------------------------------------
    # Guides API - serves the authoritative project guides (docs/ and
    # assets/) that the MCP server also exposes. The list comes from
    # asset_kit_mcp.GUIDE_FILES, so it cannot drift from the agent-facing set.
    # ------------------------------------------------------------------

    def handle_list_guides(self):
        """Lists every active guide, grouped by source folder, with whether the
        file exists on disk (a guide in the list but missing is surfaced rather
        than silently omitted)."""
        try:
            guides = []
            for display in ACTIVE_GUIDES:
                entry = GUIDE_FILES.get(display)
                if not entry:
                    continue
                root, rel = entry
                full = os.path.join(root, rel)
                exists = os.path.isfile(full)
                guides.append({
                    "name": display,
                    "group": display.split("/", 1)[0],
                    "basename": os.path.basename(rel),
                    "exists": exists,
                    "size_bytes": os.path.getsize(full) if exists else 0,
                })
            self.send_json_response({
                "success": True,
                "count": len(guides),
                "guides": guides,
            }, 200)
        except Exception as e:
            print(f"Error listing guides: {e}")
            self.send_json_response({"success": False, "error": str(e)}, 500)

    def handle_get_guide(self):
        """Returns one guide's raw markdown, looked up by its display name
        (e.g. 'docs/ITEM_ICON_STYLE_GUIDE.md'). Only names present in the
        ACTIVE_GUIDES whitelist are served, so no path can escape the two
        guide roots."""
        try:
            query = urllib.parse.urlparse(self.path).query
            params = urllib.parse.parse_qs(query)
            name = (params.get("name", [""])[0]).strip()
            if not name:
                name = urllib.parse.unquote(os.path.basename(urllib.parse.urlparse(self.path).path))

            # Resolve against the whitelist rather than the filesystem: a
            # crafted name simply won't match, so there is nothing to traverse.
            wanted = name.replace("\\", "/").strip().lower()
            display = next((d for d in ACTIVE_GUIDES if d.lower() == wanted), None)
            if display is None:
                # Allow a bare basename when it is unambiguous.
                base = os.path.basename(wanted)
                matches = [d for d in ACTIVE_GUIDES if os.path.basename(d).lower() == base]
                if len(matches) == 1:
                    display = matches[0]
                elif len(matches) > 1:
                    self.send_json_response({
                        "success": False,
                        "error": f"Ambiguous guide name '{name}'.",
                        "candidates": matches,
                    }, 400)
                    return

            if display is None:
                self.send_json_response({
                    "success": False,
                    "error": f"Unknown guide '{name}'.",
                }, 404)
                return

            root, rel = GUIDE_FILES[display]
            full = os.path.join(root, rel)
            if not os.path.isfile(full):
                self.send_json_response({
                    "success": False,
                    "error": f"Guide file missing on disk: {rel}",
                }, 404)
                return

            with open(full, "r", encoding="utf-8", errors="replace") as f:
                markdown = f.read()

            self.send_json_response({
                "success": True,
                "name": display,
                "group": display.split("/", 1)[0],
                "markdown": markdown,
            }, 200)
        except Exception as e:
            print(f"Error reading guide: {e}")
            self.send_json_response({"success": False, "error": str(e)}, 500)

    # ------------------------------------------------------------------
    # Trash (soft delete) API - backs the status-bar trash can.
    # ------------------------------------------------------------------

    def handle_list_trash(self):
        """Lists every soft-deleted asset, newest first, for the Trash panel."""
        try:
            records = trash_store.list_trash(BASE_DIR)
            total_bytes = sum((r.get("size_bytes") or 0) for r in records)
            self.send_json_response({
                "success": True,
                "count": len(records),
                "total_bytes": total_bytes,
                "items": records,
            }, 200)
        except Exception as e:
            print(f"Error listing trash: {e}")
            self.send_json_response({"success": False, "error": str(e)}, 500)

    def handle_trash_restore(self):
        """Restores the given trashed items back to their original category
        folders. Reports per-item failures rather than failing the whole
        batch, so one name collision doesn't block the others."""
        try:
            content_len = int(self.headers.get("Content-Length", 0))
            data = json.loads(self.rfile.read(content_len).decode("utf-8")) if content_len else {}
            trash_ids = data.get("trash_ids", [])
            if not trash_ids or not isinstance(trash_ids, list):
                self.send_json_response({"success": False, "error": "No trash_ids provided"}, 400)
                return
            restored = []
            errors = []
            for trash_id in trash_ids:
                ok, result = trash_store.restore_from_trash(BASE_DIR, trash_id)
                if ok:
                    restored.append(result)
                else:
                    errors.append(result)

            if restored:
                invalidate_catalog_cache()

            print(f"[TRASH RESTORE] Restored {len(restored)} item(s). Errors: {len(errors)}")
            self.send_json_response({
                "success": True,
                "restored_count": len(restored),
                "restored": restored,
                "errors": errors,
            }, 200)
        except Exception as e:
            print(f"Error restoring from trash: {e}")
            self.send_json_response({"success": False, "error": str(e)}, 500)

    def handle_trash_purge(self):
        """Permanently deletes the given trashed items (rmtree). This is the
        only path in the app that actually destroys asset data."""
        try:
            content_len = int(self.headers.get("Content-Length", 0))
            data = json.loads(self.rfile.read(content_len).decode("utf-8")) if content_len else {}
            trash_ids = data.get("trash_ids", [])
            if not trash_ids or not isinstance(trash_ids, list):
                self.send_json_response({"success": False, "error": "No trash_ids provided"}, 400)
                return
            purged, errors = trash_store.purge_from_trash(BASE_DIR, trash_ids)
            print(f"[TRASH PURGE] Permanently deleted {purged} item(s). Errors: {len(errors)}")
            self.send_json_response({
                "success": True,
                "purged_count": purged,
                "errors": errors,
            }, 200)
        except Exception as e:
            print(f"Error purging trash: {e}")
            self.send_json_response({"success": False, "error": str(e)}, 500)

    def handle_trash_purge_all(self):
        """Empties the trash entirely - the 'Delete All' button."""
        try:
            purged, errors = trash_store.purge_all(BASE_DIR)
            print(f"[TRASH PURGE ALL] Permanently deleted {purged} item(s). Errors: {len(errors)}")
            self.send_json_response({
                "success": True,
                "purged_count": purged,
                "errors": errors,
            }, 200)
        except Exception as e:
            print(f"Error emptying trash: {e}")
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
                update_script = os.path.join(SCRIPT_DIR, "update_catalog_readme.py")
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
                update_script = os.path.join(SCRIPT_DIR, "update_catalog_readme.py")
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
                update_script = os.path.join(SCRIPT_DIR, "update_catalog_readme.py")
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
                update_script = os.path.join(SCRIPT_DIR, "update_catalog_readme.py")
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
                update_script = os.path.join(SCRIPT_DIR, "update_catalog_readme.py")
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
            # kit_config.json only ever held a thin copy of each group
            # (name/icon/growth_type/max_age/time_unit + stages of
            # {stage,name,item_id,age_min,age_max}). The group's own manifest
            # is AUTHORITATIVE for its scheme, and for a migrated group it is
            # the only place a stage's icon/model/resource are recorded - the
            # stages[] array in the manifest is richer than the stored copy.
            # Overlay it here so the frontend's GROWTH_GROUPS entries carry the
            # real per-stage icon and model instead of rendering blank thumbs.
            # kit_config.json itself is left untouched: it stays the migration
            # record, and this overlay is derived fresh on every request.
            for key, grp in (cfg.get("growth_groups") or {}).items():
                if not isinstance(grp, dict):
                    continue
                category = grp.get("category")
                if not category:
                    continue
                manifest = read_growth_group_manifest(category, key)
                if not manifest:
                    continue
                growth = manifest.get("growth")
                if not isinstance(growth, dict):
                    continue
                # Manifest wins for every scheme field it declares; the stored
                # copy still supplies anything the manifest omits.
                merged = dict(grp)
                merged["name"] = manifest.get("name") or grp.get("name")
                merged["category"] = category
                for field in ("growth_type", "species", "max_age", "time_unit",
                              "total_stages", "icon_stage", "stages", "rules"):
                    if growth.get(field) is not None:
                        merged[field] = growth[field]
                cfg["growth_groups"][key] = merged
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

    def handle_get_biomes(self):
        """Lists all biomes from assets/biomes/ and aggregates associated catalog assets (via spawning.biomes)."""
        try:
            biomes = []
            if os.path.isdir(BIOMES_DIR):
                for fname in sorted(os.listdir(BIOMES_DIR)):
                    if not fname.endswith(".json"):
                        continue
                    bpath = os.path.join(BIOMES_DIR, fname)
                    try:
                        with open(bpath, "r", encoding="utf-8") as bf:
                            bdata = json.load(bf)
                            biomes.append(bdata)
                    except Exception as err:
                        print(f"Warning loading biome {fname}: {err}")

            # Sort biomes by priority descending (e.g. 10 Pond down to 1 Meadow)
            biomes.sort(key=lambda b: b.get("priority", 0), reverse=True)

            # Inverted resolution: Scan catalog items to populate dynamic spawning assets per biome
            catalog = get_cached_catalog()
            biome_assets = {b.get("id"): [] for b in biomes if b.get("id")}
            for item in catalog:
                manifest = item.get("manifest", {})
                spawning = manifest.get("spawning") or item.get("spawning")
                if isinstance(spawning, dict):
                    target_biomes = spawning.get("biomes", [])
                    for bid in target_biomes:
                        if bid in biome_assets:
                            biome_assets[bid].append({
                                "asset_id": item.get("id"),
                                "name": item.get("name"),
                                "category": item.get("category"),
                                "icon": item.get("icon"),
                                "spawning": spawning
                            })

            for b in biomes:
                bid = b.get("id")
                b["associated_assets"] = biome_assets.get(bid, [])

            self.send_json_response({"success": True, "biomes": biomes, "count": len(biomes)}, 200)
        except Exception as e:
            print(f"Error fetching biomes: {e}")
            self.send_json_response({"success": False, "error": str(e)}, 500)

    def handle_save_biome(self):
        """Saves or updates a biome manifest in assets/biomes/<id>.json."""
        try:
            content_len = int(self.headers.get("Content-Length", 0))
            post_body = self.rfile.read(content_len)
            data = json.loads(post_body.decode("utf-8")) if content_len > 0 else {}

            biome_id = (data.get("id") or "").strip().lower()
            if not biome_id or not biome_id.startswith("biome_"):
                self.send_json_response({"success": False, "error": "Biome ID must start with 'biome_'"}, 400)
                return

            safe_id = "".join(c for c in biome_id if c.isalnum() or c == "_")
            os.makedirs(BIOMES_DIR, exist_ok=True)
            target_file = os.path.join(BIOMES_DIR, f"{safe_id}.json")

            with open(target_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.write("\n")

            print(f"[SAVE BIOME] {safe_id} (priority: {data.get('priority', 0)})")
            self.send_json_response({"success": True, "biome": data, "path": f"biomes/{safe_id}.json"}, 200)
        except Exception as e:
            print(f"Error saving biome: {e}")
            self.send_json_response({"success": False, "error": str(e)}, 500)


    def handle_get_animal_ai(self):
        """Lists the animal AI definitions in assets/_ai (or returns one with ?id=), with validation results.
        The asset editor uses this to fill its "AI profile" dropdown."""
        try:
            query = urllib.parse.urlparse(self.path).query
            params = urllib.parse.parse_qs(query)
            ai_id = (params.get("id", [""])[0]).strip()
            if ai_id:
                defn = animal_ai.get_profile(BASE_DIR, ai_id)
                if defn is None:
                    self.send_json_response({"success": False, "error": f"No AI profile '{ai_id}'"}, 404)
                    return
                errors, warnings = animal_ai.validate(defn, BASE_DIR)
                self.send_json_response({"success": True, "definition": defn, "errors": errors, "warnings": warnings}, 200)
                return
            self.send_json_response({"success": True, "profiles": animal_ai.list_profiles(BASE_DIR)}, 200)
        except Exception as e:
            self.send_json_response({"success": False, "error": str(e)}, 500)

    def handle_push_to_game(self):
        """Pushes one asset into the game as part of the 'homesteader' mod (tools/push_to_game.py): copies its
        folder to Homesteader/mods/homesteader/<category>/<id>/, writes an animal's AI, and refreshes the in-game
        asset list. Body: {"category": ..., "item_id": ...}."""
        try:
            content_len = int(self.headers.get("Content-Length", 0))
            data = json.loads(self.rfile.read(content_len).decode("utf-8")) if content_len > 0 else {}
            result = push_to_game.push_item(data.get("category"), data.get("item_id"))
            print(f"[PUSH TO GAME] {data.get('category')}/{data.get('item_id')} -> {result.get('pushed')}")
            self.send_json_response({"success": True, **result}, 200)
        except (ValueError, FileNotFoundError, RuntimeError) as e:
            self.send_json_response({"success": False, "error": str(e)}, 400)
        except Exception as e:
            self.send_json_response({"success": False, "error": str(e)}, 500)

    def handle_push_growth_group(self):
        """Pushes every stage of a growth group into the game as the 'homesteader' mod (see
        push_growth_group above): one tools/push_to_game.push_item call per member item, so it
        reuses the same per-item copy/version-bump/catalog-refresh path the single Push to Game
        button already uses. Body: {"species": ...}."""
        try:
            content_len = int(self.headers.get("Content-Length", 0))
            data = json.loads(self.rfile.read(content_len).decode("utf-8")) if content_len > 0 else {}
            result = push_growth_group(data.get("species"))
            print(f"[PUSH GROWTH GROUP] {data.get('species')} -> {len(result['pushed'])} pushed, {len(result['skipped'])} skipped")
            self.send_json_response({"success": True, **result}, 200)
        except ValueError as e:
            self.send_json_response({"success": False, "error": str(e)}, 400)
        except Exception as e:
            self.send_json_response({"success": False, "error": str(e)}, 500)

    def handle_validate_animal_ai(self):
        """Validates an animal AI definition (e.g. the one embedded in an animal's manifest) without saving it."""
        try:
            content_len = int(self.headers.get("Content-Length", 0))
            data = json.loads(self.rfile.read(content_len).decode("utf-8")) if content_len > 0 else {}
            errors, warnings = animal_ai.validate(data.get("definition"), BASE_DIR)
            self.send_json_response({"success": True, "errors": errors, "warnings": warnings}, 200)
        except Exception as e:
            self.send_json_response({"success": False, "error": str(e)}, 500)

    def handle_save_animal_ai(self):
        """Validates and saves an animal AI definition to assets/_ai/<id>.json. Body: {"definition": {...}}.
        Errors (unknown need, bad action type, ...) reject the save; warnings are returned."""
        try:
            content_len = int(self.headers.get("Content-Length", 0))
            data = json.loads(self.rfile.read(content_len).decode("utf-8")) if content_len > 0 else {}
            defn = data.get("definition")
            ok, errors, warnings = animal_ai.save_profile(BASE_DIR, defn)
            if not ok:
                self.send_json_response({"success": False, "errors": errors, "warnings": warnings}, 400)
                return
            print(f"[SAVE ANIMAL AI] {defn['id']}")
            self.send_json_response({"success": True, "id": defn["id"], "warnings": warnings}, 200)
        except Exception as e:
            self.send_json_response({"success": False, "error": str(e)}, 500)

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
                            "note": sdata.get("note", ""),
                            "component": bool(sdata.get("component", False)),
                            "title": sdata.get("title", name),
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
            # Defined up front: both schema families live side by side in this
            # one directory, and the group schema is referenced below even when
            # the directory is missing, so it must exist as a name either way.
            growth_group_schema = None
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
                # The growth_group schema is CROSS-CUTTING: it applies to any
                # manifest with is_growable:true regardless of category, so it
                # is not named after a category and the lookup above never
                # found it. Load it explicitly and apply it only to growable
                # manifests (see the is_growable gate at the call site).
                gg_file = os.path.join(schemas_dir, "growth_group.schema.json")
                growth_group_schema = None
                if os.path.exists(gg_file):
                    try:
                        with open(gg_file, "r", encoding="utf-8") as gf:
                            growth_group_schema = json.load(gf)
                    except Exception:
                        growth_group_schema = None

            # Component (add-on) schemas: validated only on assets that carry their block.
            component_schemas = []
            try:
                for cfname in sorted(os.listdir(schemas_dir)):
                    if not cfname.endswith(".schema.json"):
                        continue
                    with open(os.path.join(schemas_dir, cfname), "r", encoding="utf-8") as cf:
                        cdata = json.load(cf)
                    if cdata.get("component") and cdata.get("target"):
                        component_schemas.append(cdata)
            except Exception:
                component_schemas = []

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
                # enum/pattern were declared by the schemas but never checked,
                # so a value the schema explicitly forbids passed silently.
                if isinstance(spec, dict):
                    if exp == "string" and "enum" in spec and val not in spec["enum"]:
                        errs.append(f"{path_str}: {val!r} not in {spec['enum']}")
                    if exp == "string" and spec.get("pattern"):
                        try:
                            if not re.match(spec["pattern"], val):
                                errs.append(f"{path_str}: {val!r} does not match {spec['pattern']}")
                        except re.error:
                            pass
                    # Array bounds, so a truncated stages[] is caught here too.
                    if exp == "array":
                        if "min_items" in spec and len(val) < spec["min_items"]:
                            errs.append(f"{path_str}: {len(val)} item(s) < min_items {spec['min_items']}")
                        if "max_items" in spec and len(val) > spec["max_items"]:
                            errs.append(f"{path_str}: {len(val)} item(s) > max_items {spec['max_items']}")
                        item_spec = spec.get("item_fields") or spec.get("items")
                        if isinstance(item_spec, dict):
                            for i, entry in enumerate(val):
                                if isinstance(entry, dict):
                                    for f_name, f_spec in item_spec.items():
                                        if f_name not in entry:
                                            if isinstance(f_spec, dict) and f_spec.get("required"):
                                                errs.append(f"{path_str}[{i}].{f_name}: missing (required)")
                                            continue
                                        errs.extend(check_val(entry[f_name], f_spec, f"{path_str}[{i}].{f_name}"))
                if exp == "object" and isinstance(spec, dict) and "properties" in spec:
                    for p_name, p_type in spec["properties"].items():
                        if p_name not in val:
                            errs.append(f"{path_str}.{p_name}: missing")
                        else:
                            errs.extend(check_val(val[p_name], p_type, f"{path_str}.{p_name}"))
                return errs

            def val_item(manifest, schema):
                errs = []
                # A schema "target" names WHERE its fields live. Categories use
                # "category_fields" (and _base uses "properties"), but the
                # growth_group schema declares "root+growth": its fields are
                # split across the manifest root and the nested growth block.
                # Reading that string as a literal key found nothing, so every
                # growable group reported all its scheme fields as missing.
                tgt_key = schema.get("target", "category_fields")
                if tgt_key == "root+growth":
                    tgt = dict(manifest.get("growth") or {})
                    # root_fields are required at the manifest root instead.
                    for r_name, r_spec in (schema.get("root_fields") or {}).items():
                        if r_name not in manifest:
                            if r_spec.get("required"):
                                errs.append(f"{r_name}: missing (required)")
                            continue
                        errs.extend(check_val(manifest[r_name], r_spec, r_name))
                else:
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
                # The two schema families are kept SEPARATE rather than
                # cumulative:
                #
                #   ordinary item -> base + category schemas (properties,
                #                    category_fields, and so on)
                #   growth group  -> growth_group.schema.json alone
                #
                # A group's properties/category_fields live on its per-stage
                # manifests under stages/, not on the group itself (the growth
                # schema's directory_layout says as much: '<species>.json' owns
                # the scheme, and only the stages hold models and their own
                # fields). Applying the category schema to the group as well
                # demands properties/category_fields the group is designed
                # never to have, forcing per-stage data to be duplicated up
                # onto the group - exactly the drift this shape exists to
                # prevent. So a group is validated against the growth schema
                # INSTEAD of the category ones; its stages, which ARE ordinary
                # items of the category, are validated against the category
                # schemas when that category is validated.
                is_group = bool(manifest.get("is_growable"))
                if is_group:
                    if growth_group_schema:
                        item_errs.extend(val_item(manifest, growth_group_schema))
                    # The schema calls out two cross-checks it cannot express
                    # as per-field rules: total_stages must equal len(stages),
                    # and the final stage's age_max must land on max_age (so a
                    # group is fully grown exactly at max_age). A plain field
                    # check cannot see across two fields, so do it here.
                    g = manifest.get("growth") or {}
                    stages = g.get("stages") or []
                    decl = g.get("total_stages")
                    if isinstance(decl, (int, float)) and int(decl) != len(stages):
                        item_errs.append(
                            f"growth.total_stages: declares {int(decl)} but stages[] has {len(stages)} entry(ies)")
                    max_age = g.get("max_age")
                    if stages and isinstance(max_age, (int, float)):
                        last_max = stages[-1].get("age_max")
                        if isinstance(last_max, (int, float)) and last_max != max_age:
                            item_errs.append(
                                f"growth.stages[-1].age_max: {last_max} does not reach max_age {max_age}")
                    # Contiguity: each stage's age_max must be the next's age_min.
                    for i in range(len(stages) - 1):
                        a = stages[i].get("age_max")
                        b = stages[i + 1].get("age_min")
                        if isinstance(a, (int, float)) and isinstance(b, (int, float)) and a != b:
                            item_errs.append(
                                f"growth.stages[{i}].age_max ({a}) != stages[{i+1}].age_min ({b})")
                else:
                    for s in schemas:
                        item_errs.extend(val_item(manifest, s))
                    for cs in component_schemas:
                        if isinstance(manifest.get(cs["target"]), dict):
                            item_errs.extend(val_item(manifest, cs))

                # Cross-checks the per-field schemas cannot express: a growth group's own links
                # (the item that plants it, its variant models) and its harvest tool.
                if is_group:
                    item_errs.extend(check_group_links(manifest, category))
                    ymap = (((manifest.get("growth") or {}).get("rules") or {}).get("yield") or {})
                    for tool in harvest_tools_of(ymap):
                        tool_err = check_tool_ref(tool)
                        if tool_err:
                            item_errs.append("growth.rules.yield.tools: " + tool_err)

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
            # An empty list is allowed: a freshly created tag starts empty and gets members by drag and drop.
            if not isinstance(members, list):
                self.send_json_response({"success": False, "error": "members must be a list of item ids"}, 400)
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

    def handle_rename_material_tag(self):
        """Renames a tag in place (same members, new key) - one atomic write
        instead of delete-then-recreate, so a failed second call can never
        leave the tag missing entirely."""
        try:
            content_len = int(self.headers.get("Content-Length", 0))
            post_body = self.rfile.read(content_len)
            data = json.loads(post_body.decode("utf-8")) if content_len > 0 else {}

            old_name = data.get("old_name", "").strip().lower()
            new_name = data.get("new_name", "").strip().lower()

            if not old_name or not new_name:
                self.send_json_response({"success": False, "error": "Missing old_name or new_name"}, 400)
                return
            if not re.match(r"^[a-z][a-z0-9_]*$", new_name):
                self.send_json_response({"success": False, "error": "Tag name must start with a letter and contain only lowercase letters, numbers, and underscores."}, 400)
                return

            data_store = load_material_tags()
            if old_name not in data_store["tags"]:
                self.send_json_response({"success": False, "error": f"Tag '#{old_name}' does not exist."}, 404)
                return
            if new_name != old_name and new_name in data_store["tags"]:
                self.send_json_response({"success": False, "error": f"Tag '#{new_name}' already exists."}, 400)
                return

            members = data_store["tags"].pop(old_name)
            data_store["tags"][new_name] = members
            save_material_tags(data_store)

            updated = rewrite_tag_references(old_name, new_name) if new_name != old_name else []

            print(f"[RENAME TAG] #{old_name} -> #{new_name} ({len(updated)} file(s) updated)")
            self.send_json_response({
                "success": True,
                "message": f"Tag '#{old_name}' renamed to '#{new_name}'" + (f"; {len(updated)} file(s) that used it were updated." if updated else "."),
                "new_name": new_name,
                "members": members,
                "updated_files": len(updated)
            }, 200)

        except Exception as e:
            print(f"Error renaming material tag: {e}")
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
                # Target real-world size for THIS stage's model (meters). Blank/0/absent = not set.
                # width_m/depth_m absent while height_m is set => scale uniformly by height alone.
                # All three set => scale each axis independently to hit the exact footprint.
                for dim_key in ("width_m", "depth_m", "height_m"):
                    val = st.get(dim_key)
                    if isinstance(val, (int, float)) and val > 0:
                        stage_entry[dim_key] = val
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
                # Target real-world size for this stage's generated model (meters). See
                # handle_request_asset_stages' width_m/depth_m/height_m note above for the
                # uniform-vs-per-axis scaling rule a processing agent must follow.
                for dim_key in ("width_m", "depth_m", "height_m"):
                    if dim_key in st:
                        request_data[dim_key] = st[dim_key]
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

    def handle_update_claude_usage(self):
        """Lets a Claude session push the account's plan usage (5-hour and
        weekly windows, as the Claude app reports them). Body:
        {"percent_5h": 13, "resets_5h_at": "<ISO>", "percent_7d": 2,
         "resets_7d_at": "<ISO>", "plan": "Pro"} - stored raw (same shape the
        scheduled task writes directly via the Write tool); _load_session_claude_usage
        does the ISO/percent conversion at read time."""
        try:
            content_len = int(self.headers.get("Content-Length", 0))
            post_body = self.rfile.read(content_len)
            data = json.loads(post_body.decode("utf-8")) if content_len > 0 else {}

            pct_5h = data.get("percent_5h")
            pct_7d = data.get("percent_7d")
            if not isinstance(pct_5h, (int, float)) or not isinstance(pct_7d, (int, float)):
                self.send_json_response({"success": False, "error": "percent_5h and percent_7d are required numbers"}, 400)
                return

            with open(CLAUDE_USAGE_SESSION_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

            print(f"[CLAUDE USAGE] 5h {pct_5h}% / 7d {pct_7d}%")
            self.send_json_response({"success": True, **_load_session_claude_usage()}, 200)

        except Exception as e:
            print(f"Error updating Claude usage: {e}")
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
                update_script = os.path.join(SCRIPT_DIR, "update_catalog_readme.py")
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

    # Edits the SCHEME fields (name/species/growth_type/max_age/time_unit/
    # icon_stage) of a migrated group whose manifest lives at
    # <category>/<group>/<group>.json and owns its stages in a stages/
    # subfolder - the shape migrate_growth_groups.py produces.
    #
    # This is deliberately NOT save_growth_group: that endpoint expects each
    # stage to be its own catalog asset folder and rewrites every member's
    # manifest. A migrated group's stages are resource folders the catalog
    # never walks, so reusing it would fail to resolve the stage items and
    # destroy the group. Here only the group's own manifest is touched, and
    # only the scheme fields - id/category stay pinned to the real path, and
    # the stages[] array is carried through untouched (editing per-stage age
    # windows is a separate concern from editing the scheme).
    def handle_save_group_scheme(self):
        try:
            content_len = int(self.headers.get("Content-Length", 0))
            post_body = self.rfile.read(content_len)
            data = json.loads(post_body.decode("utf-8")) if content_len > 0 else {}

            category = str(data.get("category", "")).strip().lower()
            group_id = str(data.get("group_id", "")).strip().lower()
            if not category or not group_id:
                self.send_json_response(
                    {"success": False, "error": "Missing category or group_id"}, 400)
                return
            if category not in ALLOWED_CATEGORIES:
                self.send_json_response(
                    {"success": False, "error": f"Invalid category: {category}"}, 400)
                return
            manifest_path = os.path.join(BASE_DIR, category, group_id,
                                        group_id + ".json")
            if not os.path.isfile(manifest_path):
                self.send_json_response({
                    "success": False,
                    "error": f"No group manifest at {category}/{group_id}/{group_id}.json"
                }, 404)
                return
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)

            growth = manifest.get("growth")
            if not isinstance(growth, dict):
                self.send_json_response({
                    "success": False,
                    "error": "This manifest has no growth{} scheme block to edit."
                }, 400)
                return
            if "name" in data:
                name = str(data.get("name", "")).strip()
                if not name:
                    self.send_json_response(
                        {"success": False, "error": "Name cannot be empty."}, 400)
                    return
                manifest["name"] = name
            if "description" in data:
                manifest["description"] = str(data.get("description", ""))

            if "species" in data:
                species = str(data.get("species", "")).strip().lower()
                if not re.match(r"^[a-z][a-z0-9_]*$", species or ""):
                    self.send_json_response({
                        "success": False,
                        "error": "Species must start with a letter and use only "
                                 "lowercase letters, numbers, and underscores.",
                    }, 400)
                    return
                growth["species"] = species
            if "growth_type" in data:
                growth["growth_type"] = str(data.get("growth_type", "")).strip() or "generic"

            if "time_unit" in data:
                growth["time_unit"] = str(data.get("time_unit", "")).strip() or "days"

            if "max_age" in data:
                try:
                    max_age = float(data.get("max_age"))
                except (TypeError, ValueError):
                    self.send_json_response(
                        {"success": False, "error": "max_age must be a number."}, 400)
                    return
                if max_age <= 0:
                    self.send_json_response(
                        {"success": False, "error": "max_age must be positive."}, 400)
                    return
                # Keep it an int when it is whole, so the file does not drift
                # from 100 to 100.0 on a value the user never changed shape of.
                growth["max_age"] = int(max_age) if max_age.is_integer() else max_age
            if "icon_stage" in data:
                try:
                    icon_stage = int(data.get("icon_stage"))
                except (TypeError, ValueError):
                    self.send_json_response(
                        {"success": False, "error": "icon_stage must be a whole number."}, 400)
                    return
                stages = growth.get("stages") or []
                if not (1 <= icon_stage <= len(stages)):
                    self.send_json_response({
                        "success": False,
                        "error": f"icon_stage must be between 1 and {len(stages)}.",
                    }, 400)
                    return
                growth["icon_stage"] = icon_stage
            # Per-stage edits. Each entry is matched by its `stage` number, so
            # the editor can send only the row the user touched. `resource`,
            # `model` and `icon` are the group-manifest-only fields (a stage
            # folder is a resource, not a catalog asset, so these are the only
            # place they are recorded), alongside the name and age window that
            # every lifecycle shares.
            if "stages" in data:
                incoming = data.get("stages")
                if not isinstance(incoming, list):
                    self.send_json_response(
                        {"success": False, "error": "stages must be an array."}, 400)
                    return
                existing = growth.get("stages") or []
                by_num = {}
                for st in existing:
                    if isinstance(st, dict) and st.get("stage") is not None:
                        by_num[int(st["stage"])] = st
                for entry in incoming:
                    if not isinstance(entry, dict):
                        continue
                    try:
                        num = int(entry.get("stage"))
                    except (TypeError, ValueError):
                        self.send_json_response({
                            "success": False,
                            "error": "Each stage edit needs a numeric 'stage'.",
                        }, 400)
                        return
                    target = by_num.get(num)
                    if target is None:
                        self.send_json_response({
                            "success": False,
                            "error": f"No stage {num} in this group's scheme.",
                        }, 400)
                        return
                    if "name" in entry:
                        nm = str(entry.get("name", "")).strip()
                        if not nm:
                            self.send_json_response({
                                "success": False,
                                "error": f"Stage {num} name cannot be empty.",
                            }, 400)
                            return
                        target["name"] = nm
                    for fld in ("resource", "model", "icon"):
                        if fld in entry:
                            v = str(entry.get(fld, "")).strip()
                            # An empty optional icon is legitimate (not every
                            # stage ships one); an empty resource/model is not,
                            # since the stage would stop resolving.
                            if not v and fld in ("resource", "model"):
                                self.send_json_response({
                                    "success": False,
                                    "error": f"Stage {num} {fld} cannot be empty.",
                                }, 400)
                                return
                            if v:
                                target[fld] = v
                            elif fld == "icon" and fld in target:
                                del target[fld]
                    for fld in ("age_min", "age_max"):
                        if fld in entry:
                            try:
                                fv = float(entry.get(fld))
                            except (TypeError, ValueError):
                                self.send_json_response({
                                    "success": False,
                                    "error": f"Stage {num} {fld} must be a number.",
                                }, 400)
                                return
                            if fv < 0:
                                self.send_json_response({
                                    "success": False,
                                    "error": f"Stage {num} {fld} cannot be negative.",
                                }, 400)
                                return
                            target[fld] = int(fv) if fv.is_integer() else fv
                    if "age_min" in target and "age_max" in target:
                        if target["age_max"] <= target["age_min"]:
                            self.send_json_response({
                                "success": False,
                                "error": f"Stage {num}: age_max must be greater than age_min.",
                            }, 400)
                            return
            # Group-level growth rules (see growth_group.schema.json `rules`).
            # They apply ONLY to trees and crops: for any other growth_type a
            # non-empty rules block is rejected and a stale one is dropped.
            if growth.get("growth_type") not in ("tree", "crop"):
                if data.get("rules"):
                    self.send_json_response({
                        "success": False,
                        "error": "Growth rules only apply to tree and crop groups.",
                    }, 400)
                    return
                growth.pop("rules", None)
            elif "rules" in data:
                rules, rules_err = sanitize_growth_rules(data.get("rules"), len(growth.get("stages") or []), group_id, growth.get("growth_type"))
                if rules_err:
                    self.send_json_response({"success": False, "error": rules_err}, 400)
                    return
                growth["rules"] = rules

            manifest["growth"] = growth
            with open(manifest_path, "w", encoding="utf-8", newline="\n") as f:
                json.dump(manifest, f, indent=2, ensure_ascii=False)
                f.write("\n")

            invalidate_catalog_cache()
            print(f"[GROUP SCHEME] {category}/{group_id} saved")
            self.send_json_response({"success": True, "manifest": manifest}, 200)

        except Exception as e:
            print(f"Error saving group scheme: {e}")
            self.send_json_response({"success": False, "error": str(e)}, 500)

    def handle_save_economy(self):
        """Batch-saves the economy fields (is_buyable / is_sellable / cost) that
        the Economy view edits across many items at once.

        WHY A BATCH ENDPOINT: the Economy view is a table of every item, and a
        user expects one Save to persist every edited row. Posting N single
        saves would leave the catalog half-updated if one failed partway, so
        this validates EVERY row first and only then writes; a single invalid
        row rejects the whole request with the offending item named.

        Cost is written to properties.base_value - the same field the store-catalog
        scripts read as the shelf price - so an edit here reaches the shops.
        The two flags are written into `properties`, and
        are removed (not written as false/0) when they are at their default, so
        a manifest that never used them stays byte-identical to before."""
        try:
            content_len = int(self.headers.get("Content-Length", 0))
            post_body = self.rfile.read(content_len)
            data = json.loads(post_body.decode("utf-8")) if content_len > 0 else {}

            rows = data.get("items")
            if not isinstance(rows, list) or not rows:
                self.send_json_response(
                    {"success": False, "error": "'items' must be a non-empty list"}, 400)
                return
            # ---- validate everything up front, before touching any file ----
            resolved = []
            errors = []
            for row in rows:
                if not isinstance(row, dict):
                    errors.append("each item must be a JSON object")
                    continue
                category = str(row.get("category", "")).strip().lower()
                item_id = str(row.get("item_id", "")).strip().lower()
                label = f"{category}/{item_id}" or "(unnamed item)"

                if not category or not item_id:
                    errors.append(f"{label}: missing category or item_id")
                    continue
                if category not in ALLOWED_CATEGORIES:
                    errors.append(f"{label}: invalid category")
                    continue
                if ".." in item_id or "/" in item_id or "\\" in item_id:
                    errors.append(f"{label}: invalid item_id")
                    continue
                item_dir = os.path.join(BASE_DIR, category, item_id)
                manifest_path = os.path.join(item_dir, f"{item_id}.json")
                if not os.path.isfile(manifest_path):
                    errors.append(f"{label}: manifest not found")
                    continue
                cost = row.get("base_value", row.get("cost", 0))
                try:
                    cost = float(cost)
                except (TypeError, ValueError):
                    errors.append(f"{label}: cost must be a number")
                    continue
                if cost < 0:
                    errors.append(f"{label}: cost cannot be negative")
                    continue
                # Whole dollars only: base_value is a whole-number price in
                # every existing manifest, and cents would render noisily.
                cost = int(round(cost))

                resolved.append({
                    "category": category,
                    "item_id": item_id,
                    "path": manifest_path,
                    "label": label,
                    "is_buyable": bool(row.get("is_buyable", False)),
                    "is_sellable": bool(row.get("is_sellable", False)),
                    # None = client did not send it: leave the manifest's value alone.
                    "is_consumable": (bool(row["is_consumable"]) if "is_consumable" in row else None),
                    "cost": cost,
                })

            if errors:
                self.send_json_response({
                    "success": False,
                    "error": "Nothing was saved. Fix these first: " + "; ".join(errors),
                    "errors": errors,
                }, 400)
                return
            # ---- all rows valid, now write ----
            saved = []
            for r in resolved:
                try:
                    with open(r["path"], "r", encoding="utf-8") as f:
                        manifest = json.load(f)
                except Exception as e:
                    self.send_json_response({
                        "success": False,
                        "error": f"{r['label']}: could not read manifest: {e}",
                    }, 500)
                    return
                props = manifest.get("properties")
                if not isinstance(props, dict):
                    props = {}

                # Write only non-default values. Dropping them when default keeps
                # manifests that never opted in free of noise fields, and means
                # re-running the view over a clean catalog is a no-op.
                # base_value is required by _base.schema.json, so it is
                # always written (never removed) - only the two optional
                # flags are dropped when false, keeping untouched
                # manifests free of noise fields.
                props["base_value"] = r["cost"]
                # is_consumable is mandatory in _base.schema.json, so it is always
                # written as an explicit boolean (never dropped when false).
                if r["is_consumable"] is not None:
                    props["is_consumable"] = r["is_consumable"]
                # is_buyable / is_sellable are mandatory in _base.schema.json: always explicit booleans.
                props["is_buyable"] = bool(r["is_buyable"])
                props["is_sellable"] = bool(r["is_sellable"])
                if props:
                    manifest["properties"] = props
                elif "properties" in manifest:
                    manifest["properties"] = props
                with open(r["path"], "w", encoding="utf-8") as f:
                    json.dump(manifest, f, indent=2)
                saved.append({
                    "category": r["category"],
                    "item_id": r["item_id"],
                    "is_buyable": r["is_buyable"],
                    "is_sellable": r["is_sellable"],
                    "is_consumable": bool(props.get("is_consumable", False)),
                    "base_value": r["cost"],
                })

            # The catalog is cached with a TTL; force a rebuild so /api/catalog
            # reflects the new prices immediately rather than up to 10s later.
            invalidate_catalog_cache()
            # The phone stores stock is_buyable items and the Market sells is_sellable ones (StoreCatalogs.json),
            # so rebuild it whenever those flags or prices change. Best effort: a failure must not fail the save.
            try:
                for script in ("_build_store_catalogs_json.py", "_add_new_store_catalogs.py"):
                    subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), script)],
                                   check=True, capture_output=True, timeout=60)
            except Exception as e:
                print(f"[SAVE ECONOMY] could not rebuild StoreCatalogs.json: {e}")
            print(f"[SAVE ECONOMY] {len(saved)} item(s) updated")
            self.send_json_response({
                "success": True,
                "message": f"Saved economy data for {len(saved)} item(s).",
                "items": saved,
            }, 200)

        except Exception as e:
            print(f"Error saving economy data: {e}")
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

            light_errors, _light_warnings = light_emitter.validate_lights(manifest.get("lights"))
            if light_errors:
                self.send_json_response({"success": False, "error": "Lights: " + "; ".join(light_errors)}, 400)
                return

            manifest_path = os.path.join(item_dir, f"{item_id}.json")
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2)

            try:
                update_script = os.path.join(SCRIPT_DIR, "update_catalog_readme.py")
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

