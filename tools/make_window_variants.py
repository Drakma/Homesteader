"""
Makes the muntin VARIANTS of the window items (assets/building/building_window_<type>_<pattern>): the bars are part of the window you buy, and a window is changed by clicking a window of the
building with a different one in hand (it is swapped). The base items (building_window_double_hung, _picture, _slider) are the FOUR-pane window (a cross); the variants are the plain window and
the two, six and eight pane ones, each a copy of its base (same model, icon, price) with its own id and name.

    python tools/make_window_variants.py
    python tools/generate_unity_asset_catalog.py ; python tools/package_catalog_as_mods.py

The patterns and suffixes must match Assets/Scripts/Growth/StructureWindows.cs (MuntinGrid, PatternSuffix).
"""
import json
import os
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(ROOT, 'assets', 'building')
BASES = ('building_window_double_hung', 'building_window_picture', 'building_window_slider')
# pattern index -> (id suffix, label); 2, the cross (four panes), is the base item itself
PATTERNS = {
    0: ('_plain', 'Plain'),
    1: ('_panes2', 'Two Panes'),
    3: ('_panes6', 'Six Panes'),
    4: ('_panes8', 'Eight Panes'),
}
BASE_LABEL = 'Four Panes'


def write_json(path, data):
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write('\n')


def main():
    made = 0
    for base in BASES:
        src = os.path.join(BUILD, base)
        m0 = json.load(open(os.path.join(src, base + '.json'), encoding='utf-8'))
        kind = m0['name'].split(',')[0]
        if not m0['name'].endswith(BASE_LABEL):                        # the base item is the four-pane window: its name says so
            m0['name'] = '%s, %s' % (kind, BASE_LABEL)
            m0['description'] = m0['description'].split(' Its muntins')[0]
            write_json(os.path.join(src, base + '.json'), m0)
        with open(os.path.join(src, 'README.md'), 'w', encoding='utf-8', newline='\n') as f:
            f.write('# %s\n\n%s\n' % (m0['name'], m0['description']))
        for idx, (suffix, label) in PATTERNS.items():
            item = base + suffix
            dst = os.path.join(BUILD, item)
            os.makedirs(dst, exist_ok=True)
            for ext in ('.glb', '.png'):
                shutil.copyfile(os.path.join(src, base + ext), os.path.join(dst, item + ext))
            m = json.loads(json.dumps(m0))
            m['id'] = item
            m['name'] = '%s, %s' % (kind, label)
            m['description'] = '%s Its muntins: %s.' % (m0['description'].rstrip(), label.lower())
            m['icon'] = item + '.png'
            for mod in m.get('models', []):
                mod['file'] = item + '.glb'
            write_json(os.path.join(dst, item + '.json'), m)
            with open(os.path.join(dst, 'README.md'), 'w', encoding='utf-8', newline='\n') as f:
                f.write('# %s\n\n%s\n\nA muntin variant of `%s` (tools/make_window_variants.py).\n' % (m['name'], m['description'], base))
            made += 1
    print('%d window variants' % made)


if __name__ == '__main__':
    main()
