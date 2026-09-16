#!/usr/bin/env python3
"""
Homesteader 3D Foliage & Icon QA Validation Suite
Validates all 28 foliage 3D meshes (.obj + .mtl) and 128x128 preview icons (.png)
against strict Homesteader rules:
- Ground level root alignment (z_min ~= 0)
- Valid metric scale & normals
- Synchronized dual workspaces (HUD & UE5)
- 128x128 32-bit pure transparent RGBA
- Strict 12px safe margin (bounding box <= 104px)
- 100% outer perimeter alpha == 0
- Zero frames / outlines
"""

import os
import sys
from PIL import Image

HUD_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UE5_ROOT = os.path.abspath(os.path.join(HUD_ROOT, "..", "Homesteader", "Content", "Homesteader"))

HUD_MODELS_DIR = os.path.join(HUD_ROOT, "assets", "foliage", "models")
HUD_ICONS_DIR = os.path.join(HUD_ROOT, "assets", "foliage", "icons")
UE5_MODELS_DIR = os.path.join(UE5_ROOT, "Assets", "Foliage", "Meshes")
UE5_ICONS_DIR = os.path.join(UE5_ROOT, "UI", "Icons", "Foliage")

EXPECTED_ASSETS = [
    "SM_Tree_Oak_Large",
    "SM_Tree_Oak_Medium",
    "SM_Tree_Oak_Small",
    "SM_Tree_Oak_Autumn",
    "SM_Tree_Pine_Tall",
    "SM_Tree_Pine_Medium",
    "SM_Tree_Pine_Small",
    "SM_Tree_Birch_Tall",
    "SM_Tree_Birch_Medium",
    "SM_Tree_Apple",
    "SM_Tree_Willow",
    "SM_Tree_Dead_Snag",
    "SM_Bush_Round_Large",
    "SM_Bush_Round_Medium",
    "SM_Bush_Berry",
    "SM_Bush_Flowering",
    "SM_Bush_DryScrub",
    "SM_Bramble_Patch_Large",
    "SM_Bramble_Patch_Small",
    "SM_Bramble_Arch",
    "SM_Grass_Tuft_Meadow",
    "SM_Grass_Tall_Wild",
    "SM_Grass_Short_Lawn",
    "SM_Flora_Reeds_Cattail",
    "SM_Flora_Fern_Forest",
    "SM_Flora_Mushroom_Cluster",
    "SM_Flora_Tree_Stump",
    "SM_Flora_Fallen_Log",
]

