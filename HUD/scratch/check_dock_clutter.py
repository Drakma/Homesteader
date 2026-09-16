import os, csv
from PIL import Image

HUD_ITEMS = r"C:\Users\casey\Desktop\Homesteader\HUD\assets\items"

# Check the dock vs clutter files
print("Checking dock vs clutter...")
for name in ["dock_large_new", "dock_large_old", "dock_small_new", "dock_small_old", "clutter_branch", "clutter_dirt_clump", "clutter_grass_tuft"]:
    p = os.path.join(HUD_ITEMS, f"{name}.png")
    if os.path.exists(p):
        im = Image.open(p)
        print(f"  {name:<20}: size={im.size} bbox={im.getbbox()}")

