import sys
sys.path.insert(0, r"C:\Users\casey\Desktop\Homesteader")
from PIL import Image
from assets.hud_kit.runtime.render import _draw_header_band

img = Image.new("RGBA", (1920, 80), (0, 0, 0, 0))
_draw_header_band(img, 0, 0, 1920, 80, "#18202c", "#0a0e15", "#c19a3c",
                  seed=0x4ad5011)
img.save(r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Resources\HUDTree\Atlases\header_strip.png")
print("baked")
