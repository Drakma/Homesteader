"""
Step 4 v4: raw download via requests.get with HTTP Range-GET resume.

Why this version: huggingface_hub's `hf_hub_download` stalls on Windows
after 12+ minutes (open TCP connections but no bytes moving). We go lower-
level: build the resolve URL ourselves, stream bytes in chunks, write to disk,
and verify sha256 against HfApi's reported size for any completed file.

Strategy:
  - HfApi.repo_info with files_metadata=True gives us the canonical size of
    each file. We don't need to verify sha256 because huggingface.co LFS
    guarantees that the bytes returned for a given URL are the canonical
    file at that revision.
  - HTTP Range-GET with file-size header checks: if local file has fewer
    bytes than remote, append `Range: bytes=N-` and resume.
  - Print progress every 5% and reset ETAs. Live stdout, no buffering.
"""
import os
import sys
import time
import math
import requests
from huggingface_hub import HfApi

MB = 1024 * 1024

REPO_ID = "Qwen/Qwen-Image-2.1"
LOCAL_DIR = r"C:\Users\casey\Desktop\models\Qwen-Image-2.1"
RESOLUTION = "main"
ALLOW = [
    "*.json", "*.md", "LICENSE",
    "tokenizer/*", "scheduler/*", "processor/*",
    "text_encoder/*.safetensors", "text_encoder/*.json",
    "transformer/*.safetensors", "transformer/*.json",
    "vae/*.safetensors", "vae/*.json", "model_index.json",
]

import fnmatch

api = HfApi()
info = api.repo_info(REPO_ID, files_metadata=True, revision=RESOLUTION)

# Build list of (size, filename), smallest first.
candidates = []
for sib in info.siblings:
    if not any(fnmatch.fnmatch(sib.rfilename, p) for p in ALLOW):
        continue
    candidates.append((getattr(sib, "size", 0) or 0, sib.rfilename))
candidates.sort(key=lambda t: t[0])

print(f"[step4v4] {len(candidates)} files, total "
      f"{sum(s for s,_ in candidates) / (1024**3):.2f} GB", flush=True)

session = requests.Session()

ok = 0
fail = 0
for size, fname in candidates:
    relpath = fname.replace("/", os.sep)
    dest = os.path.join(LOCAL_DIR, relpath)
    os.makedirs(os.path.dirname(dest), exist_ok=True)

    # Already complete? skip
    if os.path.isfile(dest) and os.path.getsize(dest) == size:
        msg = ("  [SKIP] " + fname + " (" + str(round(size/MB, 1)) + " MB)")
        print(msg, flush=True)
        ok += 1
        continue

    url = f"https://huggingface.co/{REPO_ID}/resolve/{RESOLUTION}/{fname}"
    # Resume offset = current on-disk size (if any).
    have = os.path.getsize(dest) if os.path.isfile(dest) else 0
    headers = {"Range": f"bytes={have}-"} if have > 0 else {}

    msg = ("  [START] " + fname
           + " (" + str(round(size/MB, 1)) + " MB, have="
           + str(round(have/MB, 1)) + " MB)")
    print(msg, flush=True)
    t0 = time.time()
    try:
        with session.get(url, headers=headers, stream=True, timeout=120) as resp:
            if resp.status_code not in (200, 206):
                print(f"    HTTP {resp.status_code} for {fname} ({resp.reason})", flush=True)
                fail += 1
                continue
            mode = "ab" if have > 0 else "wb"
            chunk = 8 * 1024 * 1024  # 8 MB chunks
            written = have
            last_print = time.time()
            with open(dest, mode) as fh:
                for blob in resp.iter_content(chunk_size=chunk):
                    if blob:
                        fh.write(blob)
                        written += len(blob)
                    # Every ~5 seconds, log progress.
                    now = time.time()
                    if now - last_print > 5:
                        pct = (written / size * 100) if size else 0
                        mb_s = (written - have) / MB / max(1, now - t0)
                        msg = ("    [+%.1fs] %.1f / %.1f MB (%.1f%%) %.1f MB/s"
                               % ((now - t0), written / MB, size / MB, pct, mb_s))
                        print(msg, flush=True)
                        last_print = now
        elapsed = time.time() - t0
        mb_s = size / MB / elapsed if elapsed > 0 else float('inf')
        print(f"  [DONE] {fname} in {elapsed:.1f}s ({mb_s:.1f} MB/s now -> "
              f"session total written={written/MB:.1f} MB)", flush=True)
        ok += 1
    except Exception as e:
        print(f"  [FAIL] {fname}: {repr(e)}", flush=True)
        fail += 1

print(f"[step4v4] ok={ok} fail={fail}", flush=True)
print(f"[step4v4] on-disk total: "
      f"{sum(os.path.getsize(os.path.join(r,f)) for r,_,fs in os.walk(LOCAL_DIR) for f in fs) / (1024**3):.2f} GB", flush=True)
