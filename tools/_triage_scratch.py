"""Triage the scratch debris in tools/.

Classifies untracked files into: definite scratch, probably scratch, and KEEP
(anything that looks like real project tooling). Writes a report only - it
deletes nothing. Review the report, then run with --delete to act.

Usage:
    python tools/_triage_scratch.py            # report only (safe)
    python tools/_triage_scratch.py --delete   # act on the SAFE bucket
"""
import json
import os
import re
import subprocess
import sys

REPO = r"C:\Users\casey\Desktop\Homesteader"
TOOLS = os.path.join(REPO, "tools")
REPORT = os.path.join(TOOLS, "_triage_report.txt")

# Names that are unambiguously agent scratch: leading underscore + a verb.
SCRATCH_PREFIX = re.compile(
    r"^_(check|find|grep|poll|smoke|step|run|scan|tail|read|inspect|probe|verify|"
    r"list|search|size|test|qwen|git|srv|curl|debug|diagnose|dry|kill|touch|"
    r"make|mark|copy|tail|peek|regen|update|enable|launch|remove|vfix|vorder|"
    r"qa_|cleanup|scratch|post_|prep_|extract|measure|perfect|crop|find_)",
    re.IGNORECASE,
)

# Extensions that are pure scratch output.
SCRATCH_EXT = {".log", ".err", ".out"}

# Crop/preview image prefixes - generated scratch, never source art.
SCRATCH_IMG_PREFIX = re.compile(
    r"^(app_card_|apps1_|apps2_|card\d|cell_|icon_r|icon_apps2_|lbl_r|p_apps|"
    r"debug_row|test_clean_|test_exact_|test_icon_|test_proper_|test_text_|"
    r"bm_from|exact_bm|perfect_board|vitals_preview|c0_full|sheet_)",
    re.IGNORECASE,
)

# Anything matching these is REAL tooling and must never be deleted.
NEVER_DELETE = {
    "python.cmd",
    "server.py",
    "app.py",
    "render_icon_from_model.py",
    "blender_to_glb.py",
    "convert_models_to_glb.py",
    "procedural_asset.py",
    "generate_all_biomes.py",
    "sync_mods_to_unity.py",
    "package_catalog_as_mods.py",
    "import_asset_catalog_to_unity.py",
    "build_exe.py",
    "check_syntax.py",
    "decimate_clutter.py",
    "apply_glb_to_manifests.py",
    "build_pointers.py",
    "build_remaining_meshes.py",
    "free_generator.py",
    "meshy_client.py",
    "generate_request_icon.py",
    "regen_icons.py",
    "splice_icons.py",
    "run_batch.py",
    "process_queued_batch.py",
    "see_image.py",
    "vision_mcp.py",
    "reference_images.py",
    "find_duplicates.py",
    "diagnose_mesh.py",
    "trash_store.py",
    "qa_biomes.mjs",
    "male_ped_apose_concept.py",
    "male_ped_fbx_to_glb.py",
    "install_qwen_image.py",
    "qwen_image_local.py",
    "migrate_food_and_fuel.py",
    "migrate_ingredients.py",
    "migrate_materials.py",
    "migrate_naming_conventions.py",
    "migrate_naming_conventions_pass2.py",
    "glb_conversion_log.jsonl",
    "glb_conversion_run.log",
    "requirements_qwen_image.txt",
    "drive_unity_menu.ps1",
    "deploy_cursors.py",
    "gen_old_farmer.py",
    "build_full_catalog" ,
}

# Directories that are real working trees, not debris.
NEVER_DELETE_DIRS = {".diffusers-src", ".glb_work", ".scratch", ".venv", "venv"}


def untracked():
    out = subprocess.run(
        [r"C:\Program Files\Git\cmd\git.exe", "status", "--porcelain", "--", "tools/"],
        cwd=REPO, capture_output=True, text=True,
    ).stdout
    items = []
    for line in out.splitlines():
        if line.startswith("?? "):
            items.append(line[3:].strip().strip('"'))
    return items


def classify(path):
    rel = path.replace("tools/", "", 1).replace("\\", "/")
    name = os.path.basename(rel)
    ext = os.path.splitext(name)[1].lower()

    if name in NEVER_DELETE:
        return "KEEP", "known real tooling"
    if rel.split("/")[0] in NEVER_DELETE_DIRS:
        return "KEEP", "real working tree"

    # A bare .py/.mjs with no underscore prefix and a real-sounding name.
    if ext in (".py", ".mjs", ".cmd", ".bat") and not name.startswith("_"):
        # Could still be scratch (e.g. qwen_state2.ps1) - check the prefix rule.
        if SCRATCH_PREFIX.match(name):
            return "SCRATCH", "underscore/verb scratch name"
        return "KEEP", "non-underscore script, possibly real"

    if ext in SCRATCH_EXT:
        return "SCRATCH", "log/err/out output"

    if ext in (".png", ".jpg", ".jpeg") and SCRATCH_IMG_PREFIX.match(name):
        return "SCRATCH", "generated crop/preview"

    if name.startswith("_"):
        if SCRATCH_PREFIX.match(name):
            return "SCRATCH", "underscore scratch pattern"
        return "MAYBE", "underscore but unrecognised verb"

    if ext in (".png", ".jpg", ".jpeg"):
        return "MAYBE", "image output, prefix unrecognised"

    # Reference sheets / coordinate dumps are usually worth keeping.
    if name.startswith("sheet_") or "pointers" in name:
        return "KEEP", "reference/pointer data"

    return "MAYBE", "unclassified"


def main():
    do_delete = "--delete" in sys.argv
    items = untracked()

    buckets = {"SCRATCH": [], "MAYBE": [], "KEEP": []}
    reasons = {}
    for it in items:
        if not it.startswith("tools/"):
            continue
        full = os.path.join(REPO, it.replace("/", os.sep))
        if os.path.isdir(full):
            buckets["KEEP"].append(it)
            reasons[it] = "directory"
            continue
        b, why = classify(it)
        buckets[b].append(it)
        reasons[it] = why

    lines = []
    lines.append(f"Triage of tools/ untracked files ({len(items)} entries)")
    lines.append("=" * 68)
    for b in ("SCRATCH", "MAYBE", "KEEP"):
        lines.append("")
        lines.append(f"--- {b} ({len(buckets[b])}) ---")
        for it in sorted(buckets[b]):
            lines.append(f"  {it}   [{reasons[it]}]")

    lines.append("")
    lines.append("=" * 68)
    lines.append(f"SCRATCH: {len(buckets['SCRATCH'])}  MAYBE: {len(buckets['MAYBE'])}  KEEP: {len(buckets['KEEP'])}")

    text = "\n".join(lines)
    with open(REPORT, "w", encoding="utf-8") as f:
        f.write(text)
    print(text)
    print()
    print(f"report written to {REPORT}")

    if not do_delete:
        print()
        print("DRY RUN - nothing deleted. Re-run with --delete to remove SCRATCH only.")
        return

    freed = 0
    removed = 0
    for it in buckets["SCRATCH"]:
        full = os.path.join(REPO, it.replace("/", os.sep))
        try:
            freed += os.path.getsize(full)
            os.remove(full)
            removed += 1
        except OSError as e:
            print(f"  could not remove {it}: {e}")
    print()
    print(f"deleted {removed} files, freed {freed/1024:.0f} KB")
    print(f"MAYBE ({len(buckets['MAYBE'])}) and KEEP ({len(buckets['KEEP'])}) left untouched.")


if __name__ == "__main__":
    main()
