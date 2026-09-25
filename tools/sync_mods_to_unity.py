#!/usr/bin/env python3
"""
Sync Homesteader mods (and their referenced models) into the Unity project.

WHY THIS EXISTS
---------------
`assets/` and `mods/` live outside the Unity project, so Unity never imports
them. Data (JSON) is read from disk at runtime and needs no import, but GEOMETRY
does: Unity must import a .fbx at build time to produce a usable mesh. This
script copies each mod into `Homesteader/Assets/Mods/<mod_id>/` so Unity sees it.

DESIGN: ONE MOD, ONE FOLDER
---------------------------
Every mod owns exactly one folder under `Assets/Mods/`. That folder IS the
record of what the mod contributed, so:

  * remove the mod from `mods/` and re-run  ->  its `Assets/Mods/` folder is
    deleted along with the rest, leaving nothing orphaned in Unity;
  * two mods can never collide, because each is namespaced by its own id.

A `.sync_state.json` inside each mod folder lists the files the sync created, so
a re-sync can prune files that were dropped from the mod without touching files
a human added by hand afterwards.

NOTE - USUALLY NOT NEEDED
-------------------------
The game reads mods straight from the repo's mods/ folder (ModManager scans <project>/../mods), and GLB models
are loaded at RUNTIME, so nothing has to be imported by Unity. Copying every mod into Assets/Mods makes Unity
import ~1000 GLBs (about 4 GB), which froze/crashed the editor. Only sync when you need Unity to import
something (e.g. a rigged FBX for the prefab generator), and never sync the whole catalog at once.

WHAT GETS COPIED
----------------
  1. The mod's own files (mod.json, asset JSONs, icons, any models it ships).
  2. Any model file the mod REFERENCES but does not ship. Mods commonly declare
     `models[].file` pointing at a model that lives in the core `assets/`
     catalog; those are resolved and copied in so the mod is self-contained.
     Without this, Unity has nothing to import and the asset renders as nothing.

Unity-only files (hand-made .mat assets, animator controllers) are preserved:
they live under `Assets/Mods/_handmade/` and are never pruned by this script.

USAGE
-----
  py -3 tools/sync_mods_to_unity.py                 # dry run (default)
  py -3 tools/sync_mods_to_unity.py --apply         # actually write
  py -3 tools/sync_mods_to_unity.py --apply --mod oak_woodland   # just one
"""
import argparse
import io
import json
import os
import shutil
import sys
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SCRIPT_DIR)

MODS_DIR = os.path.join(ROOT, "Homesteader", "mods")
ASSETS_DIR = os.path.join(ROOT, "assets")
# Assets/Mods is the authoring location (Editor prefab generation reads it).
# Assets/Resources/Mods is what the RUNTIME resolver loads from: Resources.Load
# only works under a folder literally named "Resources", so the prefabs the
# generator produces are mirrored there.
UNITY_MODS_DIR = os.path.join(ROOT, "Homesteader", "Assets", "Mods")
UNITY_RESOURCES_DIR = os.path.join(ROOT, "Homesteader", "Assets", "Resources", "Mods")

STATE_FILE = ".sync_state.json"

# Extensions Unity must import as assets (case-insensitive).
COPY_EXTS = {
    ".json", ".png", ".jpg", ".jpeg", ".tga", ".fbx", ".obj", ".glb", ".gltf",
    ".mtl", ".mat", ".controller", ".anim", ".asset", ".txt", ".md", ".xml",
}

# Never copy these into Unity.
SKIP_DIRS = {"_staging", "__pycache__", ".git", ".vs", "obj", "bin"}
SKIP_EXTS = {".meta"}  # Unity owns .meta files; never copy or delete them


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------

def log(msg):
    print(msg)


def norm(path):
    return path.replace("/", os.sep).replace("\\", os.sep)


def should_copy(path):
    """True when a source file belongs in the Unity project."""
    ext = os.path.splitext(path)[1].lower()
    if ext in SKIP_EXTS:
        return False
    return ext in COPY_EXTS


