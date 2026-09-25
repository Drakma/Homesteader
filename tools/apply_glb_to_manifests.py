"""
Points manifests at the GLB models produced by tools/convert_models_to_glb.py.

For every model recorded as converted in tools/glb_conversion_log.jsonl:
  - the manifest(s) in the model's folder: the models[] entries for that stem (fbx / obj / mtl) are
    replaced by ONE entry {"file": "<stem>.glb", "format": "glb"}
  - a growth group manifest (the model sits in <group>/stages/<stage>/): growth.stages[].model
    becomes <stem>.glb
Originals are left on disk (nothing is deleted); only references change. Re-running is safe.

  python tools/apply_glb_to_manifests.py            # apply
  python tools/apply_glb_to_manifests.py --dry-run  # report only
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG = os.path.join(ROOT, 'tools', 'glb_conversion_log.jsonl')
LEGACY_EXT = ('.fbx', '.obj', '.mtl')


def read(p):
    return open(p, encoding='utf-8', newline='').read()


def write_json(p, raw, data):
    ind = re.search(r'\n([ \t]+)"', raw)
    indent = ind.group(1) if ind else '  '
    open(p, 'w', encoding='utf-8', newline='').write(json.dumps(data, indent=indent, ensure_ascii=False) + ('\n' if raw.endswith('\n') else ''))


def entry_file(m):
    return m.get('file') if isinstance(m, dict) else m


def update_models(data, stem):
    """Replace this stem's legacy entries with a single glb entry. Returns True if changed."""
    models = data.get('models')
    if not isinstance(models, list):
        return False
    glb_name = stem + '.glb'
    out, placed, changed = [], False, False
    for m in models:
        f = entry_file(m) or ''
        s, ext = os.path.splitext(f)
        if s == stem and ext.lower() in LEGACY_EXT:
            changed = True
            if not placed:
                new = dict(m) if isinstance(m, dict) else {}
                new['file'] = glb_name
                new['format'] = 'glb'
                out.append(new if isinstance(m, dict) else {'file': glb_name, 'format': 'glb'})
                placed = True
            continue
        if f == glb_name:
            placed = True
        out.append(m)
    if changed:
        data['models'] = out
    return changed


def main(dry):
    converted = []
    for line in open(LOG, encoding='utf-8'):
        r = json.loads(line)
        if r['status'] == 'ok' and os.path.isfile(r['out']):
            converted.append(r)
    touched = set()
    for r in converted:
        src = r['src']
        folder = os.path.dirname(src)
        stem = os.path.splitext(os.path.basename(src))[0]
        # 1. manifests in the model's own folder
        for f in os.listdir(folder):
            if not f.endswith('.json'):
                continue
            p = os.path.join(folder, f)
            raw = read(p)
            try:
                data = json.loads(raw)
            except Exception:
                continue
            if isinstance(data, dict) and update_models(data, stem):
                touched.add(p)
                if not dry:
                    write_json(p, raw, data)
        # 2. growth group manifest above a stages/<stage>/ folder
        parts = folder.replace('\\', '/').split('/')
        if 'stages' in parts:
            gi = parts.index('stages')
            group_dir = '/'.join(parts[:gi])
            group_id = parts[gi - 1]
            gp = os.path.join(group_dir, group_id + '.json')
            if os.path.isfile(gp):
                raw = read(gp)
                data = json.loads(raw)
                changed = False
                for st in ((data.get('growth') or {}).get('stages') or []):
                    if st.get('model') == os.path.basename(src):
                        st['model'] = stem + '.glb'
                        changed = True
                if changed:
                    touched.add(gp)
                    if not dry:
                        write_json(gp, raw, data)
    print(('would update' if dry else 'updated'), len(touched), 'manifest file(s) for', len(converted), 'converted model(s)')


if __name__ == '__main__':
    main('--dry-run' in sys.argv)
