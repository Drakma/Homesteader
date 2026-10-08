"""
Sets properties.flow_lph (liters an hour the part can pass) on every piece of water-line equipment, the number the water flow system compares with what is asked of it
(docs/WATER_FLOW.md, Growth/WaterFlow.cs). Pipes (half inch 900, one inch 2400, two inch 9000) and pumps (500 to 3600 L/h) already had one; this adds the filters,
spigots, faucets, the house inlet, the tanks' fittings and the hand pump, and keeps the older per-minute fields in step (max_flow_rate_lpm, max_filter_throughput_lpm = flow_lph / 60).
Nothing trips: a part that is too small simply limits the flow, and WAILA names the part that limits it.

    python tools/set_water_ratings.py            (writes the manifests)
    python tools/set_water_ratings.py --list
Afterwards: python tools/generate_unity_asset_catalog.py ; python tools/package_catalog_as_mods.py
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, 'assets')

RATINGS = {
    # filters: the water slows to what the filter passes (sediment 4 L/min, reverse osmosis 2, a spin-down 50, the UV chamber 30)
    'water_filter': 240, 'water_filter_reverse_osmosis': 120, 'water_filter_spin_down_sediment': 3000, 'water_sterilizer_uv_chamber': 1800,
    # taps and the house supply line
    'water_spigot_outdoor': 900, 'water_spigot_post': 900, 'water_faucet_indoor': 480, 'water_inlet_house': 3000,
    # a tank's fitting (what goes in or out of it), a pressure tank, a water heater
    'water_barrel_rain_200l': 600, 'water_cistern_poly_1200l': 1800, 'water_cistern_poly_2400l': 3600, 'water_cistern_poly_3800l': 3600,
    'water_ibc_tote_1000l': 1800, 'water_pressuretank_well': 3600, 'water_heater_electric_190l': 900,
    # the rest
    'water_hand_pump_wellhead': 480, 'water_pipe': 2400, 'water_fitting_camlock_coupler': 3000,
}


# reverse osmosis: the percent of the water that comes out as product (the rest is rejected to the drain); the flow rating above is the PRODUCT flow
RECOVERY = {'water_filter_reverse_osmosis': 33}


def write(path, raw, data):
    m = re.search(r'\n( +)"', raw)
    indent = len(m.group(1)) if m else 2
    out = json.dumps(data, indent=indent, ensure_ascii='\\u' in raw)
    if raw.endswith('\n'):
        out += '\n'
    with open(path, 'w', encoding='utf-8', newline='\r\n' if '\r\n' in raw else '\n') as f:
        f.write(out)


def main():
    listing = '--list' in sys.argv
    changed = 0
    for iid, lph in sorted(RATINGS.items()):
        hits = glob.glob(os.path.join(ASSETS, '*', iid, iid + '.json'))
        if not hits:
            print('MISSING', iid)
            continue
        p = hits[0]
        raw = open(p, 'rb').read().decode('utf-8')
        data = json.loads(raw)
        props = data.setdefault('properties', {})
        cf = data.setdefault('category_fields', {})
        if listing:
            print('%-40s %6s L/h   (now %s)' % (iid, lph, props.get('flow_lph')))
            continue
        before = json.dumps(data, sort_keys=True)
        props['flow_lph'] = lph
        if iid in RECOVERY:
            props['filter_recovery_pct'] = RECOVERY[iid]
        if 'max_flow_rate_lpm' in cf:
            cf['max_flow_rate_lpm'] = round(lph / 60.0, 1)
        if 'max_filter_throughput_lpm' in cf and ('filter' in iid or 'sterilizer' in iid):
            cf['max_filter_throughput_lpm'] = round(lph / 60.0, 1)
        if json.dumps(data, sort_keys=True) != before:
            write(p, raw, data)
            changed += 1
    # the pumps already have flow_lph: keep their per-minute field in step
    if not listing:
        for p in glob.glob(os.path.join(ASSETS, 'water', 'water_pump*', '*.json')):
            iid = os.path.basename(os.path.dirname(p))
            if os.path.basename(p)[:-5] != iid:
                continue
            raw = open(p, 'rb').read().decode('utf-8')
            data = json.loads(raw)
            lph = (data.get('properties') or {}).get('flow_lph')
            cf = data.get('category_fields') or {}
            if lph and 'max_flow_rate_lpm' in cf and cf['max_flow_rate_lpm'] != round(lph / 60.0, 1):
                cf['max_flow_rate_lpm'] = round(lph / 60.0, 1)
                write(p, raw, data)
                changed += 1
    print(('%d rated' % len(RATINGS)) if listing else 'updated %d manifest(s)' % changed)


if __name__ == '__main__':
    main()
