"""
Builds the KITCHEN pack (assets/kitchen/<id>/) in headless Blender: free, local, low-poly models with real detail and procedural textures, one GLB, manifest and README per item.
It is a category of its own, apart from the kit's `appliances`, `building` and furniture items (those are not touched).

    blender --background --python tools/make_kitchen_assets.py                  (every item)
    blender --background --python tools/make_kitchen_assets.py -- fridge_top range_oven      (only these models, every finish)
    python tools/make_kitchen_assets.py --icons                                 (outside Blender: render the 128 px icons of every item that has a GLB)

  appliances   refrigerators, freezers, range, cooktop, oven tower, microwaves, hood, dishwasher, sink cabinet, small countertop appliances - each in STAINLESS, WHITE and BLACK
  cabinetry    base, drawer, corner, wall and glass cabinets, pantry, island, work counter, shelf, cart - each in WHITE (shaker, marble), OAK (slab, butcher block) and BLACK (slab, granite)
  tables       dining and bistro tables, chairs, bar stool, bench - in the same three wood / paint finishes
  accessories  trash can, canisters, crocks, cookware, boards, racks ... (steel / white / black where it makes sense)

The models are in tools/kitchen_models.py, the modelling kit and procedural textures in tools/kitchen_lib.py (textures in assets/_kitchen_textures/). Afterwards:
    python tools/make_kitchen_assets.py --icons ; python tools/generate_unity_asset_catalog.py ; python tools/package_catalog_as_mods.py
"""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KITCHEN = os.path.join(ROOT, 'assets', 'kitchen')
TOOLS = os.path.join(ROOT, 'tools')

# the appliance finishes: key -> (label, price factor)
APP_FIN = {'stainless': ('Stainless Steel', 1.22), 'white': ('White', 1.0), 'black': ('Black', 1.06)}
# the cabinet / furniture finishes
CAB_FIN = {'white': 'White', 'oak': 'Oak', 'black': 'Black'}

# model, stub, name, description, kind, weight kg, price, power W, extras (manifest properties)
APPLIANCES = [
    ('fridge_top', 'fridge_top', 'Top-Freezer Refrigerator', 'A full-size refrigerator with the freezer compartment on top, two doors with bar handles and a kick plate.', 62, 620, 150, {}),
    ('fridge_side', 'fridge_side', 'Side-by-Side Refrigerator', 'A tall side-by-side refrigerator-freezer with a water and ice dispenser in the freezer door.', 105, 1150, 190, {}),
    ('fridge_french', 'fridge_french', 'French-Door Refrigerator', 'A refrigerator with two French doors over a pull-out freezer drawer.', 118, 1480, 200, {}),
    ('freezer_upright', 'freezer_upright', 'Upright Freezer', 'A tall single-door upright freezer with a temperature light.', 55, 540, 130, {}),
    ('freezer_chest', 'freezer_chest', 'Chest Freezer', 'A deep chest freezer with a hinged lid and a handle.', 48, 460, 110, {}),
    ('range_oven', 'range', 'Gas Range', 'A freestanding four-burner gas range with cast-iron grates, a glass-window oven and a backguard.', 72, 780, 0, {}),
    ('cooktop_unit', 'cooktop', 'Built-In Cooktop', 'A four-burner cooktop with cast-iron grates, to set into a countertop.', 16, 420, 0, {}),
    ('oven_tower', 'oven_tower', 'Double Wall Oven Tower', 'A tall oven cabinet with two ovens, a control panel and a warming drawer.', 95, 1750, 5200, {}),
    ('microwave_counter', 'microwave', 'Countertop Microwave', 'A countertop microwave oven with a window door and a keypad.', 14, 120, 1100, {}),
    ('microwave_otr', 'microwave_otr', 'Over-The-Range Microwave', 'A microwave oven that mounts on the wall above the range.', 22, 340, 1100, {'wall': True}),
    ('range_hood', 'range_hood', 'Range Hood', 'A chimney range hood that mounts on the wall above the cooker.', 18, 290, 180, {'wall': True}),
    ('dishwasher', 'dishwasher', 'Dishwasher', 'A built-in dishwasher with a front control strip and a bar handle.', 42, 520, 1800, {}),
    ('sink_unit', 'sink', 'Kitchen Sink Cabinet', 'A double-bowl sink in a cabinet with a countertop, a tall arched faucet and a soap dispenser.', 45, 380, 0, {'support': '0.92'}),
    ('toaster', 'toaster', 'Toaster', 'A two-slice toaster with a lever and a browning dial.', 1.9, 35, 900, {}),
    ('kettle', 'kettle', 'Electric Kettle', 'An electric kettle on its power base, with a spout and a handle.', 1.2, 42, 1500, {}),
    ('coffee_maker', 'coffee_maker', 'Drip Coffee Maker', 'A drip coffee maker with a glass carafe and a warming plate.', 2.6, 58, 900, {}),
    ('stand_mixer', 'stand_mixer', 'Stand Mixer', 'A tilt-head stand mixer with a stainless mixing bowl.', 11, 240, 325, {}),
    ('blender_jug', 'blender', 'Countertop Blender', 'A countertop blender with a glass jug and a lid.', 3.8, 95, 700, {}),
    ('toaster_oven', 'toaster_oven', 'Toaster Oven', 'A countertop toaster oven with a glass door and three dials.', 5.5, 85, 1200, {}),
]

