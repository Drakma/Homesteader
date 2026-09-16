import os
from PIL import Image

HUD_ITEMS = r"C:\Users\casey\Desktop\Homesteader\HUD\assets\items"

for name in ["icon_axe", "tool_axe", "icon_bread", "food_bread", "icon_pickaxe", "tool_pickaxe", "icon_coin", "icon_heart", "icon_stamina"]:
    p = os.path.join(HUD_ITEMS, f"{name}.png")
    if os.path.exists(p):
        im = Image.open(p)
        print(f"{name:<20}: size={im.size} mode={im.mode} unique_colors={len(set(im.getdata()))}")

