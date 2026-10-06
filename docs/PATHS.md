# Paths and roads

Hold a path or road BLUEPRINT and left click to lay control points. The route is drawn as a smooth curve (Catmull-Rom) through them, with the width of the
material. Enter lays it; Backspace or a right click takes the last point back; Esc cancels. The whole route must be on land you own and out of water.

## Path or road: the item decides
Set on the material item (asset kit, building category; schema fields in `_base_fences_paths.schema.json`):

| property | meaning |
|---|---|
| `path_kind` | `path` (narrow, walking) or `road` (wide, vehicles) |
| `path_width_m` | width of the laid surface (paths about 1.2, roads about 4) |
| `is_blueprint` | true: bought once, never used up, cannot be dropped, deleted or sold; shown on the blueprint blue #35637C |
| `path_material_item` | the material it lays (e.g. `mat_pile_gravel_small`), one item per `path_m_per_item` metres |
| `path_style` | dirt, gravel, stone or asphalt (asphalt gets a dashed centre line; roads and wide surfaces get a verge) |
| `path_m_per_item` | metres of route one item lays; a route of L metres uses ceil(L / this) items |

Blueprints: `path_dirt`, `path_gravel`, `path_stone`, `road_gravel`, `road_asphalt` (icons by `tools/make_path_icons.py`). Structures that build in stages are blueprints too (`Blueprints.cs`): the shop sells each once, straight to the toolbar, and holding it starts the construction site without using it up.

## Laying it
Materials come from the hotbar and the 4 m x 4 m work site round the first point, as for fences. The ped walks the route and lays one section
(one item) at a time, kneeling to work; a movement key or Esc stops it where it is and what is laid stays. Plants and rocks on a laid section go.

## Code
`Growth/PathBuilder.cs` (input, plan, laying), `Growth/PathRun.cs` (the curve and the mesh draped on the ground, 5 cm above it; no collider).
Saved in `GameSave.paths`.

## Laying over an existing route

When a route is finished (or stopped), any older finished route whose centre line lies under the new surface (within half the new width) and runs along it for at least 3 m (or 3 widths) is taken away there: the part under the new route is removed and what is left of the old route stays as separate pieces (`PathRun.ReplaceUnder`). A short overlap, a crossing, is not a replacement: the two routes blend (see the path shader).
