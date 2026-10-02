# Building a structure's stage models (the small cabin, step by step)

How the small cabin was made, so the barn, coop, farmhouse, greenhouse, stable and the rest can follow the same path. Everything is
free and local: headless Blender writes the models, no Meshy credits. Related docs: [CONSTRUCTION.md](CONSTRUCTION.md) (how a site
plays in the game), [MODDING_GUIDE.md](MODDING_GUIDE.md) (mod layout), `CLAUDE.md` (project rules).

## 1. What a structure is

A structure is a **growth group with four stages** (foundation, framing, walls, complete), each a stage manifest with its own model:

```
assets/structures/<id>/<id>.json                      the group manifest (growth.stages[] is authoritative: recipe, tools, size)
assets/structures/<id>/stages/struct_foundation/      struct_foundation_<id>.glb / .json / .png
assets/structures/<id>/stages/struct_framing/         ...
assets/structures/<id>/stages/struct_walls/           ...
assets/structures/<id>/stages/struct_complete/        ...
```

The stage manifests live under `stages/` and are NOT catalog items: `ModLoader.RegisterStageModel` registers only their model with
`ItemRegistry` so the construction site can show them by id. The recipe (materials, `any_of` groups, `#tag` quantities in the tag's
smallest unit) and the required tools of each stage are edited in the asset kit (rich editor, structure group) and live in the group
manifest, see CONSTRUCTION.md.

## 2. The generator

`tools/make_structure_stages.py` builds all four stages of a structure in headless Blender:

```
blender --background --python tools/make_structure_stages.py -- small_cabin
```

It reads each stage manifest's `category_fields.dimensions_m` (width = x, depth = y, height = the stage's overall height), builds the
mesh with `bmesh`, exports `<stage item id>.glb` beside the manifest, and writes `models[]` (file, format, dimensions, triangles)
back into the manifest. Then render the icon from the model and copy the files into the mod:

```
python tools/render_icon_from_model.py <stage glb> <stage png>      # icon is always rendered FROM the model
# copy glb + json + png into Homesteader/mods/homesteader/structures/<id>/stages/<stage>/   (or run tools/package_catalog_as_mods.py)
```

Free, fast and deterministic: re-run it whenever a dimension or detail changes. All four stages are regenerated together so they match.

### Conventions every stage model must follow

- 1 unit = 1 metre. Pivot at the centre of the footprint, ground at y = 0 (Blender z = 0, exported Y-up).
- **Front (the door side) is Blender -Y.** Add an empty named `FrontMarker` just in front of the door (the script puts it 0.8 m out);
  the game reads it to point the amber front arrow and to know which way the building faces.
- The same footprint in every stage, so a stage grows into the next. Foundation: slab with a low lip and a front step. Framing: studs,
  plates, openings, rafters. Walls: logs, gables, rafters. Complete: see below.
- Under 5,000 triangles per model (the cabin stages are 72 / 976 / 2,484 / 2,656).
- No `.fbx`, `.obj`, `.mtl` beside a stage: GLB only (the generator deletes legacy files of the complete stage).
- Materials are plain colours (Principled BSDF base colour); no textures needed for the procedural stages.

### The complete stage (what makes it a finished building)

`complete()` = the walls stage plus:

- **Roof boards ON TOP of the rafters.** Build the log walls and rafters a little lower than the finished height (`h_frame = h_total - 0.14`),
  then raise the board underside to the rafter centre line plus a margin (`margin`, `thick`). Fill the gable ends up to the underside.
  A roof at the same height as the rafters makes the rafters poke through.
- **A door as its own object on a hinge**: an empty named `DoorHinge` at the hinge edge, with the leaf `DoorLeaf` as its child, modelled
  in hinge-local coordinates (the leaf spans +x from the hinge). The wall keeps the full opening. The game swings it (`ConstructionSite.ToggleDoor`).
- **A window pane as its own object** named `WindowGlass`, alpha-blended glass material (`Alpha` input below 1, blend mode BLEND).
  Its own object because shadow casting is per renderer, not per material: the game switches the pane's shadow casting off so light passes.
