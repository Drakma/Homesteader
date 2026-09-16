import os, hashlib
from collections import defaultdict

HUD_ITEMS = r"C:\Users\casey\Desktop\Homesteader\HUD\assets\items"

hash_to_files = defaultdict(list)
for f in sorted(os.listdir(HUD_ITEMS)):
    if f.endswith(".png"):
        p = os.path.join(HUD_ITEMS, f)
        with open(p, "rb") as fp:
            h = hashlib.sha256(fp.read()).hexdigest()
        hash_to_files[h].append(f)

dup_hashes = {h: files for h, files in hash_to_files.items() if len(files) > 1}
print(f"=== EXACT BYTE-FOR-BYTE DUPLICATE FILES IN HUD/assets/items ({len(dup_hashes)} sets) ===")
total_dup_files = 0
for h, files in dup_hashes.items():
    print(f"  {files[0]}: duplicates -> {files[1:]}")
    total_dup_files += len(files) - 1

print(f"\nTotal redundant duplicate files: {total_dup_files}")

