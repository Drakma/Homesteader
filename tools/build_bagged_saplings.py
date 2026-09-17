#!/usr/bin/env python3
"""
build_bagged_saplings.py
Creates and standardizes 3D models, icons, and plugin manifests for all 7 bagged saplings:
- sapling_birch (golden reference)
- sapling_oak
- sapling_pine
- sapling_maple (fixed unclipped foliage)
- sapling_apple (new)
- sapling_willow (new)
- sapling_poplar (new)
"""

import os
import sys
import json
import shutil
from PIL import Image

# tools/ sits at the repo root, so the project root is one level up.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HUD_ROOT = PROJECT_ROOT  # legacy alias - keep old joins working
HOMESTEADER_DIR = r"C:\Users\casey\Desktop\Homesteader"
ASSETS_DIR = os.path.join(HOMESTEADER_DIR, "assets", "logging")
ARTIFACTS_DIR = r"C:\Users\casey\.gemini\antigravity\brain\6940286d-0152-4b36-9e37-9e6cff11c21a"
UE_ICONS = os.path.join(HOMESTEADER_DIR, "Homesteader", "Content", "Homesteader", "UI", "Icons", "Foliage")
UE_MESHES = os.path.join(HOMESTEADER_DIR, "Homesteader", "Content", "Homesteader", "Assets", "Foliage", "Meshes")

sys.path.append(os.path.join(HUD_ROOT, "tools"))
from generate_planted_saplings_and_stumps import Vec3, Mesh

# -----------------------------------------------------------------------------
# 3D Mesh Builder for Bagged Sapling (with burlap root ball)
# -----------------------------------------------------------------------------

def build_bagged_sapling_mesh(species_name, bark_color, foliage_colors, foliage_style="broadleaf"):
    m = Mesh(f"SM_Sapling_{species_name.capitalize()}")
    m.add_material("Burlap_Sack", 0.62, 0.50, 0.35)
    m.add_material("Burlap_Dark", 0.48, 0.38, 0.25)
    m.add_material("Rope_Twine", 0.74, 0.64, 0.46)
    m.add_material("Soil_Core", 0.22, 0.16, 0.12)
    m.add_material("Bark", *bark_color)
    for i, fc in enumerate(foliage_colors):
        m.add_material(f"Foliage_{i}", *fc)

    # 1. Burlap Root Ball Sack
    segs = 10
    m.add_cylinder(r0=10, r1=16, h=5, z0=0, segs=segs, mat="Burlap_Dark")
    m.add_cylinder(r0=16, r1=18, h=5, z0=5, segs=segs, mat="Burlap_Sack")
    m.add_cylinder(r0=18, r1=14, h=5, z0=10, segs=segs, mat="Burlap_Sack")
    m.add_cylinder(r0=14, r1=6.5, h=4, z0=15, segs=segs, mat="Burlap_Sack")
    m.add_cylinder(r0=7.5, r1=7.5, h=2.5, z0=18, segs=segs, mat="Rope_Twine")
    m.add_cylinder(r0=6.5, r1=11, h=6, z0=19, segs=segs, mat="Burlap_Sack")

    inner_c = Vec3(0, 0, 19)
    import math
    for i in range(segs):
        a0 = i * 2.0 * math.pi / segs
        a1 = (i + 1) * 2.0 * math.pi / segs
        p0 = Vec3(6.5 * math.cos(a0), 6.5 * math.sin(a0), 19)
        p1 = Vec3(6.5 * math.cos(a1), 6.5 * math.sin(a1), 19)
        m.add_triangle(inner_c, p1, p0, mat="Soil_Core")

    # 2. Stem
    m.add_cylinder(r0=4.0, r1=3.0, h=40, z0=19, segs=7, mat="Bark")
    m.add_cylinder(r0=3.0, r1=2.0, h=40, z0=59, segs=7, mat="Bark", c0=(0,0), c1=(1.5, 1.0))
    m.add_cylinder(r0=2.0, r1=1.2, h=35, z0=99, segs=6, mat="Bark", c0=(1.5,1.0), c1=(3.0, 2.0))

    m.add_cylinder(r0=1.4, r1=0.8, h=25, z0=70, segs=5, mat="Bark", c0=(1,0.5), c1=(-18, -12))
    m.add_cylinder(r0=1.4, r1=0.8, h=25, z0=88, segs=5, mat="Bark", c0=(2,1.5), c1=(16, 14))

    # 3. Foliage
    if foliage_style == "conifer":
        m.add_cone(r=26, h=34, z0=55, segs=7, mat="Foliage_1", c=(0,0))
        m.add_cone(r=20, h=30, z0=82, segs=7, mat="Foliage_0", c=(1,1))
        m.add_cone(r=14, h=28, z0=106, segs=6, mat="Foliage_0", c=(2,2))
    elif foliage_style == "columnar":
        m.add_icosphere_lobe(radius=15, center=(-2, -2, 75), subdivisions=1, mat="Foliage_1", flatten_z=1.4)
        m.add_icosphere_lobe(radius=16, center=(2, 2, 100), subdivisions=1, mat="Foliage_0", flatten_z=1.4)
        m.add_icosphere_lobe(radius=14, center=(1, 1, 125), subdivisions=1, mat="Foliage_0", flatten_z=1.3)
    elif foliage_style == "weeping":
        m.add_icosphere_lobe(radius=20, center=(-12, -10, 80), subdivisions=1, mat="Foliage_1", flatten_z=1.1)
        m.add_icosphere_lobe(radius=22, center=(12, 10, 92), subdivisions=1, mat="Foliage_0", flatten_z=1.1)
        m.add_icosphere_lobe(radius=18, center=(0, 0, 112), subdivisions=1, mat="Foliage_0", flatten_z=0.9)
    else:
        m.add_icosphere_lobe(radius=20, center=(-18, -12, 90), subdivisions=1, mat="Foliage_1", flatten_z=0.9)
        m.add_icosphere_lobe(radius=20, center=(16, 14, 102), subdivisions=1, mat="Foliage_0", flatten_z=0.9)
        m.add_icosphere_lobe(radius=22, center=(3, 2, 122), subdivisions=1, mat="Foliage_0", flatten_z=0.9)
        if len(foliage_colors) > 2:
            m.add_icosphere_lobe(radius=14, center=(0, 0, 138), subdivisions=1, mat="Foliage_2", flatten_z=0.85)

    m.ground_align()
    return m

