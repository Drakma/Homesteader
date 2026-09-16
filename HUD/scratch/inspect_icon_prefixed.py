import os
from PIL import Image

HUD_ITEMS = r"C:\Users\casey\Desktop\Homesteader\HUD\assets\items"

icon_prefixed = [f for f in os.listdir(HUD_ITEMS) if f.startswith("icon_")]
print(f"Files starting with icon_ ({len(icon_prefixed)}):")
for f in sorted(icon_prefixed):
    p = os.path.join(HUD_ITEMS, f)
    im = Image.open(p)
    # Check if transparent or flat
    print(f"  {f:<25} size={im.size} mode={im.mode} bbox={im.getbbox()}")

