using UnityEngine;
using UnityEngine.UIElements;

namespace Homesteader.UI
{
    /// <summary>
    /// Runtime builder for the procedural HUD. Loads UXML trees onto a
    /// PanelSettings-bound root VisualElement so the HUD appears in
    /// the SampleScene once the script is attached to a GameObject.
    ///
    /// UXML assets MUST be dragged into the inspector slots, OR they
    /// must be placed in a Resources folder (e.g. Assets/Resources/)
    /// and named so <see cref="Resources.Load{T}(string)"/> can find
    /// them by the resource path strings exposed in the inspector.
    /// </summary>
    [RequireComponent(typeof(UIDocument))]
    public sealed class HudUIBuilder : MonoBehaviour
    {
        [Header("Drag the UXML assets here OR leave null and use the " +
                "Resources fallback below.")]
        [SerializeField] private VisualTreeAsset _hudAsset;
        [SerializeField] private VisualTreeAsset _toolbarAsset;
        [SerializeField] private VisualTreeAsset _formAsset;
        [SerializeField] private VisualTreeAsset _windowAsset;

        [Header("Resources fallback. Loads from any " +
                "Assets/Resources/<Name>.uxml.")]
        [SerializeField] private string _hudResource = "HUDTree/HudUI";
        [SerializeField] private string _toolbarResource = "HUDTree/Toolbar";
        [SerializeField] private string _formResource = "HUDTree/FormPanel";
        [SerializeField] private string _windowResource = "HUDTree/WindowPanel";

        [Header("Kit-sourced chrome overlay (assets/hud_kit/).")]
        [Tooltip("When enabled, an additional overlay UXML is mounted as a " +
                 "sibling tree and the kit USS is loaded as a sibling " +
                 "stylesheet. The original status bar / toolbar / window " +
                 "keep working unchanged.")]
        [SerializeField] private bool _enableKitOverlay = false;
        [SerializeField] private VisualTreeAsset _kitOverlayAsset;
        [SerializeField] private string _kitOverlayResource = "HUDTree/HUDOverlay_kit";
        [SerializeField] private string _kitOverlayUssResource = "HUDTree/HudUI_kit";

        private void Awake()
        {
            var doc = GetComponent<UIDocument>();
            if (doc == null)
            {
                Debug.LogError("[HudUI] No UIDocument on the same GameObject. " +
                               "Add one and assign a PanelSettings asset.");
                return;
            }

            var root = doc.rootVisualElement;
            root.Clear();
            root.AddToClassList("screen-root");

            // Resolve the four UXML trees. Try inspector slot first,
            // then Resources fallback.
            var hud = LoadAsset(_hudAsset, _hudResource);
            var toolbar = LoadAsset(_toolbarAsset, _toolbarResource);
            var form = LoadAsset(_formAsset, _formResource);
            var window = LoadAsset(_windowAsset, _windowResource);

            if (hud != null) root.Add(hud.CloneTree());

            if (toolbar != null)
            {
                var t = toolbar.CloneTree();
                t.style.position = Position.Absolute;
                t.style.left = 0;
                t.style.right = 0;
                t.style.bottom = 8;
                root.Add(t);
            }

            if (window != null)
            {
                var w = window.CloneTree();
                w.style.position = Position.Absolute;
                w.style.left = 0;
                w.style.right = 0;
                w.style.top = 0;
                w.style.bottom = 0;
                w.pickingMode = PickingMode.Ignore;
                root.Add(w);
            }

            if (form != null)
            {
                var f = form.CloneTree();
                f.style.position = Position.Absolute;
                f.style.left = 24;
                f.style.right = 24;
                f.style.top = 80;
                f.style.bottom = 120;
                root.Add(f);
            }

            if (_enableKitOverlay)
            {
                AttachKitOverlay(root);
            }

            if (hud == null && toolbar == null && form == null && window == null)
            {
                Debug.LogError("[HudUI] No UXML assets resolved. Drag them " +
                               "into the inspector slots OR put them under " +
                               "Assets/Resources/HUDTree/ and rebuild.");
            }
        }

        private void AttachKitOverlay(VisualElement root)
        {
            var overlay = LoadAsset(_kitOverlayAsset, _kitOverlayResource);
            if (overlay != null)
            {
                var ov = overlay.CloneTree();
                ov.style.position = Position.Absolute;
                ov.style.left = 0;
                ov.style.right = 0;
                ov.style.top = 0;
                ov.style.bottom = 0;
                ov.pickingMode = PickingMode.Ignore;
                root.Add(ov);
            }

            // Load the kit USS as a sibling style sheet so the kit classes
            // (vital-icon, resource-icon, btn-kit-*, decor-*) resolve
            // against the kit atlases baked from assets/hud_kit/.
            try
            {
                var kitUss = Resources.Load<StyleSheet>(_kitOverlayUssResource);
                if (kitUss != null)
                {
                    root.styleSheets.Add(kitUss);
                }
                else
                {
                    Debug.LogWarning("[HudUI] Kit overlay USS not found at " +
                                     "Resources path " + _kitOverlayUssResource);
                }
            }
            catch (System.Exception ex)
            {
                Debug.LogWarning("[HudUI] Failed to attach kit USS: " + ex.Message);
            }
        }

        private static VisualTreeAsset LoadAsset(VisualTreeAsset inspector,
                                                  string resourcesPath)
        {
            if (inspector != null) return inspector;
            try
            {
                var fromResources = Resources.Load<VisualTreeAsset>(resourcesPath);
                if (fromResources != null) return fromResources;
            }
            catch (System.Exception ex)
            {
                Debug.LogWarning($"[HudUI] Resources.Load failed for " +
                                  $"{resourcesPath}: {ex.Message}");
            }
            return null;
        }
    }
}
