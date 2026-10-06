using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using UnityEngine.UIElements;

namespace Homesteader.UI
{
    /// <summary>
    /// Wires the Graphics section (Saturation / Contrast / Brightness sliders) inside the existing Settings
    /// dialog (WelcomeMenu.uxml's "SettingsDialog", opened via the menu's Settings button and owned entirely
    /// by WelcomeMenuController - this class only adds behaviour to its Graphics sliders, it doesn't manage
    /// the dialog's own open/close) to the scene's Global Volume ColorAdjustments override.
    ///
    /// These change in real time - URP re-evaluates the volume stack every frame, so there's nothing to
    /// rebuild or reload, the values just take effect on the next frame.
    ///
    /// Deliberately edits Volume.profile (the runtime-instantiated copy Unity hands back), not sharedProfile -
    /// a player's slider drag is a per-session preference, not a change to the checked-in design-time asset.
    /// Chosen values persist across sessions via PlayerPrefs and are re-applied on load.
    ///
    /// Bootstraps itself on scene load, same pattern as WailaPanel/StatsOverlay.
    /// </summary>
    public sealed class GraphicsSettingsPanel : MonoBehaviour
    {
        private const string SaturationKey = "Homesteader.Graphics.Saturation";
        private const string ContrastKey = "Homesteader.Graphics.Contrast";
        private const string BrightnessKey = "Homesteader.Graphics.Brightness";

        // Defaults match the values baked into the design-time asset (SampleSceneProfile), so Reset returns to
        // what the scene ships with rather than some arbitrary neutral point.
        private const float DefaultSaturation = 35f;
        private const float DefaultContrast = 10f;
        private const float DefaultBrightness = 0.2f;

        private Slider _saturationSlider;
        private Slider _contrastSlider;
        private Slider _brightnessSlider;
        private Button _resetBtn;

        private ColorAdjustments _colorAdjustments;
        private bool _wired;
        private bool _applyingFromCode;

        public static GraphicsSettingsPanel Instance { get; private set; }

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        private static void Bootstrap()
        {
            if (FindAnyObjectByType<GraphicsSettingsPanel>() != null) return;
            var go = new GameObject("GraphicsSettingsPanel");
            DontDestroyOnLoad(go);
            go.AddComponent<GraphicsSettingsPanel>();
        }

        private void Awake()
        {
            Instance = this;
        }

        private float _nextResolve;

        private void Update()
        {
            // WelcomeMenuController rebuilds its UI tree (fresh Slider instances) after a scene reload
            // (New Game / Continue) - if that happens after we've already wired up, our held references
            // point at now-destroyed elements (panel == null once removed from any UIDocument) and every
            // drag or Reset click on the NEW, actually-visible sliders would silently go nowhere. Re-resolve
            // whenever that happens instead of latching _wired forever from the first successful resolve.
            if (_wired && _saturationSlider != null && _saturationSlider.panel == null)
                _wired = false;

            // the scene scans in ResolveReferences are expensive: retry about once a second, not every frame
            if (!_wired && Time.unscaledTime >= _nextResolve) { _nextResolve = Time.unscaledTime + 1f; ResolveReferences(); }
        }

        private void ResolveReferences()
        {
            var doc = FindAnyObjectByType<UIDocument>();
            if (doc == null) return;
            var root = doc.rootVisualElement;
            if (root == null) return;

            _saturationSlider = root.Q<Slider>("GfxSaturationSlider");
            _contrastSlider = root.Q<Slider>("GfxContrastSlider");
            _brightnessSlider = root.Q<Slider>("GfxBrightnessSlider");
            _resetBtn = root.Q<Button>("GfxResetBtn");
            if (_saturationSlider == null || _contrastSlider == null || _brightnessSlider == null) return;

            var volume = FindAnyObjectByType<Volume>();
            // The Volume can come into existence after this script starts finding the sliders (scene/bootstrap
            // ordering) - don't latch _wired until it's actually there, or the sliders end up permanently
            // disconnected: found once, _colorAdjustments stays null forever, every drag silently no-ops.
            if (volume == null) return;

            var profile = volume.profile; // runtime copy - intentional, see class remarks
            if (!profile.TryGet(out _colorAdjustments))
                _colorAdjustments = profile.Add<ColorAdjustments>(true);

            LoadAndApplySavedValues();

            _saturationSlider.RegisterValueChangedCallback(evt => OnSliderChanged(SaturationKey, evt.newValue, v => _colorAdjustments.saturation.value = v));
            _contrastSlider.RegisterValueChangedCallback(evt => OnSliderChanged(ContrastKey, evt.newValue, v => _colorAdjustments.contrast.value = v));
            _brightnessSlider.RegisterValueChangedCallback(evt => OnSliderChanged(BrightnessKey, evt.newValue, v => _colorAdjustments.postExposure.value = v));

            _resetBtn.Clickable()?.RegisterCallback<ClickEvent>(evt => ResetToDefaults());

            GraphicsOptions.WireUi(root);   // preset, display mode, resolution, V-Sync, HUD scale

            _wired = true;
        }

        private void OnSliderChanged(string prefKey, float value, System.Action<float> apply)
        {
            if (_applyingFromCode || _colorAdjustments == null) return;
            apply(value);
            PlayerPrefs.SetFloat(prefKey, value);
            PlayerPrefs.Save();
        }

        private void LoadAndApplySavedValues()
        {
            if (_colorAdjustments == null) return;

            float sat = PlayerPrefs.GetFloat(SaturationKey, DefaultSaturation);
            float con = PlayerPrefs.GetFloat(ContrastKey, DefaultContrast);
            float bri = PlayerPrefs.GetFloat(BrightnessKey, DefaultBrightness);

            _colorAdjustments.saturation.overrideState = true;
            _colorAdjustments.saturation.value = sat;
            _colorAdjustments.contrast.overrideState = true;
            _colorAdjustments.contrast.value = con;
            _colorAdjustments.postExposure.overrideState = true;
            _colorAdjustments.postExposure.value = bri;

            _applyingFromCode = true;
            _saturationSlider.SetValueWithoutNotify(sat);
            _contrastSlider.SetValueWithoutNotify(con);
            _brightnessSlider.SetValueWithoutNotify(bri);
            _applyingFromCode = false;
        }

        public void ResetToDefaults()
        {
            PlayerPrefs.SetFloat(SaturationKey, DefaultSaturation);
            PlayerPrefs.SetFloat(ContrastKey, DefaultContrast);
            PlayerPrefs.SetFloat(BrightnessKey, DefaultBrightness);
            PlayerPrefs.Save();
            LoadAndApplySavedValues();
        }
    }
}
