using System;
using System.Collections.Generic;
using Homesteader.Growth;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using UnityEngine.UIElements;

namespace Homesteader.UI
{
    /// <summary>
    /// Graphics options: quality presets, display mode, resolution, V-Sync and the HUD scale.
    ///
    /// The one rule: an option changes how the world is DRAWN, never what is in it. Tree and bush positions, felled and picked records all come from the
    /// world seed and are saved by position, so density is never a quality setting. The presets (GameRules.Graphics, mod data in gamerules.json) scale
    /// shadows, render scale, anti-aliasing, how far small plants are drawn, the terrain's biome blend and the fps cap.
    ///
    /// "Auto" picks the highest preset the machine meets (graphics memory and CPU cores). The choice, the display mode, the resolution, V-Sync and the
    /// HUD scale are saved in PlayerPrefs and applied at startup. The URP asset is copied at runtime, so the player's choices never write to the project.
    /// </summary>
    public static class GraphicsOptions
    {
        public const string AutoId = "auto";
        private const string PresetKey = "Homesteader.Graphics.Preset";
        private const string ModeKey = "Homesteader.Graphics.DisplayMode";
        private const string ResWKey = "Homesteader.Graphics.ResW";
        private const string ResHKey = "Homesteader.Graphics.ResH";
        private const string VsyncKey = "Homesteader.Graphics.Vsync";
        private const string HudScaleKey = "Homesteader.Graphics.HudScale";
        private const string AaKey = "Homesteader.Graphics.Antialiasing";   // "" = the preset's choice
        private const string CloudShadowsKey = "Homesteader.Graphics.CloudShadows";
        private const string ShadowsKey = "Homesteader.Graphics.Shadows";   // -1 / unset = the preset's choice
        private const string WindKey = "Homesteader.Graphics.WindAnimation";
        private const string WaterReflKey = "Homesteader.Graphics.WaterReflections";   // -1 / unset = the preset's choice

        public static readonly string[] DisplayModes = { "Fullscreen", "Borderless Windowed", "Windowed" };

        /// <summary>Anti-aliasing choices: id and the name in the dropdown. FXAA and SMAA smooth edges after the picture is drawn (cheap); MSAA smooths them while it is drawn (costs more, needs more graphics memory, and is the sharpest).</summary>
        public static readonly string[] AaIds = { "off", "fxaa", "smaa", "msaa2", "msaa4", "msaa8" };
        public static readonly string[] AaNames = { "Off", "FXAA (fast)", "SMAA (balanced)", "MSAA 2x", "MSAA 4x", "MSAA 8x (slowest)" };

        public static GameRules.GraphicsPreset Current { get; private set; }
        private static UniversalRenderPipelineAsset _runtimeAsset;
        private static readonly Dictionary<UIDocument, PanelSettings> PanelCopies = new Dictionary<UIDocument, PanelSettings>();

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        private static void Bootstrap() { ApplyAll(); }

        /// <summary>Applies everything the player saved (or the Auto choice on a first run).</summary>
        public static void ApplyAll()
        {
            ApplyPreset(SavedPresetId());
            ApplyDisplayMode(SavedMode());
            if (PlayerPrefs.HasKey(ResWKey) && PlayerPrefs.HasKey(ResHKey) && SavedMode() != 1)
                Screen.SetResolution(PlayerPrefs.GetInt(ResWKey), PlayerPrefs.GetInt(ResHKey), ModeToScreen(SavedMode()));
            if (PlayerPrefs.HasKey(VsyncKey)) QualitySettings.vSyncCount = PlayerPrefs.GetInt(VsyncKey) == 1 ? 1 : 0;
            ApplyHudScale(SavedHudScale());
        }

        // ------------------------------------------------------------------ presets

        public static string SavedPresetId() => PlayerPrefs.GetString(PresetKey, GameRules.Graphics.DefaultPreset);

        public static List<string> PresetNames()
        {
            var names = new List<string> { "Auto" };
            foreach (GameRules.GraphicsPreset p in GameRules.Graphics.Presets) names.Add(p.Name);
            return names;
        }

