#!/usr/bin/env python3
"""
build_kit.py
Generates an interactive, responsive HTML5 Asset Kit for all items across
the 17 Homesteader categories in the assets/ directory.
Features:
- Category filtering (17 canonical systems) + Live Search + Quick Filters
- Grid display of items with 128x128 icons, 3D badges, growth badges
- Native <dialog> Modal on card click:
  - Interactive 3D WebGL Model Viewer (<model-viewer> for GLB, Three.js for OBJ)
  - Human-readable structured layout of <item_id>.json (properties, dimensions, utilities, growth)
  - Raw syntax-highlighted JSON viewer with Copy button
"""

import argparse
import hashlib
import os
import json
import re
import sys
# Empty byte string, spelled without a literal so no later edit to this file
# can collapse one of its quote pairs into an unterminated string.
EMPTY_BYTES = bytes()

ASSETS_DIR = r"C:\Users\casey\Desktop\Homesteader\assets"
CATEGORIES = [
    "structures", "building", "farming", "ranching", "logging",
    "fishing", "tools", "electricity", "water", "waste",
    "internet", "hud", "ground", "food", "fuel", "materials", "ingredients"
]

CATEGORY_METADATA = {
    "structures": {"name": "Structures", "icon": "🏛️", "desc": "Placed world buildings, farmhouses, cabins, barns, silos, sheds, greenhouses, coops, shelters, and towers."},
    "building": {"name": "Building", "icon": "🧱", "desc": "Modular building materials, framing, doors, windows, and hardware supplies."},
    "farming": {"name": "Farming", "icon": "🌾", "desc": "Crops, seeds, produce, fertilizers, irrigation, and agricultural machinery."},
    "ranching": {"name": "Ranching", "icon": "🐄", "desc": "Livestock species, animal feed/hay, butchered meats, hides/pelts, and animal husbandry housing."},
    "logging": {"name": "Logging", "icon": "🌲", "desc": "Modular forest trees (large/medium/small), saplings, timber logs, firewood, woodchips, and sap spigots."},
    "fishing": {"name": "Fishing", "icon": "🐟", "desc": "Whole fish species, precision meat fillets, fishing rods, lures, and tackle."},
    "tools": {"name": "Tools", "icon": "⛏️", "desc": "Hand tools, power gear, crafting implements, and surveying/measuring equipment."},
    "electricity": {"name": "Electricity", "icon": "⚡", "desc": "Solar photovoltaic panels, wind turbines, fuel generators, battery banks, and high-voltage wiring."},
    "water": {"name": "Water", "icon": "💧", "desc": "Aquifer wells, pressure tanks, poly cisterns, rain catchment barrels, and filtration racks."},
    "waste": {"name": "Waste & Sanitation", "icon": "♻️", "desc": "Septic infrastructure, compost systems, composting toilets, and organic waste management."},
    "internet": {"name": "Internet", "icon": "📡", "desc": "Starlink satellite dishes, Wi-Fi 6 mesh distribution routers, and weather-rated cabling."},
    "hud": {"name": "HUD", "icon": "🎛️", "desc": "Player vitals, coins, energy/stamina bars, clock dials, and interface elements."},
    "ground": {"name": "Ground", "icon": "🌱", "desc": "Modular terrain grid tiles (1m x 1m), road pavements, and scatter clutter props."},
    "food": {"name": "Food & Rations", "icon": "🍲", "desc": "Edible harvested produce, pantry staples, butchered meats, fresh eggs, dairy, and culinary ingredients."},
    "fuel": {"name": "Fuel & Containers", "icon": "⛽", "desc": "Liquid hydrocarbons, compressed gas tanks, bulk fuel storage, firewood cords, and transfer equipment."},
    "materials": {"name": "Materials", "icon": "🪵", "desc": "Raw construction materials, timber log piles, aggregate bulk piles, textiles, hides, and foundational crafting resources."},
    "ingredients": {"name": "Ingredients", "icon": "🥩", "desc": "Raw cooking and crafting inputs: butchered meats, fish fillets, eggs, dairy, harvested grains, and crop-derived ingredients."}
}

def collect_all_items():
    items = []
    for cat in CATEGORIES:
        cat_dir = os.path.join(ASSETS_DIR, cat)
        if not os.path.isdir(cat_dir):
            continue
        for item_id in sorted(os.listdir(cat_dir)):
            item_dir = os.path.join(cat_dir, item_id)
            if not os.path.isdir(item_dir):
                continue
                
            json_path = os.path.join(item_dir, f"{item_id}.json")
            manifest = {}
            if os.path.exists(json_path):
                try:
                    with open(json_path, 'r', encoding='utf-8') as jf:
                        manifest = json.load(jf)
                except Exception:
                    pass
                    
            # Scan files
            files = os.listdir(item_dir)
            models_list = []
            best_fbx = None
            best_glb = None
            best_obj = None
            for f in files:
                ext = os.path.splitext(f)[1].lower()
                if ext in ['.fbx', '.glb', '.gltf', '.obj', '.stl', '.usdz', '.mtl']:
                    rel = f"{cat}/{item_id}/{f}"
                    models_list.append({"file": f, "format": ext[1:], "path": rel})
                    if ext == '.fbx' and not best_fbx:
                        best_fbx = rel
                    elif ext == '.glb' and not best_glb:
                        best_glb = rel
                    elif ext == '.obj' and not best_obj:
                        best_obj = rel
                        
            icon_file = f"{item_id}.png"
            has_icon = os.path.exists(os.path.join(item_dir, icon_file))
            icon_path = f"{cat}/{item_id}/{icon_file}" if has_icon else None
            
            # Model dim info
            dim_info = {}
            for m in manifest.get('models', []):
                if isinstance(m, dict) and 'dimensions_cm' in m:
                    dim_info = m
                    break
                    
            best_model = best_fbx or best_glb or best_obj
            model_fmt = "fbx" if best_fbx else ("glb" if best_glb else ("obj" if best_obj else None))
            
            items.append({
                "id": item_id,
                "name": manifest.get("name", item_id.replace("_", " ").title()),
                "category": cat,
                "description": manifest.get("description", "Standard Homesteader simulation asset."),
                "icon": icon_path,
                "models": models_list,
                "best_model": best_model,
                "model_format": model_fmt,
                "has_3d": len(models_list) > 0,
                "properties": manifest.get("properties", {}),
                "dimensions": dim_info,
                "growth": manifest.get("growth", {}),
                "utilities": manifest.get("utilities", {}),
                "plugin_metadata": manifest.get("plugin_metadata", {}),
                "manifest": manifest
            })
    return items

