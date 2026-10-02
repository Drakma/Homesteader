using System.Collections.Generic;
using System.Globalization;
using System.Text;
using UnityEngine;
using UnityEngine.UIElements;
using Homesteader.Save;

namespace Homesteader.UI
{
    /// <summary>
    /// Where the movable windows (container contents, Steadify mini player, asset spawner) sit. A window opens centered
    /// the first time; after that it opens where the player last left it. Positions are kept in PlayerPrefs (so a new
    /// game remembers them) and in the save game (so a load puts them back).
    /// </summary>
    public static class WindowPositions
    {
        private const string PrefKey = "Homesteader.WindowPositions";
        private static Dictionary<string, Vector2> _pos;
        private static readonly Dictionary<string, VisualElement> Live = new Dictionary<string, VisualElement>();

        private static void Load()
        {
            if (_pos != null) return;
            _pos = new Dictionary<string, Vector2>();
            string raw = PlayerPrefs.GetString(PrefKey, "");
            foreach (string entry in raw.Split(new[] { ';' }, System.StringSplitOptions.RemoveEmptyEntries))
            {
                string[] f = entry.Split(',');
                if (f.Length != 3) continue;
                if (float.TryParse(f[1], NumberStyles.Float, CultureInfo.InvariantCulture, out float x)
                    && float.TryParse(f[2], NumberStyles.Float, CultureInfo.InvariantCulture, out float y))
                    _pos[f[0]] = new Vector2(x, y);
            }
        }

        private static void Persist()
        {
            var sb = new StringBuilder();
            foreach (var kv in _pos)
                sb.Append(kv.Key).Append(',').Append(kv.Value.x.ToString("0.#", CultureInfo.InvariantCulture)).Append(',')
                  .Append(kv.Value.y.ToString("0.#", CultureInfo.InvariantCulture)).Append(';');
            PlayerPrefs.SetString(PrefKey, sb.ToString());
            PlayerPrefs.Save();
        }

        public static bool TryGet(string id, out Vector2 p) { Load(); return _pos.TryGetValue(id, out p); }

        public static void Set(string id, Vector2 p) { Load(); _pos[id] = p; Persist(); }

        /// <summary>Puts a window (already added to its parent) at its saved spot, or centers it the first time.</summary>
        public static void Place(VisualElement w, string id)
        {
            if (w == null) return;
            Live[id] = w;
            w.style.position = Position.Absolute;
            w.style.translate = new Translate(0, 0);
            if (!Apply(w, id)) w.RegisterCallback<GeometryChangedEvent>(OnGeometry);
            // A hidden window has no size yet; try again whenever its size first resolves.
            void OnGeometry(GeometryChangedEvent evt)
            {
                if (Apply(w, id)) w.UnregisterCallback<GeometryChangedEvent>(OnGeometry);
            }
        }

        private static bool Apply(VisualElement w, string id)
        {
            VisualElement parent = w.parent;
            if (parent == null) return false;
            float pw = parent.resolvedStyle.width, ph = parent.resolvedStyle.height;
            float ww = w.resolvedStyle.width, wh = w.resolvedStyle.height;
            if (float.IsNaN(pw) || float.IsNaN(ww) || pw <= 0f || ph <= 0f || ww <= 0f || wh <= 0f) return false;
            Vector2 p;
            if (!TryGet(id, out p)) p = new Vector2((pw - ww) * 0.5f, (ph - wh) * 0.5f);
            w.style.left = Mathf.Clamp(p.x, 0f, Mathf.Max(0f, pw - ww));
            w.style.top = Mathf.Clamp(p.y, 0f, Mathf.Max(0f, ph - wh));
            return true;
        }

        /// <summary>Records where a window is now (call when a drag ends and when it closes).</summary>
        public static void Remember(VisualElement w, string id)
        {
            if (w == null || w.panel == null) return;
            float x = w.resolvedStyle.left, y = w.resolvedStyle.top;
            if (float.IsNaN(x) || float.IsNaN(y)) return;
            Set(id, new Vector2(x, y));
        }

        /// <summary>Drag a window by its header, kept inside its parent; the new spot is remembered when the drag ends.</summary>
        public static void MakeDraggable(VisualElement window, VisualElement handle, string id)
        {
            if (window == null || handle == null) return;
            bool dragging = false;
            Vector2 startPointer = Vector2.zero, startPos = Vector2.zero;
            handle.RegisterCallback<PointerDownEvent>(evt =>
            {
                if (evt.button != 0) return;
                if (evt.target is Button || (evt.target is VisualElement ve && ve.GetFirstAncestorOfType<Button>() != null)) return;
                dragging = true;
                startPointer = evt.position;
                startPos = new Vector2(window.resolvedStyle.left, window.resolvedStyle.top);
                handle.CapturePointer(evt.pointerId);
                evt.StopPropagation();
            });
            handle.RegisterCallback<PointerMoveEvent>(evt =>
            {
                if (!dragging) return;
                Vector2 p = startPos + ((Vector2)evt.position - startPointer);
                var parent = window.parent;
                float maxX = (parent != null ? parent.resolvedStyle.width : Screen.width) - window.resolvedStyle.width;
                float maxY = (parent != null ? parent.resolvedStyle.height : Screen.height) - window.resolvedStyle.height;
                window.style.left = Mathf.Clamp(p.x, 0f, Mathf.Max(0f, maxX));
                window.style.top = Mathf.Clamp(p.y, 0f, Mathf.Max(0f, maxY));
                evt.StopPropagation();
            });
            handle.RegisterCallback<PointerUpEvent>(evt =>
            {
                if (!dragging) return;
                dragging = false;
                handle.ReleasePointer(evt.pointerId);
                Remember(window, id);
                evt.StopPropagation();
            });
        }

        /// <summary>For the save game: every remembered position (open windows are read live first).</summary>
        public static List<GameSave.SavedWindow> Capture()
        {
            Load();
            foreach (var kv in new List<KeyValuePair<string, VisualElement>>(Live))
                if (kv.Value != null && kv.Value.panel != null && kv.Value.resolvedStyle.display != DisplayStyle.None) Remember(kv.Value, kv.Key);
            var list = new List<GameSave.SavedWindow>();
            foreach (var kv in _pos) list.Add(new GameSave.SavedWindow { id = kv.Key, x = kv.Value.x, y = kv.Value.y });
            return list;
        }

        /// <summary>For loading a save: put the remembered positions back (windows that are open move at once).</summary>
        public static void Restore(List<GameSave.SavedWindow> windows)
        {
            if (windows == null || windows.Count == 0) return;
            Load();
            foreach (var w in windows) _pos[w.id] = new Vector2(w.x, w.y);
            Persist();
            foreach (var kv in Live)
                if (kv.Value != null && kv.Value.panel != null) Apply(kv.Value, kv.Key);
        }
    }
}