        /// <summary>The preset a machine should use: the highest one whose graphics memory and CPU core needs it meets.</summary>
        public static GameRules.GraphicsPreset DetectPreset()
        {
            GameRules.GraphicsPreset best = GameRules.Graphics.Presets[0];
            int vram = SystemInfo.graphicsMemorySize, cores = SystemInfo.processorCount;
            foreach (GameRules.GraphicsPreset p in GameRules.Graphics.Presets)
                if (vram >= p.MinVramMb && cores >= p.MinCores) best = p;
            return best;
        }

        public static void SetPreset(string id)
        {
            PlayerPrefs.SetString(PresetKey, id);
            // Picking a preset takes back every individual choice (anti-aliasing, reflections, shadows, clouds, wind).
            foreach (string k in new[] { AaKey, WaterReflKey, ShadowsKey, CloudShadowsKey, WindKey }) PlayerPrefs.DeleteKey(k);
            PlayerPrefs.Save();
            ApplyPreset(id);
        }

        private static VisualElement s_root;
        private const string CustomName = "Custom";

        /// <summary>True when the player has changed any quality choice away from what the current preset sets.</summary>
        public static bool IsCustom()
        {
            if (Current == null) return false;
            if (!string.Equals(EffectiveAa(), Current.Antialiasing, StringComparison.OrdinalIgnoreCase)) return true;
            if (WaterReflectionsOn() != Current.WaterReflections) return true;
            if (ShadowsOn() != (Current.ShadowDistance > 0f)) return true;
            return !CloudShadowsOn() || !WindAnimationOn();
        }

        /// <summary>Shows Custom in the preset dropdown while any quality choice differs from the preset, otherwise the preset itself.</summary>
        private static void RefreshPresetDropdown()
        {
            var preset = s_root?.Q<DropdownField>("GfxPresetDropdown");
            if (preset == null || preset.choices == null || preset.choices.Count == 0) return;
            int idx = 0;
            if (IsCustom()) idx = preset.choices.Count - 1;
            else
            {
                string saved = SavedPresetId();
                for (int i = 0; i < GameRules.Graphics.Presets.Count; i++)
                    if (string.Equals(GameRules.Graphics.Presets[i].Id, saved, StringComparison.OrdinalIgnoreCase)) idx = i + 1;
            }
            preset.SetValueWithoutNotify(preset.choices[idx]);
            UpdateDetected(s_root);
        }

        /// <summary>Re-reads every quality control from the saved state (after a preset changed them).</summary>
        private static void RefreshControls(VisualElement root)
        {
            root.Q<DropdownField>("GfxAntiAliasingDropdown")?.SetValueWithoutNotify(AaNames[Mathf.Max(0, Array.IndexOf(AaIds, EffectiveAa()))]);
            root.Q<Toggle>("GfxWaterReflectionsToggle")?.SetValueWithoutNotify(WaterReflectionsOn());
            root.Q<Toggle>("GfxShadowsToggle")?.SetValueWithoutNotify(ShadowsOn());
            root.Q<Toggle>("GfxCloudShadowsToggle")?.SetValueWithoutNotify(CloudShadowsOn());
            root.Q<Toggle>("GfxWindAnimationToggle")?.SetValueWithoutNotify(WindAnimationOn());
            RefreshPresetDropdown();
        }

