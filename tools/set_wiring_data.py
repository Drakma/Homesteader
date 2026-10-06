#!/usr/bin/env python3
"""
set_wiring_data.py
Gives the solar-chain devices their `properties.wire_role` and the coils and spools of wire their `wire_kind` and `wire_length_m` (docs/WIRING.md). Safe to run again.
    python tools/set_wiring_data.py      then   python tools/refresh_game_content.py
"""
import glob
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")

ROLES = {
    "solar_panel": ["electricity_solar_mount_%s_%s" % (s, v) for s in ("100w", "200w", "400w") for v in ("roof", "ground")],
    "wall_entry": ["electricity_wall_entry_wire"],
    "dc_breaker": ["electricity_breaker_box_dc_32a", "electricity_breaker_box_dc_64a", "electricity_breaker_box_dc_128a"],
    "mppt": ["electricity_controller_mppt_32a", "electricity_controller_mppt_64a", "electricity_controller_mppt_128a"],
    "battery": ["electricity_battery_12v_lifepo4_1200wh", "electricity_battery_12v_agm_1200wh", "electricity_battery_12v_nmc_1200wh", "electricity_battery_rack_empty",
                "electricity_battery_wall_power_5kwh", "electricity_battery_wall_power_10kwh", "electricity_battery_wall_power_20kwh"],
    "inverter": ["electricity_inverter_hybrid_3kw", "electricity_inverter_hybrid_5kw", "electricity_inverter_hybrid_10kw"],
    "ac_panel": ["electricity_panel_breaker_outdoor_50a", "electricity_panel_breaker_outdoor_100a", "electricity_panel_breaker_outdoor_200a", "electricity_panel_breaker_subpanel"],
    "water_tank": ["water_cistern_poly_1200l", "water_cistern_poly_2400l", "water_cistern_poly_3800l", "water_ibc_tote_1000l", "water_barrel_rain_200l", "water_pressuretank_well", "water_heater_electric_190l"],
    "water_inlet": ["water_inlet_house"],
    "water_pump": ["water_pump_low_capacity", "water_pump", "water_pump_jet_shallow_well", "water_pump_high_capacity"],
    "water_spigot": ["water_spigot_outdoor", "water_faucet_indoor", "water_spigot_post"],
    "water_filter": ["water_filter_spin_down_sediment", "water_filter", "water_filter_canister_bigblue", "water_filter_reverse_osmosis", "water_sterilizer_uv_chamber"],
    "wind_turbine": ["wind_turbine_100w_wood", "wind_turbine_200w_metal", "wind_turbine_500w_metal"],
    "busbar": ["electricity_busbar_dc_100a", "electricity_busbar_dc_250a", "electricity_busbar_dc_500a"],
    # a propane line (joined with the pipe wrench, made of propane pipe): tools/make_propane_line.py
    "propane_tank": ["fuel_tank_propane_1900l", "fuel_tank_propane_3800l"],
    "propane_connector": ["fuel_propane_house_connector"],
    "propane_filler": ["fuel_propane_fill_post"],
    # sewage (docs/SEPTIC.md, tools/make_septic.py): the septic tanks and leach fields are structures whose group manifest carries the role
    "standby_generator": ["electricity_generator_standby_10kw", "electricity_generator_standby_14kw", "electricity_generator_standby_28kw"],   # propane, auto start
    "fuel_tank": ["fuel_tank_bulk_small", "fuel_tank_bulk_large"],   # gasoline / diesel, piped to fuel pumps with a fuel line
    "fuel_pump": ["fuel_pump_gas", "fuel_pump_diesel"],
    "disconnect": ["electricity_switch_disconnect_safety"],
    "generator_lockout": ["electricity_generator_lockout_box"],   # a standby generator feeds a building through it (never with the breaker box)   # a switch in a run, AC or DC (Disconnect.cs)
    "sewer_outlet": ["waste_outlet_house"],
    "sewer_pump": ["waste_pump_macerator"],
    "septic_dbox": ["waste_box_distribution_septic"],
}
WIRES = {
    "pipe_pvc_half_inch": ("water", 3), "pipe_pvc_half_inch_stack_10": ("water", 30), "pipe_pvc_half_inch_stack_20": ("water", 60),
    "pipe_pvc_two_inch": ("water", 3), "pipe_pvc_two_inch_stack_10": ("water", 30), "pipe_pvc_two_inch_stack_20": ("water", 60),
    "pipe_pvc_one_inch": ("water", 3), "pipe_pvc_one_inch_stack_10": ("water", 30), "pipe_pvc_one_inch_stack_20": ("water", 60),   # a water line from a well (docs/WELLS.md)
    "electricity_wire_dc_indoor_10m": ("dc_indoor", 10), "electricity_wire_dc_indoor_25m": ("dc_indoor", 25),
    "electricity_wire_dc_outdoor_10m": ("dc_outdoor", 10), "electricity_wire_dc_outdoor_25m": ("dc_outdoor", 25),
    "building_romex_10_3_spool": ("ac", 75), "building_romex_10_3_spool_small": ("ac", 15),
    "building_romex_14_2_spool": ("ac", 75), "building_romex_14_2_spool_small": ("ac", 15),
    "item_spool_romex_12_2": ("ac", 15), "spool_wire_romex_12_2": ("ac", 75),
    "pipe_abs_waste_three_inch": ("sewer", 3),   # black waste pipe: a building's drain to its septic system
    "fuel_pipe_line": ("fuel", 3), "fuel_pipe_line_stack_10": ("fuel", 30), "fuel_pipe_line_stack_20": ("fuel", 60),   # gasoline / diesel line
    "fuel_pipe_propane": ("propane", 3), "fuel_pipe_propane_stack_10": ("propane", 30), "fuel_pipe_propane_stack_20": ("propane", 60),
}
BATTERY_SPECS = {   # id: (capacity_wh, nominal_voltage_v)
    "electricity_battery_12v_lifepo4_1200wh": (1200, 12.8), "electricity_battery_12v_agm_1200wh": (1200, 12), "electricity_battery_12v_nmc_1200wh": (1200, 11.1),
    "electricity_battery_rack_agm_48v": (4800, 48), "electricity_battery_rack_lifepo4_48v": (5120, 51.2), "electricity_battery_rack_nmc_48v": (4914, 46.8),
    "electricity_battery_wall_power_5kwh": (5000, 51.2), "electricity_battery_wall_power_10kwh": (10000, 51.2), "electricity_battery_wall_power_20kwh": (20000, 51.2),
}