# -----------------------------------------------------------------------------
# Bagged Sapling Species Specifications
# -----------------------------------------------------------------------------

SPECIES_CONFIG = [
    ("sapling_birch", "Birch Sapling", "birch", (0.92, 0.92, 0.88), [(0.58, 0.84, 0.34), (0.50, 0.76, 0.28)], "broadleaf", None),
    ("sapling_oak", "Oak Sapling", "oak", (0.42, 0.28, 0.16), [(0.42, 0.72, 0.22), (0.24, 0.54, 0.18)], "broadleaf", None),
    ("sapling_pine", "Pine Sapling", "pine", (0.36, 0.22, 0.14), [(0.36, 0.64, 0.28), (0.24, 0.50, 0.22)], "conifer", None),
    ("sapling_maple", "Maple Sapling", "maple", (0.44, 0.30, 0.20), [(0.82, 0.22, 0.15), (0.88, 0.44, 0.14)], "broadleaf", "test_sapling_maple.png"),
    ("sapling_apple", "Apple Sapling", "apple", (0.38, 0.25, 0.16), [(0.40, 0.70, 0.22), (0.32, 0.58, 0.18)], "broadleaf", "test_sapling_apple.png"),
    ("sapling_willow", "Willow Sapling", "willow", (0.40, 0.34, 0.24), [(0.46, 0.70, 0.32), (0.36, 0.56, 0.26)], "weeping", "test_sapling_willow.png"),
    ("sapling_poplar", "Poplar Sapling", "poplar", (0.48, 0.44, 0.32), [(0.44, 0.72, 0.26), (0.36, 0.60, 0.20)], "columnar", "test_sapling_poplar.png"),
]

