"""
migrate_ingredients.py
Moves all ingredient_* items to assets/ingredients/
- Deletes stub-only ingredient_ folders in fishing/ (icon-only relics)
- Moves ingredient_* from food/ and farming/ to ingredients/
- Updates category field in each manifest JSON
"""
import os, shutil, json

BASE = r"C:\Users\casey\Desktop\Homesteader\assets"
DEST_CAT = "ingredients"
DEST = os.path.join(BASE, DEST_CAT)
os.makedirs(DEST, exist_ok=True)

moved = []
deleted_stubs = []
skipped = []

for src_cat in os.listdir(BASE):
    src_cat_path = os.path.join(BASE, src_cat)
    if not os.path.isdir(src_cat_path) or src_cat == DEST_CAT:
        continue
    for item_id in sorted(os.listdir(src_cat_path)):
        if not item_id.startswith("ingredient_"):
            continue
        src = os.path.join(src_cat_path, item_id)
        if not os.path.isdir(src):
            continue

        files = os.listdir(src)

        # Detect stub: only a PNG with no JSON manifest
        has_json = any(f.endswith(".json") for f in files)
        if not has_json:
            shutil.rmtree(src)
            deleted_stubs.append(f"{src_cat}/{item_id}")
            print(f"  [STUB-DEL] {src_cat}/{item_id}")
            continue

        dst = os.path.join(DEST, item_id)
        if os.path.exists(dst):
            skipped.append(f"{src_cat}/{item_id} -> already exists at ingredients/{item_id}")
            print(f"  [SKIP]     {src_cat}/{item_id} (already in ingredients/)")
            # Still remove source since dest is authoritative
            shutil.rmtree(src)
            continue

        shutil.move(src, dst)

        # Update manifest category
        manifest = os.path.join(dst, f"{item_id}.json")
        if os.path.exists(manifest):
            with open(manifest, encoding="utf-8") as f:
                data = json.load(f)
            data["category"] = DEST_CAT
            with open(manifest, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

        moved.append(f"{src_cat}/{item_id}")
        print(f"  [MOVED]    {src_cat}/{item_id} -> ingredients/{item_id}")

print(f"\nDone. Moved: {len(moved)}, Stub-deleted: {len(deleted_stubs)}, Skipped: {len(skipped)}")
print("Moved:", moved)
print("Stubs deleted:", deleted_stubs)
print("Skipped:", skipped)

