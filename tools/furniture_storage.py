"""
Storage for the room-pack furniture (kitchen, living, bedroom, bathroom, laundry, garage, dining, office).

One table says what each piece of furniture holds, and every pack generator calls apply() while it writes a manifest; the same function backfills the manifests that
already exist:

    python tools/furniture_storage.py            # patch every manifest under assets/<pack>/ (idempotent), print what changed
    python tools/furniture_storage.py --check    # only report, change nothing

Two kinds of storage (docs/FURNITURE_STORAGE.md):
  CLOSED   drawers, doors and lids: a `container` block (the C key, a weight capacity, contents not drawn). Accepts anything.
  OPEN     real shelves: `support_surface` + `deck_heights` (the top face of every shelf, measured from the model code). Things are PLACED on a shelf (PalletDeck.cs):
           like things stack on each other, but never higher than the shelf above allows.

A piece may be both (a cabinet with a closed lower part and glass shelves above). Wall items are not containers (a mounted thing has no contents window yet).
"""
import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACKS = ('kitchen', 'living', 'bedroom', 'bathroom', 'laundry', 'garage', 'dining', 'office')

# (pack, model) -> capacity in kg, or {style: kg} when only one style has the drawer. The model is the manifest's category_fields `<pack>_kind`.
CONTAINERS = {
    # living
    ('living', 'sideboard'): 60, ('living', 'tv_stand'): 40, ('living', 'toy_chest'): 40, ('living', 'display_cabinet'): 30,
    ('living', 'end_table'): {'classic': 8}, ('living', 'console_table'): {'classic': 10},
    # bedroom
    ('bedroom', 'nightstand'): 15, ('bedroom', 'dresser'): 60, ('bedroom', 'chest_of_drawers'): 50, ('bedroom', 'vanity_table'): 20,
    ('bedroom', 'wardrobe'): 90, ('bedroom', 'blanket_chest'): 40, ('bedroom', 'desk'): 25,
    # bathroom
    ('bathroom', 'vanity_single'): 30, ('bathroom', 'vanity_double'): 50, ('bathroom', 'linen_cabinet'): 30, ('bathroom', 'hamper'): 12,
    # laundry
    ('laundry', 'locker_unit'): 60, ('laundry', 'folding_counter'): 30, ('laundry', 'laundry_basket'): 12, ('laundry', 'sorter_hamper'): 15,
    # garage
    ('garage', 'cabinet_base'): 60, ('garage', 'cabinet_tall'): 90, ('garage', 'parts_cabinet'): 25, ('garage', 'tool_chest_rolling'): 70,
    ('garage', 'tool_chest_top'): 25,
    # dining
    ('dining', 'china_cabinet'): 35,
    # office
    ('office', 'office_desk'): 25, ('office', 'executive_desk'): 40, ('office', 'credenza'): 60, ('office', 'filing_cabinet'): 40, ('office', 'lateral_file'): 55,
}
# kitchen manifests only say 'cabinet' / 'appliance', so they are picked by id prefix (id startswith -> kg). The rest of the kitchen already has its own container block.
KITCHEN_CONTAINERS = {'kitchen_sink_': 30}

