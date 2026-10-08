# Propane flow

A propane PIPE has a flow rating by its diameter (manifest `properties.flow_lph`, liters an hour of LIQUID propane). The only thing that draws propane through a line is a standby generator, so the
pipe size decides how much of a generator's power the line can feed. Nothing trips: a line that is too small STARVES the generator, and WAILA names the pipe. Code: `Growth/PropaneFlow.cs` (a partial of
`WireNetwork`), hooks in `TickLockouts` and the generator's WAILA rows in `Growth/Wiring.cs`. Data: `tools/make_propane_sizes.py`.

## Pipe sizes

| Pipe | Item | Flow (L/h of liquid propane) | Feeds at full load |
|---|---|---|---|
| 1/2" | `fuel_pipe_propane_half_inch` | 7.5 | a 10 kW generator (6.3 L/h) |
| 3/4" | `fuel_pipe_propane_three_quarter_inch` | 15 | a 14 kW generator (8.7 L/h) |
| 1" | `fuel_pipe_propane` (the pipe that was always there) | 30 | a 28 kW generator (16.8 L/h) |
| 1-1/4" | `fuel_pipe_propane_one_and_a_quarter_inch` | 55 | two big generators on one line |

Each comes as a 3 m length and a stack of 10 and 20 (`_stack_10`, `_stack_20`), at their real outside diameters (21.3, 26.7, 33.4, 42.2 mm).
The numbers come from gas-line capacities (a 1/2 inch line carries about 190,000 BTU an hour, liquid propane being about 25,000 BTU a liter).

## How a generator is starved

A standby generator burns `fuel_consumption_l_per_min x 60` L/h at full load and 30 % of that idling. The line can feed it the narrowest pipe between it and its best tank that has propane (`PropaneFeedLph`, the
best of several ways). If that is under the full-load burn: it can give `rated x (feed / full burn - 0.3) / 0.7` watts (nothing when the line cannot even feed an idle). `GenCapableW` is that number; the lockout
box uses it instead of the nameplate, so the building runs short (a brownout) when the load is more than the starved generators give.

Examples: a 28 kW generator on 3/4 inch pipe gives 23.7 kW, on 1/2 inch 5.9 kW; a 14 kW generator on 1/2 inch gives 11.2 kW; a 10 kW generator is fine on any of them.

## WAILA

A standby generator shows `Fuel line` (what the pipe feeds against what full load burns) and, when it is starved, `Limited by` the pipe and the watts it can give.

## Not modeled

A house propane connector only says whether a tank is piped to it (`HasPropane`): the building's own gas use (grills, stoves, heaters) draws nothing through the pipe yet, so the pipe to a house is not limited.
The fill post and the fuel truck fill a tank at their own rates.
