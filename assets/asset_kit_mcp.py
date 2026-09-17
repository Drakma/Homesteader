#!/usr/bin/env python3
"""
Homesteader Asset Kit MCP Server
Provides native Model Context Protocol (MCP) tools for AI agents working
on the Homesteader project:
- Querying and updating asset generation requests in _asset_requests/
- Reading and writing item manifests (<item_id>.json)
- Managing material tags (_schemas/material_tags.json)
- Validating item icons and 3D models
- Synchronizing the master catalog README
"""

import os
import sys
import json
import time
import shutil
from typing import Optional, List, Dict, Any

from mcp.server.mcpserver import MCPServer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REQ_DIR = os.path.join(BASE_DIR, "_asset_requests")
PENDING_DIR = os.path.join(REQ_DIR, "pending")
IN_PROGRESS_DIR = os.path.join(REQ_DIR, "in_progress")
DONE_DIR = os.path.join(REQ_DIR, "done")
BATCHES_DIR = os.path.join(REQ_DIR, "batches")
SCHEMAS_DIR = os.path.join(BASE_DIR, "_schemas")
TAGS_PATH = os.path.join(SCHEMAS_DIR, "material_tags.json")

# Project guide docs live in the docs/ and assets/ folders. These are the
# authoritative rules every agent should read before creating assets.
PROJECT_DIR = os.path.dirname(BASE_DIR)          # C:\\Users\\casey\\Desktop\\Homesteader
ASSETS_GUIDES_DIR = BASE_DIR                     # the assets/ folder itself
DOCS_GUIDES_DIR = os.path.join(PROJECT_DIR, "docs")

# Active (non-legacy) guide docs exposed over MCP, grouped by source folder.
# Legacy UNREAL_* docs and session-state notes are intentionally excluded.
_GUIDE_GROUPS = [
    # AGENTS.md / CLAUDE.md live at the repo root so agents auto-index them.
    ("docs", PROJECT_DIR, [
        "AGENTS.md",
        "CLAUDE.md",
    ]),
    ("docs", DOCS_GUIDES_DIR, [
        "ASSET_CREATION_GUIDE.md",
        "ITEM_ICON_STYLE_GUIDE.md",
        "ITEM_ORGANIZATION_GUIDE.md",
        "GRID_AND_GROUND_STANDARDS.md",
        "GROUND_TILES_GUIDE.md",
        "GROUND_BLENDING_SETUP.md",
        "FOLIAGE_GUIDE.md",
        "FREE_PIPELINE_GUIDE.md",
        "UNITY_INTEGRATION_GUIDE.md",
    ]),
    ("assets", ASSETS_GUIDES_DIR, [
        "GUIDE.md",
        "API_REFERENCE.md",
        "README.md",
        "_schemas/README.md",
        "ground/README.md",
        "textures/README.md",
    ]),
]

# Canonical map: display name ("docs/AGENTS.md") -> (root_dir, rel_path)
GUIDE_FILES = {}
ACTIVE_GUIDES = []
for _g_name, _g_root, _g_files in _GUIDE_GROUPS:
    for _g_rel in _g_files:
        _g_display = f"{_g_name}/{_g_rel}"
        GUIDE_FILES[_g_display] = (_g_root, _g_rel)
        ACTIVE_GUIDES.append(_g_display)

# Basename index -> list of display names (may be ambiguous, e.g. README.md)
GUIDE_BY_BASENAME = {}
for _g_display, (_g_root, _g_rel) in GUIDE_FILES.items():
    _g_base = os.path.basename(_g_rel).lower()
    GUIDE_BY_BASENAME.setdefault(_g_base, []).append(_g_display)

mcp = MCPServer(
    "homesteader-asset-kit",
    instructions=(
        "Homesteader project guides are MANDATORY. Before generating, "
        "editing, or organizing any asset, list the guides via the "
        "`list_guides` tool (or the homesteader://guides resource) and read "
        "the relevant ones. The icon and asset-creation guides define "
        "hard rules (128x128 RGBA icons, no borders, taxonomy, manifests)."
    ),
)


# -----------------------------------------------------------------------------
# 1. Asset Requests & Queue
# -----------------------------------------------------------------------------

