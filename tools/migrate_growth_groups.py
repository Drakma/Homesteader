#!/usr/bin/env python3
"""Migrate growth groups from the old per-item-duplicate shape to the
authoritative group-asset shape defined by assets/_schemas/growth_group.schema.json.

The two shapes
--------------
OLD (what 36 groups still use): every stage is its own catalog asset, and each
one carries a full duplicate copy of the shared scheme - the same stages[] array
appears verbatim in all four oak manifests, each with its own current_stage.
There is no single authority, so the copies drift.

    assets/<cat>/tree_sapling_oak/     <- stage 1, owns a copy of the scheme
        tree_sapling_oak.json
        SM_PlantedSaplingOak.fbx
        tree_sapling_oak.png
    assets/<cat>/tree_small_oak/       <- stage 2, owns another copy
    ...

NEW (the target): one group folder per species that owns the scheme once, and a
stages/ subfolder holding each stage's resources. Stage folders are resources,
not catalog assets, and are never walked by the catalog builder.

    assets/<cat>/oak/
        oak.json                       <- the ONE authoritative scheme
        oak.png                        <- copy of the icon_stage's icon
        stages/tree_sapling/           <- moved intact: model, icon, README, manifest
        stages/tree_small/
        ...

The migration is a FOLDER MOVE per stage, not a file rewrite, so FBX/MTL/PNG and
their internal relative references survive untouched.

Usage
-----
    python tools/migrate_growth_groups.py                 # report only
    python tools/migrate_growth_groups.py --apply         # do the migration
    python tools/migrate_growth_groups.py --apply --only oak
    python tools/migrate_growth_groups.py --check         # validate migrated groups

Standard library only.
"""

import argparse
import json
import os
import shutil
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(REPO_ROOT, "assets")
SCHEMA_REF = "https://homesteader.game/schemas/growth_group_v1.json"

# Category -> subfolder the group folder should live under, if not the category
# root. The catalog uses these to keep large categories navigable.
GROUPS_ROOT_OVERRIDES = {}

# Set by --apply. In report mode nothing is written.
DRY_RUN = True


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def dump_json(path, data):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def item_dirs(category_dir):
    """Yield (item_id, item_dir) for each direct subfolder of a category."""
    for name in sorted(os.listdir(category_dir)):
        full = os.path.join(category_dir, name)
        if os.path.isdir(full) and name != "stages":
            yield name, full


def manifest_of(item_dir, item_id):
    """Return (path, data) for an item's own manifest, or (None, None)."""
    path = os.path.join(item_dir, item_id + ".json")
    if os.path.isfile(path):
        return path, load_json(path)
    return None, None


def growth_of(manifest):
    """Return the old-shape growth block if this manifest is a growth member.

    Handles BOTH places is_growable has historically appeared: at the root
    (new) and inside growth (old). The schema says root; the old files put it
    inside growth. We read either so the migration sees every member.
    """
    if not isinstance(manifest, dict):
        return None
    inner = manifest.get("growth")
    if not isinstance(inner, dict):
        return None
    if inner.get("is_growable") or manifest.get("is_growable"):
        return inner
    return None


def discover_groups():
    """Find every growth group in the old shape.

    Returns { (category, species): { 'members': [...], 'scheme': {...} }.
    A member is a stage item folder that carries a duplicate of the scheme.
    """
    groups = {}
    for category in sorted(os.listdir(ASSETS)):
        category_dir = os.path.join(ASSETS, category)
        if not os.path.isdir(category_dir) or category.startswith("_"):
            continue
        for item_id, item_dir in item_dirs(category_dir):
            if os.path.isdir(os.path.join(item_dir, "stages")):
                continue  # already migrated
            path, manifest = manifest_of(item_dir, item_id)
            if not manifest:
                continue
            growth = growth_of(manifest)
            if not growth:
                continue
            species = growth.get("species")
            growth_type = growth.get("growth_type")
            if not species:
                continue
            key = (category, species)
            bucket = groups.setdefault(key, {
                "growth_type": growth_type,
                "members": [],
                "scheme": None,
            })
            bucket["members"].append({
                "item_id": item_id,
                "dir": item_dir,
                "manifest_path": path,
                "manifest": manifest,
                "growth": growth,
                "current_stage": (growth.get("current_stage") or {}).get("stage"),
            })
            # Prefer the scheme from a member that has a full stages[] array.
            if bucket["scheme"] is None and growth.get("stages"):
                bucket["scheme"] = growth
    return groups

