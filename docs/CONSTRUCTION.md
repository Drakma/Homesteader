# Building structures

A structure (small_cabin, barn, farmhouse, and the other 4-stage percent groups in `assets/structures`) is built in stages:
foundation, framing, walls, complete. Code: `Assets/Scripts/Growth/ConstructionSite.cs`.

0. **The front.** A structure has a FRONT (the door side). While you place it, the shadow is the foundation model (with its door step) and a flat
   **amber arrow** points out of the front; the same arrow marks the dirt area until the foundation is built. R turns it in quarter turns. The
   stage models carry an empty named `FrontMarker` just in front of the door (`tools/make_structure_stages.py` adds it); the game reads that
   to know which way the front faces, so a new structure's models only need to put the door where the marker is.
1. **Start it.** Select the structure item and click (the usual two-step placement: first click brings out the shadow,
   R rotates it, Enter or a second click places it). The shadow is the foundation's footprint, turned in quarter turns (R) and snapped into a block of whole 1 m grid squares (as many as its width and depth need), centred in it, so its edges run along the grid lines with an equal margin each side. Placing makes a **dirt area**
   that size; the structure item is used up.
2. **The yard.** Materials and tools count when they are within **4 m of the foundation's edge** (`ConstructionSite.YardM`).
   A faint yellow ring shows the yard while you hold something the stage needs.
3. **Bring materials.** Place them (the normal placement), or leave them lying on the ground (dropped items and loose delivery items count too). Anything inside a box or crate standing in the yard counts too (a delivery arrives in boxes), and building takes it out of the box, removing a cardboard box once it is empty. Things on a pallet count as placed. A line asking for a `#tag`
   (`#framing_lumber`) is paid by any member of the tag.
4. **Hover the site.** Its own hover card (`ConstructionHover.cs`, beside the cursor; the F3 look-at panel stays quiet over a site)
   lists the stage, each material as have / need (teal when complete), each tool group as Ready or Missing, and what to do next.
5. **Tools are never used up.** Each tool group needs ANY ONE of its tools, in the toolbar OR placed in the yard (a table saw
   standing next to the site counts).
6. **Changed your mind?** Until the first stage is built, **Shift + right click** the dirt to remove the site; the structure item goes
   back to your toolbar. (Materials you placed stay where they are.)
7. **Build.** Right click the site itself (the dirt or the structure, not a material lying on it). The materials used by the
   stage are removed and the structure grows to the next stage; the hover list now shows the next stage. After "complete" the
   structure is finished.

**Building takes time:** a right click starts a 30 second build (`ConstructionSite.BuildSeconds`). The ped walks to the materials one source at a time (nearest first, up to 5 trips, the source vanishing as it is picked up), carries them to a random spot round the foundation (the Walk_Carry clip), then works at random spots (Dig for the foundation, Fixing_Kneeling_RT for the rest) until time is up; only then are the materials used up and the stage grows. Any movement key cancels it and nothing is used. The hover card shows the progress. Walks route round the foundation by its corners (it is a solid wall, higher on a slope) and a leg that makes no progress for a second is given up so the ped never stays stuck. Automatic walking is `PedController.AutoWalkTo`.

**Grading:** while the foundation is built the terrain is edited live (`World/TerrainGrade.cs`): the ground under the footprint rises with the build progress to the foundation's level (the highest ground under it) and the ground round it slopes down over 3 m to meet the natural ground (raise only, never dug). Items, placed objects and plants in the area ride up with it, the grass is refreshed, and cancelling puts the ground back. Nothing is saved: a built site regrades its ground when it loads, so no footing is needed.

**The finished building** (`make_structure_stages.py`, stage `complete`): log walls, roof boards, a glazed window (alpha blended glass), a stone chimney and a plank door that is its own object on a hinge (`DoorHinge` > `DoorLeaf`). A right click on it within 4 m swings the door open or shut (`ConstructionSite.ToggleDoor`, saved as `doorOpen`); its model colliders are the real mesh, so with the door open the player walks inside. Light: the walls, roof and a closed door cast shadows, so the sun and the player's flashlight / lantern (which now cast shadows, `PlayerLight`) stop at them; the window pane is its own object (`WindowGlass`) with shadow casting off, so light passes through it, and an open door leaves the doorway clear.

**Five stages** (cabin and house): foundation, framing, walls, **exterior** (roof, windows, siding, chimney masonry; the shell stands and its door works) and **finishings** (drywall, paint, flooring; the structure is finished after it). While the shell stands, a right click on the site works the door when the next stage is not ready to build.

**Foundation styles**: the foundation line is an "or" group (poured: cement bags; block: concrete blocks; brick: `#brick` or field stone; stilts: round posts). The item that paid sets `properties.look_style` (poured, block, brick, stilts). Every stage model keeps its slab in an object named `Foundation`; for block, brick or stilts the game hides it and shows the variant model `struct_foundation_<id>_<style>` (`tools/make_foundation_variants.py`) in its place, tinted by the brick or stone used. Stilts are modelled with the ground part way up their piles (an empty `GroundLevel`), skip the ground grading and the concrete footing.

