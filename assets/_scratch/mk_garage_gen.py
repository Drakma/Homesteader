import os
os.chdir(r'C:\Users\casey\Desktop\Homesteader\tools')
m = open('make_laundry_assets.py', encoding='utf-8').read()
a = m.index("PIECES = [")
b = m.index("]\nSTYLE_NOTE")
pieces = """PIECES = [
    ('workbench', 'workbench', 'Workbench', 'A workshop bench with a thick top, a lower shelf and a vise.', 'wood', 55, 340, {'support': '0.92'}),
    ('pegboard_wall', 'pegboard', 'Pegboard Wall Panel', 'A pegboard with a hammer, a saw and wrenches on hooks. Mount it on a wall.', 'wood', 6, 70, {'wall': True}),
    ('sawhorse', 'sawhorse', 'Sawhorse', 'A sawhorse for cutting boards.', 'wood', 6, 45, {'support': '0.80'}),
    ('shop_stool', 'shop_stool', 'Shop Stool', 'A round-topped stool for the workshop.', 'wood', 4, 40, {}),
    ('lumber_rack_wall', 'lumber_rack', 'Lumber Rack', 'Three steel arms holding a stack of boards. Mount it on a wall.', 'paint', 14, 90, {'wall': True}),
    ('tool_chest_rolling', 'tool_chest', 'Rolling Tool Chest', 'A rolling tool chest with five drawers.', 'paint', 46, 420, {}),
    ('tool_chest_top', 'tool_chest_top', 'Top Tool Chest', 'A top tool chest with a lid and three drawers.', 'paint', 14, 150, {'support': '0.34'}),
    ('cabinet_tall', 'cabinet_tall', 'Tall Steel Cabinet', 'A tall two-door steel cabinet with vent slots.', 'paint', 52, 310, {}),
    ('cabinet_base', 'cabinet_base', 'Steel Base Cabinet', 'A base cabinet with drawers, doors and a wood top.', 'paint', 48, 280, {'support': '0.92'}),
    ('wall_cabinet', 'wall_cabinet', 'Steel Wall Cabinet', 'A two-door steel wall cabinet. Mount it on a wall.', 'paint', 16, 130, {'wall': True}),
    ('steel_shelving', 'shelving', 'Steel Shelving Unit', 'A steel shelving unit with boxes and bins.', 'paint', 30, 140, {'support': '0.15,0.63,1.11,1.59'}),
    ('parts_cabinet', 'parts_cabinet', 'Parts Cabinet', 'A small-parts cabinet with 24 labelled drawers.', 'paint', 12, 95, {}),
    ('air_compressor', 'air_compressor', 'Air Compressor', 'A tank air compressor on wheels.', 'paint', 38, 360, {'watts': 1500}),
    ('bench_grinder', 'bench_grinder', 'Bench Grinder', 'A bench grinder with two wheels.', 'paint', 9, 110, {'watts': 400}),
"""
m = m[:a] + pieces + m[b:]
m = m.replace("from living_colors import colors", "from garage_colors import colors")
m = m.replace("import living_lib as LL", "import garage_lib as LL")
m = m.replace("LL.Palette(", "LL.GaragePalette(")
m = m.replace("'assets', 'laundry'", "'assets', 'garage'").replace("import laundry_models as M", "import garage_models as M")
m = m.replace("'laundry_%s_%s_%s'", "'garage_%s_%s_%s'").replace("'category': 'laundry'", "'category': 'garage'").replace("'laundry_kind'", "'garage_kind'")
m = m.replace('LAUNDRY', 'GARAGE').replace('laundry_models', 'garage_models').replace('make_laundry_assets', 'make_garage_assets')
m = m.replace("Builds the GARAGE / MUDROOM pack (assets/laundry/", "Builds the GARAGE / WORKSHOP pack (assets/garage/")
m = m.replace("12 pieces x 2 styles (classic, modern) x 4 colours = 96 items", "14 pieces x 2 styles (classic, modern) x 4 colours = 112 items")
m = m.replace("Upholstered pieces", "Painted-steel pieces")
open('make_garage_assets.py', 'w', encoding='utf-8', newline='\n').write(m)
print('ok')