def generate_html(items):
    items_json = json.dumps(items)
    cat_meta_json = json.dumps(CATEGORY_METADATA)
    
    total_count = len(items)
    with_3d_count = sum(1 for x in items if x["has_3d"])
    growable_count = sum(1 for x in items if x["growth"].get("is_growable"))
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Homesteader // Master Asset Kit</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap">
  
  <!-- 3D Model Viewer Google Web Component (GLB/GLTF) -->
  <script type="module" src="https://ajax.googleapis.com/ajax/libs/model-viewer/3.5.0/model-viewer.min.js"></script>
  
  <!-- Three.js + FBXLoader + OBJLoader -->
  <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/fflate@0.8.0/umd/index.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/FBXLoader.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/OBJLoader.js"></script>

  <style>
    :root {{
      --bg-canvas: #090d13;
      --bg-panel: #111823;
      --bg-card: #16202e;
      --bg-card-hover: #1c293c;
      --bg-input: #0e141c;
      --border-subtle: #233144;
      --border-accent: #334863;
      
      --accent-gold: #f59e0b;
      --accent-emerald: #10b981;
      --accent-sky: #38bdf8;
      --accent-indigo: #6366f1;
      --accent-rose: #f43f5e;
      
      --text-main: #f8fafc;
      --text-sub: #94a3b8;
      --text-muted: #64748b;
      
      --radius-sm: 6px;
      --radius-md: 10px;
      --radius-lg: 14px;
      --radius-xl: 18px;
    }}

    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}

    body {{
      background-color: var(--bg-canvas);
      color: var(--text-main);
      font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      overflow-y: scroll;
    }}

    /* Top Sticky Header */
    header.app-header {{
      position: sticky;
      top: 0;
      z-index: 100;
      background: rgba(17, 24, 35, 0.85);
      backdrop-filter: blur(14px);
      -webkit-backdrop-filter: blur(14px);
      border-bottom: 1px solid var(--border-subtle);
      padding: 14px 28px;
    }}

    .header-top {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 20px;
      flex-wrap: wrap;
    }}

    .brand-group {{
      display: flex;
      align-items: center;
      gap: 14px;
    }}

    .brand-logo {{
      width: 36px;
      height: 36px;
      background: linear-gradient(135deg, #e08a3c, #f59e0b);
      border-radius: var(--radius-sm);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 20px;
      font-weight: 800;
      color: #fff;
      box-shadow: 0 4px 12px rgba(224, 138, 60, 0.3);
    }}

    .brand-text h1 {{
      font-size: 19px;
      font-weight: 800;
      letter-spacing: -0.3px;
      display: flex;
      align-items: center;
      gap: 8px;
    }}

    .brand-badge {{
      font-size: 10px;
      font-weight: 700;
      letter-spacing: 1px;
      padding: 3px 8px;
      border-radius: 999px;
      background: rgba(56, 189, 248, 0.15);
      color: var(--accent-sky);
      border: 1px solid rgba(56, 189, 248, 0.3);
    }}

    .brand-sub {{
      font-size: 12px;
      color: var(--text-muted);
    }}

    .stats-row {{
      display: flex;
      align-items: center;
      gap: 16px;
    }}

    .stat-pill {{
      display: flex;
      align-items: center;
      gap: 8px;
      background: var(--bg-card);
      border: 1px solid var(--border-subtle);
      padding: 6px 12px;
      border-radius: 999px;
      font-size: 12px;
      font-weight: 600;
    }}

    .stat-num {{
      color: var(--accent-sky);
      font-family: 'JetBrains Mono', monospace;
      font-weight: 700;
    }}

    /* Controls Bar */
    .controls-bar {{
      margin-top: 14px;
      display: flex;
      align-items: center;
      gap: 12px;
      flex-wrap: wrap;
    }}

    .search-box {{
      flex: 1;
      min-width: 240px;
      position: relative;
    }}

    .search-input {{
      width: 100%;
      background: var(--bg-input);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md);
      padding: 10px 14px 10px 38px;
      font-size: 13.5px;
      color: var(--text-main);
      font-family: inherit;
      outline: none;
      transition: border-color 0.15s ease, box-shadow 0.15s ease;
    }}

    .search-input:focus {{
      border-color: var(--accent-sky);
      box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.15);
    }}

    .search-icon {{
      position: absolute;
      left: 12px;
      top: 50%;
      transform: translateY(-50%);
      color: var(--text-muted);
      pointer-events: none;
    }}

    .filter-chips {{
      display: flex;
      align-items: center;
      gap: 8px;
    }}

    .filter-chip {{
      background: var(--bg-card);
      border: 1px solid var(--border-subtle);
      color: var(--text-sub);
      padding: 8px 12px;
      border-radius: var(--radius-md);
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 6px;
      transition: all 0.15s ease;
    }}

    .filter-chip:hover {{
      color: var(--text-main);
      border-color: var(--border-accent);
    }}

    .filter-chip.active {{
      background: rgba(56, 189, 248, 0.15);
      border-color: var(--accent-sky);
      color: var(--accent-sky);
    }}

    /* Main Category Sidebar & Content Layout */
    .app-body {{
      display: flex;
      flex: 1;
      padding: 20px 28px 40px;
      gap: 24px;
      align-items: flex-start;
    }}

    /* Category Navigation Nav - Pinned Sticky on scroll */
    aside.cat-sidebar {{
      width: 230px;
      flex-shrink: 0;
      display: flex;
      flex-direction: column;
      gap: 4px;
      position: sticky;
      top: 125px;
      max-height: calc(100vh - 145px);
      overflow-y: auto;
      padding-right: 4px;
    }}

    aside.cat-sidebar::-webkit-scrollbar {{
      width: 4px;
    }}
    aside.cat-sidebar::-webkit-scrollbar-track {{
      background: transparent;
    }}
    aside.cat-sidebar::-webkit-scrollbar-thumb {{
      background: var(--border-subtle);
      border-radius: 4px;
    }}
    aside.cat-sidebar::-webkit-scrollbar-thumb:hover {{
      background: var(--border-accent);
    }}

    .cat-btn {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      width: 100%;
      padding: 10px 14px;
      border-radius: var(--radius-md);
      background: transparent;
      border: 1px solid transparent;
      color: var(--text-sub);
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
      font-family: inherit;
      transition: all 0.15s ease;
      user-select: none;
    }}

    .cat-btn:hover {{
      background: var(--bg-card);
      color: var(--text-main);
    }}

    .cat-btn.drag-target-hover {{
      background: rgba(56, 189, 248, 0.25) !important;
      border: 2px dashed #38bdf8 !important;
      color: #38bdf8 !important;
      transform: scale(1.03);
      box-shadow: 0 0 16px rgba(56, 189, 248, 0.4);
    }}

    .cat-btn.drag-hint {{
      border: 1px dashed rgba(56, 189, 248, 0.35);
    }}

    .cat-btn.active {{
      background: var(--bg-card);
      border-color: var(--border-subtle);
      color: var(--accent-sky);
      box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    }}

    .cat-label {{
      display: flex;
      align-items: center;
      gap: 10px;
    }}

    .cat-count {{
      font-family: 'JetBrains Mono', monospace;
      font-size: 11px;
      background: rgba(255,255,255,0.06);
      padding: 2px 6px;
      border-radius: 999px;
      color: var(--text-muted);
    }}

    .cat-btn.active .cat-count {{
      background: rgba(56, 189, 248, 0.2);
      color: var(--accent-sky);
    }}

    /* Main Gallery Grid */
    main.gallery-content {{
      flex: 1;
      min-width: 0;
    }}

    .cat-header-banner {{
      background: var(--bg-panel);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-lg);
      padding: 16px 20px;
      margin-bottom: 20px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
    }}

    .banner-text h2 {{
      font-size: 18px;
      font-weight: 700;
      display: flex;
      align-items: center;
      gap: 10px;
    }}

    .banner-text p {{
      font-size: 12.5px;
      color: var(--text-sub);
      margin-top: 4px;
    }}

    .item-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(170px, 1fr));
      gap: 14px;
    }}

    /* Item Card */
    .item-card {{
      background: var(--bg-card);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md);
      padding: 12px;
      display: flex;
      flex-direction: column;
      align-items: center;
      text-align: center;
      cursor: pointer;
      position: relative;
      transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease;
    }}

    .item-card:hover {{
      transform: translateY(-3px);
      border-color: var(--accent-sky);
      background: var(--bg-card-hover);
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
    }}

    .item-card[draggable="true"] {{
      cursor: grab;
    }}

    .item-card.dragging {{
      opacity: 0.35;
      border-color: var(--accent-sky);
      transform: scale(0.96);
    }}

    .card-thumb-wrap {{
      width: 120px;
      height: 120px;
      background: #090d14;
      border: 1px solid rgba(255,255,255,0.04);
      border-radius: var(--radius-sm);
      display: flex;
      align-items: center;
      justify-content: center;
      margin-bottom: 10px;
      position: relative;
      overflow: hidden;
    }}

    .card-thumb-wrap img {{
      max-width: 104px;
      max-height: 104px;
      object-fit: contain;
      image-rendering: -webkit-optimize-contrast;
    }}

    .badge-3d {{
      position: absolute;
      top: 6px;
      right: 6px;
      background: rgba(99, 102, 241, 0.85);
      color: #fff;
      font-size: 9px;
      font-weight: 700;
      padding: 2px 5px;
      border-radius: 4px;
      backdrop-filter: blur(4px);
    }}

    .badge-grow {{
      position: absolute;
      bottom: 6px;
      left: 6px;
      background: rgba(16, 185, 129, 0.85);
      color: #fff;
      font-size: 9px;
      font-weight: 700;
      padding: 2px 5px;
      border-radius: 4px;
      backdrop-filter: blur(4px);
    }}

    .card-quick-actions {{
      position: absolute;
      top: 6px;
      right: 6px;
      display: flex;
      gap: 4px;
      z-index: 5;
      opacity: 0;
      transition: opacity 0.15s ease;
    }}

    .item-card:hover .card-quick-actions {{
      opacity: 1;
    }}

    .card-action-btn {{
      width: 26px;
      height: 26px;
      border-radius: 6px;
      background: rgba(17, 24, 35, 0.88);
      border: 1px solid rgba(255, 255, 255, 0.15);
      color: var(--text-muted);
      font-size: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      transition: all 0.15s cubic-bezier(0.16, 1, 0.3, 1);
      backdrop-filter: blur(4px);
    }}

    .card-action-rename:hover {{
      background: var(--accent-cyan);
      color: #04101d;
      border-color: var(--accent-cyan);
      transform: scale(1.1);
      box-shadow: 0 0 10px rgba(6, 182, 212, 0.5);
    }}

    .card-action-delete:hover {{
      background: var(--accent-rose);
      color: #fff;
      border-color: var(--accent-rose);
      transform: scale(1.1);
      box-shadow: 0 0 10px rgba(225, 29, 72, 0.5);
    }}

    .card-action-regen:hover {{
      background: #0284c7;
      color: #fff;
      border-color: #38bdf8;
      transform: scale(1.1);
      box-shadow: 0 0 10px rgba(2, 132, 199, 0.6);
    }}

    .card-select-btn {{
      position: absolute;
      top: 6px;
      left: 6px;
      width: 24px;
      height: 24px;
      border-radius: 6px;
      background: rgba(17, 24, 35, 0.85);
      border: 1.5px solid rgba(255, 255, 255, 0.25);
      color: transparent;
      font-size: 13px;
      font-weight: 900;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      z-index: 6;
      opacity: 0.35;
      transition: all 0.15s cubic-bezier(0.16, 1, 0.3, 1);
      backdrop-filter: blur(4px);
      user-select: none;
    }}

    .item-card:hover .card-select-btn {{
      opacity: 0.85;
      border-color: rgba(255, 255, 255, 0.5);
    }}

    .card-select-btn.checked {{
      background: var(--accent-rose);
      border-color: var(--accent-rose);
      color: #fff;
      opacity: 1 !important;
      box-shadow: 0 0 10px rgba(225, 29, 72, 0.6);
    }}

    .item-card.selected {{
      border-color: var(--accent-rose) !important;
      background: rgba(225, 29, 72, 0.08) !important;
      box-shadow: 0 0 15px rgba(225, 29, 72, 0.25) !important;
    }}

    .confirm-checkbox-wrap {{
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      font-size: 12px;
      color: var(--text-sub);
      margin-bottom: 18px;
      cursor: pointer;
      user-select: none;
    }}

    .confirm-checkbox-wrap input {{
      accent-color: var(--accent-rose);
      width: 15px;
      height: 15px;
      cursor: pointer;
    }}

    .card-name {{
      font-size: 13px;
      font-weight: 700;
      color: var(--text-main);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      width: 100%;
    }}

    .card-id {{
      font-family: 'JetBrains Mono', monospace;
      font-size: 10.5px;
      color: var(--text-muted);
      margin-top: 2px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      width: 100%;
    }}

    /* ================================================= */
    /* Species Folder Card & Subfolder Navigation */
    /* ================================================= */
    .folder-card {{
      background: linear-gradient(145deg, #121c29, #1a2a3e);
      border: 1.5px solid rgba(56, 189, 248, 0.4);
      border-radius: var(--radius-md);
      padding: 14px 12px 12px;
      display: flex;
      flex-direction: column;
      align-items: center;
      text-align: center;
      cursor: pointer;
      position: relative;
      transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
      box-shadow: 0 6px 18px rgba(0, 0, 0, 0.4);
    }}

    .folder-card:hover {{
      transform: translateY(-4px) scale(1.02);
      border-color: #38bdf8;
      box-shadow: 0 12px 30px rgba(56, 189, 248, 0.25), 0 0 16px rgba(56, 189, 248, 0.15);
      background: linear-gradient(145deg, #17263b, #203652);
    }}

    .folder-tab {{
      position: absolute;
      top: -10px;
      left: 12px;
      background: #0284c7;
      color: #fff;
      font-size: 10px;
      font-weight: 800;
      letter-spacing: 0.5px;
      text-transform: uppercase;
      padding: 2px 10px;
      border-radius: 6px 6px 0 0;
      display: flex;
      align-items: center;
      gap: 4px;
      box-shadow: 0 -2px 6px rgba(0, 0, 0, 0.3);
    }}

    .folder-thumb-stack {{
      width: 120px;
      height: 120px;
      background: #090d14;
      border: 1px solid rgba(56, 189, 248, 0.2);
      border-radius: var(--radius-sm);
      display: flex;
      align-items: center;
      justify-content: center;
      margin-bottom: 10px;
      position: relative;
      overflow: hidden;
    }}

    .folder-thumb-stack img {{
      max-width: 100px;
      max-height: 100px;
      object-fit: contain;
      filter: drop-shadow(0 4px 8px rgba(0,0,0,0.6));
    }}

    .folder-count-badge {{
      position: absolute;
      bottom: 6px;
      right: 6px;
      background: rgba(15, 23, 42, 0.88);
      border: 1px solid rgba(56, 189, 248, 0.4);
      color: #38bdf8;
      font-size: 10.5px;
      font-weight: 800;
      font-family: 'JetBrains Mono', monospace;
      padding: 2px 7px;
      border-radius: 999px;
      display: flex;
      align-items: center;
      gap: 3px;
    }}

    .folder-name {{
      font-size: 13px;
      font-weight: 800;
      color: #f8fafc;
      display: flex;
      align-items: center;
      gap: 6px;
      margin-bottom: 3px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      width: 100%;
    }}

    .folder-meta {{
      font-size: 11px;
      color: var(--text-sub);
      display: flex;
      align-items: center;
      gap: 6px;
    }}

    .folder-action-cue {{
      margin-top: 8px;
      font-size: 11px;
      font-weight: 700;
      color: #38bdf8;
      background: rgba(56, 189, 248, 0.1);
      border: 1px solid rgba(56, 189, 248, 0.25);
      padding: 3px 8px;
      border-radius: 999px;
      width: 100%;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 4px;
      transition: all 0.15s ease;
    }}

    .folder-card:hover .folder-action-cue {{
      background: #0284c7;
      color: #fff;
    }}

    /* Subfolder Breadcrumb Header */
    .subfolder-nav-banner {{
      background: linear-gradient(135deg, rgba(2, 132, 199, 0.18), rgba(15, 23, 42, 0.85));
      border: 1px solid rgba(56, 189, 248, 0.4);
      border-radius: var(--radius-lg);
      padding: 14px 20px;
      margin-bottom: 20px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      box-shadow: 0 6px 20px rgba(0,0,0,0.3);
    }}

    .subfolder-nav-left {{
      display: flex;
      align-items: center;
      gap: 14px;
    }}

    .btn-subfolder-back {{
      background: rgba(255, 255, 255, 0.08);
      border: 1px solid rgba(255, 255, 255, 0.2);
      color: #f8fafc;
      padding: 7px 14px;
      border-radius: var(--radius-md);
      font-size: 12.5px;
      font-weight: 700;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 6px;
      transition: all 0.15s ease;
    }}

    .btn-subfolder-back:hover {{
      background: #0284c7;
      border-color: #0284c7;
      color: #fff;
      transform: translateX(-2px);
    }}

    /* ================================================= */
    /* Item Details Modal (<dialog>) */
    /* ================================================= */
    dialog.item-modal {{
      margin: auto;
      border: 1px solid var(--border-accent);
      border-radius: var(--radius-xl);
      background: var(--bg-panel);
      color: var(--text-main);
      width: 90vw;
      max-width: 1060px;
      max-height: 88vh;
      overflow: hidden;
      box-shadow: 0 25px 60px rgba(0, 0, 0, 0.75);
    }}

    dialog.item-modal::backdrop {{
      background: rgba(5, 8, 13, 0.8);
      backdrop-filter: blur(10px);
      -webkit-backdrop-filter: blur(10px);
    }}

    .modal-container {{
      display: flex;
      flex-direction: column;
      height: 100%;
      max-height: 88vh;
    }}

    /* Modal Header */
    .modal-header {{
      padding: 18px 24px;
      border-bottom: 1px solid var(--border-subtle);
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      background: rgba(0,0,0,0.2);
    }}

    .modal-title-group {{
      display: flex;
      align-items: center;
      gap: 14px;
    }}

    .modal-icon-badge {{
      width: 46px;
      height: 46px;
      background: var(--bg-card);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md);
      display: flex;
      align-items: center;
      justify-content: center;
    }}

    .modal-icon-badge img {{
      max-width: 38px;
      max-height: 38px;
    }}

    .modal-name-wrap h3 {{
      font-size: 18px;
      font-weight: 800;
      letter-spacing: -0.2px;
    }}

    .modal-id-tags {{
      display: flex;
      align-items: center;
      gap: 8px;
      margin-top: 2px;
    }}

    .modal-id-tag {{
      font-family: 'JetBrains Mono', monospace;
      font-size: 11.5px;
      color: var(--accent-sky);
    }}

    .modal-cat-tag {{
      font-size: 10px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      background: rgba(255,255,255,0.06);
      padding: 2px 7px;
      border-radius: 4px;
      color: var(--text-sub);
    }}

    .modal-close-btn {{
      background: var(--bg-card);
      border: 1px solid var(--border-subtle);
      color: var(--text-muted);
      width: 34px;
      height: 34px;
      border-radius: 50%;
      font-size: 18px;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      transition: all 0.15s ease;
    }}

    .modal-header-actions {{
      display: flex;
      align-items: center;
      gap: 10px;
    }}

    .modal-regen-btn {{
      background: rgba(2, 132, 199, 0.15);
      border: 1px solid rgba(2, 132, 199, 0.4);
      color: #38bdf8;
      padding: 6px 14px;
      border-radius: var(--radius-md);
      font-size: 12px;
      font-weight: 700;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 6px;
      transition: all 0.15s ease;
    }}

    .modal-regen-btn:hover {{
      background: #0284c7;
      color: #fff;
      border-color: #0284c7;
      box-shadow: 0 0 14px rgba(2, 132, 199, 0.4);
      transform: translateY(-1px);
    }}

    .modal-rename-btn {{
      background: rgba(6, 182, 212, 0.12);
      border: 1px solid rgba(6, 182, 212, 0.4);
      color: #38bdf8;
      padding: 6px 14px;
      border-radius: var(--radius-md);
      font-size: 12px;
      font-weight: 700;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 6px;
      transition: all 0.15s ease;
    }}

    .modal-rename-btn:hover {{
      background: var(--accent-cyan);
      color: #04101d;
      border-color: var(--accent-cyan);
      box-shadow: 0 0 14px rgba(6, 182, 212, 0.4);
    }}

    .modal-delete-btn {{
      background: rgba(225, 29, 72, 0.12);
      border: 1px solid rgba(225, 29, 72, 0.4);
      color: #fb7185;
      padding: 6px 14px;
      border-radius: var(--radius-md);
      font-size: 12px;
      font-weight: 700;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 6px;
      transition: all 0.15s ease;
    }}

    .modal-delete-btn:hover {{
      background: var(--accent-rose);
      color: #fff;
      border-color: var(--accent-rose);
      box-shadow: 0 0 14px rgba(225, 29, 72, 0.4);
    }}

    .modal-kbd {{
      background: rgba(0, 0, 0, 0.3);
      border: 1px solid rgba(255, 255, 255, 0.2);
      border-radius: 4px;
      padding: 1px 5px;
      font-family: 'JetBrains Mono', monospace;
      font-size: 10px;
    }}

    /* Floating Bottom-Right Batch Delete Bar */
    .floating-batch-bar {{
      position: fixed;
      bottom: 28px;
      right: 32px;
      z-index: 999;
      display: flex;
      align-items: center;
      gap: 16px;
      padding: 10px 16px 10px 20px;
      border-radius: 50px;
      background: #111823;
      border: 1.5px solid rgba(225, 29, 72, 0.6);
      box-shadow: 0 16px 40px rgba(0, 0, 0, 0.85), 0 0 25px rgba(225, 29, 72, 0.35);
      backdrop-filter: blur(14px);
      transform: translateY(140%);
      opacity: 0;
      pointer-events: none;
      transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
    }}

    .floating-batch-bar.show {{
      transform: translateY(0);
      opacity: 1;
      pointer-events: auto;
    }}

    .batch-bar-info {{
      display: flex;
      align-items: center;
      gap: 10px;
      font-size: 13.5px;
      font-weight: 700;
      color: #f8fafc;
    }}

    .batch-bar-check {{
      width: 22px;
      height: 22px;
      border-radius: 50%;
      background: var(--accent-rose);
      color: #fff;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 12px;
      font-weight: 900;
    }}

    .batch-bar-actions {{
      display: flex;
      align-items: center;
      gap: 8px;
    }}

    .btn-clear-selection {{
      background: rgba(255, 255, 255, 0.08);
      border: 1px solid rgba(255, 255, 255, 0.15);
      color: var(--text-sub);
      padding: 7px 14px;
      border-radius: 20px;
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.15s ease;
    }}

    .btn-clear-selection:hover {{
      background: rgba(255, 255, 255, 0.16);
      color: #fff;
    }}

    .btn-move-all {{
      background: linear-gradient(135deg, #6366f1, #4f46e5);
      border: 1px solid rgba(255, 255, 255, 0.25);
      color: #fff;
      padding: 8px 18px;
      border-radius: 20px;
      font-size: 13px;
      font-weight: 800;
      cursor: grab;
      display: flex;
      align-items: center;
      gap: 6px;
      transition: all 0.15s ease;
      box-shadow: 0 0 14px rgba(99, 102, 241, 0.5);
      user-select: none;
    }}

    .btn-move-all:hover {{
      background: linear-gradient(135deg, #818cf8, #6366f1);
      transform: scale(1.04);
      box-shadow: 0 0 20px rgba(99, 102, 241, 0.7);
    }}

    .btn-move-all:active {{
      cursor: grabbing;
    }}

    .btn-regen-all {{
      background: #0284c7;
      border: 1px solid rgba(255, 255, 255, 0.2);
      color: #fff;
      padding: 8px 18px;
      border-radius: 20px;
      font-size: 13px;
      font-weight: 800;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 6px;
      transition: all 0.15s ease;
      box-shadow: 0 0 14px rgba(2, 132, 199, 0.5);
    }}

    .btn-regen-all:hover {{
      background: #0ea5e9;
      transform: scale(1.04);
      box-shadow: 0 0 20px rgba(14, 165, 233, 0.7);
    }}

    .btn-delete-all {{
      background: var(--accent-rose);
      border: 1px solid rgba(255, 255, 255, 0.2);
      color: #fff;
      padding: 8px 18px;
      border-radius: 20px;
      font-size: 13px;
      font-weight: 800;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 6px;
      transition: all 0.15s ease;
      box-shadow: 0 0 14px rgba(225, 29, 72, 0.5);
    }}

    .btn-delete-all:hover {{
      background: #f43f5e;
      transform: scale(1.04);
      box-shadow: 0 0 20px rgba(225, 29, 72, 0.7);
    }}

    dialog.confirm-dialog {{
      margin: auto;
      border: 1px solid rgba(225, 29, 72, 0.5);
      border-radius: var(--radius-lg);
      background: #111823;
      color: var(--text-main);
      max-width: 440px;
      width: 90vw;
      padding: 0;
      box-shadow: 0 25px 60px rgba(0, 0, 0, 0.85);
      overflow: hidden;
    }}

    dialog.confirm-dialog::backdrop {{
      background: rgba(5, 8, 13, 0.85);
      backdrop-filter: blur(8px);
    }}

    .confirm-box {{
      padding: 24px;
      text-align: center;
    }}

    .confirm-icon {{
      font-size: 42px;
      margin-bottom: 12px;
    }}

    .confirm-title {{
      font-size: 18px;
      font-weight: 800;
      color: #fff;
      margin-bottom: 8px;
    }}

    .confirm-msg {{
      font-size: 13px;
      color: var(--text-sub);
      line-height: 1.5;
      margin-bottom: 14px;
    }}

    .confirm-path-pill {{
      font-family: 'JetBrains Mono', monospace;
      font-size: 11.5px;
      color: var(--accent-gold);
      background: rgba(245, 158, 11, 0.1);
      border: 1px solid rgba(245, 158, 11, 0.25);
      border-radius: 6px;
      padding: 6px 12px;
      margin-bottom: 20px;
      word-break: break-all;
    }}

    .confirm-actions {{
      display: flex;
      gap: 12px;
      justify-content: center;
    }}

    .btn-cancel {{
      background: var(--bg-card);
      border: 1px solid var(--border-subtle);
      color: var(--text-sub);
      padding: 8px 18px;
      border-radius: var(--radius-md);
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.15s ease;
    }}

    .btn-cancel:hover {{
      background: var(--bg-card-hover);
      color: var(--text-main);
    }}

    .btn-danger {{
      background: var(--accent-rose);
      border: 1px solid var(--accent-rose);
      color: #fff;
      padding: 8px 18px;
      border-radius: var(--radius-md);
      font-size: 13px;
      font-weight: 700;
      cursor: pointer;
      transition: all 0.15s ease;
    }}

    .btn-danger:hover {{
      background: #be123c;
      box-shadow: 0 0 16px rgba(225, 29, 72, 0.5);
    }}

    .toast {{
      position: fixed;
      bottom: 24px;
      right: 24px;
      background: #1e293b;
      border: 1px solid var(--border-accent);
      color: #fff;
      padding: 12px 20px;
      border-radius: var(--radius-md);
      box-shadow: 0 12px 30px rgba(0, 0, 0, 0.5);
      font-size: 13px;
      font-weight: 600;
      opacity: 0;
      transform: translateY(20px);
      transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
      pointer-events: none;
      z-index: 9999;
    }}

    .toast.show {{
      opacity: 1;
      transform: translateY(0);
    }}

    .toast.success {{
      border-color: var(--accent-emerald);
      background: #064e3b;
    }}

    .toast.error {{
      border-color: var(--accent-rose);
      background: #881337;
    }}

    .toast.warning {{
      border-color: var(--accent-gold);
      background: #78350f;
    }}

    .modal-close-btn:hover {{
      background: var(--accent-rose);
      color: #fff;
      border-color: var(--accent-rose);
    }}

    /* Modal Split Body */
    .modal-body {{
      display: grid;
      grid-template-columns: 420px 1fr;
      flex: 1;
      min-height: 0;
      overflow: hidden;
    }}

    /* Left Column: 3D Viewport */
    .modal-viewport-col {{
      background: #080c12;
      border-right: 1px solid var(--border-subtle);
      display: flex;
      flex-direction: column;
      position: relative;
    }}

    .viewport-canvas-wrap {{
      flex: 1;
      width: 100%;
      height: 100%;
      position: relative;
      display: flex;
      align-items: center;
      justify-content: center;
      min-height: 360px;
    }}

    model-viewer {{
      width: 100%;
      height: 100%;
      --poster-color: transparent;
    }}

    #three-viewport-canvas {{
      width: 100%;
      height: 100%;
      display: block;
    }}

    .viewport-toolbar {{
      position: absolute;
      bottom: 12px;
      left: 12px;
      right: 12px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      pointer-events: none;
    }}

    .viewport-pill {{
      pointer-events: auto;
      background: rgba(17, 24, 35, 0.85);
      border: 1px solid var(--border-subtle);
      backdrop-filter: blur(8px);
      padding: 4px 10px;
      border-radius: 999px;
      font-size: 11px;
      font-weight: 600;
      color: var(--text-sub);
    }}

    .viewport-hint {{
      font-size: 10.5px;
      color: var(--text-muted);
    }}

    /* Right Column: JSON Human-Readable Inspector */
    .modal-info-col {{
      padding: 24px;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 20px;
    }}

    .info-section {{
      background: var(--bg-card);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-lg);
      padding: 16px;
    }}

    .info-sec-title {{
      font-size: 12px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.8px;
      color: var(--accent-sky);
      margin-bottom: 12px;
      display: flex;
      align-items: center;
      gap: 6px;
    }}

    .kv-grid {{
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 10px;
    }}

    .kv-box {{
      background: rgba(0,0,0,0.25);
      border: 1px solid rgba(255,255,255,0.04);
      padding: 8px 12px;
      border-radius: var(--radius-sm);
    }}

    .kv-key {{
      font-size: 11px;
      color: var(--text-muted);
      font-weight: 500;
    }}

    .kv-val {{
      font-size: 13px;
      font-weight: 700;
      color: var(--text-main);
      margin-top: 2px;
      font-family: 'JetBrains Mono', monospace;
    }}

    /* Growth Stepper */
    .growth-stepper {{
      display: flex;
      align-items: center;
      gap: 8px;
      margin-top: 10px;
    }}

    .growth-step {{
      flex: 1;
      background: rgba(0,0,0,0.3);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-sm);
      padding: 8px 10px;
      text-align: center;
    }}

    .growth-step.active {{
      border-color: var(--accent-emerald);
      background: rgba(16, 185, 129, 0.1);
    }}

    .step-num {{
      font-size: 10px;
      font-weight: 800;
      color: var(--accent-emerald);
    }}

    .step-name {{
      font-size: 11.5px;
      font-weight: 700;
      color: var(--text-main);
      margin-top: 2px;
    }}

    .step-age {{
      font-size: 10px;
      color: var(--text-muted);
      font-family: 'JetBrains Mono', monospace;
    }}

    /* Utilities List */
    .util-row {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 6px 0;
      border-bottom: 1px solid rgba(255,255,255,0.05);
      font-size: 12px;
    }}

    .util-row:last-child {{
      border-bottom: none;
    }}

    .util-name {{
      color: var(--text-sub);
      font-weight: 600;
    }}

    .util-val {{
      font-family: 'JetBrains Mono', monospace;
      font-size: 11.5px;
      color: var(--text-main);
    }}

    /* Raw JSON Toggle */
    .json-accordion {{
      background: var(--bg-card);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-lg);
      overflow: hidden;
    }}

    .json-acc-header {{
      padding: 12px 16px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      cursor: pointer;
      user-select: none;
      font-size: 12px;
      font-weight: 700;
      color: var(--text-sub);
    }}

    .json-acc-header:hover {{
      color: var(--text-main);
    }}

    .copy-json-btn {{
      background: rgba(255,255,255,0.08);
      border: none;
      color: var(--text-main);
      font-size: 11px;
      font-weight: 600;
      padding: 4px 8px;
      border-radius: 4px;
      cursor: pointer;
    }}

    .copy-json-btn:hover {{
      background: var(--accent-sky);
      color: #000;
    }}

    pre.json-pre {{
      background: #090d14;
      padding: 16px;
      font-family: 'JetBrains Mono', monospace;
      font-size: 11.5px;
      line-height: 1.5;
      color: #cbd5e1;
      max-height: 240px;
      overflow-y: auto;
      border-top: 1px solid var(--border-subtle);
    }}

    /* Scrollbars */
    ::-webkit-scrollbar {{
      width: 6px;
      height: 6px;
    }}
    ::-webkit-scrollbar-track {{
      background: rgba(0,0,0,0.2);
    }}
    ::-webkit-scrollbar-thumb {{
      background: var(--border-subtle);
      border-radius: 3px;
    }}
    ::-webkit-scrollbar-thumb:hover {{
      background: var(--border-accent);
    }}
  </style>