@mcp.tool()
def list_asset_requests(status: str = "all") -> Dict[str, Any]:
    """
    Lists asset generation requests from assets/_asset_requests/.
    Args:
        status: Filter by 'all', 'pending', 'in_progress', or 'done'.
    """
    folders = []
    status = status.lower().strip()
    if status in ("pending", "all"):
        folders.append(("pending", PENDING_DIR))
    if status in ("in_progress", "all"):
        folders.append(("in_progress", IN_PROGRESS_DIR))
    if status in ("done", "all"):
        folders.append(("done", DONE_DIR))

    requests = []
    for st, folder in folders:
        if not os.path.isdir(folder):
            continue
        for fname in sorted(os.listdir(folder)):
            if not fname.endswith(".json"):
                continue
            fpath = os.path.join(folder, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                data["status"] = data.get("status", st)
                requests.append(data)
            except Exception:
                continue

    return {
        "success": True,
        "count": len(requests),
        "requests": requests
    }


@mcp.tool()
def update_asset_request(
    request_id: str,
    status: str = "",
    step: str = "",
    item_id: str = "",
    meshy_credits: int = 0,
    creative_claw_credits: int = 0
) -> Dict[str, Any]:
    """
    Updates an asset request's status, progress step, and credits used.
    Automatically moves request file between pending/in_progress/done folders.
    Args:
        request_id: Request identifier (e.g. '1789520000_steel_stud_framing')
        status: 'in_progress' or 'done'
        step: Human-readable progress description
        item_id: The final catalog item ID created (e.g. 'mat_steel_stud_framing')
        meshy_credits: Number of Meshy credits consumed
        creative_claw_credits: Number of Creative Claw credits consumed
    """
    fname = f"{request_id}.json"
    current_folder = None
    for folder in (PENDING_DIR, IN_PROGRESS_DIR, DONE_DIR):
        if os.path.isfile(os.path.join(folder, fname)):
            current_folder = folder
            break

    if current_folder is None:
        return {"success": False, "error": f"Request '{request_id}' not found in queue."}

    src_path = os.path.join(current_folder, fname)
    with open(src_path, "r", encoding="utf-8") as f:
        req = json.load(f)

    if step:
        req["step"] = step
    if item_id:
        req["created_item_id"] = item_id.strip().lower()

    if meshy_credits or creative_claw_credits:
        credits = req.get("credits_used", {})
        credits["meshy"] = credits.get("meshy", 0) + meshy_credits
        credits["creative_claw"] = credits.get("creative_claw", 0) + creative_claw_credits
        req["credits_used"] = credits

    new_folder = current_folder
    status_lower = status.lower().strip()
    if status_lower:
        if status_lower not in ("pending", "in_progress", "done"):
            return {"success": False, "error": f"Invalid status '{status}'. Must be pending, in_progress, or done."}
        req["status"] = status_lower
        if status_lower == "in_progress":
            new_folder = IN_PROGRESS_DIR
        elif status_lower == "done":
            new_folder = DONE_DIR
            req["completed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    with open(src_path, "w", encoding="utf-8") as f:
        json.dump(req, f, indent=2)

    if new_folder != current_folder:
        os.makedirs(new_folder, exist_ok=True)
        dst_path = os.path.join(new_folder, fname)
        shutil.move(src_path, dst_path)

    # If status is done, also update batch file if batch_id is present
    batch_id = req.get("batch_id")
    if status_lower == "done" and batch_id:
        batch_file = os.path.join(BATCHES_DIR, f"{batch_id}.json")
        if os.path.isfile(batch_file):
            try:
                with open(batch_file, "r", encoding="utf-8") as f:
                    batch = json.load(f)
                for it in batch.get("items", []):
                    if it.get("id") == request_id:
                        it["status"] = "done"
                with open(batch_file, "w", encoding="utf-8") as f:
                    json.dump(batch, f, indent=2)
            except Exception:
                pass

    return {
        "success": True,
        "request_id": request_id,
        "status": req.get("status"),
        "step": req.get("step"),
        "created_item_id": req.get("created_item_id")
    }


@mcp.tool()
def finalize_asset_requests() -> Dict[str, Any]:
    """
    Groups all currently pending requests into a single finalized batch
    file in assets/_asset_requests/batches/ and notifies background watchers.
    """
    os.makedirs(PENDING_DIR, exist_ok=True)
    os.makedirs(BATCHES_DIR, exist_ok=True)

    pending_files = [f for f in os.listdir(PENDING_DIR) if f.endswith(".json")]
    if not pending_files:
        return {"success": False, "error": "No pending requests to finalize."}

    items = []
    for fname in sorted(pending_files):
        p = os.path.join(PENDING_DIR, fname)
        try:
            with open(p, "r", encoding="utf-8") as f:
                items.append(json.load(f))
        except Exception:
            continue

    batch_id = f"batch_{int(time.time())}"
    batch_file = os.path.join(BATCHES_DIR, f"{batch_id}.json")
    batch_payload = {
        "batch_id": batch_id,
        "finalized_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "items": items
    }
    with open(batch_file, "w", encoding="utf-8") as f:
        json.dump(batch_payload, f, indent=2)

    return {
        "success": True,
        "batch_id": batch_id,
        "item_count": len(items)
    }


# -----------------------------------------------------------------------------
# 2. Catalog & Manifests
# -----------------------------------------------------------------------------

@mcp.tool()
def get_catalog_item(category: str, item_id: str) -> Dict[str, Any]:
    """
    Retrieves an item's manifest (<item_id>.json) and inspects its physical
    asset files on disk (3D models, textures, icon).
    Args:
        category: Catalog category (e.g. 'building', 'tools', 'farming')
        item_id: Unique item identifier (e.g. 'mat_steel_stud_framing')
    """
    item_dir = os.path.join(BASE_DIR, category, item_id)
    if not os.path.isdir(item_dir):
        return {"success": False, "error": f"Item directory not found: {category}/{item_id}"}

    manifest_file = os.path.join(item_dir, f"{item_id}.json")
    manifest = {}
    if os.path.isfile(manifest_file):
        with open(manifest_file, "r", encoding="utf-8") as f:
            manifest = json.load(f)

    files = []
    for fn in os.listdir(item_dir):
        fp = os.path.join(item_dir, fn)
        files.append({
            "name": fn,
            "size_bytes": os.path.getsize(fp),
            "ext": os.path.splitext(fn)[1].lower()
        })

    return {
        "success": True,
        "category": category,
        "item_id": item_id,
        "manifest": manifest,
        "files": files
    }


@mcp.tool()
def save_item_manifest(category: str, item_id: str, manifest: Dict[str, Any]) -> Dict[str, Any]:
    """
    Safely saves or updates an item's plugin manifest (<item_id>.json).
    Ensures id and category match the directory structure.
    Args:
        category: Catalog category
        item_id: Unique item identifier
        manifest: Complete manifest dictionary
    """
    item_dir = os.path.join(BASE_DIR, category, item_id)
    os.makedirs(item_dir, exist_ok=True)

    manifest["id"] = item_id
    manifest["category"] = category
    manifest["icon"] = f"{item_id}.png"

    manifest_file = os.path.join(item_dir, f"{item_id}.json")
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    return {
        "success": True,
        "category": category,
        "item_id": item_id,
        "path": manifest_file
    }


# -----------------------------------------------------------------------------
# 3. Material Tags & Schemas
# -----------------------------------------------------------------------------

@mcp.tool()
def list_material_tags() -> Dict[str, Any]:
    """
    Returns all recipe material tags defined in assets/_schemas/material_tags.json.
    """
    if not os.path.isfile(TAGS_PATH):
        return {"success": False, "error": "material_tags.json not found"}

    with open(TAGS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    return {
        "success": True,
        "tags": data.get("tags", {})
    }


@mcp.tool()
def save_material_tag(tag_name: str, members: List[str]) -> Dict[str, Any]:
    """
    Creates or updates a recipe material tag (e.g. #steel_framing, #metal_siding).
    Verifies that all members exist as catalog items before writing.
    Args:
        tag_name: The tag name without leading '#' (e.g. 'steel_framing')
        members: List of real catalog item IDs (e.g. ['mat_steel_stud_framing'])
    """
    tag_clean = tag_name.lstrip("#").strip().lower()
    if not tag_clean:
        return {"success": False, "error": "Invalid tag name"}

    with open(TAGS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    tags = data.setdefault("tags", {})
    tags[tag_clean] = members

    with open(TAGS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    return {
        "success": True,
        "tag_name": tag_clean,
        "members": members
    }


# -----------------------------------------------------------------------------
# 4. Catalog Synchronization & Validation
# -----------------------------------------------------------------------------

@mcp.tool()
def sync_catalog_index() -> Dict[str, Any]:
    """
    Executes update_catalog_readme.py to rebuild assets/README.md with
    all indexed items across all 16 categories.
    """
    script_path = os.path.join(BASE_DIR, "update_catalog_readme.py")
    if not os.path.isfile(script_path):
        return {"success": False, "error": "update_catalog_readme.py not found"}

    import subprocess
    res = subprocess.run([sys.executable, script_path], capture_output=True, text=True)
    return {
        "success": res.returncode == 0,
        "output": res.stdout.strip(),
        "error": res.stderr.strip() if res.returncode != 0 else None
    }


@mcp.tool()
def validate_item_icon(category: str, item_id: str) -> Dict[str, Any]:
    """
    Validates an item's 128x128 icon against Homesteader Icon Standards:
    - 128x128 32-bit RGBA
    - Item dimension <= 104px (12px safe margin)
    - 100% perimeter alpha = 0 (no borders, no frames)
    """
    icon_path = os.path.join(BASE_DIR, category, item_id, f"{item_id}.png")
    if not os.path.isfile(icon_path):
        return {"success": False, "error": f"Icon not found: {icon_path}"}

    from PIL import Image
    try:
        im = Image.open(icon_path)
    except Exception as e:
        return {"success": False, "error": f"Failed to open image: {e}"}

    errors = []
    if im.format != "PNG":
        errors.append(f"Format is {im.format}; must be PNG")
    if im.mode != "RGBA":
        errors.append(f"Mode is {im.mode}; must be RGBA (32-bit)")
    if im.size != (128, 128):
        errors.append(f"Size is {im.size}; must be 128x128")

    if im.mode == "RGBA":
        alpha = im.split()[3]
        bbox = alpha.getbbox()
        if not bbox:
            errors.append("Image is completely transparent")
        else:
            w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
            if max(w, h) > 106:
                errors.append(f"Max dimension {max(w,h)}px exceeds 104px (+2px tol)")
            # Edge alpha check
            for x in range(128):
                if im.getpixel((x, 0))[3] != 0 or im.getpixel((x, 127))[3] != 0:
                    errors.append("Non-zero alpha on top/bottom edge")
                    break
            for y in range(128):
                if im.getpixel((0, y))[3] != 0 or im.getpixel((127, y))[3] != 0:
                    errors.append("Non-zero alpha on left/right edge")
                    break

    return {
        "success": len(errors) == 0,
        "valid": len(errors) == 0,
        "errors": errors,
        "icon_path": icon_path
    }


# -----------------------------------------------------------------------------
# 5. Project Guides (rules every agent must read)
# -----------------------------------------------------------------------------
def _guide_meta():
    docs = []
    for _disp in ACTIVE_GUIDES:
        _root, _rel = GUIDE_FILES[_disp]
        path = os.path.join(_root, _rel)
        exists = os.path.isfile(path)
        docs.append({
            "name": _disp,
            "uri": f"homesteader://guides/{_disp}",
            "group": _disp.split("/", 1)[0],
            "exists": exists,
            "size_bytes": os.path.getsize(path) if exists else 0,
        })
    return docs


@mcp.tool()
def list_guides():
    """Lists the mandatory Homesteader project guides (rule/spec docs).

    READ THESE BEFORE creating, generating, editing, or organizing assets.
    Two groups are served: 'docs' (icon style, asset creation, grid/ground,
    pipeline, Unity integration) and 'assets' (master catalog GUIDE/README,
    REST API reference, schema/ground/texture READMEs).
    Each entry has a homesteader://guides/<name> URI readable via
    get_guide() or the MCP resources API.
    """
    docs = _guide_meta()
    return {
        "success": True,
        "count": len(docs),
        "groups": sorted(set(d["group"] for d in docs)),
        "guides": docs,
        "note": "Call get_guide(name) to read any guide in full.",
    }


@mcp.tool()
def get_guide(name: str):
    """Reads a Homesteader project guide in full.

    Args:
        name: Guide name, e.g. 'docs/ITEM_ICON_STYLE_GUIDE.md' or
              'assets/API_REFERENCE.md'. A bare basename such as
              'ITEM_ICON_STYLE_GUIDE.md' also resolves. Case-insensitive;
              call list_guides() for the full set.
    """
    raw = (name or "").strip().replace("\\", "/")
    key = raw.lower()
    basename = os.path.basename(key)

    # 1) Exact display-name match (e.g. "docs/ITEM_ICON_STYLE_GUIDE.md").
    display = next((d for d in ACTIVE_GUIDES if d.lower() == key), None)

    # 2) Bare basename match, but refuse to guess when ambiguous.
    if display is None:
        matches = GUIDE_BY_BASENAME.get(basename, [])
        if len(matches) == 1:
            display = matches[0]
        elif len(matches) > 1:
            return {
                "success": False,
                "error": (
                    f"Ambiguous guide name '{name}'. "
                    f"Use a full path such as '{matches[0]}'."
                ),
                "candidates": matches,
            }

    if display is None:
        return {
            "success": False,
            "error": f"Unknown guide '{name}'. Use list_guides() for valid names.",
            "available": ACTIVE_GUIDES,
        }
    root, rel = GUIDE_FILES[display]
    path = os.path.join(root, rel)
    if not os.path.isfile(path):
        return {"success": False, "error": f"Guide file missing on disk: {path}"}
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except Exception as exc:
        return {"success": False, "error": f"Failed to read {display}: {exc}"}
    return {
        "success": True,
        "name": display,
        "group": display.split("/", 1)[0],
        "uri": f"homesteader://guides/{display}",
        "size_bytes": len(content.encode("utf-8")),
        "content": content,
    }


@mcp.resource("homesteader://guides/{name}")
def guide_resource(name: str) -> str:
    """Exposes a docs/ guide as an MCP resource, by bare file name (markdown)."""
    result = get_guide("docs/" + name)
    if not result.get("success"):
        # Fall back to any unambiguous basename (covers assets/ guides too).
        result = get_guide(name)
    if not result.get("success"):
        return "# Guide not found\n\n" + str(result.get("error", "unknown error"))
    return result["content"]


@mcp.resource("homesteader://assets/{name}")
def assets_guide_resource(name: str) -> str:
    """Exposes an assets/ guide as an MCP resource (slash-safe URI)."""
    result = get_guide("assets/" + name)
    if not result.get("success"):
        return "# Guide not found\n\n" + str(result.get("error", "unknown error"))
    return result["content"]


# -----------------------------------------------------------------------------
# Main & Self-Test Mode
# -----------------------------------------------------------------------------

def run_self_test():
    print("=== Running Homesteader Asset Kit MCP Self-Tests ===")
    
    # 1. List requests
    res = list_asset_requests("all")
    print(f"[TEST 1] list_asset_requests: count={res.get('count')} (success={res.get('success')})")
    assert res["success"] is True

    # 2. Get item
    res = get_catalog_item("building", "mat_steel_stud_framing")
    print(f"[TEST 2] get_catalog_item: files={len(res.get('files', []))} (success={res.get('success')})")
    assert res["success"] is True

    # 3. Validate icon
    res = validate_item_icon("building", "mat_steel_stud_framing")
    print(f"[TEST 3] validate_item_icon: valid={res.get('valid')} (success={res.get('success')})")
    assert res["valid"] is True

    # 4. List tags
    res = list_material_tags()
    print(f"[TEST 4] list_material_tags: tag_count={len(res.get('tags', {}))} (success={res.get('success')})")
    assert "steel_framing" in res.get("tags", {})

    # 5. Sync catalog
    res = sync_catalog_index()
    print(f"[TEST 5] sync_catalog_index: output='{res.get('output')}' (success={res.get('success')})")
    assert res["success"] is True

    print("\nAll 5 self-tests passed successfully!")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        run_self_test()
    else:
        mcp.run(transport="stdio")