        public static void ApplyPreset(string id)
        {
            GameRules.GraphicsPreset p = null;
            if (!string.IsNullOrEmpty(id) && !string.Equals(id, AutoId, StringComparison.OrdinalIgnoreCase))
                p = GameRules.Graphics.Presets.Find(x => string.Equals(x.Id, id, StringComparison.OrdinalIgnoreCase));
            if (p == null) p = DetectPreset();
            Current = p;

            UniversalRenderPipelineAsset urp = RuntimePipeline();
            if (urp != null)
            {
                urp.shadowDistance = Mathf.Max(0.1f, p.ShadowDistance);
                urp.mainLightShadowmapResolution = Mathf.Clamp(p.ShadowResolution, 256, 8192);
                urp.shadowCascadeCount = Mathf.Clamp(p.ShadowCascades, 1, 4);
                urp.renderScale = Mathf.Clamp(p.RenderScale, 0.5f, 1.5f);
            }
            ApplyAntialiasing(EffectiveAa());
            ApplyShadows(ShadowsOn());
            Homesteader.World.CloudSystem.ShadowsEnabled = CloudShadowsOn();

            Homesteader.World.VegetationFocusFade.RangeScale = Mathf.Max(0.3f, p.SmallPlantRange / Homesteader.World.VegetationFocusFade.ReferenceRange);
            Shader.SetGlobalFloat("_TerrainBlendQuality", p.TerrainBlend ? 1f : 0f);
            Shader.SetGlobalFloat("_WaterReflectionQuality", WaterReflectionsOn() ? 1f : 0f);
            Shader.SetGlobalFloat("_WindSwayOff", WindAnimationOn() ? 0f : 1f);
            // With V-Sync on the monitor sets the rate; the cap is only for V-Sync off.
            Application.targetFrameRate = QualitySettings.vSyncCount > 0 ? -1 : (p.MaxFps > 0 ? p.MaxFps : -1);
        }

        /// <summary>Soft shadows of drifting clouds on the ground (cheap; on by default).</summary>
        public static bool CloudShadowsOn() => PlayerPrefs.GetInt(CloudShadowsKey, 1) == 1;

        public static void SetCloudShadows(bool on)
        {
            PlayerPrefs.SetInt(CloudShadowsKey, on ? 1 : 0);
            PlayerPrefs.Save();
            Homesteader.World.CloudSystem.ShadowsEnabled = on;
            RefreshPresetDropdown();
        }

        /// <summary>The sun's shadows. Off skips the whole shadow pass (the biggest single fps saving on weak graphics cards).</summary>
        public static bool ShadowsOn()
        {
            int saved = PlayerPrefs.GetInt(ShadowsKey, -1);
            return saved >= 0 ? saved == 1 : (Current == null || Current.ShadowDistance > 0f);
        }

        public static void SetShadows(bool on)
        {
            PlayerPrefs.SetInt(ShadowsKey, on ? 1 : 0);
            PlayerPrefs.Save();
            ApplyShadows(on);
            RefreshPresetDropdown();
        }

        private static void ApplyShadows(bool on)
        {
            Light sun = RenderSettings.sun;
            if (sun == null)
                foreach (Light l in UnityEngine.Object.FindObjectsByType<Light>(FindObjectsInactive.Exclude))
                    if (l.type == LightType.Directional) { sun = l; break; }
            if (sun != null) sun.shadows = on ? LightShadows.Soft : LightShadows.None;
        }

        /// <summary>Trees, plants and grass sway in the wind (on by default; some players prefer still plants).</summary>
        public static bool WindAnimationOn() => PlayerPrefs.GetInt(WindKey, 1) == 1;

        public static void SetWindAnimation(bool on)
        {
            PlayerPrefs.SetInt(WindKey, on ? 1 : 0);
            PlayerPrefs.Save();
            Shader.SetGlobalFloat("_WindSwayOff", on ? 0f : 1f);
            RefreshPresetDropdown();
        }

        public static bool WaterReflectionsOn()
        {
            int saved = PlayerPrefs.GetInt(WaterReflKey, -1);
            return saved >= 0 ? saved == 1 : (Current != null && Current.WaterReflections);
        }

        public static void SetWaterReflections(bool on)
        {
            PlayerPrefs.SetInt(WaterReflKey, on ? 1 : 0);
            PlayerPrefs.Save();
            Shader.SetGlobalFloat("_WaterReflectionQuality", on ? 1f : 0f);
            RefreshPresetDropdown();
        }

        public static string EffectiveAa()
        {
            string saved = PlayerPrefs.GetString(AaKey, "");
            if (!string.IsNullOrEmpty(saved) && Array.IndexOf(AaIds, saved) >= 0) return saved;
            return Current != null && Array.IndexOf(AaIds, Current.Antialiasing) >= 0 ? Current.Antialiasing : "off";
        }

        public static void SetAntialiasing(string id)
        {
            PlayerPrefs.SetString(AaKey, id);
            PlayerPrefs.Save();
            ApplyAntialiasing(id);
            RefreshPresetDropdown();
        }

