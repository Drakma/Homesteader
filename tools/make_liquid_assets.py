"""
Creates the liquid assets (assets/liquids/liquid_<name>/): manifest, README and a droplet icon in the fluid's own colour.
Safe to re-run (it rewrites these items only). Also registers the three liquid tags in assets/_schemas/material_tags.json.

A liquid's weight is properties.weight_kg = kilograms PER LITRE. category_fields: color (#RRGGBB swatch), opacity_pct
(100 = milk, about 70 = fuel), flammable. See assets/_schemas/liquids.schema.json.

    python tools/make_liquid_assets.py
"""
import json
import os

from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'assets', 'liquids')

# id suffix, name, colour, opacity %, kg per litre, flammable, thirst restore (drinkable), value per litre, description
LIQUIDS = [
    ('water', 'Water', '#7fb8e6', 35, 1.00, False, 12, 0.1, 'Clean fresh water.'),
    ('milk', 'Cow Milk', '#fdfdf6', 100, 1.03, False, 8, 1.2, 'Fresh whole cow milk. Fully opaque white.'),
    ('goat_milk', 'Goat Milk', '#faf6ea', 100, 1.03, False, 8, 2.4, 'Fresh goat milk, a touch creamier in colour than cow milk.'),
    ('cream', 'Cream', '#fff3d2', 100, 1.01, False, 0, 3.5, 'Heavy cream skimmed from fresh milk.'),
    ('diesel', 'Diesel Fuel', '#d9b23c', 70, 0.83, True, 0, 1.4, 'On-road diesel for tractors, generators and trucks.'),
    ('gasoline', 'Gasoline', '#e6d36a', 65, 0.74, True, 0, 1.2, 'Unleaded gasoline for small engines and mowers.'),
    ('propane', 'Liquid Propane', '#cfe8f4', 45, 0.51, True, 0, 0.8, 'Propane stored as a liquid under pressure.'),
    ('kerosene', 'Kerosene', '#e7dfae', 60, 0.81, True, 0, 1.6, 'Clear kerosene for lamps and heaters.'),
    ('motor_oil', 'Motor Oil', '#8c5a1a', 88, 0.88, True, 0, 4.0, 'Engine oil for tractors and generators.'),
    ('hydraulic_fluid', 'Hydraulic Fluid', '#b8452c', 78, 0.87, True, 0, 5.0, 'Red hydraulic fluid for loaders and implements.'),
    ('gear_oil', 'Gear Oil', '#6e4a1c', 90, 0.90, True, 0, 6.0, 'Thick gear and differential oil for tractors and implements.'),
    ('bar_chain_oil', 'Bar and Chain Oil', '#9c7a2a', 85, 0.88, True, 0, 5.0, 'Sticky oil that lubricates a chainsaw bar and chain.'),
    ('two_stroke_mix', 'Two-Stroke Fuel Mix', '#e08a2e', 62, 0.75, True, 0, 2.0, 'Gasoline premixed with two-stroke oil for chainsaws and trimmers.'),
    ('olive_oil', 'Olive Oil', '#b9b536', 82, 0.91, True, 0, 9.0, 'Cold pressed olive oil.'),
    ('sewage', 'Sewage', '#6b5a2c', 90, 1.01, False, 0, 0.0, 'Raw household sewage. Handle it with care and keep it out of the water.'),
    ('greywater', 'Greywater', '#9ca18c', 55, 1.00, False, 0, 0.0, 'Used water from sinks and showers.'),
    ('manure_slurry', 'Manure Slurry', '#4a391c', 98, 1.05, False, 0, 0.5, 'Liquid manure from the barn, spread as fertiliser.'),
    ('vegetable_oil', 'Vegetable Oil', '#dcbc4c', 80, 0.92, True, 0, 2.5, 'Pressed seed oil for the kitchen.'),
    ('maple_sap', 'Maple Sap', '#e6eee2', 30, 1.01, False, 4, 0.5, 'Thin, barely sweet sap tapped from maple trees.'),
    ('maple_syrup', 'Maple Syrup', '#7d4112', 95, 1.33, False, 6, 18.0, 'Sap boiled down to dark amber syrup.'),
    ('honey', 'Honey', '#d78c14', 90, 1.42, False, 6, 12.0, 'Thick golden honey from the hive.'),
    ('apple_cider', 'Apple Cider', '#c88a3c', 85, 1.05, False, 8, 3.0, 'Cloudy pressed apple cider.'),
    ('antifreeze', 'Antifreeze', '#47c27c', 78, 1.11, False, 0, 3.0, 'Green engine coolant. Not for drinking.'),
]

TAGS = {
    'liquid': ['liquid_' + x[0] for x in LIQUIDS],
    'liquid_fuel': ['liquid_diesel', 'liquid_gasoline', 'liquid_kerosene', 'liquid_two_stroke_mix'],
    'liquid_dairy': ['liquid_milk', 'liquid_goat_milk', 'liquid_cream'],
    'liquid_waste': ['liquid_sewage', 'liquid_greywater', 'liquid_manure_slurry'],
    'liquid_oil': ['liquid_motor_oil', 'liquid_gear_oil', 'liquid_bar_chain_oil', 'liquid_hydraulic_fluid', 'liquid_vegetable_oil', 'liquid_olive_oil'],
}


