import os
from PIL import Image

RENDERS_DIR = r"C:\Users\casey\Desktop\Homesteader\HUD\scratch\renders_animals"
HUD_ANIMALS_DIR = r"C:\Users\casey\Desktop\Homesteader\HUD\assets\ranching\animals"
HUD_ITEMS_DIR = r"C:\Users\casey\Desktop\Homesteader\HUD\assets\items"
UNREAL_ICONS_DIR = r"C:\Users\casey\Desktop\Homesteader\Homesteader\Content\Homesteader\UI\Icons"
UNREAL_RANCH_ICONS_DIR = r"C:\Users\casey\Desktop\Homesteader\Homesteader\Content\Homesteader\UI\Icons\ranching\animals"

target_dirs = [HUD_ANIMALS_DIR, HUD_ITEMS_DIR, UNREAL_ICONS_DIR, UNREAL_RANCH_ICONS_DIR]
for d in target_dirs:
    os.makedirs(d, exist_ok=True)

# Mapping render file prefixes to canonical icon names and aliases
ICON_MAPPING = {
    # Cattle
    "SKM_Animal_Cow_Holstein": ["livestock_cow_holstein", "cow_holstein"],
    "SKM_Animal_Cow_Jersey": ["livestock_cow_jersey", "cow_jersey"],
    "SKM_Animal_Cow_Highland": ["livestock_cow_highland", "cow_highland"],
    "SKM_Animal_Cow_Calf_Holstein": ["baby_calf_spotted", "baby_calf_holstein"],
    "SKM_Animal_Cow_Calf_Jersey": ["baby_calf_jersey"],
    "SKM_Animal_Cow_Calf_Highland": ["baby_calf_highland"],
    "SKM_Animal_Cow_Calf_Chestnut": ["baby_calf", "baby_calf_chestnut"],
    
    # Pigs
    "SKM_Animal_Pig_Pink": ["livestock_pig_pink", "pig_pink"],
    "SKM_Animal_Pig_Hampshire": ["livestock_pig_hampshire", "pig_hampshire"],
    "SKM_Animal_Pig_Duroc": ["livestock_pig_duroc", "pig_duroc"],
    "SKM_Animal_Pig_Piglet_Pink": ["baby_piglet", "baby_piglet_pink"],
    "SKM_Animal_Pig_Piglet_Hampshire": ["baby_piglet_hampshire"],
    "SKM_Animal_Pig_Piglet_Duroc": ["baby_piglet_duroc"],
    "SKM_Animal_Pig_Piglet_Spotted": ["baby_piglet_spotted"],
    
    # Sheep
    "SKM_Animal_Sheep_Suffolk": ["livestock_sheep_suffolk", "sheep_suffolk"],
    "SKM_Animal_Sheep_White": ["livestock_sheep_white", "sheep_white"],
    "SKM_Animal_Sheep_Tan": ["livestock_sheep_tan", "sheep_tan"],
    "SKM_Animal_Sheep_Lamb_Suffolk": ["baby_lamb", "baby_lamb_suffolk"],
    "SKM_Animal_Sheep_Lamb_White": ["baby_lamb_white"],
    "SKM_Animal_Sheep_Lamb_Tan": ["baby_lamb_tan"],
    "SKM_Animal_Sheep_Lamb_Spotted": ["baby_lamb_spotted"],
    
    # Goats
    "SKM_Animal_Goat_Brown": ["livestock_goat_brown", "goat_brown"],
    "SKM_Animal_Goat_White": ["livestock_goat_white", "goat_white"],
    "SKM_Animal_Goat_BlackWhite": ["livestock_goat_blackwhite", "goat_blackwhite"],
    "SKM_Animal_Goat_Kid_Brown": ["baby_kid", "baby_kid_brown"],
    "SKM_Animal_Goat_Kid_White": ["baby_kid_white"],
    "SKM_Animal_Goat_Kid_BlackWhite": ["baby_kid_blackwhite"],
    
    # Chickens
    "SKM_Animal_Chicken_Red": ["livestock_chicken_red", "chicken_red"],
    "SKM_Animal_Chicken_White": ["livestock_chicken_white", "chicken_white"],
    "SKM_Animal_Chicken_Barred": ["livestock_chicken_barred", "chicken_barred"],
    "SKM_Animal_Chicken_Chick_Yellow": ["baby_chick", "baby_chick_yellow"],
    "SKM_Animal_Chicken_Chick_White": ["baby_chick_white"],
    "SKM_Animal_Chicken_Chick_Barred": ["baby_chick_barred"],
    "SKM_Animal_Chicken_Chick_Brown": ["baby_chick_brown"],
}

processed_count = 0
for model_key, icon_names in ICON_MAPPING.items():
    render_file = os.path.join(RENDERS_DIR, f"{model_key}_render.png")
    if not os.path.exists(render_file):
        print(f"Missing render: {render_file}")
        continue
    
    img = Image.open(render_file).convert("RGBA")
    bbox = img.split()[3].getbbox()
    if not bbox:
        print(f"Empty alpha for {render_file}")
        continue
        
    cropped = img.crop(bbox)
    cw, ch = cropped.size
    max_dim = 104 # 128 - 2*12 safe margin
    scale = min(max_dim / max(cw, ch), 1.0)
    nw = max(1, int(round(cw * scale)))
    nh = max(1, int(round(ch * scale)))
    resized = cropped.resize((nw, nh), Image.Resampling.LANCZOS)
    
    out = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
    px = (128 - nw) // 2
    py = (128 - nh) // 2
    out.paste(resized, (px, py), resized)
    
    # Enforce pure 0 alpha on outer borders
    pixels = out.load()
    for x in range(128):
        pixels[x, 0] = (0, 0, 0, 0)
        pixels[x, 127] = (0, 0, 0, 0)
    for y in range(128):
        pixels[0, y] = (0, 0, 0, 0)
        pixels[127, y] = (0, 0, 0, 0)
        
    for name in icon_names:
        for tdir in target_dirs:
            p = os.path.join(tdir, f"{name}.png")
            out.save(p, "PNG")
        processed_count += 1
        print(f"  [ICON] Saved {name}.png across all folders.")

print(f"\nSUCCESS: Formatted {processed_count} animal icons to standard 128x128 transparent RGBA with 12px margins!")

