# Deploy the cursor set into StreamingAssets/HudKit/cursors so
# CursorManager can read cursors.json and the PNGs at runtime (StreamingAssets
# is readable from a built player, unlike Assets/).
import json
import shutil
from pathlib import Path

ROOT = Path(r'C:\Users\casey\Desktop\Homesteader')
SRC = ROOT / 'assets' / 'hud_kit' / 'cursors'
DST = ROOT / 'Homesteader' / 'Assets' / 'StreamingAssets' / 'HudKit' / 'cursors'

if not SRC.exists():
    raise SystemExit('source cursor dir missing: ' + str(SRC))

if DST.exists():
    shutil.rmtree(DST)
DST.mkdir(parents=True)

count = 0
for variant in ('mono', 'color'):
    src_dir = SRC / variant
    if not src_dir.exists():
        raise SystemExit('missing variant dir: ' + str(src_dir))
    (DST / variant).mkdir(parents=True)
    for png in sorted(src_dir.glob('*.png')):
        shutil.copy2(png, DST / variant / png.name)
        count += 1

# Both manifest shapes ship: cursors.json documents the set for humans, and
# cursors_array.json is the list form Unity's JsonUtility actually binds.
shutil.copy2(SRC / 'cursors.json', DST / 'cursors.json')
array_src = SRC / 'cursors_array.json'
if not array_src.exists():
    raise SystemExit('cursors_array.json missing - run tools/build_pointers.py first')
shutil.copy2(array_src, DST / 'cursors_array.json')

doc = json.loads((SRC / 'cursors.json').read_text(encoding='utf-8'))
print(f'copied {count} PNGs + cursors.json -> {DST}')
print(f'cursors in manifest: {len(doc["cursors"])}')

# Verify every manifest entry actually resolves on disk, so a typo in a path
# fails here rather than as a silent warning at runtime.
missing = []
for name, d in doc['cursors'].items():
    for key in ('mono', 'color'):
        rel = d.get(key)
        if rel and not (DST / rel).exists():
            missing.append(f'{name}.{key} -> {rel}')
if missing:
    print('MISSING FILES REFERENCED BY MANIFEST:')
    for m in missing:
        print('  ', m)
else:
    print('every manifest path verified present on disk')