def iter_files(root):
    """Walk a tree, skipping noise directories and folders switched off with a ".disabled" suffix."""
    for dp, dirs, fs in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.lower().endswith(".disabled")]
        for fn in fs:
            yield os.path.join(dp, fn)


# --------------------------------------------------------------------------
# model reference resolution
# --------------------------------------------------------------------------

def build_model_index():
    """
    Map basename -> full path for every model file under assets/ and mods/.
    A mod that references `SM_Tree_Oak_Mature.fbx` gets matched against this.
    """
    index = {}
    for base in (ASSETS_DIR, MODS_DIR):
        if not os.path.isdir(base):
            continue
        for path in iter_files(base):
            ext = os.path.splitext(path)[1].lower()
            if ext in {".fbx", ".obj", ".glb", ".gltf"}:
                index.setdefault(os.path.basename(path).lower(), path)
    return index


def referenced_models(mod_root, model_index):
    """
    Reads every asset JSON in a mod and returns the model files it references
    but does not itself ship, resolved against the catalog.
    """
    needed = {}      # resolved absolute path -> reason
    missing = []     # names we could not resolve

    for path in iter_files(mod_root):
        if os.path.splitext(path)[1].lower() != ".json":
            continue
        if os.path.basename(path) == "mod.json":
            continue
        try:
            with io.open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            continue

        for entry in data.get("models") or []:
            if not isinstance(entry, dict):
                continue
            name = entry.get("file")
            if not name:
                continue
            name = os.path.basename(norm(name))

            # Already shipped by the mod?
            shipped = os.path.join(mod_root, name)
            if os.path.exists(shipped):
                continue

            resolved = model_index.get(name.lower())
            if resolved and os.path.abspath(resolved).startswith(os.path.abspath(mod_root)):
                continue  # lives in the mod already
            if resolved:
                needed[os.path.abspath(resolved)] = name
            else:
                missing.append(name)

    return needed, missing


# --------------------------------------------------------------------------
# the sync itself
# --------------------------------------------------------------------------

class ModPlan:
    def __init__(self, mod_id):
        self.mod_id = mod_id
        self.src = os.path.join(MODS_DIR, mod_id)
        self.dest = os.path.join(UNITY_MODS_DIR, mod_id)
        self.copies = []      # (absolute src, absolute dest)
        self.missing_models = []

    @property
    def dest_rel(self):
        return os.path.relpath(self.dest, ROOT)


def plan_mod(mod_id, model_index):
    plan = ModPlan(mod_id)

    # The mod's own files, in the same Namespace/Category/Asset-folder layout. There is no separate models/
    # pool any more: every asset folder ships its own GLB (loaded at runtime), and an FBX beside its manifest.
    for src in iter_files(plan.src):
        if not should_copy(src):
            continue

        rel = os.path.relpath(src, plan.src)
        dest = os.path.join(plan.dest, rel)
        if disabled_in_unity(plan.dest, rel):
            continue          # this category / asset folder was switched off in Unity: leave it switched off
        plan.copies.append((os.path.abspath(src), os.path.abspath(dest)))

    return plan


def disabled_in_unity(dest_root, rel):
    """True when a parent folder of `rel` has been renamed "<name>.disabled" under Assets/Mods."""
    parts = rel.replace("\\", "/").split("/")[:-1]
    cur = dest_root
    for part in parts:
        if os.path.isdir(os.path.join(cur, part + ".disabled")) and not os.path.isdir(os.path.join(cur, part)):
            return True
        cur = os.path.join(cur, part)
    return False


def existing_mod_folders():
    if not os.path.isdir(UNITY_MODS_DIR):
        return []
    return [
        d for d in os.listdir(UNITY_MODS_DIR)
        if os.path.isdir(os.path.join(UNITY_MODS_DIR, d)) and d != "_handmade"
    ]


def read_state(dest):
    path = os.path.join(dest, STATE_FILE)
    if not os.path.exists(path):
        return set()
    try:
        with io.open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return set(data.get("files", []))
    except Exception:
        return set()


