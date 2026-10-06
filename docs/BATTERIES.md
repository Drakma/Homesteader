# Batteries and the battery rack

Code-built models (no paid generation): `tools/make_battery_models.py` (labels with PIL, models with headless Blender, GLB, bottom-centre pivot, front is the game's +z). Icons: `tools/render_icon_from_model.py`.

| Item | What |
|---|---|
| `electricity_battery_12v_lifepo4_1200wh` | 12.8 V 100 Ah LiFePO4, 13 kg, about 4,000 cycles |
| `electricity_battery_12v_agm_1200wh` | 12 V 100 Ah sealed AGM lead-acid, 27 kg, about 500 cycles, 50% usable |
| `electricity_battery_12v_nmc_1200wh` | 11.1 V 108 Ah NMC lithium-ion, 10 kg, about 1,500 cycles |
| `electricity_battery_rack_lifepo4_48v` / `_agm_48v` / `_nmc_48v` | 3U 19 inch rack-mount modules of each chemistry (tag `#rack_battery`) |
| `electricity_battery_rack_empty` (Battery Rack) | An empty 18U rack on casters with six 3U slots |

## The rack

The rack is a container (the `container` block of its manifest): `accepts: ["#rack_battery"]`, `max_items: 6` (the slots, whatever the modules weigh), `capacity_kg: 700`.
LEFT click it with a rack battery in hand (like placing it: the battery slides into the next slot instead of going on the ground) or right click it; C opens its contents. With `slot_pitch_m` (0.1334 m, one 3U) and `slot_start_m` (0.09 m) set, a PLACED rack draws every battery inside
as its REAL model in its slot, bottom to top (`ContainerFillView.BuildModels`); without them a container draws filling blocks as before. Both fields and `max_items` are in the container component
schema (`assets/_schemas/container.schema.json`) and the catalog (`container_max_items`, `container_slot_pitch_m`, `container_slot_start_m`).
