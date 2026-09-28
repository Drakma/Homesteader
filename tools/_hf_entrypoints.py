"""
Find the huggingface_hub CLI entry points via importlib.metadata and the
actual `python -m` module name (for newer versions there's a `cli` subcommand
style entry point). Used to pick the correct invocation path.
"""
import importlib.metadata
import importlib.util
import os
import sys

print("huggingface_hub at:", importlib.util.find_spec("huggingface_hub").origin)
print()
print("=== console_scripts entry points ===")
for ep in importlib.metadata.entry_points().select(group="console_scripts"):
    if ep.name.startswith("huggingface") or "huggingface" in ep.value:
        print(f"  {ep.name} = {ep.value}")
print()
# Search for `cli` submodules within huggingface_hub.
import huggingface_hub
pkg_dir = os.path.dirname(huggingface_hub.__file__)
print("=== huggingface_hub submodules (top-level only) ===")
for entry in sorted(os.listdir(pkg_dir)):
    full = os.path.join(pkg_dir, entry)
    if entry.startswith("_"):
        continue
    print(" ", entry)