- Frames, sill, mullion, a chimney, fascia boards: plain boxes.
- **Named materials for the look system:** call the log material `Log` and the roof `Roof` (or `Siding` / `Shingle` / `ShingleDark`): `StructureLook` recolours materials by these name prefixes when the walls or roof were built from items that set a look.
- **Split for the cutaway view:** the roof (boards, ridge cap, fascia, rafters) is its own object `Roof` and each wall (its logs or siding,
  gable, and the trim of its door and windows) is `Wall_Front` / `Wall_Back` / `Wall_Left` / `Wall_Right`, built through a `parts` dict of
  separate `Builder`s. The game finds them by name and works out which way each faces from where its bounds sit.

Sizes that matter for walking: the doorway is `DOOR_W = 1.2`, `DOOR_H = 2.3` (the player capsule is 0.7 m wide with skin, 1.8 m tall),
so the walls are `WALL_H = 2.7` to fit the header under the eaves.

## 3. What the game does with it (so you know what to name things)

| Model feature | Game behaviour | Code |
|---|---|---|
| `FrontMarker` empty | front arrow, which way the door faces, door swing direction | `ConstructionSite.LearnFront` |
| stage model by id | shown as the structure grows; stand-in boxes only if the model is missing | `ConstructionSite.RefreshVisual`, `ModLoader.RegisterStageModel` |
| `DoorHinge` > `DoorLeaf` | right click on the finished building (within 4 m) swings the door; the leaf is solid only when shut; saved as `doorOpen` | `ConstructionSite.FindDoor/ToggleDoor`, `GameSave.SavedSite` |
| `Roof`, `Wall_Front`, `Wall_Back`, `Wall_Left`, `Wall_Right` objects | the cutaway view hides the roof and the walls facing the camera while the player is inside (V) | `StructureCutaway` |
| `WindowGlass` renderer | shadow casting off, so sun and flashlight pass the window | `ConstructionSite.ShowModel` |
| walls, roof, closed door | cast shadows: they stop the sun and the player's flashlight / lantern | `PlayerLight` (shadows on) |
| solid meshes (concave) | real mesh colliders, so the player can walk in through the open door | `GlbTemplate` (`Solid`) |
| the foundation footprint | dirt area, 3 m ground grading, vegetation clearing, 4 m material yard | `TerrainGrade`, `SiteClearing`, `ConstructionSite` |

Placement snaps the foundation into a block of whole 1 m squares, turned in quarter turns, so keep footprints near whole metres where you can.

## 3b. A second example: the starter house (framed and clad)

`tools/make_house_stages.py` (`blender --background --python tools/make_house_stages.py -- starter_house`) is the framed-house sibling. It
reuses `make_structure_stages.py` as a library (`Builder`, the glass material, `roof_slab`) and shows how to generalise: a `Ctx` holds the
per-structure numbers (footprint, porch depth, wall height, openings per wall), and each stage is a function that adds to the previous one.

- foundation 276 tris: slab, wider footing step, anchor bolts, rebar stubs, three steps.
- framing 2,876: subfloor, sill plates, studs every 0.4 m with king studs, doubled headers and sills, double top plates, ceiling joists,
  porch posts and beam, rafters with collar ties, ridge board, gable studs.
- walls 3,284: the framing plus OSB sheathing (openings left clear), a sheathed roof deck, porch deck boards, rough window boxes.
- complete 3,712: clapboard siding in 0.24 m courses, corner boards, window trim with muntins, sills and shutters, a panel door
  (`DoorHinge` > `DoorLeaf`), railed porch with steps, shingled roof with course lines and ridge cap, fascia, a brick chimney,
  glazed windows (`WindowGlass`, shadow free).

Walls are built as layers measured inward from the outer plane (siding 0.03, sheathing 0.02, studs 0.14) by `wall_box`, which splits every
band round the openings; windows, trim and the door hang off the same opening table, so all four stages always agree. Its build list is
in `starter_house.json` (`growth.stages[].construction_recipe` and `required_tools`).

## 3c. Five stages, finishes and foundation styles

