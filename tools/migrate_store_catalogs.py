"""
ONE-OFF migration (already run; kept as a record): moves what Homesteader/Assets/Resources/StoreCatalogs.json knew about each
shop item INTO the item's own manifest, so the asset manifests are the single source and the phone builds every shop from the
catalog. After this, StoreCatalogs.json and the scripts that built it are gone.

Per item it writes, under `properties`:
  is_buyable      true
  base_value      the shop price (the shop price won over a differing manifest value)
  stores          the shops that sell it: lumber, depot, grocer, feed, water, vehicles, equipment, livestock, furniture,
                  voltvision, trailershack
  sale_unit       ea / kit / box / bale ... (how the shop counts it)
  store_category  only when the shop's chip label differs from the category default (see CATEGORY_LABELS)
  store_overrides only for an item sold by several shops with a different category, unit or PRICE in one of them:
                  {"trailershack": {"category": "Trailer Repair", "unit": "ea", "price": 165}}
Entries whose id has no manifest (the 21 stump_* lumber entries) are dropped; the manifest name, description and icon win over the
shop copy (13 shop-only marketing names are lost).
"""
import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STORE = os.path.join(ROOT, 'Homesteader', 'Assets', 'Resources', 'StoreCatalogs.json')

# The chip label a shop shows for an item of each asset category (also used by tools/generate_unity_asset_catalog.py)
CATEGORY_LABELS = {
    'appliances': 'Appliances', 'building': 'Building', 'electricity': 'Electronics', 'farming': 'Farming', 'food': 'Food',
    'fuel': 'Fuel', 'ingredients': 'Ingredients', 'internet': 'Telecom', 'logging': 'Logging', 'materials': 'Materials',
    'ranching': 'Ranching', 'structures': 'Structures', 'tools': 'Tools', 'vehicles': 'Vehicles',
}


LF = chr(10)
CRLF = chr(13) + chr(10)


def main():
    store = json.load(open(STORE, encoding='utf-8'))
    manifests = {}
    for f in glob.glob(os.path.join(ROOT, 'assets', '*', '*', '*.json')):
        parts = f.split(os.sep)
        if parts[-3].startswith('_') or os.path.splitext(parts[-1])[0] != parts[-2]:
            continue
        try:
            d = json.load(open(f, encoding='utf-8'))
        except Exception:
            continue
        if isinstance(d, dict) and d.get('id') and isinstance(d.get('properties'), dict):
            manifests[d['id']] = (f, d, parts[-3])

    listings = {}   # id -> [(store, entry)]
    dropped = []
    for sname, items in store.items():
        for it in items:
            if it['id'] not in manifests:
                dropped.append((sname, it['id']))
                continue
            listings.setdefault(it['id'], []).append((sname, it))

    conflicts = []
    for item_id, rows in listings.items():
        f, d, cat = manifests[item_id]
        props = d['properties']
        price = float(rows[0][1]['price'])
        if any(abs(float(r[1]['price']) - price) > 0.001 for r in rows):
            conflicts.append((item_id, [(s, e['price']) for s, e in rows]))
        props['is_buyable'] = True
        props['base_value'] = int(price) if price.is_integer() else price
        props['stores'] = [s for s, _ in rows]
        first = rows[0][1]
        props['sale_unit'] = first.get('unit') or 'ea'
        default_label = CATEGORY_LABELS.get(cat, cat.title())
        if first['category'] != default_label:
            props['store_category'] = first['category']
        else:
            props.pop('store_category', None)
        overrides = {}
        for s, e in rows[1:]:
            ov = {}
            label = e['category']
            if label != props.get('store_category', default_label):
                ov['category'] = label
            if (e.get('unit') or 'ea') != props['sale_unit']:
                ov['unit'] = e.get('unit') or 'ea'
            if abs(float(e['price']) - price) > 0.001:
                ov['price'] = int(float(e['price'])) if float(e['price']).is_integer() else float(e['price'])   # a shop that charges its own price
            if ov:
                overrides[s] = ov
        if overrides:
            props['store_overrides'] = overrides
        else:
            props.pop('store_overrides', None)
        raw = open(f, encoding='utf-8', newline='').read()
        nl = CRLF if CRLF in raw else LF
        text = json.dumps(d, indent=2, ensure_ascii=not any(ord(c) > 127 for c in raw))
        if raw.endswith(LF):
            text += LF
        with open(f, 'w', encoding='utf-8', newline='') as fh:
            fh.write(text.replace(LF, nl))

    print('items migrated:', len(listings))
    print('dropped (no manifest):', len(dropped))
    print('shops with their own price (kept as store_overrides.price):', len(conflicts))


if __name__ == '__main__':
    sys.exit(main())
