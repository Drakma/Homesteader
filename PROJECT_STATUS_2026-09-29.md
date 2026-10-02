# Homesteader Project Status — 2026-09-29

## Executive Summary
The project is mid-refactor on **terrain/grass/weather rendering** (GPU compute grass appears to be a new, not-yet-integrated addition) and on a **cow growth-stage content expansion**, with a **known-buggy welcome menu** still unresolved from the prior session. Nothing is currently running, there are no pending paid asset-generation requests, and the last recorded compile was clean. Nothing has been pushed to `origin/main` in 21 commits.

---

## 1. Engine / Pipeline Direction
- **Target**: Unity 6 (6000.6.0f1), 1 unit = 1 m, Y-up/+Z-forward.
- **Asset pipeline policy history** (documented in `CLAUDE.md`/`AGENTS.md`):
  - Old: free stack (FLUX + Hunyuan3D) — retired.
  - Then: Meshy text-to-3D only, lowpoly — superseded.
  - **Current (2026-09-28)**: Gemini reference image → Meshy **image-to-3D** (`meshy-t2`, `model_type='smart-topology'`, mandatory) → Blender scale/ground script → icon rendered from the model. Everything costs money; balance/approval required before any spend.
- **Known open bug**: meshy-t2 models sometimes show fragmented/jagged shading on curved organic surfaces in Unity/glTFast at runtime (root cause unconfirmed).

---

## 2. Repository State
- **Branch**: `main`
- **Commits ahead of origin/main**: 21 (not pushed)
- **Last commit**: `912b8a27` — massive terrain/weather overhaul (terraced heightmap, procedural biome textures, GPU grass, weather particles, land ownership, loading modals)
- **Uncommitted changes on top**: ~1,000 lines across:
  - `HomesteaderTerrainGenerator.cs` (+385 lines) — water mask/shore-depth refinements, terracing tweaks
  - `GrassRenderer.cs` (523 changed lines) — rewrite alongside new **untracked** `GrassGpu.shader` + `Assets/Resources/Compute/` folder → GPU compute-based grass pass in progress
  - `PhoneController.cs` (+257) — phone UI work
  - `WeatherEffectsManager.cs`, `WaterSurface.shader`, `WailaPanel.cs`, `HoverOutline.cs`, `IsometricLockedCamera.cs`, `StatsOverlay.cs`
  - Scene/lighting profile and HUD UXML/USS tweaks
  - New untracked `GraphicsSettingsPanel.cs` — graphics-settings UI being added but not yet wired/committed

### Compile Health
- Checked `Homesteader/Logs/Editor.log` (694 MB, last written 2026-09-28 18:08)
- Earlier in that session: CS errors in `HomesteaderTerrainGenerator.cs` (iterator/return mismatch, `res` not in scope)
- **Zero `error CS` lines after the final successful "Reloading assemblies" cycle** (line 5901750) — project was left in a compiling state at last edit
- Not re-verified since (no Unity process running now)

---

## 3. Documented Open Issues
From `docs/HANDOFF_WELCOME_MENU.md` (2026-09-27, newest non-terrain handoff):

1. **Welcome-menu wallpaper** renders as a horizontal strip instead of filling the screen (UI Toolkit layout issue)
2. **Welcome card/wallpaper don't hide** after "New Game" generation completes (USS specificity / possible stale rebuild)
3. **Water features** (pond/river) don't regenerate with a new seed on New Game

The doc's leading theory: script recompilation wasn't actually taking effect during that session — worth double-checking first before re-debugging the symptoms.

---

## 4. Content / Catalog
- **Master catalog**: 540 indexed items across 16 categories (`assets/README.md`)
- **In-progress content change**: Holstein cow growth lifecycle expanded from 2 stages to 3 (calf → yearling → adult)
  - New `animal_yearling` stage folder added (model + icon + manifest present, GLB format)
  - Manifest already updated in `assets/ranching/holstein_cow/holstein_cow.json`
  - Change is uncommitted and mirrored between `assets/ranching/...` and packaged `Homesteader/mods/homesteader/ranching/...` copy
  - Old `.mtl`/loose base-color PNGs being deleted in favor of embedded-texture GLBs (consistent with "GLB is the standard model format" rule)
- **Asset requests**: 0 pending in kit queue (`list_asset_requests` returned 0)
- **Asset-request watcher log**: stale (last write 2026-09-17) — nothing actively mid-flight in that pipeline

---

## 5. Processes / Environment
- **No Unity Editor or kit server process currently running** (checked `Get-Process`; only unrelated Node/Python processes from other tooling alive, no listening HTTP ports on usual dev ports)
- **Submodule reference**: `tools/.diffusers-src` exists in git config but has no matching `.gitmodules` entry (harmless but flags stale submodule pointer if anyone runs `git submodule status`)

---

## 6. Build Artifacts
- `Build/` folder exists with `Homesteader.exe` and `Homesteader_Data/` — a standalone build is present

---

## Next Steps (if desired)
- Verify current compile state by launching Unity in batch mode
- Continue the welcome-menu bugs (wallpaper layout, hide-on-complete, seed-based water regen)
- Finish/commit the cow growth-stage work
- Integrate the new GPU compute grass pass
- Push 21 commits to `origin/main`