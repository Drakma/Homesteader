"""
Writes what the fuel truck is ordered for in the Tank You phone store: the three bulk fuel lots (fuel_bulk_propane, fuel_bulk_diesel,
fuel_bulk_gasoline) and the tank pickup service (fuel_service_tank_pickup).

    python tools/make_bulk_fuel.py
    python tools/generate_unity_asset_catalog.py ; python tools/package_catalog_as_mods.py

A lot is 100 L of one liquid. It is not a thing you carry: it has no model, and its manifest is a liquid container sold full (liquid_container:
capacity_l, filled_with, filled_l), which is how the game knows what and how much it is (Assets/Scripts/World/FuelDelivery.cs). Ordered from the
phone, it comes the next morning with the fuel truck (vehicle_delivery_fuel_truck), which fills the tanks standing in the world one by one; what
fits nowhere is refunded. The price is the liquid's own price per liter (assets/liquids/<id>) times the liters.

An item that is already in the kit keeps its name, price and the rest. The icon is the liquid's own icon.
"""
import json
import os
import shutil
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, 'assets')
FUEL = os.path.join(ASSETS, 'fuel')
LITERS = 100

# item: (liquid, name, unused: the icon is the liquid's own)
LOTS = {
    'fuel_bulk_propane': ('liquid_propane', 'Bulk Propane', 'fuel_tank_propane_1900l'),
    'fuel_bulk_diesel': ('liquid_diesel', 'Bulk Diesel', 'fuel_large_diesel_container'),
    'fuel_bulk_gasoline': ('liquid_gasoline', 'Bulk Gasoline', 'large_gas_fuel_container'),
}


def save(path, text):
    for attempt in range(40):
        try:
            with open(path, 'w', encoding='utf-8', newline='\n') as f:
                f.write(text)
            return
        except OSError:
            time.sleep(0.25)
    raise SystemExit('could not write ' + path)


def main():
    template = json.load(open(os.path.join(FUEL, 'fuel_propane_18l', 'fuel_propane_18l.json'), encoding='utf-8'))
    for item, (liquid, name, icon_from) in LOTS.items():
        folder = os.path.join(FUEL, item)
        path = os.path.join(folder, item + '.json')
        os.makedirs(folder, exist_ok=True)
        liq = json.load(open(os.path.join(ASSETS, 'liquids', liquid, liquid + '.json'), encoding='utf-8'))
        if os.path.exists(path):
            m = json.load(open(path, encoding='utf-8'))
        else:
            m = json.loads(json.dumps(template))
            m.update({'id': item, 'icon': item + '.png', 'name': name,
                      'description': '%d L of %s, delivered. The fuel truck brings it the morning after you order and pumps it into your tanks, one after another: every '
                                     'tank that takes it and is empty or already holds it. What fits in no tank is refunded.' % (LITERS, liq['name'].lower())})
            p = m['properties']
            p.update({'weight_kg': round(liq['properties'].get('weight_kg', 1.0) * LITERS, 1), 'base_value': round(liq['properties'].get('base_value', 1.0) * LITERS),
                      'max_stack_size': 99, 'is_buyable': True, 'stores': ['water'], 'sale_unit': 'ea', 'placeable': False})
            m['models'] = []
            m['category_fields'] = {'fuel_type': liquid.replace('liquid_', ''), 'capacity_l': LITERS, 'burn_minutes_per_item': 0}
        m['category_fields'] = dict(m.get('category_fields') or {}, dimensions_m={'width': 0.0, 'depth': 0.0, 'height': 0.0})   # (required by the schema; a lot has no size)
        m['liquid_container'] = {'capacity_l': LITERS, 'accepts': [liquid], 'filled_with': liquid, 'filled_l': LITERS}
        save(path, json.dumps(m, indent=2))
        save(os.path.join(folder, 'README.md'), '# %s\n\n%s\n\nNo model: a lot of %d L of `%s` (tools/make_bulk_fuel.py). Delivered by the fuel truck: '
             '`Assets/Scripts/World/FuelDelivery.cs`.\n' % (m['name'], m['description'], LITERS, liquid))
        src = os.path.join(ASSETS, 'liquids', liquid, liquid + '.png')          # the liquid's own icon
        if os.path.exists(src):
            shutil.copyfile(src, os.path.join(folder, item + '.png'))
        print('lot', item, '|', m['name'], '|', m['properties']['base_value'], 'for', LITERS, 'L of', liquid)


PICKUP = 'fuel_service_tank_pickup'


def pickup_service(template):
    """The tank pickup: a service, not a thing. The fuel truck takes one big fuel tank away (they cannot be picked up by hand)."""
    folder = os.path.join(FUEL, PICKUP)
    path = os.path.join(folder, PICKUP + '.json')
    os.makedirs(folder, exist_ok=True)
    if os.path.exists(path):
        m = json.load(open(path, encoding='utf-8'))
    else:
        m = json.loads(json.dumps(template))
        m.update({'id': PICKUP, 'icon': PICKUP + '.png', 'name': 'Tank Pickup',
                  'description': 'The fuel truck comes the next morning and takes one of your big fuel tanks away (a tank is too heavy to pick up). It takes your emptiest tank; '
                                 'order one pickup for each tank. You are paid back at a discount: half the price of the tank, and half the price of any fuel still in it.'})
        m['properties'].update({'weight_kg': 0.0, 'base_value': 60, 'max_stack_size': 99, 'is_buyable': True, 'stores': ['water'], 'sale_unit': 'ea', 'placeable': False})
        m['models'] = []
        m.pop('liquid_container', None)
        m['category_fields'] = {'fuel_type': 'none', 'capacity_l': 0, 'burn_minutes_per_item': 0, 'dimensions_m': {'width': 0.0, 'depth': 0.0, 'height': 0.0}}
    save(path, json.dumps(m, indent=2))
    save(os.path.join(folder, 'README.md'), '# %s\n\n%s\n\nNo model: a service (tools/make_bulk_fuel.py). `Assets/Scripts/World/FuelDelivery.cs`.\n' % (m['name'], m['description']))
    src = os.path.join(ASSETS, 'vehicles', 'vehicle_delivery_fuel_truck', 'vehicle_delivery_fuel_truck.png')
    if os.path.exists(src):
        shutil.copyfile(src, os.path.join(folder, PICKUP + '.png'))
    print('service', PICKUP, '|', m['name'], '|', m['properties']['base_value'])


if __name__ == '__main__':
    main()
    pickup_service(json.load(open(os.path.join(FUEL, 'fuel_propane_18l', 'fuel_propane_18l.json'), encoding='utf-8')))
