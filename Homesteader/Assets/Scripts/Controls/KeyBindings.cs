using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.InputSystem;

namespace Homesteader.Controls
{
    /// <summary>Gameplay actions whose keyboard key the player can rebind in Settings > Controls.</summary>
    public enum BindAction
    {
        MoveUp, MoveDown, MoveLeft, MoveRight, Run,
        CameraRotateLeft, CameraRotateRight,
        PauseTime, SpeedUp, SpeedDown,
        TogglePhone, PlayerLight, ToggleMap, PlaceRotate, ToggleContainer, DropItem, ToggleCutaway, TidyArea, FirstPerson,
    }

    /// <summary>
    /// The rebindable keyboard layer. Gameplay code asks "was this ACTION pressed" instead of "was this KEY
    /// pressed", so the key behind an action can change at runtime. Bindings persist in PlayerPrefs.
    ///
    /// Only actions listed in <see cref="BindAction"/> are rebindable. Everything else (mouse input, the
    /// toolbar digits, Esc, Ctrl-wheel zoom, and the F-key debug tools) stays fixed and is listed read-only in
    /// the Controls page; docs/CONTROLS.md remains the single list of every binding.
    /// </summary>
    public static class KeyBindings
    {
        public struct ActionInfo
        {
            public BindAction Action;
            public string Label;
            public string Group;
            public Key DefaultKey;
        }

        /// <summary>Display order on the Controls page.</summary>
        public static readonly ActionInfo[] All =
        {
            new ActionInfo { Action = BindAction.MoveUp, Label = "Move up", Group = "Movement", DefaultKey = Key.W },
            new ActionInfo { Action = BindAction.MoveDown, Label = "Move down", Group = "Movement", DefaultKey = Key.S },
            new ActionInfo { Action = BindAction.MoveLeft, Label = "Move left", Group = "Movement", DefaultKey = Key.A },
            new ActionInfo { Action = BindAction.MoveRight, Label = "Move right", Group = "Movement", DefaultKey = Key.D },
            new ActionInfo { Action = BindAction.Run, Label = "Run (hold)", Group = "Movement", DefaultKey = Key.LeftShift },
            new ActionInfo { Action = BindAction.CameraRotateLeft, Label = "Rotate camera left", Group = "Camera", DefaultKey = Key.Q },
            new ActionInfo { Action = BindAction.CameraRotateRight, Label = "Rotate camera right", Group = "Camera", DefaultKey = Key.E },
            new ActionInfo { Action = BindAction.FirstPerson, Label = "First person view", Group = "Camera", DefaultKey = Key.Z },
            new ActionInfo { Action = BindAction.PauseTime, Label = "Pause / resume time", Group = "Time and menus", DefaultKey = Key.Space },
            new ActionInfo { Action = BindAction.SpeedUp, Label = "Faster time", Group = "Time and menus", DefaultKey = Key.RightBracket },
            new ActionInfo { Action = BindAction.SpeedDown, Label = "Slower time", Group = "Time and menus", DefaultKey = Key.LeftBracket },
            new ActionInfo { Action = BindAction.TogglePhone, Label = "Open / close phone", Group = "Time and menus", DefaultKey = Key.Tab },
            new ActionInfo { Action = BindAction.PlayerLight, Label = "Flashlight / lantern", Group = "World", DefaultKey = Key.L },
            new ActionInfo { Action = BindAction.ToggleMap, Label = "Show / hide map", Group = "World", DefaultKey = Key.M },
            new ActionInfo { Action = BindAction.ToggleCutaway, Label = "Cutaway view inside buildings", Group = "World", DefaultKey = Key.V },
            new ActionInfo { Action = BindAction.PlaceRotate, Label = "Rotate placement", Group = "World", DefaultKey = Key.R },
            new ActionInfo { Action = BindAction.ToggleContainer, Label = "Open / close container", Group = "World", DefaultKey = Key.C },
            new ActionInfo { Action = BindAction.DropItem, Label = "Drop the held item", Group = "World", DefaultKey = Key.F },
            new ActionInfo { Action = BindAction.TidyArea, Label = "Tidy up an area", Group = "World", DefaultKey = Key.T },
        };

        /// <summary>True while the Controls page is waiting for a key press to bind. Game actions report
        /// "not pressed" during that time so the key being captured doesn't also trigger its old action.</summary>
        public static bool IsRebinding { get; set; }

        /// <summary>Raised whenever any binding changes (rebind, swap, reset).</summary>
        public static event Action Changed;

        private const string PrefPrefix = "Homesteader.Key.";
        private static Dictionary<BindAction, Key> _current;

        private static Dictionary<BindAction, Key> Current
        {
            get
            {
                if (_current == null) Load();
                return _current;
            }
        }

