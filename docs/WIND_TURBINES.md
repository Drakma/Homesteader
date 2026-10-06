# Wind turbines

Full-size small turbines with a moving head, code-built (no paid generation): `tools/make_wind_turbines.py` (Blender, GLB, bottom-centre pivot on the mast, front is the game's +z). Icons: `tools/render_icon_from_model.py`.

Turbines are sold as KITS and built on site. For each size there is a kit item and a buildable structure (blueprint):

| Kit item | Structure (blueprint) | What |
|---|---|---|
| `electricity_wind_kit_200w_metal` | `wind_turbine_200w_metal` | 200 W, three blades (1.2 m rotor), 3 m galvanized mast, orange tail fin |
| `electricity_wind_kit_500w_metal` | `wind_turbine_500w_metal` | 500 W, three blades (1.7 m rotor), 4.5 m mast with a furling tail, blue fin |
| `electricity_wind_kit_100w_wood` | `wind_turbine_100w_wood` | 100 W, wooden blades and tail vane on a wooden post with braces, 2.5 m |

The older `electricity_turbine_wind_400w`, `_3kw` and `electricity_wind_turbine` are still in the catalog with their old static models.

## Building one (the recipe tree, `ConstructionSite`)

A kit cannot be made from building materials: no recipe asks for any. You buy the KIT only (the blueprint is not for sale). With the kit in hand, left click the ground: the structure's preview follows the cursor (R turns it a quarter turn, blue = valid) and a second click or Enter starts the WORK SITE (the dirt area, the yard ring, the arrow marking the front) and uses the kit up (`properties.builds_structure`, `PlacementController.SiteIdOf`). Then build four stages, each with its tools (any one of each group in the toolbar, a toolbox or the yard) and its own ped animation and model motion:

| Stage | Takes | Tools (any one of each) | Ped clips (in turn) | The model |
|---|---|---|---|---|
| 1 Foundation | nothing (the kit was used up placing the site) | shovel or pickaxe; adjustable or pipe wrench (wood: shovel; hammer) | Dig, Hoe | the base plate (a concrete collar) is set in the graded ground |
| 2 Mast | nothing | wrench; a drill or impact driver (wood: saw; hammer; wrench) | Push_RT, Fixing_Kneeling_RT (wood: Chop_Tree_RT, Push_RT) | `tilt_up`: the mast lies on the ground and is raised upright on its foot |
| 3 Head | nothing | wrench; drill or impact driver | Fixing_Kneeling_RT, Push_RT | `lift`: the head is hoisted up the mast |
| 4 Complete | nothing | wrench; drill or impact driver | Fixing_Kneeling_RT | `spin_up`: the rotor is fitted (it grows) and spins up |

The build time follows the tools (docs/CONSTRUCTION.md: a drill and a wrench are faster than a hand tool). A finished turbine turns into the wind and its blades spin (below).

### How a stage is worked (data, asset kit stage editor)

Each stage of a structure can carry `build_clips` (the ped's work clips while it is built, in turn: Dig, Hoe, Push_RT, Fixing_Kneeling_RT, Chop_Tree_RT, Drag ...) and `build_motion` (`tilt_up`, `lift`, `spin_up`).
While the stage is built, `ConstructionSite.RunBuildPreview` shows the stage's model in the site and `BuildMotionView` moves its node (`Mast`, `Yaw` or `Rotor`) with `BuildProgress`; the previous stage's model is hidden meanwhile and put back if the build is cancelled. Both fields are in `structures.schema.json`, the server and the kit's stage editor.

## Node convention (read by `Assets/Scripts/Growth/WindTurbine.cs`)

| Node | Meaning |
|---|---|
| `Tower` | the static mast and base |
| `Yaw` | an empty at the top of the mast; it turns about the vertical axis to face INTO the wind |
| `Nacelle` | housing, tail boom and fin (child of `Yaw`) |
| `Rotor` | hub and blades (child of `Yaw`), origin at the hub, spins about its local Z (the front) |

A finished wind turbine STRUCTURE gets the behaviour on its model (`WindTurbine.AttachToModel`, called by `ConstructionSite` for the last stage; the rated power is the blueprint's `category_fields.max_power_w`). The older placeable path (`WindTurbine.AttachIfTurbine`, an electricity item whose id contains `turbine_wind`) is still there. A model without a `Yaw` and a `Rotor` node is left alone.

## Behaviour

- The head turns at up to 28 degrees a second to face the way the wind comes from (`WeatherEffectsManager.WindDirection` is where it blows toward), wandering a few degrees with the gusts.
- The rotor stands still below 2.5 m/s and spins up to about 13 rad/s as the wind grows (it has inertia); nothing moves while the game is paused.
- `WindTurbine.Watts` is the power it makes: `max_power_w` along a cubic curve from 3 m/s to full power at 11 m/s. Nothing consumes it yet (no power grid), but a power app can sum `WindTurbine.All`.
- The head and rotor have no colliders (a moving collider costs more than it is worth); the mast keeps its own.
