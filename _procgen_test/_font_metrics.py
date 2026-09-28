"""Print font metrics for the title text used in window headers."""
import sys, os
KIT = os.path.abspath(r"C:\Users\casey\Desktop\Homesteader\assets/hud_kit")
sys.path.insert(0, KIT)
from runtime.render import _hud_font
from PIL import Image, ImageDraw

font = _hud_font(int(36 * 0.60), weight="bold")
print(f"font size: {int(36*0.60)}")
print(f"font.getmetrics(): {font.getmetrics()}")
print(f"font.getbbox('Confirm Action'): {font.getbbox('Confirm Action')}")

img = Image.new("RGB", (300, 60), "white")
d = ImageDraw.Draw(img)
d.text((0, 0), "Confirm Action", fill=(0, 0, 0), font=font)
# Find vertical extent of black pixels (the actual rendered mass).
pl = img.load()
top, bot = None, None
for y in range(60):
    has_black = False
    for x in range(300):
        r, g, b = pl[x, y]
        if r < 100 and g < 100 and b < 100:
            has_black = True
            break
    if has_black:
        if top is None:
            top = y
        bot = y
print(f"rendered glyph mass: top={top} bot={bot}  center={(top+bot)/2}")
