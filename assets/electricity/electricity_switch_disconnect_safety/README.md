# Safety Disconnect Switch (`electricity_switch_disconnect_safety`)

A fused safety disconnect in a grey steel box. Mount it on a wall (inside or out) and wire it into a run, AC or DC: between the solar panels and the wall entry, the battery and the inverter, or the inverter (or a generator) and a breaker box. Right click it to throw the handle: up the power flows, down it is cut.

Procedural model (tools/make_disconnect.py), 112 triangles. Its throw handle is a separate object named `Handle` with its origin on the hinge (up = on, down = off; `Assets/Scripts/Growth/Disconnect.cs`). `wire_role: disconnect`. See docs/WIRING.md.
