import os
import sys
import json
import shutil
import filecmp
import time

ROOT = r"C:\Users\casey\Desktop\Homesteader"
SRC_ASSETS_DIR = os.path.join(ROOT, "assets")
# The Unity project's own root (sibling to Assets/), which ModManager.cs
# already scans live via Directory.GetCurrentDirectory()/mods in the Editor -
# no Assets/ import step, so gigabytes of GLBs never touch Unity's importer.
MODS_DIR = os.path.join(ROOT, "Homesteader", "mods")

# Target categories:
EXCLUDED_CATEGORIES = {"ground", "hud", "hud_kit", "peds", "models_legacy", "textures"}

VALID_EXTENSIONS = {
    ".json", ".png", ".jpg", ".jpeg", ".tga", 
    ".fbx", ".obj", ".glb", ".gltf", ".mtl",
    ".mat", ".anim", ".controller", ".txt", ".md"
}

CATEGORY_METADATA = {
    "appliances": ("Appliances Pack", "Homestead household and workshop appliances, refrigeration, laundry, and heating equipment."),
    "building": ("Building & Construction", "Walls, roofs, trusses, windows, doors, and architectural framing components."),
    "electricity": ("Electrical & Solar Grid", "Photovoltaic solar panels, battery banks, inverters, power meters, and wiring."),
    "farming": ("Farming & Crops", "Seed packets, organic fertilizers, soil amendments, and planting supplies."),
    "fishing": ("Fishing & Tackle", "Freshwater rods, reels, cast nets, tackle boxes, and caught fish."),
    "food": ("Pantry & Provisions", "Harvested orchard fruits, farm produce, dairy, canned goods, and pantry staples."),
    "fuel": ("Fuel & Heating", "Diesel containers, bulk propane tanks, cordwood stacks, and fuel storage."),
    "ingredients": ("Culinary Ingredients", "Flours, yeasts, seasonings, culinary oils, and raw cooking staples."),
    "internet": ("Telecom & Telemetry", "Satellite dishes, cellular routers, telemetry sensors, and communication hardware."),
    "logging": ("Timber & Forestry", "Chainsaws, felling wedges, timber jacks, peaveys, and forestry equipment."),
    "materials": ("Raw Materials & Ores", "Milled timber studs, quarried stones, raw ores, ingots, and building composites."),
    "ranching": ("Livestock & Ranch Supplies", "Alfalfa hay bales, mineral salt blocks, shearing equipment, and animal care supplies."),
    "structures": ("Pre-Fab Outbuildings", "Pre-assembled storage sheds, coops, and homestead utility structures."),
    "tools": ("Hand & Power Tools", "Axes, framing hammers, hand saws, hoes, pickaxes, shovels, and mechanic wrenches."),
    "vehicles": ("Vehicles & Utility Haulers", "Homestead utility tractors, flatbed trailers, ATVs, and heavy cargo haulers."),
    "waste": ("Sanitation & Waste Processing", "Composters, septic tanks, refuse collection bins, and scrap processing equipment."),
    "water": ("Plumbing & Water Storage", "Poly rainwater cisterns, jet well pumps, filtration systems, and water distribution.")
}

def is_group_item(item_dir, item_name):
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

NAMESPACE = "homesteader"


def copy_tree_incremental(src_dir, dst_dir):
    """Copies VALID_EXTENSIONS files from src_dir into dst_dir, skipping ones that are unchanged."""
    for root, dirs, files in os.walk(src_dir):
        rel = os.path.relpath(root, src_dir)
        target_dir = os.path.join(dst_dir, rel) if rel != "." else dst_dir
        os.makedirs(target_dir, exist_ok=True)
        for fname in files:
            if os.path.splitext(fname)[1].lower() not in VALID_EXTENSIONS:
                continue
            src_f = os.path.join(root, fname)
            dst_f = os.path.join(target_dir, fname)
            if (not os.path.exists(dst_f) or os.path.getsize(src_f) != os.path.getsize(dst_f)
                    or (os.path.getsize(src_f) < 5_000_000 and not filecmp.cmp(src_f, dst_f, shallow=False))):
                shutil.copy2(src_f, dst_f)