# Liters an hour a water pipe carries (properties.flow_lph, the same field a pump's flow is in): a water line gives no more than its NARROWEST pipe lets through
# (WireNetwork.PipeCaps). The pumps lift 1400, 2300 and 2900 L/h: half inch pipe throttles every pump, one inch only the biggest, two inch none.
PIPE_FLOW_LPH = {"pipe_pvc_half_inch": 900, "pipe_pvc_one_inch": 2400, "pipe_pvc_two_inch": 9000}

# a surface pump's flow (liters an hour): it pulls stored water out of a cistern on to the next tank, the filters or a building (docs/WELLS.md)
PUMP_FLOWS = {"water_pump_low_capacity": 1200, "water_pump": 2000, "water_pump_jet_shallow_well": 2400, "water_pump_high_capacity": 3600}
# tanks that hold water under pressure: a building's taps draw from them without a pump running
PRESSURIZED = ["water_pressuretank_well", "water_heater_electric_190l"]

# what each filter does on a well's water line: water reaching a tank through a sediment, a carbon and a UV stage is clean (docs/WELLS.md)
FILTER_STAGES = {"water_filter_spin_down_sediment": "sediment", "water_filter": "sediment", "water_filter_canister_bigblue": "carbon",
                 "water_filter_reverse_osmosis": "carbon", "water_sterilizer_uv_chamber": "uv"}


def manifest_path(item_id):
    hits = glob.glob(os.path.join(ASSETS, "*", item_id, item_id + ".json"))
    return hits[0] if hits else None


def edit(item_id, props):
    p = manifest_path(item_id)
    if p is None:
        print("missing", item_id)
        return 0
    raw = open(p, "rb").read().decode("utf-8")
    crlf = "\r\n" in raw
    m = json.loads(raw)
    pr = m.setdefault("properties", {})
    if all(pr.get(k) == v for k, v in props.items()):
        return 0
    pr.update(props)
    text = json.dumps(m, indent=2, ensure_ascii=False) + "\n"
    if crlf:
        text = text.replace("\n", "\r\n")
    for attempt in range(40):   # (Windows now and then refuses a write for a moment while something else has the file open)
        try:
            open(p, "wb").write(text.encode("utf-8"))
            break
        except OSError:
            if attempt == 39:
                raise
            import time
            time.sleep(0.25)
    return 1


def main():
    n = 0
    for role, ids in ROLES.items():
        for i in ids:
            n += edit(i, {"wire_role": role})
    for i, (kind, metres) in WIRES.items():
        n += edit(i, {"wire_kind": kind, "wire_length_m": metres})
    for i, lph in PIPE_FLOW_LPH.items():
        for item in (i, i + "_stack_10", i + "_stack_20"):
            n += edit(item, {"flow_lph": lph})
    for i, lph in PUMP_FLOWS.items():
        n += edit(i, {"flow_lph": lph})
    for i in PRESSURIZED:
        n += edit(i, {"pressurized": True})
    for i, stage in FILTER_STAGES.items():
        n += edit(i, {"filter_stage": stage})
    for i, (wh, v) in BATTERY_SPECS.items():
        n += edit(i, {"capacity_wh": wh, "voltage_v": v})
    print("manifests changed:", n)


if __name__ == "__main__":
    main()
