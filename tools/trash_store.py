"""
trash_store.py
Soft-delete (recycle bin) storage for the Homesteader Asset Kit.

Deleting an asset moves its folder out of assets/<category>/<item_id>/ and
into assets/_trash/<category>__<item_id>/ (plus a sidecar .trashmeta.json
recording where it came from and when). Because build_full_catalog() only
walks ALLOWED_CATEGORIES, anything parked under _trash/ is automatically
invisible to the catalog - no separate denylist to keep in sync.

Restoring is the exact reverse move, so an item comes back byte-identical
(same manifest, same icons, same models). "Permanently delete" is the only
path that actually calls rmtree().
"""
import json
import os
import shutil
import time

TRASH_DIR_NAME = "_trash"
META_NAME = ".trashmeta.json"


def trash_dir_for(base_dir):
    """The _trash folder that sits beside the category folders, e.g.
    assets/_trash. Kept inside assets/ (not the project root) so it travels
    with the catalog and is covered by the same backups."""
    return os.path.join(base_dir, TRASH_DIR_NAME)


def _trash_folder_name(category, item_id):
    # '__' can't appear in a category slug or item id (both are validated to
    # [a-z0-9_]), so this split is unambiguous when reading it back.
    return f"{category}__{item_id}"


def _split_trash_folder_name(name):
    if "__" not in name:
        return None, None
    category, item_id = name.split("__", 1)
    return category, item_id


def _safe_unlink_dir(path):
    if os.path.isdir(path):
        shutil.rmtree(path, ignore_errors=True)


