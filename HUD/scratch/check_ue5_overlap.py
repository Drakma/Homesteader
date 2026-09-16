import os
from collections import defaultdict

UE5_ICONS = r"C:\Users\casey\Desktop\Homesteader\Homesteader\Content\Homesteader\UI\Icons"

root_files = set(f for f in os.listdir(UE5_ICONS) if f.endswith(".png"))
subdir_files = defaultdict(list)

for root, dirs, files in os.walk(UE5_ICONS):
    if root == UE5_ICONS:
        continue
    for f in files:
        if f.endswith(".png"):
            subdir_files[f].append(os.path.relpath(os.path.join(root, f), UE5_ICONS))

print(f"Root files in UI/Icons: {len(root_files)}")
print(f"Subdir files across UI/Icons: {len(subdir_files)}")

overlap = root_files.intersection(subdir_files.keys())
print(f"Files appearing in BOTH root and a subdirectory: {len(overlap)}")
for f in sorted(list(overlap))[:20]:
    print(f"  {f} -> root and {subdir_files[f]}")

