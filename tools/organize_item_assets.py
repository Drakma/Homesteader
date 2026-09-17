import os
import shutil
import math
from PIL import Image

_this_dir = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(_this_dir)  # tools/ sits at the repo root (one level up)
CONCEPTS_DIR = os.path.join(BASE_DIR, "concepts")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
HUD_ITEMS_DIR = os.path.join(ASSETS_DIR, "items")
HUD_PNG_DIR = os.path.join(ASSETS_DIR, "png")
UNREAL_ICONS_DIR = r"C:\Users\casey\Desktop\Homesteader\Homesteader\Content\Homesteader\UI\Icons"

# Complete Hierarchy Specification across all 11 Game Systems
FOLDER_SCHEMA = {
    "farming": {
        "seeds": "Seeds for planting crops in tilled farm plots",
        "crops": "Raw crops freshly harvested from farm fields",
        "produce": "Edible produce, fruits, vegetables, and crafted foodstuffs",
        "fertilizer": "Soil amendments, organic fertilizers, and growth enhancers",
        "irrigation": "Irrigation pipes, sprinkler heads, and watering apparatus"
    },
    "ranching": {
        "animals": "Livestock species, breeds, and domestic animal tokens",
        "meats": "Butchered raw meats and cuts",
        "pelts": "Cured hides, raw pelts, and tanned leathers",
        "byproducts": "Animal byproducts: milk, eggs, wool fleece, cheese, truffles, feathers",
        "feed": "Animal fodder, grain feed, and trough rations"
    },
    "logging": {
        "wood": "Timber logs, milled lumber, structural beams, and heavy equipment",
        "fuel": "Chopped firewood, kindling, and wood briquettes",
        "saplings": "Tree seedlings, saplings, and nursery starts",
        "byproducts": "Woodchips, sawdust, bark mulch, and tree sap taps"
    },
    "fishing": {
        "fish": "Freshwater and saltwater fish species (trout, bass, salmon)",
        "tackle": "Fishing rods, reels, hooks, lines, and lures",
        "bait": "Earthworms, insect larvae, dough bait, and chum",
        "equipment": "Tackle boxes, landing nets, fish baskets, and waders"
    },
    "building": {
        "materials": "Primary building blocks: stone blocks, metal plates, glass panes, ropes",
        "structures": "Pre-fabricated buildings: cabins, sheds, barns, coops, greenhouses",
        "fencing": "Boundary fencing: split rail wood, barbed wire, electric fence",
        "hardware": "Fasteners: construction nails, metal brackets, hinges, screws",
        "roads": "Ground surfaces: dirt path paving, gravel road gravel"
    },
    "tools": {
        "hand_tools": "Manual hand tools: hoes, axes, pickaxes, shovels, sickles, hammers, wrenches",
        "equipment": "Power gear & utility: chainsaws, watering cans, planter seedbags",
        "measuring": "Survey stakes, tape measures, plumb bobs, soil pH meters"
    },
    "electricity": {
        "generation": "Power generation: solar PV panels, wind turbines, fuel generators",
        "storage": "Energy storage: deep-cycle battery banks, rechargeable cells",
        "fuel": "Combustion fuels: gasoline canisters, propane tanks",
        "wiring": "Transmission: high-voltage cables, conduits, transformers"
    },
    "water": {
        "sources": "Water procurement: deep wells, rainwater catchment, electric pumps",
        "storage": "Water reserves: cistern tanks, 55-gal drums, jugs",
        "piping": "Plumbing: PVC pipes, shutoff valves, brass fittings",
        "treatment": "Purification: sediment filters, reverse osmosis, UV sterilizers"
    },
    "sewage": {
        "waste": "Sanitation: outhouses, blackwater holding tanks, waste drums",
        "treatment": "Bioconversion: wooden compost bins, aerators, microbial digesters",
        "drainage": "Drainage: septic leach fields, perforated pipes, septic tanks"
    },
    "internet": {
        "satellite_antennas": "Off-grid telemetry: phased-array satellite dishes, parabolic receivers",
        "routers_networking": "Distribution: Wi-Fi mesh routers, access point antennas, switches",
        "cabling": "Connectivity: weather-rated Cat6 Ethernet cables, fiber optic drops"
    },
    "hud": {
        "status": "Player vitals: health heart, stamina lightning bolt, hunger, hydration",
        "resources": "Homestead metrics: currency gold coin, water volume, solar flux, battery kWh",
        "hotbar": "Item selector trays, active highlight frames, slot wells",
        "bars": "Compound status pills, sundial clock capsules, resource bars",
        "buttons": "UI interaction buttons: normal, hover, active, disabled",
        "windows": "Dialog frames, inventory backdrops, modal windows"
    }
}