        /// <summary>MSAA is the pipeline asset's sample count; FXAA and SMAA are a camera setting (all cameras that carry URP camera data).</summary>
        private static void ApplyAntialiasing(string id)
        {
            UniversalRenderPipelineAsset urp = RuntimePipeline();
            int samples = id == "msaa2" ? 2 : id == "msaa4" ? 4 : id == "msaa8" ? 8 : 1;
            if (urp != null) urp.msaaSampleCount = samples;
            AntialiasingMode mode = id == "fxaa" ? AntialiasingMode.FastApproximateAntialiasing
                : id == "smaa" ? AntialiasingMode.SubpixelMorphologicalAntiAliasing : AntialiasingMode.None;
            foreach (Camera cam in Camera.allCameras)
            {
                var data = cam.GetUniversalAdditionalCameraData();
                if (data == null) continue;
                data.antialiasing = mode;
                data.antialiasingQuality = AntialiasingQuality.Medium;
            }
        }

        /// <summary>A private copy of the URP asset, so changing it in the game never writes to the project's asset.</summary>
        private static UniversalRenderPipelineAsset RuntimePipeline()
        {
            if (_runtimeAsset != null) return _runtimeAsset;
            var current = GraphicsSettings.currentRenderPipeline as UniversalRenderPipelineAsset;
            if (current == null) return null;
            _runtimeAsset = UnityEngine.Object.Instantiate(current);
            QualitySettings.renderPipeline = _runtimeAsset;
            return _runtimeAsset;
        }

        // ------------------------------------------------------------------ display

        private static FullScreenMode ModeToScreen(int mode) => mode == 0 ? FullScreenMode.ExclusiveFullScreen : mode == 1 ? FullScreenMode.FullScreenWindow : FullScreenMode.Windowed;

        public static int SavedMode()
        {
            if (PlayerPrefs.HasKey(ModeKey)) return Mathf.Clamp(PlayerPrefs.GetInt(ModeKey), 0, 2);
            return Screen.fullScreenMode == FullScreenMode.ExclusiveFullScreen ? 0 : Screen.fullScreenMode == FullScreenMode.Windowed ? 2 : 1;
        }

        public static void SetDisplayMode(int mode)
        {
            PlayerPrefs.SetInt(ModeKey, mode);
            PlayerPrefs.Save();
            ApplyDisplayMode(mode);
        }

        private static void ApplyDisplayMode(int mode)
        {
            // Borderless windowed always covers the whole desktop at its resolution; the other two use the chosen resolution.
            FullScreenMode target = ModeToScreen(mode);
            if (Screen.fullScreenMode != target) Screen.fullScreenMode = target;
        }

        /// <summary>The resolutions the display offers, one entry per width x height, largest first.</summary>
        public static List<Vector2Int> Resolutions()
        {
            var list = new List<Vector2Int>();
            foreach (Resolution r in Screen.resolutions)
            {
                var v = new Vector2Int(r.width, r.height);
                if (!list.Contains(v)) list.Add(v);
            }
            list.Sort((a, b) => b.x != a.x ? b.x.CompareTo(a.x) : b.y.CompareTo(a.y));
            return list;
        }

        public static void SetResolution(int w, int h)
        {
            PlayerPrefs.SetInt(ResWKey, w);
            PlayerPrefs.SetInt(ResHKey, h);
            PlayerPrefs.Save();
            Screen.SetResolution(w, h, ModeToScreen(SavedMode()));
        }

        public static bool Vsync => QualitySettings.vSyncCount > 0;

        public static void SetVsync(bool on)
        {
            QualitySettings.vSyncCount = on ? 1 : 0;
            PlayerPrefs.SetInt(VsyncKey, on ? 1 : 0);
            PlayerPrefs.Save();
            if (Current != null) Application.targetFrameRate = on ? -1 : (Current.MaxFps > 0 ? Current.MaxFps : -1);
        }

        // ------------------------------------------------------------------ HUD scale

        /// <summary>The scale a first run starts with: 1 up to 1080p, then in step with the screen height (4K: 2), rounded to a quarter.</summary>
        public static float DefaultHudScale() => Mathf.Clamp(Mathf.Round(Screen.height / 1080f * 4f) / 4f, 1f, 2.5f);