def build_mods():
    """
    Packages the whole catalog as ONE namespaced mod:

        mods/homesteader/mod.json
        mods/homesteader/tags.json
        mods/homesteader/<category>/<asset_folder>/...
        mods/homesteader/gamerules/gamerules.json (+ textures/)

    Namespace / Category / Asset folder. Any of the three can be switched off by appending ".disabled" to
    its folder name (the Mods app does exactly that); an already-disabled folder is left alone here.
    """
    t0 = time.time()
    print("=" * 60)
    print("PACKAGING ASSET CATALOG INTO THE 'homesteader' MOD")
    print("=" * 60)

    # The old layout was one mod_<category> per category. Remove those generated folders.
    for d in os.listdir(MODS_DIR):
        if d.startswith("mod_") and os.path.isdir(os.path.join(MODS_DIR, d)):
            shutil.rmtree(os.path.join(MODS_DIR, d))
            print(f"Removed old mod folder [{d}]")

    mod_dir = os.path.join(MODS_DIR, NAMESPACE)
    os.makedirs(mod_dir, exist_ok=True)

    categories = sorted([
        d for d in os.listdir(SRC_ASSETS_DIR)
        if os.path.isdir(os.path.join(SRC_ASSETS_DIR, d))
        and not d.startswith("_")
        and d not in EXCLUDED_CATEGORIES
    ])

    mod_contents = []
    total_items = 0
    for cat in categories:
        cat_src = os.path.join(SRC_ASSETS_DIR, cat)
        items = sorted(it for it in os.listdir(cat_src) if os.path.isdir(os.path.join(cat_src, it)))
        if not items:
            continue

        cat_dst = os.path.join(mod_dir, cat)
        if os.path.isdir(cat_dst + ".disabled"):      # the whole category is switched off: leave it alone
            print(f"[{cat}] disabled - skipped")
        else:
            os.makedirs(cat_dst, exist_ok=True)
            for it in items:
                it_dst = os.path.join(cat_dst, it)
                if os.path.isdir(it_dst + ".disabled"):   # a single asset folder switched off
                    continue
                copy_tree_incremental(os.path.join(cat_src, it), it_dst)
            # prune asset folders that no longer exist in the catalog (keep .disabled ones that still do)
            for d in os.listdir(cat_dst):
                base = d[:-len(".disabled")] if d.endswith(".disabled") else d
                if base not in items and os.path.isdir(os.path.join(cat_dst, d)):
                    shutil.rmtree(os.path.join(cat_dst, d))

        mod_contents.append({
            "type": cat.rstrip("s") if cat not in ("water", "waste", "electricity", "internet", "logging", "farming", "fishing", "ranching") else cat,
            "path": cat,
            "group": cat,
        })
        total_items += len(items)
        display_name, _ = CATEGORY_METADATA.get(cat, (cat.replace("_", " ").title(), ""))
        print(f"[{cat}] {len(items)} asset folders  ({display_name})")

    # Game rules ride along as a folder of the same mod.
    rules_src = os.path.join(SRC_ASSETS_DIR, "_gamerules")
    if os.path.isdir(rules_src):
        if not os.path.isdir(os.path.join(mod_dir, "gamerules") + ".disabled"):
            copy_tree_incremental(rules_src, os.path.join(mod_dir, "gamerules"))
        mod_contents.append({"type": "gamerules", "path": "gamerules/gamerules.json"})

    manifest = {
        "id": NAMESPACE,
        "name": "Homesteader",
        "version": "1.0.0",
        "author": "Homesteader Team",
        "date": time.strftime("%Y-%m-%d"),
        "description": "The Homesteader core catalog: every category of asset, plus the game rules.",
        "namespace": NAMESPACE,
        "compatibility": {"min": "0.1.0"},
        "contents": mod_contents,
    }
    with open(os.path.join(mod_dir, "mod.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    # Ship the tag registry so runtime code can resolve "#tag" references (union-merged on load).
    tags_src = os.path.join(SRC_ASSETS_DIR, "_schemas", "material_tags.json")
    if os.path.exists(tags_src):
        shutil.copyfile(tags_src, os.path.join(mod_dir, "tags.json"))

    print("\n" + "=" * 60)
    print(f"MOD PACKAGING COMPLETE: 1 mod ('{NAMESPACE}'), {len(mod_contents)} content entries, {total_items} asset folders.")
    print(f"Elapsed: {time.time() - t0:.2f}s")
    print("=" * 60)


if __name__ == "__main__":
    build_mods()