def sync_mod(plan, apply_changes, only_mod):
    """Syncs one mod. Returns (copied, pruned, errors)."""
    copied = pruned = 0
    errors = []

    if apply_changes:
        os.makedirs(plan.dest, exist_ok=True)

    wanted = set()

    for src, dest in plan.copies:
        rel = os.path.relpath(dest, plan.dest)
        wanted.add(rel)

        if not apply_changes:
            exists = os.path.exists(dest)
            if not exists or os.path.getsize(src) != os.path.getsize(dest):
                log(f"    + {rel}")
            copied += 1
            continue

        try:
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.copy2(src, dest)
            copied += 1
        except Exception as exc:
            errors.append(f"copy {rel}: {exc}")

    # Prune: files this mod previously owned that it no longer provides.
    previous = read_state(plan.dest)
    stale = previous - wanted

    for rel in sorted(stale):
        dest = os.path.join(plan.dest, rel)
        if not os.path.exists(dest):
            continue
        if apply_changes:
            try:
                os.remove(dest)
                remove_empty_dirs(os.path.dirname(dest), plan.dest)
                pruned += 1
            except Exception as exc:
                errors.append(f"prune {rel}: {exc}")
        else:
            log(f"    - {rel}  (stale)")
            pruned += 1

    if apply_changes:
        remove_empty_dirs(plan.dest, plan.dest)
        write_state(plan.dest, wanted)

    return copied, pruned, errors


def write_state(dest, files):
    path = os.path.join(dest, STATE_FILE)
    try:
        with io.open(path, "w", encoding="utf-8") as f:
            json.dump({
                "generated": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "mod": os.path.basename(dest),
                "files": sorted(files),
            }, f, indent=2)
            f.write("\n")
    except Exception as exc:
        log(f"    ! could not write {STATE_FILE}: {exc}")


def remove_empty_dirs(start, stop):
    """Removes now-empty directories up to (not including) `stop`."""
    stop = os.path.abspath(stop)
    cur = os.path.abspath(start)
    while cur != stop and cur.startswith(stop):
        try:
            if os.path.isdir(cur) and not os.listdir(cur):
                os.rmdir(cur)
                cur = os.path.dirname(cur)
            else:
                break
        except OSError:
            break


# --------------------------------------------------------------------------
# resources mirror
# --------------------------------------------------------------------------

def mirror_prefabs_to_resources(apply_changes):
    """
    Copies every generated prefab from Assets/Mods/<id>/prefabs/ into
    Assets/Resources/Mods/<id>/prefabs/ so Resources.Load can reach it at runtime.

    Only *.prefab (and its .meta) is mirrored - geometry stays in Assets/Mods,
    where Unity imports it once as a mesh the prefab references. Duplicating the
    FBX into Resources would bloat the build for no benefit.

    Returns the number of prefab files mirrored (or that would be).
    """
    if not os.path.isdir(UNITY_MODS_DIR):
        return 0
    count = 0
    for mod_id in sorted(os.listdir(UNITY_MODS_DIR)):
        prefab_src = os.path.join(UNITY_MODS_DIR, mod_id, "prefabs")
        if not os.path.isdir(prefab_src):
            continue
        dest = os.path.join(UNITY_RESOURCES_DIR, mod_id, "prefabs")

        for fn in sorted(os.listdir(prefab_src)):
            src = os.path.join(prefab_src, fn)
            if not os.path.isfile(src):
                continue
            count += 1
            if not apply_changes:
                continue
            os.makedirs(dest, exist_ok=True)
            shutil.copy2(src, os.path.join(dest, fn))

        # Prune mirrored prefabs whose source is gone (prefab deleted/renamed).
        if apply_changes and os.path.isdir(dest):
            src_names = set(os.listdir(prefab_src))
            for fn in os.listdir(dest):
                if fn not in src_names:
                    try:
                        os.remove(os.path.join(dest, fn))
                    except OSError:
                        pass
    # Drop Resources/Mods folders for mods that no longer exist at all.
    if apply_changes and os.path.isdir(UNITY_RESOURCES_DIR):
        live = set(os.listdir(UNITY_MODS_DIR))
        for name in os.listdir(UNITY_RESOURCES_DIR):
            if name not in live:
                shutil.rmtree(os.path.join(UNITY_RESOURCES_DIR, name), ignore_errors=True)

    return count
# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="Sync mods into the Unity project.")
    ap.add_argument("--apply", action="store_true",
                    help="write changes (default is a dry run)")
    ap.add_argument("--mod", help="sync only this mod id")
    args = ap.parse_args()

    if not os.path.isdir(MODS_DIR):
        log(f"No mods directory at {MODS_DIR}")
        return 1

    log(f"Sync mods -> Unity Assets{'  [APPLY]' if args.apply else '  [DRY RUN]'}\n")

    model_index = {}   # no longer used: models are not copied into a separate pool

    # A folder renamed with a disabled suffix (the same convention Unity's
    # ModDiscovery honours) counts as REMOVED, not as a new mod - otherwise a
    # disabled mod would be synced into Unity under its suffixed name.
    def is_disabled(name):
        low = name.lower()
        return low.endswith(".disabled") or low.endswith(".hidden") or low.startswith("disabled_")

    mod_ids = sorted(
        d for d in os.listdir(MODS_DIR)
        if os.path.isdir(os.path.join(MODS_DIR, d))
        and d not in SKIP_DIRS
        and not is_disabled(d)
    )
    if args.mod:
        mod_ids = [m for m in mod_ids if m == args.mod]

    for name in sorted(os.listdir(MODS_DIR)):
        if os.path.isdir(os.path.join(MODS_DIR, name)) and is_disabled(name):
            log(f"  (skipping disabled mod '{name}')")

    total_copies = total_prunes = 0
    all_errors = []

    for mod_id in mod_ids:
        plan = plan_mod(mod_id, model_index)
        log(f"  {mod_id}  ({len(plan.copies)} file(s))")

        if plan.missing_models:
            for name in plan.missing_models:
                log(f"    ! model not found in catalog: {name}")

        copied, pruned, errors = sync_mod(plan, args.apply, args.mod)
        total_copies += copied
        total_prunes += pruned
        all_errors.extend(errors)

        if not args.apply and copied == 0 and pruned == 0:
            log("    (up to date)")

    # Mods that vanished from mods/ but still have a Unity folder. Never when syncing a single mod (--mod):
    # every other mod would look "gone" and be deleted.
    gone = [] if args.mod else [d for d in existing_mod_folders() if d not in mod_ids]
    if gone:
        log("\n  Removed mods (folder exists in Unity but not in mods/):")
        for mod_id in sorted(gone):
            dest = os.path.join(UNITY_MODS_DIR, mod_id)
            if args.apply:
                shutil.rmtree(dest, ignore_errors=True)
                if os.path.isfile(dest + ".meta"):
                    os.remove(dest + ".meta")
                log(f"    - deleted {os.path.relpath(dest, ROOT)}")
            else:
                log(f"    - would delete {os.path.relpath(dest, ROOT)}")
            total_prunes += 1

    # Mirror generated prefabs into Resources/Mods so the RUNTIME resolver can
    # load them by path. Resources.Load only sees a folder named "Resources", so
    # the Editor-generated prefabs in Assets/Mods/<id>/prefabs/ are copied here.
    mirrored = mirror_prefabs_to_resources(args.apply)

    log("")
    log(f"  files copied/synced : {total_copies}")
    log(f"  files pruned        : {total_prunes}")
    log(f"  prefabs mirrored    : {mirrored}")

    if all_errors:
        log("")
        for e in all_errors:
            log(f"  ERROR {e}")
        return 1

    if not args.apply:
        log("\n  Dry run only. Re-run with --apply to make these changes.")
    else:
        log("\n  Done. Reopen Unity (or press Ctrl+R) to import the new files.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