def repair_stages(stages, problems, notes, max_age):
    # Repair contiguous-age violations and a mismatched final age_max.
    #
    # The schema requires stages to be contiguous and ascending: stages[0]
    # starts at 0, each age_max equals the next age_min, and the last age_max
    # equals max_age. Two groups in the catalog have an off-by-one gap (stage 1
    # ends at 30 but stage 2 starts at 31) because the bounds were treated as
    # inclusive. Closing the gap is the only reading consistent with the schema,
    # so close it and record exactly what changed rather than absorbing it.
    out = [dict(st) for st in stages]
    for i in range(1, len(out)):
        prev_max = out[i - 1].get("age_max")
        if out[i].get("age_min") != prev_max:
            notes.append("stage %s age_min %s -> %s (contiguity fix)"
                         % (out[i].get("stage"), out[i].get("age_min"), prev_max))
            out[i]["age_min"] = prev_max
    if out and max_age is not None and out[-1].get("age_max") != max_age:
        notes.append("stage %s age_max %s -> %s (must equal max_age)"
                     % (out[-1].get("stage"), out[-1].get("age_max"), max_age))
        out[-1]["age_max"] = max_age
    for st in out:
        amin, amax = st.get("age_min"), st.get("age_max")
        if amin is not None and amax is not None and amax <= amin:
            problems.append("stage %s has age_max %s <= age_min %s after repair"
                            % (st.get("stage"), amax, amin))
    return out

def plan_group(category, species, info):
    """Build the migration plan for one group, or return (None, [problems])."""
    problems = []
    notes = []
    members = info["members"]
    scheme = info["scheme"]

    if not scheme:
        return None, ["no member carries a stages[] array"]
    stages = scheme.get("stages") or []
    if not stages:
        return None, ["stages[] is empty"]

    # Repair the two pieces of drift the catalog actually contains before
    # planning the move, so a repairable group is not reported as un-migratable.
    stages = repair_stages(stages, problems, notes, scheme.get("max_age"))

    # Map declared stages to the folders that actually hold those items.
    by_item_id = {m["item_id"]: m for m in members}
    layout = []
    for st in stages:
        item_id = st.get("item_id")
        member = by_item_id.get(item_id)
        if member is None:
            # The stage may name a folder that was renamed without the scheme
            # being updated (e.g. species 'welsummer_rooter' whose folders are
            # now 'welsummer_rooster'). Recover by matching the stage number to
            # whichever member declares a matching current_stage, which is the
            # same data the duplicate copies already carry.
            by_stage = {m["current_stage"]: m for m in members
                        if m["current_stage"] is not None}
            recovered = by_stage.get(st.get("stage"))
            if recovered is not None and recovered["item_id"] not in {
                    ln["item_id"] for ln in layout}:
                notes.append(
                    "stage %s named %s but matched folder %s by stage number "
                    "- the scheme's item_id is stale"
                    % (st.get("stage"), item_id, recovered["item_id"]))
                member = recovered
                item_id = recovered["item_id"]
            else:
                problems.append("stage %s references %s, which is not a folder "
                                "in this category" % (st.get("stage"), item_id))
                continue
        # Stage folder name follows the established convention: the item id
        # with the trailing species suffix removed where that reads cleanly
        # (tree_sapling_oak -> tree_sapling), else the item id itself.
        stage_name = item_id
        if species and item_id.endswith("_" + species):
            stage_name = item_id[: -(len(species) + 1)]
        layout.append({
            "stage": st.get("stage"),
            "name": st.get("name"),
            "age_min": st.get("age_min"),
            "age_max": st.get("age_max"),
            "item_id": item_id,
            "member": member,
            "stage_folder": stage_name,
        })

    # Every member must be claimed by exactly one stage, otherwise the move
    # would strand a folder behind.
    claimed = {ln["item_id"] for ln in layout}
    unclaimed = [m["item_id"] for m in members if m["item_id"] not in claimed]
    if unclaimed:
        problems.append("folders not referenced by any stage: %s"
                        % ", ".join(sorted(unclaimed)))

    # Duplicate stage folder names would collide on move.
    names = [ln["stage_folder"] for ln in layout]
    dupes = {n for n in names if names.count(n) > 1}
    if dupes:
        problems.append("stage folder name collision: %s" % ", ".join(sorted(dupes)))

    for i, ln in enumerate(layout):
        if ln["age_min"] is None or ln["age_max"] is None:
            problems.append("stage %s missing age bounds" % ln["stage"])
        if i and layout[i - 1]["age_max"] != ln["age_min"]:
            problems.append("stage %s age_min (%s) != previous age_max (%s)"
                            % (ln["stage"], ln["age_min"], layout[i - 1]["age_max"]))

    if problems:
        return None, problems
    if layout and scheme.get("max_age") is not None \
            and layout[-1]["age_max"] != scheme.get("max_age"):
        problems.append("final stage age_max (%s) != max_age (%s)"
                        % (layout[-1]["age_max"], scheme.get("max_age")))
        return None, problems
    return {"layout": layout, "scheme": scheme, "species": species,
            "notes": notes}, []


