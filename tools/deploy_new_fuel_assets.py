#!/usr/bin/env python3
"""
Deploy new fuel types and container assets into assets/fuel/
"""

import os
import json
import math
from PIL import Image, ImageDraw

ASSETS_DIR = r"C:\Users\casey\Desktop\Homesteader\assets"
FUEL_DIR = os.path.join(ASSETS_DIR, "fuel")

NEW_FUELS = [
    {
        "id": "fuel_kerosene_can_5gal",
        "name": "5-Gallon Kerosene Can",
        "desc": "Heavy-duty blue HDPE container designed for safe kerosene fuel transport and storage.",
        "weight": 17.5,
        "value": 45.0,
        "footprint": "0.35m x 0.25m x 0.45m",
        "fuel_type": "kerosene",
        "capacity_liters": 18.9,
        "color": (2, 132, 199), # Blue
        "shape": "can"
    },
    {
        "id": "fuel_charcoal_bag_20lb",
        "name": "Hardwood Lump Charcoal 20lb",
        "desc": "Dense all-natural kiln-fired hardwood lump charcoal for clean, high-heat homestead cooking and forge fuel.",
        "weight": 9.1,
        "value": 18.5,
        "footprint": "0.4m x 0.2m x 0.6m",
        "fuel_type": "charcoal",
        "capacity_liters": 25.0,
        "color": (30, 41, 59), # Slate dark
        "shape": "bag"
    },
    {
        "id": "fuel_wood_pellets_bag_40lb",
        "name": "Heating Wood Pellets 40lb",
        "desc": "Compressed 100% hardwood sawdust pellets for automated biomass stoves and boiler systems.",
        "weight": 18.2,
        "value": 12.0,
        "footprint": "0.45m x 0.3m x 0.65m",
        "fuel_type": "wood_pellets",
        "capacity_liters": 30.0,
        "color": (161, 98, 7), # Wood brown
        "shape": "bag"
    },
    {
        "id": "fuel_biodiesel_jug_5gal",
        "name": "Bio-Diesel Fuel Jug 5gal",
        "desc": "Filtered bio-diesel fuel processed from recycled farm vegetable oils for diesel generators and farm tractors.",
        "weight": 16.8,
        "value": 38.0,
        "footprint": "0.3m x 0.3m x 0.45m",
        "fuel_type": "biodiesel",
        "capacity_liters": 18.9,
        "color": (101, 163, 13), # Olive amber
        "shape": "jug"
    },
    {
        "id": "fuel_can_gasoline_5gal",
        "name": "Gasoline Jerry Can 5gal",
        "desc": "Safety-vented red poly jerry can for gasoline storage and equipment refueling.",
        "weight": 16.2,
        "value": 35.0,
        "footprint": "0.38m x 0.22m x 0.46m",
        "fuel_type": "gasoline",
        "capacity_liters": 18.9,
        "color": (225, 29, 72), # Red
        "shape": "can"
    },
    {
        "id": "fuel_can_jerry_steel_20l",
        "name": "Military Steel Jerry Can 20L",
        "desc": "Heavy-gauge stamped steel NATO-spec fuel can with cam-locking cap and breather pipe.",
        "weight": 20.5,
        "value": 65.0,
        "footprint": "0.35m x 0.17m x 0.47m",
        "fuel_type": "universal_liquid",
        "capacity_liters": 20.0,
        "color": (74, 85, 53), # Olive drab
        "shape": "steel_can"
    },
    {
        "id": "fuel_tank_propane_100lb",
        "name": "100lb Propane Tank Cylinder",
        "desc": "Tall steel DOT-compliant 100-pound LP cylinder for cabin heating, water heaters, and continuous power generation.",
        "weight": 77.0,
        "value": 185.0,
        "footprint": "0.38m x 0.38m x 1.25m",
        "fuel_type": "propane",
        "capacity_liters": 89.0,
        "color": (203, 213, 225), # Light gray steel
        "shape": "tall_cylinder"
    },
    {
        "id": "fuel_drum_steel_55gal",
        "name": "55-Gallon Steel Fuel Drum",
        "desc": "Reinforced tight-head steel drum with 2-inch bung openings for bulk hydrocarbon fuel reserves.",
        "weight": 210.0,
        "value": 140.0,
        "footprint": "0.6m x 0.6m x 0.9m",
        "fuel_type": "bulk_fuel",
        "capacity_liters": 208.2,
        "color": (30, 58, 138), # Industrial navy
        "shape": "drum"
    },
    {
        "id": "fuel_caddy_wheeled_30gal",
        "name": "30-Gallon Wheeled Fuel Caddy",
        "desc": "Mobile poly fuel caddy equipped with pneumatic rubber wheels, grounding wire, and manual rotary transfer pump.",
        "weight": 115.0,
        "value": 295.0,
        "footprint": "0.65m x 0.55m x 1.1m",
        "fuel_type": "mobile_fuel",
        "capacity_liters": 113.5,
        "color": (194, 65, 12), # Safety orange
        "shape": "caddy"
    },
    {
        "id": "fuel_nozzle_transfer_kit",
        "name": "Fuel Transfer Nozzle & Hose Kit",
        "desc": "Heavy-duty 1-inch aluminum automatic shut-off dispensing nozzle with 14-foot anti-static fuel hose.",
        "weight": 5.2,
        "value": 85.0,
        "footprint": "0.5m x 0.3m x 0.15m",
        "fuel_type": "equipment",
        "capacity_liters": 0.0,
        "color": (71, 85, 105), # Metallic gunmetal
        "shape": "nozzle"
    }
]

