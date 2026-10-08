"""
The PROPANE PIPE sizes (docs/PROPANE_FLOW.md): the one existing propane pipe (fuel_pipe_propane, 1 inch) gets its flow rating and three more sizes join it, each as a 3 m length and a stack of 10 and 20:

    fuel_pipe_propane_half_inch               1/2"   7.5 L/h of liquid propane     enough for a 10 kW standby generator at full load (6.3 L/h)
    fuel_pipe_propane_three_quarter_inch      3/4"   15 L/h                         a 14 kW generator (8.7 L/h)
    fuel_pipe_propane                         1"     30 L/h                         a 28 kW generator (16.8 L/h); the pipe that was always there
    fuel_pipe_propane_one_and_a_quarter_inch  1-1/4" 55 L/h                         two big generators on one line

The flow is in LITERS AN HOUR OF LIQUID PROPANE (a generator's `fuel_consumption_l_per_min` x 60 at full load). Models: the existing pipe's builder (tools/make_material_stacks.py single_pipe, real outside
diameters: 21.3, 26.7, 33.4 and 42.2 mm), the stacks by its stack builder. Manifests come from the existing propane pipe.

    blender --background --python tools/make_propane_sizes.py
    python tools/render_icon_from_model.py assets/fuel/<id>/<id>.glb assets/fuel/<id>/<id>.png        (each of the nine)
Afterwards: python tools/generate_unity_asset_catalog.py ; python tools/package_catalog_as_mods.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_material_stacks as ms  # noqa: E402

FUEL = os.path.join(ms.ROOT, 'assets', 'fuel')
ms.BUILD = FUEL                                                   # its builders read and write the item folders under BUILD
CHARCOAL, YELLOW = (0.2, 0.21, 0.23), (0.95, 0.78, 0.08)
BASE = 'fuel_pipe_propane'

# id: (outside radius m, name, flow L/h of liquid propane, weight kg a 3 m length, price $ a length, description)
SIZES = {
    'fuel_pipe_propane_half_inch': (0.01065, '1/2" Propane Pipe', 7.5, 2.1, 10, 'A 3 m length of charcoal grey half-inch coated steel pipe for a small propane line: enough for a 10 kW standby generator at full load.'),
    'fuel_pipe_propane_three_quarter_inch': (0.01335, '3/4" Propane Pipe', 15.0, 3.1, 13, 'A 3 m length of charcoal grey three-quarter-inch coated steel pipe for a propane line: enough for a 14 kW standby generator at full load.'),
    'fuel_pipe_propane_one_and_a_quarter_inch': (0.0211, '1-1/4" Propane Pipe', 55.0, 6.8, 24, 'A 3 m length of charcoal grey one-and-a-quarter-inch coated steel pipe for a big propane line: carries two large standby generators at full load.'),
}
EXISTING = {'fuel_pipe_propane': 30.0, 'fuel_pipe_propane_stack_10': 30.0, 'fuel_pipe_propane_stack_20': 30.0}   # the 1 inch pipe that was always there


def load(item):
    return json.load(open(os.path.join(FUEL, item, item + '.json'), encoding='utf-8'))


def save(item, m):
    with open(os.path.join(FUEL, item, item + '.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(m, f, indent=2)


def main():
    # the pipe that was always there is the 1 inch one
    for item, flow in EXISTING.items():
        m = load(item)
        m['properties']['flow_lph'] = flow
        m['name'] = '1" Propane Pipe' + (' Stack' if '_stack_' in item else '')
        if '_stack_' not in item:
            m['description'] = 'A 3 m length of charcoal grey one-inch coated steel pipe for a propane line: carries a 28 kW standby generator at full load. ' + m['description'].split('line. ', 1)[-1]
        save(item, m)
    base = load(BASE)
    for item, (r, name, flow, kg, price, desc) in SIZES.items():
        folder = os.path.join(FUEL, item)
        os.makedirs(folder, exist_ok=True)
        m = json.loads(json.dumps(base))
        m['id'], m['name'], m['description'], m['icon'] = item, name, desc + ' ' + base['description'].split('line. ', 1)[-1], item + '.png'
        m['properties'].update({'weight_kg': kg, 'base_value': price, 'flow_lph': flow})
        m['models'] = []
        save(item, m)
        ms.SINGLES[item] = ms.single_pipe(CHARCOAL, r, stripe=YELLOW)
        ms.build_single(item)
        src = load(item)
        for n in (10, 20):
            ms.build_stack(item, n, src)
            stack = '%s_stack_%d' % (item, n)
            sm = load(stack)
            sm['properties']['wire_length_m'] = 3.0 * n
            sm['properties']['flow_lph'] = flow
            save(stack, sm)


if __name__ == '__main__':
    main()
