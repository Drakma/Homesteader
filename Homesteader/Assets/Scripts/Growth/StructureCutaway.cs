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
    /// panes go with the cutaway, and an outside door in a hidden wall is faded (translucent, still there to click and walk through). The key (V by default, rebindable) turns the cutaway on and off; the
    /// choice is remembered.
    /// </summary>
    public sealed class StructureCutaway : MonoBehaviour
    {
        private const string PrefKey = "Homesteader.Cutaway";
        private static bool s_on = true;
        /// <summary>True while the cutaway is on (the key turns it off): the structure hider follows it.</summary>
        public static bool On => s_on;
        /// <summary>The building the player is inside and the cutaway is opening, or null.</summary>
        public static ConstructionSite Current { get; private set; }

        private ConstructionSite _site;
        private readonly List<Entry> _entries = new List<Entry>();
        private float _nextCollect;
        private int _roofItems = -1;   // how many roof-mounted things (racks, panels) there were when the entries were made

        private struct Entry
        {
            public Renderer R;
            public int Kind;                  // 0 roof, 1 wall, 2 glass, 3 a door (faded, still there to click and walk through)
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

            ConstructionSite inside = s_on && !IsometricLockedCamera.FirstPerson && !WelcomeMenuController.IsLoading ? SiteAroundPlayer() : null;   // in first person the walls and roof stay
            Current = inside;
            if (inside != _site)
            {
                Restore();
                _site = inside;
                if (_site != null) Collect();
            }
            if (_site == null) return;
            if (_site != null && RoofItemCount(_site) != _roofItems) { Restore(); Collect(); }   // a rack was mounted or taken down
            if (Time.unscaledTime >= _nextPatchLook)
            {
                _nextPatchLook = Time.unscaledTime + 0.25f;
                int found = 0;
                Transform vr = _site.VisualRoot;
                if (vr != null) foreach (MeshRenderer mr in vr.GetComponentsInChildren<MeshRenderer>(true)) if (mr.name == "PaintPatch") found++;
                if (found != _patches) { Restore(); Collect(); }   // a wall was painted (or its paint rebuilt): the new paint goes with its wall too
            }
            if (_entries.Count == 0 && Time.unscaledTime >= _nextCollect) { _nextCollect = Time.unscaledTime + 0.5f; Collect(); }   // the model may still have been loading
            Apply();
        }

        private static ConstructionSite SiteAroundPlayer()
        {
            var ped = PedController.Current;
            if (ped == null) return null;
            foreach (ConstructionSite s in ConstructionSite.All)
                if (s != null && s.HasDoor && s.IsInside(ped.transform.position)) return s;   // any stage that has the shell with its door
            return null;
        }

        private static int RoofItemCount(ConstructionSite site)
        {
            int n = 0;
            foreach (AttachedObject a in AttachedObject.All) if (a != null && a.Site == site && a.Surface == "roof") n += a.GetComponent<MountedPanel>() != null ? 2 : 1;   // (a fitted panel is one more thing to hide)
            return n;
        }

        private int _patches;
        private float _nextPatchLook;

        private void Collect()
        {
            _entries.Clear();
            // what stands on the roof (solar racks and their panels) goes with the roof
            _roofItems = RoofItemCount(_site);
            foreach (AttachedObject a in AttachedObject.All)
            {
                if (a == null || a.Site != _site || a.Surface != "roof") continue;
                Collider[] acols = a.GetComponentsInChildren<Collider>(true);
                var alayers = new int[acols.Length];
                for (int ci = 0; ci < acols.Length; ci++) alayers[ci] = acols[ci].gameObject.layer;
                bool first = true;
                foreach (Renderer r in a.GetComponentsInChildren<Renderer>(true))
                {
                    _entries.Add(new Entry { R = r, Kind = 0, Cols = first ? acols : new Collider[0], Layers = first ? alayers : new int[0] });
                    first = false;
                }
            }
            Transform root = _site.VisualRoot;
            if (root == null) return;
            _patches = 0;
            foreach (Renderer r in root.GetComponentsInChildren<Renderer>(true))
            {
                if (r.name == "PaintPatch")
                {
                    // paint laid on a wall (ConstructionSite paint patches) hides with that wall: the wall it is on is the nearest edge of the building;
                    // paint on a wall inside the building (a partition) stays
                    _patches++;
                    Vector3 pl = _site.transform.InverseTransformPoint(r.bounds.center);
                    Vector2 fp = _site.Footprint;
                    if (Mathf.Abs(pl.x) < fp.x * 0.5f - 0.6f && Mathf.Abs(pl.z) < fp.y * 0.5f - 0.6f) continue;
                    Vector3 pout = Mathf.Abs(pl.x) / Mathf.Max(0.01f, fp.x) > Mathf.Abs(pl.z) / Mathf.Max(0.01f, fp.y) ? new Vector3(Mathf.Sign(pl.x), 0f, 0f) : new Vector3(0f, 0f, Mathf.Sign(pl.z));
                    _entries.Add(new Entry { R = r, Kind = 4, OutwardLocal = pout });
                    continue;
                }
                // the part's name is on the renderer's object or on one above it (a mesh with several materials can come in as children)
                string n = null;
                Transform part = null;
                for (Transform t = r.transform; t != null && t != root.parent; t = t.parent)
                    if (t.name == "Roof" || t.name == "Porch" || t.name == "WindowGlass" || t.name.StartsWith("Wall_") || t.name.StartsWith("Door")) { n = t.name; part = t; break; }
                if (n == null) continue;
                // every collider of the part: glTFast puts the MeshCollider on the part's own object while a multi-material mesh renders from child
                // primitives, so the renderer's own object alone misses it and the hidden wall kept catching clicks
                Collider[] cols = part.GetComponentsInChildren<Collider>(true);
                var layers = new int[cols.Length];
                for (int ci = 0; ci < cols.Length; ci++) layers[ci] = cols[ci].gameObject.layer;
                if (n == "Roof" || n == "Porch") _entries.Add(new Entry { R = r, Kind = 0, Cols = cols, Layers = layers });
                else if (n == "WindowGlass") _entries.Add(new Entry { R = r, Kind = 0, Cols = cols, Layers = layers });   // the panes go with the cutaway (they are one object for the whole building, so all together)
                else
                {
                    // which way the wall faces: from the middle of the building to the middle of the wall
                    Vector3 local = _site.transform.InverseTransformPoint(r.bounds.center);
                    // a door of the building's outside hides with the wall it is in; a door inside (between rooms) stays
                    if (n.StartsWith("Door"))
                    {
                        Vector2 foot = _site.Footprint;
                        if (Mathf.Abs(local.x) < foot.x * 0.5f - 0.6f && Mathf.Abs(local.z) < foot.y * 0.5f - 0.6f) continue;
                    }
                    Vector3 outward = Mathf.Abs(local.x) > Mathf.Abs(local.z) ? new Vector3(Mathf.Sign(local.x), 0f, 0f) : new Vector3(0f, 0f, Mathf.Sign(local.z));
                    _entries.Add(new Entry { R = r, Kind = n.StartsWith("Door") ? 3 : 1, OutwardLocal = outward, Cols = cols, Layers = layers });
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
                bool facing = Vector3.Dot(_site.transform.TransformDirection(e.OutwardLocal), toCamera) > 0.25f;
                if (e.Kind == 3) { Fade(e.R, facing); continue; }
                if (e.Kind == 4) { e.R.enabled = !facing; continue; }   // paint on a wall: gone with the wall
                bool hide = e.Kind != 1 || facing;
                Show(e, !hide);
            }
        }

        // ------------------------------------------------------------------ fading a door

        private const float DoorAlpha = 0.28f;
        private static readonly Dictionary<Renderer, Material[]> s_faded = new Dictionary<Renderer, Material[]>();   // renderer -> its own materials while faded
        private static readonly Dictionary<Renderer, Material[]> s_madeFor = new Dictionary<Renderer, Material[]>();

        /// <summary>Fades a door (translucent copies of its materials, same colour and picture) or puts its own materials back.</summary>
        private static void Fade(Renderer r, bool faded)
        {
            if (r == null) return;
            if (faded)
            {
                if (s_faded.ContainsKey(r)) return;
                Material[] src = r.sharedMaterials;
                var made = new Material[src.Length];
                for (int i = 0; i < src.Length; i++) made[i] = FadedCopy(src[i]);
                s_faded[r] = src;
                s_madeFor[r] = made;
                r.sharedMaterials = made;
            }
            else if (s_faded.TryGetValue(r, out Material[] own))
            {
                r.sharedMaterials = own;
                if (s_madeFor.TryGetValue(r, out Material[] made)) foreach (Material m in made) if (m != null) Destroy(m);
                s_faded.Remove(r);
                s_madeFor.Remove(r);
            }
        }

        private static Material FadedCopy(Material src)
        {
            var f = new Material(Shader.Find("Universal Render Pipeline/Lit")) { name = "DoorFaded" };
            Color c = Color.white;
            if (src != null)
            {
                if (src.HasProperty("baseColorFactor")) c = src.GetColor("baseColorFactor");
                else if (src.HasProperty("_BaseColor")) c = src.GetColor("_BaseColor");
                Texture tex = src.HasProperty("baseColorTexture") ? src.GetTexture("baseColorTexture") : src.HasProperty("_BaseMap") ? src.GetTexture("_BaseMap") : null;
                if (tex != null) f.SetTexture("_BaseMap", tex);
            }
            c.a = DoorAlpha;
            f.SetColor("_BaseColor", c);
            f.SetFloat("_Smoothness", 0.25f);
            f.SetFloat("_Surface", 1f);
            f.SetFloat("_Blend", 0f);
            f.SetFloat("_ZWrite", 0f);
            f.SetInt("_SrcBlend", (int)UnityEngine.Rendering.BlendMode.SrcAlpha);
            f.SetInt("_DstBlend", (int)UnityEngine.Rendering.BlendMode.OneMinusSrcAlpha);
            f.EnableKeyword("_SURFACE_TYPE_TRANSPARENT");
            f.SetOverrideTag("RenderType", "Transparent");
            f.renderQueue = 3000;
            return f;
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
                if (e.Kind == 3) Fade(e.R, false);
                e.R.enabled = true;
                e.R.shadowCastingMode = e.Kind == 2 || e.Kind == 4 ? UnityEngine.Rendering.ShadowCastingMode.Off : UnityEngine.Rendering.ShadowCastingMode.On;   // glass and paint cast no shadow
                if (e.Cols != null)
                    for (int i = 0; i < e.Cols.Length; i++)
                        if (e.Cols[i] != null) e.Cols[i].gameObject.layer = e.Layers[i];
            }
            _entries.Clear();
        }

        private void OnDisable() { Restore(); }
    }
}
