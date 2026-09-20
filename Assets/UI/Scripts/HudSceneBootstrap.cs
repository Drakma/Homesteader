using UnityEngine;
using UnityEngine.UIElements;

namespace Homesteader.UI
{
    /// <summary>
    /// Entry point: place a single empty ``HudRoot`` GameObject in
    /// <c>SampleScene</c> with this component on it. The component
    /// attaches a <c>UIDocument</c>, locates or creates a
    /// <c>PanelSettings</c>, and attaches <c>HudUIBuilder</c>. Press
    /// play -> the HUD appears.
    ///
    /// This replaces the need to wire components manually in the
    /// inspector.
    /// </summary>
    [DefaultExecutionOrder(-100)]
    public sealed class HudSceneBootstrap : MonoBehaviour
    {
        [Tooltip("Optional override path to a PanelSettings asset. " +
                 "If empty, the script copies any HUDTree PanelSettings " +
                 "from Resources.")]
        [SerializeField] private PanelSettings _panelSettingsOverride;

        [Tooltip("Enable the kit-sourced chrome overlay (vitals, " +
                 "resources, decor) sourced from assets/hud_kit/. " +
                 "Disabled by default so we don't paint over an existing " +
                 "designed HUD until you opt in.")]
        [SerializeField] private bool _enableKitOverlay = false;

        private void Awake()
        {
            EnsureDocument();
            EnsureBuilder();
        }

        private void EnsureDocument()
        {
            var doc = GetComponent<UIDocument>();
            if (doc == null)
            {
                doc = gameObject.AddComponent<UIDocument>();
            }

            // Look for a HUDTree prefixed PanelSettings in Resources.
            if (_panelSettingsOverride == null)
            {
                var allPanels = Resources.FindObjectsOfTypeAll<PanelSettings>();
                foreach (var p in allPanels)
                {
                    if (p != null)
                    {
                        doc.panelSettings = p;
                        return;
                    }
                }
                // No PanelSettings available. Construct one in memory so
                // a Play session without manual wiring still shows the HUD.
                doc.panelSettings = ScriptableObject.CreateInstance<PanelSettings>();
                doc.panelSettings.name = "RuntimePanelSettings";
                doc.panelSettings.scaleMode = PanelScaleMode.ConstantPixelSize;
                doc.panelSettings.themeStyleSheet = ScriptableObject.CreateInstance<UnityEngine.UIElements.ThemeStyleSheet>();
            }
            else
            {
                doc.panelSettings = _panelSettingsOverride;
            }
        }

        private void EnsureBuilder()
        {
            var existing = GetComponent<HudUIBuilder>();
            if (existing == null)
            {
                existing = gameObject.AddComponent<HudUIBuilder>();
            }
#if UNITY_EDITOR
            if (_enableKitOverlay)
            {
                ApplyKitOverlayFlag(existing);
            }
#endif
        }

#if UNITY_EDITOR
        private void ApplyKitOverlayFlag(HudUIBuilder target)
        {
            var so = new UnityEditor.SerializedObject(target);
            var prop = so.FindProperty("_enableKitOverlay");
            if (prop != null)
            {
                prop.boolValue = true;
                so.ApplyModifiedProperties();
            }
        }
#endif
    }
}
