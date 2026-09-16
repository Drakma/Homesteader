import os
import shutil

hud_root = r"c:\Users\casey\Desktop\Homesteader\HUD"
ue5_root = r"c:\Users\casey\Desktop\Homesteader\Homesteader\Content\Homesteader"
test_dir = os.path.join(hud_root, "scratch", "test_extracted")

hud_items_dir = os.path.join(hud_root, "assets", "items")
ue5_icons_dir = os.path.join(ue5_root, "UI", "Icons")

files = [f for f in os.listdir(test_dir) if f.endswith(".png")]
print(f"Deploying {len(files)} authentic 3D icons...")

for f in files:
    src = os.path.join(test_dir, f)
    dst_hud = os.path.join(hud_items_dir, f)
    dst_ue5 = os.path.join(ue5_icons_dir, f)
    
    shutil.copy2(src, dst_hud)
    shutil.copy2(src, dst_ue5)
    print(f"  [DEPLOY] {f} -> HUD & UE5")

# Also copy to specific model icon preview locations if needed:
model_icon_mappings = [
    ("tree_tap.png", "assets/tools/icons/SM_Tool_TreeTap.png", "UI/Icons/tools/SM_Tool_TreeTap.png"),
    ("mat_leather.png", "assets/building/icons/SM_Mat_Leather_Roll.png", "UI/Icons/building/SM_Mat_Leather_Roll.png"),
    ("clutter_branch.png", "assets/ground/icons/SM_Clutter_Branch.png", "UI/Icons/ground/SM_Clutter_Branch.png"),
    ("clutter_dirt_clump.png", "assets/ground/icons/SM_Clutter_DirtClump.png", "UI/Icons/ground/SM_Clutter_DirtClump.png"),
    ("clutter_grass_tuft.png", "assets/ground/icons/SM_Clutter_GrassTuft.png", "UI/Icons/ground/SM_Clutter_GrassTuft.png"),
    ("fish_catfish.png", "assets/fishing/icons/SM_Item_Fish_Catfish.png", "UI/Icons/fishing/SM_Item_Fish_Catfish.png"),
    ("fish_walleye.png", "assets/fishing/icons/SM_Item_Fish_Walleye.png", "UI/Icons/fishing/SM_Item_Fish_Walleye.png"),
    ("fish_crappie.png", "assets/fishing/icons/SM_Item_Fish_Crappie.png", "UI/Icons/fishing/SM_Item_Fish_Crappie.png"),
    ("fillet_bass.png", "assets/fishing/icons/SM_Item_FishFillet_Bass.png", "UI/Icons/fishing/SM_Item_FishFillet_Bass.png"),
    ("fillet_salmon.png", "assets/fishing/icons/SM_Item_FishFillet_Salmon.png", "UI/Icons/fishing/SM_Item_FishFillet_Salmon.png"),
    ("fillet_trout.png", "assets/fishing/icons/SM_Item_FishFillet_Trout.png", "UI/Icons/fishing/SM_Item_FishFillet_Trout.png"),
    ("fillet_catfish.png", "assets/fishing/icons/SM_Item_FishFillet_Catfish.png", "UI/Icons/fishing/SM_Item_FishFillet_Catfish.png"),
    ("fillet_walleye.png", "assets/fishing/icons/SM_Item_FishFillet_Walleye.png", "UI/Icons/fishing/SM_Item_FishFillet_Walleye.png"),
    ("fillet_crappie.png", "assets/fishing/icons/SM_Item_FishFillet_Crappie.png", "UI/Icons/fishing/SM_Item_FishFillet_Crappie.png"),
]

for src_name, hud_sub, ue5_sub in model_icon_mappings:
    src = os.path.join(test_dir, src_name)
    dst_h = os.path.join(hud_root, hud_sub)
    dst_u = os.path.join(ue5_root, ue5_sub)
    os.makedirs(os.path.dirname(dst_h), exist_ok=True)
    os.makedirs(os.path.dirname(dst_u), exist_ok=True)
    shutil.copy2(src, dst_h)
    shutil.copy2(src, dst_u)
    print(f"  [SYNC PREVIEW] {src_name} -> {hud_sub}")

print("\nDeployment completed successfully!")

