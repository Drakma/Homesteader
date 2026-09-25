# Procedural Asset Generator - Canonical Invariants

This document is the durable record of the rules that took ~10 iterations
of debugging to land correctly. It is duplicated as a comment block at
the top of `tools/procedural_asset.py` and enforced by
`_procgen_test/test_invariants.py`.

If you change `tools/procedural_asset.py`, run the regression tests:

    python _procgen_test/test_invariants.py

If any test fails, **stop and figure out which invariant you broke before
making any further change.** All six invariants below were each the root
cause of at least one icon-iteration bug.

## Invariant 1: Rotate the object, never the camera

The camera is fixed by definition. Its basis, position, and projection
formula must not vary across calls. The only thing that varies is the
object's rotation, applied via `object_rotation(yaw_deg, pitch_deg)`.

Camera convention (UNCHANGEABLE):
- position: `(0, +inf, 0)` (viewer at +Y)
- looking at origin
- `screen.x = world.x`  (camera-right is world +X)
- `screen.y = world.z`  (camera-up is world +Z)
- `depth    = -world.y` (camera-forward is world -Y)

If a future change introduces a class or method that manipulates
camera basis vectors, this invariant is broken.

## Invariant 2: Set per-tri outward normals explicitly at build time

`Mesh.add_quad(..., normal=...)` takes its outward normal as an
explicit parameter. The renderer trusts this value and does NOT compute
normals from cross-product winding order. Cross-product normals were
inverted on every cube face in early versions; literal normal vectors
in the build functions always face the right direction.

If a future change replaces explicit normals with `cross(p1-p0, p2-p0)`
or similar, this invariant is broken.

## Invariant 3: z-buffer starts at +infinity; smaller depth wins

The depth axis is `depth = -world.y`. Front-of-object triangles (smaller
world.y) have smaller depth and must occlude back-of-object triangles.
The z-buffer initial value is `+infinity` and the comparison is
`d < zb_sub` (strictly less than).

If the initial value flips to `-infinity` or the comparison flips to
`>`, triangles will silently fail to rasterise (every render produces
a fully transparent icon).

## Invariant 4: Determinism from spec

Running `pa.generate(spec, out_dir)` twice on the same spec produces
byte-identical PNGs. There is no random seed, no time-dependent
component, no environment read beyond the spec itself.

If a future change introduces `random`, `time`, network IO, or
file-system reads outside the output directory, this invariant is broken.

## Invariant 5: Output passes `tools/validate_item_icon.py`

Every output PNG must:
- be PNG format
- be RGBA mode
- be exactly 128x128
- have an item bbox ≤ 104 px (validator tolerates 106)
- have `alpha = 0` on every pixel of x=0/x=127/y=0/y=127

`make_icon()` enforces the perimeter alpha-zero. The `fit = 0.45` ratio
in `render()` keeps the bbox comfortably under 104 px. If the icon's
shape, layout, or scale parameter changes, run the validator manually
on the new output to confirm.

## Invariant 6: NEAREST downsampling only; flat-shaded tris

The renderer supersamples at `ss=4` then downsamples with `Image.NEAREST`
to keep facet seams hard. No Lanczos, no bilinear, no smoothing. Each
rendered triangle is flat-shaded (single colour per tri). Together,
these are what produce the "visible flat polygons on every surface"
look the icon ruleset requires.

If a future change introduces Lanczos/bilinear/cubic downsampling,
icons will lose the visible-facets property at icon scale.

## What changing the rules costs

When modifying any of the six invariants, expect to re-iterate the
icon visually at least 2-3 times. The first cut will look subtly
wrong even though it passes the byte-level validator (`validate_item_icon.py`
only checks 128x128/pixel format/dimensions/perimeter — it does NOT
check the visual shape of the icon). Visual inspection is mandatory.

Reference: the corrected iso cube produced by these invariants lives at
`_procgen_test/crate_objframe/wood_crate.png` and is what every other
generated icon should match in style.
