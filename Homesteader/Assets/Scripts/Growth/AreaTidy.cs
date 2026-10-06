using Homesteader.Controls;
using Homesteader.UI;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.UIElements;

namespace Homesteader.Growth
{
    /// <summary>
    /// Tidies up any area, not just a building yard. The Tidy key turns the mode on; the player drags out a rectangle on the ground (left button, on the grid) and
    /// on release everything in it is tidied (<see cref="YardTidy.RunArea"/>): partly used piles combined, loose building materials packed or piled, stackables
    /// stacked, all laid out in neat lines along the rectangle's longer side. Esc (or the key again) cancels. While it is on, the other left-click tools are off.
    /// </summary>
    public sealed class AreaTidy : MonoBehaviour
    {
        public static bool Active { get; private set; }

        private static AreaTidy s_instance;
        private LineRenderer _outline;
        private Material _mat;
        private VisualElement _prompt;
        private bool _dragging;
        private Vector3 _start, _end;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        private static void Bootstrap()
        {
            Active = false;
            if (FindAnyObjectByType<AreaTidy>() != null) return;
            var go = new GameObject("AreaTidy");
            DontDestroyOnLoad(go);
            s_instance = go.AddComponent<AreaTidy>();
        }

        private void Awake() { s_instance = this; }

        /// <summary>Esc while the mode is on turns it off (HudBindings calls this).</summary>
        public static bool Cancel()
        {
            if (!Active || s_instance == null) return false;
            s_instance.Stop();
            return true;
        }

        private void Update()
        {
            if (!Active)
            {
                if (!HudBindings.KeyboardCaptured && KeyBindings.WasPressedThisFrame(BindAction.TidyArea)) StartMode();
                return;
            }
            if (!HudBindings.KeyboardCaptured && KeyBindings.WasPressedThisFrame(BindAction.TidyArea)) { Stop(); return; }

            Mouse mouse = Mouse.current;
            Camera cam = Camera.main != null ? Camera.main : FindAnyObjectByType<Camera>();
            if (mouse == null || cam == null) return;
            Vector2 pointer = mouse.position.ReadValue();
            HudBindings hud = HudBindings.Instance;
            bool overUi = hud != null && hud.IsPointerOverUI(pointer);

            if (mouse.leftButton.wasPressedThisFrame && !overUi && CursorGround(cam, pointer, out Vector3 p0))
            {
                _dragging = true;
                _start = Snap(p0, false);
                _end = Snap(p0, true);
            }
            if (_dragging)
            {
                if (CursorGround(cam, pointer, out Vector3 p)) _end = Snap(p, true);   // (on a plane at the ground: passing over an object, a tree or a roof does not stop it)
                DrawOutline();
                if (mouse.leftButton.wasReleasedThisFrame)
                {
                    _dragging = false;
                    Rect area = AreaRect();
                    var ped = PedController.Current;
                    if (area.width >= 1f && area.height >= 1f) YardTidy.RunArea(area, ped != null ? ped.transform.position : new Vector3(area.center.x, 0f, area.center.y));
                    Stop();
                }
            }
        }

        /// <summary>
        /// The ground under the cursor, found by running the camera ray down to the ground's own height instead of asking what the ray hits first: the area can be dragged across
        /// objects, stacks, trees and buildings without the corner getting stuck on them (the old pick gave up at the first thing that was not the terrain).
        /// </summary>
        private static bool CursorGround(Camera cam, Vector2 pointer, out Vector3 point)
        {
            point = default;
            if (cam == null) return false;
            Ray ray = cam.ScreenPointToRay(pointer);
            var ped = PedController.Current;
            float y = ped != null ? Homesteader.Generation.TerrainHeightDetector.GetSurfaceY(ped.transform.position) : 0f;
            for (int i = 0; i < 3; i++)   // a plane at the player's ground, then at the ground found there: it follows a slope
            {
                var plane = new Plane(Vector3.up, new Vector3(0f, y, 0f));
                if (!plane.Raycast(ray, out float enter)) return false;
                Vector3 hit = ray.GetPoint(enter);
                y = Homesteader.Generation.TerrainHeightDetector.GetSurfaceY(hit);
                point = new Vector3(hit.x, y, hit.z);
            }
            return true;
        }

