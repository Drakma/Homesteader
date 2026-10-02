using System.Collections.Generic;
using Homesteader.Controls;
using Homesteader.UI;
using UnityEngine;

namespace Homesteader.Growth
{
    /// <summary>
    /// Cutaway view of a finished building while the player is inside it: the roof and the walls between the camera and the player stop
    /// being drawn (they keep casting their shadows, so the light inside does not change), so the interior shows. The models split these
    /// parts into their own objects (Roof, Wall_Front, Wall_Back, Wall_Left, Wall_Right; see docs/STRUCTURE_STAGES_GUIDE.md). The window
    /// panes stay visible so you can see where the windows are. The key (V by default, rebindable) turns the cutaway on and off; the
    /// choice is remembered.
    /// </summary>
    public sealed class StructureCutaway : MonoBehaviour
    {
        private const string PrefKey = "Homesteader.Cutaway";
        private static bool s_on = true;

        private ConstructionSite _site;
        private readonly List<Entry> _entries = new List<Entry>();
        private float _nextCollect;

        private struct Entry
        {
            public Renderer R;
            public int Kind;                  // 0 roof, 1 wall, 2 glass
            public Vector3 OutwardLocal;      // walls: which way the wall faces, in the site's local space
            public Collider[] Cols;           // the part's colliders and the layers they were on
            public int[] Layers;
        }

        private const int IgnoreRaycastLayer = 2;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        private static void Bootstrap()
        {
            if (FindAnyObjectByType<StructureCutaway>() != null) return;
            s_on = PlayerPrefs.GetInt(PrefKey, 1) == 1;
            var go = new GameObject("StructureCutaway");
            DontDestroyOnLoad(go);
            go.AddComponent<StructureCutaway>();
        }

        private void Update()
        {
            if (!WelcomeMenuController.IsLoading && !HudBindings.KeyboardCaptured && KeyBindings.WasPressedThisFrame(BindAction.ToggleCutaway))
            {
                s_on = !s_on;
                PlayerPrefs.SetInt(PrefKey, s_on ? 1 : 0);
                PlayerPrefs.Save();
            }

            ConstructionSite inside = s_on && !WelcomeMenuController.IsLoading ? SiteAroundPlayer() : null;
            if (inside != _site)
            {
                Restore();
                _site = inside;
                if (_site != null) Collect();
            }
            if (_site == null) return;
            if (_entries.Count == 0 && Time.unscaledTime >= _nextCollect) { _nextCollect = Time.unscaledTime + 0.5f; Collect(); }   // the model may still have been loading
            Apply();
        }

        private static ConstructionSite SiteAroundPlayer()
        {
            var ped = FindAnyObjectByType<PedController>();
            if (ped == null) return null;
            foreach (ConstructionSite s in ConstructionSite.All)
                if (s != null && s.HasDoor && s.IsInside(ped.transform.position)) return s;   // any stage that has the shell with its door
            return null;
        }

        private void Collect()
        {
            _entries.Clear();
            Transform root = _site.VisualRoot;
            if (root == null) return;
            foreach (Renderer r in root.GetComponentsInChildren<Renderer>(true))
            {
                // the part's name is on the renderer's object or on one above it (a mesh with several materials can come in as children)
                string n = null;
                for (Transform t = r.transform; t != null && t != root.parent; t = t.parent)
                    if (t.name == "Roof" || t.name == "WindowGlass" || t.name.StartsWith("Wall_")) { n = t.name; break; }
                if (n == null) continue;
                Collider[] cols = r.GetComponents<Collider>();
                var layers = new int[cols.Length];
                for (int ci = 0; ci < cols.Length; ci++) layers[ci] = cols[ci].gameObject.layer;
                if (n == "Roof") _entries.Add(new Entry { R = r, Kind = 0, Cols = cols, Layers = layers });
                else if (n == "WindowGlass") continue;   // the panes stay, so you can see where the windows are (and keep things away from them)
                else
                {
                    // which way the wall faces: from the middle of the building to the middle of the wall
                    Vector3 local = _site.transform.InverseTransformPoint(r.bounds.center);
                    Vector3 outward = Mathf.Abs(local.x) > Mathf.Abs(local.z) ? new Vector3(Mathf.Sign(local.x), 0f, 0f) : new Vector3(0f, 0f, Mathf.Sign(local.z));
                    _entries.Add(new Entry { R = r, Kind = 1, OutwardLocal = outward, Cols = cols, Layers = layers });
                }
            }
        }

        private void Apply()
        {
            Camera cam = Camera.main != null ? Camera.main : FindAnyObjectByType<Camera>();
            Vector3 toCamera = cam != null ? -cam.transform.forward : Vector3.back;
            toCamera.y = 0f;
            toCamera.Normalize();
            foreach (Entry e in _entries)
            {
                if (e.R == null) continue;
                bool hide = e.Kind != 1 || Vector3.Dot(_site.transform.TransformDirection(e.OutwardLocal), toCamera) > 0.25f;
                Show(e, !hide);
            }
        }

        private static void Show(Entry e, bool visible)
        {
            if (e.Kind == 2) { e.R.enabled = visible; return; }   // a window pane casts no shadow either way
            // hidden walls and roof still cast their shadows, so the inside is as dark as before
            e.R.shadowCastingMode = visible ? UnityEngine.Rendering.ShadowCastingMode.On : UnityEngine.Rendering.ShadowCastingMode.ShadowsOnly;
            // a hidden wall or roof must not catch the mouse: its colliders move to the Ignore Raycast layer (the player still collides with
            // them, only raycasts such as clicks, hover and placement pass through)
            if (e.Cols != null)
                for (int i = 0; i < e.Cols.Length; i++)
                    if (e.Cols[i] != null) e.Cols[i].gameObject.layer = visible ? e.Layers[i] : IgnoreRaycastLayer;
        }

        private void Restore()
        {
            foreach (Entry e in _entries)
            {
                if (e.R == null) continue;
                e.R.enabled = true;
                e.R.shadowCastingMode = e.Kind == 2 ? UnityEngine.Rendering.ShadowCastingMode.Off : UnityEngine.Rendering.ShadowCastingMode.On;   // glass casts no shadow
                if (e.Cols != null)
                    for (int i = 0; i < e.Cols.Length; i++)
                        if (e.Cols[i] != null) e.Cols[i].gameObject.layer = e.Layers[i];
            }
            _entries.Clear();
        }

        private void OnDisable() { Restore(); }
    }
}