# model, stub, name, description, weight kg, price, extras
CABINETRY = [
    ('base_cab_60', 'base_cab', 'Base Cabinet', 'A single-door base cabinet with a countertop.', 28, 160, {'support': '0.92'}),
    ('base_cab_90', 'base_cab_wide', 'Double-Door Base Cabinet', 'A wide base cabinet with two doors and a countertop.', 38, 230, {'support': '0.92'}),
    ('base_cab_drawers', 'base_cab_drawers', 'Drawer Base Cabinet', 'A base cabinet of three deep drawers with a countertop.', 34, 260, {'support': '0.92'}),
    ('corner_base', 'corner_base', 'Corner Base Cabinet', 'An L-shaped corner base cabinet with a countertop, for turning a counter run round a corner.', 46, 290, {'support': '0.92'}),
    ('wall_cab_60', 'wall_cab', 'Wall Cabinet', 'A single-door wall cabinet. Mount it on a wall.', 14, 95, {'wall': True}),
    ('wall_cab_90', 'wall_cab_wide', 'Double-Door Wall Cabinet', 'A wide wall cabinet with two doors. Mount it on a wall.', 20, 140, {'wall': True}),
    ('wall_cab_glass', 'wall_cab_glass', 'Glass-Door Wall Cabinet', 'A wall cabinet with a glass door for showing dishes. Mount it on a wall.', 15, 170, {'wall': True}),
    ('pantry', 'pantry', 'Pantry Cabinet', 'A tall two-door pantry cabinet.', 52, 340, {}),
    ('island', 'island', 'Kitchen Island', 'A kitchen island with drawers and doors on the work side and an overhang for stools on the other.', 118, 860, {'support': '0.92'}),
    ('countertop_slab', 'work_counter', 'Work Counter', 'A freestanding countertop slab on slim legs, a work table for the kitchen.', 36, 210, {'support': '0.92'}),
    ('open_shelf', 'open_shelf', 'Open Kitchen Shelf', 'A wall shelf board on two brackets. Mount it on a wall and stand things on it.', 6, 48, {'wall': True, 'shelf': True}),
    ('kitchen_cart', 'cart', 'Kitchen Cart', 'A kitchen cart with a counter top, a drawer, a lower shelf and a towel bar.', 24, 190, {'support': '0.88'}),
]

