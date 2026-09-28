"""
Step 4 v3: sequential per-file download using hf_hub_download directly.
Bypasses `snapshot_download` parallelism (which stalls on Windows) and
gives us per-file progress + automatic resume via Range GET.

For each missing file, we call hf_hub_download which:
  - if file already exists with matching size: skip
  - if file is partially there: tries to resume from byte offset
  - else: full HTTP download

Order: smallest first, then by descending size. This way, the JSON/config
files get a fast path, then the largest transformer file goes last, and we
can interrupt+resume on anything before that.
"""
import os
import sys
import time
import requests
from huggingface_hub import hf_hub_download, HfApi

REPO_ID = "Qwen/Qwen-Image-2.1"
LOCAL_DIR = r"C:\Users\casey\Desktop\models\Qwen-Image-2.1"
RESOLUTION = "main"

# Allow patterns.
ALLOW = [
    "*.json", "*.md", "LICENSE",
    "tokenizer/*", "scheduler/*", "processor/*",
    "text_encoder/*.safetensors", "text_encoder/*.json",
    "transformer/*.safetensors", "transformer/*.json",
    "vae/*.safetensors", "vae/*.json",
    "model_index.json",
]

import fnmatch

api = HfApi()
info = api.repo_info(REPO_ID, files_metadata=True, revision=RESOLUTION)

candidates = []
for sib in info.siblings:
    if not any(fnmatch.fnmatch(sib.rfilename, p) for p in ALLOW):
        continue
    candidates.append((getattr(sib, "size", 0) or 0, sib.rfilename))
# Smallest first so the JSONs come down fast.
candidates.sort(key=lambda t: t[0])

print(f"[step4v3] {len(candidates)} files", flush=True)
total_size = sum(t[0] for t in candidates)
print(f"[step4v3] total size: {total_size / (1024**3):.2f} GB", flush=True)
done = 0

# We deliberately do NOT pass local_dir to hf_hub_download; we want manual
# control over where the destination lives, and we want progress to be
# observable byte-by-byte. We replicate the local-dir behaviour below.
os.makedirs(LOCAL_DIR, exist_ok=True)

MB = 1024 * 1024
ok = 0
fail = 0
for size, fname in candidates:
    relpath = fname.replace("/", os.sep)
    dest = os.path.join(LOCAL_DIR, relpath)
    os.makedirs(os.path.dirname(dest), exist_ok=True)

    if os.path.isfile(dest) and os.path.getsize(dest) == size:
        print(f"  [skip {time.strftime('%H:%M:%S')}] {fname} ({size/MB:.1f} MB)", flush=True)
        ok += 1
        continue

    print(f"  [start {time.strftime('%H:%M:%S')}] {fname} ({size/MB:.1f} MB)", flush=True)
    t0 = time.time()

    # Use hf_hub_download's content-addressed dedup by writing into the
    # standard global cache layout so future runs are content-addressed.
    # We then move the file to LOCAL_DIR.
    try:
        cached = hf_hub_download(
            repo_id=REPO_ID,
            filename=fname,
            revision=RESOLUTION,
            etag_timeout=60,
        )
        # Move/symlink into local_dir.
        import shutil
        if os.path.abspath(cached) != os.path.abspath(dest):
            # Replace dest with cached (overwrite).
            shutil.copyfile(cached, dest)
        elapsed = time.time() - t0
        rate_MBs = (size / MB) / elapsed if elapsed > 0 else float('inf')
        print(f"  [done {time.strftime('%H:%M:%S')}] {fname} in {elapsed:.1f}s ({rate_MBs:.1f} MB/s)", flush=True)
        ok += 1
    except Exception as e:
        print(f"  [FAIL {time.strftime('%H:%M:%S')}] {fname}: {repr(e)}", flush=True)
        fail += 1

print(f"[step4v3] ok={ok} fail={fail}", flush=True)
