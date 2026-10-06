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
2. **The yard.** Materials and tools count when they are within **5 m of the foundation's edge** (`ConstructionSite.YardM`).
   A faint yellow ring shows the yard while you hold something the stage needs.
3. **Bring materials.** Place them (the normal placement), or leave them lying on the ground (dropped items and loose delivery items count too). Anything inside a box or crate standing in the yard counts too (a delivery arrives in boxes), and building takes it out of the box, removing a cardboard box once it is empty. Things on a pallet count as placed. A line asking for a `#tag`
   (`#framing_lumber`) is paid by any member of the tag.
4. **Hover the site.** Its own hover card (`ConstructionHover.cs`, beside the cursor; the F3 look-at panel stays quiet over a site)
   lists the stage, each material as have / need (teal when complete), each tool group as Ready or Missing, and what to do next.
5. **Tools are never used up.** A tool inside a toolbox counts wherever the toolbox is: carried in the toolbar (any slot) or standing in the yard.
   The same goes for actions: a toolbox in the ACTIVE slot works as every tool in it (an axe in it fells a tree, a hoe tills, a pickaxe breaks
   stone ...), through `GrowthRegistry.HeldToolMatches`. Each tool group needs ANY ONE of its tools, in the toolbar OR placed in the yard (a table saw
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

## Recipe sections (all of / any one of / if)

A stage's `construction_recipe` is a LIST of nodes (the list as a whole means "all of these"). Format reference: `tools/recipe_format.py`.

- A **line**: `{"item_id": "<asset | #tag | ~equivalency>", "quantity": 4}`.
- A **section**: `{"section": "Masonry", "mode": "all" | "any", "if": {...}, "items": [nodes]}`, nestable.
  - `mode: "all"`: every child is needed. `mode: "any"`: ANY ONE child in full; a child may itself be an "all" section, so "bricks AND mortar, OR blocks AND mortar, OR 6 cement bags" is an any-section of two all-sections and a line.
  - `if`: the section only applies when an EARLIER line was paid with an item matching the spec, `{"uses": "#brick"}`, or was not, `{"not_uses": "#brick"}` (an asset id, #tag or ~equivalency). "If you use bricks you also need mortar" is `{"section": "Mortar", "if": {"uses": "#brick"}, "items": [{"item_id": "building_mortar_mix_bag", "quantity": 2}]}` placed after the brick line. A section whose condition does not hold is shown dimmed ("Not needed") and takes nothing.
- `uses` / `not_uses` are true when an EARLIER line was paid with a matching item, or simply asks for that spec: the alternative the player is working on counts before anything is placed, so the "water for the bagged mix" section shows as soon as the bagged option is the one in progress.
- The old `{"any_of": [...]}` line is still read (as an "any" section); `tools/migrate_recipes.py` converted all existing recipes.

Kit: the Stages table of a structure and the stage item's Construction Recipe card use the same tree editor (+ Material, + Section; each section has a title, All/Any, an If condition, up/down/remove).
The hover card draws the tree: once one alternative of an "Either of these" choice is met, the other alternatives are struck through and dimmed; section headers, "Either of these:" with "or" between the alternatives, "If using X:" (dimmed when it does not apply). Only what paid is used up. Code: `ConstructionSite.EvaluateNode`, `LineStatus` (tree), `PayingLeaves`.

## Tools set the build time

A stage takes 30 s with a baseline tool. Each tool carries `properties.build_speed` in its manifest (asset kit field "Build Speed"; empty = 1; 0.5 = twice as long, 2 = twice as fast). Primitive tools are below 1 (hand saw 0.4, claw hammer 0.5, shovel 0.6), power tools 1 or more (circular saw 1.2, impact driver 1.2, miter saw 1.3). Every tool group of a stage counts the FASTEST of its tools that is at the site (toolbar, a carried toolbox, the yard); the stage is as slow as its SLOWEST group (`ConstructionSite.ToolSpeedNow`). The hover card shows "Build time with these tools". Code: `ConstructionSite.EstimatedBuildSeconds`, `BuildRoutine`.

## How a stage is worked: clips and model motion

A stage may set `build_clips` (the ped's work clips while it is built, one after the other: Dig, Hoe, Push_RT, Fixing_Kneeling_RT, Chop_Tree_RT, Drag ...; empty = Dig for the foundation, Fixing_Kneeling_RT after) and `build_motion` (`tilt_up` raises the stage model's node `Mast`, `lift` hoists `Yaw`, `spin_up` fits and spins `Rotor`; the model shows in the site while the ped works). Both are in the asset kit's stage editor. A stage with no materials (an empty recipe) is built with its tools alone; a KIT structure (docs/WIND_TURBINES.md) asks for its kit item at stage 1 only and cannot be built from building materials.

## Tidying the yard

Tidying is MANUAL (user rule, 2026-10-05): finishing a building no longer tidies its yard by itself, because that moved things out of neighbouring buildings (a pump house built behind a tool shed emptied the shed's floor). The player tidies with the Tidy Area key (T: drag out a rectangle, `AreaTidy` > `YardTidy.RunArea`). `YardTidy.Run(site)` is still there but nothing calls it. What a tidy does (to the rectangle; it used to be the building yard, 5 m round the foundation): partly used piles of one material are combined into the fewest piles, loose
building materials are packed into stacks / bundles / cases / pallets where a pack exists (`GrowthRegistry.PacksOf`), what is left over (a few bags, boards) is PILED, stacked on top of each other up to
about 1.3 m, PLACED lumber, bricks and the like (every piece, stacked or not) is made up into the biggest packs it makes, then the next size, as the sawmill does (the pieces left over are stacked), and identical stackable placed items (crates, boxes) are put into neat stacks. The area is dragged on a plane at the ground, so it can cross objects, trees and buildings. Everything is laid out in LINES along one side of the building: one line per kind of thing (piles, then
packs, then single things in stacks), all turned the way of the building, spaced by their real size with a small gap, the next line further out when one is full. Everything else stays where it is.

## Choosing how to build

An "any one of" section is a QUESTION, asked up front: the stage list shows the question and one button per option, and nothing under it counts until one is chosen. Choosing removes the other
options from the list (only the chosen option's materials show); a question inside the chosen option is asked next (concrete: bagged or your own mix). A section with a single option is chosen for you.
The buttons are on the PINNED list (P over the site; the hover list just says to pin it). A **Reset choices** button at the top of the pinned list forgets the stage's choices so the questions are asked again
(not while the stage is being built). A stage cannot be built until every question is answered. Choices are saved with the site. Code: `ConstructionSite.Choose`, `ResetChoices`, `Unresolved`, `ConstructionHover.AddQuestion`.

## Mixing rule: mortar, grout, concrete and cement need water

Any recipe that calls for mortar, grout, concrete mix or cement MUST also ask for water (`~water`, liters, paid with the full jugs and the bucket of water) and have a tool group with a
wheelbarrow or a cement mixer (the mix is made in one). CONCRETE can be an `any` choice: bagged mix, or "mix your own" from cement. The water goes INSIDE each option (bagged mix: bags + water; own mix: cement + sand + aggregate + water; mortar: mortar + water), never as a separate section. Choosing cement always means
sand and aggregate (`~sand`, `~gravel`) too, and costs far less than bagged mix: the player buys cement and collects sand and aggregate (chopping stones) themselves. Mortar is the bagged
mortar mix plus water (no cement option). `python tools/check_recipes.py` audits every structure recipe.

Proportions used (the manual well, `tools/set_well_recipes.py`):

| Mix | Proportion | Water |
|---|---|---|
| Concrete, own mix | 1 cement : 2 sand : 3 aggregate by volume (dry volume = 1.54 x wet) | water/cement 0.5 by weight (about 0.5 L per kg of cement) |
| Concrete, bagged (20 lb, yields 0.15 cu ft = 0.0042 m3) | 1 bag per 0.0042 m3 | about 0.9 L per bag (1 quart; 3 to 4 quarts per 80 lb) |
| Mortar, bagged (60 lb, yields about 0.45 cu ft = 0.013 m3) | 1 bag per 0.013 m3 | about 3.5 L per bag (3 3/4 quarts) |

Sources: Quikrete data sheets (concrete mix 1101, mortar mix 1102), the 1:2:3 mix and the 0.5 water-cement ratio from common concrete mix design guides. Grout is not in a recipe yet; use the
bag's own water figure when one is added.

## Equivalencies (units, packages and piles; items OR tags as members)

A **tag** (`#flooring`) is a plain group of interchangeable items: a recipe line naming it accepts any ONE member. An **equivalency** (`~framing_lumber`) is a separate
thing, a unit system. It lives in `assets/_schemas/equivalencies.json` (shipped to the game as the mod's `equivalencies.json`):

```
"framing_lumber": { "unit": "studs", "label": "Framing Lumber", "members": [
    { "item": "lumber_stud_2x4", "value": 1 },
    { "item": "lumber_bundle_2x4_small", "value": 20 },
    { "item": "lumber_bundle_2x4_large", "value": 40 } ] }
"bricks":          { "unit": "bricks", "members": [ { "tag": "brick", "value": 1 }, { "item": "brick_pallet", "value": 500 } ] }
```

A member is an **item** or a **tag** (every item of the tag counts at that value, so the player chooses a colour or a material: any `#brick` is 1 brick), and says how many units
it is worth. A recipe line `~framing_lumber x 100` is paid by ANY mix worth 100: five large bundles, one large and three small, 100 studs ... Items are picked to waste the least
(the biggest that still fits, then the smallest that covers the rest); an item that overshoots is broken down: the surplus is dropped beside the site as the next size down, then single
items (ConstructionSite.GiveChange). The hover card shows the count in the unit (`12 / 20 studs`) and cycles through the members. If an item is reachable twice (directly and through a tag) the higher value counts.

Two unit words are special: an equivalency whose `unit` is `m3` (the bulk piles) or `m` (cable: `~romex_14_2`, `~romex_12_2`, `~romex_10_3`, a 15 m coil and a 75 m spool each,
built by `tools/make_romex.py`) is counted in cubic metres / metres and shown through `UnitFormat` in the player's units (`ConstructionHover`).

Edit them in the asset kit's **Equiv.** tab (next to Tags in the left rail): the rail lists the equivalencies, the catalog area shows the editor of the selected one (name, label, unit word, a row per member
-- an item or a tag, added with **+ Add item or tag** -- with a "worth N" box, a plain-words preview, **Save Equivalency**, **Revert**, Rename and Delete). **Add Equivalency** in the banner makes a new one. Like the tags,
you can **drag an asset card onto an equivalency in the rail** (hovering the Equiv. tab while dragging opens it) and it is added as a member worth 1 and saved. A rename rewrites every recipe that asks for `~old`; a
delete is refused while a recipe uses it. (The Tag Registry dialog has an **Equivalencies...** button that jumps to the tab.) The recipe pickers (the structure stages table, the construction recipe card) offer tags, equivalencies and assets. A tag that is a member of an
equivalency cannot be deleted until it is removed there; renaming such a tag updates the equivalency. Code: `GrowthRegistry` (`IsGroupSpec`, `EquivalencyValue`, `RegisterEquivalency`),
`ModLoader.LoadEquivalencies`, server `/api/equivalencies`, `/api/save-equivalency`, `/api/delete-equivalency`, `/api/rename-equivalency`. `tools/migrate_equivalencies.py` moved the old `tag_values`
over. The recipe sections (above) cover the cases an equivalency does not fit.

## Saving

`GameSave.sites` holds each site (structure id, position, turn, stage); the materials are ordinary placed objects and are saved
with the rest of the world.
