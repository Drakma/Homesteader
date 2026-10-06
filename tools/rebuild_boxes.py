#!/usr/bin/env python3
"""
Rebuilds the cardboard boxes of the building materials as TEXTURED single-mesh boxes: the name of what is in them printed on the sides, a colour band and a white
label, a taped seam across the top, all in the texture (tools/box_textures.py) instead of extra blocks on the model.

    python tools/rebuild_boxes.py

For each box: draws its atlas, builds the GLB (tools/make_box_models.py in Blender), updates the manifest's model entry and dimensions, renders the icon.
Run tools/generate_unity_asset_catalog.py and tools/package_catalog_as_mods.py afterwards.
"""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import box_textures  # noqa: E402

BUILD = os.path.join(ROOT, 'assets', 'building')
TMP = os.path.join(ROOT, 'assets', '_scratch', 'box_textures')

# id, the common name printed on the sides, (no small line), band colour, width x depth x height in metres
BOXES = [
    ('building_roofing_nails_box', 'Roofing Nails', None, (0.85, 0.2, 0.15), (0.2, 0.12, 0.1)),
    ('anchor_bolts_case_10', 'Anchor Bolts', None, (0.2, 0.3, 0.55), (0.25, 0.14, 0.1)),
    ('joist_hangers_case_10', 'Joist Hangers', None, (0.35, 0.35, 0.38), (0.25, 0.16, 0.12)),
    ('hurricane_ties_case_10', 'Hurricane Ties', None, (0.5, 0.3, 0.15), (0.22, 0.14, 0.1)),
    ('building_roofing_nails_case', 'Roofing Nails', None, (0.85, 0.2, 0.15), (0.42, 0.24, 0.22)),
    ('anchor_bolts_case_20', 'Anchor Bolts', None, (0.2, 0.3, 0.55), (0.5, 0.28, 0.22)),
    ('joist_hangers_case_20', 'Joist Hangers', None, (0.35, 0.35, 0.38), (0.5, 0.32, 0.26)),
    ('hurricane_ties_case_20', 'Hurricane Ties', None, (0.5, 0.3, 0.15), (0.44, 0.28, 0.22)),
    ('lag_bolts_case_10', 'Lag Bolts', None, (0.45, 0.3, 0.55), (0.25, 0.14, 0.1)),
    ('lag_bolts_case_20', 'Lag Bolts', None, (0.45, 0.3, 0.55), (0.5, 0.28, 0.22)),
    ('framing_nails_case_10', 'Framing Nails', None, (0.85, 0.5, 0.1), (0.25, 0.14, 0.1)),
    ('finishing_nails_case_10', 'Finishing Nails', None, (0.1, 0.5, 0.5), (0.25, 0.14, 0.1)),
    ('deck_screws_case_10', 'Deck Screws', None, (0.2, 0.5, 0.25), (0.25, 0.14, 0.1)),
    ('framing_nails_case_20', 'Framing Nails', None, (0.85, 0.5, 0.1), (0.5, 0.28, 0.22)),
    ('finishing_nails_case_20', 'Finishing Nails', None, (0.1, 0.5, 0.5), (0.5, 0.28, 0.22)),
    ('deck_screws_case_20', 'Deck Screws', None, (0.2, 0.5, 0.25), (0.5, 0.28, 0.22)),
]


def main():
    os.makedirs(TMP, exist_ok=True)
    spec = []
    for item_id, name, note, band, (w, d, h) in BOXES:
        folder = os.path.join(BUILD, item_id)
        if not os.path.isdir(folder):
            print('skip (no folder):', item_id)
            continue
        atlas = os.path.join(TMP, item_id + '.png')
        box_textures.make_atlas(dict(w=w, d=d, h=h, name=name, note=note, band=band)).save(atlas)
        spec.append(dict(id=item_id, folder=folder, w=w, d=d, h=h, atlas=atlas))
    spec_path = os.path.join(TMP, 'spec.json')
    json.dump(spec, open(spec_path, 'w'), indent=1)
    r = subprocess.run(['blender', '-b', '-P', os.path.join(ROOT, 'tools', 'make_box_models.py'), '--', spec_path], capture_output=True, text=True)
    print('\n'.join(l for l in r.stdout.splitlines() if l.startswith('box ')) or r.stdout[-800:] + r.stderr[-800:])
    for it in spec:
        mp = os.path.join(it['folder'], it['id'] + '.json')
        m = json.load(open(mp, encoding='utf-8'))
        m['models'] = [{'file': it['id'] + '.glb', 'format': 'glb', 'dimensions_m': {'x': it['w'], 'y': it['h'], 'z': it['d']}, 'triangles': 12}]
        m.setdefault('category_fields', {})['dimensions_m'] = {'width': it['w'], 'depth': it['d'], 'height': it['h']}
        tmp = mp + '.tmp'
        with open(tmp, 'w', encoding='utf-8', newline='\n') as f:
            json.dump(m, f, indent=2)
        os.replace(tmp, mp)
        subprocess.run([sys.executable, os.path.join(ROOT, 'tools', 'render_icon_from_model.py'), os.path.join(it['folder'], it['id'] + '.glb'),
                        os.path.join(it['folder'], it['id'] + '.png')], capture_output=True)
        print('rebuilt', it['id'])


if __name__ == '__main__':
    main()
