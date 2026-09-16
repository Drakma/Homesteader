import os
from PIL import Image, ImageDraw

p = r"C:\Users\casey\Desktop\Homesteader\HUD\assets\textures\animals\T_Baby_Calf_BaseColor.png"
os.makedirs(os.path.dirname(p), exist_ok=True)

# 512x512 texture palette
img = Image.new("RGBA", (512, 512), (218, 146, 88, 255)) # Rich caramel fur
draw = ImageDraw.Draw(img)

# 0: Fur base (already filled: 218, 146, 88)
# 1: Cream face / blaze
draw.rectangle([0, 0, 255, 127], fill=(251, 245, 235, 255))
# 2: Soft Pink Muzzle
draw.rectangle([256, 0, 511, 127], fill=(244, 206, 201, 255))
# 3: Dark Hooves
draw.rectangle([0, 128, 127, 255], fill=(92, 58, 44, 255))
# 4: Inner Ear Pink
draw.rectangle([128, 128, 255, 255], fill=(243, 148, 140, 255))
# 5: Horn Cream
draw.rectangle([256, 128, 383, 255], fill=(250, 244, 234, 255))
# 6: Eye Black
draw.rectangle([384, 128, 511, 255], fill=(18, 18, 22, 255))
# 7: White belly / eye highlight
draw.rectangle([0, 256, 127, 383], fill=(245, 243, 240, 255))
# 8: Fur Shadow / Tail Tuft
draw.rectangle([128, 256, 255, 383], fill=(186, 114, 62, 255))
# 9: Nostril dark
draw.rectangle([256, 256, 383, 383], fill=(160, 100, 92, 255))

img.save(p)
print("Updated calf texture saved.")

