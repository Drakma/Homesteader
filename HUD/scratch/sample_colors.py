from PIL import Image

palette_path = r"C:\Users\casey\Desktop\Homesteader\HUD\assets\textures\palettes\T_Homesteader_Palette.png"
icon_path = r"C:\Users\casey\Desktop\Homesteader\HUD\scratch\batch3\all_extracted\baby_calf.png"

pal = Image.open(palette_path).convert("RGB")
icon = Image.open(icon_path).convert("RGBA")

def find_cell(target_rgb):
    min_dist = 999999
    best = None
    for row in range(16):
        for col in range(16):
            px = int((col + 0.5) * pal.width / 16)
            py = int((row + 0.5) * pal.height / 16)
            c = pal.getpixel((px, py))
            dist = sum((a - b)**2 for a, b in zip(c, target_rgb))
            if dist < min_dist:
                min_dist = dist
                best = (col, row, c)
    return best

samples = {
    "snout_pink": icon.getpixel((25, 65))[:3],
    "forehead_white": icon.getpixel((35, 45))[:3],
    "horn_cream": icon.getpixel((40, 30))[:3],
    "body_caramel": icon.getpixel((80, 55))[:3],
    "hoof_brown": icon.getpixel((75, 105))[:3],
}

for k, v in samples.items():
    col, row, rgb = find_cell(v)
    print(f"{k}: target={v} -> palette col={col}, row={row}, rgb={rgb}")

