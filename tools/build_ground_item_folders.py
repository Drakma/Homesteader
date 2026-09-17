#!/usr/bin/env python3
"""
build_ground_item_folders.py
Creates complete item folders for all 32 ground items (10 clutter props + 22 modular tiles)
inside C:\\Users\\casey\\Desktop\\Homesteader\\assets\\ground\\<item_id>\\
Following Homesteader asset rules:
- <item_id>.png
- <item_id>.json (machine-readable plugin manifest)
- README.md
- 3D models (.obj, .mtl, .fbx)
And cleans up any scattered/duplicate clutter and tile folders from other categories.
"""

import os
import json
import shutil

HOMESTEADER_DIR = r"C:\Users\casey\Desktop\Homesteader"
ASSETS_DIR = os.path.join(HOMESTEADER_DIR, "assets")
GROUND_DIR = os.path.join(ASSETS_DIR, "ground")
GROUND_MODELS_DIR = os.path.join(GROUND_DIR, "models")

# Icon source paths
ICON_SEARCH_DIRS = [
    os.path.join(HOMESTEADER_DIR, "Homesteader", "Content", "Homesteader", "UI", "Icons", "ground"),
    os.path.join(HOMESTEADER_DIR, "HUD", "assets", "clutter", "ground"),
    os.path.join(GROUND_DIR, "icons"),
]

def find_icon(candidates):
    for sdir in ICON_SEARCH_DIRS:
        if not os.path.exists(sdir):
            continue
        for c in candidates:
            p = os.path.join(sdir, c + ".png")
            if os.path.exists(p):
                return p
    return None

