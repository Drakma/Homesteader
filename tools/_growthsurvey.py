"""Survey the growth-group structure across the whole catalog."""
import glob
import json
import collections

growable = []
for f in glob.glob("assets/**/*.json", recursive=True):
    try:
        d = json.load(open(f, encoding="utf-8"))
    except Exception:
        continue
    if not isinstance(d, dict):
        continue
    g = d.get("growth")
    if isinstance(g, dict) and g.get("is_growable"):
        growable.append((d.get("id"), g))

print(f"growable items: {len(growable)}")

# Group by (growth_type, species) - that pair is what defines a growth group.
groups = collections.defaultdict(list)
for item_id, g in growable:
    groups[(g.get("growth_type"), g.get("species"))].append((item_id, g))

print(f"distinct growth groups: {len(groups)}\n")

for (gtype, species), members in sorted(groups.items(), key=lambda kv: str(kv[0])):
    sizes = {len(m[1].get("stages") or []) for m in members}
    print(f"  {gtype}/{species}:  {len(members)} item(s)  stage-lists={sorted(sizes)}")
    for item_id, g in sorted(members):
        cur = (g.get("current_stage") or {}).get("name")
        print(f"      {item_id:<30} current={cur:<10} total_stages={g.get('total_stages')}")
        for st in (g.get("stages") or []):
            print(f"           stage {st.get('stage')}: {st.get('name'):<10} -> {st.get('item_id')}")
    print()
