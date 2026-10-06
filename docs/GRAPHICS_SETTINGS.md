# Graphics settings and sky

Settings > Graphics. Code: `Assets/Scripts/UI/GraphicsOptions.cs`. Presets are mod data (`gamerules.json` `graphics`, see MODDING_GUIDE.md).

## Quality

- **Preset**: Auto, Low, Medium, High, Ultra, or Custom. Auto picks the highest preset whose `min_vram_mb` / `min_cores` the machine meets. Custom is shown whenever any quality choice below differs from the preset; picking a preset resets all of them. A preset changes how the world is drawn, never what is in it.
- **Per-preset values**: shadow distance, shadow-map resolution, cascades, render scale, anti-aliasing, small-plant draw range, terrain blend, water reflections, frame cap.
- **Anti-aliasing**: Off, FXAA, SMAA, MSAA 2x/4x/8x (MSAA is the pipeline asset's sample count; FXAA/SMAA are a camera setting).
- **Water Reflections**: sky (and clouds, stars, moon) reflected in water. Shader global `_WaterReflectionQuality`.
- **Shadows**: the sun's shadows on/off (sets the sun light's shadow mode; off skips the shadow pass).
- **Light Occlusion**: walls stop the light of lamps, the fire, the lantern and the flashlight (they cast shadows); off lets light shine through walls and saves frame rate (`LightOcclusion`, on by default).
- **Cloud Shadows**: soft shadows of drifting clouds on land (`CloudSystem.ShadowsEnabled`).
- **Wind Animation**: sway of trees, bushes, tufts and grass (`_WindSwayOff` global).
- **Colorized Mouse Cursors** (default on): the amber, bevelled cursor set; off uses the black-and-white set (`CursorManager.SetVariant`, art in `assets/hud_kit/cursors/`, chooser in `CursorHints`). A taste setting: it does not affect the preset.
- **Seasonal Lighting**: the sun and moon change colour and strength with the season (`DayNightCycle.SeasonalLighting`). Off keeps the summer palette all year; the sun path still follows the date. Changing it shows Custom in the preset dropdown.

## Display

Display mode (Fullscreen, Borderless Windowed, Windowed), resolution, V-Sync, and HUD Scale (50 to 300 percent, default follows screen height so 4K starts at 200). The choices are saved in PlayerPrefs (`Homesteader.Graphics.*`) and applied at startup.

## Clouds, stars and the moon

- `HomesteaderSky.hlsl` holds the shared procedural cloud noise, the cloud shadow factor and the star field. Included by the terrain, vegetation, grass and water shaders.
- `World/CloudSystem.cs` sets `_CloudParams` (coverage from the weather, shadow strength, wind drift offset). Coverage eases over about 20 s.
- `DayNightCycle` sets `_SkyParams.x` (night amount). The water shader shows stars and the moon's glitter on ripples at night, hidden behind clouds.
- Nothing is saved; the sky is cosmetic.

## Other changes in this commit

- F2 ground grid starts off and the toggle no longer shows a toast. The terrain material's grid is re-applied when a new terrain appears.
- The GPU grass (`GrassRenderer`, `GrassGpu`, `GrassInstanceGen.compute`, `GrassClearMask`) was removed: the ground grass is the terrain shader.
- Settings toggles are larger and their labels are clickable.
- In the editor a shader variant is compiled the first time it is used (for example Ultra's 4 shadow cascades), so the first switch to a preset can stall; later switches are instant.

## Measured

Low + FXAA about 280 fps; Ultra + MSAA 8x about 159 fps; Low + MSAA 8x about 241 fps (1920x1080, editor).