- **Stages:** foundation, framing, walls, exterior (folder `struct_complete`, the roof / siding / windows shell with its door) and finishings
  (folder `struct_finishings`: the same shell plus baseboards, drywall paint, flooring). Stage 5 is the last: the structure is finished after it.
  `finishings_data.py`-style edits live in the group manifest (`growth.stages[]`: recipe, tools, `age_min/age_max`).
- **Named parts for the game:** `Foundation` (slab, lip, steps: its own object in every stage so another style can replace it), `Roof`,
  `Wall_Front/Back/Left/Right`, `WindowGlass`, `DoorHinge` > `DoorLeaf`, `FrontMarker`.
- **Named materials for the look system:** `Log`/`Siding`, `Roof`/`Shingle`/`ShingleDark`, `Interior` (a thin layer inside the walls), `Floor`,
  `Masonry` (chimney), `FoundationFace` (variants). Anything else keeps its colour.
- **Foundation variants:** `tools/make_foundation_variants.py -- <ids>` writes block, brick and stilts models beside the foundation stage.
- **Finish items:** `tools/make_finish_items.py` creates the paints, carpets and tiles, sidings, roofings, bricks and field stone (model,
  manifest with `properties.look_*`, README), then `tools/finish_items_icons.py` renders their icons from the models. Add a row to `ITEMS`
  for a new finish; tags (`#paint`, `#flooring`, `#siding`, `#roofing`, `#brick`, `#chimney_masonry`) in `assets/_schemas/material_tags.json`.

## 4. Checklist for a new structure

1. Make sure `assets/structures/<id>/` has the group manifest and the four stage folders with stage manifests (the asset kit's growth group
   form creates them). Fill each stage's `dimensions_m`; use one footprint for all four.
2. Decide the layout: where the door and windows go, the wall height, the roof shape. The script is written for a log cabin (door on the
   -Y wall, one window on the +X wall, a chimney on -X). Generalise it before reuse: move the constants (`WALL_H`, `LOG_D`, `DOOR_W/H`, `WIN_*`,
   openings, chimney) into a per-structure config dict keyed by structure id, and add builders for other construction (framed walls with
   siding, a barn's big doors, a greenhouse's glazing). Keep every stage consistent with the openings.
3. Run the generator, render the icons, check the models: render them from a close angle (a small Blender view script with a
   workbench camera is enough) and look for rafters through the roof, gaps at the gables, doors that do not fit the opening.
4. Copy into `mods/homesteader`, restart Play, build the structure through every stage, then open the door and walk in.
5. If the structure has no door (a silo, a tent), skip `DoorHinge`; the game then just says the structure is finished.

## 5. Pitfalls we already hit

- **Centimetre models.** The Unreal-era finished models were written in centimetres (a 5 m cabin 510 units wide) with no scale. Check
  every imported structure GLB's real size (apply node scales, then the accessor bounds) and bake 0.01 into the vertices, not a node scale:
  a scaled node still hands Unity a mesh with 500-unit triangles, which makes mesh colliders warn. Procedural models are in metres already.
- **Missing palette texture.** Those same models use the `M_Homesteader_Palette` material and UVs but the palette image was never in the
  GLB (grey models). `assets/textures/palettes/T_Homesteader_Palette.png` has to be embedded.
- **Z-fighting.** The palette models have back-to-back coincident faces (door slabs inside walls) and a double-sided material draws both.
  Make solid-building materials single sided (`doubleSided: false`); keep it on for open surfaces like tents.
- **Stage models not showing.** `ModLoader` used to skip everything under `/stages/`, so every stage fell back to a brown box. Stage
  models are registered by id now (`RegisterStageModel`).
- **Doorway too small.** Walking through a 0.95 m by 2.05 m opening was impossible; size openings for the player capsule.
- **Light leaking.** Additional lights had shadows off, and a pane inside the main mesh cannot lose its shadow on its own: split it out.

## 6. Procedural vs Meshy

Use this for blocky, hard-edged things (buildings, sheds, crates, tanks, vans): clean low-poly shapes, a consistent look, zero credit cost.
Organic things (animals, people, plants) and fine detail still go through the reference image + Meshy image-to-3D pipeline in CLAUDE.md.
