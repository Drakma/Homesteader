"""
The duplicate checker: lists the items that look like the same thing twice. The same rules as the asset kit's own check (computeDuplicates in
assets/index.html), so the two agree:

    python tools/find_duplicates.py

Two items are flagged when
  1. they SHOW the same name, or
  2. one's id is the other's id without its category prefix (an unprefixed relic), or
  3. their ids are the same once the category prefix is taken off.

The name compared is the name the game and the kit SHOW, not the stored one (shown_name below; HudBindings.GetDisplayName, shownName in the kit):
the stored plain name plus what is generated from the item's data: a pack's quantity ("x10"), a liquid container's capacity ("(5 L)"), a
material's weight ("(9 kg)"), a power source's rated power ("(10 kW)") and a breaker's rated current ("(32 A)"). So "Standby Generator" at 10 kW and at 28 kW are different things,
and a stored name never needs to carry a quantity, a capacity or a wattage (user rule).
"""
import os
import re
import sys
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'assets'))
from build_kit import collect_all_items  # noqa: E402

PREFIXES = [
    'electricity_', 'electric_', 'water_', 'waste_', 'sewage_', 'net_', 'internet_',
    'animal_fish_', 'ingredient_fillet_', 'fishing_', 'machinery_', 'struct_', 'tool_',
    'seed_', 'crop_', 'food_', 'ingredient_', 'mat_bale_', 'mat_pelt_', 'mat_wool_', 'mat_',
    'tree_', 'tile_', 'clutter_', 'hud_', 'building_', 'fuel_'
]
LIFECYCLE = ('seed_', 'crop_', 'food_', 'ingredient_')


def number(v):
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else 0.0


def shown_name(it):
    """The name the game shows: keep in step with shownName (assets/index.html) and HudBindings.GetDisplayName."""
    p = it.get('properties') or {}
    manifest = it.get('manifest') or {}
    out = str(it.get('name') or '')
    if number(p.get('pack_quantity')) > 1:
        out += ' x%d' % p['pack_quantity']
    watts = number((manifest.get('category_fields') or {}).get('max_power_w'))
    if watts > 0:
        out += ' (%s)' % ('%g kW' % (round(watts / 100) / 10) if watts >= 1000 else '%d W' % round(watts))
    amps = number((manifest.get('category_fields') or {}).get('max_current_a'))
    if amps > 0:
        out += ' (%g A)' % (round(amps * 10) / 10)
    liters = number((manifest.get('liquid_container') or {}).get('capacity_l'))
    if liters > 0:
        return out + ' (%g L)' % liters
    kg = number(p.get('weight_kg'))
    if p.get('display_weight') is True and kg > 0:
        out += ' (%s kg)' % (str(round(kg)) if kg >= 10 else '%g' % (round(kg * 10) / 10))
    return out


def clean_stem(item_id):
    cur = item_id.lower()
    for p in PREFIXES:
        if cur.startswith(p):
            cur = cur[len(p):]
            break
    return cur.strip('_')


def find(items):
    dups, clusters = set(), defaultdict(list)
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            a, b = items[i], items[j]
            sp_a, sp_b = (a.get('growth') or {}).get('species'), (b.get('growth') or {}).get('species')
            if sp_a and sp_b and sp_a == sp_b:                       # two stages of one species
                continue
            life = lambda x: x.startswith(LIFECYCLE + ('tree_', 'plantable_'))
            if (sp_a and sp_a == a['id'] and life(b['id'])) or (sp_b and sp_b == b['id'] and life(a['id'])):   # the plant, and its seed or harvest
                continue
            if (a['id'].startswith('animal_fish_') and b['id'].startswith('ingredient_fillet_')) or \
               (b['id'].startswith('animal_fish_') and a['id'].startswith('ingredient_fillet_')):
                continue
            if a['id'].startswith(LIFECYCLE) and b['id'].startswith(LIFECYCLE) and a['name'].lower() != b['name'].lower():
                continue
            if (a['id'].startswith('tree_') and b['id'].startswith('food_')) or (b['id'].startswith('tree_') and a['id'].startswith('food_')):
                continue
            norm_a = re.sub(r'[^a-z0-9]', '', shown_name(a).lower())
            norm_b = re.sub(r'[^a-z0-9]', '', shown_name(b).lower())
            stem_a, stem_b = clean_stem(a['id']), clean_stem(b['id'])
            reason = ''
            if norm_a and norm_a == norm_b:
                reason = 'same shown name: ' + shown_name(a)
            elif (a['id'] == stem_b and not a['id'].startswith(tuple(PREFIXES))) or (b['id'] == stem_a and not b['id'].startswith(tuple(PREFIXES))):
                reason = 'unprefixed relic: ' + stem_a
            elif stem_a == stem_b:
                reason = 'same id stem: ' + stem_a
            if reason:
                dups.add('%s/%s' % (a['category'], a['id']))
                dups.add('%s/%s' % (b['category'], b['id']))
                clusters[reason].append(('%s/%s' % (a['category'], a['id']), '%s/%s' % (b['category'], b['id'])))
    return dups, clusters


if __name__ == '__main__':
    dups, clusters = find(collect_all_items())
    print('Total duplicate items identified: %d' % len(dups))
    print('Total duplicate pairs: %d' % sum(len(v) for v in clusters.values()))
    for k, v in sorted(clusters.items()):
        print('  [%s] -> %s' % (k, v))
