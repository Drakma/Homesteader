#!/usr/bin/env python3
"""Point bare relative map_Kd references at the real texture in the tree.

Some .mtl files reference a texture by bare filename (e.g.
"T_Homesteader_Palette.png") assuming it sits alongside the .mtl. It does not -
the texture lives under assets/textures/ or assets/ground/textures/. This
rewrites each such reference to a path relative to the .mtl itself.

References whose texture exists nowhere in the tree (generator artifacts like
texture_0.png) are reported and left untouched, not guessed at.
"""
import glob
import os

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(REPO_ROOT, "assets")

# Index every file under assets/ by basename.
index = {}
for dirpath, dirnames, filenames in os.walk(ASSETS):
    for fn in filenames:
        index.setdefault(fn.lower(), []).append(os.path.join(dirpath, fn))

fixed, unresolved = [], []
for path in sorted(glob.glob(os.path.join(ASSETS, "**", "*.mtl"), recursive=True)):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    changed = False
    for i, line in enumerate(lines):
        if not line.startswith("map_Kd"):
            continue
        parts = line.split(None, 1)
        if len(parts) < 2:
            continue
        ref = parts[1].strip()

        # Only touch bare relative refs that do not already resolve.
        if os.path.isabs(ref):
            continue
        if os.path.exists(os.path.normpath(os.path.join(os.path.dirname(path), ref))):
            continue

        candidates = index.get(os.path.basename(ref).lower(), [])
        if not candidates:
            unresolved.append((os.path.relpath(path, REPO_ROOT), ref))
            continue

        # Prefer the candidate nearest the .mtl (shortest relative path).
        target = min(candidates, key=lambda c: len(os.path.relpath(c, os.path.dirname(path))))
        new_ref = os.path.relpath(target, os.path.dirname(path)).replace(os.sep, "/")
        lines[i] = f"map_Kd {new_ref}\n"
        changed = True
        fixed.append((os.path.relpath(path, REPO_ROOT), ref, new_ref))

    if changed:
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.writelines(lines)

print(f"Rewrote {len(fixed)} reference(s):")
for rel_mtl, old, new in fixed:
    print(f"  {rel_mtl}")
    print(f"      {old}  ->  {new}")

if unresolved:
    print(f"\nLeft alone - texture exists nowhere ({len(unresolved)}):")
    for rel_mtl, ref in unresolved:
        print(f"  {rel_mtl}  ->  {ref}")

# Re-verify everything.
print("\nRe-verifying all map_Kd references:")
bad = 0
for path in sorted(glob.glob(os.path.join(ASSETS, "**", "*.mtl"), recursive=True)):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            if not line.startswith("map_Kd"):
                continue
            parts = line.split(None, 1)
            if len(parts) < 2:
                continue
            ref = parts[1].strip()
            resolved = ref if os.path.isabs(ref) else os.path.normpath(os.path.join(os.path.dirname(path), ref))
            if not os.path.exists(resolved):
                bad += 1
                print(f"  [STILL BROKEN] {os.path.relpath(path, REPO_ROOT)} -> {ref}")
print(f"  {bad} broken reference(s) remaining.")
