#!/usr/bin/env python3
import os
import json

ASSETS_DIR = r"C:\Users\casey\Desktop\Homesteader\assets"
CATEGORIES = [
    "structures", "building", "farming", "ranching", "logging",
    "fishing", "tools", "electricity", "water", "waste",
    "internet", "hud", "ground", "food", "fuel", "materials", "ingredients"
]

category_descriptions = {
    "structures": "Placed world buildings, farmhouses, cabins, barns, silos, sheds, greenhouses, coops, shelters, and towers.",
    "building": "Modular building materials, framing, doors, windows, and hardware supplies.",
    "farming": "Crops, seeds, produce, fertilizers, irrigation, and agricultural machinery.",
    "ranching": "Livestock species, animal feed/hay, butchered meats, hides/pelts, and animal husbandry housing.",
    "logging": "Modular forest trees (large/medium/small), saplings, timber logs, firewood, woodchips, and sap spigots.",
    "fishing": "Whole fish species, precision meat fillets, fishing rods, lures, and tackle.",
    "tools": "Hand tools, power gear, crafting implements, and surveying/measuring equipment.",
    "electricity": "Solar photovoltaic panels, wind turbines, fuel generators, battery banks, and high-voltage wiring.",
    "water": "Aquifer wells, pressure tanks, poly cisterns, rain catchment barrels, and filtration racks.",
    "waste": "Septic infrastructure, compost systems, composting toilets, and organic waste management.",
    "internet": "Starlink satellite dishes, Wi-Fi 6 mesh distribution routers, and weather-rated cabling.",
    "hud": "Player vitals, coins, energy/stamina bars, clock dials, and interface elements.",
    "ground": "Modular terrain grid tiles (1m x 1m), road pavements, and scatter clutter props.",
    "food": "Edible harvested produce, pantry staples, fresh eggs, dairy, and whole foods.",
    "fuel": "Liquid hydrocarbons, compressed gas tanks, bulk fuel storage, firewood cords, and transfer equipment.",
    "materials": "Raw construction materials, timber log piles, aggregate bulk piles, textiles, hides, and foundational crafting resources.",
    "ingredients": "Raw cooking and crafting inputs: butchered meats, fish fillets, eggs, dairy, harvested grains, and crop-derived ingredients."
}

model_exts = {".obj", ".glb", ".fbx", ".gltf", ".stl", ".usdz"}

def main():
    catalog_data = {}
    total_items = 0

    for cat in CATEGORIES:
        cat_path = os.path.join(ASSETS_DIR, cat)
        catalog_data[cat] = []
        if not os.path.isdir(cat_path):
            continue
        for item_id in sorted(os.listdir(cat_path)):
            item_path = os.path.join(cat_path, item_id)
            if not os.path.isdir(item_path):
                continue
            
            json_path = os.path.join(item_path, f"{item_id}.json")
            manifest = {}
            if os.path.exists(json_path):
                try:
                    with open(json_path, "r", encoding="utf-8") as jf:
                        manifest = json.load(jf)
                except Exception:
                    pass
                    
            files = os.listdir(item_path)
            has_model = any(os.path.splitext(f)[1].lower() in model_exts for f in files)
            is_growable = manifest.get("growth", {}).get("is_growable", False)
            display_name = manifest.get("name", item_id.replace("_", " ").title())
            
            catalog_data[cat].append({
                "id": item_id,
                "name": display_name,
                "has_model": has_model,
                "is_growable": is_growable
            })
            total_items += 1

    lines = [
        "# Homesteader Unified Assets Catalog\n",
        "Welcome to the master asset repository for the **Homesteader** project. This directory organizes every in-game item, building, structure, clutter object, tool, utility, and resource across the 13 core gameplay systems.\n",
        "Each item subfolder contains:",
        "- 🖼️ **`<item_id>.png`**: 128×128 32-bit transparent RGBA render (12px safe margin, 3D faceted style).",
        "- 📦 **3D Model Files**: `.obj`, `.mtl`, `.fbx`, or `.glb` files with flat-shaded low-poly geometry.",
        "- ⚙️ **`<item_id>.json`**: Machine-readable plugin manifest with metrics, utilities, dimensions, and 4-stage growth lifecycle.",
        "- 📄 **`README.md`**: Human-readable overview and quick reference for the asset.\n",
        "### Developer & AI Agent Specifications\n",
        "- 🌐 **[`API_REFERENCE.md`](API_REFERENCE.md)**: Authoritative REST API specification for `server.py` (queue pipeline, mutations, schemas, tags).",
        "- 📋 **[`FREE_PIPELINE_GUIDE.md`](FREE_PIPELINE_GUIDE.md)**: 100% Free generation pipeline guide (FLUX, Hunyuan3D-2, Unity target).\n",
        "## Category Taxonomy Summary\n",
        f"Total Indexed Items: **{total_items}**\n",
        "| Category | Items Count | Description |",
        "| :--- | :---: | :--- |"
    ]

    for cat in CATEGORIES:
        cnt = len(catalog_data[cat])
        desc = category_descriptions.get(cat, "")
        lines.append(f"| [**{cat.capitalize()}**]({cat}/) | {cnt} items | {desc} |")

    lines.append("\n### Shared System & World Asset Directories\n")
    lines.append("| System Directory | Contents | Specification |")
    lines.append("| :--- | :--- | :--- |")
    lines.append("| [**Ground**](ground/) | 20 Seamless PBR Texture Sets (BaseColor, Normal, ORM), 16 Landscape Blend Masks, 20 Modular Grid Tiles (`SM_Tile_*`), and 10 Scatter Clutter Meshes. | [`ground/README.md`](ground/README.md) |")
    lines.append("| [**Textures**](textures/) | Master 3D low-poly color palette atlas (`T_Homesteader_Palette.png`) and entity skeletal mesh base colors (`animals/`). | [`textures/README.md`](textures/README.md) |")
    lines.append("\n---\n")

    for cat in CATEGORIES:
        entries = catalog_data[cat]
        lines.append(f"### 📂 [{cat.capitalize()}]({cat}/) ({len(entries)} items)\n")
        lines.append("| Item ID | Display Name | 3D Model | Growth | Plugin Manifest |")
        lines.append("| :--- | :--- | :---: | :---: | :--- |")
        for e in entries:
            m_badge = "✅ Yes" if e["has_model"] else "—"
            g_badge = "🌱 4-Stage" if e["is_growable"] else "—"
            i_id = e["id"]
            d_name = e["name"]
            lines.append(f"| `{i_id}` | {d_name} | {m_badge} | {g_badge} | [{i_id}.json]({cat}/{i_id}/{i_id}.json) |")
        lines.append("")

    readme_path = os.path.join(ASSETS_DIR, "README.md")
    with open(readme_path, "w", encoding="utf-8") as rf:
        rf.write("\n".join(lines))

    print(f"Successfully updated {readme_path} with {total_items} items.")

if __name__ == "__main__":
    main()

