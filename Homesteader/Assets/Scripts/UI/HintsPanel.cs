using System.Collections.Generic;
using Homesteader.Controls;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.UIElements;

namespace Homesteader.UI
{
    /// <summary>
    /// The controls hint list: a column of "[key] what it does" lines down the left of the viewport, white text with a shadow, no
    /// background, 6 px from the left edge. Keys sit in small white chips. F1 turns it off and on (remembered). The keys of
    /// rebindable actions follow the player's bindings. Styles: HudUI.uss (hints-*). Keys: docs/CONTROLS.md.
    /// </summary>
    public sealed class HintsPanel : MonoBehaviour
    {
        private const string PrefKey = "Homesteader.HintsVisible";

        private VisualElement _panel;
        private bool _visible;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        private static void Bootstrap()
        {
            if (FindAnyObjectByType<HintsPanel>() != null) return;
            var go = new GameObject("HintsPanel");
            DontDestroyOnLoad(go);
            go.AddComponent<HintsPanel>();
        }

        private void OnEnable()
        {
            _visible = PlayerPrefs.GetInt(PrefKey, 0) != 0;
            KeyBindings.Changed += Rebuild;
        }

        private void OnDisable() { KeyBindings.Changed -= Rebuild; }

        private void Update()
        {
            if (WelcomeMenuController.IsLoading) return;
            Keyboard kb = Keyboard.current;
            if (kb != null && kb.f1Key.wasPressedThisFrame && !HudBindings.KeyboardCaptured)
            {
                _visible = !_visible;
                PlayerPrefs.SetInt(PrefKey, _visible ? 1 : 0);
                PlayerPrefs.Save();
            }
            EnsureBuilt();
            if (_panel != null) _panel.style.display = _visible ? DisplayStyle.Flex : DisplayStyle.None;
        }

        private void EnsureBuilt()
        {
            UIDocument doc = FindAnyObjectByType<UIDocument>();
            VisualElement root = doc != null ? doc.rootVisualElement : null;
            if (root == null) return;
            if (_panel != null && _panel.parent == root) return;   // built, and still in this scene's document
            _panel = null;
            Rebuild();
        }

        private void Rebuild()
        {
            UIDocument doc = FindAnyObjectByType<UIDocument>();
            VisualElement root = doc != null ? doc.rootVisualElement : null;
            if (root == null) return;
            _panel?.RemoveFromHierarchy();

            _panel = new VisualElement { name = "HintsPanel", pickingMode = PickingMode.Ignore };
            _panel.AddToClassList("hints-panel");
            foreach (Hint h in Hints()) _panel.Add(Row(h));
            // Index 0: the welcome menu and its wallpaper (added later) sit on top and hide it while the menu is open.
            root.Insert(0, _panel);
        }

        private struct Hint
        {
            public string[] Keys;
            public string Text;
        }

        private static Hint H(string text, params string[] keys) { return new Hint { Keys = keys, Text = text }; }

        private static string K(BindAction a) { return KeyBindings.KeyLabel(KeyBindings.KeyOf(a)); }

        private static List<Hint> Hints()
        {
            return new List<Hint>
            {
                H("Move", K(BindAction.MoveUp), K(BindAction.MoveLeft), K(BindAction.MoveDown), K(BindAction.MoveRight)),
                H("Run", K(BindAction.Run)),
                H("Rotate the camera", K(BindAction.CameraRotateLeft), K(BindAction.CameraRotateRight)),
                H("Zoom", "Ctrl", "Wheel"),
                H("Pick a toolbar slot", "1 - 0"),
                H("Use the item, or start placing it", "Left Click"),
                H("Plant, harvest, chop, build, open a door, pick up", "Right Click"),
                H("Rotate what you are placing", K(BindAction.PlaceRotate)),
                H("Place it", "Enter"),
                H("Open a container", K(BindAction.ToggleContainer)),
                H("Drop the held item (Shift: the stack)", K(BindAction.DropItem)),
                H("Pin a build site list (over the site), drag to move", "P"),
                H("Flashlight and lantern", K(BindAction.PlayerLight)),
                H("Cutaway view inside a building", K(BindAction.ToggleCutaway)),
                H("Firewood or a lighter on a chimney", "Right Click"),
                H("Map", K(BindAction.ToggleMap)),
                H("Pause time", K(BindAction.PauseTime)),
                H("Time speed", K(BindAction.SpeedDown), K(BindAction.SpeedUp)),
                H("Phone", K(BindAction.TogglePhone)),
                H("Settings, or close a window", "Esc"),
                H("Hints on and off", "F1"),
                H("Grid overlay", "F2"),
                H("Look-at panel", "F3"),
                H("Save now", "F9"),
            };
        }

        private static VisualElement Row(Hint h)
        {
            var row = new VisualElement { pickingMode = PickingMode.Ignore };
            row.AddToClassList("hints-row");
            var keys = new VisualElement { pickingMode = PickingMode.Ignore };
            keys.AddToClassList("hints-keys");
            foreach (string k in h.Keys)
            {
                var chip = new Label(k) { pickingMode = PickingMode.Ignore };
                chip.AddToClassList("hints-key");
                keys.Add(chip);
            }
            row.Add(keys);
            var text = new Label(h.Text) { pickingMode = PickingMode.Ignore };
            text.AddToClassList("hints-text");
            row.Add(text);
            return row;
        }
    }
}
