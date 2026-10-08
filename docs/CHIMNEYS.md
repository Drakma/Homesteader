# Chimneys

Chimneys are NOT part of the structure models any more. They are built from kits, on any outside wall of a finished building (`Assets/Scripts/Growth/Chimney.cs`).

## The kits

`building_chimney_kit_brick` (Brick Chimney Kit) and `building_chimney_kit_stone` (Fieldstone Chimney Kit), sold at the depot (`tools/make_chimney_kits.py`: pallet of masonry, a flue liner,
a bag of mortar mix). Manifest: `placeable: false`, `attach_surface: "chimney"` (schema `_base_mounting`, asset kit "Mounts On" > "Chimney (kit)").

## Building one

Hold a kit, left click an outside wall of a FINISHED building (from outside, or from inside: the cutaway lets the cursor through the walls it hides) to bring out the preview, left click again
or press Enter to build it (blue = it can go there, red = not, the toast says why). The kit is used up. Whichever side you aim from, the result is the same:

- the STACK stands outside the wall (0.9 m wide, 0.6 m out), from the ground up, with a cap and a flue hole;
- inside, a mantel-height breast (0.9 m wide, 0.45 m out, 1.15 m high) with a firebox, a mantel shelf and a hearth in front;
- the stack rises 1 m past the roof where it goes through: the top is the highest roof surface found over the stack and the wall beside it, plus 1 m (the walls' top when there is no roof there).

It is refused on a window or a door: rays are cast from outside through the whole width of the stack (and 20 cm either side), floor to eaves; any spot where a ray does not meet plain wall
(an opening, an open door) or meets a door, window, frame, trim or porch part says "A window or door is in the way." It is also refused when something is mounted there, when anything is
standing where the stack, the breast or the hearth go (furniture, trees, other chimneys; the porch), within 1.6 m of another chimney, on an inside wall ("A chimney goes on an outside wall."),
or when the player is too far (3.5 m).

## Using and removing

The firebox is a working fireplace (`Growth/Fireplace.cs`): right click the chimney with firewood in hand (an item with `burn_minutes`) to lay it, right click with a lighter to light it;
it lights the room and smokes from the flue while the fuel lasts. The fuel and the fire are saved with the chimney. Shift + right click with a wrench takes it down (the firebox must be
empty): the kit goes back to the toolbar.

## Cutaway view

While the cutaway (V) is open on the building the player is in, the chimney's STACK (the outside part, up through the roof) is hidden with the roof, shadows kept, and its collider is looked through by the cursor. The breast, firebox and hearth inside stay (`StructureCutaway`, the `ChimneyStack` part of the chimney).

## Saved

`GameSave.chimneys` (`SavedChimney`: kit, the building's place in the saved sites, position and turn in the building's space, wall thickness, bottom and top, brick or stone, fuel, lit).
Older saves have none: their buildings simply have no chimney now.

## In the models

The stage models carry no chimney (`tools/strip_chimneys.py` took the old `Chimney`, `FireboxPoint` and `SmokePoint` nodes out of the built GLBs; the generators build one only when
`make_structure_stages.BUILD_CHIMNEYS` is True). The chimney masonry lines were taken out of the structure recipes. WAILA names a chimney, its height and what is in the fireplace.