def main():
    print("=== BUILDING BAGGED SAPLINGS FOR ALL 7 TREE SPECIES ===")
    
    for item_id, display_name, species, bark_c, fol_c, style, new_icon_source in SPECIES_CONFIG:
        print(f"\nProcessing {item_id} ({display_name})...")
        item_dir = os.path.join(ASSETS_DIR, item_id)
        os.makedirs(item_dir, exist_ok=True)
        
        # 1. Generate 3D Wavefront Mesh
        mesh = build_bagged_sapling_mesh(species, bark_c, fol_c, style)
        obj_name = f"SM_{item_id.title().replace('_', '')}.obj"
        mtl_name = f"SM_{item_id.title().replace('_', '')}.mtl"
        obj_path = os.path.join(item_dir, obj_name)
        mtl_path = os.path.join(item_dir, mtl_name)
        mesh.save_obj_and_mtl(obj_path, mtl_path)
        bounds = mesh.compute_bounds()
        print(f"  Generated 3D mesh: {obj_name} ({bounds['vertices']} verts, {bounds['width_x_cm']}x{bounds['depth_y_cm']}x{bounds['height_z_cm']} cm)")
        
        # 2. Icon placement
        target_icon = os.path.join(item_dir, f"{item_id}.png")
        if new_icon_source:
            src_icon = os.path.join(ARTIFACTS_DIR, new_icon_source)
            if os.path.exists(src_icon):
                shutil.copy2(src_icon, target_icon)
                print(f"  Deployed new unclipped icon from: {new_icon_source}")
        else:
            if not os.path.exists(target_icon):
                print(f"  Warning: target icon not found at {target_icon}")
                
        # 3. JSON Plugin Manifest
        max_age_val = 100 if species not in ["apple", "poplar", "willow"] else (80 if species != "willow" else 90)
        manifest = {
            "$schema": "https://homesteader.game/schemas/item_v1.json",
            "id": item_id,
            "name": display_name,
            "category": "logging",
            "description": f"A young {species.capitalize()} sapling nursery start with its root ball safely bundled in a tied burlap sack and ready for planting.",
            "icon": f"{item_id}.png",
            "properties": {
                "weight_kg": 3.5,
                "max_stack_size": 10,
                "base_value": 15.0,
                "is_consumable": True,
                "footprint": "1x1"
            },
            "models": [
                {
                    "file": mtl_name,
                    "format": "mtl"
                },
                {
                    "file": obj_name,
                    "format": "obj",
                    "dimensions_cm": {
                        "x": bounds["width_x_cm"],
                        "y": bounds["depth_y_cm"],
                        "z": bounds["height_z_cm"]
                    },
                    "dimensions_m": {
                        "x": bounds["width_x_m"],
                        "y": bounds["depth_y_m"],
                        "z": bounds["height_z_m"]
                    },
                    "vertices": bounds["vertices"],
                    "faces": bounds["faces"],
                    "bounding_box": {
                        "min": [bounds["bounds"][0], bounds["bounds"][2], bounds["bounds"][4]],
                        "max": [bounds["bounds"][1], bounds["bounds"][3], bounds["bounds"][5]]
                    }
                }
            ],
            "utilities": {
                "water": { "metric": "Requires 1.5 L/day moisture until planted into ground", "details": "Requires 1.5 L/day moisture" },
                "electricity": { "metric": "None (passive / unpowered)", "details": "None (passive / unpowered)" },
                "sewage": { "metric": "None (no waste discharge)", "details": "None (no waste discharge)" },
                "battery": { "metric": "None (no internal battery)", "details": "None (no internal battery)" },
                "internet": { "metric": "None (offline / non-networked)", "details": "None (offline / non-networked)" }
            },
            "growth": {
                "is_growable": True,
                "growth_type": "tree",
                "species": species,
                "max_age": max_age_val,
                "time_unit": "days",
                "total_stages": 4,
                "current_stage": {
                    "stage": 1,
                    "name": "sapling",
                    "age_min": 0,
                    "age_max": 15
                },
                "stages": [
                    { "stage": 1, "name": "sapling", "item_id": item_id, "planted_item_id": f"planted_sapling_{species}", "age_min": 0, "age_max": 15 },
                    { "stage": 2, "name": "small", "item_id": f"tree_{species}_small", "age_min": 15, "age_max": 40 },
                    { "stage": 3, "name": "medium", "item_id": f"tree_{species}_medium", "age_min": 40, "age_max": 75 },
                    { "stage": 4, "name": "large (mature)", "item_id": f"tree_{species}_large" if species != "pine" and species != "birch" else f"tree_{species}_tall", "age_min": 75, "age_max": 100 }
                ]
            },
            "plugin_metadata": {
                "version": "1.0.0",
                "author": "Homesteader Core",
                "compatible_api": "v1"
            }
        }
        with open(os.path.join(item_dir, f"{item_id}.json"), "w", encoding="utf-8") as jf:
            json.dump(manifest, jf, indent=2)
            
        # 4. Human-readable README.md
        readme = [
            f"# {display_name} (`{item_id}`)\n",
            f"![{display_name} Icon]({item_id}.png)\n",
            "## Overview",
            "- **Category**: `logging`",
            f"- **Item Identifier**: `{item_id}`",
            "- **Max Stack Size**: 10",
            "- **Weight**: 3.5 kg",
            "- **Base Economic Value**: $15.0",
            "- **Consumable**: True (consumed upon planting)\n",
            "## Description",
            f"A healthy young {species.capitalize()} sapling nursery start with its root ball safely bundled in burlap and tied with cord. Can be planted into homestead terrain to establish a live timber tree.\n",
            "## Growth & Planting Progression (Stage 1 of 4)",
            f"- **Nursery Item**: `{item_id}` (Bagged root ball)",
            f"- **Planted Form**: [`planted_sapling_{species}`](../planted_sapling_{species}/planted_sapling_{species}.json) (In-ground bare stem)",
            f"- **Stage 2**: `15 – 40 days` (`tree_{species}_small`)",
            f"- **Stage 3**: `40 – 75 days` (`tree_{species}_medium`)",
            f"- **Stage 4**: `75 – 100 days` (`tree_{species}_large` / mature)\n",
            "## 3D Model & Mesh Specifications",
            f"- **Physical Dimensions (X × Y × Z)**: `{bounds['width_x_cm']} cm × {bounds['depth_y_cm']} cm × {bounds['height_z_cm']} cm` (`{bounds['width_x_m']}m × {bounds['depth_y_m']}m × {bounds['height_z_m']}m`)",
            f"- **Mesh Complexity**: {bounds['vertices']} vertices, {bounds['faces']} polygon faces",
            "- **Root Ball Geometry**: 10-segment bulging burlap sack with tied cord and gathered ruffled collar.",
            "- **Shading Aesthetic**: 3D Low-Poly Faceted, Metric Scale (cm), Ground-Aligned Pivot ($Z_{min} = 0$).\n",
            "## Asset Files & Links",
            f"- **Plugin Manifest (JSON)**: [{item_id}.json]({item_id}.json)",
            f"- **Icon (PNG)**: [{item_id}.png]({item_id}.png)",
            f"- **3D Mesh (OBJ)**: [{obj_name}]({obj_name})",
            f"- **Material (MTL)**: [{mtl_name}]({mtl_name})\n"
        ]
        with open(os.path.join(item_dir, "README.md"), "w", encoding="utf-8") as rf:
            rf.write("\n".join(readme))
            
        # Sync to UE Content
        if os.path.exists(target_icon):
            shutil.copy2(target_icon, os.path.join(UE_ICONS, f"{item_id}.png"))
        shutil.copy2(obj_path, os.path.join(UE_MESHES, obj_name))
        shutil.copy2(mtl_path, os.path.join(UE_MESHES, mtl_name))

    print("\n>>> ALL 7 BAGGED SAPLINGS BUILT AND DEPLOYED SUCCESSFULLY <<<")

if __name__ == "__main__":
    main()

