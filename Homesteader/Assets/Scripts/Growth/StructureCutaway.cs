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
        private int _chimneys = -1;   // how many chimneys the building had when the entries were made
        private int _roofItems = -1;   // how many roof-mounted things (racks, panels) there were when the entries were made

        private struct Entry
        {
            public Renderer R;
            public int Kind;                  // 0 roof, 1 wall, 2 glass, 3 a door (faded, still there to click and walk through)
            public Vector3 OutwardLocal;      // walls: which way the wall faces, in the site's local space
            public bool Window;               // a movable window's frame or pane: it hides with the wall it is in (found after all the walls are known)
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
            if (_site != null && ChimneyCount(_site) != _chimneys) { Restore(); Collect(); }   // a chimney was built or taken down
            if (Time.unscaledTime >= _nextPatchLook)
            {
                _nextPatchLook = Time.unscaledTime + 0.25f;
                int found = 0;
                Transform vr = _site.VisualRoot;
                if (vr != null) foreach (MeshRenderer mr in vr.GetComponentsInChildren<MeshRenderer>(true)) if (mr.name == "PaintPatch" || (mr.name.StartsWith("Window") && mr.gameObject.activeInHierarchy)) found++;
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

        private static int ChimneyCount(ConstructionSite site)
        {
            int n = 0;
            foreach (PlacedChimney c in PlacedChimney.All) if (c != null && c.Site == site) n++;
            return n;
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
            // the chimneys of this building: the STACK (outside, up through the roof) goes with the roof; the breast and the firebox inside stay
            _chimneys = ChimneyCount(_site);
            foreach (PlacedChimney ch in PlacedChimney.All)
            {
                if (ch == null || ch.Site != _site) continue;
                foreach (Transform t in ch.GetComponentsInChildren<Transform>(true))
                {
                    if (t.name != ChimneyBuilder.StackName) continue;
                    Collider[] ccols = t.GetComponentsInChildren<Collider>(true);
                    var clayers = new int[ccols.Length];
                    for (int ci = 0; ci < ccols.Length; ci++) clayers[ci] = ccols[ci].gameObject.layer;
                    bool firstR = true;
                    foreach (Renderer cr in t.GetComponentsInChildren<Renderer>(true))
                    {
                        _entries.Add(new Entry { R = cr, Kind = 0, Cols = firstR ? ccols : new Collider[0], Layers = firstR ? clayers : new int[0] });
                        firstR = false;
                    }
                }
            }
            Transform root = _site.VisualRoot;
            if (root == null) return;
            _patches = 0;
            // The middle of each WING (a wall part named "Wall_Back@B" is a wing "B" part; no tag is the main wing): which way a wall faces is measured from the middle of its own wing,
            // not from the middle of the whole building (an L-shaped house's origin is at the back wall of the main wing, so its back wall would face the front).
            var wingBox = new Dictionary<string, Bounds>();
            var partOutward = new Dictionary<Transform, Vector3>();   // which way each wall part faces (one answer per part)
            foreach (Renderer r in root.GetComponentsInChildren<Renderer>(true))
            {
                string wname = null;
                for (Transform t = r.transform; t != null && t != root.parent; t = t.parent)
                    if (t.name.StartsWith("Wall_")) { wname = t.name; break; }
                if (wname == null) continue;
                int wat = wname.IndexOf('@');
                string tag = wat >= 0 ? wname.Substring(wat + 1) : "";
                Bounds wb = r.bounds;
                for (int ci = 0; ci < 8; ci++)
                {
                    Vector3 corner = wb.center + Vector3.Scale(wb.extents, new Vector3((ci & 1) == 0 ? -1 : 1, (ci & 2) == 0 ? -1 : 1, (ci & 4) == 0 ? -1 : 1));
                    Vector3 lc = _site.transform.InverseTransformPoint(corner);
                    if (!wingBox.TryGetValue(tag, out Bounds acc)) acc = new Bounds(lc, Vector3.zero); else acc.Encapsulate(lc);
                    wingBox[tag] = acc;
                }
            }
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
                    if (t.name == "Roof" || t.name == "Porch" || t.name.StartsWith("WindowGlass") || t.name.StartsWith("WindowFrame_") || t.name.StartsWith("WindowMuntin_") || t.name.StartsWith("Wall_") || t.name.StartsWith("Door")) { n = t.name; part = t; break; }
                if (n == null) continue;
                // every collider of the part: glTFast puts the MeshCollider on the part's own object while a multi-material mesh renders from child
                // primitives, so the renderer's own object alone misses it and the hidden wall kept catching clicks
                Collider[] cols = part.GetComponentsInChildren<Collider>(true);
                var layers = new int[cols.Length];
                for (int ci = 0; ci < cols.Length; ci++) layers[ci] = cols[ci].gameObject.layer;
                if (n == "Roof" || n == "Porch") _entries.Add(new Entry { R = r, Kind = 0, Cols = cols, Layers = layers });
                else if (n.StartsWith("WindowGlass") || n.StartsWith("WindowFrame_") || n.StartsWith("WindowMuntin_"))
                {
                    if (n == "WindowGlass") { _entries.Add(new Entry { R = r, Kind = 0, Cols = cols, Layers = layers }); continue; }   // the panes of the doors, the vents: with the roof
                    // a movable window hides with the wall it is in (the wall it sits nearest to, judged against the footprint so a long wall does not read as a side one)
                    Vector3 wl = _site.transform.InverseTransformPoint(r.bounds.center);
                    Vector2 fp = _site.Footprint;
                    Vector3 wout = Mathf.Abs(wl.x) / Mathf.Max(0.01f, fp.x) > Mathf.Abs(wl.z) / Mathf.Max(0.01f, fp.y) ? new Vector3(Mathf.Sign(wl.x), 0f, 0f) : new Vector3(0f, 0f, Mathf.Sign(wl.z));
                    if (r.gameObject.activeInHierarchy) _patches++;       // (counted, so a window put in, taken out or swapped is seen: Update)
                    _entries.Add(new Entry { R = r, Kind = n.StartsWith("WindowGlass") ? 5 : 1, OutwardLocal = wout, Cols = cols, Layers = layers, Window = true });   // (5: a pane: hidden with its wall, never a shadow)
                }   // the panes go with the cutaway (they are one object for the whole building, so all together)
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
                    Vector3 outward;
                    int wat = n.IndexOf('@');
                    if (n.StartsWith("Wall_") && wingBox.TryGetValue(wat >= 0 ? n.Substring(wat + 1) : "", out Bounds wing))
                    {
                        // ONE answer for the whole wall part, from where the part as a whole stands in its own wing (measured against the wing's half sizes, so a long wing's back wall
                        // is not taken for a side wall): a window casing or a gable at the end of a long wall must hide with its wall, not with the wall at that end
                        if (!partOutward.TryGetValue(part, out outward))
                        {
                            Bounds pb = default;
                            bool anyPart = false;
                            foreach (Renderer pr in part.GetComponentsInChildren<Renderer>(true))
                            {
                                Bounds b0 = pr.bounds;
                                for (int ci = 0; ci < 8; ci++)
                                {
                                    Vector3 corner = b0.center + Vector3.Scale(b0.extents, new Vector3((ci & 1) == 0 ? -1 : 1, (ci & 2) == 0 ? -1 : 1, (ci & 4) == 0 ? -1 : 1));
                                    Vector3 lc = _site.transform.InverseTransformPoint(corner);
                                    if (!anyPart) { pb = new Bounds(lc, Vector3.zero); anyPart = true; } else pb.Encapsulate(lc);
                                }
                            }
                            Vector3 rel = pb.center - wing.center;
                            outward = Mathf.Abs(rel.x) / Mathf.Max(0.5f, wing.extents.x) > Mathf.Abs(rel.z) / Mathf.Max(0.5f, wing.extents.z) ? new Vector3(Mathf.Sign(rel.x), 0f, 0f) : new Vector3(0f, 0f, Mathf.Sign(rel.z));
                            partOutward[part] = outward;
                        }
                    }
                    else outward = Mathf.Abs(local.x) > Mathf.Abs(local.z) ? new Vector3(Mathf.Sign(local.x), 0f, 0f) : new Vector3(0f, 0f, Mathf.Sign(local.z));
                    _entries.Add(new Entry { R = r, Kind = n.StartsWith("Door") ? 3 : 1, OutwardLocal = outward, Cols = cols, Layers = layers });
                }
            }
            // paint on an outside wall goes with the wall it is on: the nearest wall part (the building's middle is no guide on an L)
            for (int i = 0; i < _entries.Count; i++)
            {
                if ((_entries[i].Kind != 4 && !_entries[i].Window) || _entries[i].R == null) continue;   // paint, and the windows (on an L the building's middle is no guide to which wall a window is in)
                float bestD = float.MaxValue;
                Vector3 pc = _entries[i].R.bounds.center;
                Entry e4 = _entries[i];
                foreach (Entry w in _entries)
                {
                    if (w.Kind != 1 || w.Window || w.R == null) continue;
                    float d = (w.R.bounds.ClosestPoint(pc) - pc).sqrMagnitude;
                    if (d < bestD) { bestD = d; e4.OutwardLocal = w.OutwardLocal; }
                }
                _entries[i] = e4;
            }
        }

        private void Apply()
        {
            Camera cam = Camera.main != null ? Camera.main : FindAnyObjectByType<Camera>();
            Vector3 toCamera = cam != null ? -cam.transform.forward : Vector3.back;
            toCamera.y = 0f;
            toCamera.Normalize();
            PedController ped = PedController.Current;
            Vector3 pedLocal = ped != null ? _site.transform.InverseTransformPoint(ped.transform.position) : Vector3.zero;
            foreach (Entry e in _entries)
            {
                if (e.R == null) continue;
                bool facing = Vector3.Dot(_site.transform.TransformDirection(e.OutwardLocal), toCamera) > 0.25f;
                if (facing && ped != null && e.OutwardLocal.sqrMagnitude > 0.1f)
                {
                    // a wall is between the camera and the player only when the player is on its INSIDE: a player past the wall's plane (in the den of an L, behind the main wing's back wall,
                    // which is an outside wall from the other side) keeps it: it is the wall of the room they stand in
                    float plane = Vector3.Dot(_site.transform.InverseTransformPoint(e.R.bounds.center), e.OutwardLocal);
                    if (Vector3.Dot(pedLocal, e.OutwardLocal) > plane + 0.05f) facing = false;
                }
                if (e.Kind == 3) { Fade(e.R, facing); continue; }
                if (e.Kind == 4 || e.Kind == 5) { e.R.enabled = !facing; continue; }   // paint on a wall, a window pane: gone with the wall
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
                e.R.shadowCastingMode = e.Kind == 2 || e.Kind == 4 || e.Kind == 5 ? UnityEngine.Rendering.ShadowCastingMode.Off : UnityEngine.Rendering.ShadowCastingMode.On;   // glass and paint cast no shadow
                if (e.Cols != null)
                    for (int i = 0; i < e.Cols.Length; i++)
                        if (e.Cols[i] != null) e.Cols[i].gameObject.layer = e.Layers[i];
            }
            _entries.Clear();
        }

        private void OnDisable() { Restore(); }
    }
}
