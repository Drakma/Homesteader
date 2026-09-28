using UnityEngine;
using UnityEngine.UIElements;
using UnityEngine.InputSystem;

namespace Homesteader.DebugTools
{
    /// <summary>
    /// Debug statistics window toggled by F12. Uses the same UI Toolkit window
    /// chrome as the rest of the game (`.window`, `.window-header`, etc.) by
    /// adding a StatsWindow element to the HUD UXML and driving its labels.
    /// Bootstraps itself on scene load.
    /// </summary>
    public sealed class StatsOverlay : MonoBehaviour
    {
        private bool _visible;
        private float _accumTime;
        private int _accumFrames;
        private float _fps;
        private float _frameTimeMs;

        private VisualElement _statsWindow;
        private Label _fpsLabel;
        private Label _zoomLabel;
        private Label _gridLabel;
        private Label _ramLabel;
        private Label _drawLabel;
        private Label _trisLabel;
        private Label _screenLabel;
        private Label _cpuLabel;
        private Button _closeBtn;

        private IsometricLockedCamera _isoCam;
        private GridBrightnessToggle _gridToggle;
        private bool _wired;

        private const float UpdateInterval = 0.25f;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        private static void Bootstrap()
        {
            if (FindAnyObjectByType<StatsOverlay>() != null) return;
            var go = new GameObject("StatsOverlay");
            DontDestroyOnLoad(go);
            go.AddComponent<StatsOverlay>();
        }

        private void Update()
        {
            bool pressed = Keyboard.current != null
                ? Keyboard.current.f12Key.wasPressedThisFrame
                : Input.GetKeyDown(KeyCode.F12);
            if (pressed)
            {
                _visible = !_visible;
                ApplyVisibility();
            }

            // Accumulate FPS regardless of visibility.
            _accumTime += Time.unscaledDeltaTime;
            _accumFrames++;
            if (_accumTime >= UpdateInterval)
            {
                _fps = _accumFrames / _accumTime;
                _frameTimeMs = _accumTime / _accumFrames * 1000f;
                _accumTime = 0f;
                _accumFrames = 0;
            }

            // Update labels every frame while visible.
            if (_visible && _wired)
                UpdateLabels();
        }

        private void ApplyVisibility()
        {
            if (_statsWindow == null) ResolveReferences();
            if (_statsWindow == null) return;

            if (_visible)
                _statsWindow.RemoveFromClassList("stats-window--hidden");
            else
                _statsWindow.AddToClassList("stats-window--hidden");
        }

        private void ResolveReferences()
        {
            var doc = FindAnyObjectByType<UIDocument>();
            if (doc == null) return;
            var root = doc.rootVisualElement;
            if (root == null) return;

            _statsWindow = root.Q<VisualElement>("StatsWindow");
            if (_statsWindow == null) return;

            _fpsLabel    = root.Q<Label>("StatsFpsLabel");
            _zoomLabel   = root.Q<Label>("StatsZoomLabel");
            _gridLabel   = root.Q<Label>("StatsGridLabel");
            _ramLabel    = root.Q<Label>("StatsRamLabel");
            _drawLabel   = root.Q<Label>("StatsDrawLabel");
            _trisLabel   = root.Q<Label>("StatsTrisLabel");
            _screenLabel = root.Q<Label>("StatsScreenLabel");
            _cpuLabel    = root.Q<Label>("StatsCpuLabel");
            _closeBtn    = root.Q<Button>("StatsCloseBtn");

            if (_closeBtn != null)
                _closeBtn.clicked += () => { _visible = false; ApplyVisibility(); };

            // Make the window draggable by its header (same pattern as HudBindings).
            var header = _statsWindow.Q<VisualElement>(className: "window-header");
            if (header != null)
                MakeDraggable(_statsWindow, header);

            _wired = true;
        }

