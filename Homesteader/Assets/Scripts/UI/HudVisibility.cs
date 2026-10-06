using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.UIElements;

namespace Homesteader.UI
{
    /// <summary>
    /// F11 hides the whole HUD (toolbar, windows, minimap, phone, toasts, the F1 hints, everything the document draws) for a clean view of the
    /// game, and brings it back. The welcome menu, its loading screen and the dialogs on it are not part of the HUD and are never hidden. Not saved:
    /// the HUD is back the next time the game starts. Key list: docs/CONTROLS.md.
    /// </summary>
    public sealed class HudVisibility : MonoBehaviour
    {
        private static bool s_hidden;
        public static bool Hidden => s_hidden;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
        private static void Reset() { s_hidden = false; }

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        private static void Bootstrap()
        {
            if (FindAnyObjectByType<HudVisibility>() != null) return;
            var go = new GameObject("HudVisibility");
            DontDestroyOnLoad(go);
            go.AddComponent<HudVisibility>();
        }

        private UIDocument _doc;
        private bool _applied;       // the children have been hidden (and not yet brought back)
        private float _nextApply;

        private void Update()
        {
            Keyboard kb = Keyboard.current;
            if (kb != null && kb.f11Key.wasPressedThisFrame && !HudBindings.KeyboardCaptured && !WelcomeMenuController.IsLoading)
                s_hidden = !s_hidden;
            // Shown and nothing was hidden: nothing to do. Hidden: re-apply ten times a second (a toast or window may be added at any time).
            if (!s_hidden && !_applied) return;
            if (s_hidden && _applied && Time.unscaledTime < _nextApply) return;
            _nextApply = Time.unscaledTime + 0.1f;
            if (_doc == null) _doc = FindAnyObjectByType<UIDocument>();   // cached: a scene scan every frame was a top Update cost
            UIDocument doc = _doc;
            if (doc == null || doc.rootVisualElement == null) return;
            _applied = s_hidden;   // once shown again this pass restores everything, then the early return above takes over
            // every frame while hidden (a toast or window may be added to the document at any time), once more when it comes back
            foreach (VisualElement child in doc.rootVisualElement.Children())
            {
                if (IsMenu(child)) continue;
                if (s_hidden)
                {
                    child.style.display = DisplayStyle.None;
                    child.AddToClassList("hud-f11-hidden");
                }
                else if (child.ClassListContains("hud-f11-hidden"))
                {
                    child.style.display = StyleKeyword.Null;   // back to whatever the element showed before
                    child.RemoveFromClassList("hud-f11-hidden");
                }
            }
        }

        /// <summary>The welcome menu (its wallpaper and card tree, with the loading screen and dialogs inside it) is not the HUD.</summary>
        private static bool IsMenu(VisualElement e)
        {
            return e.name == "WelcomeWallpaper" || e.Q<VisualElement>("WelcomeMenuRoot") != null || e.Q<VisualElement>("LoadingModal") != null;
        }
    }
}
