# Generator Lockout Box (`electricity_generator_lockout_box`)

A weatherproof transfer box with a generator inlet, mounted on the OUTSIDE wall of a building. Wire a standby generator to it with AC wire: the building runs on its breaker box while that can carry it, and the box switches it over to the generator when the breaker box has no power, cannot carry the load or its batteries run low, then back once they have recovered. Never both at once. The handle shows which side is feeding: up the breaker box, down the generator.

Procedural model (tools/make_lockout.py), 232 triangles. Its handle is a separate object named `Handle` with its origin on the hinge. `wire_role: generator_lockout`. See docs/WIRING.md.
