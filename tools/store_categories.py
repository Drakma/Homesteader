"""
Sorts everything the phone shops sell into store categories, so a shop opens on a grid of category tiles instead of one huge list.

    python tools/store_categories.py            (writes properties.store_category into the manifests of every item that is sold)
    python tools/store_categories.py --report   (only prints the tiles of each shop)

A category is a path: "Roofing", or "Living Room/Sofa" (a tile inside a tile; the shop shows a grid at every level that has more than one). The label goes in
`properties.store_category` (the asset kit's Store card), the catalog generator copies it into the shop listing (`store_listings[].category`), and PhoneController draws the tiles
(`StoreTiles`). A category's icon is `Resources/StoreCategoryIcons/<slug>.png` (tools/make_store_category_icons.py); a tile without one uses the icon of an item in it.
An item that sets `store_overrides.<shop>.category` keeps that for the shop. Re-run this after adding items to a shop.
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# (regex on the item id, category), first match wins, tried per source category (`cat` is the item's asset category)
BUILDING = [
    (r'^(lumber_|post_wood|sheet_plywood|building_beam|building_truss|building_bundle_rafter|building_lumber|building_pallet|building_framing)', 'Lumber & Framing'),
    (r'^building_chimney', 'Chimneys'),
    (r'^roofing_|^building_bitumen|^building_shingle|^building_roof', 'Roofing'),
    (r'^building_siding|^building_steel_siding|^building_corrugated|^building_metal_stack|^building_cladding', 'Siding & Cladding'),
    (r'^building_door|^building_window|^building_glass|^building_garage_door', 'Doors & Windows'),
    (r'^building_floor|^building_carpet|^building_tile', 'Flooring'),
    (r'^building_insulation|^building_drywall|^building_joint_compound|^building_weatherstripping|^building_paint|^building_caulk', 'Insulation & Drywall'),
    (r'^building_concrete|^masonry_|^20lb_|^building_mortar|^building_grout|^building_thinset|^building_cement|^building_sand|^building_stucco', 'Concrete & Masonry'),
    (r'^pipe_|^building_valve|^building_pvc|^drain_|^building_downspout|^building_gutter', 'Plumbing & Pipe'),
    (r'^(anchor_bolts|deck_screws|framing_nails|finishing_nails|lag_bolts|hurricane_ties|joist_hangers)|^building_roofing_nails|^building_rebar|^building_steel_(frame|stud)', 'Fasteners & Hardware'),
    (r'^building_romex|^building_wire|^building_conduit', 'Electrical Wire'),
    (r'^building_shel', 'Shelving'),
    (r'^box_', 'Boxes & Packaging'),
    (r'^(anchor_bolt|deck_screw|finishing_nail|framing_nail|lag_bolt|joist_hanger|hardware_|item_hardware_|gland_)', 'Fasteners & Hardware'),
    (r'^building_(trim|fascia|soffit|flashing|house_wrap|chinking|metal)', 'Trim & Flashing'),
    (r'^sheet_drywall', 'Insulation & Drywall'),
    (r'^item_spool_barbedwire|^insulators_tpost|^fence_|^gate_|^dock_|^camp_|^lot_|^road_|^path_|^building_gate|^building_pickup_flag', 'Fencing & Outdoor'),
    (r'^item_spool_', 'Electrical Wire'),
    (r'^part_floor_', 'Flooring'),
    (r'^icon_wood_log', 'Lumber & Framing'),
]
TOOLS = [
    (r'^tool_(angle_grinder|circular_saw|drill|impact_driver|miter_saw|table_saw|cement_mixer|cordless)', 'Power Tools'),
    (r'^tool_(chainsaw|kit_chainsaw|axe|hatchet|maul|wedge|cant_hook|chain_choker|tongs_skidding|helmet_logging|sawhorse|saw_hand|cord_shore)', 'Hand Tools/Logging & Saws'),
    (r'^tool_(shovel|hoe|trowel|sickle|shears|loppers|seedbag|pickaxe|wheelbarrow|plastic_wheelbarrow|steel_wheelbarrow|pump_sprayer|hose|bucket|pail|animal_paddle)', 'Hand Tools/Garden & Farm'),
]
VOLT = [
    (r'^electricity_solar_panel', 'Solar Panels'),
    (r'^electricity_solar_mount', 'Solar Mounts'),
    (r'^electricity_battery', 'Batteries'),
    (r'^electricity_(controller|inverter)', 'Controllers & Inverters'),
    (r'^(electricity_generator|portable_generator)', 'Generators'),
    (r'^electricity_(wind|turbine|power_pole|powerpole|wooden_utility)', 'Wind & Power Poles'),
    (r'^electricity_', 'Breakers & Wiring'),
]
GROCER_FOOD = [
    (r'^food_.*muffin|^food_(bread|burger_bun|cornbread)', 'Baked Goods'),
    (r'^food_(apple|apricot|blueberry|cantaloupe|cherry|fig|grapes|peach|pear|plum|raspberry|rhubarb|strawberry|watermelon|lemon|orange|huckleberry|haskap|elderberry)\b', 'Fruit'),
    (r'^food_(hazelnut|pecan|walnut|peanuts)', 'Nuts'),
    (r'^food_(beet|broccoli|cabbage|carrot|cucumber|garlic|green_beans|lettuce|onion|peas|pepper|potato|pumpkin|radish|spinach|tomato|truffle|zucchini|corn)', 'Vegetables'),
    (r'^food_cheese', 'Dairy & Eggs'),
    (r'^food_', 'Cooked Meat & Fish'),
]
GROCER_INGR = [
    (r'^ingredient_(fillet_|beef|bacon|chicken|goat_meat|ground_beef|ham|lamb_chop|pork|sausage|steak)', 'Raw Meat & Fish'),
    (r'^ingredient_(milk|butter|egg)', 'Dairy & Eggs'),
    (r'^ingredient_(flour|barley_flour|corn_flour|oat_flour|soy_flour|cornmeal|grits|pasta|oats|rolled_oats|pearl_barley|cracked_wheat|flax_meal)', 'Flour & Grains'),
    (r'^ingredient_(alfalfa|barley|canola|corn|cotton|flax|hops|soybeans|sunflower|tobacco|wheat)\b', 'Farm Crops'),
    (r'^ingredient_', 'Pantry Staples'),
]
MATERIALS = [
    (r'^mat_(log|pile_logs|wood_logs)', 'Lumber & Framing'),
    (r'^mat_(pile_|stone)', 'Dirt, Gravel & Stone'),
    (r'^mat_bale|^mat_pile_bedding', 'Hay, Straw & Bedding'),
    (r'^mat_', 'Farm Materials'),
]
LABEL = {'structures': 'Structures & Kits', 'fuel': 'Fuel', 'water': 'Water', 'waste': 'Waste', 'internet': 'Telecom', 'farming': 'Farming', 'ranching': 'Ranching',
         'logging': 'Logging', 'vehicles': 'Vehicles', 'kitchen': 'Kitchen', 'decor': 'Decor', 'appliances': 'Appliances'}
ROOMS = {'living': 'Living Room', 'kitchen': 'Kitchen', 'bathroom': 'Bathroom', 'bedroom': 'Bedroom', 'garage': 'Garage', 'laundry': 'Laundry', 'office': 'Office',
         'dining': 'Dining', 'decor': 'Decor', 'appliances': 'Appliances', 'appliance': 'Appliances'}
STYLES = {'classic', 'modern', 'budget', 'premium'}
COLORS = None


def first(rules, item_id):
    for rx, label in rules:
        if re.search(rx, item_id):
            return label
    return None


def piece_of(item_id, prefix):
    """The kind of piece in a furniture id: living_sofa_classic_burgundy -> Sofa (the room prefix and the trailing style and colour come off)."""
    parts = item_id.split('_')
    if parts and parts[0] in ('living', 'kitchen', 'bathroom', 'bedroom', 'garage', 'laundry', 'office', 'dining', 'decor', 'appliance', 'lighting'):
        parts = parts[1:]
    cut = len(parts)
    for i, p in enumerate(parts):
        if p in STYLES:
            cut = i
            break
    parts = parts[:cut] or parts[:1]
    return ' '.join(parts).title()


def classify(item_id, cat, stores):
    """The category path of an item, or None when it is not sold."""
    if item_id.startswith('building_light_'):
        return 'Lighting/' + ' '.join(item_id.split('_')[2:]).title()
    if cat == 'water' and 'water' not in stores:
        # the Water tile belongs to the water shop; the other shops file these by what they are
        if 'grocer' in stores: return 'Bottled Water'
        if 'depot' in stores: return 'Plumbing & Pipe'
        return 'Water Treatment'
    if cat == 'building':
        return first(BUILDING, item_id) or 'Building Supplies'
    if cat == 'tools':
        return first(TOOLS, item_id) or 'Hand Tools/General'
    if cat == 'materials':
        return first(MATERIALS, item_id) or 'Farm Materials'
    if cat == 'electricity':
        return first(VOLT, item_id) or 'Breakers & Wiring'
    if cat == 'lighting':
        return 'Lighting/' + piece_of(item_id, 'lighting')
    if cat == 'food':
        return first(GROCER_FOOD, item_id) or 'Cooked Meat & Fish'
    if cat == 'ingredients':
        return first(GROCER_INGR, item_id) or 'Pantry Staples'
    if cat in ('kitchen',) and 'grocer' in stores and 'furniture' not in stores:
        return 'Jars & Bottles'
    if cat in ROOMS or cat in ('appliances',):
        return ROOMS.get(cat, cat.title()) + '/' + piece_of(item_id, cat)
    if cat == 'living':
        return 'Living Room/' + piece_of(item_id, cat)
    return LABEL.get(cat, cat.title())


def main():
    report = '--report' in sys.argv
    tiles = {}
    changed = 0
    for path in sorted(glob.glob(os.path.join(ROOT, 'assets', '*', '*', '*.json'))):
        folder = os.path.dirname(path)
        if os.path.basename(path)[:-5] != os.path.basename(folder) or '_scratch' in path or os.sep + '_' in path.replace(ROOT, ''):
            continue
        try:
            m = json.load(open(path, encoding='utf-8'))
        except Exception:
            continue
        props = m.get('properties') or {}
        stores = props.get('stores') or []
        if not stores or not props.get('is_buyable', True):
            continue
        label = classify(m.get('id', ''), m.get('category', ''), stores)
        for s in stores:
            tiles.setdefault(s, {}).setdefault(label, 0)
            tiles[s][label] += 1
        if report:
            continue
        if props.get('store_category') != label:
            props['store_category'] = label
            m['properties'] = props
            raw = open(path, encoding='utf-8', newline='').read()
            nl = '\r\n' if '\r\n' in raw else '\n'
            text = json.dumps(m, indent=2, ensure_ascii=False) + '\n'
            with open(path, 'w', encoding='utf-8', newline='') as f:
                f.write(text.replace('\n', nl))
            changed += 1
    for s, c in sorted(tiles.items()):
        tops = {}
        for label, n in c.items():
            tops.setdefault(label.split('/')[0], 0)
            tops[label.split('/')[0]] += n
        print('%s: %d items, %d tiles' % (s, sum(tops.values()), len(tops)))
        print('   ' + ', '.join('%s %d' % (k, v) for k, v in sorted(tops.items(), key=lambda kv: -kv[1])))
    print('manifests changed:', changed)


if __name__ == '__main__':
    main()