        private void UpdateLabels()
        {
            // FPS
            string fpsColor = _fps >= 45f ? "lime" : (_fps >= 25f ? "yellow" : "red");
            if (_fpsLabel != null) _fpsLabel.text = $"{_fps:F0} FPS  {_frameTimeMs:F1} ms";

            // Zoom
            if (_isoCam == null) _isoCam = FindAnyObjectByType<IsometricLockedCamera>();
            float zoom = 0f;
            if (_isoCam != null)
            {
                var cam = _isoCam.GetComponent<Camera>();
                if (cam != null) zoom = cam.orthographicSize;
            }
            if (_zoomLabel != null) _zoomLabel.text = $"Zoom  {zoom:F1}";

            // Grid
            if (_gridToggle == null) _gridToggle = FindAnyObjectByType<GridBrightnessToggle>();
            string gridState = "N/A";
            if (_gridToggle != null)
            {
                var fi = typeof(GridBrightnessToggle).GetField("_level",
                    System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
                if (fi != null)
                {
                    int level = (int)fi.GetValue(_gridToggle);
                    string[] names = { "Off", "Cell under cursor", "Dim", "Bright" };
                    gridState = names[Mathf.Clamp(level, 0, names.Length - 1)];
                }
            }
            if (_gridLabel != null) _gridLabel.text = $"Grid  {gridState}";

            // RAM
            long managedRam = System.GC.GetTotalMemory(false);
            string ramStr = FormatBytes(managedRam);
            long unityMem = UnityEngine.Profiling.Profiler.GetTotalReservedMemoryLong();
            string unityReserved = unityMem > 0 ? FormatBytes(unityMem) : "";
            if (_ramLabel != null) _ramLabel.text = $"RAM  {ramStr}" + (string.IsNullOrEmpty(unityReserved) ? "" : $"  (Unity {unityReserved})");

            // Render stats
            int drawCalls = GetRenderStat("drawCalls");
            int triangles = GetRenderStat("triangles");
            int vertices = GetRenderStat("vertices");
            int batches = GetRenderStat("batches");
            if (_drawLabel != null) _drawLabel.text = $"Draw  {drawCalls} calls  {batches} batches";
            if (_trisLabel != null) _trisLabel.text = $"Tris  {triangles:N0}  Verts {vertices:N0}";

            // Screen
            string screenRes = $"{Screen.width}x{Screen.height}";
            string screenScale = Screen.width > 0 ? $"{(float)Screen.currentResolution.width / Screen.width:F1}x" : "1x";
            if (_screenLabel != null) _screenLabel.text = $"Screen  {screenRes}  {screenScale}";

            // CPU
            float cpuPct = Mathf.Clamp01(_frameTimeMs / 16.67f) * 100f;
            if (_cpuLabel != null) _cpuLabel.text = $"CPU  {cpuPct:F0}%";
        }

        /// <summary>
        /// Makes a VisualElement draggable by dragging from a header element.
        /// Repositions the element from its CSS layout position to absolute
        /// on first drag, then tracks the pointer delta.
        /// </summary>
        private static void MakeDraggable(VisualElement window, VisualElement header)
        {
            bool dragging = false;
            Vector2 dragStart = Vector2.zero;
            Vector2 winStart = Vector2.zero;

            header.RegisterCallback<PointerDownEvent>(evt =>
            {
                dragging = true;
                dragStart = evt.position;
                var style = window.resolvedStyle;
                winStart = new Vector2(style.left, style.top);
                header.CapturePointer(evt.pointerId);
                evt.StopPropagation();
            });

            header.RegisterCallback<PointerMoveEvent>(evt =>
            {
                if (!dragging) return;
                Vector2 delta = (Vector2)evt.position - dragStart;
                float newLeft = winStart.x + delta.x;
                float newTop = winStart.y + delta.y;
                // Clamp to screen bounds
                newLeft = Mathf.Clamp(newLeft, 0, Screen.width - window.resolvedStyle.width);
                newTop = Mathf.Clamp(newTop, 0, Screen.height - window.resolvedStyle.height);
                window.style.left = newLeft;
                window.style.top = newTop;
                window.style.bottom = StyleKeyword.Auto;
                evt.StopPropagation();
            });

            header.RegisterCallback<PointerUpEvent>(evt =>
            {
                dragging = false;
                header.ReleasePointer(evt.pointerId);
                evt.StopPropagation();
            });
        }

        private static string FormatBytes(long bytes)
        {
            if (bytes < 1024) return $"{bytes} B";
            if (bytes < 1024 * 1024) return $"{bytes / 1024f:F1} KB";
            if (bytes < 1024 * 1024 * 1024) return $"{bytes / (1024f * 1024f):F1} MB";
            return $"{bytes / (1024f * 1024f * 1024f):F2} GB";
        }

        private static int GetRenderStat(string name)
        {
            try
            {
                var type = System.Type.GetType("UnityEngine.Rendering.UnityStats, UnityEngine.CoreModule, Version=0.0.0.0, Culture=neutral, PublicKeyToken=null");
                if (type != null)
                {
                    var prop = type.GetProperty(name, System.Reflection.BindingFlags.Public | System.Reflection.BindingFlags.Static);
                    if (prop != null) return (int)prop.GetValue(null);
                }
            }
            catch { }
            return 0;
        }
    }
}
