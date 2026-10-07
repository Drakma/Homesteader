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
            if (_panel != null) _panel.style.display = _visible && !HudVisibility.Hidden ? DisplayStyle.Flex : DisplayStyle.None;
        }

        private float _nextEnsure;

        private void EnsureBuilt()
        {
            if (_panel != null && _panel.panel != null && Time.unscaledTime < _nextEnsure) return;   // built and attached: look again about once a second
            _nextEnsure = Time.unscaledTime + 1f;
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
                H("Swap two toolbar slots", "Drag one onto the other"),
                H("Take down something mounted on a wall, ceiling or roof, or a solar panel or mount: wrench in hand", "Shift", "Right Click"),
                H("Switch a light (lamp, ceiling, wall or post light) off or on", "Right Click"),
                H("Take up a bolted-down fitting (kitchen, bathroom, living room and lighting pieces): wrench in hand", "Right Click"),
                H("Take ONE piece from a placed bundle, stack or case", "Right Click"),
                H("Take the whole bundle, stack or case (what is left stays in it)", "Shift + Right Click"),
                H("Cut a tree stump out with a chainsaw (leaves a pile of wood chips)", "Right Click"),
                H("Lay an uncut log on a sawmill's track (the log in hand)", "Left Click"),
                H("Sawmill with a log on it: choose the lumber to cut (Shift: take the log off)", "Right Click"),
                H("Stand the held item on a wall shelf", "Left Click"),
                H("Wire cutters in hand: a dish or yagi, then a router, a switch, a device, lays a Cat6 cable (again unplugs it)", "Right Click"),
                H("Slide a rackmount router or switch into a wall rack", "Left Click"),
                H("A dish, yagi or access point in hand, aimed at a roof: put it up there (R turns it)", "Left Click"),
                H("Turn a dish, yagi or access point that is up on a roof (Shift: the other way)", K(BindAction.PlaceRotate)),
                H("Take a router or switch out of a wall rack", "Right Click"),
                H("Take a thing off a wall shelf", "Right Click"),
                H("Wire cutters in hand: wire one device to another (4 m apart, wire within 4 m of you); again to cut it; Shift cuts every wire off a device", "Right Click"),
                H("Solar panel in hand: fit it on a roof or ground mount (roof ones from the ground)", "Left or Right Click"),
                H("Use or place the held item; add a fence, path or road point; mount a breaker box or light on a building", "Left Click"),
                H("Act on what is under the cursor: plant, harvest, chop, dig, paint, pick up, open a door, build", "Right Click"),
                H("Pickaxe in hand: break a stone into aggregate", "Right Click"),
                H("Shovel in hand: dig sand from sandy ground", "Right Click"),
                H("Hoe in hand: till the ground into farmland", "Right Click"),
                H("Wire cutters in hand: cut down a section of wire fence", "Right Click"),
                H("Pipe wrench in hand: a propane tank, then a house connector or fill post, lays a propane line (again cuts it)", "Right Click"),
                H("Portable propane tank in hand: fill it at a fill post", "Right Click"),
                H("Pipe wrench in hand: a well, filter or tank, then the next, lays a water line (again cuts it)", "Right Click"),
                H("Well sub panel in hand: fit it on a finished well", "Left Click"),
                H("Bucket, jug or watering can in hand: fill it at a spigot or faucet", "Right Click"),
                H("Pipe wrench in hand: a waste outlet, macerator, septic tank, distribution box or leach field, then the next, lays a sewer line", "Right Click"),
                H("Sink, toilet, shower or washer in a building: use it (Shift: pick it up)", "Right Click"),
                H("Safety disconnect: throw it on or off", "Right Click"),
                H("Fuel pump: take the nozzle, then fill a fuel container on the ground", "Right Click"),
                H("Pipe wrench in hand: a bulk fuel tank, then a fuel pump, lays a fuel line", "Right Click"),
                H("Tidy up an area: drag out a rectangle", K(BindAction.TidyArea)),
                H("Loaded shovel: empty onto a pile or on open ground (starts a pile)", "Right Click"),
                H("Straw bale (in hand): spread bedding over the floor of the room; a shovel takes it up", "Right Click"),
                H("Wheelbarrow: take the handles (empty slot) and push it; again to put it down", "Right Click"),
                H("Wheelbarrow: empty it onto the ground as piles", "Shift", "Right Click"),
                H("Shovel (in hand): scoop a pile, or move shovelfuls to and from a wheelbarrow", "Right Click"),
                H("Rotate what you are placing", K(BindAction.PlaceRotate)),
                H("Place it, or lay the path", "Enter"),
                H("Open a container", K(BindAction.ToggleContainer)),
                H("Drop the held item (Shift: the stack)", K(BindAction.DropItem)),
                H("Pin a build site list, drag to move", "P"),
                H("Flashlight and lantern", K(BindAction.PlayerLight)),
                H("Cutaway view inside a building", K(BindAction.ToggleCutaway)),
                H("First person view (right drag turns, A / D sidestep)", K(BindAction.FirstPerson)),
                H("Map", K(BindAction.ToggleMap)),
                H("Pause time, slower, faster", K(BindAction.PauseTime), K(BindAction.SpeedDown), K(BindAction.SpeedUp)),
                H("Phone", K(BindAction.TogglePhone)),
                H("Settings, or close a window", "Esc"),
                H("Hints, grid overlay, look-at panel", "F1", "F2", "F3"),
                H("Save now", "F9"),
                H("Hide the whole HUD", "F11"),
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