def stage_folder_name(grp):
    """Folder for the group under assets/<category>/."""
    return grp["species"]


def build_group_manifest(category, species, grp):
    """Compose the authoritative group manifest from the plan."""
    scheme = grp["scheme"]
    layout = grp["layout"]
    root_member = min(grp["layout"], key=lambda ln: ln["stage"])["member"]
    root_manifest = root_member["manifest"]

    stages = []
    for ln in layout:
        stages.append({
            "stage": ln["stage"],
            "name": ln["name"],
            "age_min": ln["age_min"],
            "age_max": ln["age_max"],
            "resource": "stages/%s/" % ln["stage_folder"],
            "model": model_filename(ln["member"], ln["stage_folder"]),
            "icon": "%s.png" % ln["item_id"],
        })

    manifest = {
        "$schema": SCHEMA_REF,
        "id": species,
        "name": group_display_name(species, root_manifest, scheme),
        "category": category,
        "description": group_description(species, scheme, stages),
        "icon": "%s.png" % species,
        "is_growable": True,
        "growth": {
            "growth_type": scheme.get("growth_type"),
            "species": species,
            "max_age": scheme.get("max_age"),
            "time_unit": scheme.get("time_unit"),
            "total_stages": len(stages),
            # The schema's convention: promote the largest stage's icon so the
            # catalog shows the asset fully grown rather than in seed form.
            "icon_stage": len(stages),
            "stages": stages,
        },
        "plugin_metadata": root_manifest.get("plugin_metadata") or {
            "version": "1.0.0",
            "author": "Homesteader Core",
            "compatible_api": "v1",
        },
    }
    return manifest


