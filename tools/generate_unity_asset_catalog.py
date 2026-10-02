import os
import sys
import json

ROOT = r"C:\Users\casey\Desktop\Homesteader"
ASSETS_DIR = os.path.join(ROOT, "assets")
OUTPUT_PATH = os.path.join(ROOT, "Homesteader", "Assets", "Resources", "AssetCatalog.json")

# The chip label a phone shop shows for an item of each asset category (an item can override it with properties.store_category)
STORE_CATEGORY_LABELS = {
    "appliances": "Appliances", "building": "Building", "electricity": "Electronics", "farming": "Farming", "food": "Food",
    "fuel": "Fuel", "ingredients": "Ingredients", "internet": "Telecom", "logging": "Logging", "materials": "Materials",
    "ranching": "Ranching", "structures": "Structures", "tools": "Tools", "vehicles": "Vehicles",
}

EXCLUDED_CATEGORIES = {"ground", "hud", "hud_kit", "peds", "models_legacy", "textures", "biomes"}

def main():
    print("Indexing asset catalog from:", ASSETS_DIR)
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    categories = sorted([
        d for d in os.listdir(ASSETS_DIR)
        if os.path.isdir(os.path.join(ASSETS_DIR, d))
        and not d.startswith("_")
        and d not in EXCLUDED_CATEGORIES
    ])

    all_items = []
    cat_counts = {}

    for cat in categories:
        cat_dir = os.path.join(ASSETS_DIR, cat)
        items = sorted([
            d for d in os.listdir(cat_dir)
            if os.path.isdir(os.path.join(cat_dir, d))
            and not d.startswith("_")
        ])
        cat_counts[cat] = 0

        for item_folder in items:
            manifest_path = os.path.join(cat_dir, item_folder, f"{item_folder}.json")
            if not os.path.exists(manifest_path):
                # Fallback manifest if named item.json
                for fn in os.listdir(os.path.join(cat_dir, item_folder)):
                    if fn.endswith(".json") and not fn.startswith("_"):
                        manifest_path = os.path.join(cat_dir, item_folder, fn)
                        break

            item_data = {
                "id": item_folder,
                "name": item_folder.replace("_", " ").title(),
                "category": cat,
                "description": "",
                "icon": f"{item_folder}.png",
                "max_stack": 64
            }

            if os.path.exists(manifest_path):
                try:
                    with open(manifest_path, "r", encoding="utf-8") as f:
                        m = json.load(f)
                    item_data["id"] = m.get("id", item_folder)
                    item_data["name"] = m.get("name", item_folder.replace("_", " ").title())
                    item_data["category"] = m.get("category", cat)
                    item_data["description"] = m.get("description", "")
                    item_data["icon"] = m.get("icon", f"{item_folder}.png")
                    props = m.get("properties", {})
                    if props and isinstance(props, dict):
                        ms = props.get("max_stack_size")
                        if ms and isinstance(ms, int) and ms > 0:
                            item_data["max_stack"] = ms
                        wk = props.get("weight_kg")
                        if isinstance(wk, (int, float)) and not isinstance(wk, bool):
                            item_data["weight_kg"] = float(wk)
                        if props.get("support_surface") is True:
                            item_data["support_surface"] = True
                        # Where the phone shops sell it (the manifest is the only place this lives): properties.stores, with a
                        # per-shop category / unit / price in store_overrides when one shop differs.
                        stores = props.get("stores")
                        if props.get("is_buyable") is True and isinstance(stores, list) and stores:
                            overrides = props.get("store_overrides") if isinstance(props.get("store_overrides"), dict) else {}
                            base_price = props.get("base_value", 0)
                            base_price = float(base_price) if isinstance(base_price, (int, float)) and not isinstance(base_price, bool) else 0.0
                            listings = []
                            for sid in stores:
                                ov = overrides.get(sid) if isinstance(overrides.get(sid), dict) else {}
                                price = ov.get("price", base_price)
                                listings.append({
                                    "store": str(sid),
                                    "category": str(ov.get("category") or props.get("store_category") or STORE_CATEGORY_LABELS.get(cat, cat.title())),
                                    "unit": str(ov.get("unit") or props.get("sale_unit") or "ea"),
                                    "price": float(price) if isinstance(price, (int, float)) and not isinstance(price, bool) else base_price,
                                })
                            item_data["store_listings"] = listings
                    # the fruiting component schema: a plant picked by hand one fruit at a time
                    fb = m.get("fruiting")
                    if isinstance(fb, dict):
                        item_data["fruiting_tools"] = [str(x) for x in fb.get("tools", [])] if isinstance(fb.get("tools"), list) else []
                        item_data["fruiting_drops"] = [str(x) for x in fb.get("drops", [])] if isinstance(fb.get("drops"), list) else []
                        rd = fb.get("regrow_days")
                        item_data["fruiting_regrow_days"] = float(rd) if isinstance(rd, (int, float)) and not isinstance(rd, bool) else 8.0
                    # the container component schema (its own top-level block)
                    cb = m.get("container")
                    if isinstance(cb, dict):
                        cap = cb.get("capacity_kg")
                        if isinstance(cap, (int, float)) and not isinstance(cap, bool) and cap > 0:
                            item_data["container_capacity_kg"] = float(cap)
                            sl = cb.get("stacking_limit")
                            if isinstance(sl, (int, float)) and not isinstance(sl, bool) and sl > 1:
                                item_data["container_stacking_limit"] = int(sl)
                            acc = cb.get("accepts")
                            item_data["container_accepts"] = [str(x) for x in acc] if isinstance(acc, list) else []
                            item_data["container_show_fill"] = bool(cb.get("show_fill", True))
                            item_data["container_single_type"] = bool(cb.get("single_type", False))
                            item_data["container_disposable"] = bool(cb.get("disposable", False))
                    # a structure built in stages (foundation -> framing -> walls -> complete): each stage's manifest holds its
                    # construction_recipe (materials consumed), required_tools (groups, any one of each, not consumed) and size
                    g = m.get("growth")
                    if cat == "structures" and isinstance(g, dict) and isinstance(g.get("stages"), list):
                        stages_out = []
                        item_dir = os.path.join(cat_dir, item_folder)
                        for st in g["stages"]:
                            res = str(st.get("resource", "")).strip("/").replace("/", os.sep)
                            sd = None
                            stage_dir = os.path.join(item_dir, res)
                            if res and os.path.isdir(stage_dir):
                                for fn in sorted(os.listdir(stage_dir)):
                                    if fn.endswith(".json") and not fn.startswith("_"):
                                        with open(os.path.join(stage_dir, fn), "r", encoding="utf-8") as sf:
                                            sd = json.load(sf)
                                        break
                            if not isinstance(sd, dict):
                                continue
                            scf = sd.get("category_fields", {}) if isinstance(sd.get("category_fields"), dict) else {}
                            dims = scf.get("dimensions_m", {}) if isinstance(scf.get("dimensions_m"), dict) else {}
                            recipe = []
                            # The group's own stage entry is authoritative; the stage manifest is the fallback.
                            src_recipe = st.get("construction_recipe", scf.get("construction_recipe", [])) or []
                            for line in src_recipe:
                                if isinstance(line, dict) and isinstance(line.get("any_of"), list):
                                    # an "or" line: the stage takes any ONE alternative in full
                                    opts = [{"item_id": str(o["item_id"]), "quantity": int(o.get("quantity", 1) or 1)}
                                            for o in line["any_of"] if isinstance(o, dict) and o.get("item_id")]
                                    if opts:
                                        recipe.append({"item_id": "", "quantity": 0, "any_of": opts})
                                elif isinstance(line, dict) and line.get("item_id"):
                                    recipe.append({"item_id": str(line["item_id"]), "quantity": int(line.get("quantity", 1) or 1)})
                            groups = []
                            for grp in (st.get("required_tools", scf.get("required_tools", [])) or []):
                                if isinstance(grp, list):
                                    groups.append({"tools": [str(x) for x in grp]})
                            stages_out.append({
                                "name": str(st.get("name", "")),
                                "item_id": str(sd.get("id", "")),
                                "width": float(dims.get("width", 0) or 0),
                                "depth": float(dims.get("depth", 0) or 0),
                                "height": float(dims.get("height", 0) or 0),
                                "recipe": recipe,
                                "tool_groups": groups,
                            })
                        if stages_out:
                            item_data["construction_stages"] = stages_out
                    # the liquid_container component schema: holds one liquid by volume
                    lb = m.get("liquid_container")
                    if isinstance(lb, dict):
                        lcap = lb.get("capacity_l")
                        if isinstance(lcap, (int, float)) and not isinstance(lcap, bool) and lcap > 0:
                            item_data["liquid_capacity_l"] = float(lcap)
                            lacc = lb.get("accepts")
                            item_data["liquid_accepts"] = [str(x) for x in lacc] if isinstance(lacc, list) else []
                    # a liquid itself (category liquids): colour, opacity and weight per litre (properties.weight_kg)
                    if cat == "liquids":
                        cf = m.get("category_fields", {})
                        if isinstance(cf, dict):
                            if isinstance(cf.get("color"), str):
                                item_data["liquid_color"] = cf["color"]
                            op = cf.get("opacity_pct")
                            if isinstance(op, (int, float)) and not isinstance(op, bool):
                                item_data["liquid_opacity_pct"] = float(op)
                            item_data["liquid_flammable"] = bool(cf.get("flammable", False))
                except Exception as ex:
                    print(f"Warning reading {manifest_path}: {ex}")

            all_items.append(item_data)
            cat_counts[cat] += 1

    catalog_dict = {
        "items": all_items
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(catalog_dict, f, indent=2)

    print(f"Successfully generated {OUTPUT_PATH}")
    print(f"Total items: {len(all_items)} across {len(categories)} categories:")
    for c, cnt in cat_counts.items():
        print(f"  {c}: {cnt}")

if __name__ == "__main__":
    main()

