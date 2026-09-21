# Icon & Model Standards

Every generated asset follows the same conventions, so the catalog stays
visually and structurally consistent. These rules are worth knowing because
they explain why things look the way they do — and what to check when a
generated asset looks wrong.

## Icons

Icons are standardized to **128×128 RGBA**:

- Art occupies at most **104px**, leaving a **12px margin** on every side
- The **perimeter alpha is zero** — nothing touches the edge
- **No borders** and no baked-in frames
- Backgrounds are fully transparent, with de-spilled edges so no halo of the
  original background colour survives anti-aliasing

The house style is **3D faceted**, and icons face **left** by default. A
consistent facing direction is what makes a grid of icons read as one coherent
set rather than a pile of unrelated pictures.

Regenerating an icon (🔄 in the item modal, or **Regen Icons** in the banner)
re-runs generation against these rules, which is the fix when an icon came back
off-style.

## Models

### External view, always

100% of concept generations for **buildings and objects** must be an
**external view** — the complete outer facade, walls, and roof, seen from
outside.

Interiors, cutaways, and indoor camera perspectives are **not** used, unless an
exterior view naturally sees inside through an open door or window. An interior
concept must never be handed to 3D reconstruction.

<blockquote>

**Why this matters:** reconstruction works from the silhouette and outer form.
An interior or cutaway concept gives it no coherent outside to build, so the
resulting mesh comes back malformed. This is the single most common cause of a
bad building model.

</blockquote>

### Naming and selection

Model filenames encode their state, and the app reads those conventions:

| Pattern | Meaning |
| --- | --- |
| `_walk` / `_run` | Animated — preferred as the primary model |
| `_rigged` | Has a skeleton, but no animation |
| anything else | Plain static mesh |

A rigged-and-animated asset therefore displays the animation rather than a
static mesh, because the app deliberately prefers the most complete version
available.

## Rigging

Rigging is done in **Blender**, not by the app. Requests queue the work and a
session performs it.

Two skeleton conventions are in use:

- **Unity Mecanim Humanoid** (via Mixamo) for characters
- **Generic** for quadrupeds — animals use a Blender animal rig rather than a
  humanoid skeleton

This is why the rigging picker asks for a rig type: a quadruped given a humanoid
skeleton produces broken animation, so the choice has to be made explicitly
rather than guessed.

## World units

The target engine is **Unity 6**, at **1 unit = 1 metre**, **Y-up**, with
**+Z forward**. Models are authored to these units, so a 1.3-metre corn plant is
1.3 units tall in the engine.

## Where these rules live

The canonical references are:

- `docs/ITEM_ICON_STYLE_GUIDE.md` — the visual rules for icons
- `docs/FREE_PIPELINE_GUIDE.md` — the generation pipeline, step by step
- `docs/UNITY_INTEGRATION_GUIDE.md` — import settings, Mecanim setup, materials
- `assets/API_REFERENCE.md` — the full REST API for the local server

## Generation pipelines

Icon generation defaults to a **100% free stack** (FLUX.1 [schnell] via Hugging
Face Spaces, Google AI Studio, or Pollinations). 3D models default to
**Hunyuan3D-2.0**, also free.

Paid services — **Meshy.ai** and **Creative Claw** — are available but strictly
**opt-in per request**, chosen from the Generation Pipeline dropdown. They are
never used implicitly, and the credit cost is confirmed before spending
anything.