def _read_meta(entry_path):
    meta_path = os.path.join(entry_path, META_NAME)
    if not os.path.exists(meta_path):
        return None
    try:
        with open(meta_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _read_item_summary(entry_path):
    """Best-effort name/icon for a trashed item, so the Trash panel can show
    something readable. Scans the folder for the first .json manifest that
    isn't our own metadata file."""
    summary = {"name": None, "icon": None}
    try:
        for fname in sorted(os.listdir(entry_path)):
            if not fname.lower().endswith(".json") or fname == META_NAME:
                continue
            with open(os.path.join(entry_path, fname), "r", encoding="utf-8") as f:
                manifest = json.load(f)
            summary["name"] = manifest.get("name")
            summary["icon"] = manifest.get("icon")
            break
    except Exception:
        pass
    return summary


def list_trash(base_dir):
    """Returns one record per trashed item, newest first.

    Reads the .trashmeta.json sidecar when present (the normal case, written
    at delete time) and falls back to parsing the folder name otherwise, so a
    folder dropped into _trash by hand still shows up and can be restored.
    """
    root = trash_dir_for(base_dir)
    if not os.path.isdir(root):
        return []

    records = []
    for name in os.listdir(root):
        entry_path = os.path.join(root, name)
        if not os.path.isdir(entry_path):
            continue

        meta = _read_meta(entry_path)
        if meta:
            category = meta.get("category")
            item_id = meta.get("item_id")
            trashed_at = meta.get("trashed_at")
            size_bytes = meta.get("size_bytes")
        else:
            category, item_id = _split_trash_folder_name(name)
            trashed_at = None
            size_bytes = None

        if not category or not item_id:
            # Unrecognised folder - surface it so it isn't silently stranded,
            # but leave it unrestorable.
            records.append({
                "trash_id": name,
                "category": None,
                "item_id": None,
                "name": name,
                "icon": None,
                "trashed_at": None,
                "size_bytes": size_bytes,
                "restorable": False,
                "reason": "unrecognised folder",
            })
            continue

        summary = _read_item_summary(entry_path)
        records.append({
            "trash_id": name,
            "category": category,
            "item_id": item_id,
            "name": summary["name"] or item_id,
            "icon": summary["icon"],
            "trashed_at": trashed_at,
            "size_bytes": size_bytes,
            "restorable": True,
            "reason": (meta or {}).get("reason"),
        })

    records.sort(key=lambda r: r.get("trashed_at") or 0, reverse=True)
    return records


def _dir_size_bytes(path):
    total = 0
    for root, _dirs, files in os.walk(path):
        for f in files:
            try:
                total += os.path.getsize(os.path.join(root, f))
            except OSError:
                pass
    return total


def move_to_trash(base_dir, category, item_id, reason="deleted"):
    """Moves assets/<category>/<item_id>/ into the trash store.

    Returns (ok, payload). On success payload is the new trash record.
    """
    source = os.path.join(base_dir, category, item_id)
    if not os.path.isdir(source):
        return False, f"Asset folder not found: {category}/{item_id}"

    root = trash_dir_for(base_dir)
    os.makedirs(root, exist_ok=True)

    trash_id = _trash_folder_name(category, item_id)
    dest = os.path.join(root, trash_id)
    if os.path.exists(dest):
        # Same id deleted again (e.g. re-created then deleted): disambiguate
        # with a timestamp rather than overwriting the older copy.
        trash_id = f"{trash_id}__{int(time.time())}"
        dest = os.path.join(root, trash_id)

    size_bytes = _dir_size_bytes(source)
    try:
        shutil.move(source, dest)
    except Exception as e:
        return False, f"Failed to move asset to trash: {e}"

    meta = {
        "category": category,
        "item_id": item_id,
        "trashed_at": time.time(),
        "reason": reason,
        "size_bytes": size_bytes,
        "original_path": os.path.join("assets", category, item_id),
    }
    try:
        with open(os.path.join(dest, META_NAME), "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)
    except Exception as e:
        # The move already happened; without the sidecar the folder name
        # still encodes enough to restore, so this is recoverable - warn only.
        print(f"Warning: trashed {category}/{item_id} but could not write {META_NAME}: {e}")

    summary = _read_item_summary(dest)
    return True, {
        "trash_id": trash_id,
        "category": category,
        "item_id": item_id,
        "name": summary["name"] or item_id,
        "icon": summary["icon"],
        "trashed_at": meta["trashed_at"],
        "size_bytes": size_bytes,
        "reason": reason,
    }


def restore_from_trash(base_dir, trash_id):
    """Moves a trashed item back to its original category folder.

    Refuses to clobber an existing asset at the destination - restoring over
    a live item would destroy data that is not in the trash, which is exactly
    what the trash exists to prevent.
    """
    root = trash_dir_for(base_dir)
    entry_path = os.path.join(root, trash_id)
    if not trash_id or not os.path.isdir(entry_path):
        return False, f"Trash entry not found: {trash_id}"

    meta = _read_meta(entry_path)
    if meta:
        category = meta.get("category")
        item_id = meta.get("item_id")
    else:
        category, item_id = _split_trash_folder_name(trash_id)

    if not category or not item_id:
        return False, f"Cannot determine original location for {trash_id}"

    # Guard against a crafted/corrupt trash_id escaping the store.
    if ".." in category or ".." in item_id or "/" in item_id or "\\" in item_id:
        return False, "Invalid original location in trash metadata"

    dest = os.path.join(base_dir, category, item_id)
    if os.path.exists(dest):
        return False, (
            f"Cannot restore: '{category}/{item_id}' already exists. "
            "Rename or delete the existing item first."
        )

    os.makedirs(os.path.dirname(dest), exist_ok=True)
    try:
        shutil.move(entry_path, dest)
    except Exception as e:
        return False, f"Failed to restore asset: {e}"

    # Remove the sidecar from the restored folder - it is trash bookkeeping,
    # not part of the item, and would otherwise ship into the catalog.
    try:
        os.remove(os.path.join(dest, META_NAME))
    except OSError:
        pass

    return True, {"category": category, "item_id": item_id}


def purge_from_trash(base_dir, trash_ids):
    """Permanently deletes the given trashed entries. Returns (count, errors)."""
    root = trash_dir_for(base_dir)
    purged = 0
    errors = []
    for trash_id in trash_ids:
        entry_path = os.path.join(root, trash_id)
        if not trash_id or not os.path.isdir(entry_path):
            errors.append(f"Trash entry not found: {trash_id}")
            continue
        try:
            shutil.rmtree(entry_path, ignore_errors=False)
            purged += 1
        except Exception as e:
            errors.append(f"Failed to permanently delete {trash_id}: {e}")
    return purged, errors


def purge_all(base_dir):
    """Empties the trash. Returns (count, errors)."""
    records = list_trash(base_dir)
    return purge_from_trash(base_dir, [r["trash_id"] for r in records])