        private static void Load()
        {
            // One-time: the flashlight / lantern moves to L whatever an older build saved for it (and anything else saved on L gives it up).
            if (PlayerPrefs.GetInt(PrefPrefix + "FlashlightOnL", 0) == 0)
            {
                PlayerPrefs.DeleteKey(PrefPrefix + BindAction.PlayerLight);
                foreach (ActionInfo info in All)
                    if (info.Action != BindAction.PlayerLight && PlayerPrefs.GetInt(PrefPrefix + info.Action, -1) == (int)Key.L)
                        PlayerPrefs.DeleteKey(PrefPrefix + info.Action);
                PlayerPrefs.SetInt(PrefPrefix + "FlashlightOnL", 1);
                PlayerPrefs.Save();
            }
            _current = new Dictionary<BindAction, Key>();
            foreach (ActionInfo info in All)
            {
                int saved = PlayerPrefs.GetInt(PrefPrefix + info.Action, (int)info.DefaultKey);
                Key key = Enum.IsDefined(typeof(Key), saved) ? (Key)saved : info.DefaultKey;
                _current[info.Action] = key;
            }
        }

        public static Key Get(BindAction action) => Current[action];

        public static Key DefaultFor(BindAction action)
        {
            foreach (ActionInfo info in All) if (info.Action == action) return info.DefaultKey;
            return Key.None;
        }

        /// <summary>Keys that can't be bound: they have fixed meanings elsewhere (Esc, toolbar digits, the
        /// F-key debug tools, Ctrl for zoom/pin clicks) or aren't real keys.</summary>
        public static bool IsReserved(Key key)
        {
            if (key == Key.None || key == Key.ContextMenu || key == Key.PrintScreen) return true;
            if (key == Key.Escape || key == Key.LeftCtrl || key == Key.RightCtrl) return true;
            if (key >= Key.Digit1 && key <= Key.Digit0) return true; // enum order is Digit1..Digit9, Digit0
            if (key >= Key.Numpad0 && key <= Key.Numpad9) return true;
            if (key >= Key.F1 && key <= Key.F12) return true;
            return false;
        }

        /// <summary>Binds an action to a key. If another action already uses that key the two swap, so no
        /// key is ever bound to two actions at once. Returns the action it swapped with, if any.</summary>
        public static BindAction? Set(BindAction action, Key key)
        {
            if (IsReserved(key)) return null;
            Key previous = Current[action];
            BindAction? swappedWith = null;

            foreach (ActionInfo info in All)
            {
                if (info.Action != action && Current[info.Action] == key)
                {
                    Current[info.Action] = previous;
                    PlayerPrefs.SetInt(PrefPrefix + info.Action, (int)previous);
                    swappedWith = info.Action;
                    break;
                }
            }

            Current[action] = key;
            PlayerPrefs.SetInt(PrefPrefix + action, (int)key);
            PlayerPrefs.Save();
            Changed?.Invoke();
            return swappedWith;
        }

        public static void ResetAll()
        {
            foreach (ActionInfo info in All)
            {
                Current[info.Action] = info.DefaultKey;
                PlayerPrefs.DeleteKey(PrefPrefix + info.Action);
            }
            PlayerPrefs.Save();
            Changed?.Invoke();
        }

        // ------------------------------------------------------------------ gameplay queries

        /// <summary>The key an action is bound to now.</summary>
        public static Key KeyOf(BindAction action) { return Current[action]; }

        public static bool IsPressed(BindAction action)
        {
            if (IsRebinding) return false;
            Keyboard kb = Keyboard.current;
            return kb != null && kb[Current[action]].isPressed;
        }

        public static bool WasPressedThisFrame(BindAction action)
        {
            if (IsRebinding) return false;
            Keyboard kb = Keyboard.current;
            return kb != null && kb[Current[action]].wasPressedThisFrame;
        }

        // ------------------------------------------------------------------ display

        public static string KeyLabel(Key key)
        {
            switch (key)
            {
                case Key.None: return "Unbound";
                case Key.LeftShift: return "Left Shift";
                case Key.RightShift: return "Right Shift";
                case Key.LeftAlt: return "Left Alt";
                case Key.RightAlt: return "Right Alt";
                case Key.LeftBracket: return "[";
                case Key.RightBracket: return "]";
                case Key.Semicolon: return ";";
                case Key.Quote: return "'";
                case Key.Comma: return ",";
                case Key.Period: return ".";
                case Key.Slash: return "/";
                case Key.Backslash: return "\\";
                case Key.Backquote: return "`";
                case Key.Minus: return "-";
                case Key.Equals: return "=";
                case Key.UpArrow: return "Up";
                case Key.DownArrow: return "Down";
                case Key.LeftArrow: return "Left";
                case Key.RightArrow: return "Right";
                default: return key.ToString();
            }
        }
    }
}