def parse_obj_dimensions(obj_path):
    if not os.path.exists(obj_path):
        return None
    xs, ys, zs = [], [], []
    verts, faces = 0, 0
    with open(obj_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            if line.startswith('v '):
                parts = line.split()
                if len(parts) >= 4:
                    try:
                        xs.append(float(parts[1]))
                        ys.append(float(parts[2]))
                        zs.append(float(parts[3]))
                        verts += 1
                    except ValueError:
                        pass
            elif line.startswith('f '):
                faces += 1
    if not xs:
        return None
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    min_z, max_z = min(zs), max(zs)
    dx = round(max_x - min_x, 1)
    dy = round(max_y - min_y, 1)
    dz = round(max_z - min_z, 1)
    return {
        'width_x_cm': dx,
        'depth_y_cm': dy,
        'height_z_cm': dz,
        'width_x_m': round(dx / 100.0, 2),
        'depth_y_m': round(dy / 100.0, 2),
        'height_z_m': round(dz / 100.0, 2),
        'vertices': verts,
        'faces': faces,
        'bounds': (min_x, max_x, min_y, max_y, min_z, max_z)
    }

GROUND_ITEMS = [
    # Clutter Items
    ('clutter_acorns', 'Acorns Clutter', 'SM_Clutter_Acorns', ['clutter_acorns', 'SM_Clutter_Acorns'], 0.2, 99, 1.0, 'Scatter clutter of fallen autumn acorns.'),
    ('clutter_branch', 'Branch Clutter', 'SM_Clutter_Branch', ['SM_Clutter_Branch', 'clutter_branch'], 1.5, 50, 2.0, 'Fallen tree branch for kindling and natural ground scatter.'),
    ('clutter_cattails', 'Cattails Clutter', 'SM_Clutter_Cattails', ['SM_Clutter_Cattails', 'clutter_cattails'], 0.5, 99, 3.0, 'Wild wetland cattail reeds for wetland decoration and fiber.'),
    ('clutter_dirt_clump', 'Dirt Clump Clutter', 'SM_Clutter_DirtClump', ['SM_Clutter_DirtClump', 'clutter_dirt_clump', 'clutter_dirtclump'], 0.8, 99, 1.0, 'Excavated clump of topsoil scatter.'),
    ('clutter_grass_tuft', 'Grass Tuft Clutter', 'SM_Clutter_GrassTuft', ['SM_Clutter_GrassTuft', 'clutter_grass_tuft', 'clutter_grasstuft'], 0.3, 99, 1.0, 'Wild grass cluster scatter for field realism.'),
    ('clutter_leaves', 'Fallen Leaves Clutter', 'SM_Clutter_Leaves', ['clutter_leaves', 'SM_Clutter_Leaves'], 0.1, 99, 1.0, 'Autumn fallen leaves scatter.'),
    ('clutter_pebbles', 'Pebbles Clutter', 'SM_Clutter_Pebbles', ['SM_Clutter_Pebbles', 'clutter_pebbles'], 2.0, 99, 2.0, 'Small smooth stone pebbles for pathways and rockery.'),
    ('clutter_pinecones', 'Pinecones Clutter', 'SM_Clutter_Pinecones', ['clutter_pinecones', 'SM_Clutter_Pinecones'], 0.3, 99, 1.0, 'Fallen conifer pinecones for fire-starting and forest floor scatter.'),
    ('clutter_tall_grass', 'Tall Grass Clutter', 'SM_Clutter_TallGrass', ['SM_Clutter_TallGrass', 'clutter_tall_grass', 'clutter_tallgrass'], 0.4, 99, 1.0, 'Tall prairie meadow grass tuft.'),
    ('clutter_twigs', 'Twigs Clutter', 'SM_Clutter_Twigs', ['clutter_twigs', 'SM_Clutter_Twigs'], 0.3, 99, 1.0, 'Dry forest floor twigs and small sticks.'),
    
    # Modular Ground Tiles (100cm x 100cm x 20cm)
    ('tile_black_top', 'Black Top Tile', 'SM_Tile_Black_top', ['SM_Tile_Black_top', 'tile_black_top'], 30.0, 50, 15.0, 'Compacted asphalt black-top pavement tile (1m x 1m).'),
    ('tile_bricks', 'Bricks Pavement Tile', 'SM_Tile_Bricks', ['SM_Tile_Bricks', 'tile_bricks'], 25.0, 50, 20.0, 'Classic brick pavers modular ground tile (1m x 1m).'),
    ('tile_concrete', 'Concrete Slab Tile', 'SM_Tile_Concrete', ['SM_Tile_Concrete', 'tile_concrete'], 35.0, 50, 18.0, 'Smooth industrial poured concrete slab tile (1m x 1m).'),
    ('tile_deep_water', 'Deep Water Tile', 'SM_Tile_Deep_water', ['SM_Tile_Deep_water', 'tile_deep_water'], 0.0, 1, 0.0, 'Deep natural lake / river water surface tile (1m x 1m).'),
    ('tile_dirt', 'Compacted Dirt Tile', 'SM_Tile_Dirt', ['SM_Tile_Dirt', 'tile_dirt'], 20.0, 50, 5.0, 'Compacted earth homestead ground tile (1m x 1m).'),
    ('tile_farmland', 'Tilled Farmland Tile', 'SM_Tile_Farmland', ['SM_Tile_Farmland', 'tile_farmland'], 18.0, 50, 8.0, 'Aerated arable topsoil tile for planting crops (1m x 1m).'),
    ('tile_farmland_furrows', 'Farmland Furrows Tile', 'SM_Tile_Farmland_Furrows', ['SM_Tile_Farmland_Furrows', 'tile_farmland_furrows'], 18.0, 50, 10.0, 'Plowed ridged furrows for organized agricultural rows (1m x 1m).'),
    ('tile_flagstone', 'Flagstone Tile', 'SM_Tile_Flagstone', ['SM_Tile_Flagstone', 'tile_flagstone'], 28.0, 50, 22.0, 'Rustic natural cut flagstone paving tile (1m x 1m).'),
    ('tile_forest_floor', 'Forest Floor Tile', 'SM_Tile_Forest_floor', ['SM_Tile_Forest_floor', 'tile_forest_floor'], 15.0, 50, 6.0, 'Pine needle, leaf mulch, and organic woodland loam tile (1m x 1m).'),
    ('tile_grass', 'Meadow Grass Tile', 'SM_Tile_Grass', ['SM_Tile_Grass', 'tile_grass'], 16.0, 50, 6.0, 'Lush green meadow grass homestead terrain tile (1m x 1m).'),
    ('tile_gravel', 'Compacted Gravel Tile', 'SM_Tile_Gravel', ['SM_Tile_Gravel', 'tile_gravel'], 24.0, 50, 10.0, 'Interlocking crushed aggregate stone gravel tile (1m x 1m).'),
    ('tile_mud', 'Wet Mud Tile', 'SM_Tile_Mud', ['SM_Tile_Mud', 'tile_mud'], 22.0, 50, 4.0, 'Saturated soft mud ground tile with moisture sheen (1m x 1m).'),
    ('tile_path', 'Worn Path Tile', 'SM_Tile_Path', ['SM_Tile_Path', 'tile_path'], 18.0, 50, 5.0, 'Beaten footpath earth tile for trails and walkways (1m x 1m).'),
    ('tile_pond', 'Shallow Pond Tile', 'SM_Tile_Pond', ['SM_Tile_Pond', 'tile_pond'], 0.0, 1, 0.0, 'Shallow littoral pond water tile for wetland edges (1m x 1m).'),
    ('tile_road', 'Country Dirt Road Tile', 'SM_Tile_Road', ['SM_Tile_Road', 'tile_road'], 22.0, 50, 8.0, 'Graded country dirt road tile with vehicle tire tracks (1m x 1m).'),
    ('tile_road_asphalt', 'Crowned Asphalt Road Tile', 'SM_Tile_Road_Asphalt', ['SM_Tile_Road_Asphalt', 'tile_road_asphalt'], 32.0, 50, 25.0, 'Crowned asphalt roadway tile with camber drainage (1m x 1m).'),
    ('tile_sand', 'River Sand Tile', 'SM_Tile_Sand', ['SM_Tile_Sand', 'tile_sand'], 20.0, 50, 6.0, 'Fine riverbed / shoreline mineral sand tile (1m x 1m).'),
    ('tile_snow', 'Snow Pack Tile', 'SM_Tile_Snow', ['SM_Tile_Snow', 'tile_snow'], 12.0, 50, 4.0, 'Cold winter snow accumulation ground tile (1m x 1m).'),
    ('tile_swamp', 'Murky Swamp Tile', 'SM_Tile_Swamp', ['SM_Tile_Swamp', 'tile_swamp'], 19.0, 50, 5.0, 'Wetland marsh and peat moss turf tile (1m x 1m).'),
    ('tile_tall_grass', 'Tall Pasture Grass Tile', 'SM_Tile_Tall_grass', ['SM_Tile_Tall_grass', 'tile_tall_grass'], 17.0, 50, 7.0, 'Dense wild pasture grass terrain tile (1m x 1m).'),
    ('tile_trampled_grass', 'Trampled Grass Tile', 'SM_Tile_Trampled_grass', ['SM_Tile_Trampled_grass', 'tile_trampled_grass'], 18.0, 50, 5.0, 'Livestock corral trampled pasture turf tile (1m x 1m).'),
    ('tile_wood_planks', 'Wood Planks Boardwalk Tile', 'SM_Tile_Wood_planks', ['SM_Tile_Wood_planks', 'SM_Tile_WoodPlanks', 'tile_wood_planks'], 14.0, 50, 16.0, 'Timber boardwalk decking planks ground tile (1m x 1m).'),
]

def main():
    print(f"Setting up {len(GROUND_ITEMS)} ground item folders in {GROUND_DIR}...")

    for item_id, name, model_base, icon_cands, weight, stack, val, desc in GROUND_ITEMS:
        item_folder = os.path.join(GROUND_DIR, item_id)
        os.makedirs(item_folder, exist_ok=True)
        
        # 1. Copy icon as <item_id>.png
        src_icon = find_icon(icon_cands)
        target_icon = os.path.join(item_folder, f"{item_id}.png")
        if src_icon and os.path.exists(src_icon):
            shutil.copy2(src_icon, target_icon)
        else:
            print(f"Warning: icon not found for {item_id}")
            
        # 2. Copy 3D models (.obj, .mtl, .fbx)
        models_list = []
        for ext in ['.obj', '.mtl', '.fbx']:
            src_m = os.path.join(GROUND_MODELS_DIR, model_base + ext)
            if not os.path.exists(src_m):
                for f in os.listdir(GROUND_MODELS_DIR):
                    if f.lower() == (model_base + ext).lower():
                        src_m = os.path.join(GROUND_MODELS_DIR, f)
                        break
            if os.path.exists(src_m):
                target_m = os.path.join(item_folder, os.path.basename(src_m))
                shutil.copy2(src_m, target_m)
                models_list.append(target_m)
                
        # Parse OBJ dimensions
        obj_file = next((m for m in models_list if m.endswith('.obj')), None)
        dims = parse_obj_dimensions(obj_file) if obj_file else None
        
        # 3. Write <item_id>.json manifest
        model_entries = []
        for m in models_list:
            bf = os.path.basename(m)
            ext = os.path.splitext(bf)[1].replace('.', '').lower()
            entry = {'file': bf, 'format': ext}
            if ext == 'obj' and dims:
                entry['dimensions_cm'] = {'x': dims['width_x_cm'], 'y': dims['depth_y_cm'], 'z': dims['height_z_cm']}
                entry['dimensions_m'] = {'x': dims['width_x_m'], 'y': dims['depth_y_m'], 'z': dims['height_z_m']}
                entry['vertices'] = dims['vertices']
                entry['faces'] = dims['faces']
                entry['bounding_box'] = {
                    'min': [dims['bounds'][0], dims['bounds'][2], dims['bounds'][4]],
                    'max': [dims['bounds'][1], dims['bounds'][3], dims['bounds'][5]]
                }
            model_entries.append(entry)
            
        is_water_tile = 'water' in item_id or 'pond' in item_id
        is_farm_tile = 'farmland' in item_id
        water_metric = 'Produces +10 L/min natural surface water' if is_water_tile else ('Requires 2.0 L/day moisture for crop cultivation' if is_farm_tile else 'None (unplumbed / passive)')
        footprint_str = "1x1" if item_id.startswith("tile_") else "Scatter"
        
        manifest = {
            '$schema': 'https://homesteader.game/schemas/item_v1.json',
            'id': item_id,
            'name': name,
            'category': 'ground',
            'description': desc,
            'icon': f'{item_id}.png',
            'properties': {
                'weight_kg': weight,
                'max_stack_size': stack,
                'base_value': val,
                'is_consumable': False,
                'footprint': footprint_str
            },
            'models': model_entries,
            'utilities': {
                'water': {'metric': water_metric.split(':')[0], 'details': water_metric},
                'electricity': {'metric': 'None (passive / unpowered)', 'details': 'None (passive / unpowered)'},
                'sewage': {'metric': 'None (no waste discharge)', 'details': 'None (no waste discharge)'},
                'battery': {'metric': 'None (no internal battery)', 'details': 'None (no internal battery)'},
                'internet': {'metric': 'None (offline / non-networked)', 'details': 'None (offline / non-networked)'}
            },
            'growth': {
                'is_growable': False,
                'growth_type': None,
                'species': None,
                'max_age': None,
                'time_unit': None,
                'total_stages': 0,
                'current_stage': None,
                'stages': []
            },
            'plugin_metadata': {
                'version': '1.0.0',
                'author': 'Homesteader Core',
                'compatible_api': 'v1'
            }
        }
        
        with open(os.path.join(item_folder, f'{item_id}.json'), 'w', encoding='utf-8') as jf:
            json.dump(manifest, jf, indent=2)
            
        # 4. Write README.md preview
        readme = [
            f"# {name} (`{item_id}`)\n",
            f"![{name} Icon]({item_id}.png)\n",
            "## Overview",
            "- **Category**: `ground`",
            f"- **Item Identifier**: `{item_id}`",
            f"- **Footprint**: `{'1x1 (100cm x 100cm grid cell)' if item_id.startswith('tile_') else 'Scatter decoration prop'}`",
            f"- **Max Stack Size**: {stack}",
            f"- **Weight**: {weight} kg",
            f"- **Base Economic Value**: ${val}",
            "- **Consumable**: False\n",
            "## Description",
            f"{desc}\n",
            "## 3D Model & Mesh Specifications",
        ]
        if dims:
            readme.append(f"- **Physical Dimensions (X × Y × Z)**: `{dims['width_x_cm']} cm × {dims['depth_y_cm']} cm × {dims['height_z_cm']} cm` (`{dims['width_x_m']}m × {dims['depth_y_m']}m × {dims['height_z_m']}m`)")
            readme.append(f"- **Mesh Complexity**: {dims['vertices']} vertices, {dims['faces']} polygon faces")
            readme.append(f"- **Bounding Box**: $X_{{min}}={dims['bounds'][0]}$, $X_{{max}}={dims['bounds'][1]}$, $Y_{{min}}={dims['bounds'][2]}$, $Y_{{max}}={dims['bounds'][3]}$, $Z_{{min}}={dims['bounds'][4]}$, $Z_{{max}}={dims['bounds'][5]}$")
        readme.append("- **Shading Aesthetic**: 3D Low-Poly Faceted, Metric Scale (cm), Ground-Aligned Pivot ($Z_{min} = 0$).")
        readme.append("- **Texture / Materials**: PBR Material Instance / `T_Homesteader_Palette`.\n")
        readme.append("## Utilities & Resource Profile")
        readme.append(f"- **💧 Water**: {water_metric}")
        readme.append("- **⚡ Electricity**: None (passive / unpowered)")
        readme.append("- **🚽 Sewage / Waste**: None (no waste discharge)")
        readme.append("- **🔋 Battery Power**: None (no internal battery)")
        readme.append("- **🌐 Internet / Data**: None (offline / non-networked)\n")
        readme.append("## Asset Files & Links")
        readme.append(f"- **Plugin Manifest (JSON)**: [{item_id}.json]({item_id}.json)")
        readme.append(f"- **Icon (PNG)**: [{item_id}.png]({item_id}.png)")
        for m in models_list:
            bf = os.path.basename(m)
            ext = os.path.splitext(bf)[1].upper().replace('.', '')
            readme.append(f"- **3D Mesh ({ext})**: [{bf}]({bf})")
        readme.append("")
        
        with open(os.path.join(item_folder, 'README.md'), 'w', encoding='utf-8') as rf:
            rf.write("\n".join(readme))

    print(f"\nAll {len(GROUND_ITEMS)} ground items created successfully in {GROUND_DIR}!")

    # Remove loose ground/icons directory
    loose_icons = os.path.join(GROUND_DIR, "icons")
    if os.path.exists(loose_icons):
        shutil.rmtree(loose_icons)
        print("Removed loose assets/ground/icons/ directory (all icons now inside item folders).")

    # Purge leftover clutter/tile folders from other categories
    for cat in ['building', 'farming', 'water']:
        cat_dir = os.path.join(ASSETS_DIR, cat)
        if not os.path.exists(cat_dir):
            continue
        for item in list(os.listdir(cat_dir)):
            if item.lower().startswith(('clutter_', 'tile_', 'sm_clutter_', 'sm_tile_')):
                p = os.path.join(cat_dir, item)
                shutil.rmtree(p)
                print(f"Cleaned up miscategorized {cat}/{item}")

if __name__ == '__main__':
    main()

