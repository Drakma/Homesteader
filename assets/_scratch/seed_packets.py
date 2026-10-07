import glob, json, os
os.chdir(r'C:\Users\casey\Desktop\Homesteader')
n = 0
for p in sorted(glob.glob('assets/farming/seed_*/seed_*.json')):
    with open(p, encoding='utf-8') as f:
        m = json.load(f)
    props = m.setdefault('properties', {})
    props['units_per_sale'] = 20
    props['max_stack_size'] = 100
    props['weight_kg'] = 0.005
    d = m.get('description', '')
    if '20 seeds' not in d:
        m['description'] = (d.rstrip('.') + '. ' if d else '') + 'A packet holds 20 seeds. Planting a tile uses 4: one in each quarter.'
    with open(p, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(m, f, indent=2, ensure_ascii=False)
        f.write('\n')
    n += 1
print('updated', n)