def make_obj_cylinder(r, h, segs=12):
    verts = []
    faces = []
    # Bottom circle
    for i in range(segs):
        ang = 2 * math.pi * i / segs
        verts.append((r * math.cos(ang), r * math.sin(ang), 0.0))
    # Top circle
    for i in range(segs):
        ang = 2 * math.pi * i / segs
        verts.append((r * math.cos(ang), r * math.sin(ang), h))
        
    # Side quads
    for i in range(segs):
        i_next = (i + 1) % segs
        v1 = i + 1
        v2 = i_next + 1
        v3 = segs + i_next + 1
        v4 = segs + i + 1
        faces.append((v1, v2, v3, v4))
    return verts, faces

def make_obj_box(w, d, h):
    # Centered X, Y, Z from 0 to h
    hw = w / 2.0
    hd = d / 2.0
    verts = [
        (-hw, -hd, 0), (hw, -hd, 0), (hw, hd, 0), (-hw, hd, 0),
        (-hw, -hd, h), (hw, -hd, h), (hw, hd, h), (-hw, hd, h),
    ]
    faces = [
        (1, 2, 3, 4), # bottom
        (5, 8, 7, 6), # top
        (1, 5, 6, 2), # front
        (2, 6, 7, 3), # right
        (3, 7, 8, 4), # back
        (4, 8, 5, 1), # left
    ]
    return verts, faces

def write_obj_file(fpath, item_id, verts, faces):
    mtl_name = f"{item_id}.mtl"
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(f"# Homesteader Fuel Asset: {item_id}\n")
        f.write(f"mtllib {mtl_name}\n")
        f.write(f"o {item_id}\n")
        for x, y, z in verts:
            # Scale to Unreal Units (cm)
            f.write(f"v {x*100.0:.3f} {y*100.0:.3f} {z*100.0:.3f}\n")
        f.write(f"usemtl M_Palette\n")
        f.write(f"s 1\n")
        for face in faces:
            if len(face) == 3:
                f.write(f"f {face[0]} {face[1]} {face[2]}\n")
            elif len(face) == 4:
                f.write(f"f {face[0]} {face[1]} {face[2]} {face[3]}\n")

def write_mtl_file(fpath):
    with open(fpath, "w", encoding="utf-8") as f:
        f.write("# Homesteader Palette Material\n")
        f.write("newmtl M_Palette\n")
        f.write("Ka 1.000000 1.000000 1.000000\n")
        f.write("Kd 0.800000 0.800000 0.800000\n")
        f.write("Ks 0.100000 0.100000 0.100000\n")
        f.write("Ns 20.000000\n")
        f.write("map_Kd ../../textures/palettes/T_Homesteader_Palette.png\n")