TABLES = [
    ('table_rect', 'table', 'Dining Table', 'A rectangular dining table that seats six.', 38, 340, {'support': '0.76'}),
    ('table_round', 'table_round', 'Round Pedestal Table', 'A round pedestal table that seats four.', 26, 280, {'support': '0.75'}),
    ('table_bistro', 'table_bistro', 'Bistro Table', 'A small round bistro table for two.', 9, 95, {'support': '0.74'}),
    ('chair_dining', 'chair', 'Dining Chair', 'A dining chair with a slatted back.', 6.5, 70, {}),
    ('stool_bar', 'stool', 'Counter Stool', 'A counter-height stool with a round seat and a foot ring.', 5, 60, {}),
    ('bench', 'bench', 'Kitchen Bench', 'A plain bench for the kitchen table.', 11, 110, {'support': '0.46'}),
]

# accessories on the appliance finishes (steel / white / black): model, stub, name, description, kg, price
ACC_FIN = [
    ('trash_can', 'trash_can', 'Step Trash Can', 'A step-on kitchen trash can with a pedal and a lid.', 3.2, 58),
    ('canisters', 'canisters', 'Canister Set', 'Three lidded canisters in graduated sizes.', 2.4, 36),
    ('utensil_crock', 'utensil_crock', 'Utensil Crock', 'A crock holding a bunch of kitchen utensils.', 1.1, 18),
    ('paper_towel_holder', 'paper_towels', 'Paper Towel Holder', 'A weighted holder with a roll of paper towels.', 0.9, 14),
    ('bread_box', 'bread_box', 'Bread Box', 'A bread box with a roll-top lid.', 1.8, 32),
]
# accessories in one finish
ACC_ONE = [
    ('pot_stock', 'pot_stock', 'Stock Pot', 'A stainless stock pot with a lid.', 2.6, 55, 'stainless'),
    ('saucepan', 'saucepan', 'Saucepan', 'A stainless saucepan with a long handle.', 1.0, 28, 'stainless'),
    ('skillet', 'skillet', 'Cast-Iron Skillet', 'A heavy cast-iron skillet.', 3.4, 34, 'black'),
    ('dish_rack', 'dish_rack', 'Dish Drying Rack', 'A wire dish drying rack with a drip tray.', 1.3, 22, 'stainless'),
    ('pot_rack', 'pot_rack', 'Hanging Pot Rack', 'A wall rack with a bar, hooks and three hanging pans. Mount it on a wall.', 4.0, 85, 'black', {'wall': True}),
]
# accessories on the cabinet finishes
ACC_CAB = [
    ('cutting_board', 'cutting_board', 'Cutting Board', 'A thick wooden cutting board.', 1.6, 24, {}),
    ('fruit_bowl', 'fruit_bowl', 'Fruit Bowl', 'A wooden bowl with an apple, a lemon and a banana.', 0.9, 26, {}),
    ('knife_block', 'knife_block', 'Knife Block', 'A wooden knife block with five knives.', 1.5, 48, {}),
    ('spice_rack', 'spice_rack', 'Spice Rack', 'A wall spice rack with two shelves and a row of jars. Mount it on a wall.', 2.2, 32, {'wall': True}),
]
BOARD_LABEL = {'oak': 'Oak', 'white': 'Maple', 'black': 'Walnut'}