        public static float SavedHudScale() => Mathf.Clamp(PlayerPrefs.GetFloat(HudScaleKey, DefaultHudScale()), 0.5f, 3f);

        public static void SetHudScale(float scale)
        {
            scale = Mathf.Clamp(scale, 0.5f, 3f);
            PlayerPrefs.SetFloat(HudScaleKey, scale);
            PlayerPrefs.Save();
            ApplyHudScale(scale);
        }

        /// <summary>Scales every HUD document (the HUD, the phone, the menus are all in it) through a private copy of its PanelSettings.</summary>
        public static void ApplyHudScale(float scale)
        {
            foreach (UIDocument doc in UnityEngine.Object.FindObjectsByType<UIDocument>(FindObjectsSortMode.None))
            {
                if (doc.panelSettings == null) continue;
                if (!PanelCopies.TryGetValue(doc, out PanelSettings copy) || copy == null)
                {
                    copy = UnityEngine.Object.Instantiate(doc.panelSettings);
                    PanelCopies[doc] = copy;
                    doc.panelSettings = copy;
                }
                copy.scaleMode = PanelScaleMode.ConstantPixelSize;
                copy.scale = scale;
            }
        }

        // ------------------------------------------------------------------ the Settings > Graphics page

        /// <summary>Wires the new controls of the Graphics page (called by GraphicsSettingsPanel whenever it resolves the UI).</summary>
        public static void WireUi(VisualElement root)
        {
            s_root = root;
            var preset = root.Q<DropdownField>("GfxPresetDropdown");
            if (preset != null)
            {
                var names = PresetNames();
                names.Add(CustomName);
                preset.choices = names;
                preset.RegisterValueChangedCallback(evt =>
                {
                    int i = preset.index;
                    if (i < 0 || i >= names.Count - 1) { RefreshPresetDropdown(); return; }   // Custom is a state, not a choice
                    SetPreset(i == 0 ? AutoId : GameRules.Graphics.Presets[i - 1].Id);
                    RefreshControls(root);
                });
                preset.tooltip = "Auto picks the best preset for this computer. Presets change shadows, render scale, anti-aliasing, how far small plants are drawn and the terrain blend, never what is in the world.";
            }
            RefreshPresetDropdown();

            var aa = root.Q<DropdownField>("GfxAntiAliasingDropdown");
            if (aa != null)
            {
                aa.choices = new List<string>(AaNames);
                aa.SetValueWithoutNotify(AaNames[Mathf.Max(0, Array.IndexOf(AaIds, EffectiveAa()))]);
                aa.RegisterValueChangedCallback(evt => { if (aa.index >= 0) SetAntialiasing(AaIds[aa.index]); });
                aa.tooltip = "Smooths jagged edges. FXAA and SMAA are cheap; MSAA is sharper but costs more frame rate and graphics memory (8x the most). Each preset picks a sensible default.";
            }

            var refl = root.Q<Toggle>("GfxWaterReflectionsToggle");
            if (refl != null)
            {
                refl.SetValueWithoutNotify(WaterReflectionsOn());
                refl.RegisterValueChangedCallback(evt => SetWaterReflections(evt.newValue));
                refl.tooltip = "The sky reflected in rivers, ponds and lakes (the sun's glint is always on). Costs very little.";
            }

            // Clicking a row's label flips its checkbox too (the box itself is small).
            root.Query<VisualElement>(className: "settings-row").ForEach(row =>
            {
                Toggle tg = row.Q<Toggle>(className: "hs-toggle");
                Label lb = row.Q<Label>(className: "settings-label");
                if (tg != null && lb != null) lb.RegisterCallback<ClickEvent>(_ => tg.value = !tg.value);
            });

            var shadows = root.Q<Toggle>("GfxShadowsToggle");
            if (shadows != null)
            {
                shadows.SetValueWithoutNotify(ShadowsOn());
                shadows.RegisterValueChangedCallback(evt => SetShadows(evt.newValue));
                shadows.tooltip = "The sun's shadows. Turning them off gives the biggest frame-rate gain on older graphics cards.";
            }

            var cloudShadows = root.Q<Toggle>("GfxCloudShadowsToggle");
            if (cloudShadows != null)
            {
                cloudShadows.SetValueWithoutNotify(CloudShadowsOn());
                cloudShadows.RegisterValueChangedCallback(evt => SetCloudShadows(evt.newValue));
                cloudShadows.tooltip = "Soft shadows of drifting clouds across the land. Costs almost nothing.";
            }

            var wind = root.Q<Toggle>("GfxWindAnimationToggle");
            if (wind != null)
            {
                wind.SetValueWithoutNotify(WindAnimationOn());
                wind.RegisterValueChangedCallback(evt => SetWindAnimation(evt.newValue));
                wind.tooltip = "Trees, bushes and grass sway in the wind. Turn off for perfectly still plants.";
            }

            var mode = root.Q<DropdownField>("GfxDisplayModeDropdown");
            if (mode != null)
            {
                mode.choices = new List<string>(DisplayModes);
                mode.SetValueWithoutNotify(DisplayModes[SavedMode()]);
                mode.RegisterValueChangedCallback(evt => { if (mode.index >= 0) SetDisplayMode(mode.index); });
                mode.tooltip = "Fullscreen: exclusive. Borderless Windowed: a window the size of the desktop, easy to alt-tab. Windowed: a normal window.";
            }

            var res = root.Q<DropdownField>("GfxResolutionDropdown");
            if (res != null)
            {
                var list = Resolutions();
                var names = new List<string>();
                foreach (Vector2Int v in list) names.Add($"{v.x} x {v.y}");
                res.choices = names;
                int cur = list.FindIndex(v => v.x == Screen.width && v.y == Screen.height);
                res.SetValueWithoutNotify(cur >= 0 ? names[cur] : $"{Screen.width} x {Screen.height}");
                res.RegisterValueChangedCallback(evt =>
                {
                    int i = res.index;
                    if (i >= 0 && i < list.Count) SetResolution(list[i].x, list[i].y);
                });
                res.tooltip = "The size of the game window or screen. Borderless Windowed always uses the desktop size.";
            }

            var vsync = root.Q<Toggle>("VsyncToggle");
            if (vsync != null)
            {
                vsync.SetValueWithoutNotify(Vsync);
                vsync.RegisterValueChangedCallback(evt => SetVsync(evt.newValue));
                vsync.tooltip = "Match the monitor's refresh rate. Off lets the preset's fps cap (if any) rule.";
            }

            var hud = root.Q<Slider>("GfxHudScaleSlider");
            if (hud != null)
            {
                hud.lowValue = 50f;
                hud.highValue = 300f;
                hud.SetValueWithoutNotify(SavedHudScale() * 100f);
                hud.RegisterValueChangedCallback(evt => SetHudScale(Mathf.Round(evt.newValue / 5f) * 5f / 100f));
                hud.tooltip = "Makes the whole interface bigger or smaller (50% to 300%). On a 4K monitor the default is 200%.";
                var reset = root.Q<Button>("GfxHudScaleResetBtn");
                if (reset != null)
                {
                    reset.tooltip = "Back to the size that suits this screen.";
                    reset.RegisterCallback<ClickEvent>(evt =>
                    {
                        PlayerPrefs.DeleteKey(HudScaleKey);
                        float d = DefaultHudScale();
                        hud.SetValueWithoutNotify(d * 100f);
                        ApplyHudScale(d);
                    });
                }
            }
        }

        private static void UpdateDetected(VisualElement root)
        {
            var label = root.Q<Label>("GfxPresetDetected");
            if (label == null) return;
            bool auto = string.Equals(SavedPresetId(), AutoId, StringComparison.OrdinalIgnoreCase);
            label.text = auto && Current != null
                ? $"Auto chose {Current.Name} ({SystemInfo.graphicsMemorySize} MB graphics memory, {SystemInfo.processorCount} CPU cores)."
                : "";
            label.style.display = label.text.Length > 0 ? DisplayStyle.Flex : DisplayStyle.None;
        }
    }
}
