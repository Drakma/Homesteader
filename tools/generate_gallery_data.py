#!/usr/bin/env python3
"""
Inspects all 267 models across assets/ and generates full JS arrays
and HTML markup for gallery/index.html
"""
import os
import json

# tools/ sits at the repo root, so the project root is one level up.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HUD_ROOT = PROJECT_ROOT  # legacy alias - keep old joins working

def parse_obj(obj_path):
    verts = []
    face_count = 0
    with open(obj_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("v "):
                parts = line.strip().split()
                verts.append((float(parts[1]), float(parts[2]), float(parts[3])))
            elif line.startswith("f "):
                face_count += 1
    if not verts:
        return None
    xs = [v[0] for v in verts]
    ys = [v[1] for v in verts]
    zs = [v[2] for v in verts]
    return {
        "num_verts": len(verts),
        "num_faces": face_count,
        "dx": max(xs) - min(xs),
        "dy": max(ys) - min(ys),
        "dz": max(zs) - min(zs),
    }

print("Testing parse_obj on a sample model...")
p = os.path.join(HUD_ROOT, "assets", "farming", "models", "SM_Machine_Tractor_Large.obj")
print("Parsed:", parse_obj(p))