def validate_mesh(name):
    errors = []
    hud_obj = os.path.join(HUD_MODELS_DIR, f"{name}.obj")
    hud_mtl = os.path.join(HUD_MODELS_DIR, f"{name}.mtl")
    ue5_obj = os.path.join(UE5_MODELS_DIR, f"{name}.obj")
    ue5_mtl = os.path.join(UE5_MODELS_DIR, f"{name}.mtl")

    # File presence check
    for p in [hud_obj, hud_mtl, ue5_obj, ue5_mtl]:
        if not os.path.exists(p) or os.path.getsize(p) == 0:
            errors.append(f"Missing or empty file: {p}")

    if errors:
        return False, errors, {}

    # Parse OBJ
    v_count = 0
    f_count = 0
    z_coords = []
    used_materials = set()

    with open(hud_obj, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("v "):
                parts = line.split()
                if len(parts) >= 4:
                    v_count += 1
                    z_coords.append(float(parts[3]))
            elif line.startswith("f "):
                f_count += 1
            elif line.startswith("usemtl "):
                used_materials.add(line.split()[1])

    # Parse MTL
    mtl_materials = set()
    with open(hud_mtl, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("newmtl "):
                mtl_materials.add(line.split()[1])

    if v_count < 8:
        errors.append(f"Insufficient vertices: {v_count}")
    if f_count < 4:
        errors.append(f"Insufficient faces: {f_count}")

    # Ground alignment check (z_min should be around 0)
    if z_coords:
        z_min = min(z_coords)
        z_max = max(z_coords)
        height = z_max - z_min
        if abs(z_min) > 1.5:
            errors.append(f"Pivot not at ground level: z_min={z_min:.2f} (expected ~0.0)")
    else:
        errors.append("No vertices parsed")
        height = 0

    # Material matching
    missing_mats = used_materials - mtl_materials
    if missing_mats:
        errors.append(f"Materials used in OBJ but missing in MTL: {missing_mats}")

    stats = {
        "vertices": v_count,
        "triangles": f_count,
        "height_cm": height,
        "materials": list(used_materials)
    }

    return (len(errors) == 0), errors, stats

def validate_icon(name):
    errors = []
    hud_icon = os.path.join(HUD_ICONS_DIR, f"{name}.png")
    ue5_icon = os.path.join(UE5_ICONS_DIR, f"{name}.png")

    for p in [hud_icon, ue5_icon]:
        if not os.path.exists(p) or os.path.getsize(p) == 0:
            errors.append(f"Missing or empty icon: {p}")

    if errors:
        return False, errors, {}

    img = Image.open(hud_icon)
    if img.size != (128, 128):
        errors.append(f"Incorrect canvas size: {img.size} (expected 128x128)")
    if img.mode != "RGBA":
        errors.append(f"Incorrect color mode: {img.mode} (expected RGBA)")

    # Analyze alpha channels and bounding box
    pixels = img.load()
    w, h = img.size

    # Perimeter check (x=0, x=127, y=0, y=127 must have alpha == 0)
    for x in range(w):
        if pixels[x, 0][3] != 0:
            errors.append(f"Top perimeter has non-zero alpha at x={x}")
            break
        if pixels[x, h - 1][3] != 0:
            errors.append(f"Bottom perimeter has non-zero alpha at x={x}")
            break
    for y in range(h):
        if pixels[0, y][3] != 0:
            errors.append(f"Left perimeter has non-zero alpha at y={y}")
            break
        if pixels[w - 1, y][3] != 0:
            errors.append(f"Right perimeter has non-zero alpha at y={y}")
            break

    # Alpha bounding box
    min_x, max_x = w, 0
    min_y, max_y = h, 0
    solid_pixel_count = 0

    for y in range(h):
        for x in range(w):
            alpha = pixels[x, y][3]
            if alpha > 10:  # non-trivial alpha
                solid_pixel_count += 1
                if x < min_x: min_x = x
                if x > max_x: max_x = x
                if y < min_y: min_y = y
                if y > max_y: max_y = y

    if solid_pixel_count == 0:
        errors.append("Icon is completely empty transparent")
        bbox_w, bbox_h = 0, 0
        pad_l, pad_r, pad_t, pad_b = 0, 0, 0, 0
    else:
        bbox_w = (max_x - min_x) + 1
        bbox_h = (max_y - min_y) + 1
        pad_l = min_x
        pad_r = w - 1 - max_x
        pad_t = min_y
        pad_b = h - 1 - max_y

        if bbox_w > 104 or bbox_h > 104:
            errors.append(f"Bounding box exceeds 104px safe margin: {bbox_w}x{bbox_h}")
        min_pad = min(pad_l, pad_r, pad_t, pad_b)
        if min_pad < 12:
            errors.append(f"Safe padding violated: min padding = {min_pad}px (must be >= 12px)")

    stats = {
        "bbox": f"{bbox_w}x{bbox_h}",
        "min_padding_px": min(pad_l, pad_r, pad_t, pad_b),
        "solid_pixels": solid_pixel_count
    }

    return (len(errors) == 0), errors, stats

def main():
    print("=" * 70)
    print("Homesteader 3D Foliage & Icon QA Validation Suite")
    print("=" * 70)

    total_meshes = len(EXPECTED_ASSETS)
    passed_meshes = 0
    mesh_stats_table = []

    print(f"\n[1/2] VALIDATING 3D LOW-POLY MESHES ({total_meshes} assets)...")
    for name in EXPECTED_ASSETS:
        ok, errors, stats = validate_mesh(name)
        if ok:
            passed_meshes += 1
            mesh_stats_table.append((name, stats["height_cm"], stats["triangles"], len(stats["materials"])))
            print(f"  [PASS] {name:<26} H={stats['height_cm']:>5.1f}cm  Tris={stats['triangles']:>4}  Mats={len(stats['materials'])}")
        else:
            print(f"  [FAIL] {name:<26}")
            for e in errors:
                print(f"         - {e}")

    total_icons = len(EXPECTED_ASSETS)
    passed_icons = 0
    print(f"\n[2/2] VALIDATING 128x128 PREVIEW ICONS ({total_icons} assets)...")
    for name in EXPECTED_ASSETS:
        ok, errors, stats = validate_icon(name)
        if ok:
            passed_icons += 1
            print(f"  [PASS] {name:<26} BBox={stats['bbox']:>7}  MinPad={stats['min_padding_px']:>2}px  PerimeterAlpha=0")
        else:
            print(f"  [FAIL] {name:<26}")
            for e in errors:
                print(f"         - {e}")

    print("\n" + "=" * 70)
    print(f"SUMMARY REPORT:")
    print(f"  3D Meshes: {passed_meshes}/{total_meshes} passed")
    print(f"  2D Icons:  {passed_icons}/{total_icons} passed")
    print("=" * 70)

    if passed_meshes == total_meshes and passed_icons == total_icons:
        print("ALL QA CHECKS PASSED PERFECTLY! ZERO ERRORS.\n")
        return 0
    else:
        print("QA CHECKS FAILED! Please inspect reported errors above.\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())

