## Old farmer rigging — handoff notes (2026-09-22)

**Status: NOT SOLVED.** No rigged file currently renders correctly. Read this before touching anything — it records what is proven, what was tried, and which of my findings were wrong.

### The symptom (Casey's description, accurate from the first report)
> "splits it head to toe, keeps the T-pose, treats each half of the body as a leg"
> later: "the feet need to come in slightly and the shoulders need to be widened"

### ROOT CAUSE, PROVEN (headless Mesh2Motion path)
The rig was **never fitted to the mesh**. Mesh2Motion's design has a human drag the skeleton into the mesh; `autorig_farmer.test.ts` skipped that step and skinned immediately. Closest-bone weighting then bound nearly everything to whichever bones were nearest.

Measured directly from the shipped GLB — **only 4 of 66 bones owned any vertex**: `calf_l`, `calf_r`, `foot_l`, `foot_r`. The **left half of the body was bound to `calf_l`, the right half to `calf_r`**, and every head/spine/arm bone owned **zero**. That is precisely "split in half, each half a leg, arms in T-pose."

### What was fixed and verified
1. **`tools/mesh2motion/src/lib/processes/edit-skeleton/RigFitter.ts`** (new) — scales/grounds a rig to a mesh's bounds + `coverage()` health check + `rebind()`. Compiles clean, eslint clean, unit-tested.
2. Wired into **both** `autorig_farmer.test.ts` and `autorig_anims.test.ts` **before** skinning, with a hard assertion `expect(coverageAfter).toBeGreaterThan(0.5)`. That assertion caught a malformed identity matrix of mine; keep it.
3. Result: **4 → 28 bones owning vertices, 10.6% → 78.8% coverage.** Arms and head bind for the first time.
4. **`export_animation_mode` defaults to `ACTIONS`** in Blender's glTF exporter — it writes **every** action that can bind to the armature, ignoring which is assigned. Importing the 87-clip library produced a 15.9 MB file. Deleting the other actions first gave **2.44 MB with only `Walk`**. This is the recurring "all 87 actions" mistake.
5. `.mcp.json` blender port was **9877, should be 9876** — every earlier Blender MCP call failed because of this.

### Blender route — what was learned, and where it went wrong
Blender was chosen because it computes bind matrices during parenting, which the headless exporter does not do correctly. It reached a **nearly-correct** result:

- `autorig_farmer` weights replaced with **deterministic nearest-bone + edge smoothing**. **Critical:** `bpy.ops.object.parent_set(type='ARMATURE_AUTO')` (bone heat) **silently produced ALL-ZERO weights** while still creating 66 vertex groups and an armature modifier — the model looked bound, exported fine, and did not deform at all. Never trust it; always verify weights are non-zero.
- With direct weighting: **0 unweighted of 3,585**, ≤4 influences/vertex, and `Walk` applied with **all 13 key bones moving** (feet 0.64, knees 0.44, arms 0.37, hips 0.06, head 0.07).
- **`export_yup=True` bakes the armature's object origin into the exported root node.** The root carried `translation (0.265, 0.576, -0.160)` and `root` bone carried the -90° X conversion → the whole figure leaned. Zeroing the armature origin fixed the lean.
- Blender 5.x API changes: **`Action.fcurves` no longer exists.** Curves live at `action.layers[*].strips[*].channelbags[*].fcurves`, and actions bind via **slots** (`action_slot`), named after the armature they were authored for (`Armature.001`). An assigned action with no slot bound evaluates to nothing.

### The remaining, UNFIXED defect
**The inverse bind matrices carry an X/Y swap against the node transforms** — in the Mesh2Motion export *and* the Blender export. Signature: `upperarm_l` node `(0.439, 2.022, -0.225)` vs bind `(-2.024, 0.434, -0.213)`; `hand_l` node `(0.750, 1.439)` vs bind `(-1.439, 0.750)`. X and Y swapped with a sign flip = a -90° X rotation applied in one place and not the other. `ibm scale` is 1.0000, so it is pure rotation, not scale corruption.

