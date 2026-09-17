import os
import sys

def validate_obj(path):
    errors = []
    if not os.path.exists(path):
        return [f"File not found: {path}"]

    verts = []
    uvs = []
    normals = []
    faces = []
    mtllib = None

    with open(path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            parts = line.strip().split()
            if not parts:
                continue
            tag = parts[0]
            if tag == "mtllib":
                mtllib = parts[1]
            elif tag == "v":
                if len(parts) >= 4:
                    try:
                        verts.append((float(parts[1]), float(parts[2]), float(parts[3])))
                    except ValueError:
                        errors.append(f"Line {line_num}: Invalid vertex float")
            elif tag == "vt":
                if len(parts) >= 3:
                    try:
                        u, v = float(parts[1]), float(parts[2])
                        if not (0.0 <= u <= 1.0 and 0.0 <= v <= 1.0):
                            errors.append(f"Line {line_num}: UV ({u}, {v}) outside [0, 1]")
                        uvs.append((u, v))
                    except ValueError:
                        errors.append(f"Line {line_num}: Invalid UV float")
            elif tag == "vn":
                if len(parts) >= 4:
                    try:
                        normals.append((float(parts[1]), float(parts[2]), float(parts[3])))
                    except ValueError:
                        errors.append(f"Line {line_num}: Invalid normal float")
            elif tag == "f":
                if len(parts) >= 4:
                    faces.append(parts[1:])

    if not verts:
        errors.append("No vertices found")
    if not uvs:
        errors.append("No UV coordinates found")
    if not normals:
        errors.append("No vertex normals found")
    if not faces:
        errors.append("No faces found")

    # Check companion MTL file
    mtl_path = os.path.splitext(path)[0] + ".mtl"
    if not os.path.exists(mtl_path):
        errors.append(f"Missing companion MTL file: {mtl_path}")

    # Calculate bounding box (cm)
    if verts:
        xs = [v[0] for v in verts]
        ys = [v[1] for v in verts]
        zs = [v[2] for v in verts]
        dx = max(xs) - min(xs)
        dy = max(ys) - min(ys)
        dz = max(zs) - min(zs)
        bbox_dims = (round(dx, 1), round(dy, 1), round(dz, 1))
    else:
        bbox_dims = (0, 0, 0)

    return errors, len(verts), len(faces), bbox_dims

def main():
    target = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\casey\Desktop\Homesteader\assets\models"
    
    if os.path.isfile(target):
        errs, num_v, num_f, dims = validate_obj(target)
        if errs:
            print(f"[FAIL] {os.path.basename(target)}:")
            for e in errs: print(f"  - {e}")
            sys.exit(1)
        else:
            print(f"[PASS] {os.path.basename(target)}: {num_v} verts, {num_f} faces, size={dims} cm")
    elif os.path.isdir(target):
        print(f"Validating 3D Static Meshes in: {target}\n")
        total = 0
        failed = 0
        for root, _, files in os.walk(target):
            for f in sorted(files):
                if f.endswith(".obj"):
                    total += 1
                    full_path = os.path.join(root, f)
                    errs, num_v, num_f, dims = validate_obj(full_path)
                    if errs:
                        failed += 1
                        print(f"  [FAIL] {f}:")
                        for e in errs: print(f"    - {e}")
                    else:
                        print(f"  [PASS] {f:28}: {num_v:3d} verts, {num_f:3d} faces, bbox={dims} cm")

        print(f"\nCompleted 3D validation: {total - failed}/{total} meshes passed.")
        if failed > 0:
            sys.exit(1)

if __name__ == "__main__":
    main()

