"""How many item READMEs disagree with their own JSON growth data?"""
import json
import glob
import os
import re

mismatch = []
checked = 0

for jp in glob.glob("assets/**/*.json", recursive=True):
    try:
        d = json.load(open(jp, encoding="utf-8"))
    except Exception:
        continue
    if not isinstance(d, dict):
        continue
    g = d.get("growth")
    if not isinstance(g, dict) or not g.get("is_growable"):
        continue

    rp = os.path.join(os.path.dirname(jp), "README.md")
    if not os.path.exists(rp):
        continue
    checked += 1

    readme = open(rp, encoding="utf-8").read()
    real_ids = [st.get("item_id") for st in (g.get("stages") or []) if st.get("item_id")]

    missing = [i for i in real_ids if i and i not in readme]
    if missing:
        mismatch.append((d.get("id"), missing))

print(f"growable items with a README: {checked}")
print(f"READMEs that do NOT contain the real stage ids: {len(mismatch)}\n")
for item_id, missing in mismatch[:25]:
    print(f"  {item_id:<26} README is missing: {missing}")
if len(mismatch) > 25:
    print(f"  ... and {len(mismatch) - 25} more")