def variants():
    """Every item to build: dicts with the model, the finish key, the id, name, text and numbers."""
    out = []
    for model, stub, name, desc, kg, price, watts, ex in APPLIANCES:
        for fk, (label, factor) in APP_FIN.items():
            out.append(dict(model=model, fin=fk, kind='appliance', id='kitchen_%s_%s' % (stub, fk), name='%s %s' % (label, name),
                            desc='%s %s finish.' % (desc, label), kg=kg, price=round(price * factor), watts=watts, extras=ex, cab=False, label=label))
    for model, stub, name, desc, kg, price, ex in CABINETRY:
        for fk, label in CAB_FIN.items():
            out.append(dict(model=model, fin=fk, kind='cabinet', id='kitchen_%s_%s' % (stub, fk), name='%s %s' % (label, name),
                            desc='%s %s' % (desc, {'white': 'White shaker doors, marble top.', 'oak': 'Oak, butcher-block top.', 'black': 'Black, granite top.'}[fk]),
                            kg=kg, price=price, watts=0, extras=ex, cab=True, label=label))
    for model, stub, name, desc, kg, price, ex in TABLES:
        for fk, label in CAB_FIN.items():
            out.append(dict(model=model, fin=fk, kind='table' if model.startswith('table') or model == 'bench' else 'seating', id='kitchen_%s_%s' % (stub, fk),
                            name='%s %s' % (label, name), desc='%s %s finish.' % (desc, label), kg=kg, price=round(price * (1.0 if fk != 'oak' else 1.1)),
                            watts=0, extras=ex, cab=True, label=label))
    for model, stub, name, desc, kg, price in ACC_FIN:
        for fk, (label, factor) in APP_FIN.items():
            out.append(dict(model=model, fin=fk, kind='accessory', id='kitchen_%s_%s' % (stub, fk), name='%s %s' % (label, name), desc='%s %s finish.' % (desc, label),
                            kg=kg, price=max(1, round(price * (1.0 + (factor - 1.0) * 0.6))), watts=0, extras={}, cab=False, label=label))
    for row in ACC_ONE:
        model, stub, name, desc, kg, price, fk = row[:7]
        ex = row[7] if len(row) > 7 else {}
        out.append(dict(model=model, fin=fk, kind='accessory', id='kitchen_%s' % stub, name=name, desc=desc, kg=kg, price=price, watts=0, extras=ex, cab=False, label=''))
    for model, stub, name, desc, kg, price, ex in ACC_CAB:
        for fk, label in CAB_FIN.items():
            lab = BOARD_LABEL[fk] if model == 'cutting_board' else label
            out.append(dict(model=model, fin=fk, kind='accessory', id='kitchen_%s_%s' % (stub, fk), name='%s %s' % (lab, name), desc='%s %s finish.' % (desc, lab),
                            kg=kg, price=price, watts=0, extras=ex, cab=True, label=lab))
    return out


def manifest(v, tris, dims):
    w, d, h = dims
    props = {
        'weight_kg': float(v['kg']), 'max_stack_size': 1, 'base_value': int(v['price']), 'is_consumable': False,
        'footprint': '%.2fm W x %.2fm D x %.2fm H' % (w, d, h),
        'happiness_modifier': 0, 'thirst_restore': 0, 'energy_restore': 0, 'stamina_restore': 0, 'wellness_modifier': 0,
        'placeable': not v['extras'].get('wall'), 'wrench_remove': True, 'is_buyable': True, 'stores': ['furniture'], 'sale_unit': 'ea',
    }
    if v['extras'].get('wall'):
        props['attach_surface'] = 'wall'
        props['attach_side'] = 'interior'
    if v['extras'].get('shelf'):
        props['shelf'] = True
    if v['extras'].get('support'):
        props['support_surface'] = True
        props['deck_heights'] = v['extras']['support']
    return {
        '$schema': 'https://homesteader.game/schemas/item_v1.json',
        'id': v['id'], 'name': v['name'], 'category': 'kitchen', 'description': v['desc'], 'icon': v['id'] + '.png',
        'properties': props,
        'models': [{'file': v['id'] + '.glb', 'format': 'glb', 'dimensions_m': {'x': round(w, 3), 'y': round(h, 3), 'z': round(d, 3)}, 'triangles': int(tris)}],
        'utilities': {
            'water': {'metric': 'None (unplumbed / dry)', 'details': 'None (unplumbed / dry)'},
            'electricity': ({'metric': '%d W' % v['watts'], 'details': 'Draws about %d W while it runs.' % v['watts']} if v['watts'] else {'metric': 'None (passive / unpowered)', 'details': 'None (passive / unpowered)'}),
            'sewage': {'metric': 'None (no waste discharge)', 'details': 'None (no waste discharge)'},
            'battery': {'metric': 'None (no internal battery)', 'details': 'None (no internal battery)'},
            'internet': {'metric': 'None (offline / non-networked)', 'details': 'None (offline / non-networked)'},
        },
        'growth': {'is_growable': False, 'growth_type': None, 'species': None, 'max_age': None, 'time_unit': None, 'total_stages': 0, 'current_stage': None, 'stages': []},
        'plugin_metadata': {'version': '1.0.0', 'author': 'Homesteader Core', 'compatible_api': 'v1'},
        'category_fields': {'dimensions_m': {'width': round(w, 3), 'depth': round(d, 3), 'height': round(h, 3)}, 'kitchen_kind': v['kind'],
                           'finish': (v['label'] or 'Standard').lower().replace(' ', '_'), 'power_draw_w': int(v['watts'])},
    }