# (pack, model) -> top face of every shelf in metres, lowest first; {style: '...'} where classic and modern differ. Measured from tools/<pack>_models.py.
DECKS = {
    ('living', 'bookshelf'): {'classic': '0.125,0.525,0.925,1.325,1.705', 'modern': '0.065,0.525,0.925,1.325,1.705'},
    ('living', 'coffee_table'): {'classic': '0.15,0.45', 'modern': '0.185,0.45'},
    ('living', 'display_cabinet'): '0.812,1.132,1.452',
    ('dining', 'china_cabinet'): '0.93,1.232,1.532,1.832',
    ('dining', 'bar_cart'): '0.21,0.57,0.85',
    ('dining', 'wine_rack'): '0.02,0.32,0.61,0.90,1.20',
    ('laundry', 'shelf_unit'): '0.225,0.645,1.065,1.485,1.80',
    ('laundry', 'shoe_rack'): '0.10,0.28,0.46',
    ('laundry', 'boot_bench'): {'classic': '0.17,0.50', 'modern': '0.16,0.46'},
    ('garage', 'steel_shelving'): '0.15,0.63,1.11,1.59,1.90',
    ('garage', 'workbench'): {'classic': '0.20,0.92', 'modern': '0.23,0.92'},
}
KITCHEN_DECKS = {'kitchen_cart_': '0.23,0.88'}
# kitchen floor cabinets and appliances that form a RUN: they snap to each other and the wall, with filler strips (properties.run_snap, Growth/KitchenRun.cs)
KITCHEN_RUN = ('kitchen_base_cab_', 'kitchen_corner_base_', 'kitchen_sink_', 'kitchen_dishwasher_', 'kitchen_range_white', 'kitchen_range_black', 'kitchen_range_stainless',
               'kitchen_oven_tower_', 'kitchen_pantry_', 'kitchen_fridge_', 'kitchen_freezer_upright_', 'kitchen_work_counter_')
# wall items that are shelves (a single top face, docs/ATTACHED_ITEMS.md)
KITCHEN_SHELF = ('kitchen_spice_rack_',)


def _pick(v, style):
    if isinstance(v, dict):
        return v.get(style)
    return v


def apply(man, pack, model, style=None):
    """Set the storage fields of one manifest from the table. Returns True when it changed anything."""
    before = json.dumps(man, sort_keys=True)
    mid = man.get('id', '')
    props = man.setdefault('properties', {})

    kg = _pick(CONTAINERS.get((pack, model)), style)
    if pack == 'kitchen':
        for pre, v in KITCHEN_CONTAINERS.items():
            if mid.startswith(pre):
                kg = v
    if kg and not props.get('attach_surface'):
        old = man.get('container') or {}
        blk = {'capacity_kg': kg, 'accepts': list(old.get('accepts', [])), 'show_fill': False}
        if old.get('stacking_limit'):
            blk['stacking_limit'] = old['stacking_limit']
        man['container'] = blk

    decks = _pick(DECKS.get((pack, model)), style)
    if pack == 'kitchen':
        for pre, v in KITCHEN_DECKS.items():
            if mid.startswith(pre):
                decks = v
    if decks:
        props['support_surface'] = True
        props['deck_heights'] = decks

    if pack == 'kitchen' and any(mid.startswith(p) for p in KITCHEN_SHELF):
        props['shelf'] = True
    if pack == 'kitchen' and any(mid.startswith(p) for p in KITCHEN_RUN):
        props['run_snap'] = True
    return json.dumps(man, sort_keys=True) != before


def kind_of(man):
    for k, v in man.get('category_fields', {}).items():
        if k.endswith('_kind'):
            return v
    return None


def backfill(write=True):
    changed = 0
    seen = set()
    for pack in PACKS:
        for f in sorted(glob.glob(os.path.join(ROOT, 'assets', pack, '*', '*.json'))):
            with open(f, encoding='utf-8') as fh:
                man = json.load(fh)
            model = kind_of(man)
            style = man.get('category_fields', {}).get('style')
            seen.add((pack, model))
            if apply(man, pack, model, style):
                changed += 1
                if write:
                    with open(f, 'w', encoding='utf-8', newline='\n') as fh:
                        json.dump(man, fh, indent=2, ensure_ascii=False)
                        fh.write('\n')
    for key in list(CONTAINERS) + list(DECKS):
        if key not in seen:
            print('WARNING: no manifest has the model', key)
    return changed


def main():
    n = backfill(write='--check' not in sys.argv)
    print('%d manifest(s) %s' % (n, 'would change' if '--check' in sys.argv else 'updated'))


if __name__ == '__main__':
    main()
