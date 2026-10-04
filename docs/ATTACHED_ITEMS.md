# Attached items: things that mount on a building

Breaker boxes, lights (and later switches) are not put on the ground: they mount on a **finished** building's wall or ceiling.

## Manifest

Base properties (`assets/_schemas/_base.schema.json`, edited in the asset kit popup next to "Lights Fires"):

| Property | Values | Meaning |
|---|---|---|
| `attach_surface` | `wall`, `ceiling`, empty | It mounts on a building (and is not `placeable`). |
| `attach_side` | `interior`, `exterior`, `either` | A wall item: the side of the wall it goes on. |
| `provides_power` | bool | Mounted on the OUTSIDE it brings electricity to that building. |

Lights use the existing `lights` list (`assets/_schemas/light_emitter.schema.json`). A light that should only work with power sets `"requires_power": true`;
`"on": "always"` keeps a room light on while powered, `"on": "night"` is dusk to dawn (the exterior lantern).

## Model convention

- Wall item: its BACK is the plane `y = 0` (Blender) and it sticks out towards `-y` (the game's +z: measured in the game, the model occupies z = 0 .. +depth). Bottom at `z = 0`, centred on `x`.
- Ceiling item: it hangs from its TOP; `z = 0` is its lowest point and its height is where it touches the ceiling.
- Light offsets (`offset_m`) are in the game's model space: `[x, y up, z out from the wall]`; a ceiling item's y is measured from its lowest point.

`tools/make_attached_items.py` builds the five items below (models, manifests, READMEs); icons: `tools/render_icon_from_model.py`.

| Item | Mounts | Notes |
|---|---|---|
| `electricity_panel_breaker_subpanel` (Outdoor Breaker Subpanel) | wall, exterior | `provides_power`; its model was rebuilt wall-ready (0.40 x 0.60 x 0.15 m, as its manifest says) |
| `electricity_light_sconce_interior` | wall, interior | on while powered |
| `electricity_light_sconce_exterior` | wall, exterior | on dusk to dawn while powered |
| `electricity_light_ceiling_flush` | ceiling | on while powered |
| `electricity_light_ceiling_pendant` | ceiling | on while powered |

## In the game

- `Assets/Scripts/Growth/AttachController.cs`: with such an item in the active slot, a left click brings out the preview, a second click or Enter mounts it (see `docs/CONTROLS.md`).
  Only a finished building takes them, within 3.5 m; a wall item must be on the side its `attach_side` says; a ceiling light is aimed at the floor (you cannot see a ceiling from above): it goes up to the ceiling over that spot, and the player must be inside; two mounted things are at least 0.3 m apart.
- `Assets/Scripts/Growth/AttachedObject.cs`: the mounted thing (a child of its building, saved with it in `GameSave.attached`), its light emitter, and the power rule:
  `AttachedObject.HasPower(site)` is true while a `provides_power` item is mounted outside that building. `LightEmitter.PowerCheck` is set to it, but it only gates things that are
  mounted on a building: any other light that "requires power" is unaffected.
- A right click on a mounted item takes it down into the toolbar (`PlacementController` calls `AttachedObject.TryPickUpAtRay`).
- `ConstructionSite.CeilingY()`: the ceiling height of a finished model, from the tops of its `Wall_*` parts (an eave wall ends 0.45 m above the ceiling).

## Not yet

Switches (inside, control the lights of their room), sockets, and a building's power draw or the grid supply are not built: a powered building simply lights everything mounted in it.
