"""
Cross-check: actual on-disk file sizes vs expected (HF Hub reported) sizes.
"""
import os
import fnmatch
from huggingface_hub import HfApi

REPO_ID = "Qwen/Qwen-Image-2.1"
LOCAL_DIR = r"C:\Users\casey\Desktop\models\Qwen-Image-2.1"
ALLOW = [
    "*.json", "*.md", "LICENSE",
    "tokenizer/*", "scheduler/*", "processor/*",
    "text_encoder/*.safetensors", "text_encoder/*.json",
    "transformer/*.safetensors", "transformer/*.json",
    "vae/*.safetensors", "vae/*.json", "model_index.json",
]

api = HfApi()
info = api.repo_info(REPO_ID, files_metadata=True)

def matches(s, pats):
    return any(fnmatch.fnmatch(s, p) for p in pats)

ok = []
bad = []
for sib in info.siblings:
    if not matches(sib.rfilename, ALLOW):
        continue
    expected = getattr(sib, "size", 0) or 0
    local = os.path.join(LOCAL_DIR, sib.rfilename.replace("/", os.sep))
    actual = os.path.getsize(local) if os.path.isfile(local) else None
    if actual is None:
        bad.append((sib.rfilename, expected, "MISSING"))
        continue
    if actual == expected:
        ok.append((sib.rfilename, expected))
    else:
        bad.append((sib.rfilename, expected, actual))

print(f"OK  ({len(ok)} files):")
for f, sz in ok:
    print(f"  {sz:>14,d}  {f}")
print()
print(f"BAD ({len(bad)} files):")
for f, e, a in bad:
    print(f"  expected={e:>14,d}  actual={a!s:>14}  {f}")