**Look follows the materials** (`Growth/StructureLook.cs`): a construction material whose manifest sets `properties.look_target` (`roof` or `walls`) with `look_color`, `look_smoothness` and `look_metallic` (asset kit: Building Look fields) gives that part of the building its look when a stage is built with it: birch logs make white-cream log walls, pine brown, oak darker; corrugated steel roofing makes a silver tin roof, shingle bundles a slate one. The finished-stage models name the recoloured materials (cabin: `Log`, `Roof`; house: `Siding`, `Shingle`, `ShingleDark`). The item ids that set the looks are saved with the site (`SavedSite.looks`). Targets: `roof`, `walls` (logs, siding), `interior` (paint), `floor` (carpet, tile, flooring), `chimney` (brick, stone), `foundation` (a comma list per item; bricks are `chimney,foundation`). Models name the materials that get recoloured: `Roof`/`Shingle`/`ShingleDark`, `Log`/`Siding`, `Interior`, `Floor`, `Masonry`, `FoundationFace`. Shape is not changed, only colour and sheen. The finish items (paints, carpets and tiles, sidings, roofings, bricks, field stone) are made by `tools/make_finish_items.py`.

**Fireplace** (`Growth/Fireplace.cs`): the stage models hold the chimney as its own object `Chimney` with a firebox, a mantel-height breast inside the room, a flue hole in the cap and two empties, `FireboxPoint` and `SmokePoint`. A right click on the chimney with firewood (`properties.burn_minutes`: seasoned firewood 45 game minutes, a tied bundle 225) puts it in; with a lighter (`properties.lights_fires`, the Lighter tool) it lights the fire. It burns the fuel down in game time (up to 540 minutes held), draws logs that shrink as it burns, flames, a flickering warm light and smoke from the flue; out of fuel it goes out. `SavedSite.fuelMinutes` and `fireLit` keep it.

**Clearing:** when the foundation is built, every tree, stump, rock, bush, plant and bit of debris inside its footprint plus 0.75 m is removed, with no logs (`SiteClearing.cs`; it runs again when a save is loaded). Items, boxes and other sites are left alone. Grass is not cleared.

**On the ground:** the foundation stands on the HIGHEST ground under its footprint, and a concrete footing reaches down to the lowest, so no
side is buried and none has a gap under it. The dirt area is only the marked site: it goes as soon as the foundation is built. Every
stage has a collider (a model with none gets one box around its meshes), so the cursor, the hover card and the player meet it.

## Data (the asset kit)

Everything comes from the stage manifests under `assets/structures/<id>/stages/<stage>/`: `category_fields.construction_recipe`
(materials consumed), `required_tools` (groups; any one of each), `dimensions_m` (the stage's size; the foundation's width and
depth are the dirt area). `tools/generate_unity_asset_catalog.py` exports them as `construction_stages` on the structure's
catalog entry. A stage that has its own model shows it; the rest use a plain stand-in built in code from the stage's size
(slab, post-and-beam frame, walls, then walls with a roof) until real models exist.

**Editing the stages in the asset kit:** Structures category, open the structure (for example Small Cabin) to see its stage rail and the scheme
panel on the right. In the **Stages** table every stage row now has a block under it with that stage's **Materials** (picked with
the asset picker, with a quantity) and **Tools** (groups of "any one of these", also picked). **Save** writes them to the group's
manifest (`growth.stages[].construction_recipe` / `required_tools`, authoritative); the stage manifests are updated from it. The
catalog export reads the group first. Materials can be any asset (materials, ingredients, liquids) or a `#tag`.

## Either-or lines

A material line can be an OR group, `{"any_of": [{"item_id": "lumber_bundle_2x4_large", "quantity": 2}, {"item_id": "lumber_bundle_2x4_small", "quantity": 4}]}`:
the stage takes ANY ONE alternative in full (2 x Large 2x4 Bundle, or 4 x Small 2x4 Bundle). Build it in the stages table of the structure's
scheme panel with **+ Add "or" group** (then **+ Add alternative**). The hover card lists the alternatives under "Either of these:" with "or"
between them, each with its own count. Only the alternative that paid is used up.

## Tag equivalencies (one tag, several sizes)

A tag can say how its members relate: the SMALLEST item counts 1, and each bigger item says how many of the smallest it holds. In
`assets/_schemas/material_tags.json`, `tag_values`:

```
"tag_values": { "framing_lumber": { "unit": "studs", "values": { "lumber_bundle_2x4_small": 10, "lumber_bundle_2x4_large": 20 } } }
```

(a stud is 1 by default; a small bundle holds 10 studs, a large bundle 20). A recipe line `#framing_lumber x 20` is then paid by ANY mix
worth 20: one large bundle, two small bundles, 20 studs, one small and ten studs ... Items are picked to waste the least (the biggest
that still fits, then the smallest that covers the rest); an item that overshoots is broken down: the surplus is dropped beside the site as the next size down, then single items (ConstructionSite.GiveChange). The hover card shows the count in the
tag's unit (`12 / 20 studs`). Edit it in the asset kit: **Tag Registry**, then **Edit** on the tag (or **+ New Tag**). The editor opens for that one tag: its unit word, and
a row per member with its icon and a "holds N" box (the smallest is marked and counts 1; a bigger item says how many of the smallest it
holds), **+ Add member**, a plain-words preview ("1 Large 2x4 Bundle = 20 Stud 2x4 (studs)") and **Save Tag**. The either-or recipe line (`any_of`, above) stays for cases a tag does not fit.

## Saving

`GameSave.sites` holds each site (structure id, position, turn, stage); the materials are ordinary placed objects and are saved
with the rest of the world.
