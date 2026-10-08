"""
Gives the internet gear its network data (docs/INTERNET.md). Safe to run again.

    python tools/set_net_data.py

properties.wire_role     what it is on the network (net_dish, net_yagi, net_router, net_switch, net_ap, net_camera, net_rack, net_antenna)
properties.net_ports     how many cables it takes (a router: its LAN ports; the dish or yagi that feeds it goes in its WAN port, which is not counted)
properties.poe           its ports give 15 W of DC power each over the cable
properties.poe_powered   it runs from its cable: it only goes on a PoE port (everything else only on a standard port)
properties.rack_units    a rackmount device: the units it takes in a wall rack
properties.rack_capacity_u   a rack: the units it holds
properties.wire_kind / wire_length_m   a Cat6 cable: "net" and its metres
category_fields.range_m, bandwidth_mbps, power_draw_w, bandwidth_usage_mbps   the numbers the game reads
"""
import json
import os
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NET = os.path.join(ROOT, 'assets', 'internet')

# id: (properties, category_fields)
DATA = {
    'net_dish_satellite': ({'roof_mount': True, 'wire_role': 'net_dish', 'net_ports': 1}, {'bandwidth_mbps': 250, 'power_draw_w': 60, 'range_m': 0, 'is_connected': True}),
    'net_dish_satellite_high_perf': ({'roof_mount': True, 'wire_role': 'net_dish', 'net_ports': 1}, {'bandwidth_mbps': 500, 'power_draw_w': 110, 'range_m': 0, 'is_connected': True}),
    'net_antenna_yagi_directional': ({'roof_mount': True, 'wire_role': 'net_yagi', 'net_ports': 1, 'poe_powered': True}, {'bandwidth_mbps': 150, 'power_draw_w': 8, 'range_m': 1500, 'is_connected': False}),
    'net_antenna_omni_cellular': ({'roof_mount': True, 'wire_role': 'net_antenna'}, {'bandwidth_mbps': 0, 'power_draw_w': 10, 'range_m': 60, 'is_connected': False}),
    'net_ap_outdoor_weatherproof': ({'roof_mount': True, 'wire_role': 'net_ap', 'net_ports': 1, 'poe_powered': True}, {'bandwidth_mbps': 866, 'power_draw_w': 12, 'range_m': 60, 'is_connected': False}),
    'net_ap_indoor_ceiling': ({'wire_role': 'net_ap', 'net_ports': 1, 'poe_powered': True}, {'bandwidth_mbps': 1200, 'power_draw_w': 9, 'range_m': 25, 'is_connected': False}),
    'net_router': ({'wire_role': 'net_router', 'net_ports': 4}, {'bandwidth_mbps': 1000, 'power_draw_w': 10, 'range_m': 30, 'is_connected': False}),
    'net_router_mesh_wifi6': ({'wire_role': 'net_router', 'net_ports': 2}, {'bandwidth_mbps': 1200, 'power_draw_w': 12, 'range_m': 45, 'is_connected': False}),
    'net_router_rackmount': ({'wire_role': 'net_router', 'net_ports': 4, 'rack_units': 1}, {'bandwidth_mbps': 1000, 'power_draw_w': 18, 'range_m': 0, 'is_connected': False}),
    'net_networkswitch_poe': ({'wire_role': 'net_switch', 'net_ports': 5, 'poe': True}, {'bandwidth_mbps': 1000, 'power_draw_w': 60, 'range_m': 0, 'is_connected': False}),
    'net_switch_poe_8port': ({'wire_role': 'net_switch', 'net_ports': 8, 'poe': True}, {'bandwidth_mbps': 1000, 'power_draw_w': 130, 'range_m': 0, 'is_connected': False}),
    'net_switch_poe_16port': ({'wire_role': 'net_switch', 'net_ports': 16, 'poe': True, 'rack_units': 1}, {'bandwidth_mbps': 1000, 'power_draw_w': 250, 'range_m': 0, 'is_connected': False}),
    'net_switch_rackmount_16port': ({'wire_role': 'net_switch', 'net_ports': 16, 'rack_units': 1}, {'bandwidth_mbps': 1000, 'power_draw_w': 20, 'range_m': 0, 'is_connected': False}),
    'net_switch_rackmount_32port': ({'wire_role': 'net_switch', 'net_ports': 32, 'rack_units': 1}, {'bandwidth_mbps': 1000, 'power_draw_w': 35, 'range_m': 0, 'is_connected': False}),
    'net_injector_poe_adapter': ({'wire_role': 'net_switch', 'net_ports': 2, 'poe': True}, {'bandwidth_mbps': 1000, 'power_draw_w': 30, 'range_m': 0, 'is_connected': False}),
    'net_camera_poe': ({'wire_role': 'net_camera', 'net_ports': 1, 'poe_powered': True}, {'bandwidth_mbps': 0, 'power_draw_w': 8, 'range_m': 0, 'is_connected': False, 'bandwidth_usage_mbps': 4}),
    'net_ups_rackmount': ({'rack_units': 2, 'capacity_wh': 3000}, {'bandwidth_mbps': 0, 'power_draw_w': 0, 'range_m': 0, 'is_connected': False}),   # 2 h at a full rack: 6 units of PoE switch, 1500 W
    'net_rack_wall_8u': ({'wire_role': 'net_rack', 'rack_capacity_u': 8}, {'bandwidth_mbps': 0, 'power_draw_w': 0, 'range_m': 0, 'is_connected': False}),
    'net_jack_wall': ({'wire_role': 'net_jack', 'net_ports': 2}, {'bandwidth_mbps': 0, 'power_draw_w': 0, 'range_m': 0, 'is_connected': False}),
    'net_cable_ethernet_cat6_15m': ({'wire_kind': 'net', 'wire_length_m': 15, 'stacking_limit': 10}, {}),
    'net_cable_ethernet_cat6_30m': ({'wire_kind': 'net', 'wire_length_m': 30, 'stacking_limit': 10}, {}),
    'net_spool_cable_cat6_150m': ({'wire_kind': 'net', 'wire_length_m': 150, 'stacking_limit': 4}, {}),
}
KEYS = ('roof_mount', 'wire_role', 'net_ports', 'poe', 'poe_powered', 'rack_units', 'rack_capacity_u')


def main():
    n = 0
    for item, (props, fields) in DATA.items():
        folder, name = (os.path.join(ROOT, 'assets', item.split('/')[0]), item.split('/')[1]) if '/' in item else (NET, item)
        path = os.path.join(folder, name, name + '.json')
        if not os.path.exists(path):
            print('missing', item)
            continue
        raw = open(path, encoding='utf-8', newline='').read()
        m = json.loads(raw)
        p = m.setdefault('properties', {})
        for k in KEYS:
            if k not in props:
                p.pop(k, None)
        p.update(props)
        m['category_fields'] = dict(m.get('category_fields') or {}, **fields)
        text = json.dumps(m, indent=2, ensure_ascii=False) + '\n'
        if '\r\n' in raw:
            text = text.replace('\n', '\r\n')
        if text == raw:
            continue
        for k in range(40):
            try:
                open(path, 'w', encoding='utf-8', newline='').write(text)
                break
            except OSError:
                time.sleep(0.25)
        n += 1
    print(n, 'internet manifests updated')


if __name__ == '__main__':
    main()
