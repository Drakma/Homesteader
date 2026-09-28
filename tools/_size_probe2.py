"""
Re-probe: see which files in our allow-list are NOT yet fully present on disk.
Needed to plan a targeted re-download that picks up where the stalled attempt
stopped.
"""
import os
from huggingface_hub import HfApi

REPO_ID = "Qwen/Qwen-Image-2.1"
LOCAL_DIR = r"C:\Users\casey\Desktop\models\Qwen-Image-2.1"

ALLOW = [
    "*.json", "*.md", "LICENSE", "tokenizer/*", "scheduler/*", "processor/*",
    "text_encoder/*.safetensors", "text_encoder/*.json",
    "transformer/*.safetensors", "transformer/*.json",
    "vae/*.safetensors", "vae/*.json", "model_index.json",
]

# The cache subdir layout for `local_dir=` placements differs from the global
# cache layout. For local_dir, huggingface_hub writes files directly into the
# target, NOT into a .cache subdir. The .cache subdir we saw is from
# instantiating HfApi's snapshot chain and using the *global* cache layout for
# resume coordination - files are staged in .cache and then moved into local_dir.
# We compute "did this file finish?" by checking local_dir directly.
import fnmatch

api = HfApi()
info = api.repo_info(REPO_ID, files_metadata=True)
def matches(p, pats):
    return any(fnmatch.fnmatch(p, pt) for pt in pats)

print(f"cache layout: local_dir path: {LOCAL_DIR}")
print(f"all siblings under repo: {len(info.siblings)}")

# On-disk state under local_dir.
present = set()
total_present = 0
for root, _, files in os.walk(LOCAL_DIR):
    for f in files:
        if f.endswith(".incomplete") or f.endswith(".lock") or f.endswith(".metadata"):
            continue
        # compute path-relative
        full = os.path.join(root, f)
        rel = os.path.relpath(full, LOCAL_DIR).replace("\\", "/")
        present.add(rel)
        try:
            total_present += os.path.getsize(full)
        except OSError:
            pass

print(f"on-disk files (excluding .incomplete/.lock/.metadata): {len(present)}")
print(f"on-disk size (excluding temp): {total_present:,} bytes = {total_present / (1024**3):.2f} GB")

# What's missing?
missing = []
size_missing = 0
for sib in info.siblings:
    if not matches(sib.rfilename, ALLOW):
        continue
    if sib.rfilename in present:
        continue
    size = getattr(sib, "size", None) or 0
    missing.append((sib.rfilename, size))
    size_missing += size

print()
print(f"missing files: {len(missing)}")
print(f"missing bytes: {size_missing:,} = {size_missing / (1024**3):.2f} GB")
for p, s in missing:
    print(f"  {s:>14,d}  {p}")
