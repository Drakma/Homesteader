# Handoff: Welcome Menu, Terrain Generation, and UI Fixes

**Date:** 2026-09-27
**Status:** Multiple issues remain unresolved despite multiple fix attempts.

---

## Project Context

Homesteader is a Unity 6 (URP) survival/farming game. The codebase was originally Unreal Engine 5 and has been partially migrated. The game uses Unity UI Toolkit (UXML/USS) for all HUD elements, with a `UIDocument` on the main scene that hosts the HUD.

---

## What Was Done (Completed)

### 1. Documentation Updates
- Updated all docs from UE5 references to Unity 6 (`FOLIAGE_GUIDE.md`, `GROUND_TILES_GUIDE.md`, `GRID_AND_GROUND_STANDARDS.md`, `GROUND_BLENDING_SETUP.md`, `ITEM_ICON_STYLE_GUIDE.md`, `ITEM_EXPANSION_SESSION_STATE.md`, `assets/ground/README.md`, `assets/textures/README.md`, `tools/README.md`)
- Retired `UNREAL_3D_INTEGRATION_GUIDE.md` and `UNREAL_INTEGRATION_GUIDE.md` with redirect notices
- Created `docs/HUD_TREE.md` documenting the full HUD visual tree

### 2. MCP Configuration
- Added `homesteader-asset-kit`, `unity-mcp`, and `mesh2motion` servers to `C:\Users\casey\.codegpt-plus-plus\mcp_config.json`

### 3. Welcome Menu (Created)
- **Files:**
  - `Assets/Resources/HUDTree/WelcomeMenu.uxml` — layout
  - `Assets/Resources/HUDTree/WelcomeMenu.uss` — styling
  - `Assets/Scripts/UI/WelcomeMenuController.cs` — controller
- **Features implemented:**
  - New Game, Continue, Save/Load (same row), Settings (placeholder), Exit buttons
  - Background wallpaper image (`Assets/Resources/HUDTree/WelcomeBackground.jpg`)
  - Progress bar inside the card, below Exit
  - ESC toggles menu (open/close), background only shows on startup
  - Bootstraps via `[RuntimeInitializeOnLoadMethod]`, attaches to existing HUD `UIDocument`
  - `DontDestroyOnLoad` so it persists across scene reloads

### 4. Terrain Generation
- Added `GenerateTerrainAsync()` coroutine to `HomesteaderTerrainGenerator.cs` with progress reporting (`GenerationProgress`, `IsGenerating`, `GenerationPhase`)
- Added `Random.InitState(worldSeed)` to both `GenerateTerrain()` and `GenerateTerrainAsync()`
- Made water features seed-dependent: `pondCenter`, `RiverSeedOffset`, `GetRiverCenterX`, `GetRiverHalfWidth`, `GetPondRadius`, `GetBranchCenterX`
- Added `InvalidateSeedCache()` method and `_cachedPondCenter` field
- Fixed `TerrainGeneratorBootstrap` to register `SceneManager.sceneLoaded` callback (was only running once via `RuntimeInitializeOnLoadMethod`)

### 5. Terrain Height Detector
- Created `Assets/Scripts/TerrainHeightDetector.cs` — centralized static utility for terrain surface detection
- Wired into `PlacementController`, `AnimalMover`, `AnimalSpawner`, `WorldItem.TryDrop`, `GameRules` zone creation, `GridBrightnessToggle`, `PlantedGrowth.Plant()`
- `PedController.Start()` snaps player to ground surface (was dropping 3m)

### 6. Old Settings Window Removed
- Removed the old HUD settings window from `HudUI.uxml` and `HudBindings.cs` (gear icon, sliders, toggles, all methods)
- Fixed `HudWiringMenu.cs` — added `EditorApplication.isPlaying` guard to prevent `MarkSceneDirty` during play mode

### 7. MiniMap Fix
- Fixed `MiniMap` to register `SceneManager.sceneLoaded` callback (same issue as TerrainGeneratorBootstrap — `RuntimeInitializeOnLoadMethod` only fires once)

---

## Outstanding Issues (Unresolved)

### Issue 1: Wallpaper Does Not Fill the Screen
**Symptom:** The background image shows as a strip across the middle of the screen, not filling the full viewport.

