from build_kit import collect_all_items
import re
from collections import defaultdict

items = collect_all_items()
PREFIXES = [
    'electricity_', 'electric_', 'water_', 'waste_', 'sewage_', 'net_', 'internet_',
    'animal_fish_', 'ingredient_fillet_', 'fishing_', 'machinery_', 'struct_', 'tool_',
    'seed_', 'crop_', 'food_', 'ingredient_', 'mat_bale_', 'mat_pelt_', 'mat_wool_', 'mat_',
    'tree_', 'tile_', 'clutter_', 'hud_', 'building_', 'fuel_'
]

def get_clean_stem(i_id):
    cur = i_id.lower()
    for p in PREFIXES:
        if cur.startswith(p):
            cur = cur[len(p):]
            break
    return cur.strip('_')

# Check duplicates
dups = set()
clusters = defaultdict(list)

for i in range(len(items)):
    for j in range(i + 1, len(items)):
        a = items[i]
        b = items[j]
        
        # Skip if both are different growable stages of same species
        sp_a = a['growth'].get('species')
        sp_b = b['growth'].get('species')
        if sp_a and sp_b and sp_a == sp_b:
            continue
            
        # Skip fish creature vs fish fillet
        if (a['id'].startswith('animal_fish_') and b['id'].startswith('ingredient_fillet_')) or \
           (b['id'].startswith('animal_fish_') and a['id'].startswith('ingredient_fillet_')):
            continue

        # Skip seed vs crop vs food
        prefixes_lifecycle = ('seed_', 'crop_', 'food_', 'ingredient_')
        if any(a['id'].startswith(p) for p in prefixes_lifecycle) and any(b['id'].startswith(p) for p in prefixes_lifecycle):
            if a['name'].lower() != b['name'].lower():
                continue

        # Skip tree vs food fruit (tree_apple vs food_apple)
        if (a['id'].startswith('tree_') and b['id'].startswith('food_')) or (b['id'].startswith('tree_') and a['id'].startswith('food_')):
            continue

        norm_a = re.sub(r'[^a-z0-9]', '', a['name'].lower())
        norm_b = re.sub(r'[^a-z0-9]', '', b['name'].lower())
        
        stem_a = get_clean_stem(a['id'])
        stem_b = get_clean_stem(b['id'])
        
        is_dup = False
        reason = ''
        
        # Condition 1: Same normalized name
        if norm_a and norm_a == norm_b:
            is_dup = True
            reason = f"{a['name']}"
        # Condition 2: Unprefixed relic matching stem
        elif (a['id'] == stem_b and not any(a['id'].startswith(p) for p in PREFIXES)) or \
             (b['id'] == stem_a and not any(b['id'].startswith(p) for p in PREFIXES)):
            is_dup = True
            reason = f"{stem_a.replace('_', ' ').title()}"
        # Condition 3: Same stem and neither is a distinct lifecycle item
        elif stem_a == stem_b:
            is_dup = True
            reason = f"{stem_a.replace('_', ' ').title()}"
                
        if is_dup:
            dups.add(f"{a['category']}/{a['id']}")
            dups.add(f"{b['category']}/{b['id']}")
            clusters[reason].append((f"{a['category']}/{a['id']}", f"{b['category']}/{b['id']}"))

print(f"Total duplicate items identified: {len(dups)}")
print(f"Total duplicate pairs: {sum(len(v) for v in clusters.values())}")
for k, v in sorted(clusters.items()):
    print(f"  [{k}] -> {v}")
