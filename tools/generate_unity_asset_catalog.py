import os
import sys
import json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recipe_format

ROOT = r"C:\Users\casey\Desktop\Homesteader"
ASSETS_DIR = os.path.join(ROOT, "assets")
OUTPUT_PATH = os.path.join(ROOT, "Homesteader", "Assets", "Resources", "AssetCatalog.json")

# The chip label a phone shop shows for an item of each asset category (an item can override it with properties.store_category)
STORE_CATEGORY_LABELS = {
    "appliances": "Appliances", "building": "Building", "electricity": "Electronics", "farming": "Farming", "food": "Food",
    "fuel": "Fuel", "ingredients": "Ingredients", "internet": "Telecom", "kitchen": "Kitchen", "living": "Living Room", "lighting": "Lighting", "bathroom": "Bathroom", "bedroom": "Bedroom", "laundry": "Laundry", "garage": "Garage", "dining": "Dining", "office": "Office", "logging": "Logging", "materials": "Materials",
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
                        us = props.get("uses_per_item")   # how many uses one item holds (a seed packet = 20 seeds)
                        if isinstance(us, (int, float)) and us > 1:
                            item_data["uses_per_item"] = int(us)
                        pq = props.get("pack_quantity")
                        if isinstance(pq, (int, float)) and pq > 1:
                            item_data["pack_quantity"] = int(pq)
                        for ik in ("net_ports", "rack_units", "rack_capacity_u"):   # network gear (docs/INTERNET.md)
                            iv = props.get(ik)
                            if isinstance(iv, (int, float)) and not isinstance(iv, bool) and iv > 0:
                                item_data[ik] = int(iv)
                        if props.get("poe") is True:
                            item_data["poe"] = True
                        if props.get("poe_powered") is True:
                            item_data["poe_powered"] = True
                        if m.get("category") == "internet" and isinstance(m.get("category_fields"), dict):
                            rm = m["category_fields"].get("range_m")
                            if isinstance(rm, (int, float)) and not isinstance(rm, bool) and rm > 0:
                                item_data["range_m"] = float(rm)
                        for wk in ("wire_role", "wire_kind"):
                            if isinstance(props.get(wk), str) and props.get(wk):
                                item_data[wk] = props[wk]
                        for nk in ("capacity_wh", "voltage_v", "panel_offset_m", "panel_tilt_deg", "panel_width_m", "panel_depth_m", "power_radius_tiles"):
                            nv = props.get(nk)
                            if isinstance(nv, (int, float)) and not isinstance(nv, bool) and nv > 0:
                                item_data[nk] = float(nv)
                        if isinstance(props.get("flow_lph"), (int, float)) and props.get("flow_lph") > 0:
                            item_data["flow_lph"] = float(props["flow_lph"])          # a well pump: liters an hour it lifts
                        if isinstance(props.get("heater_w"), (int, float)) and props.get("heater_w") > 0:
                            item_data["heater_w"] = float(props["heater_w"])         # a water heater: its element's watts
                        if isinstance(props.get("filter_stage"), str) and props.get("filter_stage"):
                            item_data["filter_stage"] = props["filter_stage"]        # a water filter: sediment | carbon | uv
                        if props.get("pressurized") is True:
                            item_data["pressurized"] = True                              # a pressure tank: the taps draw from it with no pump running
                        for sk in ("sewage_capacity_l", "leach_lpd", "leach_storage_l"):   # a septic tank / leach field structure (docs/SEPTIC.md)
                            sv = props.get(sk)
                            if isinstance(sv, (int, float)) and not isinstance(sv, bool) and sv > 0:
                                item_data[sk] = float(sv)
                        if props.get("is_well") is True:
                            item_data["is_well"] = True                                  # a drilled well (docs/WELLS.md)
                        if isinstance(props.get("attach_item"), str) and props.get("attach_item"):
                            item_data["attach_item"] = props["attach_item"]              # what fits on it (a well's sub panel)
                        if props.get("pushable") is True:
                            item_data["container_pushable"] = True   # pushed like a wheelbarrow (a portable generator)
                        wl = props.get("wire_length_m")
                        if isinstance(wl, (int, float)) and not isinstance(wl, bool) and wl > 0:
                            item_data["wire_length_m"] = float(wl)
                        cfp = m.get("category_fields")
                        mpw = cfp.get("max_power_w") if isinstance(cfp, dict) else None
                        if isinstance(mpw, (int, float)) and not isinstance(mpw, bool) and mpw > 0:
                            item_data["max_power_w"] = float(mpw)
                        if isinstance(cfp, dict):   # the internet (ResView): what a source brings in, what a device uses
                            bw, use = cfp.get("bandwidth_mbps"), cfp.get("bandwidth_usage_mbps")
                            if isinstance(bw, (int, float)) and not isinstance(bw, bool) and bw > 0:
                                item_data["bandwidth_mbps"] = float(bw)
                                if cfp.get("is_connected") is True and m.get("category") == "internet":
                                    item_data["net_source"] = True
                            if isinstance(use, (int, float)) and not isinstance(use, bool) and use > 0:
                                item_data["bandwidth_usage_mbps"] = float(use)
                        wcap = cfp.get("capacity_l") if isinstance(cfp, dict) else None
                        if isinstance(wcap, (int, float)) and not isinstance(wcap, bool) and wcap > 0:
                            item_data["water_capacity_l"] = float(wcap)   # a water tank: what a well's pipe can fill it with
                        wpu = cfp.get("water_per_use_l") if isinstance(cfp, dict) else None
                        if isinstance(wpu, (int, float)) and not isinstance(wpu, bool) and wpu > 0:
                            item_data["water_per_use_l"] = float(wpu)   # a fixture: liters one use takes from the building's water and sends down its drain
                        flpm = cfp.get("fuel_consumption_l_per_min") if isinstance(cfp, dict) else None
                        if isinstance(flpm, (int, float)) and not isinstance(flpm, bool) and flpm > 0 and props.get("wire_role") == "standby_generator":
                            item_data["fuel_lpm"] = float(flpm)   # a standby generator: liters of propane a minute at full load
                        pdw = cfp.get("power_draw_w") if isinstance(cfp, dict) else None
                        if isinstance(pdw, (int, float)) and not isinstance(pdw, bool) and pdw > 0:
                            item_data["power_draw_w"] = float(pdw)   # a corded electric tool: it needs a generator at the build site
                        if props.get("sawmill") is True:
                            item_data["sawmill"] = True   # a stationary sawmill (Sawmill.cs)
                        if props.get("roof_mount") is True:
                            item_data["roof_mount"] = True
                        if props.get("shelf") is True:
                            item_data["shelf"] = True   # a wall shelf: things are stood on it (Shelf.cs)
                        mca = cfp.get("max_current_a") if isinstance(cfp, dict) else None
                        if isinstance(mca, (int, float)) and not isinstance(mca, bool) and mca > 0:
                            item_data["max_current_a"] = float(mca)
                        bs = props.get("build_speed")
                        if isinstance(bs, (int, float)) and not isinstance(bs, bool) and bs > 0:
                            item_data["build_speed"] = float(bs)
                        if props.get("display_weight") is True:
                            item_data["display_weight"] = True
                        wk = props.get("weight_kg")
                        if isinstance(wk, (int, float)) and not isinstance(wk, bool):
                            item_data["weight_kg"] = float(wk)
                        bv = props.get("base_value")
                        if isinstance(bv, (int, float)) and not isinstance(bv, bool) and bv > 0:
                            item_data["base_value"] = float(bv)   # what it is worth: the market pays a share of it (MarketPickup.cs)
                        if props.get("support_surface") is True:
                            item_data["support_surface"] = True
                            if props.get("deck_heights"):
                                item_data["deck_heights"] = str(props["deck_heights"])   # a shelving unit: one top face per shelf (PalletDeck.cs)
                        # placed stacking for a plain item (bags): the game reads it as container_stacking_limit (ContainerRules.StackingLimit);
                        # a container's own container.stacking_limit, read further down, replaces it
                        psl = props.get("stacking_limit")
                        if isinstance(psl, (int, float)) and not isinstance(psl, bool) and psl > 1:
                            item_data["container_stacking_limit"] = int(psl)
                        # fences and gates (see FenceBuilder.cs)
                        if props.get("fence_style") in ("wood", "wire"):
                            item_data["fence_style"] = props["fence_style"]
                            item_data["fence_panel_m"] = float(props.get("fence_panel_m", 2.4))
                            item_data["fence_height_m"] = float(props.get("fence_height_m", 1.2))
                            item_data["fence_post_item"] = str(props.get("fence_post_item", "post_wood_round_6inch"))
                        if props.get("is_blueprint") is True:
                            item_data["is_blueprint"] = True
                        if props.get("lot_style") in ("dirt", "gravel", "asphalt", "concrete"):   # a lot blueprint (LotBuilder.cs)
                            item_data["lot_style"] = props["lot_style"]
                            item_data["lot_material_item"] = str(props.get("lot_material_item", ""))
                            item_data["lot_m2_per_item"] = float(props.get("lot_m2_per_item", 3.0))
                            if props.get("lot_binder_item"):   # a lot that is a mix (asphalt: gravel and bitumen)
                                item_data["lot_binder_item"] = str(props["lot_binder_item"])
                                item_data["lot_binder_m2_per_item"] = float(props.get("lot_binder_m2_per_item", props.get("lot_m2_per_item", 3.0)))
                        if props.get("path_material_item"):
                            item_data["path_material_item"] = str(props["path_material_item"])
                        if props.get("path_kind") in ("path", "road"):
                            item_data["path_kind"] = props["path_kind"]
                            item_data["path_width_m"] = float(props.get("path_width_m", 4.0 if props["path_kind"] == "road" else 1.2))
                            item_data["path_style"] = str(props.get("path_style", "gravel") or "gravel")
                            item_data["path_m_per_item"] = float(props.get("path_m_per_item", 2.0))
                        gw = props.get("gate_width_m")
                        if isinstance(gw, (int, float)) and not isinstance(gw, bool) and gw > 0:
                            item_data["gate_width_m"] = float(gw)
                            item_data["gate_style"] = str(props.get("gate_style", "wood") or "wood")
                        # fireplace fuel and lighters (see Fireplace.cs)
                        bm = props.get("burn_minutes")
                        if isinstance(bm, (int, float)) and not isinstance(bm, bool) and bm > 0:
                            item_data["burn_minutes"] = float(bm)
                        if props.get("lights_fires") is True:
                            item_data["lights_fires"] = True
                        # how this item makes a building look when it is used as a construction material (see StructureLook.cs)
                        if props.get("look_target"):
                            item_data["look_target"] = str(props["look_target"])
                            item_data["look_style"] = str(props.get("look_style", ""))
                            item_data["look_color"] = str(props.get("look_color", "#a8742f"))
                            item_data["look_smoothness"] = float(props.get("look_smoothness", 0.2))
                            item_data["look_metallic"] = float(props.get("look_metallic", 0.0))
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
                            item_data["container_pushable"] = bool(cb.get("pushable", False))
                            if any(k.startswith("fill_") for k in cb):
                                # where the contents show, as fractions of the model's bounds: xmin, xmax, ymin, ymax, zmin, zmax
                                item_data["container_fill_region"] = [float(cb.get("fill_%s_%s" % (a, e), 0 if e == "min" else 1)) for a in "xyz" for e in ("min", "max")]
                            item_data["container_disposable"] = bool(cb.get("disposable", False))
                            mi = cb.get("max_items")
                            if isinstance(mi, (int, float)) and not isinstance(mi, bool) and mi >= 1:
                                item_data["container_max_items"] = int(mi)
                            sp = cb.get("slot_pitch_m")
                            if isinstance(sp, (int, float)) and not isinstance(sp, bool) and sp > 0:
                                item_data["container_slot_pitch_m"] = float(sp)
                                item_data["container_slot_start_m"] = float(cb.get("slot_start_m", 0) or 0)
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
                            # The group's own stage entry is authoritative; the stage manifest is the fallback.
                            src_recipe = st.get("construction_recipe", scf.get("construction_recipe", [])) or []
                            recipe = recipe_format.for_game(recipe_format.normalize(src_recipe)[0] or [])
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
                                "build_clips": [str(x) for x in (st.get("build_clips", scf.get("build_clips", [])) or [])],
                                "build_motion": str(st.get("build_motion", scf.get("build_motion", "")) or ""),
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
                            # a container that is sold full: what is in it when bought (see liquid_container.schema.json)
                            lfill = lb.get("filled_with")
                            if isinstance(lfill, str) and lfill:
                                lfl = lb.get("filled_l")
                                item_data["liquid_filled_with"] = lfill
                                item_data["liquid_filled_l"] = float(lfl) if isinstance(lfl, (int, float)) and not isinstance(lfl, bool) and lfl > 0 else float(lcap)
                    # a liquid itself (category liquids): colour, opacity and weight per liter (properties.weight_kg)
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