        // the corners are on the grid: the first is the corner at the start of the drag, the second the far corner
        private static Vector3 Snap(Vector3 p, bool far)
        {
            float g = PlantingValidator.GridSizeM;
            p.x = (far ? Mathf.Ceil(p.x / g) : Mathf.Floor(p.x / g)) * g;
            p.z = (far ? Mathf.Ceil(p.z / g) : Mathf.Floor(p.z / g)) * g;
            return p;
        }

        private Rect AreaRect()
        {
            // the dragged rectangle: from the start corner to the cursor, whichever way it was dragged, whole grid squares
            float g = PlantingValidator.GridSizeM;
            float x0 = Mathf.Min(_start.x, _end.x), x1 = Mathf.Max(_start.x, _end.x);
            float z0 = Mathf.Min(_start.z, _end.z), z1 = Mathf.Max(_start.z, _end.z);
            if (x1 - x0 < g) x1 = x0 + g;
            if (z1 - z0 < g) z1 = z0 + g;
            return new Rect(x0, z0, x1 - x0, z1 - z0);
        }

        private void DrawOutline()
        {
            if (_outline == null)
            {
                var go = new GameObject("TidyOutline");
                go.transform.SetParent(transform, false);
                _outline = go.AddComponent<LineRenderer>();
                _outline.loop = true;
                _outline.positionCount = 4;
                _outline.widthMultiplier = 0.08f;
                _outline.useWorldSpace = true;
                _mat = new Material(Shader.Find("Universal Render Pipeline/Unlit")) { color = new Color(1f, 0.75f, 0.2f, 1f) };
                _outline.sharedMaterial = _mat;
            }
            _outline.enabled = true;
            Rect r = AreaRect();
            Vector3 a = new Vector3(r.xMin, 0f, r.yMin), b = new Vector3(r.xMax, 0f, r.yMin), c = new Vector3(r.xMax, 0f, r.yMax), d = new Vector3(r.xMin, 0f, r.yMax);
            Vector3[] corners = { a, b, c, d };
            for (int i = 0; i < 4; i++)
            {
                corners[i].y = Homesteader.Generation.TerrainHeightDetector.GetSurfaceY(corners[i]) + 0.12f;
                _outline.SetPosition(i, corners[i]);
            }
        }

        private void StartMode()
        {
            Active = true;
            _dragging = false;
            ShowPrompt(true);
        }

        private void Stop()
        {
            Active = false;
            _dragging = false;
            if (_outline != null) _outline.enabled = false;
            ShowPrompt(false);
        }

        private void ShowPrompt(bool on)
        {
            UIDocument doc = FindAnyObjectByType<UIDocument>();
            VisualElement root = doc != null ? doc.rootVisualElement : null;
            if (root == null) return;
            if (on && _prompt == null)
            {
                _prompt = new Label("Tidy: drag out the area on the ground. Esc cancels.") { pickingMode = PickingMode.Ignore };
                _prompt.AddToClassList("hs-prompt");
                _prompt.style.position = Position.Absolute;
                _prompt.style.top = 70;
                _prompt.style.left = 0;
                _prompt.style.right = 0;
                _prompt.style.unityTextAlign = TextAnchor.MiddleCenter;
                _prompt.style.color = new Color(1f, 0.82f, 0.35f, 1f);
                _prompt.style.fontSize = 15;
                root.Add(_prompt);
            }
            if (_prompt != null) _prompt.style.display = on ? DisplayStyle.Flex : DisplayStyle.None;
        }
    }
}