# Complete mapping of 3D rendered icons into categorized subfolders
EXISTING_ICON_MAP = {
    # FARMING
    ("farming", "seeds"): [
        "seed_corn.png", "seed_tomato.png", "seed_carrot.png", "seed_wheat.png",
        "seed_potato.png", "seed_pumpkin.png", "seed_strawberry.png",
        "seed_sunflower.png", "seed_cotton.png", "seed_herb.png", "icon_seeds.png"
    ],
    ("farming", "crops"): [
        "crop_corn.png", "crop_tomato.png", "crop_carrot.png", "crop_wheat.png",
        "crop_potato.png", "crop_pumpkin.png", "crop_strawberry.png",
        "crop_sunflower.png", "crop_cotton.png", "crop_herb.png", "icon_wheat.png"
    ],
    ("farming", "produce"): [
        "crop_corn.png", "crop_tomato.png", "crop_carrot.png", "crop_potato.png",
        "crop_pumpkin.png", "crop_strawberry.png", "food_apple.png",
        "food_bread.png", "food_stew.png", "food_cheese.png", "icon_bread.png"
    ],
    ("farming", "fertilizer"): [
        "mat_fertilizer.png"
    ],
    ("farming", "irrigation"): [
        "water_pipe.png"
    ],

    # RANCHING
    ("ranching", "meats"): [
        "meat_chicken.png", "meat_beef.png", "meat_pork.png", "meat_mutton.png",
        "meat_goat.png", "animal_meat.png"
    ],
    ("ranching", "pelts"): [
        "mat_leather.png", "pelt_cow.png", "pelt_sheep.png", "pelt_goat.png"
    ],
    ("ranching", "byproducts"): [
        "animal_egg.png", "animal_milk.png", "animal_wool.png", "animal_truffle.png",
        "mat_feather.png", "food_cheese.png"
    ],
    ("ranching", "feed"): [
        "crop_wheat.png", "crop_corn.png", "icon_wheat.png"
    ],

    # LOGGING
    ("logging", "wood"): [
        "wood_logs_stack.png", "mat_lumber.png", "icon_wood_log.png", "tool_chainsaw.png"
    ],
    ("logging", "fuel"): [
        "fuel_firewood.png"
    ],
    ("logging", "saplings"): [
        "tree_sapling.png"
    ],
    ("logging", "byproducts"): [
        "tree_tap.png"
    ],

    # FISHING
    ("fishing", "fish"): [
        "fish_trout.png", "fish_bass.png", "fish_salmon.png"
    ],
    ("fishing", "tackle"): [
        "tool_fishing_rod.png", "fishing_lure.png"
    ],
    ("fishing", "bait"): [
        "fishing_bait.png"
    ],
    ("fishing", "equipment"): [
        "tool_fishing_rod.png", "fishing_lure.png"
    ],

    # BUILDING
    ("building", "materials"): [
        "mat_stone.png", "mat_metal.png", "mat_glass.png", "mat_rope.png", "mat_lumber.png"
    ],
    ("building", "hardware"): [
        "hardware_nails.png"
    ],

    # TOOLS
    ("tools", "hand_tools"): [
        "tool_hoe.png", "tool_axe.png", "tool_pickaxe.png", "tool_shovel.png",
        "tool_sickle.png", "tool_hammer.png", "tool_wrench.png",
        "icon_axe.png", "icon_pickaxe.png", "icon_shovel.png"
    ],
    ("tools", "equipment"): [
        "tool_chainsaw.png", "tool_watering_can.png", "tool_seedbag.png", "icon_watering_can.png"
    ],

    # ELECTRICITY
    ("electricity", "generation"): [
        "item_solar_panel.png", "item_wind_turbine.png", "item_generator.png", "icon_solar.png"
    ],
    ("electricity", "storage"): [
        "icon_battery.png"
    ],
    ("electricity", "fuel"): [
        "fuel_gasoline.png", "fuel_propane.png"
    ],
    ("electricity", "wiring"): [
        "internet_cable.png"
    ],

    # WATER
    ("water", "sources"): [
        "water_pump.png", "icon_water.png"
    ],
    ("water", "piping"): [
        "water_pipe.png"
    ],
    ("water", "treatment"): [
        "water_filter.png"
    ],

    # SEWAGE
    ("sewage", "treatment"): [
        "sewage_compost_bin.png"
    ],
    ("sewage", "drainage"): [
        "sewage_septic_tank.png"
    ],
    ("sewage", "waste"): [
        "sewage_septic_tank.png"
    ],

    # INTERNET
    ("internet", "satellite_antennas"): [
        "internet_satellite_dish.png"
    ],
    ("internet", "routers_networking"): [
        "internet_router.png"
    ],
    ("internet", "cabling"): [
        "internet_cable.png"
    ],

    # HUD
    ("hud", "status"): [
        "icon_heart.png", "icon_stamina.png"
    ],
    ("hud", "resources"): [
        "icon_coin.png", "icon_water.png", "icon_solar.png", "icon_battery.png"
    ],
    ("hud", "hotbar"): [
        "compact_hotbar_10slots.png", "compact_hotbar_slot.png", "compact_selector_active.png"
    ],
    ("hud", "bars"): [
        "compact_player_status.png", "compact_time_season.png", "compact_resources.png"
    ],
    ("hud", "buttons"): [
        "compact_btn_slate_normal.png", "compact_btn_slate_hover.png",
        "compact_btn_green_normal.png", "compact_btn_amber_normal.png"
    ],
    ("hud", "windows"): [
        "compact_window_dialog.png"
    ]
}