def hex_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def icon(path, colour, opacity):
    """A droplet in the fluid's colour: 128 px RGBA, transparent edge, 12+ px margin, no border."""
    s = 4
    n = 128 * s
    img = Image.new('RGBA', (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    r, g, b = hex_rgb(colour)
    alpha = int(255 * (0.6 + 0.4 * opacity / 100.0))
    cx, top, bottom = 64 * s, 22 * s, 106 * s
    rad = 30 * s
    cy = bottom - rad
    dark = (int(r * 0.6), int(g * 0.6), int(b * 0.6), 255)
    for grow, fill in ((3 * s, dark), (0, (r, g, b, alpha))):
        d.ellipse((cx - rad - grow, cy - rad - grow, cx + rad + grow, cy + rad + grow), fill=fill)
        d.polygon([(cx, top - grow), (cx - rad * 0.93 - grow, cy - rad * 0.35), (cx + rad * 0.93 + grow, cy - rad * 0.35)], fill=fill)
    d.ellipse((cx - 17 * s, cy - 8 * s, cx - 7 * s, cy + 10 * s), fill=(255, 255, 255, 150))   # highlight
    img = img.resize((128, 128), Image.LANCZOS)
    img.save(path)


def manifest(suffix, name, colour, opacity, kg_l, flammable, thirst, value, desc):
    item_id = 'liquid_' + suffix
    return item_id, {
        '$schema': 'https://homesteader.game/schemas/item_v1.json',
        'id': item_id,
        'name': name,
        'category': 'liquids',
        'description': desc,
        'icon': item_id + '.png',
        'properties': {
            'weight_kg': kg_l,
            'max_stack_size': 1,
            'base_value': value,
            'is_consumable': thirst > 0,
            'footprint': None,
            'happiness_modifier': 0,
            'thirst_restore': thirst,
            'energy_restore': 0,
            'stamina_restore': 0,
            'wellness_modifier': 0,
        },
        'models': [],
        'utilities': {
            'water': {'metric': 'None (unplumbed / dry)', 'details': 'None (unplumbed / dry)'},
            'electricity': {'metric': 'None (passive / unpowered)', 'details': 'None (passive / unpowered)'},
            'sewage': {'metric': 'None (no waste discharge)', 'details': 'None (no waste discharge)'},
            'battery': {'metric': 'None (no internal battery)', 'details': 'None (no internal battery)'},
            'internet': {'metric': 'None (offline / non-networked)', 'details': 'None (offline / non-networked)'},
        },
        'growth': {'is_growable': False, 'growth_type': None, 'species': None, 'max_age': None, 'time_unit': None,
                   'total_stages': 0, 'current_stage': None, 'stages': []},
        'plugin_metadata': {'version': '1.0.0', 'author': 'Homesteader Core', 'compatible_api': 'v1'},
        # dimensions_m is required of every item: a liquid is measured as ONE litre, a 10 cm cube
        'category_fields': {'dimensions_m': {'width': 0.1, 'depth': 0.1, 'height': 0.1}, 'color': colour, 'opacity_pct': opacity, 'flammable': flammable},
    }


def readme(item_id, m):
    p = m['properties']
    cf = m['category_fields']
    return f'''# {m['name']} (`{item_id}`)

![{m['name']} Icon]({item_id}.png)

## Overview
- **Category**: `liquids`
- **Item Identifier**: `{item_id}`
- **Weight**: {p['weight_kg']} kg per litre
- **Base Economic Value**: ${p['base_value']} per litre
- **Fluid colour**: `{cf['color']}`
- **Opacity**: {cf['opacity_pct']}%
- **Flammable**: {cf['flammable']}

## Description
{m['description']}

A liquid is not carried or placed on its own: it fills a liquid container (a bucket, can, drum or tank, see the
`liquid_container` schema) by volume, and its weight is the weight per litre times the litres held.

## Asset Files & Links
- **Plugin Manifest (JSON)**: [{item_id}.json]({item_id}.json)
- **Icon (PNG)**: [{item_id}.png]({item_id}.png)
'''


def main():
    os.makedirs(OUT, exist_ok=True)
    for row in LIQUIDS:
        item_id, m = manifest(*row)
        folder = os.path.join(OUT, item_id)
        os.makedirs(folder, exist_ok=True)
        with open(os.path.join(folder, item_id + '.json'), 'w', encoding='utf-8') as f:
            json.dump(m, f, indent=2)
        with open(os.path.join(folder, 'README.md'), 'w', encoding='utf-8') as f:
            f.write(readme(item_id, m))
        icon(os.path.join(folder, item_id + '.png'), row[2], row[3])
    print('liquids written:', len(LIQUIDS))

    p = os.path.join(ROOT, 'assets', '_schemas', 'material_tags.json')
    d = json.load(open(p, encoding='utf-8'))
    d['tags'].update(TAGS)
    json.dump(d, open(p, 'w', encoding='utf-8'), indent=2)
    print('tags:', ', '.join(TAGS))


if __name__ == '__main__':
    main()
