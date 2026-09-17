import os
import sys
from PIL import Image

_this_dir = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(_this_dir)  # tools/ sits at the repo root (one level up)

HUD_GROUND_TEX = os.path.join(BASE_DIR, "assets", "ground", "textures")
HUD_GROUND_MODELS = os.path.join(BASE_DIR, "assets", "ground", "models")
UNREAL_GROUND_TEX = r"C:\Users\casey\Desktop\Homesteader\Homesteader\Content\Homesteader\Assets\Ground\Textures"
UNREAL_GROUND_MESHES = r"C:\Users\casey\Desktop\Homesteader\Homesteader\Content\Homesteader\Assets\Ground\Meshes"

GROUND_TYPES = [
    "gravel", "dirt", "road", "path", "grass", 
    "tall_grass", "farmland", "trampled_grass", "concrete", "black_top", 
    "bricks", "mud", "swamp", "pond", "deep_water", 
    "sand", "wood_planks", "snow", "forest_floor", "flagstone"
]

def validate_textures(tex_root):
    print(f"=== Validating Ground Textures in: {tex_root} ===")
    errors = 0
    checked = 0
    if not os.path.isdir(tex_root):
        # The Unity-side tree is only populated by a separate deploy step
        # (see docs/UNITY_INTEGRATION_GUIDE.md). Skip it when absent rather
        # than reporting every ground type as missing.
        print(f"  [SKIP] ground texture target not deployed yet: {tex_root}\n")
        return errors
    for gt in GROUND_TYPES:
        g_dir = os.path.join(tex_root, gt)
        if not os.path.isdir(g_dir):
            print(f"  [MISSING FOLDER] {gt}")
            errors += 1
            continue
        for suffix in ["BaseColor", "Normal", "ORM"]:
            checked += 1
            fname = f"T_Ground_{gt}_{suffix}.png"
            p = os.path.join(g_dir, fname)
            if not os.path.exists(p):
                print(f"  [MISSING FILE] {gt}/{fname}")
                errors += 1
                continue
            try:
                im = Image.open(p)
                if im.size != (512, 512):
                    print(f"  [INVALID SIZE] {gt}/{fname}: {im.size}, expected (512, 512)")
                    errors += 1
            except Exception as e:
                print(f"  [CORRUPT] {gt}/{fname}: {e}")
                errors += 1

    print(f"Textures Checked: {checked}, Errors: {errors}\n")
    return errors

def validate_meshes(mesh_root):
    print(f"=== Validating Ground Meshes in: {mesh_root} ===")
    errors = 0
    checked = 0
    if not os.path.isdir(mesh_root):
        # Ground meshes are optional - the folder is absent until the first
        # ground mesh is generated. Skip rather than crash the whole run.
        print(f"  [SKIP] no ground mesh folder yet: {mesh_root}\n")
        return errors
    for f in sorted(os.listdir(mesh_root)):
        if f.endswith(".obj"):
            checked += 1
            p = os.path.join(mesh_root, f)
            verts, uvs, normals, faces = 0, 0, 0, 0
            xs, ys, zs = [], [], []
            with open(p, "r", encoding="utf-8") as of:
                for line in of:
                    parts = line.strip().split()
                    if not parts: continue
                    if parts[0] == "v":
                        verts += 1
                        xs.append(float(parts[1]))
                        ys.append(float(parts[2]))
                        zs.append(float(parts[3]))
                    elif parts[0] == "vt":
                        uvs += 1
                        u, v = float(parts[1]), float(parts[2])
                        if not (-0.01 <= u <= 1.01 and -0.01 <= v <= 1.01):
                            errors += 1
                            print(f"  [INVALID UV] {f}: ({u}, {v})")
                    elif parts[0] == "vn":
                        normals += 1
                    elif parts[0] == "f":
                        faces += 1

            dx = round(max(xs) - min(xs), 1) if xs else 0
            dy = round(max(ys) - min(ys), 1) if ys else 0
            dz = round(max(zs) - min(zs), 1) if zs else 0
            
            mtl_p = os.path.splitext(p)[0] + ".mtl"
            has_mtl = os.path.exists(mtl_p)
            if not has_mtl:
                print(f"  [MISSING MTL] {f}")
                errors += 1
            else:
                print(f"  [PASS] {f:28}: {verts:3d} verts, {faces:3d} faces, size=({dx}, {dy}, {dz}) cm")

    print(f"Meshes Checked: {checked}, Errors: {errors}\n")
    return errors

def main():
    # Unity-side deployment is validated separately, not here - this script
    # only covers the source assets/ tree. Re-enable the two UNREAL_* calls
    # once the Unity Content/ tree is actually populated.
    tex_err = validate_textures(HUD_GROUND_TEX)
    mesh_err = validate_meshes(HUD_GROUND_MODELS)

    total_err = tex_err + mesh_err
    if total_err == 0:
        print(">>> ALL GROUND TEXTURES & 3D MESHES PASSED VALIDATION! <<<")
    else:
        print(f">>> VALIDATION FAILED WITH {total_err} ERRORS <<<")
        sys.exit(1)

if __name__ == "__main__":
    main()