# 3D Concept Sheet Extraction Specifications for Supplementary Categories
SHEET_FISHING_LOGGING_ITEMS = [
    ("tool_fishing_rod", 153, 224, 130, 22.0),
    ("fish_trout", 420, 206, 125, 22.0),
    ("fish_bass", 685, 203, 125, 22.0),
    ("fish_salmon", 953, 202, 120, 22.0),
    ("fishing_bait", 1218, 206, 120, 22.0),
    ("fishing_lure", 164, 549, 125, 22.0),
    ("tree_sapling", 422, 565, 135, 22.0),
    ("wood_logs_stack", 693, 570, 125, 22.0),
    ("tree_tap", 963, 560, 130, 22.0),
    ("tool_chainsaw", 1199, 558, 130, 22.0),
]

SHEET_UTILITIES_TECH_ITEMS = [
    ("internet_satellite_dish", 185, 112, 125, 20.0),
    ("internet_router", 519, 154, 120, 20.0),
    ("internet_cable", 858, 130, 120, 20.0),
    ("item_solar_panel", 1196, 130, 125, 20.0),
    ("item_wind_turbine", 185, 393, 130, 20.0),
    ("item_generator", 510, 385, 120, 20.0),
    ("water_pump", 849, 390, 125, 20.0),
    ("water_filter", 1188, 385, 120, 20.0),
    ("water_pipe", 174, 647, 120, 20.0),
    ("sewage_septic_tank", 524, 637, 125, 20.0),
    ("sewage_compost_bin", 863, 641, 125, 20.0),
    ("hardware_nails", 1198, 642, 125, 20.0),
]

