import os
import sys
from PIL import Image

def validate_icon(path):
    errors = []
    try:
        im = Image.open(path)
    except Exception as e:
        return [f"Unable to open image: {e}"]

    # 1. Format check
    if im.format != "PNG":
        errors.append(f"Format is {im.format}; must be PNG")
    if im.mode != "RGBA":
        errors.append(f"Color mode is {im.mode}; must be RGBA (32-bit)")

    # 2. Dimension check
    if im.size != (128, 128):
        errors.append(f"Dimensions are {im.size}; must be exactly 128x128 px")

    # 3. Alpha bounds check
    alpha = im.split()[3]
    bbox = alpha.getbbox()
    if not bbox:
        errors.append("Image is completely transparent / empty")
        return errors

    x0, y0, x1, y1 = bbox
    item_w, item_h = x1 - x0, y1 - y0
    max_dim = max(item_w, item_h)
    if max_dim > 106:
        errors.append(f"Max item dimension is {max_dim}px; exceeds 104px safe zone (+2px tolerance)")

    # 4. Canvas edge transparency check (NO CLIPPING & NO BORDERS)
    w, h = im.size
    for x in range(w):
        if im.getpixel((x, 0))[3] != 0 or im.getpixel((x, h - 1))[3] != 0:
            errors.append("Non-zero alpha detected on top/bottom canvas edge (border or clipping issue)")
            break
    for y in range(h):
        if im.getpixel((0, y))[3] != 0 or im.getpixel((w - 1, y))[3] != 0:
            errors.append("Non-zero alpha detected on left/right canvas edge (border or clipping issue)")
            break

    return errors

def main():
    target = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\casey\Desktop\Homesteader\assets\items"
    
    if os.path.isfile(target):
        errs = validate_icon(target)
        if errs:
            print(f"[FAIL] {os.path.basename(target)}:")
            for e in errs:
                print(f"  - {e}")
            sys.exit(1)
        else:
            print(f"[PASS] {os.path.basename(target)} meets all ruleset criteria!")
    elif os.path.isdir(target):
        print(f"Validating icons in: {target}")
        total = 0
        failed = 0
        for root, _, files in os.walk(target):
            for f in sorted(files):
                if f.endswith(".png") and not f.startswith("compact_"):
                    total += 1
                    full_path = os.path.join(root, f)
                    errs = validate_icon(full_path)
                    if errs:
                        failed += 1
                        print(f"  [FAIL] {f}:")
                        for e in errs:
                            print(f"    - {e}")
        print(f"\nCompleted validation: {total - failed}/{total} icons passed ruleset.")
        if failed > 0:
            sys.exit(1)

if __name__ == "__main__":
    main()