**What was tried:**
- USS `background-image` on `.welcome-root` with `scale-and-crop` → strip
- USS `background-image` on `.welcome-root` with `scale-to-fit` → strip
- C# `style.backgroundImage` on `tree` (TemplateContainer) with explicit `position: absolute; left:0; top:0; right:0; bottom:0; width:100%; height:100%` → strip
- C# `style.backgroundImage` on `_root` (UIDocument root panel) → showed but rendered behind HUD
- Created dedicated `_wallpaper` VisualElement inserted between HUD and welcome card → still a strip

**Likely root cause:** The `TemplateContainer` returned by `CloneTree()` may not be sizing its children correctly. The `_root` panel from `HudBindings` may have layout constraints that prevent full-screen children. The wallpaper element's parent chain may not have explicit dimensions all the way up.

**What to investigate:**
- Check if `_root` (the `VisualElement` from `HudBindings.Instance.GetComponent<UIDocument>().rootVisualElement`) has explicit width/height or flex layout
- Try setting `_wallpaper` style directly in C#: `style.position = Position.Absolute; style.left = 0; style.top = 0; style.right = 0; style.bottom = 0;`
- Check if the `UIDocument` itself has a fixed size that's smaller than the screen
- Consider using a separate `UIDocument` for the welcome menu instead of sharing with the HUD

### Issue 2: Welcome Card and Wallpaper Stay Visible After New Game Generation Completes
**Symptom:** After clicking New Game, the progress bar reaches 100%, but the welcome card and wallpaper remain on screen. The menu does not close.

**What was tried:**
- `RunAsyncGeneration` calls `Hide()` after generation completes
- `Hide()` adds `welcome--hidden` class to `_menuRoot` and clears background from `_wallpaper`
- USS specificity fix: changed `.welcome--hidden { display: none; }` to `.welcome-root.welcome--hidden { display: none; }` (compound selector, higher specificity)
- Same fix applied to `.loading-section.loading--hidden`
- Added debug log `[WelcomeMenu] RunAsyncGeneration complete, calling Hide()...` — **but console logs were empty, suggesting the code may not be running or the rebuild didn't take effect**

**Likely root cause:** The USS changes may not be taking effect. The console was empty when checked, which means either:
1. The rebuild didn't actually recompile the changed scripts
2. The UXML/USS files weren't refreshed by Unity
3. The `Hide()` method is being called but the USS class toggle isn't working

**What to investigate:**
- Enter Play mode, click New Game, and check Unity Console for the debug logs
- If no logs appear, the scripts weren't recompiled — try `Assets > Reimport All` or manually delete the `Library/ScriptAssemblies` folder
- If logs appear but menu stays visible, add `Debug.Log(_menuRoot.ClassListContains("welcome--hidden"))` after `Hide()` to verify the class was toggled
- Check if the USS file is actually being loaded — add a deliberate syntax error to verify Unity is reading it

### Issue 3: Water Features Don't Change After New Game
**Symptom:** After New Game generates new terrain, the water features (pond, river) appear unchanged or missing.

**What was tried:**
- Made `pondCenter` seed-dependent with `System.Random(worldSeed + 1000)`
- Added `RiverSeedOffset` to phase-shift river sine waves
- Added `InvalidateSeedCache()` to clear `_cachedPondCenter` when seed changes
- `WelcomeMenuController.ApplyNewSeedAfterTerrainReady` calls `generator.InvalidateSeedCache()` after setting the new seed
- Added debug log `[TerrainGen] pondCenter computed for seed X: (px, pz)` — **but console was empty**

**Likely root cause:** Same as Issue 2 — the code changes may not be taking effect. The empty console logs are the strongest signal that the rebuild isn't working.

**What to investigate:**
- Verify the scripts are actually recompiling (check `Library/ScriptAssemblies` timestamp)
- Check if `GenerateTerrainAsync()` is actually being called (look for `[TerrainGen] GenerateTerrainAsync started with seed X` log)
- If the async method isn't called, trace the `OnNewGame` → `ReloadScene` → `OnSceneLoaded` → `ApplyNewSeedAfterTerrainReady` flow
- The `TerrainGeneratorBootstrap` now registers `SceneManager.sceneLoaded`, but verify it's actually creating a new generator on scene reload

---

## Key Files Modified

