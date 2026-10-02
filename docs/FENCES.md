# Fences and gates

The fence builder (`Growth/FenceBuilder.cs`, `Growth/FenceRun.cs`). Paths and roads are meant to follow the same click-a-line way of building;
for now only fences are built.

## Building a fence

Select a fence item in the hotbar (a manifest with `properties.fence_style`: Wood Fence Section, Wire Fence Section).

| Input | Action |
| :--- | :--- |
| Left click | Place a post on the ground (snapped to 0.5 m). Owned land only, not in water, not on top of the last post |
| Left click on the FIRST post | Close the fence into an enclosure (needs at least 3 posts) |
| Enter | Finish an open fence line (at least 2 posts) |
| Backspace | Take the last post back |
| Esc, or choosing another slot | Throw the plan away |

A card beside the cursor shows how many panels and posts the plan needs and how many are in the hotbar. Nothing is used until the fence is built;
then the posts (the item named by `fence_post_item`, one per post, intermediate posts included) and the panels (`ceil(run length /
fence_panel_m)` per run between posts) are taken from the hotbar, and the fencing is filled in between the posts, following the ground.
Not enough: a warning says what is missing and the plan stays.

**The ped builds it.** Once the plan is accepted the ped sets the first post and then walks the fence line, a section at a time (one panel and the
post at its end), kneeling to work on each for about 2.4 seconds; the section appears when the work is done and its panel and post come out of the
hotbar then. It stands beside the fence on the side it started on (inside a closed fence if it was inside). Pressing a movement key or Esc stops it:
what is built stands (saved as a partly built fence), the rest is not made and its materials stay in the hotbar.

## Gates

Select a gate item (`properties.gate_width_m`, Wood / Metal Farm Gate) and left click a built fence: the fence there is taken out for the gate's
width, hinge and latch posts stand at the gap, and the gate (one item from the hotbar) stands in it. Right click a gate within 4 m to open or shut
it (it swings away from you; shut it blocks, open it does not). A gate needs a run at least its width + 0.4 m long and room next to other gates.

## Stuck inside

A fence is a barrier (colliders on the Ignore Raycast layer: they stop the player and the animals, the mouse sees through). Completing a CLOSED
fence while the player stands inside it with no gate in the hotbar asks first: "You would be stuck inside" (Build it anyway / Keep editing).

## Data

- Item properties (asset kit item popup, `_base.schema.json`): `fence_style` (wood, wire), `fence_panel_m`, `fence_height_m`, `fence_post_item`;
  `gate_width_m`, `gate_style` (wood, metal).
- Save: `GameSave.fences` (style, items, posts, closed, gates with segment / distance / width / open).
- The geometry is procedural (one mesh per fence; wood = posts and 3 rails, wire = thin posts and 5 strands).
