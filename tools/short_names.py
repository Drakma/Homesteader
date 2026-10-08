"""
Short display names for the catalog (the room packs above all) and the cabinets' Upper / Lower labels.

    python tools/short_names.py            # rename every item manifest (and the title line of its README.md), print what changed
    python tools/short_names.py --check    # only list what would change, and any two items of one category that would end up with the same name

The names are display names only (ids, recipes, saves and shop listings use ids). Every pack generator calls apply() while it writes a manifest, so a regeneration keeps the short
names; lighting and decor have no such hook yet (run this script after them). Rules are applied in order, longest phrase first, and are safe to run again.
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

RULES = [
    # cabinets: lower (on the floor) and upper (on the wall)
    ('Kitchen Sink Cabinet', 'Lower Sink Cabinet'),
    ('Double-Door Base Cabinet', 'Wide Lower Cabinet'),
    ('Double-Door Wall Cabinet', 'Wide Upper Cabinet'),
    ('Glass-Door Wall Cabinet', 'Glass Upper Cabinet'),
    ('Drawer Base Cabinet', 'Drawer Lower Cabinet'),
    ('Corner Base Cabinet', 'Corner Lower Cabinet'),
    ('Slim Base Cabinet', 'Slim Lower Cabinet'),
    ('Slim Wall Cabinet', 'Slim Upper Cabinet'),
    ('Laundry Wall Cabinet', 'Upper Cabinet'),
    ('Steel Wall Cabinet', 'Upper Cabinet'),
    ('Steel Base Cabinet', 'Lower Cabinet'),
    ('Tall Steel Cabinet', 'Tall Cabinet'),
    ('Base Cabinet', 'Lower Cabinet'),
    ('Wall Cabinet', 'Upper Cabinet'),
    ('Pantry Cabinet', 'Pantry'),
    # finishes
    ('Stainless Steel', 'Steel'), ('Polished Chrome', 'Chrome'), ('Antique Brass', 'Brass'), ('Oiled Bronze', 'Bronze'), ('Brushed Nickel', 'Nickel'),
    ('Matte Black', 'Black'), ('Black Iron', 'Iron'), ('Safety Orange', 'Orange'), ('Forest Green', 'Green'),
    # kitchen
    ('Side-by-Side Refrigerator', 'Side Fridge'), ('French-Door Refrigerator', 'French Fridge'), ('Top-Freezer Refrigerator', 'Top Fridge'), ('Refrigerator', 'Fridge'),
    ('Over-The-Range Microwave', 'OTR Microwave'), ('Countertop Microwave', 'Microwave'), ('Countertop ', ''), ('Built-In Cooktop', 'Cooktop'),
    ('Drip Coffee Maker', 'Coffee Maker'), ('Electric Kettle', 'Kettle'), ('Double Wall Oven Tower', 'Oven Tower'), ('Step Trash Can', 'Trash Can'),
    ('Paper Towel Holder', 'Towel Holder'), ('Canister Set', 'Canisters'), ('Kitchen Bench', 'Bench'), ('Kitchen Cart', 'Cart'), ('Kitchen Island', 'Island'),
    ('Open Kitchen Shelf', 'Open Shelf'), ('Round Pedestal Table', 'Round Table'), ('Counter Stool', 'Stool'), ('Dish Drying Rack', 'Dish Rack'),
    ('Hanging Pot Rack', 'Pot Rack'), ('Cast-Iron Skillet', 'Skillet'), ('Drinking Glass', 'Glass'),
    # living
    ('Sectional Sofa', 'Sectional'), ('Rocking Chair', 'Rocker'), ('Television', 'TV'), ('Large Wall-Mount TV', 'Large Wall TV'), ('Wall-Mount TV', 'Wall TV'),
    ('Framed Picture', 'Picture'), ('Potted Plant', 'Plant'), ('Floor Pouf', 'Pouf'),
    # bedroom
    ('Chest Of Drawers', 'Chest'), ('Baby Crib', 'Crib'), ('Bed-End Bench', 'End Bench'), ('Dressing Table', 'Vanity'), ('Writing Desk', 'Desk'),
    # bathroom
    ('Soap and Toothbrush Set', 'Soap Set'), ('Toilet Paper Holder', 'TP Holder'), ('Robe Hook Rail', 'Hook Rail'), ('Laundry Hamper', 'Hamper'),
    ('Alcove Bathtub', 'Alcove Tub'), ('Freestanding Bathtub', 'Freestanding Tub'), ('Bathroom Mirror', 'Bath Mirror'),
    # laundry
    ('Mudroom Lockers', 'Lockers'), ('Mudroom Bench', 'Mud Bench'), ('Storage Shelves', 'Shelves'), ('Laundry Basket', 'Basket'), ('Laundry Sorter', 'Sorter'),
    # garage
    ('Pegboard Wall Panel', 'Pegboard'), ('Rolling Tool Chest', 'Tool Chest'), ('Top Tool Chest', 'Top Chest'), ('Steel Shelving Unit', 'Shelving'),
    # dining, office
    ('Round Dining Table', 'Round Table'), ('Cork Board', 'Corkboard'),
    # lighting
    ('Flush-Mount Ceiling Light', 'Flush Light'), ('Ceiling Fan With Light', 'Ceiling Fan'), ('Garden Bollard Light', 'Bollard'), ('Security Flood Light', 'Flood Light'),
    ('Yard Pole Light', 'Pole Light'), ('Garden Post Lamp', 'Post Lamp'), ('Swing-Arm Wall Lamp', 'Swing Lamp'), ('Exterior Wall Lantern', 'Wall Lantern'),
    ('Vanity Light Bar', 'Vanity Bar'), ('Wall Sconce', 'Sconce'), ('Pendant Light', 'Pendant'),
    # decor
    (' Pot ', ' '), ('Succulent Pot', 'Succulent'),
    # colours, and the building stacks
    ('Camel Leather', 'Camel'), ('Sage Green', 'Sage'),
    ('Corrugated Steel Wall Siding', 'Steel Siding'), ('Corrugated Steel Roofing', 'Steel Roofing'),
]
REGEX_RULES = [(r'Standing Seam (\w+) Metal Roofing', r'\1 Seam Roofing')]


def shorten(name):
    out = name
    for old, new in RULES:
        out = out.replace(old, new)
    for pat, rep in REGEX_RULES:
        out = re.sub(pat, rep, out)
    out = re.sub(r'\s*\((?:Meshy|own icon)[^)]*\)', '', out)   # dev notes that ended up in a name
    return re.sub(r'\s+', ' ', out).strip()


def apply(man):
    """Shorten the display name of one manifest. Returns True when it changed."""
    new = shorten(man.get('name', ''))
    if new and new != man.get('name'):
        man['name'] = new
        return True
    return False


def main():
    check = '--check' in sys.argv
    changed = 0
    names = {}
    for f in sorted(glob.glob(os.path.join(ROOT, 'assets', '*', '*', '*.json'))):
        if True:
            if os.sep + '_' in f[len(ROOT):]:
                continue
            raw = open(f, encoding='utf-8', newline='').read()
            try:
                man = json.loads(raw)
            except ValueError:
                continue
            if not isinstance(man, dict) or 'properties' not in man or 'name' not in man:
                continue
            old = man.get('name', '')
            if apply(man):
                changed += 1
                if not check:
                    nl = '\r\n' if '\r\n' in raw else '\n'
                    out = json.dumps(man, indent=2, ensure_ascii=False) + '\n'
                    open(f, 'w', encoding='utf-8', newline='').write(out.replace('\n', nl) if nl == '\r\n' else out)
                    rd = os.path.join(os.path.dirname(f), 'README.md')
                    if os.path.exists(rd):
                        text = open(rd, encoding='utf-8', newline='').read()
                        head = '# ' + old
                        if text.startswith(head):
                            open(rd, 'w', encoding='utf-8', newline='').write('# ' + man['name'] + text[len(head):])
            names.setdefault((man.get('category'), man['name']), []).append(man['id'])
    print('%d name(s) %s' % (changed, 'would change' if check else 'changed'))
    for (cat, name), ids in names.items():
        if len(ids) > 1:
            print('DUPLICATE in %s: "%s" -> %s' % (cat, name, ', '.join(ids[:4])))


if __name__ == '__main__':
    main()
