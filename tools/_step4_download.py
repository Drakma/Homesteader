"""
Step 4: actually download the Qwen/Qwen-Image-2.1 weights via the
Python-API snapshot_download helper. Sidesteps the `hf` CLI's
CLAUDE.md-fetch behavior that triggered a 404 in this environment.

Approach: snapshot_download(repo_id=, local_dir=, allow_patterns=...) - the
allow_patterns list mirrors the include globs we verified via _size_probe.py.
"""
import os
import sys
import time

from huggingface_hub import snapshot_download

REPO_ID = "Qwen/Qwen-Image-2.1"
LOCAL_DIR = r"C:\Users\casey\Desktop\models\Qwen-Image-2.1"

# Allow-patterns: include statement. Excludes the model's image-format sidecars
# (test_image.png, etc.) that exist in the repo but aren't needed for inference.
ALLOW = [
    "*.json",
    "*.md",
    "LICENSE",
    "tokenizer/*",
    "scheduler/*",
    "processor/*",
    "text_encoder/*.safetensors",
    "text_encoder/*.json",
    "transformer/*.safetensors",
    "transformer/*.json",
    "vae/*.safetensors",
    "vae/*.json",
    "model_index.json",
]

# Make sure the parent directory exists.
os.makedirs(LOCAL_DIR, exist_ok=True)

print(f"[step4 {time.strftime('%H:%M:%S')}] starting snapshot_download", flush=True)
print(f"  repo:    {REPO_ID}", flush=True)
print(f"  to:      {LOCAL_DIR}", flush=True)
print(f"  filters: {len(ALLOW)} allow patterns", flush=True)

# Per-file progress callback so a stalled worker is visible in the log every
# few seconds (the `tqdm` progress from snapshot_download is
# overwritable/replaceable and may have buffered on SIGPIPE in v1).
last_log = [time.time()]
def _on_progress(current, total):
    now = time.time()
    if now - last_log[0] < 10:
        return
    last_log[0] = now
    print(f"  [{time.strftime('%H:%M:%S')}] {current:,} / {total:,} bytes ({current/total*100:.1f}%)", flush=True)

t0 = time.time()
try:
    snapshot_download(
        repo_id=REPO_ID,
        local_dir=LOCAL_DIR,
        allow_patterns=ALLOW,
        tqdm_class=None,
        max_workers=2,           # 2 v 4: less Windows file-handle contention
        etag_timeout=60,
    )
except TypeError as e:
    print(f"[step4 retry without extended kwargs: {e}", flush=True)
    snapshot_download(
        repo_id=REPO_ID,
        local_dir=LOCAL_DIR,
        allow_patterns=ALLOW,
    )

elapsed = time.time() - t0
print(f"[step4 {time.strftime('%H:%M:%S')}] DONE in {elapsed:.1f}s", flush=True)

# Final size.
total = 0
for root, _, files in os.walk(LOCAL_DIR):
    for f in files:
        try:
            total += os.path.getsize(os.path.join(root, f))
        except OSError:
            pass
print(f"[step4] on-disk total: {total:,} bytes = {total / (1024**3):.2f} GB", flush=True)
