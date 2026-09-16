import os
from PIL import Image

HUD_ITEMS = r"C:\Users\casey\Desktop\Homesteader\HUD\assets\items"

clutter_items = [f for f in os.listdir(HUD_ITEMS) if f.startswith("clutter_")]
print("Clutter items:")
for f in clutter_items:
    im = Image.open(os.path.join(HUD_ITEMS, f))
    print(f"  {f:<25}: size={im.size} bbox={im.getbbox()}")