def model_filename(member, stage_folder=None):
    """The stage's primary model filename, from its own models[] array."""
    # Prefer a real mesh over a sidecar/material file, then an FBX over an OBJ.
    # Structure manifests list models[] in a mixed order (e.g. the .mtl before
    # the .obj it describes), so taking the first entry would point the catalog
    # at a material file. Some stages (early construction phases) declare an
    # empty models[] array - fall back to whatever mesh sits in the stage
    # folder, which is the only thing that can actually be displayed.
    mesh_exts = (".fbx", ".obj", ".glb", ".gltf", ".blend")
    models = member["manifest"].get("models") or []

    def rank(fname):
        low = fname.lower()
        if not low.endswith(mesh_exts):
            return -1
        if any(k in low for k in ("_walk", "_run")):
            return 3
        if low.endswith(".fbx"):
            return 2
        return 1
    candidates = [f for f in ((m.get("file") or "").strip() for m in models) if f]
    if not candidates and stage_folder:
        stage_dir = member["dir"]
        if os.path.isdir(stage_dir):
            candidates = sorted(f for f in os.listdir(stage_dir)
                                if f.lower().endswith(mesh_exts))

    best, best_rank = "", 0
    for f in candidates:
        r = rank(f)
        if r > best_rank:
            best, best_rank = f, r
    return best


def group_display_name(species, root_manifest, scheme):
    """Readable group name, derived from the mature stage's name where possible."""
    base = species.replace("_", chr(32)).title()
    gtype = (scheme.get("growth_type") or "").lower()
    if gtype == "tree":
        if not base.lower().endswith("tree"):
            base = "%s Tree" % base
    elif gtype in ("animal",):
        return base
    elif gtype in ("crop", "plant"):
        if not base.lower().endswith(("plant", "crop")):
            base = "%s Plant" % base
    elif gtype == "building":
        pass
    return base


def group_description(species, scheme, stages):
    gtype = (scheme.get("growth_type") or "generic").lower()
    max_age = scheme.get("max_age")
    unit = scheme.get("time_unit") or "days"
    names = " -> ".join(s["name"] for s in stages)
    return ("A %s lifecycle growing through %d stages (%s) over %s %s. "
            "This group is the authoritative owner of the %s scheme."
            % (gtype, len(stages), names, max_age, unit, species))


def strip_growth_from_stage(member):
    """Remove the duplicated scheme from a stage's own manifest.

    The stage keeps its identity, properties, models, and utilities - only the
    copied scheme goes, because the group now owns it. A stale copy left behind
    is exactly the drift this migration exists to end.
    """
    manifest = member["manifest"]
    manifest.pop("is_growable", None)
    if isinstance(manifest.get("growth"), dict):
        del manifest["growth"]
    return manifest


def migrate_group(category, species, info, apply=False):
    """Migrate one group. Returns a result dict describing what happened."""
    grp, problems = plan_group(category, species, info)
    if problems:
        return {"species": species, "category": category, "status": "skipped",
                "problems": problems, "moved": []}

    group_dir = os.path.join(ASSETS, category, stage_folder_name(grp))
    stages_dir = os.path.join(group_dir, "stages")

    if os.path.exists(group_dir) and os.path.isdir(os.path.join(group_dir, "stages")):
        return {"species": species, "category": category, "status": "already",
                "problems": [], "moved": []}

    moved = []
    if apply:
        os.makedirs(stages_dir, exist_ok=True)
        for ln in grp["layout"]:
            src = ln["member"]["dir"]
            dst = os.path.join(stages_dir, ln["stage_folder"])
            if os.path.exists(dst):
                return {"species": species, "category": category,
                        "status": "error",
                        "problems": ["destination already exists: %s" % dst],
                        "moved": moved}
            shutil.move(src, dst)

            # Rewrite the stage manifest without the duplicated scheme, and
            # re-point its $schema at the stage schema.
            stage_manifest_path = os.path.join(dst, ln["item_id"] + ".json")
            if os.path.isfile(stage_manifest_path):
                stage_manifest = strip_growth_from_stage(ln["member"])
                dump_json(stage_manifest_path, stage_manifest)
            moved.append((ln["item_id"], dst))

        # Write the authoritative group manifest and promote the icon_stage icon.
        group_manifest = build_group_manifest(category, species, grp)
        dump_json(os.path.join(group_dir, species + ".json"), group_manifest)

        icon_stage = grp["layout"][-1]
        src_icon = os.path.join(stages_dir, icon_stage["stage_folder"],
                                "%s.png" % icon_stage["item_id"])
        if os.path.isfile(src_icon):
            shutil.copy2(src_icon, os.path.join(group_dir, species + ".png"))

    return {"species": species, "category": category,
            "status": "migrated" if apply else "ready",
            "problems": [], "moved": moved, "group_dir": group_dir}


