import os
from PIL import Image

hud_root = r"c:\Users\casey\Desktop\Homesteader\HUD"
ue5_root = r"c:\Users\casey\Desktop\Homesteader\Homesteader\Content\Homesteader"
hud_icons_dir = os.path.join(hud_root, "assets", "ground", "icons")
ue5_icons_dir = os.path.join(ue5_root, "UI", "Icons", "Ground")

os.makedirs(hud_icons_dir, exist_ok=True)
os.makedirs(ue5_icons_dir, exist_ok=True)

ground_names = [
    "SM_Tile_Gravel", "SM_Tile_Dirt", "SM_Tile_Road", "SM_Tile_Path",
    "SM_Tile_Grass", "SM_Tile_Tall_grass", "SM_Tile_Farmland",
    "SM_Tile_Trampled_grass", "SM_Tile_Concrete", "SM_Tile_Black_top",
    "SM_Tile_Bricks", "SM_Tile_Mud", "SM_Tile_Swamp", "SM_Tile_Pond",
    "SM_Tile_Deep_water", "SM_Tile_Sand", "SM_Tile_Wood_planks",
    "SM_Tile_Snow", "SM_Tile_Forest_floor", "SM_Tile_Flagstone",
    "SM_Tile_Farmland_Furrows", "SM_Tile_Road_Asphalt", "SM_Tile_WoodPlanks",
    "SM_Clutter_TallGrass", "SM_Clutter_Pebbles", "SM_Clutter_Cattails",
    "SM_Clutter_Branch", "SM_Clutter_DirtClump", "SM_Clutter_GrassTuft"
]

clutter_map = {
    "SM_Clutter_Branch": os.path.join(hud_root, "assets", "items", "clutter_branch.png"),
    "SM_Clutter_Pebbles": os.path.join(hud_root, "assets", "items", "clutter_pebbles.png"),
    "SM_Clutter_DirtClump": os.path.join(hud_root, "assets", "items", "clutter_dirt_clump.png"),
    "SM_Clutter_GrassTuft": os.path.join(hud_root, "assets", "items", "clutter_grass_tuft.png"),
    "SM_Clutter_TallGrass": os.path.join(hud_root, "assets", "foliage", "icons", "SM_Grass_Tall_Wild.png"),
    "SM_Clutter_Cattails": os.path.join(hud_root, "assets", "foliage", "icons", "SM_Flora_Reeds_Cattail.png"),
}

for name in ground_names:
    hud_dest = os.path.join(hud_icons_dir, f"{name}.png")
    ue5_dest = os.path.join(ue5_icons_dir, f"{name}.png")

    if name in clutter_map and os.path.exists(clutter_map[name]):
        img = Image.open(clutter_map[name]).convert("RGBA")
        img = img.resize((128, 128), Image.Resampling.LANCZOS)
        img.save(hud_dest, "PNG")
        img.save(ue5_dest, "PNG")
        print(f"Generated clutter icon: {name}")
        continue

    # Terrain tile texture lookup
    tex_name = name.replace("SM_Tile_", "").lower()
    if tex_name == "road_asphalt":
        tex_name = "road"
    elif tex_name == "woodplanks":
        tex_name = "wood_planks"
    elif tex_name == "farmland_furrows":
        tex_name = "farmland"

    tex_dir = os.path.join(hud_root, "assets", "ground", "textures", tex_name)
    base_color_path = os.path.join(tex_dir, f"T_Ground_{tex_name}_BaseColor.png")

    if os.path.exists(base_color_path):
        tex_img = Image.open(base_color_path).convert("RGBA")
        tex_img = tex_img.resize((104, 104), Image.Resampling.LANCZOS)
        
        # Place within 128x128 canvas with 12px margin
        canvas = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
        canvas.paste(tex_img, (12, 12))
        canvas.save(hud_dest, "PNG")
        canvas.save(ue5_dest, "PNG")
        print(f"Generated terrain icon: {name}")
    else:
        print(f"WARNING: Texture not found for {name} at {base_color_path}")

