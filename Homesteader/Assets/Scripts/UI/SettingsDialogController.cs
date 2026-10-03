using System.Collections.Generic;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.UIElements;
using Homesteader.Controls;

namespace Homesteader.UI
{
    /// <summary>
    /// Drives the wide Settings dialog in WelcomeMenu.uxml: the left-hand category list (General, Graphics,
    /// Audio, Controls), the display options (quality, fullscreen, v-sync), the rebindable Controls page, and
    /// "Reset All Settings".
    ///
    /// The dialog's open/close and the zoom fields stay owned by WelcomeMenuController, the colour sliders by
    /// GraphicsSettingsPanel and the volume sliders by AudioManager - this class only adds the pieces that
    /// didn't have an owner. Bootstraps itself on scene load like the other UI helpers, and re-resolves its
    /// elements if the welcome tree is ever rebuilt.
    /// </summary>
    public sealed class SettingsDialogController : MonoBehaviour
    {
        private const string QualityPrefKey = "Homesteader.Display.Quality";
        private const string FullscreenPrefKey = "Homesteader.Display.Fullscreen";
        private const string VsyncPrefKey = "Homesteader.Display.Vsync";

        private static readonly string[] PageNames = { "General", "Graphics", "Audio", "Controls" };

        // Bindings that stay fixed (mouse, toolbar, Esc, debug keys), shown read-only under the rebindable ones.
        private static readonly (string input, string action)[] FixedBindings =
        {
            ("Ctrl + mouse wheel", "Zoom the camera"),
            ("Right mouse + drag", "Pan the camera"),
            ("1 - 9, 0", "Select toolbar slot"),
            ("Mouse wheel", "Cycle toolbar slot"),
            ("Left click", "Place the selected item"),
            ("Right click", "Plant / harvest"),
            ("Ctrl + click (phone app)", "Pin the app to the screen"),
            ("Esc", "Close the top window / open the menu"),
            ("F9", "Save the game now"),
            ("F2 / F3", "Grid overlay / look-at panel (debug)"),
            ("F5 / F6", "Spawn dev animal / animal AI labels (debug)"),
        };

        private VisualElement _dialog;
        private readonly Button[] _navButtons = new Button[4];
        private readonly VisualElement[] _pages = new VisualElement[4];
        private Button _resetAllBtn;
        private SliderInt _zoomMaxField;

        private DropdownField _qualityDropdown;
        private Toggle _fullscreenToggle;
        private Toggle _vsyncToggle;

        private VisualElement _controlsList;
        private Label _controlsHint;
        private Button _controlsResetBtn;
        private readonly Dictionary<BindAction, Button> _keyButtons = new Dictionary<BindAction, Button>();
        private BindAction? _capturing;
        private bool _releaseRebindNextFrame;

        private bool _wired;
        private const string DefaultControlsHint = "Click a key, then press the new one. Esc cancels.";

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        private static void Bootstrap()
        {
            ApplySavedDisplaySettings();
            if (FindAnyObjectByType<SettingsDialogController>() != null) return;
            var go = new GameObject("SettingsDialogController");
            DontDestroyOnLoad(go);
            go.AddComponent<SettingsDialogController>();
        }

        /// <summary>Re-applies the player's saved display choices at startup. Only keys that were actually
        /// saved are applied, so a player who never touched these keeps the project's own defaults.</summary>
        private static void ApplySavedDisplaySettings()
        {
            // Quality, display mode, resolution, V-Sync and the HUD scale are GraphicsOptions' now (it applies them at startup).
        }

        private void OnDestroy()
        {
            KeyBindings.Changed -= RefreshKeyButtons;
            KeyBindings.IsRebinding = false;
        }

        private void Update()
        {
            // The welcome tree can be rebuilt (fresh elements) after a scene reload; drop our stale references.
            if (_wired && _dialog != null && _dialog.panel == null)
            {
                KeyBindings.Changed -= RefreshKeyButtons;
                EndCapture(immediate: true);
                _wired = false;
            }

            if (!_wired) ResolveReferences();
            if (!_wired) return;

            UpdateCapture();
        }