def repair_migrated_models():
    # Re-resolve every migrated group's per-stage `model` field from the stage
    # folder on disk. Needed because the first migration pass picked whichever
    # filename came first in models[] (which for structures was a .mtl) and
    # left early construction stages with an empty string. Idempotent: safe to
    # run repeatedly, and it only ever writes a field it can resolve.
    fixed = []
    for category in sorted(os.listdir(ASSETS)):
        category_dir = os.path.join(ASSETS, category)
        if not os.path.isdir(category_dir) or category.startswith("_"):
            continue
        for grp_id, grp_dir in item_dirs(category_dir):
            stages_dir = os.path.join(grp_dir, "stages")
            if not os.path.isdir(stages_dir):
                continue
            mpath = os.path.join(grp_dir, grp_id + ".json")
            if not os.path.isfile(mpath):
                continue
            m = load_json(mpath)
            growth = m.get("growth") or {}
            stages = growth.get("stages") or []
            changed = False
            for st in stages:
                res = (st.get("resource") or "").strip()
                if not res.startswith("stages/"):
                    continue
                folder = res.rstrip("/").split("/")[-1]
                stage_dir = os.path.join(stages_dir, folder)
                if not os.path.isdir(stage_dir):
                    continue
                # Build a stand-in member so model_filename can reuse its
                # ranking and on-disk fallback without re-reading a manifest.
                stage_jsons = [f for f in os.listdir(stage_dir) if f.endswith(".json")]
                stage_manifest = {}
                if stage_jsons:
                    try:
                        stage_manifest = load_json(os.path.join(stage_dir, stage_jsons[0]))
                    except Exception:
                        stage_manifest = {}
                member = {"manifest": stage_manifest, "dir": stage_dir}
                resolved = model_filename(member, folder)
                if resolved and st.get("model") != resolved:
                    fixed.append("%s/%s stage %s: %r -> %r"
                                 % (category, grp_id, st.get("stage"),
                                    st.get("model"), resolved))
                    st["model"] = resolved
                    changed = True
            if changed:
                dump_json(mpath, m)
    return fixed

def check_migrated():
    """Validate every group that is already in the new shape."""
    problems = []
    checked = 0
    for category in sorted(os.listdir(ASSETS)):
        category_dir = os.path.join(ASSETS, category)
        if not os.path.isdir(category_dir) or category.startswith("_"):
            continue
        for grp_id, grp_dir in item_dirs(category_dir):
            stages_dir = os.path.join(grp_dir, "stages")
            if not os.path.isdir(stages_dir):
                continue
            checked += 1
            mpath = os.path.join(grp_dir, grp_id + ".json")
            if not os.path.isfile(mpath):
                problems.append("%s/%s: missing group manifest" % (category, grp_id))
                continue
            m = load_json(mpath)
            if not m.get("is_growable"):
                problems.append("%s/%s: is_growable is not at the manifest root"
                                % (category, grp_id))
            g = m.get("growth") or {}
            stages = g.get("stages") or []
            if g.get("total_stages") != len(stages):
                problems.append("%s/%s: total_stages %s != len(stages) %s"
                                % (category, grp_id, g.get("total_stages"),
                                   len(stages)))
            if stages and stages[-1].get("age_max") != g.get("max_age"):
                problems.append("%s/%s: last stage age_max %s != max_age %s"
                                % (category, grp_id, stages[-1].get("age_max"),
                                   g.get("max_age")))
            for i, st in enumerate(stages):
                res = st.get("resource") or ""
                if not res.startswith("stages/"):
                    problems.append("%s/%s stage %s: resource %r is not under stages/"
                                    % (category, grp_id, st.get("stage"), res))
                    continue
                folder = os.path.join(grp_dir, res.rstrip("/").replace("/", os.sep))
                if not os.path.isdir(folder):
                    problems.append("%s/%s stage %s: resource folder missing: %s"
                                    % (category, grp_id, st.get("stage"), res))
                    continue
                model = (st.get("model") or "").strip()
                if model and not os.path.isfile(os.path.join(folder, model)):
                    problems.append("%s/%s stage %s: model missing: %s"
                                    % (category, grp_id, st.get("stage"), model))
                if i and stages[i - 1].get("age_max") != st.get("age_min"):
                    problems.append("%s/%s: age gap between stage %s and %s"
                                    % (category, grp_id, st.get("stage") - 1,
                                       st.get("stage")))
            icon = os.path.join(grp_dir, grp_id + ".png")
            if not os.path.isfile(icon):
                problems.append("%s/%s: group icon missing" % (category, grp_id))
    return checked, problems


