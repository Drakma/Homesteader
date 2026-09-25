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
    [DefaultExecutionOrder(-90)]
    [RequireComponent(typeof(UIDocument))]
    public sealed class HudUIBuilder : MonoBehaviour
    {
        [Header("Drag the UXML assets here OR leave null and use the " +
                "Resources fallback below.")]
        [SerializeField] private VisualTreeAsset _hudAsset;

        [Header("Resources fallback. Loads from any " +
                "Assets/Resources/<Name>.uxml.")]
        [SerializeField] private string _hudResource = "HUDTree/HudUI";

        [Header("Kit-sourced chrome overlay (assets/hud_kit/).")]
        [Tooltip("When enabled, an additional overlay UXML is mounted as a " +
                 "sibling tree and a kit USS is loaded as a sibling " +
                 "stylesheet. HudUI.uxml already imports HudUI_kit.uss " +
                 "directly so kit chrome applies without the overlay tree; " +
                 "the overlay remains opt-in for decorative-only stages, " +
                 "but live values need to be bound into it.")]
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
            if (root == null) { return; }
            root.Clear();

            var hud = LoadAsset(_hudAsset, _hudResource);
            if (hud != null)
            {
                var tree = hud.CloneTree();
                tree.style.width = new StyleLength(new Length(100f, LengthUnit.Percent));
                tree.style.height = new StyleLength(new Length(100f, LengthUnit.Percent));
                tree.style.position = Position.Absolute;
                tree.style.left = 0;
                tree.style.top = 0;
                tree.style.right = 0;
                tree.style.bottom = 0;
                root.Add(tree);
            }

            // Always load the kit USS as a sibling style sheet so the
            // chrome that overrides the tint placeholders is present, even
            // if the inspector flag toggles the UXML overlay.
            try
            {
                var kitUss = Resources.Load<StyleSheet>(_kitOverlayUssResource);
                if (kitUss != null)
                {
                    root.styleSheets.Add(kitUss);
                }
            }
            catch (System.Exception ex)
            {
                Debug.LogWarning("[HudUI] Failed to attach kit USS: " + ex.Message);
            }

            if (hud == null)
            {
                Debug.LogError("[HudUI] No HUD UXML resolved. Drag the " +
                               "HudUI.uxml into the inspector slot OR put " +
                               "it under Assets/Resources/HUDTree/ and rebuild.");
            }

            // Ensure bindings reconnect to the newly mounted visual tree
            var bindings = GetComponent<HudBindings>();
            if (bindings != null)
            {
                bindings.ResolveReferences();
            }
        }

        // No-op kept for backward compatibility. The kit overlay UXML
        // (HUDOverlay_kit) is not loaded because HudUI.uxml already
        // renders every element bindings write to; mounting duplicates
        // would render ghost rows.
        private void AttachKitOverlay(VisualElement root) { }

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