        // ------------------------------------------------------------------ wiring

        private void ResolveReferences()
        {
            var doc = FindAnyObjectByType<UIDocument>();
            if (doc == null) return;
            var root = doc.rootVisualElement;
            if (root == null) return;

            _dialog = root.Q<VisualElement>("SettingsDialog");
            if (_dialog == null) return;

            for (int i = 0; i < PageNames.Length; i++)
            {
                _navButtons[i] = root.Q<Button>("SettingsNav" + PageNames[i]);
                _pages[i] = root.Q<VisualElement>("SettingsPage" + PageNames[i]);
                if (_navButtons[i] == null || _pages[i] == null) return;
            }

            _resetAllBtn = root.Q<Button>("SettingsResetAllBtn");
            _zoomMaxField = root.Q<SliderInt>("ZoomMaxLevel");
            _qualityDropdown = root.Q<DropdownField>("QualityDropdown");
            _fullscreenToggle = root.Q<Toggle>("FullscreenToggle");
            _vsyncToggle = root.Q<Toggle>("VsyncToggle");
            _controlsList = root.Q<VisualElement>("ControlsList");
            _controlsHint = root.Q<Label>("ControlsHint");
            _controlsResetBtn = root.Q<Button>("ControlsResetBtn");
            if (_controlsList == null) return;

            for (int i = 0; i < _navButtons.Length; i++)
            {
                int page = i;
                _navButtons[i].clicked += () => ShowPage(page);
            }
            ShowPage(0);

            WireDisplayOptions();
            Homesteader.Radio.RadioSettingsPanel.Wire(root);
            BuildControlsPage();
            KeyBindings.Changed += RefreshKeyButtons;

            if (_controlsResetBtn != null) _controlsResetBtn.clicked += KeyBindings.ResetAll;
            if (_resetAllBtn != null) _resetAllBtn.clicked += ResetAllSettings;

            _wired = true;
        }

        private void ShowPage(int index)
        {
            EndCapture(immediate: false);
            for (int i = 0; i < _pages.Length; i++)
            {
                bool active = i == index;
                if (active) _pages[i].RemoveFromClassList("settings-page--hidden");
                else _pages[i].AddToClassList("settings-page--hidden");
                if (active) _navButtons[i].AddToClassList("settings-nav-btn--active");
                else _navButtons[i].RemoveFromClassList("settings-nav-btn--active");
            }
        }

        // ------------------------------------------------------------------ display options

        private void WireDisplayOptions()
        {
            // The display controls (preset, display mode, resolution, V-Sync, HUD scale) are wired by GraphicsOptions.WireUi (from GraphicsSettingsPanel).
        }

        // ------------------------------------------------------------------ controls page

        private void BuildControlsPage()
        {
            _controlsList.Clear();
            _keyButtons.Clear();

            string lastGroup = null;
            foreach (KeyBindings.ActionInfo info in KeyBindings.All)
            {
                if (info.Group != lastGroup)
                {
                    lastGroup = info.Group;
                    var groupTitle = new Label(info.Group.ToUpperInvariant());
                    groupTitle.AddToClassList("controls-group-title");
                    _controlsList.Add(groupTitle);
                }

                var row = new VisualElement();
                row.AddToClassList("controls-row");

                var label = new Label(info.Label);
                label.AddToClassList("settings-label");
                row.Add(label);

                BindAction action = info.Action;
                var keyBtn = new Button { text = KeyBindings.KeyLabel(KeyBindings.Get(action)) };
                keyBtn.AddToClassList("controls-key-btn");
                keyBtn.clicked += () => BeginCapture(action);
                row.Add(keyBtn);
                _keyButtons[action] = keyBtn;

                _controlsList.Add(row);
            }

            var fixedTitle = new Label("FIXED (CANNOT BE CHANGED)");
            fixedTitle.AddToClassList("controls-group-title");
            _controlsList.Add(fixedTitle);

            foreach (var (input, action) in FixedBindings)
            {
                var row = new VisualElement();
                row.AddToClassList("controls-row");

                var label = new Label(action);
                label.AddToClassList("settings-label");
                row.Add(label);

                var key = new Label(input);
                key.AddToClassList("controls-fixed-key");
                row.Add(key);

                _controlsList.Add(row);
            }
        }

