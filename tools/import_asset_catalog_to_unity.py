import os
import sys
import json
import shutil
import time

ROOT = r"C:\Users\casey\Desktop\Homesteader"
SRC_ASSETS_DIR = os.path.join(ROOT, "assets")
DST_UNITY_DIR = os.path.join(ROOT, "Homesteader", "Assets", "AssetCatalog")

# Categories explicitly excluded:
# - ground (per prompt)
# - HUD / hud_kit (per prompt)
# - peds (per prompt)
# - internal/non-catalog folders: _*, models_legacy, textures
EXCLUDED_CATEGORIES = {"ground", "hud", "hud_kit", "peds", "models_legacy", "textures"}

# Valid extensions to import into Unity
VALID_EXTENSIONS = {
    ".json", ".png", ".jpg", ".jpeg", ".tga", 
    ".fbx", ".obj", ".glb", ".gltf", ".mtl",
    ".mat", ".anim", ".controller", ".txt", ".md"
}

def is_group_item(item_dir, item_name):
    # Rule 5 in operating guidelines: groups have stages/ or manifest with stages[]
    if os.path.exists(os.path.join(item_dir, "stages")):
        return True
    manifest = os.path.join(item_dir, f"{item_name}.json")
    if os.path.exists(manifest):
        try:
            with open(manifest, "r", encoding="utf-8") as f:
                d = json.load(f)
                if "stages" in d or "growth_group" in d:
                    return True
                if d.get("type") in ("growth_group", "structure_group"):
                    return True
        except Exception:
            pass
    return False

def main():
    t0 = time.time()
    print("=" * 60)
    print("IMPORTING ASSET CATALOG INTO UNITY")
    print("=" * 60)
    print(f"Source: {SRC_ASSETS_DIR}")
    print(f"Destination: {DST_UNITY_DIR}")
    print(f"Excluded categories: {sorted(EXCLUDED_CATEGORIES)}")

    os.makedirs(DST_UNITY_DIR, exist_ok=True)

    all_categories = sorted([
        d for d in os.listdir(SRC_ASSETS_DIR)
        if os.path.isdir(os.path.join(SRC_ASSETS_DIR, d))
        and not d.startswith("_")
        and d not in EXCLUDED_CATEGORIES
    ])

    print(f"Found {len(all_categories)} target categories: {', '.join(all_categories)}\n")

    imported_categories = 0
    imported_items = 0
    skipped_groups = 0
    copied_files_count = 0

    manifest_summary = {}

    for cat in all_categories:
        cat_src = os.path.join(SRC_ASSETS_DIR, cat)
        cat_dst = os.path.join(DST_UNITY_DIR, cat)
        os.makedirs(cat_dst, exist_ok=True)

        items = sorted([
            it for it in os.listdir(cat_src)
            if os.path.isdir(os.path.join(cat_src, it))
        ])

        cat_imported_items = 0
        cat_skipped_groups = 0

        for it in items:
            it_src = os.path.join(cat_src, it)
            if is_group_item(it_src, it):
                cat_skipped_groups += 1
                skipped_groups += 1
                continue

            it_dst = os.path.join(cat_dst, it)
            os.makedirs(it_dst, exist_ok=True)

            # Copy all valid files
            for fname in os.listdir(it_src):
                ext = os.path.splitext(fname)[1].lower()
                if ext in VALID_EXTENSIONS:
                    src_f = os.path.join(it_src, fname)
                    dst_f = os.path.join(it_dst, fname)
                    # Only copy if destination doesn't exist or size/mtime differ
                    if not os.path.exists(dst_f) or os.path.getsize(src_f) != os.path.getsize(dst_f):
                        shutil.copy2(src_f, dst_f)
                    copied_files_count += 1

            cat_imported_items += 1
            imported_items += 1

        imported_categories += 1
        manifest_summary[cat] = {
            "items": cat_imported_items,
            "skipped_groups": cat_skipped_groups
        }
        print(f"  [{cat}] Imported {cat_imported_items} items (skipped {cat_skipped_groups} groups)")

    elapsed = time.time() - t0
    print("\n" + "=" * 60)
    print("IMPORT COMPLETE")
    print(f"Categories imported: {imported_categories}")
    print(f"Total non-group items: {imported_items}")
    print(f"Total groups excluded: {skipped_groups}")
    print(f"Files processed: {copied_files_count}")
    print(f"Elapsed time: {elapsed:.2f}s")
    print("=" * 60)

if __name__ == "__main__":
    main()