def render_fuel_icon(fpath, item_info):
    # 128x128 transparent RGBA low-poly faceted render icon
    img = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    col = item_info["color"]
    r, g, b = col
    # Shadow shade
    dark = (max(0, r - 50), max(0, g - 50), max(0, b - 50), 255)
    # Highlight shade
    light = (min(255, r + 45), min(255, g + 45), min(255, b + 45), 255)
    base = (r, g, b, 255)
    
    shape = item_info["shape"]
    
    if shape in ["can", "steel_can"]:
        # Isometric Jerry Can
        # Left shaded face
        draw.polygon([(36, 42), (64, 56), (64, 102), (36, 88)], fill=dark)
        # Right highlighted face
        draw.polygon([(64, 56), (92, 42), (92, 88), (64, 102)], fill=base)
        # Top face
        draw.polygon([(36, 42), (64, 28), (92, 42), (64, 56)], fill=light)
        # Handle
        draw.line([(50, 26), (64, 20), (78, 26)], fill=light, width=4)
        # Spout
        draw.polygon([(40, 28), (48, 24), (48, 32), (40, 36)], fill=(220, 220, 225, 255))
        
    elif shape in ["bag"]:
        # Feed/Charcoal/Pellet bag
        draw.polygon([(40, 36), (64, 46), (64, 104), (40, 94)], fill=dark)
        draw.polygon([(64, 46), (88, 36), (88, 94), (64, 104)], fill=base)
        draw.polygon([(40, 36), (64, 26), (88, 36), (64, 46)], fill=light)
        # Label stripe
        draw.polygon([(40, 60), (64, 70), (88, 60), (88, 72), (64, 82), (40, 72)], fill=(245, 245, 250, 240))
        
    elif shape in ["jug"]:
        draw.polygon([(38, 46), (64, 58), (64, 102), (38, 90)], fill=dark)
        draw.polygon([(64, 58), (90, 46), (90, 90), (64, 102)], fill=base)
        draw.polygon([(38, 46), (64, 34), (90, 46), (64, 58)], fill=light)
        # Neck & cap
        draw.rectangle([(58, 22), (70, 34)], fill=(240, 240, 240, 255))
        
    elif shape in ["drum", "tall_cylinder"]:
        # Cylinder
        h_top = 30 if shape == "drum" else 20
        h_bot = 100
        w = 34 if shape == "drum" else 24
        # Left side
        draw.polygon([(64 - w, h_top + 10), (64, h_top + 20), (64, h_bot), (64 - w, h_bot - 10)], fill=dark)
        # Right side
        draw.polygon([(64, h_top + 20), (64 + w, h_top + 10), (64 + w, h_bot - 10), (64, h_bot)], fill=base)
        # Top oval
        draw.ellipse([(64 - w, h_top), (64 + w, h_top + 20)], fill=light)
        # Rib lines
        draw.arc([(64 - w, h_top + 25), (64 + w, h_top + 45)], 0, 180, fill=(20, 20, 30, 180), width=2)
        draw.arc([(64 - w, h_top + 50), (64 + w, h_top + 70)], 0, 180, fill=(20, 20, 30, 180), width=2)
        
    elif shape in ["caddy"]:
        # Wheeled caddy box
        draw.polygon([(38, 38), (64, 50), (64, 96), (38, 84)], fill=dark)
        draw.polygon([(64, 50), (90, 38), (90, 84), (64, 96)], fill=base)
        draw.polygon([(38, 38), (64, 26), (90, 38), (64, 50)], fill=light)
        # Wheels
        draw.ellipse([(32, 80), (44, 102)], fill=(15, 23, 42, 255))
        draw.ellipse([(84, 80), (96, 102)], fill=(15, 23, 42, 255))
        # Handle
        draw.line([(64, 26), (64, 14), (74, 14)], fill=(200, 200, 210, 255), width=3)
        
    elif shape in ["nozzle"]:
        # Gunmetal fuel nozzle
        draw.polygon([(30, 48), (60, 38), (80, 50), (84, 62), (64, 68), (44, 58)], fill=light)
        draw.line([(80, 50), (102, 38)], fill=(220, 225, 230, 255), width=5) # Spout
        draw.line([(40, 58), (48, 88), (60, 92)], fill=(30, 41, 59, 255), width=6) # Hose
        draw.polygon([(52, 60), (68, 64), (64, 76), (48, 72)], fill=(225, 29, 72, 255)) # Trigger
        
    # Enforce outer border transparent safe margin
    # Ensure x=0..11 and x=116..127, y=0..11 and y=116..127 are alpha=0
    px = img.load()
    for y in range(128):
        for x in range(128):
            if x < 12 or x > 115 or y < 12 or y > 115:
                px[x, y] = (0, 0, 0, 0)
                
    img.save(fpath, "PNG")

