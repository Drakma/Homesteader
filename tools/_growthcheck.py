"""Confirm the growth-group namespace gap in the modded oaks."""
import json
import glob
import os

print("=== core oak: how stage references are written ===")
p = "assets/logging/tree_sapling_oak/tree_sapling_oak.json"
d = json.load(open(p, encoding="utf-8"))
g = d["growth"]
print(f"  id={d['id']}  namespace={d.get('namespace')}  qualified={d.get('qualified_id')}")
print(f"  species={g.get('species')}  stages:")
for st in g["stages"]:
    print(f"      stage {st['stage']}: item_id = {st['item_id']}   (bare, no namespace)")

print()
print("=== modded oak: the SAME structure, but namespaced item ids ===")
mp = glob.glob("mods/oak_woodland/assets/logging/*/tree_sapling_oak.json")
if mp:
    m = json.load(open(mp[0], encoding="utf-8"))
    g = m["growth"]
    print(f"  id={m['id']}  namespace={m.get('namespace')}  qualified={m.get('qualified_id')}")
    print(f"  species={g.get('species')}  stages:")
    for st in g["stages"]:
        print(f"      stage {st['stage']}: item_id = {st['item_id']}   (bare -> resolves to CORE)")
else:
    print("  (mod folder not found)")

print()
print("=== the consequence ===")
print("  Core tree_sapling_oak  qualifies as  core:tree_sapling_oak")
print("  Mod  tree_sapling_oak  qualifies as  oak_woodland:tree_sapling_oak")
print("  ...but the mod's growth stages point at bare 'tree_small_oak',")
print("  which the registry resolves to the CORE oak, not the mod's own.")