| File | Changes |
|---|---|
| `Assets/Resources/HUDTree/WelcomeMenu.uxml` | Welcome menu layout |
| `Assets/Resources/HUDTree/WelcomeMenu.uss` | Welcome menu styling, specificity fixes |
| `Assets/Resources/HUDTree/WelcomeBackground.jpg` | Background image (from Downloads) |
| `Assets/Scripts/UI/WelcomeMenuController.cs` | Menu controller, New Game flow, progress bar |
| `Assets/Scripts/HomesteaderTerrainGenerator.cs` | Async generation, seed-dependent water, caching |
| `Assets/Scripts/TerrainHeightDetector.cs` | New file — centralized terrain height utility |
| `Assets/Scripts/UI/HudBindings.cs` | Removed old settings window |
| `Assets/Resources/HUDTree/HudUI.uxml` | Removed old settings window elements |
| `Assets/Scripts/PedController.cs` | Snap player to ground on Start |
| `Assets/Scripts/GameSaveManager.cs` | Snap player to ground on save restore |
| `Assets/Scripts/PlacementController.cs` | Use TerrainHeightDetector |
| `Assets/Scripts/Animals/AnimalMover.cs` | Use TerrainHeightDetector |
| `Assets/Scripts/Animals/AnimalSpawner.cs` | Use TerrainHeightDetector |
| `Assets/Scripts/WorldItem.cs` | Use TerrainHeightDetector for drops |
| `Assets/Scripts/GameRules.cs` | Use TerrainHeightDetector for zones |
| `Assets/Scripts/GridBrightnessToggle.cs` | Use TerrainHeightDetector |
| `Assets/Scripts/PlantedGrowth.cs` | Use TerrainHeightDetector for planting |
| `Assets/Scripts/MiniMap.cs` | Register sceneLoaded callback |
| `Assets/Scripts/TerrainGeneratorBootstrap.cs` | Register sceneLoaded callback |
| `Assets/Editor/HudWiringMenu.cs` | isPlaying guard |

---

## Architecture Notes

### Welcome Menu Bootstrap Flow
1. `[RuntimeInitializeOnLoadMethod]` → `WelcomeMenuController` creates itself, finds HUD `UIDocument`, clones `WelcomeMenu.uxml` into `_root`
2. On startup: shows menu with wallpaper, pauses game
3. ESC: toggles menu (without wallpaper on re-open)
4. New Game: sets `PlayerPrefs["Homesteader.NewWorldSeed"]`, calls `SceneManager.LoadScene` to reload
5. `TerrainGeneratorBootstrap` runs on `sceneLoaded`, creates terrain generator, generates terrain synchronously
6. `WelcomeMenuController.OnSceneLoaded` fires, starts `ApplyNewSeedAfterTerrainReady` coroutine
7. Coroutine waits for menu UI rebuild, sets new seed, calls `InvalidateSeedCache()`, starts `GenerateTerrainAsync()`
8. `RunAsyncGeneration` polls `IsGenerating`/`GenerationProgress` each frame, updates progress bar
9. When done: calls `Hide()` to close menu

### Known Race Conditions
- `InitWhenReady` and `ApplyNewSeedAfterTerrainReady` run as parallel coroutines after scene reload
- The menu UI must be rebuilt (`Build()` called by `InitWhenReady`) before `ApplyNewSeedAfterTerrainReady` can show the progress bar
- Fixed by adding a wait loop in `ApplyNewSeedAfterTerrainReady` that blocks until `_loadingSection != null && _menuRoot != null`

### USS Specificity Issue
- `.welcome--hidden { display: none; }` was being overridden by `.welcome-root { ... }` because both are class selectors (same specificity) and `.welcome-root` came later in the file
- Fixed by using compound selector `.welcome-root.welcome--hidden { display: none; }` (two classes = higher specificity)
- Same pattern applied to `.loading-section.loading--hidden`

---

## Recommendations for Next Session

1. **First:** Verify the rebuild is actually working. Enter Play mode, check console for any of the debug logs. If empty, the scripts aren't recompiling — delete `Library/ScriptAssemblies` and force a fresh compile.

2. **Wallpaper:** Try a completely different approach — use a `SpriteRenderer` or `Camera` background instead of UI Toolkit, or create a separate `UIDocument` just for the welcome menu so it doesn't share layout constraints with the HUD.

3. **Menu not closing:** Add more granular debug logs inside `Hide()` itself to verify each step. Check if `_menuRoot` is null (it might be null after scene reload if `Build()` hasn't run).

4. **Water features:** Once the rebuild is confirmed working, the debug logs should show the seed and pond center values. If the pond center changes but water still doesn't appear, the issue may be in the terrain material/shader not updating after regeneration.

5. **Consider simplifying:** The current approach of sharing the HUD's `UIDocument` and inserting elements at specific indices is fragile. A dedicated `UIDocument` for the welcome menu would avoid all the z-ordering and layout issues.
