import os
import re

from items_water import WATER_BUILDERS
from items_sewage import SEWAGE_BUILDERS
from items_electricity import ELECTRICITY_BUILDERS
from items_internet import INTERNET_BUILDERS
from items_building import BUILDING_BUILDERS
from items_tools import TOOLS_BUILDERS
from items_farming_ranching import FARMING_RANCHING_BUILDERS
from items_fishing_logging import FISHING_LOGGING_BUILDERS

def human_name(item_id):
    parts = item_id.split('_')
    # Custom adjustments for nicer names
    words = []
    for p in parts:
        if p.lower() in ('pvc', 'cmu', 'mppt', 'poe', 'wifi6', 'ap', 'led', 'dc', 'ac', 'rv', 'cdx', 'emt', 'uv'):
            words.append(p.upper())
        elif p.lower() == 'gal':
            words.append('Gallon')
        elif p.lower() == 'ft':
            words.append('ft')
        elif p.lower() == '50a':
            words.append('50A')
        elif p.lower() == '30a':
            words.append('30A')
        elif p.lower() == '20v':
            words.append('20V')
        elif p.lower() == '3000w':
            words.append('3000W')
        elif p.lower() == '2000w':
            words.append('2000W')
        elif p.lower() == '7500w':
            words.append('7500W')
        elif p.lower() == '15kw':
            words.append('15kW')
        elif p.lower() == '100w':
            words.append('100W')
        elif p.lower() == '400w':
            words.append('400W')
        elif p.lower() == '3kw':
            words.append('3kW')
        elif p.lower() == '100ah':
            words.append('100Ah')
        elif p.lower() == '200ah':
            words.append('200Ah')
        elif p.lower() == '48v':
            words.append('48V')
        elif p.lower() == '5kwh':
            words.append('5kWh')
        elif p.lower() == '10kwh':
            words.append('10kWh')
        elif p.lower() == '1000gal':
            words.append('1000 Gallon')
        elif p.lower() == '500gal':
            words.append('500 Gallon')
        elif p.lower() == '275gal':
            words.append('275 Gallon')
        elif p.lower() == '55gal':
            words.append('55 Gallon')
        elif p.lower() == '5gal':
            words.append('5 Gallon')
        elif p.lower() == '100gal':
            words.append('100 Gallon')
        elif p.lower() == '15gal':
            words.append('15 Gallon')
        elif p.lower() == '50lb':
            words.append('50 lb')
        elif p.lower() == '1000ft':
            words.append('1000ft')
        elif p.lower() == '500ft':
            words.append('500ft')
        elif p.lower() == '100ft':
            words.append('100ft')
        elif p.lower() == '50ft':
            words.append('50ft')
        elif p.lower() == '20ft':
            words.append('20ft')
        elif p.lower() == '10ft':
            words.append('10ft')
        elif p.lower() == '16':
            words.append('16"')
        elif p.lower() == '20':
            words.append('20"')
        elif p.lower() == '2x4':
            words.append('2x4')
        elif p.lower() == '4x4':
            words.append('4x4')
        elif p.lower() == '2x8':
            words.append('2x8')
        elif p.lower() == '6inch':
            words.append('6"')
        elif p.lower() == 'half':
            words.append('1/2"')
        elif p.lower() == 'one':
            words.append('1"')
        elif p.lower() == 'two':
            words.append('2"')
        else:
            words.append(p.capitalize())
    return ' '.join(words)

def update_index_html():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    hud_dir = os.path.dirname(script_dir)
    html_path = os.path.join(hud_dir, "index.html")

    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()

    # Find existing CSV_ITEMS block
    m = re.search(r'(const CSV_ITEMS = \[\r?\n)([\s\S]*?)(\r?\n\s*\];)', html)
    if not m:
        print("Error: Could not find CSV_ITEMS block in index.html")
        return

    prefix, existing_items_str, suffix = m.group(1), m.group(2), m.group(3)

    # Extract existing IDs
    existing_ids = set(re.findall(r"id:\s*'([^']+)'", existing_items_str))

    categories_map = [
        ("WATER", WATER_BUILDERS),
        ("SEWAGE", SEWAGE_BUILDERS),
        ("ELECTRICITY", ELECTRICITY_BUILDERS),
        ("INTERNET", INTERNET_BUILDERS),
        ("BUILDING", BUILDING_BUILDERS),
        ("TOOLS", TOOLS_BUILDERS),
        ("FARMING & RANCHING", FARMING_RANCHING_BUILDERS),
        ("FISHING & LOGGING", FISHING_LOGGING_BUILDERS),
    ]

    new_entries = []
    for cat_name, b_list in categories_map:
        cat_entries = []
        for item_id, _, cat, sub in b_list:
            if item_id not in existing_ids:
                h_name = human_name(item_id)
                cat_entries.append(f"      {{ id: '{item_id}', name: '{h_name}', cat: '{cat}', sub: '{sub}' }},")
                existing_ids.add(item_id)
        if cat_entries:
            new_entries.append(f"      // NEW {cat_name} EXPANSIONS")
            new_entries.extend(cat_entries)

    print(f"Adding {len([e for e in new_entries if not e.startswith('      //')])} new items to CSV_ITEMS...")

    updated_items_str = existing_items_str.rstrip() + ",\n\n" + "\n".join(new_entries)
    updated_html = html[:m.start(2)] + updated_items_str + html[m.end(2):]

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(updated_html)

    print("Successfully updated index.html with expanded catalog!")

if __name__ == "__main__":
    update_index_html()