        private void RefreshKeyButtons()
        {
            foreach (var pair in _keyButtons)
                pair.Value.text = KeyBindings.KeyLabel(KeyBindings.Get(pair.Key));
        }

        private void BeginCapture(BindAction action)
        {
            EndCapture(immediate: true);
            _capturing = action;
            KeyBindings.IsRebinding = true;
            _releaseRebindNextFrame = false;
            _keyButtons[action].text = "Press a key...";
            _keyButtons[action].AddToClassList("controls-key-btn--capturing");
            SetControlsHint("Press the new key for this action. Esc cancels.");
        }

        private void EndCapture(bool immediate)
        {
            if (_capturing.HasValue && _keyButtons.TryGetValue(_capturing.Value, out Button btn))
            {
                btn.RemoveFromClassList("controls-key-btn--capturing");
                btn.text = KeyBindings.KeyLabel(KeyBindings.Get(_capturing.Value));
            }
            _capturing = null;

            // Hold IsRebinding for one more frame unless told otherwise: the key that just got bound was
            // pressed THIS frame, and scripts that run after this one would otherwise see that press and fire
            // the action it was just bound to.
            if (immediate) KeyBindings.IsRebinding = false;
            else _releaseRebindNextFrame = true;
        }

        private void UpdateCapture()
        {
            if (_releaseRebindNextFrame && !_capturing.HasValue)
            {
                _releaseRebindNextFrame = false;
                KeyBindings.IsRebinding = false;
            }

            if (!_capturing.HasValue) return;

            // Closed (or hidden) while waiting for a key: drop the capture so the game isn't left ignoring input.
            if (_dialog.ClassListContains("settings--hidden") || _dialog.resolvedStyle.display == DisplayStyle.None)
            {
                EndCapture(immediate: true);
                SetControlsHint(DefaultControlsHint);
                return;
            }

            Keyboard kb = Keyboard.current;
            if (kb == null) return;

            if (kb.escapeKey.wasPressedThisFrame)
            {
                EndCapture(immediate: false);
                SetControlsHint(DefaultControlsHint);
                return;
            }

            foreach (var keyControl in kb.allKeys)
            {
                if (!keyControl.wasPressedThisFrame) continue;

                Key key = keyControl.keyCode;
                if (KeyBindings.IsReserved(key))
                {
                    SetControlsHint(KeyBindings.KeyLabel(key) + " is reserved and can't be used. Press another key, or Esc to cancel.");
                    return;
                }

                BindAction action = _capturing.Value;
                BindAction? swapped = KeyBindings.Set(action, key);
                EndCapture(immediate: false);
                SetControlsHint(swapped.HasValue
                    ? KeyBindings.KeyLabel(key) + " was already used, so the two actions swapped keys."
                    : DefaultControlsHint);
                return;
            }
        }

        private void SetControlsHint(string text)
        {
            if (_controlsHint != null) _controlsHint.text = text;
        }

        // ------------------------------------------------------------------ reset all

        private void ResetAllSettings()
        {
            KeyBindings.ResetAll();

            // Zoom: the fields are read back (and saved) by WelcomeMenuController when the dialog closes.
            if (_zoomMaxField != null) _zoomMaxField.value = 15;

            if (GraphicsSettingsPanel.Instance != null) GraphicsSettingsPanel.Instance.ResetToDefaults();
            if (Homesteader.Audio.AudioManager.Instance != null) Homesteader.Audio.AudioManager.Instance.ResetVolumes();
            Homesteader.Radio.RadioSettings.ResetToDefaults();   // script writer and model; the API key is kept
            Homesteader.Radio.RadioSettingsPanel.Refresh();
        }
    }
}
