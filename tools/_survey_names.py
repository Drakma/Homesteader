import glob
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACKS = ['kitchen', 'living', 'bedroom', 'bathroom', 'laundry', 'garage', 'dining', 'office', 'lighting', 'decor']
for pack in PACKS:
    seen = {}
    for f in sorted(glob.glob(os.path.join(ROOT, 'assets', pack, '*', '*.json'))):
        m = json.load(open(f, encoding='utf-8'))
        piece = re.sub(r'_(classic|modern)_.*$', '', m['id'])
        seen.setdefault(piece, m['name'])
    print('##', pack)
    for k, v in seen.items():
        print('  %-40s %s' % (k, v))