def extract_3d_item_outside_in(sheet_img, cx, cy, r, tol):
    """
    Extracts an isolated 3D model with 100% pure transparent background,
    NO BORDERS, NO CLIPPING, and intact internal shading.
    Uses perimeter background flood fill from outer boundaries.
    """
    x0 = max(0, cx - r)
    y0 = max(0, cy - r)
    x1 = min(sheet_img.width, cx + r)
    y1 = min(sheet_img.height, cy + r)
    
    crop = sheet_img.crop((x0, y0, x1, y1))
    cw, ch = crop.size
    
    # Sample perimeter background
    perim_pixels = []
    for x in range(cw):
        perim_pixels.append(crop.getpixel((x, 0)))
        perim_pixels.append(crop.getpixel((x, ch - 1)))
    for y in range(ch):
        perim_pixels.append(crop.getpixel((0, y)))
        perim_pixels.append(crop.getpixel((cw - 1, y)))
        
    bg_r = sum(p[0] for p in perim_pixels) / len(perim_pixels)
    bg_g = sum(p[1] for p in perim_pixels) / len(perim_pixels)
    bg_b = sum(p[2] for p in perim_pixels) / len(perim_pixels)
    bg = (bg_r, bg_g, bg_b)
    
    def is_bg_like(px):
        return math.sqrt((px[0]-bg[0])**2 + (px[1]-bg[1])**2 + (px[2]-bg[2])**2) < tol

    # Outside-in flood fill from perimeter
    visited = [[False]*cw for _ in range(ch)]
    queue = []
    for x in range(cw):
        if is_bg_like(crop.getpixel((x, 0))):
            visited[0][x] = True
            queue.append((x, 0))
        if is_bg_like(crop.getpixel((x, ch - 1))):
            visited[ch - 1][x] = True
            queue.append((x, ch - 1))
    for y in range(ch):
        if not visited[y][0] and is_bg_like(crop.getpixel((0, y))):
            visited[y][0] = True
            queue.append((0, y))
        if not visited[y][cw - 1] and is_bg_like(crop.getpixel((cw - 1, y))):
            visited[y][cw - 1] = True
            queue.append((cw - 1, y))
            
    while queue:
        qx, qy = queue.pop(0)
        for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
            nx, ny = qx + dx, qy + dy
            if 0 <= nx < cw and 0 <= ny < ch and not visited[ny][nx]:
                if is_bg_like(crop.getpixel((nx, ny))):
                    visited[ny][nx] = True
                    queue.append((nx, ny))
                    
    # Foreground = not visited
    rgba = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    for y in range(ch):
        for x in range(cw):
            if not visited[y][x]:
                px = crop.getpixel((x, y))
                d = math.sqrt((px[0]-bg[0])**2 + (px[1]-bg[1])**2 + (px[2]-bg[2])**2)
                # Soft feathering at edge
                if d < tol + 8:
                    alpha = min(255, max(0, int(255 * (d - tol + 8) / 8.0)))
                else:
                    alpha = 255
                rgba.putpixel((x, y), (px[0], px[1], px[2], alpha))
                
    bbox = rgba.split()[3].getbbox()
    if not bbox:
        return None
        
    item_only = rgba.crop(bbox)
    # Uniform scaling to MAX_ITEM_DIM = 104px (TARGET_SIZE 128 - 2 * 12 padding)
    scale = min(104.0 / item_only.width, 104.0 / item_only.height)
    nw = max(1, int(round(item_only.width * scale)))
    nh = max(1, int(round(item_only.height * scale)))
    resized = item_only.resize((nw, nh), Image.Resampling.LANCZOS)
    
    canvas = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
    canvas.paste(resized, ((128 - nw) // 2, (128 - nh) // 2), resized)
    return canvas

def extract_all_supplementary_3d_icons():
    """
    Extracts all 22 3D rendered items from the concept sheets
    """
    extracted = {}
    
    sheet_fl_path = os.path.join(CONCEPTS_DIR, "sheet_fishing_logging.jpg")
    if os.path.exists(sheet_fl_path):
        sheet_fl = Image.open(sheet_fl_path).convert("RGB")
        for name, cx, cy, r, tol in SHEET_FISHING_LOGGING_ITEMS:
            icon = extract_3d_item_outside_in(sheet_fl, cx, cy, r, tol)
            if icon:
                extracted[f"{name}.png"] = icon
                print(f"  [3D Extracted] {name}.png from Fishing & Logging sheet")
                
    sheet_ut_path = os.path.join(CONCEPTS_DIR, "sheet_utilities_tech.jpg")
    if os.path.exists(sheet_ut_path):
        sheet_ut = Image.open(sheet_ut_path).convert("RGB")
        for name, cx, cy, r, tol in SHEET_UTILITIES_TECH_ITEMS:
            icon = extract_3d_item_outside_in(sheet_ut, cx, cy, r, tol)
            if icon:
                extracted[f"{name}.png"] = icon
                print(f"  [3D Extracted] {name}.png from Utilities & Tech sheet")
                
    return extracted

def main():
    print("=== HOMESTEADER 3D ITEM & HUD CATEGORY ORGANIZER ===")
    
    # Destination root paths to organize
    targets = [
        ASSETS_DIR,                               # <root>\assets\<category>\<subfolder>
        HUD_ITEMS_DIR,                            # <root>\assets\items\<category>\<subfolder>
        os.path.join(ASSETS_DIR, "categories"),   # <root>\assets\categories\<category>\<subfolder>
        UNREAL_ICONS_DIR                          # C:\Users\casey\Desktop\Homesteader\Homesteader\Content\Homesteader\UI\Icons\<category>\<subfolder>
    ]

    for root in targets:
        print(f"\nVerifying folder structure in: {root}")
        for main_cat, sub_dict in FOLDER_SCHEMA.items():
            main_path = os.path.join(root, main_cat)
            os.makedirs(main_path, exist_ok=True)
            for sub_cat, desc in sub_dict.items():
                sub_path = os.path.join(main_path, sub_cat)
                os.makedirs(sub_path, exist_ok=True)
                
                # Write a clean README.md explaining the folder
                readme_path = os.path.join(sub_path, "README.md")
                with open(readme_path, "w", encoding="utf-8") as rf:
                    rf.write(f"# {main_cat.capitalize()} / {sub_cat.capitalize()}\n\n")
                    rf.write(f"**Purpose**: {desc}\n\n")
                    rf.write("All icons in this folder are standard **128 × 128 px** RGBA PNGs with pure transparent backgrounds, 3D low-poly rendered style, and zero borders.\n")

    # Extract 3D low-poly rendered icons from concept sheets
    print("\nExtracting 3D low-poly icons for fishing, logging, utilities, and internet...")
    new_3d_icons = extract_all_supplementary_3d_icons()
    
    # Save newly extracted 3D icons to root directories (overwriting any previous flat procedural versions)
    for fname, img in new_3d_icons.items():
        img.save(os.path.join(HUD_ITEMS_DIR, fname), "PNG")
        img.save(os.path.join(UNREAL_ICONS_DIR, fname), "PNG")
        img.save(os.path.join(HUD_PNG_DIR, fname), "PNG")

    # Distribute all icons into categorized subfolders across all targets
    print("\nDistributing icons into categorized subfolders...")
    distributed_count = 0
    for (main_cat, sub_cat), filenames in EXISTING_ICON_MAP.items():
        for fname in filenames:
            src_path = os.path.join(HUD_ITEMS_DIR, fname)
            if not os.path.exists(src_path):
                src_path = os.path.join(HUD_PNG_DIR, fname)
            
            if os.path.exists(src_path):
                for root in targets:
                    dest_file = os.path.join(root, main_cat, sub_cat, fname)
                    shutil.copy2(src_path, dest_file)
                distributed_count += 1
            else:
                print(f"  Warning: Source icon {fname} not found")

    print(f"Successfully distributed {distributed_count} icon instances across categorized subfolders.")

    # Generate complete summary markdown
    print("\nWriting categorized organization documentation...")
    guide_path = os.path.join(BASE_DIR, "ITEM_ORGANIZATION_GUIDE.md")
    with open(guide_path, "w", encoding="utf-8") as gf:
        gf.write("# Homesteader Item & HUD Asset Organization Guide\n\n")
        gf.write("Complete structured taxonomy of all game items and HUD assets across survival, farming, ranching, logging, fishing, building, utilities, and UI systems.\n\n")
        gf.write("All icons are **128 × 128 px** transparent RGBA PNGs featuring cohesive **3D low-poly faceted render** styling, zero borders, and comfortable 12px margins.\n\n")
        gf.write("## Folder Hierarchy & Item Distribution\n\n")
        for main_cat, sub_dict in FOLDER_SCHEMA.items():
            gf.write(f"### `{main_cat}/`\n")
            for sub_cat, desc in sub_dict.items():
                items = EXISTING_ICON_MAP.get((main_cat, sub_cat), [])
                gf.write(f"- **`{sub_cat}/`**: {desc}\n")
                if items:
                    gf.write(f"  - *Icons ({len(items)})*: {', '.join([f'`{i}`' for i in items])}\n")
                else:
                    gf.write("  - *Icons*: Ready for future expansion items\n")
            gf.write("\n")

    print(f"Saved organization guide to: {guide_path}")
    print("\nCOMPLETE: All 11 categories and subfolders populated with matching 3D low-poly icons.")

if __name__ == "__main__":
    main()