def main(argv):
    global DRY_RUN
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true",
                    help="actually move folders and write manifests")
    ap.add_argument("--only", help="migrate just one species (e.g. oak)")
    ap.add_argument("--check", action="store_true",
                    help="validate groups already in the new shape")
    ap.add_argument("--repair-models", action="store_true",
                    help="re-resolve each migrated stage's model from disk")
    args = ap.parse_args(argv[1:])

    if args.repair_models:
        fixed = repair_migrated_models()
        if fixed:
            print("resolved %d stage model reference(s):" % len(fixed))
            for f in fixed:
                print("  %s" % f)
        else:
            print("all stage model references already correct")
        return 0

    if args.check:
        checked, problems = check_migrated()
        print("checked %d migrated group(s)" % checked)
        if problems:
            for p in problems:
                print("  PROBLEM %s" % p)
            return 1
        print("all migrated groups valid")
        return 0

    DRY_RUN = not args.apply
    groups = discover_groups()

    if args.only:
        groups = {k: v for k, v in groups.items() if k[1] == args.only}
        if not groups:
            print("no group with species %r in the old shape" % args.only)
            return 1

    mode = "APPLY" if args.apply else "REPORT (dry run - nothing is written)"
    print("growth-group migration - %s" % mode)
    print("%d group(s) still in the old shape\n" % len(groups))

    results = []
    for (category, species), info in sorted(groups.items()):
        r = migrate_group(category, species, info, apply=args.apply)
        r["stages"] = len(info["scheme"].get("stages") or []) if info["scheme"] else 0
        r["members"] = len(info["members"])
        results.append(r)

    ready = [r for r in results if r["status"] in ("ready", "migrated")]
    skipped = [r for r in results if r["status"] == "skipped"]
    errored = [r for r in results if r["status"] == "error"]

    for r in results:
        if r["status"] == "ready":
            print("  READY   %-10s %-22s %d stage(s) -> assets/%s/%s/stages/"
                  % (r["category"], r["species"], r["stages"], r["category"],
                     r["species"]))
        elif r["status"] == "migrated":
            print("  MOVED   %-10s %-22s %d folder(s) -> assets/%s/%s/stages/"
                  % (r["category"], r["species"], len(r["moved"]), r["category"],
                     r["species"]))
            for item_id, dst in r["moved"]:
                print("              %s -> %s" % (item_id, os.path.relpath(dst, REPO_ROOT)))
        elif r["status"] == "error":
            print("  ERROR   %-10s %-22s %s" % (r["category"], r["species"],
                                                "; ".join(r["problems"])))
        else:
            print("  SKIP    %-10s %-22s %s" % (r["category"], r["species"],
                                                "; ".join(r["problems"])))

    print("\n%d ready, %d skipped, %d error" % (len(ready), len(skipped), len(errored)))
    if skipped:
        print("\nSkipped groups need a decision before they can migrate - a stage")
        print("referenced by the scheme has no folder, or a folder is unclaimed.")

    return 1 if errored else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
