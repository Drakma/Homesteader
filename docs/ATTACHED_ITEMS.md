# Attached items: things that mount on a building

Breaker boxes, lights (and later switches) are not put on the ground: they mount on a **finished** building's wall or ceiling.

## Manifest

Base properties (`assets/_schemas/_base_mounting.schema.json`, edited in the asset kit popup next to "Lights Fires"):

| Property | Values | Meaning |
|---|---|---|
| `attach_surface` | `wall`, `ceiling`, empty | It mounts on a building (and is not `placeable`). |
| `attach_surface` = `roof` | | A solar rack: aimed at the ROOF from the ground and lies on the roof surface, its long side up the slope (R turns it on a flat roof). |
| `attach_item` / `attach_result` | item ids | A mount takes this item (a solar panel): right click the placed mount with it in hand and the mount becomes `attach_result` (the mount with its panel). |
| `attach_through` | bool | A wall item that goes THROUGH the wall (a wire entry): the game puts a second plate on the other side and a sleeve through the wall, so it shows and is clicked from both sides. The model has the nodes `Plate` and `Pipe` (a 0.25 m sleeve, lengthened to the wall). |
| `attach_side` | `interior`, `exterior`, `either` | A wall item: the side of the wall it goes on. |
| `provides_power` | bool | Mounted on the OUTSIDE it brings electricity to that building. A building takes ONE such box: a second is refused ("already has a breaker box"). |
| `shelf` | bool | A wall item that is a SHELF: things are stood on its top face (see Shelves below). |

Lights use the existing `lights` list (`assets/_schemas/light_emitter.schema.json`). A light that should only work with power sets `"requires_power": true`;
`"on": "always"` keeps a room light on while powered, `"on": "night"` is dusk to dawn (the exterior lantern).
A light mounted INSIDE a building is on only while the player is in its ROOM (`LightEmitter.Occupied`): it goes out when they leave the room, comes back when they return, and
draws no power meanwhile. Exterior lights and lights not mounted on a building are not affected. The rooms are not authored: `RoomMap` (`Assets/Scripts/Growth/RoomMap.cs`)
cuts the space inside the walls into 0.2 m cells, closes a cell where the model's own colliders stand just under the ceiling (a partition is whole there: a doorway has its
header, a half-height stall wall does not reach), and flood fills the rest; it logs `[Rooms] <building>: N room(s)` once per model. A player standing in a doorway is still in
the room they came from. A building with one room (or whose rooms cannot be told) is lit as a whole.

## Shelves

A wall item with `shelf: true` holds things (`Assets/Scripts/Growth/Shelf.cs`). The face things stand on is the TOP of the model's bounds, its full width and depth, so
nothing of a shelf model may rise above its board. With an item in the active slot a left click on the shelf (or on a thing already on it) stands ONE of it there: at the
cursor, slid along to the nearest free place, 1.5 cm from its neighbours; a thing longer than it is wide lies along the shelf. It must have a model, be no taller than
0.9 m and no deeper than the board plus 6 cm, and a container must be empty. A right click on a thing takes it back (within 3.5 m). What is on the shelf is still the item
it was (a part-used coil keeps its metres, a can its liquid), has no physics, shows in the look-at panel (what is on it, the length free) and is saved with the shelf
(`SavedAttached.shelfIds / shelfX / shelfUsed / shelfLiquids`). A shelf with things on it cannot be taken down.

`tools/make_shelves.py` builds them: `building_shelf_wall_wood` (0.9 m, two brackets), `building_shelf_wall_wood_long` (1.8 m, three), `building_shelf_wall_steel`
(1.2 m, 0.35 m deep). Either side of a wall; sold at the depot.

## Wiring

The solar chain devices are wired together with wire cutters and coils or spools of wire (docs/WIRING.md). An outdoor breaker box brings a building electricity only while it is wired to an inverter with a complete chain behind it.

## Roof mounts and solar panels

There are no ladders, so a roof item is put up from the GROUND: with it in hand, aim at the roof of a FINISHED building, left click to bring out the preview (it follows the roof surface under the cursor, blue = valid), left click again or Enter to mount it. Only the distance from the player to the building counts (6 m, `AttachController.RoofReach`), not the distance to the roof spot. Two roof items keep half a rack apart. A Shift + right click with a wrench takes it down again.

Solar panels (`electricity_solar_panel_100w_rigid`, `_200w`, `_400w_commercial`) are not placeable: they only go on a mount. Each size has a roof mount (`electricity_solar_mount_<size>_roof`, attaches to a roof) and a ground mount (`..._ground`, a placeable rack). Hold the panel and right click the mount (roof ones from the ground too): the panel stays its own item: it is consumed and its own model is placed on the rack (`panel_offset_m`, `panel_tilt_deg` in the mount manifest); taking the mount down returns both. There are no combined array items. Panels also come in stacks of 4 and 8 (`..._stack_4`, `_stack_8`, packs of one equivalency `~solar_panel_<size>` so the yard tidy packs loose panels). Models: `tools/make_solar_breaker_models.py` (code-built GLBs, no paid generation).

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
- **Shift + right click with a WRENCH** (adjustable or pipe, in the active slot) on a mounted item (wall, ceiling or roof) takes it down into the toolbar (`PlacementController` calls `AttachedObject.TryPickUpAtRay`); a plain right click only says how. Nothing else takes a mounted item down.
- `ConstructionSite.CeilingY()`: the ceiling height of a finished model, from the tops of its `Wall_*` parts (an eave wall ends 0.45 m above the ceiling).

## Not yet

Switches (inside, control the lights of their room), sockets, and a building's power draw or the grid supply are not built: a powered building simply lights everything mounted in it.

Solar racks snap to each other: a ground rack (placed) or a roof rack (mounted) held near another rack of the same kind snaps edge to edge to it on any side, 3 cm apart, so the panels fitted on them sit in a neat row or block (`PlacementController.TrySnapMount`, `AttachController.TrySnapRoof`). A roof rack also takes the rotation of the rack it snaps to.
