"""
Direct Python-API download using huggingface_hub.snapshot_download. This
bypasses the CLI subcommand entirely and uses the well-tested snapshot helper.
We use this instead of `hf download` because `hf` 1.31.0 hangs on a missing
CLAUDE.md fetch when invoked from an AI agent context.

Dry-run variant: list_files only, no download.
"""
import os
import sys

from huggingface_hub import HfApi

REPO_ID = "Qwen/Qwen-Image-2.1"

api = HfApi()
info = api.repo_info(REPO_ID, files_metadata=True)

include_patterns = [
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

import fnmatch

def matches(path, patterns):
    for p in patterns:
        if fnmatch.fnmatch(path, p):
            return True
    return False

print(f"repo: {REPO_ID}")
print(f"all siblings: {len(info.siblings)}")
total = 0
matched = []
for sib in info.siblings:
    if not matches(sib.rfilename, include_patterns):
        continue
    size = getattr(sib, "size", None) or 0
    matched.append((sib.rfilename, size))
    total += size

print(f"matched files: {len(matched)}")
print(f"total bytes   : {total:,}  ({total / (1024**3):.2f} GB)")
print()
for path, sz in matched:
    print(f"  {sz:>14,d}  {path}")
