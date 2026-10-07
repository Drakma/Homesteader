import os
os.chdir(r'C:\Users\casey\Desktop\Homesteader\tools')

# clean the leftover no-op lines in the two model files
for f in ('dining_models.py', 'office_models.py'):
    s = open(f, encoding='utf-8').read()
    s = '\n'.join(l for l in s.split('\n') if 'if False else None' not in l)
    open(f, 'w', encoding='utf-8').write(s)

PACKS = {
    'dining': dict(
        title='DINING ROOM', folder='dining', models='dining_models', n=8, count=64,
        pieces="""PIECES = [
    ('dining_table', 'table', 'Dining Table', 'A dining table that seats six.', 'wood', 48, 560, {'support': '0.76'}),
    ('round_table', 'round_table', 'Round Dining Table', 'A round pedestal dining table that seats four.', 'wood', 34, 460, {'support': '0.76'}),
    ('china_cabinet', 'china_cabinet', 'China Cabinet', 'A china cabinet with glass doors and a shelf of plates.', 'wood', 70, 880, {}),
    ('bar_cart', 'bar_cart', 'Bar Cart', 'A rolling bar cart with bottles and glasses.', 'wood', 12, 190, {'support': '0.85'}),
    ('wine_rack', 'wine_rack', 'Wine Rack', 'A wine rack with twelve bottles.', 'wood', 14, 160, {}),
    ('dining_chair', 'chair', 'Dining Chair', 'An upholstered dining chair.', 'fabric', 7, 130, {}),
    ('host_chair', 'host_chair', 'Host Chair', 'A carver chair with arms, for the head of the table.', 'fabric', 9, 190, {}),
    ('dining_bench', 'bench', 'Dining Bench', 'An upholstered bench for the side of the table.', 'fabric', 12, 240, {'support': '0.48'}),
"""),
    'office': dict(
        title='HOME OFFICE', folder='office', models='office_models', n=8, count=64,
        pieces="""PIECES = [
    ('office_desk', 'desk', 'Writing Desk', 'A writing desk with a drawer pedestal.', 'wood', 32, 340, {'support': '0.76'}),
    ('executive_desk', 'executive_desk', 'Executive Desk', 'A large desk with two drawer pedestals and a modesty panel.', 'wood', 64, 780, {'support': '0.78'}),
    ('credenza', 'credenza', 'Credenza', 'A credenza with drawers and doors.', 'wood', 44, 460, {'support': '0.76'}),
    ('filing_cabinet', 'filing_cabinet', 'Filing Cabinet', 'A two-drawer filing cabinet.', 'wood', 24, 190, {'support': '0.72'}),
    ('lateral_file', 'lateral_file', 'Lateral File', 'A wide two-drawer lateral filing cabinet.', 'wood', 30, 260, {'support': '0.70'}),
    ('whiteboard_wall', 'whiteboard', 'Whiteboard', 'A framed whiteboard with a marker tray. Mount it on a wall.', 'wood', 8, 95, {'wall': True}),
    ('corkboard_wall', 'corkboard', 'Cork Board', 'A framed cork board with pinned notes. Mount it on a wall.', 'wood', 4, 60, {'wall': True}),
    ('office_chair', 'office_chair', 'Office Chair', 'A swivel office chair on a five-star base.', 'fabric', 12, 260, {}),
    ('guest_chair', 'guest_chair', 'Guest Chair', 'An upholstered chair for visitors.', 'fabric', 7, 150, {}),
"""),
}

for pk, c in PACKS.items():
    m = open('make_laundry_assets.py', encoding='utf-8').read()
    a = m.index("PIECES = [")
    b = m.index("]\nSTYLE_NOTE")
    m = m[:a] + c['pieces'] + m[b:]
    m = m.replace("'assets', 'laundry'", "'assets', '%s'" % c['folder']).replace("import laundry_models as M", "import %s as M" % c['models'])
    m = m.replace("'laundry_%s_%s_%s'", "'%s_%%s_%%s_%%s'" % pk).replace("'category': 'laundry'", "'category': '%s'" % pk).replace("'laundry_kind'", "'%s_kind'" % pk)
    m = m.replace('LAUNDRY', pk.upper()).replace('laundry_models', c['models']).replace('make_laundry_assets', 'make_%s_assets' % pk)
    m = m.replace("Builds the %s / MUDROOM pack (assets/laundry/" % pk.upper(), "Builds the %s pack (assets/%s/" % (c['title'], c['folder']))
    m = m.replace("12 pieces x 2 styles (classic, modern) x 4 colours = 96 items", "%d pieces x 2 styles (classic, modern) x 4 colours = %d items" % (c['n'], c['count']))
    m = m.replace(", 'water_per_use_l': ex.get('water_per_use_l', 0), 'water_usage_lpm': ex.get('water_lpm', 0)", '')
    open('make_%s_assets.py' % pk, 'w', encoding='utf-8', newline='\n').write(m)
print('ok')