for item in NEW_FUELS:
    item_id = item["id"]
    item_dir = os.path.join(FUEL_DIR, item_id)
    os.makedirs(item_dir, exist_ok=True)
    
    # 1. 3D Model
    obj_path = os.path.join(item_dir, f"{item_id}.obj")
    mtl_path = os.path.join(item_dir, f"{item_id}.mtl")
    
    if item["shape"] in ["can", "steel_can", "caddy"]:
        verts, faces = make_obj_box(0.35, 0.22, 0.46)
    elif item["shape"] in ["bag"]:
        verts, faces = make_obj_box(0.40, 0.25, 0.60)
    elif item["shape"] in ["jug"]:
        verts, faces = make_obj_box(0.30, 0.30, 0.42)
    elif item["shape"] in ["drum"]:
        verts, faces = make_obj_cylinder(0.30, 0.90, segs=16)
    elif item["shape"] in ["tall_cylinder"]:
        verts, faces = make_obj_cylinder(0.19, 1.25, segs=16)
    elif item["shape"] in ["nozzle"]:
        verts, faces = make_obj_box(0.45, 0.15, 0.25)
    else:
        verts, faces = make_obj_box(0.3, 0.3, 0.5)
        
    write_obj_file(obj_path, item_id, verts, faces)
    write_mtl_file(mtl_path)
    
    # 2. Icon
    icon_path = os.path.join(item_dir, f"{item_id}.png")
    render_fuel_icon(icon_path, item)
    
    # 3. Manifest JSON
    manifest = {
        "id": item_id,
        "name": item["name"],
        "category": "fuel",
        "description": item["desc"],
        "icon": f"{item_id}.png",
        "properties": {
            "weight_kg": item["weight"],
            "max_stack_size": 1 if item["weight"] > 10 else 4,
            "base_value": item["value"],
            "is_consumable": True if "can" in item_id or "bag" in item_id or "jug" in item_id else False,
            "footprint": item["footprint"],
            "fuel_type": item["fuel_type"],
            "capacity_liters": item["capacity_liters"]
        },
        "models": [
            {
                "file": f"{item_id}.obj",
                "format": "obj",
                "is_primary": True,
                "lod": 0
            }
        ],
        "utilities": {
            "fuel_type": item["fuel_type"],
            "capacity_liters": item["capacity_liters"]
        },
        "growth": {
            "is_growable": False,
            "max_age": None,
            "stages": []
        },
        "plugin_metadata": {
            "version": "1.0.0",
            "author": "Homesteader Development Team",
            "api_version": "1.0"
        }
    }
    
    with open(os.path.join(item_dir, f"{item_id}.json"), "w", encoding="utf-8") as jf:
        json.dump(manifest, jf, indent=2)
        
    # 4. README
    with open(os.path.join(item_dir, "README.md"), "w", encoding="utf-8") as rf:
        rf.write(f"# {item['name']} (`{item_id}`)\n\n")
        rf.write(f"![{item['name']}](./{item_id}.png)\n\n")
        rf.write(f"**Category**: Fuel & Containers (`fuel`)\n\n")
        rf.write(f"{item['desc']}\n\n")
        rf.write(f"- **Fuel Type**: `{item['fuel_type']}`\n")
        rf.write(f"- **Capacity**: `{item['capacity_liters']} L`\n")
        rf.write(f"- **Weight**: `{item['weight']} kg`\n")
        rf.write(f"- **Base Value**: `${item['value']:.2f}`\n")
        rf.write(f"- **Model**: `{item_id}.obj`\n")

print(f"Successfully generated {len(NEW_FUELS)} new fuel assets.")