Where it comes from, in the Mesh2Motion path (**proven by reading the exporter**): `GLTFExporter` writes each joint's inverse bind matrix as
```
skeleton.boneInverses[i] * object.bindMatrix
```
(`GLTFExporter.js` ~line 2419). `SkinnedMesh.bind()` freezes `bindMatrix` at bind time. The export step then **reparents the mesh into a fresh `Scene`**, which changes `matrixWorld` but leaves `bindMatrix` stale — so a stale matrix is multiplied into every joint. Re-binding after the reparent (`mesh.bind(skeleton, mesh.matrixWorld)`) was implemented in `autorig_anims.test.ts` and did **not** resolve it; the verified numbers were unchanged. That is where to look next.

### Also proven, so nobody re-treads it
- `<model-viewer>` on the asset kit page **never upgrades the element** — `availableAnimations` is `null` (property absent), not `0`. The library is loaded by a **dynamic `import()` at `assets/index.html:167`** while the `<model-viewer>` markup is injected by string at `:17893`; if the markup runs first the element is never defined. **Every "0 animations" result from my probes was meaningless** because of this.
- **`tools/server.py` `best_model` ranks by ANIMATION CLIP COUNT** (`if clip_count >= 2: rank = 5`). A manifest could not override it, so the viewer always loaded the clip-heaviest GLB. Added a `viewer_model` manifest key that outranks the heuristic (rank 100). Keep it.
- `GlbTextureSpliceService.ts` (new) re-attaches a texture byte-wise after export — needed because Node has no canvas and `GLTFExporter` throws re-encoding images. `autorig_farmer` strips textures for jsdom parsing, so the rigged output has `images: 0` without it.

### Two competing Blender MCP addons were installed
- `scripts/addons/blender_mcp.py` — the **correct** one, protocol 9.
- `extensions/user_default/mcp/` — a **different** addon, wrong protocol. With both enabled, whichever grabbed port 9876 answered `get_addon_info` and the server got an unparseable **51-byte** reply. Disable the extension.

### My errors, recorded so they are not repeated
- I **overwrote `assets/peds/peds_old_farmer/peds_old_farmer.glb`** with a *different* Meshy generation (10,667 verts vs the original 3,585). Recovered from `tools/mesh2motion/static/staged/peds_old_farmer.glb`, byte-identical, SHA256 `DEC26DC2A198A8DE3DEE39BE49D5708E31D604402EA2C8373CB86F3B19C12935`. **The original is 3,585 verts; anything else is wrong.**
- I reported "5816 invalid animation channels" — my check used `t.get('')`, an empty-string key that always matched. The file was valid.
- I reported `ERR_ABORTED` on GLB loads as a finding — it was my own test swapping `src` mid-flight.
- I claimed I had broken the mesh/rig alignment with a Y shift; the script had **crashed on a format-string error before writing**, so nothing changed. Verify a change landed before reporting its effect.

### Key files
| path | what |
|---|---|
| `mesh_output/peds_source/peds_old_farmer_ORIGINAL.glb` | the correct mesh, 3,585 verts, textured |
| `mesh_output/peds_source/peds_old_farmer_base_color.png` | 2048² base colour |
| `tools/mesh2motion/static/staged/peds_old_farmer.glb` | byte-identical rig source |
| `mesh_output/rigged/peds_old_farmer_walk_blender.glb` | Blender-rigged + Walk — **broke when shoulders were widened; do not trust** |
| `assets/peds/peds_old_farmer/` | catalog copy + manifest |
| `tools/mesh2motion/src/lib/processes/edit-skeleton/RigFitter.ts` | the fit fix — keep |

### Blender session state
Blender 5.2.1 is open with `Mesh_0` (3,585 verts), `Armature` (66 bones), `Walk` applied, weights computed. **The last change widened the shoulders (`clavicle`/`upperarm` ±0.174 → ±0.314) and nudged feet to ±0.114, and Casey reports "it's all wrong now."** The previous export, before that change, was judged "very close".