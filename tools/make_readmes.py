"""
Writes the missing README.md of every item folder (assets/<category>/<id>/) from its own manifest, in the same layout as the other READMEs: overview, description, model, properties,
category fields, growth stages, utilities and the files in the folder. A README that exists is never touched. No emoji.

    python tools/make_readmes.py            (write the missing ones)
    python tools/make_readmes.py --list     (only list them)
"""
import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, 'assets')
NL = chr(10)
SKIP_FIELDS = {'dimensions_m', 'dimensions_cm'}
UTIL_ROWS = (('water', 'Water'), ('electricity', 'Electricity'), ('sewage', 'Sewage / Waste'), ('battery', 'Battery Power'), ('internet', 'Internet / Data'))


def num(v, nd=2):
    if isinstance(v, float):
        return ('%.*f' % (nd, v)).rstrip('0').rstrip('.')
    return str(v)


def scalar_lines(d, skip=()):
    out = []
    for k, v in d.items():
        if k in skip or k in SKIP_FIELDS:
            continue
        if isinstance(v, (str, int, float, bool)) and v != '':
            out.append('- **%s**: `%s`' % (k.replace('_', ' ').capitalize(), num(v)))
        elif isinstance(v, list) and v and all(isinstance(x, (str, int, float)) for x in v):
            out.append('- **%s**: %s' % (k.replace('_', ' ').capitalize(), ', '.join('`%s`' % x for x in v)))
    return out


def readme(m, folder):
    iid = m.get('id') or os.path.basename(folder)
    name = m.get('name') or iid
    cat = m.get('category') or os.path.basename(os.path.dirname(folder))
    p = m.get('properties') or {}
    cf = m.get('category_fields') or {}
    files = sorted(f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f)) and f != 'README.md')
    o = ['# %s (`%s`)' % (name, iid), '']
    icon = m.get('icon') if m.get('icon') in files else (iid + '.png' if iid + '.png' in files else None)
    if icon:
        o += ['![%s Icon](%s)' % (name, icon), '']
    o += ['## Overview', '- **Category**: `%s`' % cat, '- **Item Identifier**: `%s`' % iid]
    if 'max_stack_size' in p:
        o.append('- **Max Stack Size**: %s' % p['max_stack_size'])
    if 'weight_kg' in p:
        o.append('- **Weight**: %s kg' % num(p['weight_kg']))
    if 'base_value' in p:
        o.append('- **Base Economic Value**: $%s' % num(p['base_value']))
    if 'is_consumable' in p:
        o.append('- **Consumable**: %s' % p['is_consumable'])
    o += ['', '## Description', m.get('description') or 'No description yet.', '']

    models = [x for x in (m.get('models') or []) if isinstance(x, dict)]
    dims = None
    for x in models:
        if x.get('dimensions_m'):
            dims = x['dimensions_m']
            break
    dims = dims or cf.get('dimensions_m')
    if models or dims:
        o.append('## 3D Model')
        if dims:
            vals = [dims.get(k) for k in (('x', 'y', 'z') if 'x' in dims else ('width', 'depth', 'height'))]
            if all(v is not None for v in vals):
                o.append('- **Dimensions (m)**: `%s x %s x %s`' % tuple(num(v, 3) for v in vals))
        for x in models:
            if x.get('format') in ('glb', 'fbx', 'obj'):
                tri = ', %s triangles' % x['triangles'] if x.get('triangles') else ''
                o.append('- **Model**: `%s` (%s%s)' % (x.get('file'), x['format'].upper(), tri))
        o += ['- **Scale**: metric, 1 unit = 1 m. Ground-level pivot for placed things, centred pivot for handheld ones.', '']

    extra = scalar_lines(p, skip={'weight_kg', 'max_stack_size', 'base_value', 'is_consumable', 'footprint'})
    if extra:
        o += ['## Properties'] + extra + ['']
    cfl = scalar_lines(cf)
    if cfl:
        o += ['## Category Fields'] + cfl + ['']
    if isinstance(m.get('container'), dict):
        o += ['## Container'] + scalar_lines(m['container']) + ['']
    if isinstance(m.get('liquid_container'), dict):
        o += ['## Liquid Container'] + scalar_lines(m['liquid_container']) + ['']

    g = m.get('growth')
    if isinstance(g, dict) and (g.get('stages') or g.get('growth_type')):
        o += ['## Growth', '- **Type**: `%s`' % g.get('growth_type'), '- **Species**: `%s`' % g.get('species', iid)]
        if g.get('max_age'):
            o.append('- **Full age**: %s %s' % (g['max_age'], g.get('time_unit', 'days')))
        rules = g.get('rules') or {}
        y = rules.get('yield') or {}
        if y.get('item_id'):
            o.append('- **Yield**: %s to %s `%s` at stage %s' % (y.get('amount_min', 1), y.get('amount_max', 1), y['item_id'], y.get('harvest_stage', '?')))
        pl = rules.get('planting') or {}
        if pl.get('seasons'):
            o.append('- **Planting**: %s; seed `%s`' % (', '.join(pl['seasons']), pl.get('item_id', '')))
        stages = [s for s in (g.get('stages') or []) if isinstance(s, dict)]
        if stages:
            o += ['', '| Stage | Name | Age range |', '| :--- | :--- | :--- |']
            for s in stages:
                o.append('| %s | %s | %s to %s |' % (s.get('stage'), s.get('name'), s.get('age_min', ''), s.get('age_max', '')))
        o.append('')

    u = m.get('utilities') or {}
    if u:
        o += ['## Utilities', '| Utility System | Usage / Output Metric | Operational Details |', '| :--- | :--- | :--- |']
        for key, label in UTIL_ROWS:
            row = u.get(key) or {}
            o.append('| **%s** | `%s` | %s |' % (label, row.get('metric', 'None'), row.get('details', 'None')))
        o.append('')

    o += ['## Asset Files']
    for f in files:
        label = {'json': 'Plugin Manifest (JSON)', 'png': 'Icon (PNG)', 'glb': '3D Model (GLB)', 'fbx': '3D Model (FBX)', 'obj': '3D Mesh (OBJ)', 'mtl': '3D Material (MTL)'}.get(f.rsplit('.', 1)[-1].lower(), 'File')
        o.append('- **%s**: [%s](%s)' % (label, f, f))
    return NL.join(o) + NL


def main():
    listing = '--list' in sys.argv
    made = []
    for p in sorted(glob.glob(os.path.join(ASSETS, '*', '*', '*.json'))):
        folder = os.path.dirname(p)
        rel = os.path.relpath(p, ASSETS).split(os.sep)
        if rel[0].startswith('_') or os.path.basename(p)[:-5] != rel[1]:
            continue
        rp = os.path.join(folder, 'README.md')
        if os.path.exists(rp):
            continue
        try:
            with open(p, encoding='utf-8') as f:
                m = json.load(f)
        except Exception:
            continue
        if not isinstance(m, dict):
            continue
        made.append(rel[1])
        if not listing:
            with open(rp, 'w', encoding='utf-8', newline=NL) as f:
                f.write(readme(m, folder))
    print(('would write' if listing else 'wrote'), len(made), 'README.md file(s)')


if __name__ == '__main__':
    main()