def readme(v, tris, dims):
    w, d, h = dims
    return ('# %s\n\n%s\n\nProcedural model (tools/make_kitchen_assets.py, tools/kitchen_models.py), %d triangles, %.2f x %.2f x %.2f m (W x D x H).%s\n'
            % (v['name'], v['desc'], tris, w, d, h, ' A wall item: mount it on a wall.' if v['extras'].get('wall') else ''))


def build_all(only):
    import bpy
    sys.path.insert(0, TOOLS)
    import kitchen_lib as L
    import kitchen_models as M
    fins = L.finishes()
    built = 0
    for v in variants():
        if only and v['model'] not in only:
            continue
        L.reset_scene()
        fin = M.CAB_KEYS.get(v['fin'], v['fin']) if v['cab'] else fins[v['fin']]
        K = getattr(M, v['model'])(fin)
        obj = K.build()
        lo, hi = L.bounds(obj)
        dims = (hi.x - lo.x, hi.y - lo.y, hi.z - lo.z)
        folder = os.path.join(KITCHEN, v['id'])
        os.makedirs(folder, exist_ok=True)
        L.export_glb(obj, os.path.join(folder, v['id'] + '.glb'))
        tris = obj['triangles']
        with open(os.path.join(folder, v['id'] + '.json'), 'w', encoding='utf-8', newline='\n') as f:
            json.dump(manifest(v, tris, dims), f, indent=2, ensure_ascii=False)
            f.write('\n')
        with open(os.path.join(folder, 'README.md'), 'w', encoding='utf-8', newline='\n') as f:
            f.write(readme(v, tris, dims))
        built += 1
        print('built', v['id'], tris, 'tris', '%.2f x %.2f x %.2f' % dims)
    print('KITCHEN: %d items' % built)


def make_icons(workers=4):
    """Renders the item icon of every kitchen item that has a GLB and no icon yet (or all with --force)."""
    from concurrent.futures import ThreadPoolExecutor
    force = '--force' in sys.argv
    jobs = []
    for v in variants():
        folder = os.path.join(KITCHEN, v['id'])
        glb, png = os.path.join(folder, v['id'] + '.glb'), os.path.join(folder, v['id'] + '.png')
        if os.path.exists(glb) and (force or not os.path.exists(png)):
            jobs.append((glb, png))

    def one(job):
        r = subprocess.run([sys.executable, os.path.join(TOOLS, 'render_icon_from_model.py'), job[0], job[1]], capture_output=True, text=True)
        ok = os.path.exists(job[1]) and r.returncode == 0
        print(('icon ' if ok else 'FAILED ') + os.path.basename(job[1]))
        return ok
    with ThreadPoolExecutor(max_workers=workers) as ex:
        results = list(ex.map(one, jobs))
    print('ICONS: %d of %d' % (sum(results), len(jobs)))


if __name__ == '__main__':
    if '--icons' in sys.argv:
        make_icons()
    else:
        only = set(sys.argv[sys.argv.index('--') + 1:]) if '--' in sys.argv else set()
        build_all(only)
