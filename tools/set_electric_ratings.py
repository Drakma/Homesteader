"""
Sets category_fields.max_current_a (the rated current in amps) on every piece of electric equipment, the number the overload system compares the current through the part with
(docs/OVERLOAD.md, Growth/Overload.cs). Breakers, bus bars, wall entries, disconnects, controllers, inverters, batteries, generators, and the sources (panels, turbines) all carry one.
Loads (lights, appliances, pumps) have none: they are the current, their watts (`power_draw_w`) are what flows. AC amps are watts / 240 V (a split-phase service), DC amps are
watts / 48 V (the battery bus). The ratings below follow the names of the parts (a 100 A panel, a 250 A bus bar) and their rated watts.

    python tools/set_electric_ratings.py            (writes the manifests)
    python tools/set_electric_ratings.py --list     (prints the table)
Afterwards: python tools/generate_unity_asset_catalog.py ; python tools/package_catalog_as_mods.py
"""
import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, 'assets')

RATINGS = {
    # AC breaker boxes (watts / 240 V)
    'electricity_panel_breaker_outdoor_50a': 50, 'electricity_panel_breaker_outdoor_100a': 100, 'electricity_panel_breaker_outdoor_200a': 200,
    'electricity_panel_breaker_subpanel': 150, 'electricity_panel_well_sub': 20,
    # DC breaker boxes (already set), bus bars (named by their amps), the wall entry
    'electricity_breaker_box_dc_32a': 32, 'electricity_breaker_box_dc_64a': 64, 'electricity_breaker_box_dc_128a': 128,
    'electricity_busbar_dc_100a': 100, 'electricity_busbar_dc_250a': 250, 'electricity_busbar_dc_500a': 500,
    'electricity_wall_entry_wire': 64,
    # switching
    'electricity_switch_disconnect_safety': 50, 'electricity_generator_lockout_box': 50,
    # charge controllers (named by their output amps at 48 V)
    'electricity_controller_mppt_32a': 32, 'electricity_controller_mppt_64a': 64, 'electricity_controller_mppt_128a': 128,
    # inverters: AC output amps (rated watts / 240 V)
    'electricity_inverter_hybrid_3kw': 12.5, 'electricity_inverter_hybrid_5kw': 20.8, 'electricity_inverter_hybrid_10kw': 41.7,
    # batteries: continuous current at the 48 V bus = the continuous watts / 48. Wall batteries keep their manifest watts (0.5 to 0.6 C); the rest: AGM 0.5 C, lithium 1 C
    'electricity_battery_12v_agm_1200wh': 12.5, 'electricity_battery_12v_lifepo4_1200wh': 25, 'electricity_battery_12v_nmc_1200wh': 25,
    'electricity_battery_wall_power_5kwh': 62.5, 'electricity_battery_wall_power_10kwh': 104.2, 'electricity_battery_wall_power_20kwh': 208.3,
    'electricity_battery_rack_agm_48v': 50, 'electricity_battery_rack_lifepo4_48v': 106.7, 'electricity_battery_rack_nmc_48v': 102.4,
    # generators: rated watts / 240 V
    'electricity_generator': 20.8, 'portable_generator': 31.3,
    'electricity_generator_standby_10kw': 41.7, 'electricity_generator_standby_14kw': 58.3, 'electricity_generator_standby_28kw': 116.7,
    # sources: the current at their rated output (panels and turbines cannot be overloaded; the rating is what they push)
    'electricity_solar_panel_100w_rigid': 6, 'electricity_solar_panel_200w': 11, 'electricity_solar_panel_400w_commercial': 11,
    'wind_turbine_100w_wood': 2.1, 'wind_turbine_200w_metal': 4.2, 'wind_turbine_500w_metal': 10.4,
    'electricity_turbine_wind_400w': 8.3, 'electricity_turbine_wind_3kw': 62.5,
    # wire (already set)
    'electricity_wire_dc_indoor_10m': 55, 'electricity_wire_dc_indoor_25m': 55, 'electricity_wire_dc_outdoor_10m': 55, 'electricity_wire_dc_outdoor_25m': 55,
}
# the panel and turbine stacks rate like the single panel
for suffix in ('_stack_4', '_stack_8'):
    for base in ('electricity_solar_panel_100w_rigid', 'electricity_solar_panel_200w', 'electricity_solar_panel_400w_commercial'):
        RATINGS[base + suffix] = RATINGS[base]


def main():
    listing = '--list' in sys.argv
    changed = 0
    for iid, amps in sorted(RATINGS.items()):
        hits = glob.glob(os.path.join(ASSETS, '*', iid, iid + '.json'))
        if not hits:
            print('MISSING', iid)
            continue
        p = hits[0]
        raw = open(p, 'rb').read().decode('utf-8')
        data = json.loads(raw)
        cf = data.setdefault('category_fields', {})
        if listing:
            print('%-52s %6s A   (now %s)' % (iid, amps, cf.get('max_current_a')))
            continue
        if cf.get('max_current_a') == amps:
            continue
        cf['max_current_a'] = amps
        crlf = '\r\n' in raw
        import re
        m = re.search(r'\n( +)"', raw)
        indent = len(m.group(1)) if m else 2
        out = json.dumps(data, indent=indent, ensure_ascii='\\u' in raw)
        if raw.endswith('\n'):
            out += '\n'
        with open(p, 'w', encoding='utf-8', newline='\r\n' if crlf else '\n') as f:
            f.write(out)
        changed += 1
    print(('%d rated' % len(RATINGS)) if listing else 'set max_current_a on %d manifest(s)' % changed)


if __name__ == '__main__':
    main()