</head>
<body>

  <!-- Top App Header -->
  <header class="app-header">
    <div class="header-top">
      <div class="brand-group">
        <div class="brand-logo">H</div>
        <div class="brand-text">
          <h1>Homesteader <span class="brand-badge">Asset Kit</span></h1>
          <div class="brand-sub">Unified Game Items, Structures & 3D Catalog</div>
        </div>
      </div>
      
      <div class="stats-row">
        <div class="stat-pill">Items: <span class="stat-num" id="stat-total">{total_count}</span></div>
        <div class="stat-pill">3D Meshes: <span class="stat-num" id="stat-3d">{with_3d_count}</span></div>
        <div class="stat-pill">4-Stage Growable: <span class="stat-num" id="stat-growth">{growable_count}</span></div>
      </div>
    </div>

    <!-- Controls Toolbar -->
    <div class="controls-bar">
      <div class="search-box">
        <span class="search-icon">🔍</span>
        <input type="text" id="search-input" class="search-input" placeholder="Search {total_count} assets by name, item ID, or tag... (Press '/' to focus)">
      </div>

      <div class="filter-chips">
        <button class="filter-chip active" data-filter="all" id="chip-all">All Assets</button>
        <button class="filter-chip" data-filter="duplicates" id="chip-duplicates" title="List all duplicate assets across categories" style="border-color: rgba(245, 158, 11, 0.4); color: #f59e0b;">⚠️ Duplicates (<span id="stat-dup-count">0</span>)</button>
        <button class="filter-chip" data-filter="3d" id="chip-3d">📦 3D Models Only</button>
        <button class="filter-chip" data-filter="grow" id="chip-grow">🌱 Growable</button>
        <button class="filter-chip active" id="btn-group-species" title="Toggle grouping growable lifecycle stages by species into clickable subfolders" style="border-color: rgba(56, 189, 248, 0.4); color: #38bdf8;">📂 Group Species: ON</button>
      </div>
    </div>
  </header>

  <!-- App Main Body -->
  <div class="app-body">
    <!-- Category Sidebar -->
    <aside class="cat-sidebar" id="cat-sidebar">
      <!-- Populated dynamically via JS -->
    </aside>

    <!-- Main Content Area -->
    <main class="gallery-content">
      <div class="cat-header-banner" id="cat-banner">
        <div class="banner-text">
          <h2 id="banner-title">🏛️ Structures</h2>
          <p id="banner-desc">Placed world buildings, farmhouses, cabins, barns, silos, sheds, greenhouses, coops, shelters, and towers.</p>
        </div>
        <div class="banner-meta" id="banner-count-pill" style="display: flex; align-items: center; gap: 8px;">
          <span class="stat-pill">Showing: <span class="stat-num" id="showing-count">0</span></span>
          <button class="stat-pill" id="select-all-btn" style="cursor: pointer; background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.15); color: var(--text-sub);" title="Check or uncheck all currently shown assets">☑️ Select All Shown</button>
          <button class="stat-pill" id="regen-all-btn" style="cursor: pointer; background: rgba(2, 132, 199, 0.15); border: 1px solid rgba(2, 132, 199, 0.4); color: #38bdf8;" title="Regenerate all icons in current view following HUD rules">🔄 Regen Icons</button>
        </div>
      </div>

      <div class="item-grid" id="item-grid">
        <!-- Rendered dynamically via JS -->
      </div>
    </main>
  </div>

  <!-- Native <dialog> Modal for Item Inspection -->
  <dialog class="item-modal" id="item-modal">
    <div class="modal-container">
      <!-- Modal Header -->
      <div class="modal-header">
        <div class="modal-title-group">
          <div class="modal-icon-badge" id="m-icon-badge">
            <img id="m-icon-img" src="" alt="Icon">
          </div>
          <div class="modal-name-wrap">
            <h3 id="m-name">Item Name</h3>
            <div class="modal-id-tags">
              <span class="modal-id-tag" id="m-id">item_id</span>
              <span class="modal-cat-tag" id="m-cat">Category</span>
            </div>
          </div>
        </div>
        <div class="modal-header-actions">
          <button class="modal-regen-btn" id="m-regen-btn" title="Regenerate Icon (HUD 128x128 3D low-poly rules)">
            🔄 Regen Icon
          </button>
          <button class="modal-rename-btn" id="m-rename-btn" title="Rename Asset (F2 key)">
            ✏️ Rename <kbd class="modal-kbd">F2</kbd>
          </button>
          <button class="modal-delete-btn" id="m-delete-btn" title="Permanently Delete Asset (Delete key)">
            🗑️ Delete Asset <kbd class="modal-kbd">Del</kbd>
          </button>
          <button class="modal-close-btn" id="m-close-btn" title="Close (Esc)">✕</button>
        </div>
      </div>

      <!-- Modal Body (3D Viewport on Left, Human-Readable Inspector on Right) -->
      <div class="modal-body">
        <!-- Left: 3D Viewport -->
        <div class="modal-viewport-col">
          <div class="viewport-canvas-wrap" id="viewport-wrap">
            <!-- model-viewer for GLB or Three.js canvas for OBJ inserted here -->
          </div>
          <div class="viewport-toolbar">
            <div class="viewport-pill" id="m-model-badge">3D Model Available</div>
            <div class="viewport-hint">🖱️ Left Drag: Rotate • Right Drag: Pan • Scroll: Zoom</div>
          </div>
        </div>

        <!-- Right: Human-Readable Inspector -->
        <div class="modal-info-col">
          <!-- Description -->
          <div class="info-section">
            <div class="info-sec-title">📖 Description</div>
            <p id="m-desc" style="font-size: 13.5px; color: var(--text-main); line-height: 1.5;"></p>
          </div>

          <!-- Physical & Game Properties -->
          <div class="info-section">
            <div class="info-sec-title">⚙️ Simulation Properties</div>
            <div class="kv-grid">
              <div class="kv-box"><div class="kv-key">Weight</div><div class="kv-val" id="m-weight">1.0 kg</div></div>
              <div class="kv-box"><div class="kv-key">Max Stack Size</div><div class="kv-val" id="m-stack">99</div></div>
              <div class="kv-box"><div class="kv-key">Base Value</div><div class="kv-val" id="m-value">$10.00</div></div>
              <div class="kv-box"><div class="kv-key">Consumable</div><div class="kv-val" id="m-consumable">No</div></div>
              <div class="kv-box"><div class="kv-key">Footprint</div><div class="kv-val" id="m-footprint">—</div></div>
              <div class="kv-box"><div class="kv-key">Available Formats</div><div class="kv-val" id="m-formats-summary">—</div></div>
            </div>
          </div>

          <!-- 3D Dimensions & Geometry -->
          <div class="info-section" id="sec-dimensions">
            <div class="info-sec-title">📐 3D Dimensions & Metric Geometry</div>
            <div class="kv-grid">
              <div class="kv-box"><div class="kv-key">Width (X)</div><div class="kv-val" id="m-dim-x">—</div></div>
              <div class="kv-box"><div class="kv-key">Depth (Y)</div><div class="kv-val" id="m-dim-y">—</div></div>
              <div class="kv-box"><div class="kv-key">Height (Z)</div><div class="kv-val" id="m-dim-z">—</div></div>
              <div class="kv-box"><div class="kv-key">Polygons / Faces</div><div class="kv-val" id="m-faces">—</div></div>
            </div>
          </div>

          <!-- Utilities -->
          <div class="info-section" id="sec-utilities">
            <div class="info-sec-title">🔌 Utility Infrastructure</div>
            <div id="m-util-container">
              <!-- Utility rows inserted dynamically -->
            </div>
          </div>

          <!-- 4-Stage Growth Lifecycle -->
          <div class="info-section" id="sec-growth">
            <div class="info-sec-title">🌱 4-Stage Growth Progression</div>
            <div class="growth-stepper" id="m-growth-stepper">
              <!-- Steps inserted dynamically -->
            </div>
          </div>

          <!-- Raw JSON Manifest Accordion -->
          <div class="json-accordion">
            <div class="json-acc-header" id="json-acc-header">
              <span>📄 Machine-Readable Plugin Manifest (<span id="m-json-filename">item.json</span>)</span>
              <button class="copy-json-btn" id="copy-json-btn" title="Copy raw JSON">Copy JSON</button>
            </div>
            <pre class="json-pre" id="m-raw-json"></pre>
          </div>
        </div>
      </div>
    </div>
  </dialog>

  <!-- Confirm Delete Modal -->
  <dialog class="confirm-dialog" id="confirm-delete-dialog">
    <div class="confirm-box">
      <div class="confirm-icon">⚠️</div>
      <h4 class="confirm-title">Permanently Delete Asset?</h4>
      <p class="confirm-msg" id="confirm-delete-msg">Are you sure you want to permanently delete this asset folder from disk?</p>
      <div class="confirm-path-pill" id="confirm-delete-path">assets/category/item_id</div>
      <label class="confirm-checkbox-wrap">
        <input type="checkbox" id="dont-ask-delete">
        <span>Don't ask again (1-click instant delete)</span>
      </label>
      <div class="confirm-actions">
        <button class="btn-cancel" id="confirm-cancel-btn">Cancel (Esc)</button>
        <button class="btn-danger" id="confirm-proceed-btn">Permanently Delete (Enter)</button>
      </div>
    </div>
  </dialog>

  <!-- Rename Asset Modal -->
  <dialog class="confirm-dialog" id="rename-dialog" style="border-color: rgba(6, 182, 212, 0.5); max-width: 460px;">
    <div class="confirm-box" style="text-align: left; padding: 24px;">
      <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px;">
        <div style="font-size: 24px; width: 40px; height: 40px; border-radius: 10px; background: rgba(6, 182, 212, 0.12); display: flex; align-items: center; justify-content: center; border: 1px solid rgba(6, 182, 212, 0.3);">✏️</div>
        <div>
          <h4 class="confirm-title" style="margin: 0; text-align: left; font-size: 16px;">Rename Asset</h4>
          <div style="font-size: 11px; color: var(--text-muted); font-family: 'JetBrains Mono', monospace; margin-top: 2px;" id="rename-path-hint">assets/category/item_id</div>
        </div>
      </div>
      <div style="margin-bottom: 14px;">
        <label style="display: block; font-size: 12px; font-weight: 700; color: var(--text-sub); margin-bottom: 6px;">Display Name</label>
        <input type="text" id="rename-name-input" style="width: 100%; border-radius: 6px; padding: 9px 12px; font-size: 13.5px; background: #0c121c; border: 1px solid rgba(255,255,255,0.15); color: #f8fafc; outline: none;" placeholder="e.g. Chicken Coop">
      </div>
      <div style="margin-bottom: 22px;">
        <label style="display: block; font-size: 12px; font-weight: 700; color: var(--text-sub); margin-bottom: 6px;">
          Asset ID & Folder Slug <span style="font-weight: normal; color: var(--text-muted); font-size: 11px;">(alphanumeric, underscores)</span>
        </label>
        <input type="text" id="rename-id-input" style="width: 100%; border-radius: 6px; padding: 9px 12px; font-size: 13px; font-family: 'JetBrains Mono', monospace; background: #0c121c; border: 1px solid rgba(255,255,255,0.15); color: #38bdf8; outline: none;" placeholder="e.g. chicken_coop">
      </div>
      <div class="confirm-actions" style="justify-content: flex-end; gap: 10px;">
        <button class="btn-cancel" id="rename-cancel-btn">Cancel (Esc)</button>
        <button class="btn-primary" id="rename-proceed-btn" style="background: var(--accent-cyan); color: #04101d; border: none; font-weight: 700; padding: 8px 18px; border-radius: 6px; cursor: pointer;">Save Changes (Enter)</button>
      </div>
    </div>
  </dialog>

  <!-- Floating Bottom-Right Batch Delete Bar -->
  <div class="floating-batch-bar" id="floating-batch-bar">
    <div class="batch-bar-info">
      <span class="batch-bar-check">✓</span>
      <span id="batch-count-text">0 checked</span>
    </div>
    <div class="batch-bar-actions">
      <button class="btn-clear-selection" id="batch-clear-btn" title="Clear checked items (Esc)">Clear</button>
      <button class="btn-move-all" id="batch-move-btn" draggable="true" title="Drag this button onto any category on the left sidebar to move all checked assets">
        📦 Move All (<span id="batch-move-count">0</span>)
      </button>
      <button class="btn-regen-all" id="batch-regen-btn" title="Regenerate icons for all checked assets (HUD 128x128 3D low-poly standard)">
        🔄 Regen Icons (<span id="batch-regen-count">0</span>)
      </button>
      <button class="btn-delete-all" id="batch-delete-btn" title="Delete all checked assets">
        🗑️ Delete All (<span id="batch-delete-count">0</span>)
      </button>
    </div>
  </div>

  <!-- Batch Delete Confirmation Modal -->
  <dialog class="confirm-dialog" id="batch-delete-dialog" style="max-width: 520px;">
    <div class="confirm-box" style="text-align: left; padding: 24px;">
      <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 14px;">
        <div style="font-size: 26px; width: 44px; height: 44px; border-radius: 10px; background: rgba(225, 29, 72, 0.15); display: flex; align-items: center; justify-content: center; border: 1px solid rgba(225, 29, 72, 0.4); color: #fb7185;">⚠️</div>
        <div>
          <h4 class="confirm-title" style="margin: 0; text-align: left; font-size: 17px; color: #f8fafc;">Delete <span id="batch-dialog-count">0</span> Selected Assets?</h4>
          <p style="margin: 3px 0 0 0; font-size: 12px; color: var(--text-muted);">Permanently removes all checked asset folders from disk.</p>
        </div>
      </div>
      <div id="batch-dialog-list" style="max-height: 180px; overflow-y: auto; background: #0c121c; border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; padding: 10px 12px; margin-bottom: 18px; display: flex; flex-wrap: wrap; gap: 6px;">
        <!-- Filled dynamically with asset tags -->
      </div>
      <div class="confirm-actions" style="justify-content: flex-end; gap: 10px;">
        <button class="btn-cancel" id="batch-cancel-btn">Cancel (Esc)</button>
        <button class="btn-danger" id="batch-confirm-btn" style="background: var(--accent-rose); color: #fff; border: none; font-weight: 700; padding: 9px 20px; border-radius: 6px; cursor: pointer;">Permanently Delete All (Enter)</button>
      </div>
    </div>
  </dialog>

  <!-- Floating Toast Notification -->
  <div class="toast" id="toast-notify"></div>


  <!-- Embedded Data Payload -->
  <script>
    const ALL_ITEMS = {items_json};
    const CATEGORIES_META = {cat_meta_json};
    
    let activeItem = null;
    const SELECTED_ITEMS = new Map(); // key category_slash_id to item object

    function toggleItemSelection(itemId, category, event) {{
      if (event) event.stopPropagation();
      const key = `${{category}}/${{itemId}}`;
      const it = ALL_ITEMS.find(x => x.id === itemId && x.category === category);
      if (!it) return;

      if (SELECTED_ITEMS.has(key)) {{
        SELECTED_ITEMS.delete(key);
      }} else {{
        SELECTED_ITEMS.set(key, {{ category: it.category, id: it.id, name: it.name }});
      }}

      updateSelectionUI();
    }}

    function updateSelectionUI() {{
      const count = SELECTED_ITEMS.size;
      const bar = document.getElementById("floating-batch-bar");
      const countText = document.getElementById("batch-count-text");
      const deleteCount = document.getElementById("batch-delete-count");
      const regenCount = document.getElementById("batch-regen-count");

      if (count > 0) {{
        bar.classList.add("show");
        countText.innerText = `${{count}} asset${{count === 1 ? '' : 's'}} checked`;
        if (deleteCount) deleteCount.innerText = count;
        if (regenCount) regenCount.innerText = count;
        const moveCount = document.getElementById("batch-move-count");
        if (moveCount) moveCount.innerText = count;
      }} else {{
        bar.classList.remove("show");
      }}

      // Update card checkmarks and outline
      document.querySelectorAll(".item-card").forEach(card => {{
        const id = card.dataset.itemId;
        const cat = card.dataset.category;
        const key = `${{cat}}/${{id}}`;
        const isChecked = SELECTED_ITEMS.has(key);

        card.classList.toggle("selected", isChecked);
        const btn = card.querySelector(".card-select-btn");
        if (btn) {{
          btn.classList.toggle("checked", isChecked);
          btn.innerText = isChecked ? "✓" : "";
          btn.title = isChecked ? "Uncheck asset" : "Check to delete";
        }}
      }});
    }}

    function clearSelection() {{
      SELECTED_ITEMS.clear();
      updateSelectionUI();
    }}

    function toggleSelectAllShown() {{
      const shownCards = document.querySelectorAll(".item-card");
      if (shownCards.length === 0) return;

      let allShownSelected = true;
      shownCards.forEach(c => {{
        const key = `${{c.dataset.category}}/${{c.dataset.itemId}}`;
        if (!SELECTED_ITEMS.has(key)) allShownSelected = false;
      }});

      if (allShownSelected) {{
        shownCards.forEach(c => {{
          const key = `${{c.dataset.category}}/${{c.dataset.itemId}}`;
          SELECTED_ITEMS.delete(key);
        }});
      }} else {{
        shownCards.forEach(c => {{
          const it = ALL_ITEMS.find(x => x.id === c.dataset.itemId && x.category === c.dataset.category);
          if (it) {{
            SELECTED_ITEMS.set(`${{it.category}}/${{it.id}}`, {{ category: it.category, id: it.id, name: it.name }});
          }}
        }});
      }}
      updateSelectionUI();
    }}

    function openBatchDeleteDialog() {{
      if (SELECTED_ITEMS.size === 0) return;
      const dialog = document.getElementById("batch-delete-dialog");
      const countEl = document.getElementById("batch-dialog-count");
      const listEl = document.getElementById("batch-dialog-list");
      const confirmBtn = document.getElementById("batch-confirm-btn");

      countEl.innerText = SELECTED_ITEMS.size;
      listEl.innerHTML = "";

      SELECTED_ITEMS.forEach(it => {{
        const tag = document.createElement("span");
        tag.style.cssText = "font-size: 11px; font-family: 'JetBrains Mono', monospace; background: rgba(225,29,72,0.15); color: #fb7185; border: 1px solid rgba(225,29,72,0.3); padding: 3px 8px; border-radius: 4px; display: inline-flex; align-items: center; gap: 4px;";
        tag.innerHTML = `<span>${{it.name}}</span> <span style="opacity: 0.6;">(${{it.id}})</span>`;
        listEl.appendChild(tag);
      }});

      dialog.showModal();
      confirmBtn.focus();
    }}

    async function executeBatchDelete() {{
      if (SELECTED_ITEMS.size === 0) return;
      const dialog = document.getElementById("batch-delete-dialog");
      const confirmBtn = document.getElementById("batch-confirm-btn");

      confirmBtn.disabled = true;
      confirmBtn.innerText = "Deleting...";

      const itemsToDelete = Array.from(SELECTED_ITEMS.values());

      try {{
        const res = await fetch("/api/delete-batch", {{
          method: "POST",
          headers: {{ "Content-Type": "application/json" }},
          body: JSON.stringify({{ items: itemsToDelete }})
        }});

        const text = await res.text();
        let data = null;
        try {{
          data = JSON.parse(text);
        }} catch (e) {{
          throw new Error(text.slice(0, 100) || "Invalid server response");
        }}

        if (res.ok && data.success) {{
          dialog.close();
          const deletedCount = data.deleted_count || itemsToDelete.length;

          // Remove deleted items from ALL_ITEMS
          itemsToDelete.forEach(it => {{
            const idx = ALL_ITEMS.findIndex(x => x.id === it.id && x.category === it.category);
            if (idx !== -1) ALL_ITEMS.splice(idx, 1);
          }});

          // Clear selection
          SELECTED_ITEMS.clear();
          updateSelectionUI();

          // Refresh sidebar & gallery
          computeDuplicates();
          buildCategorySidebar();
          renderGallery();

          showToast(`🗑️ Successfully deleted ${{deletedCount}} assets from disk.`, "success");
        }} else {{
          showToast(`Error: ${{data?.error || "Failed to batch delete"}}`, "error");
        }}
      }} catch (err) {{
        console.error("Batch delete failed:", err);
        showToast(`Server error: ${{err.message}}`, "error");
      }} finally {{
        confirmBtn.disabled = false;
        confirmBtn.innerText = "Permanently Delete All (Enter)";
        dialog.close();
      }}
    }}

    function refreshItemIcons(items) {{
      const ts = Date.now();
      items.forEach(it => {{
        const id = it.id || it.item_id;
        const cat = it.category;
        const imgs = document.querySelectorAll(`.item-card[data-item-id="${{id}}"][data-category="${{cat}}"] img`);
        imgs.forEach(img => {{
          try {{
            const url = new URL(img.src, window.location.href);
            url.searchParams.set("t", ts);
            img.src = url.toString();
          }} catch(e) {{
            img.src = `${{img.src.split('?')[0]}}?t=${{ts}}`;
          }}
        }});
        if (activeItem && activeItem.id === id && activeItem.category === cat) {{
          const mImg = document.getElementById("m-icon-img");
          if (mImg) {{
            try {{
              const mUrl = new URL(mImg.src, window.location.href);
              mUrl.searchParams.set("t", ts);
              mImg.src = mUrl.toString();
            }} catch(e) {{
              mImg.src = `${{mImg.src.split('?')[0]}}?t=${{ts}}`;
            }}
          }}
        }}
      }});
    }}

    async function executeBatchRegen() {{
      if (SELECTED_ITEMS.size === 0) return;
      const regenBtn = document.getElementById("batch-regen-btn");
      const itemsToRegen = Array.from(SELECTED_ITEMS.values());

      if (regenBtn) {{
        regenBtn.disabled = true;
        regenBtn.innerText = "Regenerating...";
      }}

      try {{
        const res = await fetch("/api/regen-icons", {{
          method: "POST",
          headers: {{ "Content-Type": "application/json" }},
          body: JSON.stringify({{ items: itemsToRegen }})
        }});
        const data = await res.json();
        if (res.ok && data.success) {{
          const count = data.success_count || itemsToRegen.length;
          showToast(`🔄 Successfully regenerated ${{count}} icon${{count === 1 ? '' : 's'}} (128x128 3D low-poly rules)!`, "success");
          refreshItemIcons(itemsToRegen);
        }} else {{
          showToast(`Error: ${{data?.error || "Failed to regenerate icons"}}`, "error");
        }}
      }} catch (err) {{
        console.error("Batch regen failed:", err);
        showToast(`Server error: ${{err.message}}`, "error");
      }} finally {{
        if (regenBtn) {{
          regenBtn.disabled = false;
          regenBtn.innerHTML = `🔄 Regen Icons (<span id="batch-regen-count">${{SELECTED_ITEMS.size}}</span>)`;
        }}
      }}
    }}

    async function executeRegenAllShown() {{
      const shownCards = document.querySelectorAll(".item-card");
      if (shownCards.length === 0) {{
        showToast("No assets currently visible to regenerate.", "info");
        return;
      }}
      const items = [];
      shownCards.forEach(c => {{
        items.push({{ category: c.dataset.category, id: c.dataset.itemId }});
      }});

      const btn = document.getElementById("regen-all-btn");
      if (btn) {{
        btn.disabled = true;
        btn.innerText = "⏳ Regenerating...";
      }}

      try {{
        const res = await fetch("/api/regen-icons", {{
          method: "POST",
          headers: {{ "Content-Type": "application/json" }},
          body: JSON.stringify({{ items: items }})
        }});
        const data = await res.json();
        if (res.ok && data.success) {{
          const count = data.success_count || items.length;
          showToast(`🔄 Successfully regenerated ${{count}} icon${{count === 1 ? '' : 's'}} following HUD rules!`, "success");
          refreshItemIcons(items);
        }} else {{
          showToast(`Error: ${{data?.error || "Failed to regenerate icons"}}`, "error");
        }}
      }} catch (err) {{
        console.error("Regen all shown failed:", err);
        showToast(`Server error: ${{err.message}}`, "error");
      }} finally {{
        if (btn) {{
          btn.disabled = false;
          btn.innerText = "🔄 Regen Icons";
        }}
      }}
    }}

    async function requestRegenIconFromCard(itemId, category, event) {{
      if (event) event.stopPropagation();
      const card = document.querySelector(`.item-card[data-item-id="${{itemId}}"][data-category="${{category}}"]`);
      const btn = card ? card.querySelector(".card-action-regen") : null;
      if (btn) btn.innerText = "⏳";

      try {{
        const res = await fetch("/api/regen-icon", {{
          method: "POST",
          headers: {{ "Content-Type": "application/json" }},
          body: JSON.stringify({{ category: category, item_id: itemId }})
        }});
        const data = await res.json();
        if (res.ok && data.success) {{
          showToast(`🔄 Icon regenerated for '${{itemId}}' (128x128 3D low-poly)!`, "success");
          refreshItemIcons([{{ id: itemId, category: category }}]);
        }} else {{
          showToast(`Error: ${{data?.error || "Failed to regenerate icon"}}`, "error");
        }}
      }} catch (err) {{
        console.error("Regen icon failed:", err);
        showToast(`Server error: ${{err.message}}`, "error");
      }} finally {{
        if (btn) btn.innerText = "🔄";
      }}
    }}

    async function executeRegenCurrentModal() {{
      if (!activeItem) return;
      const btn = document.getElementById("m-regen-btn");
      if (btn) {{
        btn.disabled = true;
        btn.innerText = "⏳ Regenerating...";
      }}
      try {{
        const res = await fetch("/api/regen-icon", {{
          method: "POST",
          headers: {{ "Content-Type": "application/json" }},
          body: JSON.stringify({{ category: activeItem.category, item_id: activeItem.id }})
        }});
        const data = await res.json();
        if (res.ok && data.success) {{
          showToast(`🔄 Icon regenerated for '${{activeItem.id}}'!`, "success");
          refreshItemIcons([{{ id: activeItem.id, category: activeItem.category }}]);
        }} else {{
          showToast(`Error: ${{data?.error || "Failed to regenerate icon"}}`, "error");
        }}
      }} catch (err) {{
        console.error("Modal regen failed:", err);
        showToast(`Server error: ${{err.message}}`, "error");
      }} finally {{
        if (btn) {{
          btn.disabled = false;
          btn.innerText = "🔄 Regen Icon";
        }}
      }}
    }}

    function showToast(msg, type = "info") {{
      const t = document.getElementById("toast-notify");
      t.innerText = msg;
      t.className = `toast show ${type}`;
      setTimeout(() => {{
        t.className = "toast";
      }}, 4000);
    }}

    let assetToRename = null;

    function requestRenameAssetFromCard(itemId, category, event) {{
      const it = ALL_ITEMS.find(x => x.id === itemId && x.category === category);
      if (!it) return;
      openRenameDialog(it);
    }}

    function openRenameDialog(it) {{
      if (!it) return;
      assetToRename = it;
      const dialog = document.getElementById("rename-dialog");
      const nameInput = document.getElementById("rename-name-input");
      const idInput = document.getElementById("rename-id-input");
      const hint = document.getElementById("rename-path-hint");

      nameInput.value = it.name;
      idInput.value = it.id;
      hint.innerText = `assets/${{it.category}}/${{it.id}}/`;
      delete idInput.dataset.manuallyEdited;

      nameInput.oninput = () => {{
        if (!idInput.dataset.manuallyEdited) {{
          idInput.value = nameInput.value.toLowerCase().trim().replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '');
        }}
      }};
      idInput.oninput = () => {{
        idInput.dataset.manuallyEdited = "true";
      }};

      dialog.showModal();
      nameInput.focus();
      nameInput.select();
    }}

    async function executeRenameAsset() {{
      if (!assetToRename) return;
      const dialog = document.getElementById("rename-dialog");
      const proceedBtn = document.getElementById("rename-proceed-btn");
      const nameInput = document.getElementById("rename-name-input");
      const idInput = document.getElementById("rename-id-input");

      const newName = nameInput.value.trim();
      const newId = idInput.value.trim().toLowerCase();

      if (!newName) {{
        showToast("Display Name cannot be empty.", "warning");
        nameInput.focus();
        return;
      }}

      if (!newId) {{
        showToast("Asset ID cannot be empty.", "warning");
        idInput.focus();
        return;
      }}

      const idRegex = /^[a-z0-9_\\-]+$/;
      if (!idRegex.test(newId)) {{
        showToast("Asset ID must only contain lowercase letters, numbers, hyphens, and underscores.", "warning");
        idInput.focus();
        return;
      }}

      if (newName === assetToRename.name && newId === assetToRename.id) {{
        dialog.close();
        return;
      }}

      proceedBtn.disabled = true;
      proceedBtn.innerText = "Renaming...";

      try {{
        const res = await fetch("/api/rename-asset", {{
          method: "POST",
          headers: {{ "Content-Type": "application/json" }},
          body: JSON.stringify({{
            category: assetToRename.category,
            old_id: assetToRename.id,
            new_id: newId,
            new_name: newName
          }})
        }});

        const text = await res.text();
        let data = null;
        try {{
          data = JSON.parse(text);
        }} catch (parseErr) {{
          if (text.includes("<!DOCTYPE") || text.includes("<html")) {{
            showToast("Server error: please verify Asset Kit server on port 8088 is running.", "error");
            return;
          }}
          throw new Error(text.slice(0, 100) || "Invalid server response");
        }}

        if (res.ok && data.success) {{
          dialog.close();
          showToast(`✏️ Renamed to "${{newName}}" (${{newId}})`, "success");

          const oldId = assetToRename.id;
          const category = assetToRename.category;

          // Update in-memory item
          assetToRename.name = newName;
          assetToRename.id = newId;
          assetToRename.icon = data.icon || `${{category}}/${{newId}}/${{newId}}.png`;

          // If detail modal is open for this item, update its fields
          if (activeItem && activeItem.category === category && (activeItem.id === oldId || activeItem.id === newId)) {{
            activeItem.name = newName;
            activeItem.id = newId;
            activeItem.icon = assetToRename.icon;
            const mName = document.getElementById("m-name");
            if (mName) mName.innerText = newName;
            const mId = document.getElementById("m-id");
            if (mId) mId.innerText = newId;
            const mImg = document.getElementById("m-icon-img");
            if (mImg) mImg.src = assetToRename.icon;
            const mJsonName = document.getElementById("m-json-filename");
            if (mJsonName) mJsonName.innerText = `${{newId}}.json`;
            if (activeItem.raw_manifest) {{
              activeItem.raw_manifest.id = newId;
              activeItem.raw_manifest.name = newName;
              activeItem.raw_manifest.icon = `${{newId}}.png`;
              const rawEl = document.getElementById("m-raw-json");
              if (rawEl) rawEl.textContent = JSON.stringify(activeItem.raw_manifest, null, 2);
            }}
          }}

          // Update DOM Card in gallery
          const card = document.querySelector(`.item-card[data-item-id="${{oldId}}"][data-category="${{category}}"]`);
          if (card) {{
            card.dataset.itemId = newId;
            const nameEl = card.querySelector(".card-name");
            if (nameEl) {{ nameEl.innerText = newName; nameEl.title = newName; }}
            const idEl = card.querySelector(".card-id");
            if (idEl) {{ idEl.innerText = newId; }}
            const imgEl = card.querySelector(".card-thumb-wrap img");
            if (imgEl) {{ imgEl.src = assetToRename.icon; }}
            const delBtn = card.querySelector(".card-action-delete");
            if (delBtn) {{
              delBtn.setAttribute("onclick", `event.stopPropagation(); requestDeleteAssetFromCard('${{newId}}', '${{category}}', event);`);
            }}
            const renBtn = card.querySelector(".card-action-rename");
            if (renBtn) {{
              renBtn.setAttribute("onclick", `event.stopPropagation(); requestRenameAssetFromCard('${{newId}}', '${{category}}', event);`);
            }}
          }}
        }} else {{
          showToast(`Error: ${{data?.error || "Failed to rename asset"}}`, "error");
        }}
      }} catch (err) {{
        console.error("Rename failed:", err);
        showToast(`Server error: ${{err.message}}`, "error");
      }} finally {{
        proceedBtn.disabled = false;
        proceedBtn.innerText = "Save Changes (Enter)";
      }}
    }}

    function requestDeleteAssetFromCard(itemId, category, event) {{
      const it = ALL_ITEMS.find(x => x.id === itemId && x.category === category);
      if (!it) return;

      const isInstant = localStorage.getItem("asset_kit_instant_delete") === "true" || event?.shiftKey;
      if (isInstant) {{
        executeDeleteAsset(it);
      }} else {{
        requestDeleteAsset(it);
      }}
    }}

    function requestDeleteAsset(it) {{
      if (!it) return;
      const confirmDialog = document.getElementById("confirm-delete-dialog");
      document.getElementById("confirm-delete-msg").innerText = `Are you sure you want to permanently delete "${{it.name}}" (${{it.id}}) from disk?`;
      document.getElementById("confirm-delete-path").innerText = `assets/${{it.category}}/${{it.id}}/`;

      const dontAskBox = document.getElementById("dont-ask-delete");
      if (dontAskBox) {{
        dontAskBox.checked = localStorage.getItem("asset_kit_instant_delete") === "true";
        dontAskBox.onchange = (e) => {{
          localStorage.setItem("asset_kit_instant_delete", e.target.checked ? "true" : "false");
        }};
      }}

      const proceedBtn = document.getElementById("confirm-proceed-btn");
      proceedBtn.onclick = () => {{
        if (dontAskBox && dontAskBox.checked) {{
          localStorage.setItem("asset_kit_instant_delete", "true");
        }}
        executeDeleteAsset(it);
      }};

      const cancelBtn = document.getElementById("confirm-cancel-btn");
      cancelBtn.onclick = () => confirmDialog.close();

      confirmDialog.showModal();
      proceedBtn.focus();
    }}

    async function executeDeleteAsset(it) {{
      const confirmDialog = document.getElementById("confirm-delete-dialog");
      const itemModal = document.getElementById("item-modal");
      const proceedBtn = document.getElementById("confirm-proceed-btn");
      
      proceedBtn.disabled = true;
      proceedBtn.innerText = "Deleting...";

      try {{
        const res = await fetch("/api/delete-asset", {{
          method: "POST",
          headers: {{ "Content-Type": "application/json" }},
          body: JSON.stringify({{ category: it.category, item_id: it.id }})
        }});

        const text = await res.text();
        let data = null;
        try {{
          data = JSON.parse(text);
        }} catch (parseErr) {{
          if (text.includes("<!DOCTYPE") || text.includes("<html") || text.includes("Error response")) {{
            showToast("⚠️ Old static server detected! Please close the previous server window and run 'launch_asset_kit.bat' to enable Delete API.", "warning");
            return;
          }}
          throw new Error(text.slice(0, 100) || "Invalid server response");
        }}

        if (res.ok && data.success) {{
          confirmDialog.close();
          itemModal.close();
          cleanup3DViewport();
          
          // Remove from memory
          const idx = ALL_ITEMS.findIndex(x => x.id === it.id && x.category === it.category);
          if (idx !== -1) {{
            ALL_ITEMS.splice(idx, 1);
          }}
          
          // Animate card removal from DOM
          const card = document.querySelector(`.item-card[data-item-id="${{it.id}}"][data-category="${{it.category}}"]`);
          if (card) {{
            card.style.transition = "all 0.3s ease";
            card.style.transform = "scale(0.8)";
            card.style.opacity = "0";
            setTimeout(() => {{
              card.remove();
              computeDuplicates();
              buildCategorySidebar();
              renderGallery();
            }}, 300);
          }} else {{
            computeDuplicates();
            buildCategorySidebar();
            renderGallery();
          }}
          
          showToast(`🗑️ Asset "${{it.id}}" permanently deleted from disk.`, "success");
        }} else {{
          showToast(`Error: ${{data?.error || "Failed to delete asset"}}`, "error");
        }}
      }} catch (err) {{
        console.error("Delete failed:", err);
        if (window.location.protocol === "file:") {{
          showToast("To delete files permanently, launch Asset Kit with 'launch_asset_kit.bat' (runs local server).", "warning");
        }} else {{
          showToast(`Server error: ${{err.message}}`, "error");
        }}
      }} finally {{
        proceedBtn.disabled = false;
        proceedBtn.innerText = "Permanently Delete (Enter)";
        confirmDialog.close();
      }}
    }}

    function showCategoryDropHints(active) {{
      document.querySelectorAll(".cat-btn[data-category]").forEach(btn => {{
        btn.classList.toggle("drag-hint", active);
        if (!active) btn.classList.remove("drag-target-hover");
      }});
    }}

    async function handleCategoryDrop(e, targetCat) {{
      showCategoryDropHints(false);
      try {{
        const raw = e.dataTransfer.getData("application/json");
        if (!raw) return;
        const data = JSON.parse(raw);

        if (data.type === "single") {{
          if (data.category === targetCat) {{
            showToast(`Asset '${{data.id}}' is already in '${{targetCat}}'.`, "info");
            return;
          }}
          await executeMoveAsset(data.id, data.category, targetCat);
        }} else if (data.type === "batch") {{
          const items = Array.from(SELECTED_ITEMS.values());
          if (items.length === 0) {{
            showToast("No assets checked to move.", "warning");
            return;
          }}
          const toMove = items.filter(it => it.category !== targetCat);
          if (toMove.length === 0) {{
            showToast(`All checked assets are already in '${{targetCat}}'.`, "info");
            return;
          }}
          await executeBatchMove(toMove, targetCat);
        }}
      }} catch (err) {{
        console.error("Drop handling error:", err);
      }}
    }}

    async function executeMoveAsset(itemId, category, targetCat) {{
      showToast(`📦 Moving "${{itemId}}" to ${{targetCat}}...`, "info");
      try {{
        const res = await fetch("/api/move-asset", {{
          method: "POST",
          headers: {{ "Content-Type": "application/json" }},
          body: JSON.stringify({{ item_id: itemId, category: category, target_category: targetCat }})
        }});
        const data = await res.json();
        if (res.ok && data.success) {{
          const it = ALL_ITEMS.find(x => x.id === itemId && x.category === category);
          if (it) {{
            it.id = data.new_id;
            it.category = data.target_category;
            it.name = data.new_name || it.name;
            it.icon = data.icon;
          }}
          SELECTED_ITEMS.delete(`${{category}}/${{itemId}}`);
          updateSelectionUI();

          computeDuplicates();
          buildCategorySidebar();
          renderGallery();
          showToast(`📦 Moved "${{itemId}}" to ${{targetCat}} as "${{data.new_id}}"!`, "success");
        }} else {{
          showToast(`Error: ${{data?.error || "Failed to move asset"}}`, "error");
        }}
      }} catch (err) {{
        console.error("Move error:", err);
        showToast(`Server error: ${{err.message}}`, "error");
      }}
    }}

    async function executeBatchMove(itemsToMove, targetCat) {{
      showToast(`📦 Moving ${{itemsToMove.length}} asset${{itemsToMove.length === 1 ? '' : 's'}} to ${{targetCat}}...`, "info");
      try {{
        const res = await fetch("/api/move-batch", {{
          method: "POST",
          headers: {{ "Content-Type": "application/json" }},
          body: JSON.stringify({{ items: itemsToMove, target_category: targetCat }})
        }});
        const data = await res.json();
        if (res.ok && data.success) {{
          (data.moved || []).forEach(m => {{
            const it = ALL_ITEMS.find(x => x.id === m.old_id && x.category === m.old_category);
            if (it) {{
              it.id = m.new_id;
              it.category = m.target_category;
              it.name = m.new_name || it.name;
              it.icon = m.icon;
            }}
            SELECTED_ITEMS.delete(`${{m.old_category}}/${{m.old_id}}`);
          }});
          updateSelectionUI();

          computeDuplicates();
          buildCategorySidebar();
          renderGallery();
          showToast(`📦 Successfully moved ${{data.moved_count || itemsToMove.length}} assets to ${{targetCat}}!`, "success");
        }} else {{
          showToast(`Error: ${{data?.error || "Failed to move assets"}}`, "error");
        }}
      }} catch (err) {{
        console.error("Batch move error:", err);
        showToast(`Server error: ${{err.message}}`, "error");
      }}
    }}

    let activeCategory = "structures";
    let activeFilter = "all";
    let searchQuery = "";
    let activeSubfolder = null;
    let groupBySpecies = true;

    const SPECIES_META = {{
      apple: {{ name: "Apple Tree", icon: "🍎" }},
      birch: {{ name: "Birch Tree", icon: "🪵" }},
      maple: {{ name: "Maple Tree", icon: "🍁" }},
      oak: {{ name: "Oak Tree", icon: "🌳" }},
      pine: {{ name: "Pine Tree", icon: "🌲" }},
      poplar: {{ name: "Poplar Tree", icon: "🌿" }},
      willow: {{ name: "Willow Tree", icon: "🌾" }},
      carrot: {{ name: "Carrot", icon: "🥕" }},
      corn: {{ name: "Sweet Corn", icon: "🌽" }},
      cotton: {{ name: "Cotton Plant", icon: "☁️" }},
      herb: {{ name: "Culinary Herbs", icon: "🌿" }},
      potato: {{ name: "Potato", icon: "🥔" }},
      pumpkin: {{ name: "Pumpkin", icon: "🎃" }},
      strawberry: {{ name: "Strawberry", icon: "🍓" }},
      sunflower: {{ name: "Sunflower", icon: "🌻" }},
      tomato: {{ name: "Tomato", icon: "🍅" }},
      wheat: {{ name: "Wheat Grain", icon: "🌾" }},
      chicken: {{ name: "Chicken Flock", icon: "🐔" }},
      cattle: {{ name: "Cattle Herd", icon: "🐄" }},
      cow: {{ name: "Cattle Herd", icon: "🐄" }},
      goat: {{ name: "Goat Herd", icon: "🐐" }},
      pig: {{ name: "Swine & Pigs", icon: "🐖" }},
      sheep: {{ name: "Sheep Flock", icon: "🐑" }}
    }};

    function getSpeciesForItem(it) {{
      if (it.growth && it.growth.species) {{
        return it.growth.species.toLowerCase();
      }}
      const id = it.id.toLowerCase();
      for (const sp of Object.keys(SPECIES_META)) {{
        if (id === sp || id.startsWith(sp + "_") || id.includes("_" + sp + "_") || id.endsWith("_" + sp)) {{
          return sp;
        }}
      }}
      return null;
    }}

    function openSubfolder(speciesKey, meta, cat) {{
      activeSubfolder = {{
        species: speciesKey,
        name: meta.name || speciesKey.replace("_", " ").toUpperCase(),
        icon: meta.icon || "🌱",
        category: cat
      }};
      renderGallery();
      window.scrollTo({{ top: 0, behavior: "smooth" }});
    }}

    function exitSubfolder() {{
      activeSubfolder = null;
      renderGallery();
    }}
    
    // Three.js instance handles
    let threeScene = null;
    let threeCamera = null;
    let threeRenderer = null;
    let threeControls = null;
    let threeAnimId = null;

    function computeDuplicates() {{
      ALL_ITEMS.forEach(it => {{
        delete it._isDuplicate;
        delete it._duplicateCluster;
      }});

      const PREFIXES = [
        "electricity_", "electric_", "water_", "waste_", "sewage_", "net_", "internet_",
        "animal_fish_", "ingredient_fillet_", "fishing_", "machinery_", "struct_", "tool_",
        "seed_", "crop_", "food_", "ingredient_", "mat_bale_", "mat_pelt_", "mat_wool_", "mat_",
        "tree_", "tile_", "clutter_", "hud_", "building_", "fuel_"
      ];

      function getCleanStem(iId) {{
        let cur = (iId || "").toLowerCase();
        for (const p of PREFIXES) {{
          if (cur.startsWith(p)) {{
            cur = cur.slice(p.length);
            break;
          }}
        }}
        return cur.replace(/^_+|_+$/g, "");
      }}

      for (let i = 0; i < ALL_ITEMS.length; i++) {{
        for (let j = i + 1; j < ALL_ITEMS.length; j++) {{
          const a = ALL_ITEMS[i];
          const b = ALL_ITEMS[j];

          // Skip if both are different growable stages of same species
          const spA = a.growth?.species;
          const spB = b.growth?.species;
          if (spA && spB && spA === spB) continue;

          // Skip fish creature vs fish fillet
          if ((a.id.startsWith("animal_fish_") && b.id.startsWith("ingredient_fillet_")) ||
              (b.id.startsWith("animal_fish_") && a.id.startsWith("ingredient_fillet_"))) {{
            continue;
          }}

          // Skip seed vs crop vs food of different names
          const pLifecycle = ["seed_", "crop_", "food_", "ingredient_"];
          if (pLifecycle.some(p => a.id.startsWith(p)) && pLifecycle.some(p => b.id.startsWith(p))) {{
            if (a.name.toLowerCase() !== b.name.toLowerCase()) continue;
          }}

          // Skip tree vs food fruit (tree_apple vs food_apple)
          if ((a.id.startsWith("tree_") && b.id.startsWith("food_")) || (b.id.startsWith("tree_") && a.id.startsWith("food_"))) {{
            continue;
          }}

          const normA = a.name.toLowerCase().replace(/[^a-z0-9]/g, "");
          const normB = b.name.toLowerCase().replace(/[^a-z0-9]/g, "");
          const stemA = getCleanStem(a.id);
          const stemB = getCleanStem(b.id);

          let isDup = false;
          let clusterName = "";

          if (normA && normA === normB) {{
            isDup = true;
            clusterName = a.name;
          }} else if ((a.id === stemB && !PREFIXES.some(p => a.id.startsWith(p))) ||
                     (b.id === stemA && !PREFIXES.some(p => b.id.startsWith(p)))) {{
            isDup = true;
            clusterName = stemA.replace(/_/g, " ").toUpperCase();
          }} else if (stemA === stemB) {{
            isDup = true;
            clusterName = stemA.replace(/_/g, " ").toUpperCase();
          }}

          if (isDup) {{
            a._isDuplicate = true;
            a._duplicateCluster = a._duplicateCluster || clusterName;
            b._isDuplicate = true;
            b._duplicateCluster = b._duplicateCluster || clusterName;
          }}
        }}
      }}

      const dupCount = ALL_ITEMS.filter(x => x._isDuplicate).length;
      const badge = document.getElementById("stat-dup-count");
      if (badge) badge.innerText = dupCount;
      return dupCount;
    }}

    // Initialize Web App
    document.addEventListener("DOMContentLoaded", () => {{
      computeDuplicates();
      buildCategorySidebar();
      renderGallery();
      setupEventListeners();
    }});

    function buildCategorySidebar() {{
      const sidebar = document.getElementById("cat-sidebar");
      sidebar.innerHTML = "";
      
      // Compute counts per category
      const counts = {{}};
      ALL_ITEMS.forEach(it => {{
        counts[it.category] = (counts[it.category] || 0) + 1;
      }});

      // "All" button
      const allBtn = document.createElement("button");
      allBtn.className = `cat-btn ${{activeCategory === "all" ? "active" : ""}}`;
      allBtn.innerHTML = `
        <span class="cat-label"><span>✨</span> All Categories</span>
        <span class="cat-count">${{ALL_ITEMS.length}}</span>
      `;
      allBtn.onclick = () => selectCategory("all");
      sidebar.appendChild(allBtn);

      // Category buttons
      Object.keys(CATEGORIES_META).forEach(cat => {{
        const meta = CATEGORIES_META[cat];
        const count = counts[cat] || 0;
        const btn = document.createElement("button");
        btn.className = `cat-btn ${{activeCategory === cat ? "active" : ""}}`;
        btn.dataset.category = cat;
        btn.innerHTML = `
          <span class="cat-label"><span>${{meta.icon}}</span> ${{meta.name}}</span>
          <span class="cat-count">${{count}}</span>
        `;
        btn.onclick = () => selectCategory(cat);

        // Drag & drop listeners for category moving
        btn.ondragover = (e) => {{
          e.preventDefault();
          e.dataTransfer.dropEffect = "move";
          btn.classList.add("drag-target-hover");
        }};
        btn.ondragleave = () => {{
          btn.classList.remove("drag-target-hover");
        }};
        btn.ondrop = async (e) => {{
          e.preventDefault();
          btn.classList.remove("drag-target-hover");
          await handleCategoryDrop(e, cat);
        }};

        sidebar.appendChild(btn);
      }});
    }}

    function selectCategory(cat) {{
      activeCategory = cat;
      activeSubfolder = null;
      buildCategorySidebar();
      
      // Update banner
      const bannerTitle = document.getElementById("banner-title");
      const bannerDesc = document.getElementById("banner-desc");
      if (cat === "all") {{
        bannerTitle.innerHTML = "✨ All Homesteader Assets";
        bannerDesc.innerText = "Browsing all in-game items, structures, tools, and simulation resources across all 15 systems.";
      }} else {{
        const meta = CATEGORIES_META[cat] || {{}};
        bannerTitle.innerHTML = `${{meta.icon || ""}} ${{meta.name || cat}}`;
        bannerDesc.innerText = meta.desc || "";
      }}
      
      renderGallery();
    }}

    function renderGallery() {{
      const grid = document.getElementById("item-grid");
      grid.innerHTML = "";
      
      const q = searchQuery.toLowerCase().trim();
      
      const filtered = ALL_ITEMS.filter(it => {{
        if (activeSubfolder) {{
          const sp = getSpeciesForItem(it);
          if (sp !== activeSubfolder.species) return false;
          if (it.category === "food") return false;  // food drops shown in Food category, not in lifecycle groups
          if (it.id.startsWith("seed_")) return false;  // seeds shown in Farming category, not in lifecycle groups
          if (it.category === "ingredients") return false;  // ingredients shown in Ingredients category, not in lifecycle groups
        }} else {{
          if (activeCategory !== "all" && it.category !== activeCategory) return false;
        }}
        
        if (activeFilter === "duplicates" && !it._isDuplicate) return false;
        if (activeFilter === "3d" && !it.has_3d) return false;
        if (activeFilter === "grow" && !it.growth?.is_growable) return false;
        
        if (q) {{
          const matchName = it.name.toLowerCase().includes(q);
          const matchId = it.id.toLowerCase().includes(q);
          const matchDesc = it.description.toLowerCase().includes(q);
          const sp = getSpeciesForItem(it);
          const matchSpecies = sp ? sp.toLowerCase().includes(q) : false;
          if (!matchName && !matchId && !matchDesc && !matchSpecies) return false;
        }}
        
        return true;
      }});

      if (activeFilter === "duplicates") {{
        filtered.sort((a, b) => (a._duplicateCluster || a.name).localeCompare(b._duplicateCluster || b.name));
      }}

      // Update banner
      const bannerTitle = document.getElementById("banner-title");
      const bannerDesc = document.getElementById("banner-desc");
      if (activeFilter === "duplicates") {{
        bannerTitle.innerHTML = `<span style="display: inline-flex; align-items: center; gap: 8px;"><span>⚠️</span> Duplicate Assets</span>`;
        bannerDesc.innerText = `Listing potential duplicate assets across categories, grouped side-by-side. Use the trashcan or batch delete to clean up duplicates.`;
      }} else if (activeSubfolder) {{
        bannerTitle.innerHTML = `
          <div style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
            <button class="btn-subfolder-back" onclick="exitSubfolder()" title="Return to parent category">
              <span>⬅️</span> Back to ${{activeCategory === "all" ? "All Categories" : (CATEGORIES_META[activeCategory]?.name || activeCategory)}}
            </button>
            <span style="display: inline-flex; align-items: center; gap: 8px;">
              <span>${{activeSubfolder.icon}}</span> ${{activeSubfolder.name}} Lifecycle
            </span>
          </div>
        `;
        bannerDesc.innerText = `Viewing all growth stages, variants, and products for ${{activeSubfolder.name}}. Click any stage to inspect 3D models or properties.`;
      }} else {{
        if (activeCategory === "all") {{
          bannerTitle.innerHTML = "✨ All Homesteader Assets";
          bannerDesc.innerText = "Browsing all in-game items, structures, tools, and simulation resources across all 16 systems.";
        }} else {{
          const meta = CATEGORIES_META[activeCategory] || {{}};
          bannerTitle.innerHTML = `${{meta.icon || ""}} ${{meta.name || activeCategory}}`;
          bannerDesc.innerText = meta.desc || "";
        }}
      }}

      document.getElementById("showing-count").innerText = filtered.length;

      if (filtered.length === 0) {{
        grid.innerHTML = `
          <div style="grid-column: 1/-1; text-align: center; padding: 60px 20px; color: var(--text-muted);">
            <div style="font-size: 32px; margin-bottom: 10px;">🔍</div>
            <h3 style="font-size: 16px; color: var(--text-main);">No matching assets found</h3>
            <p style="font-size: 13px; margin-top: 4px;">Try searching for a different keyword or resetting your filter chips.</p>
          </div>
        `;
        return;
      }}

      if (!activeSubfolder && groupBySpecies && activeFilter !== "duplicates") {{
        const speciesGroups = {{}};
        const standaloneItems = [];

        filtered.forEach(it => {{
          const sp = getSpeciesForItem(it);
          if (sp && it.growth?.is_growable && it.category !== "food" && it.category !== "ingredients" && !it.id.startsWith("seed_")) {{
            speciesGroups[sp] = speciesGroups[sp] || [];
            speciesGroups[sp].push(it);
          }} else {{
            standaloneItems.push(it);
          }}
        }});

        // 1. Render Species Folder Cards
        Object.keys(speciesGroups).sort().forEach(sp => {{
          const spItems = speciesGroups[sp];
          const meta = SPECIES_META[sp] || {{ name: sp.replace("_", " ").toUpperCase(), icon: "🌱" }};

          let bestThumb = null;
          for (const item of spItems) {{
            if (item.id.includes("mature") || item.id.includes("large") || item.id.includes("adult")) {{
              bestThumb = item.icon;
              break;
            }}
          }}
          if (!bestThumb && spItems.length > 0) {{
            bestThumb = spItems[spItems.length - 1].icon || spItems[0].icon;
          }}

          const folderCard = document.createElement("div");
          folderCard.className = "folder-card";
          folderCard.title = `Click to open ${{meta.name}} subfolder (${{spItems.length}} stages/variants)`;
          folderCard.onclick = () => openSubfolder(sp, meta, spItems[0].category);

          folderCard.innerHTML = `
            <div class="folder-tab">📂 Subfolder</div>
            <div class="folder-thumb-stack">
              <img src="${{bestThumb || ''}}" alt="${{meta.name}}" loading="lazy" onerror="this.src='data:image/svg+xml,<svg xmlns=\\'http://www.w3.org/2000/svg\\' width=\\'64\\' height=\\'64\\'><rect width=\\'64\\' height=\\'64\\' fill=\\'%2316202e\\'/><text x=\\'32\\' y=\\'36\\' font-size=\\'24\\' text-anchor=\\'middle\\' fill=\\'%2364748b\\'>📦</text></svg>'">
              <span class="folder-count-badge">🌱 ${{spItems.length}} stages</span>
            </div>
            <div class="folder-name" title="${{meta.name}}">${{meta.icon}} ${{meta.name}}</div>
            <div class="folder-meta">
              <span>${{spItems[0].category.toUpperCase()}}</span>
              <span>•</span>
              <span>Lifecycle Group</span>
            </div>
            <div class="folder-action-cue">
              <span>Open Subfolder</span> <span>➔</span>
            </div>
          `;
          grid.appendChild(folderCard);
        }});

        // 2. Render remaining standalone items
        standaloneItems.forEach(it => renderItemCardDOM(it, grid));
      }} else {{
        filtered.forEach(it => renderItemCardDOM(it, grid));
      }}
    }}

    function renderItemCardDOM(it, grid) {{
      const card = document.createElement("div");
      card.className = "item-card";
      card.dataset.itemId = it.id;
      card.dataset.category = it.category;
      card.draggable = true;

      card.ondragstart = (e) => {{
        e.stopPropagation();
        e.dataTransfer.setData("application/json", JSON.stringify({{
          type: "single",
          id: it.id,
          category: it.category,
          name: it.name
        }}));
        e.dataTransfer.effectAllowed = "move";
        card.classList.add("dragging");
        showCategoryDropHints(true);
      }};

      card.ondragend = () => {{
        card.classList.remove("dragging");
        showCategoryDropHints(false);
      }};

      const key = `${{it.category}}/${{it.id}}`;
      const isChecked = SELECTED_ITEMS.has(key);
      if (isChecked) card.classList.add("selected");

      card.onclick = (e) => {{
        if (e.ctrlKey || e.metaKey) {{
          e.preventDefault();
          toggleItemSelection(it.id, it.category, e);
        }} else {{
          openItemModal(it);
        }}
      }};
      
      const iconSrc = it.icon || "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' width='64' height='64' fill='%23334863'><rect width='64' height='64' rx='8'/><text x='32' y='36' font-size='20' text-anchor='middle' fill='%2364748b'>📦</text></svg>";
      
      const badge3D = it.has_3d ? `<span class="badge-3d">${{it.model_format?.toUpperCase() || '3D'}}</span>` : "";
      const badgeGrow = it.growth?.is_growable ? `<span class="badge-grow">🌱 STAGE ${{it.growth.current_stage?.stage || 1}}</span>` : "";
      const badgeDup = it._isDuplicate ? `<span class="badge-dup" style="position: absolute; bottom: 8px; right: 8px; background: rgba(245, 158, 11, 0.25); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.5); font-size: 10px; font-weight: 700; padding: 2px 6px; border-radius: 4px; pointer-events: none; z-index: 2;">⚠️ DUP</span>` : "";
      
      card.innerHTML = `
        <div class="card-thumb-wrap">
          <button class="card-select-btn ${{isChecked ? 'checked' : ''}}" title="${{isChecked ? 'Uncheck asset' : 'Check to delete'}}" onclick="event.stopPropagation(); toggleItemSelection('${{it.id}}', '${{it.category}}', event);">${{isChecked ? '✓' : ''}}</button>
          <img src="${{iconSrc}}" alt="${{it.name}}" loading="lazy" onerror="this.src='data:image/svg+xml,<svg xmlns=\\'http://www.w3.org/2000/svg\\' width=\\'64\\' height=\\'64\\'><rect width=\\'64\\' height=\\'64\\' fill=\\'%2316202e\\'/><text x=\\'32\\' y=\\'36\\' font-size=\\'24\\' text-anchor=\\'middle\\' fill=\\'%2364748b\\'>📦</text></svg>'">
          ${{badge3D}}
          ${{badgeGrow}}
          ${{badgeDup}}
          <div class="card-quick-actions">
            <button class="card-action-btn card-action-regen" title="Regenerate Icon (HUD Rules)" onclick="event.stopPropagation(); requestRegenIconFromCard('${{it.id}}', '${{it.category}}', event);">🔄</button>
            <button class="card-action-btn card-action-rename" title="Rename Asset" onclick="event.stopPropagation(); requestRenameAssetFromCard('${{it.id}}', '${{it.category}}', event);">✏️</button>
            <button class="card-action-btn card-action-delete" title="Permanently Delete (Click to delete, Shift+click for instant delete)" onclick="event.stopPropagation(); requestDeleteAssetFromCard('${{it.id}}', '${{it.category}}', event);">🗑️</button>
          </div>
        </div>
        <div class="card-name" title="${{it.name}}">${{it.name}}</div>
        <div class="card-id">${{it.id}}</div>
        ${{it._isDuplicate ? `<div style="font-size: 10px; font-weight: 600; color: #f59e0b; margin-top: 3px; font-family: 'JetBrains Mono', monospace; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="Category: ${{it.category}} | Group: ${{it._duplicateCluster || it.name}}">📁 ${{it.category.toUpperCase()}} • ${{it._duplicateCluster || it.name}}</div>` : ''}}
      `;
      grid.appendChild(card);
    }}

    function setupEventListeners() {{
      const searchInput = document.getElementById("search-input");
      searchInput.addEventListener("input", (e) => {{
        searchQuery = e.target.value;
        renderGallery();
      }});

      // Keyboard shortcuts
      window.addEventListener("keydown", (e) => {{
        const itemModal = document.getElementById("item-modal");
        const confirmDialog = document.getElementById("confirm-delete-dialog");
        const renameDialog = document.getElementById("rename-dialog");
        const batchDialog = document.getElementById("batch-delete-dialog");

        // F2 key triggers rename of open asset
        if (e.key === "F2" && itemModal.open && !confirmDialog.open && !renameDialog.open && (!batchDialog || !batchDialog.open)) {{
          e.preventDefault();
          openRenameDialog(activeItem);
          return;
        }}

        // Enter key inside rename dialog confirms rename
        if (e.key === "Enter" && renameDialog.open) {{
          e.preventDefault();
          executeRenameAsset();
          return;
        }}

        // Enter key inside batch delete dialog confirms batch delete
        if (e.key === "Enter" && batchDialog && batchDialog.open) {{
          e.preventDefault();
          executeBatchDelete();
          return;
        }}

        // Delete key triggers permanent deletion of open asset
        if ((e.key === "Delete" || e.key === "Del") && itemModal.open && !confirmDialog.open && !renameDialog.open && (!batchDialog || !batchDialog.open)) {{
          if (document.activeElement.tagName !== "INPUT" && document.activeElement.tagName !== "TEXTAREA") {{
            e.preventDefault();
            requestDeleteAsset(activeItem);
            return;
          }}
        }}

        // Enter key inside confirm dialog confirms delete
        if (e.key === "Enter" && confirmDialog.open) {{
          e.preventDefault();
          document.getElementById("confirm-proceed-btn").click();
          return;
        }}

        // Escape clears selection if floating bar is visible and no dialogs are open
        if (e.key === "Escape" && !itemModal.open && !confirmDialog.open && !renameDialog.open && (!batchDialog || !batchDialog.open)) {{
          if (SELECTED_ITEMS.size > 0) {{
            clearSelection();
          }}
        }}

        if (e.key === "/" && document.activeElement !== searchInput) {{
          e.preventDefault();
          searchInput.focus();
        }}
      }});

      // Filter chips
      const chips = [
        {{ id: "chip-all", filter: "all" }},
        {{ id: "chip-duplicates", filter: "duplicates" }},
        {{ id: "chip-3d", filter: "3d" }},
        {{ id: "chip-grow", filter: "grow" }}
      ];
      chips.forEach(c => {{
        const el = document.getElementById(c.id);
        if (!el) return;
        el.onclick = () => {{
          chips.forEach(x => {{
            const chipEl = document.getElementById(x.id);
            if (chipEl) chipEl.classList.remove("active");
          }});
          el.classList.add("active");
          activeFilter = c.filter;
          if (c.filter === "duplicates") {{
            activeCategory = "all";
            buildCategorySidebar();
          }}
          renderGallery();
        }};
      }});

      // Close modal button
      const modal = document.getElementById("item-modal");
      document.getElementById("m-close-btn").onclick = () => modal.close();
      modal.addEventListener("close", () => cleanup3DViewport());

      // Rename dialog action buttons
      const renameProceed = document.getElementById("rename-proceed-btn");
      if (renameProceed) renameProceed.onclick = () => executeRenameAsset();
      const renameCancel = document.getElementById("rename-cancel-btn");
      if (renameCancel) renameCancel.onclick = () => document.getElementById("rename-dialog").close();

      // Batch Delete & Regen Actions
      const batchRegenBtn = document.getElementById("batch-regen-btn");
      if (batchRegenBtn) batchRegenBtn.onclick = () => executeBatchRegen();

      const batchDeleteBtn = document.getElementById("batch-delete-btn");
      if (batchDeleteBtn) batchDeleteBtn.onclick = () => openBatchDeleteDialog();

      const batchClearBtn = document.getElementById("batch-clear-btn");
      if (batchClearBtn) batchClearBtn.onclick = () => clearSelection();

      const batchConfirmBtn = document.getElementById("batch-confirm-btn");
      if (batchConfirmBtn) batchConfirmBtn.onclick = () => executeBatchDelete();

      const batchCancelBtn = document.getElementById("batch-cancel-btn");
      if (batchCancelBtn) batchCancelBtn.onclick = () => document.getElementById("batch-delete-dialog").close();

      // Batch Move Drag & Click Actions
      const batchMoveBtn = document.getElementById("batch-move-btn");
      if (batchMoveBtn) {{
        batchMoveBtn.ondragstart = (e) => {{
          if (SELECTED_ITEMS.size === 0) {{
            e.preventDefault();
            return;
          }}
          e.dataTransfer.setData("application/json", JSON.stringify({{ type: "batch" }}));
          e.dataTransfer.effectAllowed = "move";
          showCategoryDropHints(true);
        }};
        batchMoveBtn.ondragend = () => {{
          showCategoryDropHints(false);
        }};
        batchMoveBtn.onclick = () => {{
          showToast("💡 Tip: Drag this 'Move All' button onto any category on the left sidebar to move all checked assets!", "info");
        }};
      }}

      const selectAllBtn = document.getElementById("select-all-btn");
      if (selectAllBtn) selectAllBtn.onclick = () => toggleSelectAllShown();

      const regenAllBtn = document.getElementById("regen-all-btn");
      if (regenAllBtn) regenAllBtn.onclick = () => executeRegenAllShown();

      const groupSpeciesBtn = document.getElementById("btn-group-species");
      if (groupSpeciesBtn) {{
        groupSpeciesBtn.onclick = () => {{
          groupBySpecies = !groupBySpecies;
          activeSubfolder = null;
          groupSpeciesBtn.classList.toggle("active", groupBySpecies);
          groupSpeciesBtn.innerText = groupBySpecies ? "📂 Group Species: ON" : "📋 Flat View: ON";
          groupSpeciesBtn.style.color = groupBySpecies ? "#38bdf8" : "#94a3b8";
          renderGallery();
        }};
      }}
      
      // Copy JSON button
      document.getElementById("copy-json-btn").onclick = (e) => {{
        e.stopPropagation();
        const jsonText = document.getElementById("m-raw-json").innerText;
        navigator.clipboard.writeText(jsonText).then(() => {{
          const btn = document.getElementById("copy-json-btn");
          btn.innerText = "✓ Copied!";
          setTimeout(() => btn.innerText = "Copy JSON", 1800);
        }});
      }};
    }}

    /* Open & Populate Item Modal */
    function openItemModal(it) {{
      activeItem = it;
      const delBtn = document.getElementById("m-delete-btn");
      if (delBtn) {{
        delBtn.onclick = () => requestDeleteAsset(it);
      }}
      const renBtn = document.getElementById("m-rename-btn");
      if (renBtn) {{
        renBtn.onclick = () => openRenameDialog(it);
      }}
      const regBtn = document.getElementById("m-regen-btn");
      if (regBtn) {{
        regBtn.onclick = () => executeRegenCurrentModal();
      }}
      const modal = document.getElementById("item-modal");
      
      // Header
      const iconSrc = it.icon || "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' width='64' height='64'><rect width='64' height='64' fill='%2316202e'/><text x='32' y='36' font-size='24' text-anchor='middle' fill='%2364748b'>📦</text></svg>";
      document.getElementById("m-icon-img").src = iconSrc;
      document.getElementById("m-name").innerText = it.name;
      document.getElementById("m-id").innerText = it.id;
      document.getElementById("m-cat").innerText = it.category.toUpperCase();
      document.getElementById("m-desc").innerText = it.description || "No description provided.";
      
      // Properties
      const p = it.properties || {{}};
      document.getElementById("m-weight").innerText = p.weight_kg !== undefined && p.weight_kg !== null ? `${{p.weight_kg}} kg` : "—";
      document.getElementById("m-stack").innerText = p.max_stack_size || "1";
      document.getElementById("m-value").innerText = p.base_value !== undefined && p.base_value !== null ? `$${{Number(p.base_value).toFixed(2)}}` : "—";
      document.getElementById("m-consumable").innerText = p.is_consumable ? "Yes (Consumable)" : "No (Permanent)";
      document.getElementById("m-footprint").innerText = p.footprint || "—";
      
      const formatSet = new Set(it.models.map(m => m.format.toUpperCase()));
      document.getElementById("m-formats-summary").innerText = formatSet.size > 0 ? Array.from(formatSet).join(", ") : "None";
      
      // Dimensions
      const d = it.dimensions || {{}};
      const dCm = d.dimensions_cm || {{}};
      const dM = d.dimensions_m || {{}};
      if (dCm.x || dM.x) {{
        document.getElementById("sec-dimensions").style.display = "block";
        document.getElementById("m-dim-x").innerText = dM.x ? `${{dM.x}} m (${{dCm.x}} cm)` : `${{dCm.x}} cm`;
        document.getElementById("m-dim-y").innerText = dM.y ? `${{dM.y}} m (${{dCm.y}} cm)` : `${{dCm.y}} cm`;
        document.getElementById("m-dim-z").innerText = dM.z ? `${{dM.z}} m (${{dCm.z}} cm)` : `${{dCm.z}} cm`;
        document.getElementById("m-faces").innerText = d.faces ? Number(d.faces).toLocaleString() : "—";
      }} else {{
        document.getElementById("sec-dimensions").style.display = "none";
      }}

      // Utilities
      const u = it.utilities || {{}};
      const utilBox = document.getElementById("m-util-container");
      utilBox.innerHTML = "";
      const utilKeys = ["electricity", "water", "sewage", "battery", "internet"];
      let hasAnyUtil = false;
      utilKeys.forEach(k => {{
        const uData = u[k];
        if (uData) {{
          hasAnyUtil = true;
          const row = document.createElement("div");
          row.className = "util-row";
          const label = k.charAt(0).toUpperCase() + k.slice(1);
          const val = typeof uData === "object" ? (uData.metric || uData.details || JSON.stringify(uData)) : uData;
          row.innerHTML = `<span class="util-name">${{label}}</span><span class="util-val">${{val}}</span>`;
          utilBox.appendChild(row);
        }}
      }});
      document.getElementById("sec-utilities").style.display = hasAnyUtil ? "block" : "none";

      // Growth Lifecycle
      const g = it.growth || {{}};
      const growthSec = document.getElementById("sec-growth");
      if (g.is_growable && Array.isArray(g.stages) && g.stages.length > 0) {{
        growthSec.style.display = "block";
        const stepper = document.getElementById("m-growth-stepper");
        stepper.innerHTML = "";
        g.stages.forEach(st => {{
          const isCur = g.current_stage?.stage === st.stage;
          const stepDiv = document.createElement("div");
          stepDiv.className = `growth-step ${{isCur ? "active" : ""}}`;
          stepDiv.innerHTML = `
            <div class="step-num">STAGE ${{st.stage}}</div>
            <div class="step-name">${{st.name}}</div>
            <div class="step-age">${{st.age_min}} - ${{st.age_max}}d</div>
          `;
          stepper.appendChild(stepDiv);
        }});
      }} else {{
        growthSec.style.display = "none";
      }}

      // Raw JSON
      document.getElementById("m-json-filename").innerText = `${{it.id}}.json`;
      document.getElementById("m-raw-json").innerText = JSON.stringify(it.manifest, null, 2);

      // 3D Model Viewport Setup
      setup3DViewport(it);

      modal.showModal();
    }}

    /* Setup 3D Viewport in Modal */
    function setup3DViewport(it) {{
      cleanup3DViewport();
      const wrap = document.getElementById("viewport-wrap");
      const badge = document.getElementById("m-model-badge");
      
      if (!it.has_3d || !it.best_model) {{
        badge.innerText = "No 3D Model (2D Item)";
        badge.style.color = "var(--text-muted)";
        wrap.innerHTML = `
          <div style="text-align: center; color: var(--text-muted); padding: 40px 20px;">
            <img src="${{it.icon || ''}}" style="max-width: 140px; max-height: 140px; margin-bottom: 12px; filter: drop-shadow(0 8px 16px rgba(0,0,0,0.5));">
            <div style="font-size: 13px; font-weight: 600; color: var(--text-sub);">2D Interface Asset</div>
            <div style="font-size: 11px; margin-top: 4px;">No 3D mesh is assigned to this inventory item.</div>
          </div>
        `;
        return;
      }}

      badge.innerText = `Active Model: ${{it.model_format?.toUpperCase()}} (${{it.models.length}} formats)`;
      badge.style.color = "var(--accent-sky)";

      if (it.model_format === "fbx") {{
        // Use Three.js FBXLoader (100% Native FBX Pipeline)
        wrap.innerHTML = `<div id="three-canvas-container" style="width: 100%; height: 100%;"></div>`;
        initThreeFBX(it.best_model, document.getElementById("three-canvas-container"));
      }} else if (it.model_format === "glb") {{
        // Use Google's <model-viewer>
        wrap.innerHTML = `
          <model-viewer
            id="active-model-viewer"
            src="${{it.best_model}}"
            alt="${{it.name}} 3D Model"
            camera-controls
            auto-rotate
            rotation-per-second="20deg"
            shadow-intensity="1.2"
            exposure="1.05"
            interaction-prompt="none"
            ar>
          </model-viewer>
        `;
        const mv = document.getElementById("active-model-viewer");
        mv.addEventListener("error", () => {{
          if (window.location.protocol === "file:") {{
            wrap.innerHTML = `
              <div style="text-align: center; color: var(--text-muted); padding: 36px 20px;">
                <div style="font-size: 36px; margin-bottom: 8px;">🛡️</div>
                <div style="font-size: 14px; font-weight: 700; color: var(--accent-gold);">Browser Security Policy</div>
                <div style="font-size: 12px; max-width: 320px; margin: 8px auto; line-height: 1.5; color: var(--text-sub);">
                  Browsers block WebGL mesh loading when opened directly from disk (<code>file://</code>).
                  <br><br>
                  Run <b>launch_asset_kit.bat</b> in this folder or start a local server:
                  <div style="background: rgba(0,0,0,0.5); border: 1px solid var(--border-subtle); padding: 6px 10px; border-radius: 6px; margin-top: 8px; font-family: monospace; color: var(--accent-sky);">
                    python -m http.server
                  </div>
                </div>
              </div>
            `;
          }}
        }});
      }} else if (it.model_format === "obj") {{
        // Use Three.js OBJLoader
        wrap.innerHTML = `<div id="three-canvas-container" style="width: 100%; height: 100%;"></div>`;
        initThreeOBJ(it.best_model, document.getElementById("three-canvas-container"));
      }}
    }}

    function initThreeFBX(fbxUrl, container) {{
      const width = container.clientWidth || 420;
      const height = container.clientHeight || 420;

      threeScene = new THREE.Scene();
      threeScene.background = new THREE.Color(0x080c12);

      threeCamera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
      threeCamera.position.set(2, 2.5, 3.5);

      threeRenderer = new THREE.WebGLRenderer({{ antialias: true }});
      threeRenderer.setSize(width, height);
      threeRenderer.setPixelRatio(window.devicePixelRatio);
      container.appendChild(threeRenderer.domElement);

      threeControls = new THREE.OrbitControls(threeCamera, threeRenderer.domElement);
      threeControls.enableDamping = true;
      threeControls.dampingFactor = 0.05;
      threeControls.autoRotate = true;
      threeControls.autoRotateSpeed = 2.0;

      // Lighting
      const ambient = new THREE.AmbientLight(0xffffff, 0.85);
      threeScene.add(ambient);
      const dirLight = new THREE.DirectionalLight(0xffffff, 0.95);
      dirLight.position.set(5, 12, 7.5);
      threeScene.add(dirLight);
      const fillLight = new THREE.DirectionalLight(0x38bdf8, 0.35);
      fillLight.position.set(-5, 0, -5);
      threeScene.add(fillLight);

      // Ground Grid
      const grid = new THREE.GridHelper(6, 12, 0x334863, 0x16202e);
      grid.position.y = 0;
      threeScene.add(grid);

      const loader = new THREE.FBXLoader();
      loader.load(
        fbxUrl,
        (fbx) => {{
          const box = new THREE.Box3().setFromObject(fbx);
          const size = box.getSize(new THREE.Vector3());
          const center = box.getCenter(new THREE.Vector3());
          
          const maxDim = Math.max(size.x, size.y, size.z);
          const scale = 2.2 / (maxDim || 1.0);
          fbx.scale.set(scale, scale, scale);
          
          fbx.position.x = -center.x * scale;
          fbx.position.y = -box.min.y * scale;
          fbx.position.z = -center.z * scale;
          
          threeScene.add(fbx);
        }},
        undefined,
        (err) => {{
          console.error("Failed to load FBX model:", err);
          if (window.location.protocol === "file:") {{
            container.innerHTML = `
              <div style="text-align: center; color: var(--text-muted); padding: 36px 20px;">
                <div style="font-size: 36px; margin-bottom: 8px;">🛡️</div>
                <div style="font-size: 14px; font-weight: 700; color: var(--accent-gold);">Browser Security Policy</div>
                <div style="font-size: 12px; max-width: 320px; margin: 8px auto; line-height: 1.5; color: var(--text-sub);">
                  Browsers block local FBX files when opened directly via <code>file://</code>.
                  <br><br>
                  Run <b>launch_asset_kit.bat</b> in this folder or start a local server:
                  <div style="background: rgba(0,0,0,0.5); border: 1px solid var(--border-subtle); padding: 6px 10px; border-radius: 6px; margin-top: 8px; font-family: monospace; color: var(--accent-sky);">
                    python -m http.server
                  </div>
                </div>
              </div>
            `;
          }}
        }}
      );

      function animate() {{
        threeAnimId = requestAnimationFrame(animate);
        threeControls.update();
        threeRenderer.render(threeScene, threeCamera);
      }}
      animate();
    }}

    function initThreeOBJ(objUrl, container) {{
      const width = container.clientWidth || 420;
      const height = container.clientHeight || 420;

      threeScene = new THREE.Scene();
      threeScene.background = new THREE.Color(0x080c12);

      threeCamera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
      threeCamera.position.set(2, 2.5, 3.5);

      threeRenderer = new THREE.WebGLRenderer({{ antialias: true }});
      threeRenderer.setSize(width, height);
      threeRenderer.setPixelRatio(window.devicePixelRatio);
      container.appendChild(threeRenderer.domElement);

      threeControls = new THREE.OrbitControls(threeCamera, threeRenderer.domElement);
      threeControls.enableDamping = true;
      threeControls.dampingFactor = 0.05;
      threeControls.autoRotate = true;
      threeControls.autoRotateSpeed = 2.0;

      // Lights
      const ambient = new THREE.AmbientLight(0xffffff, 0.7);
      threeScene.add(ambient);
      const dirLight = new THREE.DirectionalLight(0xffffff, 0.9);
      dirLight.position.set(5, 10, 7.5);
      threeScene.add(dirLight);
      const fillLight = new THREE.DirectionalLight(0x38bdf8, 0.3);
      fillLight.position.set(-5, 0, -5);
      threeScene.add(fillLight);

      // Ground Grid
      const grid = new THREE.GridHelper(6, 12, 0x334863, 0x16202e);
      grid.position.y = 0;
      threeScene.add(grid);

      // Load OBJ
      const loader = new THREE.OBJLoader();
      loader.load(
        objUrl,
        (obj) => {{
          // Auto center and scale
          const box = new THREE.Box3().setFromObject(obj);
          const size = box.getSize(new THREE.Vector3());
          const center = box.getCenter(new THREE.Vector3());
          
          const maxDim = Math.max(size.x, size.y, size.z);
          const scale = 2.0 / (maxDim || 1.0);
          obj.scale.set(scale, scale, scale);
          
          // Re-center
          obj.position.x = -center.x * scale;
          obj.position.y = -box.min.y * scale; // Ground base
          obj.position.z = -center.z * scale;
          
          // Apply default nice material if mesh has none
          obj.traverse((child) => {{
            if (child.isMesh) {{
              if (!child.material || child.material.length === 0) {{
                child.material = new THREE.MeshStandardMaterial({{
                  color: 0x10b981,
                  roughness: 0.6,
                  metalness: 0.1,
                  flatShading: true
                }});
              }}
            }}
          }});
          
          threeScene.add(obj);
        }},
        undefined,
        (err) => {{
          console.error("Failed to load OBJ model:", err);
          if (window.location.protocol === "file:") {{
            container.innerHTML = `
              <div style="text-align: center; color: var(--text-muted); padding: 36px 20px;">
                <div style="font-size: 36px; margin-bottom: 8px;">🛡️</div>
                <div style="font-size: 14px; font-weight: 700; color: var(--accent-gold);">Browser Security Policy</div>
                <div style="font-size: 12px; max-width: 320px; margin: 8px auto; line-height: 1.5; color: var(--text-sub);">
                  Browsers block WebGL mesh loading when opened directly from disk (<code>file://</code>).
                  <br><br>
                  Run <b>launch_asset_kit.bat</b> in this folder or start a local server:
                  <div style="background: rgba(0,0,0,0.5); border: 1px solid var(--border-subtle); padding: 6px 10px; border-radius: 6px; margin-top: 8px; font-family: monospace; color: var(--accent-sky);">
                    python -m http.server
                  </div>
                </div>
              </div>
            `;
          }}
        }}
      );

      function animate() {{
        threeAnimId = requestAnimationFrame(animate);
        threeControls.update();
        threeRenderer.render(threeScene, threeCamera);
      }}
      animate();
    }}

    function cleanup3DViewport() {{
      if (threeAnimId) {{
        cancelAnimationFrame(threeAnimId);
        threeAnimId = null;
      }}
      if (threeRenderer) {{
        threeRenderer.dispose();
        threeRenderer = null;
      }}
      threeScene = null;
      threeCamera = null;
      threeControls = null;
      const wrap = document.getElementById("viewport-wrap");
      if (wrap) wrap.innerHTML = "";
    }}
  </script>
</body>
</html>
"""
    return html

def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), EMPTY_BYTES):
            h.update(chunk)
    return h.hexdigest()


def write_output(out_path, html_content, force=False):
    # Write the generated HTML without ever destroying hand-edited work.
    #
    # assets/index.html is a REAL source file that the app reads and that has
    # been hand-edited (its git history contains "smart presets", "autofill",
    # "stage 4 min age"). This script regenerates a different app from the
    # template below, so a bare open(path, "w") silently discarded all of
    # that - which is exactly what happened. Two safeguards now:
    #
    #   1. Each write records the result in a sidecar hash file.
    #   2. If the file on disk no longer matches that record, it has been
    #      hand-edited and we REFUSE to overwrite it.
    #
    # --force overrides the refusal deliberately; there is no accidental path
    # to clobbering someone's work.
    sidecar = out_path + ".generated.sha256"

    if os.path.exists(out_path):
        recorded = None
        if os.path.isfile(sidecar):
            try:
                with open(sidecar, "r", encoding="utf-8") as f:
                    recorded = f.read().strip()
            except OSError:
                recorded = None
        if recorded is None:
            print("REFUSING TO WRITE: %s exists with no generation record." % out_path)
            print("  It was not produced by this script, so it may be hand-edited.")
            print("  Nothing was changed. Use --out <path>, or --force to override.")
            return False
        if _sha256(out_path) != recorded:
            print("REFUSING TO WRITE: %s has local edits." % out_path)
            print("  It was modified by hand since this script last generated it,")
            print("  so overwriting would discard that work. Nothing was changed.")
            print("  Use --out <path>, or --force to override.")
            return False
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(html_content)
    try:
        with open(sidecar, "w", encoding="utf-8") as f:
            f.write(_sha256(out_path))
    except OSError as exc:
        print("warning: could not write %s: %s" % (sidecar, exc))
    return True
if __name__ == "__main__":
    _ap = argparse.ArgumentParser(description="Generate the Asset Kit HTML.")
    _ap.add_argument("--out", help="output path (default: assets/index.html)")
    _ap.add_argument("--force", action="store_true",
                     help="overwrite even if the target has hand edits")
    _ap.add_argument("--dry-run", action="store_true",
                     help="report what would be written, write nothing")
    _args = _ap.parse_args()

    print(f"Collecting asset data across all {len(CATEGORIES)} categories...")
    items = collect_all_items()
    print(f"Collected {len(items)} items.")

    html_content = generate_html(items)
    out_path = (os.path.abspath(_args.out) if _args.out
                else os.path.join(ASSETS_DIR, "index.html"))

    if _args.dry_run:
        print(f"dry run: would write {len(html_content)} bytes to {out_path}")
        sys.exit(0)

    if write_output(out_path, html_content, force=_args.force):
        print(f"Successfully generated Asset Kit at: {out_path} ({len(html_content)} bytes)")
    else:
        sys.exit(1)
