using System.Collections.Generic;
using Homesteader.UI;
using UnityEngine;
#if ENABLE_INPUT_SYSTEM
using UnityEngine.InputSystem;
#endif

namespace Homesteader.Growth
{
    /// <summary>
    /// WINDOWS OF A FINISHED BUILDING (docs/WINDOWS.md). In the finished model the walls are solid where a window is, and each window is an empty "WinSpec_k_wall_u0_u1_z0_z1_m2"
    /// (millimetres, in the model file's axes; the wall may end in "@B": the cross wing of the L-shaped house) plus its objects (WindowFrame_k, WindowGlass_k). This component, on the model's root:
    ///  - cuts the hole: each wall's meshes are copied with every triangle clipped against the window rectangles, and the wall's colliders take the same mesh, so the hole is real for the
    ///    eye, shadows, rays (paint, rooms, the cursor) and the player;
    ///  - slides a window (a wrench in the active slot, Shift + right click: it follows the cursor along its wall, never over a door, a corner or another window; left click sets it down, Esc puts it back);
    ///  - the muntins are part of the window ITEM (every type comes in every pattern of bars; a window is changed by swapping it for another window item); the bars are drawn here for every window, so every building acts the same;
    ///  - removes it (a wrench, Ctrl + right click: the wall closes and the window goes into the toolbar as its item);
    ///  - swaps it (a window item in hand, right click on a window: the held type replaces it, and the old one goes into the toolbar) or puts one in (a window item in hand, right click on a bare wall).
    /// A window put in or swapped is built here from its type (a frame, a pane, a rail or a stile; building_window_*) in the building's own trim material. Everything about each window is
    /// saved with the building (SavedSite.windowStates).
    /// </summary>
    public sealed class StructureWindows : MonoBehaviour
    {
        public sealed class Win
        {
            public int Index;
            public string Token;                   // the wall: front, back, left, right (+ "@B" for the L-shaped house's cross wing)
            public bool OnX;                       // the wall runs along the model's x (front and back walls), else along z
            public Vector3 Outward;                // out of the building, in the model's space
            public float DefU0, DefU1, DefZ0, DefZ1;   // the opening as built, in the model's (Unity) space
            public bool Baked = true;              // part of the model (else put in by the player)
            public bool Removed;
            public string Type;                    // null = as built, else the item id of the window
            public int MuntinCount = 2;            // the pattern of bars (see MuntinGrid): 0 none ... MuntinPatterns - 1
            public float CentreU, Sill, W, H;      // the opening now
            public float Outer, Thick;             // where the wall's outer face is (across the wall) and how thick the wall is
            public Transform BakedFrame, BakedGlass;
            public Vector3 FrameHome, GlassHome;
            public readonly List<Transform> BakedMuntins = new List<Transform>();
            public GameObject RFrame, RGlass, RMuntins;     // built here
            public bool Shutters;                  // a pair of shutters on it (the model's own, or built here)
            public readonly List<Renderer> BakedShutters = new List<Renderer>();   // the model's own shutters of this window (they stand in its frame object)
            public GameObject RShutters;           // built here
            public float U0 { get { return CentreU - W * 0.5f; } }
            public float U1 { get { return CentreU + W * 0.5f; } }
            public float Z0 { get { return Sill; } }
            public float Z1 { get { return Sill + H; } }
            public float DefCentre { get { return (DefU0 + DefU1) * 0.5f; } }
        }

        private struct Hole { public bool OnX; public float U0, U1, Y0, Y1; }

        private sealed class WallMesh
        {
            public string Token;
            public MeshFilter Filter;
            public Mesh Original, Clipped;
            public MeshCollider[] Colliders;
            public Matrix4x4 ToRoot, FromRoot;
            public Vector3[] RootVerts;           // the original mesh's vertices in the model's space, worked out once (Mesh.vertices copies the whole array every time it is read)
        }

        // the window items: width, and the tallest the opening may be (it stays under the head of the building's own windows)
        private static readonly Dictionary<string, Vector2> BaseTypes = new Dictionary<string, Vector2>
        {
            { "building_window_double_hung", new Vector2(0.96f, 1.43f) },
            { "building_window_picture", new Vector2(1.56f, 1.23f) },
            { "building_window_slider", new Vector2(1.26f, 0.83f) },
        };

        // The bars are part of the window item: each type comes in every pattern of MuntinGrid (tools/make_window_variants.py makes the items). The suffix of the item id says which; the base
        // item is the cross (pattern 2). A window is changed by clicking it with a different window item in hand.
        private static readonly string[] PatternSuffix = { "_plain", "_panes2", "", "_panes6", "_panes8" };   // plain, two panes, four panes (the base item), six, eight
        private static readonly Dictionary<string, Vector2> Types = BuildTypes(out ItemPattern, out ItemBase);
        private static Dictionary<string, int> ItemPattern;              // window item id -> its pattern of bars
        private static Dictionary<string, string> ItemBase;              // window item id -> the base item of its type

        private static Dictionary<string, Vector2> BuildTypes(out Dictionary<string, int> pattern, out Dictionary<string, string> baseOf)
        {
            var types = new Dictionary<string, Vector2>();
            pattern = new Dictionary<string, int>();
            baseOf = new Dictionary<string, string>();
            foreach (KeyValuePair<string, Vector2> kv in BaseTypes)
                for (int p = 0; p < PatternSuffix.Length; p++)
                {
                    string id = kv.Key + PatternSuffix[p];
                    types[id] = kv.Value; pattern[id] = p; baseOf[id] = kv.Key;
                }
            return types;
        }

        private const float CornerMarginM = 0.30f;     // a window stays this far from the end of its wall (the corner boards, the jamb)
        private const float NeighbourMarginM = 0.15f;  // and from another window
        private const float DoorMarginM = 0.35f;       // and from a door and its frame
        private const float ReachM = 4.5f;             // the player must be this close to work on one
        private const float MinHeightM = 0.45f;

        public readonly List<Win> Windows = new List<Win>();
        private readonly List<WallMesh> _walls = new List<WallMesh>();
        private readonly Dictionary<string, Vector2> _wallRange = new Dictionary<string, Vector2>();   // the extent of each wall along its axis
        private Transform _root;
        private ConstructionSite _site;
        private Win _moving;
        private float _startCentre;
        private float _headLimit = 2.15f;              // the head of the tallest window the building came with
        private Material _trimMat, _glassMat, _shutterMat;
        public const string ShutterItem = "building_window_shutters";
        public static bool IsShutterItem(string itemId) { return itemId == ShutterItem; }
        private int _nextIndex = 1000;

        public static bool IsWindowItem(string itemId) { return !string.IsNullOrEmpty(itemId) && Types.ContainsKey(itemId); }

        // ------------------------------------------------------------------ attaching

        /// <summary>Finds the windows of a finished model and cuts their holes. Null when the model has none (the early stages keep their own openings).</summary>
        public static StructureWindows Attach(ConstructionSite site, Transform model, List<string> states)
        {
            if (model == null) return null;
            var specs = new List<Transform>();
            foreach (Transform t in model.GetComponentsInChildren<Transform>(true)) if (t.name.StartsWith("WinSpec_")) specs.Add(t);
            if (specs.Count == 0) return null;
            StructureWindows sw = model.gameObject.AddComponent<StructureWindows>();
            sw.Init(site, model, specs, states);
            return sw;
        }

        private static string Cap(string s) { return char.ToUpperInvariant(s[0]) + s.Substring(1); }

        private static void SetWall(Win w, string token)
        {
            w.Token = token;
            string b = token.Split('@')[0];
            w.OnX = b == "front" || b == "back";
            // the model is mirrored from the file's axes: the file's front (-y) is +z here, the file's left wall (-x) is at +x
            switch (b) { case "front": w.Outward = Vector3.forward; break; case "back": w.Outward = Vector3.back; break; case "left": w.Outward = Vector3.right; break; default: w.Outward = Vector3.left; break; }
        }

        private void Init(ConstructionSite site, Transform model, List<Transform> specs, List<string> states)
        {
            _site = site;
            _root = model;
            var tokens = new List<string>();
            foreach (Transform t in specs)
            {
                string[] p = t.name.Split('_');   // WinSpec_<k>_<wall>_<u0>_<u1>_<z0>_<z1>[_m<n>], millimetres
                if (p.Length < 7 || !int.TryParse(p[1], out int k) || !int.TryParse(p[3], out int u0) || !int.TryParse(p[4], out int u1) || !int.TryParse(p[5], out int z0) || !int.TryParse(p[6], out int z1)) continue;
                var w = new Win { Index = k };
                SetWall(w, p[2]);
                if (!tokens.Contains(p[2])) tokens.Add(p[2]);
                Vector3 off = _root.InverseTransformPoint(t.position);   // the spec empty sits at the file's origin: where it is now is how far the loader moved the model (grounding it)
                float du = w.OnX ? off.x : off.z;
                w.DefU0 = -u1 / 1000f + du; w.DefU1 = -u0 / 1000f + du; w.DefZ0 = z0 / 1000f + off.y; w.DefZ1 = z1 / 1000f + off.y;   // the file's x and y run the other way round here
                w.CentreU = w.DefCentre; w.Sill = w.DefZ0; w.W = w.DefU1 - w.DefU0; w.H = w.DefZ1 - w.DefZ0;
                if (p.Length > 7 && p[7].Length > 1 && p[7][0] == 'm' && int.TryParse(p[7].Substring(1), out int dm)) w.MuntinCount = Mathf.Clamp(dm, 0, MuntinPatterns - 1);
                w.BakedFrame = FindNamed("WindowFrame_" + k);
                w.BakedGlass = FindNamed("WindowGlass_" + k);
                if (w.BakedFrame != null) w.FrameHome = w.BakedFrame.localPosition;
                if (w.BakedGlass != null) w.GlassHome = w.BakedGlass.localPosition;
                if (w.BakedFrame != null)
                    foreach (Renderer sr in w.BakedFrame.GetComponentsInChildren<Renderer>(true))   // the part of the frame that is all shutter material: a renderer of its own
                    {
                        Material[] sm = sr.sharedMaterials;
                        bool all = sm.Length > 0;
                        foreach (Material m1 in sm) if (m1 == null || !m1.name.StartsWith("Shutter")) all = false;
                        if (!all) continue;
                        w.BakedShutters.Add(sr);
                        if (_shutterMat == null) _shutterMat = sm[0];
                    }
                w.Shutters = w.BakedShutters.Count > 0;
                for (int mn = 1; mn <= 3; mn++) { Transform m = FindNamed("WindowMuntin_" + k + "_" + mn); if (m != null) { w.BakedMuntins.Add(m); m.gameObject.SetActive(false); } }   // (the bars are drawn here)
                _headLimit = Mathf.Max(_headLimit, w.DefZ1);
                Windows.Add(w);
            }
            Windows.Sort((a, b) => a.Index.CompareTo(b.Index));
            foreach (Transform wt in _root.GetComponentsInChildren<Transform>(true))   // every wall, also one with no window yet: a window can be put into it
            {
                if (!wt.name.StartsWith("Wall_")) continue;
                string wn = wt.name.Substring(5);
                string wb = wn.Split('@')[0].ToLowerInvariant();
                if (wb != "front" && wb != "back" && wb != "left" && wb != "right") continue;
                string wtok = wb + (wn.Contains("@") ? "@" + wn.Split('@')[1] : "");
                if (!tokens.Contains(wtok)) tokens.Add(wtok);
            }
            foreach (Win w in Windows)
            {
                if (_trimMat == null && w.BakedFrame != null) _trimMat = TrimMaterial(w.BakedFrame);
                if (_glassMat == null && w.BakedGlass != null) { Renderer gr = w.BakedGlass.GetComponentInChildren<Renderer>(true); if (gr != null) _glassMat = gr.sharedMaterial; }
            }
            foreach (string token in tokens)
            {
                string b = token.Split('@')[0];
                Transform part = FindNamed("Wall_" + Cap(b) + (token.Contains("@") ? "@" + token.Split('@')[1] : ""));
                if (part == null) continue;
                bool onX = b == "front" || b == "back";
                float lo = float.MaxValue, hi = float.MinValue;
                foreach (MeshFilter mf in part.GetComponentsInChildren<MeshFilter>(true))
                {
                    if (mf.sharedMesh == null) continue;
                    var wm = new WallMesh { Token = token, Filter = mf, Original = mf.sharedMesh, Colliders = mf.GetComponents<MeshCollider>() };
                    wm.ToRoot = _root.worldToLocalMatrix * mf.transform.localToWorldMatrix;
                    wm.FromRoot = wm.ToRoot.inverse;
                    _walls.Add(wm);
                    Bounds bd = wm.Original.bounds;
                    for (int i = 0; i < 8; i++)
                    {
                        Vector3 c = bd.center + Vector3.Scale(bd.extents, new Vector3((i & 1) == 0 ? -1 : 1, (i & 2) == 0 ? -1 : 1, (i & 4) == 0 ? -1 : 1));
                        Vector3 r = wm.ToRoot.MultiplyPoint3x4(c);
                        float u = onX ? r.x : r.z;
                        lo = Mathf.Min(lo, u); hi = Mathf.Max(hi, u);
                    }
                }
                if (lo < hi) _wallRange[token] = new Vector2(lo, hi);
            }
            foreach (Win w in Windows) Measure(w);
            if (states != null) ApplyStates(states);
            foreach (Win w in Windows) Refresh(w);
            Rebuild(null, true);
            Store();
        }

        private Transform FindNamed(string name)
        {
            foreach (Transform t in _root.GetComponentsInChildren<Transform>(true)) if (t.name == name) return t;   // (the topmost: a multi-material part comes in as same-name children)
            return null;
        }

        private static Material TrimMaterial(Transform frame)
        {
            Material first = null;
            foreach (Renderer r in frame.GetComponentsInChildren<Renderer>(true))
                foreach (Material m in r.sharedMaterials)
                {
                    if (m == null) continue;
                    if (first == null) first = m;
                    if (m.name.StartsWith("Trim") || m.name.StartsWith("Timber")) return m;
                }
            return first;
        }

        /// <summary>Finds where the wall's outer face is and how thick it is, from the wall's own vertices round the window.</summary>
        private void Measure(Win w)
        {
            float sgn = w.OnX ? w.Outward.z : w.Outward.x;
            // the wall's vertices round the window; a flat wall has none there (its corners are far away), so the search widens: the same stretch of wall at any height, then the whole wall
            float[] reach = { 0.03f, 1.0f, float.MaxValue };
            for (int pass = 0; pass < reach.Length; pass++)
            {
                float lo = float.MaxValue, hi = float.MinValue;
                foreach (WallMesh wm in _walls)
                {
                    if (wm.Token != w.Token) continue;
                    if (wm.RootVerts == null)
                    {
                        Vector3[] raw = wm.Original.vertices;
                        wm.RootVerts = new Vector3[raw.Length];
                        for (int i = 0; i < raw.Length; i++) wm.RootVerts[i] = wm.ToRoot.MultiplyPoint3x4(raw[i]);
                    }
                    Vector3[] vs = wm.RootVerts;
                    for (int i = 0; i < vs.Length; i++)
                    {
                        Vector3 r = vs[i];
                        float u = w.OnX ? r.x : r.z;
                        if (pass < 2 && (u < w.DefU0 - reach[pass] || u > w.DefU1 + reach[pass])) continue;
                        if (pass == 0 && (r.y < w.DefZ0 - 0.03f || r.y > w.DefZ1 + 0.03f)) continue;
                        float a = (w.OnX ? r.z : r.x) * sgn;
                        lo = Mathf.Min(lo, a); hi = Mathf.Max(hi, a);
                    }
                }
                if (lo < hi && hi - lo > 0.05f && hi - lo < 0.8f) { w.Outer = hi * sgn; w.Thick = hi - lo; return; }
            }
            w.Outer = 0f; w.Thick = 0.21f;   // (the bars and the lining would then be drawn at the middle of the building: found nothing of this wall at all)
        }

        // ------------------------------------------------------------------ the state of every window (saved)

        private List<string> States()
        {
            var list = new List<string>();
            foreach (Win w in Windows)
                list.Add(w.Index + "|" + w.Token + "|" + w.CentreU.ToString("0.###", System.Globalization.CultureInfo.InvariantCulture) + "|" + w.Sill.ToString("0.###", System.Globalization.CultureInfo.InvariantCulture)
                         + "|" + (w.Type ?? "") + "|" + w.MuntinCount + "|" + (w.Removed ? 1 : 0) + "|" + (w.Baked ? 1 : 0) + "|" + (w.Shutters ? 1 : 0));
            return list;
        }

        private void Store() { if (_site != null) _site.StoreWindowStates(States()); }

        private void ApplyStates(List<string> states)
        {
            foreach (string s in states)
            {
                string[] p = s.Split('|');
                if (p.Length < 8 || !int.TryParse(p[0], out int k)) continue;
                float.TryParse(p[2], System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out float centre);
                float.TryParse(p[3], System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out float sill);
                int.TryParse(p[5], out int mun);
                bool removed = p[6] == "1", baked = p[7] == "1";
                Win w = Windows.Find(x => x.Index == k);
                if (w == null)
                {
                    if (baked) continue;
                    w = new Win { Index = k, Baked = false };
                    SetWall(w, p[1]);
                    Windows.Add(w);
                    w.Outer = 0f; w.Thick = 0.21f;
                    foreach (Win o in Windows) if (o != w && o.Token == w.Token && o.Thick > 0.05f) { w.Outer = o.Outer; w.Thick = o.Thick; break; }
                    _nextIndex = Mathf.Max(_nextIndex, k + 1);
                }
                w.CentreU = centre; w.Sill = sill; w.MuntinCount = Mathf.Clamp(mun, 0, MuntinPatterns - 1); w.Removed = removed;
                w.Type = string.IsNullOrEmpty(p[4]) ? null : p[4];
                if (p.Length >= 9) w.Shutters = p[8] == "1";      // (a save from before shutters keeps what the model came with)
                SetSize(w);
            }
        }

        // ------------------------------------------------------------------ sizes and the objects of a window

        private void SetSize(Win w)
        {
            if (string.IsNullOrEmpty(w.Type) || !Types.TryGetValue(w.Type, out Vector2 t)) { if (w.Baked) { w.W = w.DefU1 - w.DefU0; w.H = w.DefZ1 - w.DefZ0; } return; }
            w.W = t.x;
            w.H = Mathf.Min(t.y, _headLimit - w.Sill);
        }

        private static bool UsesBakedObjects(Win w) { return w.Baked && string.IsNullOrEmpty(w.Type); }

        /// <summary>Makes the window's objects match its state: the model's own, or built here; the bars always built here.</summary>
        private void Refresh(Win w)
        {
            bool baked = UsesBakedObjects(w) && !w.Removed;
            if (w.BakedFrame != null) w.BakedFrame.gameObject.SetActive(baked);
            if (w.BakedGlass != null) w.BakedGlass.gameObject.SetActive(baked);
            if (w.RFrame != null) Destroy(w.RFrame);
            if (w.RGlass != null) Destroy(w.RGlass);
            if (w.RMuntins != null) Destroy(w.RMuntins);
            if (w.RShutters != null) Destroy(w.RShutters);
            w.RFrame = w.RGlass = w.RMuntins = w.RShutters = null;
            foreach (Renderer sr in w.BakedShutters) if (sr != null) sr.enabled = baked && !w.Removed && w.Shutters;
            if (w.Removed) return;
            if (baked)
            {
                float d = w.CentreU - w.DefCentre;
                Vector3 shift = (w.OnX ? Vector3.right : Vector3.forward) * d;
                if (w.BakedFrame != null) w.BakedFrame.localPosition = w.FrameHome + shift;
                if (w.BakedGlass != null) w.BakedGlass.localPosition = w.GlassHome + shift;
            }
            else
            {
                var frame = new MeshBuilder();
                var glass = new MeshBuilder();
                BuildFrame(w, frame, glass);
                w.RFrame = MakeObject("WindowFrame_" + w.Index, frame, _trimMat, true, true);
                w.RGlass = MakeObject("WindowGlass_" + w.Index, glass, _glassMat, false, true);
            }
            if (w.Shutters && !(baked && w.BakedShutters.Count > 0))   // shutters of the model's own stand in its frame; any others are built here
            {
                var sh = new MeshBuilder();
                const float t = 0.07f;
                bool onX = w.OnX;
                foreach (float[] side in new[] { new[] { w.U0 - t - 0.42f, w.U0 - t - 0.04f }, new[] { w.U1 + t + 0.04f, w.U1 + t + 0.42f } })
                {
                    Vector3 a = Map(w, side[0], w.Z0 - t, -0.04f), b = Map(w, side[1], w.Z1 + t, 0f);
                    sh.Slab(Vector3.Min(a, b), Vector3.Max(a, b), onX);
                }
                if (_shutterMat == null && _trimMat != null) { _shutterMat = new Material(_trimMat) { name = "Shutter" }; if (_shutterMat.HasProperty("_Color")) _shutterMat.color = new Color(0.2f, 0.3f, 0.38f); }
                w.RShutters = MakeObject("WindowShutter_" + w.Index, sh, _shutterMat, true, false);
                StructureLook.Apply(w.RShutters.transform, null);   // the louvres: a picture on the slab
            }
            if (w.MuntinCount > 0)
            {
                var bars = new MeshBuilder();
                foreach (Vector4 b in WindowBars(w)) Box(w, bars, b.x, b.y, b.z, b.w, -0.03f, 0.012f);
                w.RMuntins = MakeObject("WindowMuntin_" + w.Index + "_" + w.MuntinCount, bars, _trimMat, true, false);
            }
        }

        /// <summary>The patterns of bars (the window's panes): how many VERTICAL bars and how many HORIZONTAL ones. 0 plain, 1 two panes, 2 four panes (a cross: the default), 3 six panes (3 x 2), 4 eight panes (4 x 2).</summary>
        private static readonly int[,] MuntinGrid =
        {
            { 0, 0 },   // 0 plain: one pane
            { 1, 0 },   // 1 two panes: one vertical bar
            { 1, 1 },   // 2 four panes: a cross
            { 2, 1 },   // 3 six panes: two vertical bars and a horizontal one
            { 3, 1 },   // 4 eight panes: three vertical bars and a horizontal one
        };
        private static int MuntinPatterns { get { return MuntinGrid.GetLength(0); } }

        private static List<Vector4> Bars(int pattern, float u0, float u1, float za, float zb)
        {
            const float t = 0.015f;
            pattern = Mathf.Clamp(pattern, 0, MuntinPatterns - 1);
            int nv = MuntinGrid[pattern, 0], nh = MuntinGrid[pattern, 1];
            var l = new List<Vector4>();
            for (int k = 1; k <= nv; k++) { float u = u0 + (u1 - u0) * k / (nv + 1); l.Add(new Vector4(u - t, u + t, za, zb)); }          // vertical bars: the full height
            for (int k = 1; k <= nh; k++) { float z = za + (zb - za) * k / (nh + 1); l.Add(new Vector4(u0, u1, z - t, z + t)); }          // horizontal bars: the full width
            return l;
        }

        private GameObject MakeObject(string name, MeshBuilder mb, Material mat, bool shadows, bool collider)
        {
            var go = new GameObject(name);
            go.transform.SetParent(_root, false);
            Mesh mesh = mb.ToMesh(name);
            go.AddComponent<MeshFilter>().sharedMesh = mesh;
            var mr = go.AddComponent<MeshRenderer>();
            if (mat != null) mr.sharedMaterial = mat;
            if (!shadows) mr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            if (collider) go.AddComponent<MeshCollider>().sharedMesh = mesh;
            return go;
        }

        /// <summary>A point in the window's own frame (u along the wall, v up, e inward from the wall's outer face) in the model's space.</summary>
        private static Vector3 Map(Win w, float u, float v, float e)
        {
            float sgn = w.OnX ? w.Outward.z : w.Outward.x;
            float across = w.Outer - sgn * e;
            return w.OnX ? new Vector3(u, v, across) : new Vector3(across, v, u);
        }

        private static void Box(Win w, MeshBuilder mb, float u0, float u1, float v0, float v1, float e0, float e1)
        {
            Vector3 a = Map(w, u0, v0, e0), b = Map(w, u1, v1, e1);
            mb.Box(Vector3.Min(a, b), Vector3.Max(a, b));
        }

        /// <summary>The frame of a window put in or swapped: casing, sill and a lining through the wall round the opening, the sash bar of its type, and the pane.</summary>
        private static void BuildFrame(Win w, MeshBuilder f, MeshBuilder g)
        {
            float u0 = w.U0, u1 = w.U1, v0 = w.Z0, v1 = w.Z1, th = w.Thick, t = 0.07f, kk = 0.02f;
            Box(w, f, u0 - t, u0, v0 - t, v1 + t, -0.05f, 0.03f);
            Box(w, f, u1, u1 + t, v0 - t, v1 + t, -0.05f, 0.03f);
            Box(w, f, u0 - t, u1 + t, v1, v1 + t, -0.05f, 0.03f);
            Box(w, f, u0 - t, u1 + t, v0 - t, v0, -0.05f, 0.03f);
            Box(w, f, u0 - t - 0.04f, u1 + t + 0.04f, v0 - t - 0.04f, v0 - t, -0.09f, 0.03f);          // the sill
            Box(w, f, u0, u0 + kk, v0, v1, 0f, th);                                                    // the lining: both jambs, the sill board and the head board
            Box(w, f, u1 - kk, u1, v0, v1, 0f, th);
            Box(w, f, u0 + kk, u1 - kk, v0, v0 + kk, 0f, th);
            Box(w, f, u0 + kk, u1 - kk, v1 - kk, v1, 0f, th);
            if (w.Type == "building_window_double_hung") Box(w, f, u0, u1, (v0 + v1) * 0.5f - 0.02f, (v0 + v1) * 0.5f + 0.02f, -0.03f, 0.02f);        // the meeting rail of the two sashes
            else if (IsSlider(w.Type)) SashFrames(w, f);                                                                                           // a slider: two sashes, each its own window
            Box(w, g, u0, u1, v0, v1, 0.02f, 0.05f);
        }

        private static bool IsSlider(string type) { return !string.IsNullOrEmpty(type) && ItemBase.TryGetValue(type, out string b) && b == "building_window_slider"; }

        private const float SashOverlap = 0.02f, SashRail = 0.035f;

        /// <summary>The two sashes of a sliding window: the left one in front, the right one behind it, each with its own frame (they meet in the middle with a hand's width of overlap).</summary>
        private static void SashFrames(Win w, MeshBuilder f)
        {
            float um = (w.U0 + w.U1) * 0.5f, v0 = w.Z0, v1 = w.Z1, r = SashRail;
            for (int s = 0; s < 2; s++)
            {
                float a = s == 0 ? w.U0 : um - SashOverlap, b = s == 0 ? um + SashOverlap : w.U1, e0 = s == 0 ? -0.025f : 0.0f, e1 = e0 + 0.025f;
                Box(w, f, a, b, v1 - r, v1, e0, e1);
                Box(w, f, a, b, v0, v0 + r, e0, e1);
                Box(w, f, a, a + r, v0, v1, e0, e1);
                Box(w, f, b - r, b, v0, v1, e0, e1);
            }
        }

        /// <summary>The bars of a window as boxes (u0, u1, v0, v1): the pattern over the whole window, or, for a slider, over each of its two sashes.</summary>
        private static List<Vector4> WindowBars(Win w)
        {
            if (!IsSlider(w.Type)) return Bars(w.MuntinCount, w.U0, w.U1, w.Z0, w.Z1);
            float um = (w.U0 + w.U1) * 0.5f;
            List<Vector4> l = Bars(w.MuntinCount, w.U0 + SashRail, um + SashOverlap - SashRail, w.Z0 + SashRail, w.Z1 - SashRail);
            l.AddRange(Bars(w.MuntinCount, um - SashOverlap + SashRail, w.U1 - SashRail, w.Z0 + SashRail, w.Z1 - SashRail));
            return l;
        }

        private sealed class MeshBuilder
        {
            private readonly List<Vector3> _v = new List<Vector3>(), _n = new List<Vector3>();
            private readonly List<int> _t = new List<int>();
            private readonly List<Vector2> _uv = new List<Vector2>();

            /// <summary>A box whose UVs run 0..1 across it (u along the wall, v up): for a slab with a picture on it (a shutter's louvres).</summary>
            public void Slab(Vector3 mn, Vector3 mx, bool onX)
            {
                int s = _v.Count;
                Box(mn, mx);
                float du = Mathf.Max(1e-4f, onX ? mx.x - mn.x : mx.z - mn.z), dv = Mathf.Max(1e-4f, mx.y - mn.y);
                for (int i = s; i < _v.Count; i++) _uv[i] = new Vector2(((onX ? _v[i].x : _v[i].z) - (onX ? mn.x : mn.z)) / du, (_v[i].y - mn.y) / dv);
            }

            private void Face(Vector3 a, Vector3 b, Vector3 c, Vector3 d, Vector3 n)
            {
                int s = _v.Count;
                _v.Add(a); _v.Add(b); _v.Add(c); _v.Add(d);
                for (int i = 0; i < 4; i++) { _n.Add(n); _uv.Add(Vector2.zero); }
                bool flip = Vector3.Dot(Vector3.Cross(b - a, c - a), n) < 0f;   // (Unity: the first edge crossed with the second points out of a front face)
                if (!flip) { _t.Add(s); _t.Add(s + 1); _t.Add(s + 2); _t.Add(s); _t.Add(s + 2); _t.Add(s + 3); }
                else { _t.Add(s); _t.Add(s + 2); _t.Add(s + 1); _t.Add(s); _t.Add(s + 3); _t.Add(s + 2); }
            }

            public void Box(Vector3 mn, Vector3 mx)
            {
                Vector3 p000 = new Vector3(mn.x, mn.y, mn.z), p100 = new Vector3(mx.x, mn.y, mn.z), p010 = new Vector3(mn.x, mx.y, mn.z), p110 = new Vector3(mx.x, mx.y, mn.z);
                Vector3 p001 = new Vector3(mn.x, mn.y, mx.z), p101 = new Vector3(mx.x, mn.y, mx.z), p011 = new Vector3(mn.x, mx.y, mx.z), p111 = new Vector3(mx.x, mx.y, mx.z);
                Face(p001, p011, p111, p101, Vector3.forward);
                Face(p100, p110, p010, p000, Vector3.back);
                Face(p101, p111, p110, p100, Vector3.right);
                Face(p000, p010, p011, p001, Vector3.left);
                Face(p010, p110, p111, p011, Vector3.up);
                Face(p000, p001, p101, p100, Vector3.down);
            }

            public Mesh ToMesh(string name)
            {
                var m = new Mesh { name = name };
                m.SetVertices(_v);
                m.SetNormals(_n);
                m.SetUVs(0, _uv);
                m.SetTriangles(_t, 0);
                m.RecalculateBounds();
                return m;
            }
        }

        // ------------------------------------------------------------------ cutting the holes

        /// <summary>Re-cuts the walls (one wall, or all when <paramref name="token"/> is null); the colliders take the new mesh only when asked (a collider is costly to rebuild while dragging).</summary>
        private void Rebuild(string token, bool colliders)
        {
            foreach (WallMesh wm in _walls)
            {
                if (token != null && wm.Token != token) continue;
                var holes = new List<Hole>();
                foreach (Win w in Windows)
                    if (w.Token == wm.Token && !w.Removed) holes.Add(new Hole { OnX = w.OnX, U0 = w.U0, U1 = w.U1, Y0 = w.Z0, Y1 = w.Z1 });
                Mesh made = holes.Count == 0 ? wm.Original : Clip(wm.Original, wm.ToRoot, wm.FromRoot, holes);
                if (wm.Clipped != null && wm.Clipped != wm.Original) Destroy(wm.Clipped);
                wm.Clipped = made;
                wm.Filter.sharedMesh = made;
                if (colliders) foreach (MeshCollider c in wm.Colliders) if (c != null) c.sharedMesh = made;
            }
        }

        private void OnDestroy()
        {
            foreach (WallMesh wm in _walls) if (wm.Clipped != null && wm.Clipped != wm.Original) Destroy(wm.Clipped);
        }

        private struct V { public Vector3 P, N; public Vector2 UV; public Color C; }

        private static V Lerp(V a, V b, float t)
        {
            return new V { P = Vector3.Lerp(a.P, b.P, t), N = Vector3.Lerp(a.N, b.N, t).normalized, UV = Vector2.Lerp(a.UV, b.UV, t), C = Color.Lerp(a.C, b.C, t) };
        }

        /// <summary>The part of a polygon on one side of a plane (u or height = plane), or null when nothing is left.</summary>
        private static List<V> Half(List<V> poly, bool onX, bool useY, float plane, bool keepLess)
        {
            var res = new List<V>(poly.Count + 2);
            for (int i = 0; i < poly.Count; i++)
            {
                V cur = poly[i], nxt = poly[(i + 1) % poly.Count];
                float vc = useY ? cur.P.y : (onX ? cur.P.x : cur.P.z), vn = useY ? nxt.P.y : (onX ? nxt.P.x : nxt.P.z);
                float dc = keepLess ? plane - vc : vc - plane, dn = keepLess ? plane - vn : vn - plane;
                if (dc >= 0f) res.Add(cur);
                if ((dc >= 0f) != (dn >= 0f)) res.Add(Lerp(cur, nxt, dc / (dc - dn)));
            }
            return res.Count >= 3 ? res : null;
        }

        /// <summary>A polygon minus a rectangle (in u along the wall and height): up to four convex pieces.</summary>
        private static void Outside(List<V> poly, Hole h, List<List<V>> into)
        {
            List<V> a = Half(poly, h.OnX, false, h.U0, true);          // left of the hole
            List<V> rest = Half(poly, h.OnX, false, h.U0, false);
            List<V> b = rest != null ? Half(rest, h.OnX, false, h.U1, false) : null;   // right of it
            List<V> mid = rest != null ? Half(rest, h.OnX, false, h.U1, true) : null;
            List<V> c = mid != null ? Half(mid, h.OnX, true, h.Y0, true) : null;       // below
            List<V> d = mid != null ? Half(mid, h.OnX, true, h.Y1, false) : null;      // above
            if (a != null) into.Add(a);
            if (b != null) into.Add(b);
            if (c != null) into.Add(c);
            if (d != null) into.Add(d);
        }

        private static Mesh Clip(Mesh src, Matrix4x4 toRoot, Matrix4x4 fromRoot, List<Hole> holes)
        {
            Vector3[] vs = src.vertices, ns = src.normals;
            Vector2[] uvs = src.uv;
            Color[] cs = src.colors;
            bool hasN = ns != null && ns.Length == vs.Length, hasUV = uvs != null && uvs.Length == vs.Length, hasC = cs != null && cs.Length == vs.Length;
            var rp = new Vector3[vs.Length];
            for (int i = 0; i < vs.Length; i++) rp[i] = toRoot.MultiplyPoint3x4(vs[i]);
            var outV = new List<Vector3>(vs);
            var outN = hasN ? new List<Vector3>(ns) : null;
            var outUV = hasUV ? new List<Vector2>(uvs) : null;
            var outC = hasC ? new List<Color>(cs) : null;
            int subs = src.subMeshCount;
            var outT = new List<int>[subs];
            var pieces = new List<List<V>>();
            var next = new List<List<V>>();
            for (int s = 0; s < subs; s++)
            {
                int[] tris = src.GetTriangles(s);
                outT[s] = new List<int>(tris.Length);
                for (int t = 0; t + 2 < tris.Length; t += 3)
                {
                    int i0 = tris[t], i1 = tris[t + 1], i2 = tris[t + 2];
                    Vector3 p0 = rp[i0], p1 = rp[i1], p2 = rp[i2];
                    bool near = false;
                    foreach (Hole h in holes)
                    {
                        float u0 = h.OnX ? p0.x : p0.z, u1 = h.OnX ? p1.x : p1.z, u2 = h.OnX ? p2.x : p2.z;
                        float minU = Mathf.Min(u0, Mathf.Min(u1, u2)), maxU = Mathf.Max(u0, Mathf.Max(u1, u2));
                        float minY = Mathf.Min(p0.y, Mathf.Min(p1.y, p2.y)), maxY = Mathf.Max(p0.y, Mathf.Max(p1.y, p2.y));
                        if (maxU > h.U0 && minU < h.U1 && maxY > h.Y0 && minY < h.Y1) { near = true; break; }
                    }
                    if (!near) { outT[s].Add(i0); outT[s].Add(i1); outT[s].Add(i2); continue; }   // clear of every hole: as it was
                    var poly = new List<V>(3);
                    foreach (int vi in new[] { i0, i1, i2 })
                        poly.Add(new V { P = rp[vi], N = hasN ? ns[vi] : Vector3.up, UV = hasUV ? uvs[vi] : Vector2.zero, C = hasC ? cs[vi] : Color.white });
                    pieces.Clear();
                    pieces.Add(poly);
                    foreach (Hole h in holes)
                    {
                        next.Clear();
                        foreach (List<V> pc in pieces) Outside(pc, h, next);
                        pieces.Clear();
                        pieces.AddRange(next);
                    }
                    foreach (List<V> pc in pieces)
                    {
                        if (pc.Count < 3) continue;
                        if (Vector3.Cross(pc[1].P - pc[0].P, pc[2].P - pc[0].P).sqrMagnitude < 1e-12f && pc.Count == 3) continue;
                        int start = outV.Count;
                        foreach (V v in pc)
                        {
                            outV.Add(fromRoot.MultiplyPoint3x4(v.P));
                            if (hasN) outN.Add(v.N);
                            if (hasUV) outUV.Add(v.UV);
                            if (hasC) outC.Add(v.C);
                        }
                        for (int k = 1; k + 1 < pc.Count; k++) { outT[s].Add(start); outT[s].Add(start + k); outT[s].Add(start + k + 1); }
                    }
                }
            }
            var mesh = new Mesh { name = src.name + "_cut", indexFormat = UnityEngine.Rendering.IndexFormat.UInt32 };
            mesh.SetVertices(outV);
            if (hasN) mesh.SetNormals(outN);
            if (hasUV) mesh.SetUVs(0, outUV);
            if (hasC) mesh.SetColors(outC);
            mesh.subMeshCount = subs;
            for (int s = 0; s < subs; s++) mesh.SetTriangles(outT[s], s, false);
            if (!hasN) mesh.RecalculateNormals();
            mesh.RecalculateBounds();
            return mesh;
        }

        // ------------------------------------------------------------------ working on a window

        /// <summary>
        /// The window of a finished building nearest to a spot on one of its walls (inward = the way out of the wall into the room): where its middle is along the wall (as a world
        /// point on the spot's own height) and the world height of its top edge. For things that hang by a window (curtains). False when no window is within a metre and a half along that wall.
        /// </summary>
        public static bool OpeningNear(ConstructionSite site, Vector3 p, Vector3 inward, out Vector3 centre, out float headY)
        {
            centre = p; headY = 0f;
            StructureWindows sw = site != null ? site.GetComponentInChildren<StructureWindows>() : null;
            if (sw == null || sw._root == null) return false;
            Vector3 lp = sw._root.InverseTransformPoint(p);
            float best = 1.5f;
            foreach (Win w in sw.Windows)
            {
                if (w.Removed || Vector3.Dot(sw._root.TransformDirection(w.Outward), -inward) < 0.9f) continue;   // a window of this wall (it looks out the way the room's wall faces away)
                float along = w.OnX ? lp.x : lp.z;
                float d = Mathf.Abs(along - w.CentreU);
                if (d >= best) continue;
                best = d;
                Vector3 c = lp;
                if (w.OnX) c.x = w.CentreU; else c.z = w.CentreU;
                centre = sw._root.TransformPoint(c);
                headY = sw._root.TransformPoint(new Vector3(c.x, w.Sill + w.H, c.z)).y;
            }
            return best < 1.5f;
        }

        private static Camera Cam() { return Camera.main != null ? Camera.main : FindAnyObjectByType<Camera>(); }

        /// <summary>
        /// A right click on a window (or, with a window in hand, on a bare wall) of a finished building, within reach. With a wrench: Shift picks it up and slides it, Ctrl takes it out.
        /// With a window item: swap it, or put one in. True when the click was dealt with.
        /// </summary>
        public static bool TryRightClick(Camera cam, Vector2 pointer, Transform player)
        {
            if (cam == null) return false;
            string held = ConstructionSite.HeldItem();
            bool wrench = AttachedObject.WrenchInHand(), item = IsWindowItem(held), shutters = IsShutterItem(held);
            if (!wrench && !item && !shutters) return false;
            RaycastHit[] hits = Physics.RaycastAll(cam.ScreenPointToRay(pointer), 1000f, Physics.DefaultRaycastLayers, QueryTriggerInteraction.Ignore);
            System.Array.Sort(hits, (a, b) => a.distance.CompareTo(b.distance));
            foreach (RaycastHit h in hits)
            {
                if (h.collider == null || (player != null && h.collider.transform.IsChildOf(player))) continue;
                StructureWindows sw = h.collider.GetComponentInParent<StructureWindows>();
                if (sw == null) return false;                    // the first thing hit is not part of a finished building
                Win win = sw.WindowOf(h.collider.transform);
                string wallToken = win == null ? sw.WallTokenOf(h.collider.transform) : null;
                if (shutters)   // a pair of shutters in hand: onto the window under the cursor
                {
                    if (win == null && wallToken == null) continue;
                    if (win == null) { ToastNotificationSystem.ShowInfo("Window", "Click a window to fit the shutters."); return true; }
                    if (player != null && Vector2.Distance(new Vector2(player.position.x, player.position.z), new Vector2(h.point.x, h.point.z)) > ReachM) { ToastNotificationSystem.ShowInfo("Window", "Move closer to work on that."); return true; }
                    sw.FitShutters(win);
                    return true;
                }
                if (win == null && wallToken == null && item) continue;              // the floor, the paint, a trim: look on for the wall
                if (win == null && (wallToken == null || !item)) return false;
                if (player != null && Vector2.Distance(new Vector2(player.position.x, player.position.z), new Vector2(h.point.x, h.point.z)) > ReachM)
                {
                    ToastNotificationSystem.ShowInfo("Window", "Move closer to work on that.");
                    return true;
                }
                if (item) { if (win != null) sw.Swap(win, held); else sw.Install(wallToken, h.point, held); return true; }
                Keyboard kb = Keyboard.current;
                bool ctrl = kb != null && kb.ctrlKey.isPressed, shift = kb != null && kb.shiftKey.isPressed;
                if (ctrl) { sw.Remove(win); return true; }                      // Ctrl + right click: take it out
                if (shift) { sw.Begin(win); return true; }                      // Shift + right click: pick it up and slide it (like anything placed: a wrench and Shift)
                if (win.Shutters) { sw.TakeShutters(win); return true; }        // a plain right click with the wrench: the shutters come off
                ToastNotificationSystem.ShowInfo("Window", "Shift + right click moves it, Ctrl + right click takes it out. Click it with another window in hand to swap it.");
                return true;
            }
            return false;
        }

        /// <summary>
        /// A LEFT click with a window item in hand: it goes into the wall under the cursor (a bare wall: put in; a window: swapped), exactly like the right click, and is never set on the ground.
        /// True when the click was dealt with (also when it says why not).
        /// </summary>
        public static bool TryInstallAtCursor(Camera cam, Vector2 pointer, Transform player)
        {
            string held = ConstructionSite.HeldItem();
            if (cam == null || (!IsWindowItem(held) && !IsShutterItem(held))) return false;
            RaycastHit[] hits = Physics.RaycastAll(cam.ScreenPointToRay(pointer), 1000f, Physics.DefaultRaycastLayers, QueryTriggerInteraction.Ignore);
            System.Array.Sort(hits, (a, b) => a.distance.CompareTo(b.distance));
            foreach (RaycastHit h in hits)
            {
                if (h.collider == null || (player != null && h.collider.transform.IsChildOf(player))) continue;
                if (h.collider.GetComponentInParent<PlacedObject>() != null) continue;   // furniture in front of the wall
                StructureWindows sw = h.collider.GetComponentInParent<StructureWindows>();
                if (sw == null) break;
                Win win = sw.WindowOf(h.collider.transform);
                string wallToken = win == null ? sw.WallTokenOf(h.collider.transform) : null;
                if (win == null && wallToken == null) continue;                      // the floor, the paint, a trim: look on for the wall
                if (IsShutterItem(held))
                {
                    if (win == null) { ToastNotificationSystem.ShowInfo("Window", "Click a window to fit the shutters."); return true; }
                    if (player != null && Vector2.Distance(new Vector2(player.position.x, player.position.z), new Vector2(h.point.x, h.point.z)) > ReachM) { ToastNotificationSystem.ShowInfo("Window", "Move closer to work on that."); return true; }
                    sw.FitShutters(win);
                    return true;
                }
                if (player != null && Vector2.Distance(new Vector2(player.position.x, player.position.z), new Vector2(h.point.x, h.point.z)) > ReachM)
                {
                    ToastNotificationSystem.ShowInfo("Window", "Move closer to work on that.");
                    return true;
                }
                if (win != null) sw.Swap(win, held); else sw.Install(wallToken, h.point, held);
                return true;
            }
            ToastNotificationSystem.ShowInfo("Window", "Click a wall of a finished building to put the window in.");
            return true;
        }

        private Win WindowOf(Transform t)
        {
            foreach (Win w in Windows)
            {
                if (w.Removed) continue;
                if ((w.BakedFrame != null && t.IsChildOf(w.BakedFrame)) || (w.BakedGlass != null && t.IsChildOf(w.BakedGlass))
                    || (w.RFrame != null && t.IsChildOf(w.RFrame.transform)) || (w.RGlass != null && t.IsChildOf(w.RGlass.transform))
                    || (w.RMuntins != null && t.IsChildOf(w.RMuntins.transform))) return w;
            }
            return null;
        }

        /// <summary>The wall (token) a collider belongs to, or null.</summary>
        private string WallTokenOf(Transform t)
        {
            for (; t != null && t != _root.parent; t = t.parent)
                if (t.name.StartsWith("Wall_"))
                {
                    string n = t.name.Substring(5);
                    string suffix = n.Contains("@") ? "@" + n.Split('@')[1] : "";
                    string b = n.Split('@')[0].ToLowerInvariant();
                    string token = b + suffix;
                    return _wallRange.ContainsKey(token) ? token : null;
                }
            return null;
        }

        private static string ItemForWidth(float width)
        {
            string best = "building_window_double_hung";
            float bestD = float.MaxValue;
            foreach (KeyValuePair<string, Vector2> kv in BaseTypes) { float d = Mathf.Abs(kv.Value.x - width); if (d < bestD) { bestD = d; best = kv.Key; } }
            return best;
        }

        /// <summary>The window item this window is: its type (by its width when it came with the building) in its own pattern of bars.</summary>
        private static string ItemOf(Win w)
        {
            string baseId = !string.IsNullOrEmpty(w.Type) && ItemBase.TryGetValue(w.Type, out string b) ? b : ItemForWidth(w.W);
            return baseId + PatternSuffix[Mathf.Clamp(w.MuntinCount, 0, PatternSuffix.Length - 1)];
        }

        private static bool Give(string itemId)
        {
            HudState hud = HudState.Active;
            if (hud == null) return false;
            hud.EnsureToolbarSlots();
            if (hud.AddItemToToolbar(itemId, 1, HudBindings.GetMaxStack(itemId)) <= 0) { ToastNotificationSystem.ShowWarning("Toolbar full", "No room in the toolbar for the window."); return false; }
            HudBindings.Instance?.RefreshToolbar();
            return true;
        }

        /// <summary>The shutters in hand go onto this window (it must have room for them along its wall).</summary>
        private void FitShutters(Win w)
        {
            if (w == null || w.Removed) return;
            if (w.Shutters) { ToastNotificationSystem.ShowInfo("Window", "It has shutters already."); return; }
            if (_wallRange.TryGetValue(w.Token, out Vector2 range) && (w.U0 - 0.49f < range.x || w.U1 + 0.49f > range.y)) { ToastNotificationSystem.ShowInfo("Window", "There is no room for shutters beside that window."); return; }
            HudState hud = HudState.Active;
            if (hud == null || !hud.ConsumeFromSelectedSlot(1)) return;
            HudBindings.Instance?.RefreshToolbar();
            w.Shutters = true;
            Refresh(w);
            Store();
        }

        /// <summary>A wrench and a right click: the shutters come off into the toolbar.</summary>
        private void TakeShutters(Win w)
        {
            if (w == null || !w.Shutters || !Give(ShutterItem)) return;
            w.Shutters = false;
            Refresh(w);
            Store();
        }

        private void Remove(Win w)
        {
            if (w == null || w.Removed) return;
            if (!Give(ItemOf(w))) return;
            if (w.Shutters && Give(ShutterItem)) w.Shutters = false;       // the shutters come off with it
            w.Removed = true;
            Refresh(w);
            Rebuild(w.Token, true);
            Store();
        }

        /// <summary>The held window replaces this one (same sill, same place as near as it fits); the old one goes into the toolbar.</summary>
        private void Swap(Win w, string itemId)
        {
            HudState hud = HudState.Active;
            if (hud == null || w.Removed) return;
            string oldItem = ItemOf(w);
            if (itemId == oldItem) return;      // the same window
            Vector2 t = Types[itemId];
            float width = t.x;
            float height = Mathf.Min(t.y, _headLimit - w.Sill);
            if (height < MinHeightM) { ToastNotificationSystem.ShowInfo("Window", "That one is too tall for this wall."); return; }
            float centre = FitCentre(w.Token, w.CentreU, width, w, out bool ok);
            if (!ok) { ToastNotificationSystem.ShowInfo("Window", "There is no room for that window here."); return; }
            if (!Give(oldItem)) return;
            hud.ConsumeFromSelectedSlot(1);
            HudBindings.Instance?.RefreshToolbar();
            w.Type = itemId;
            w.MuntinCount = ItemPattern[itemId];
            w.CentreU = centre;
            w.W = width; w.H = height;
            Refresh(w);
            Rebuild(w.Token, true);
            Store();
        }

        /// <summary>Puts a window of the held type in a bare wall where the cursor is, at the sill of the building's windows.</summary>
        private void Install(string token, Vector3 world, string itemId)
        {
            HudState hud = HudState.Active;
            if (hud == null) return;
            float sill = float.MaxValue;
            foreach (Win o in Windows) sill = Mathf.Min(sill, o.Sill);
            if (sill == float.MaxValue) sill = 1.05f;
            float head = _headLimit > 0.5f ? _headLimit : 2.2f;
            Vector2 t = Types[itemId];
            float height = Mathf.Min(t.y, head - sill);
            if (height < MinHeightM) return;
            bool onX = token.Split('@')[0] == "front" || token.Split('@')[0] == "back";
            Vector3 local = _root.InverseTransformPoint(world);
            float want = onX ? local.x : local.z;
            var w = new Win { Index = _nextIndex++, Baked = false };
            SetWall(w, token);
            foreach (Win o in Windows) if (o.Token == token && o.Thick > 0.05f) { w.Outer = o.Outer; w.Thick = o.Thick; break; }
            if (w.Thick < 0.05f)   // a wall with no window yet: its thickness and outer face are measured from its own mesh, round the spot
            {
                w.DefU0 = want - t.x * 0.5f; w.DefU1 = want + t.x * 0.5f; w.DefZ0 = sill; w.DefZ1 = sill + height;
                Measure(w);
            }
            w.Sill = sill; w.W = t.x; w.H = height; w.Type = itemId; w.MuntinCount = ItemPattern[itemId];
            float centre = FitCentre(token, want, t.x, null, out bool ok);
            if (!ok || Mathf.Abs(centre - want) > 0.6f) { ToastNotificationSystem.ShowInfo("Window", "There is no room for a window there."); return; }
            w.CentreU = centre;
            hud.ConsumeFromSelectedSlot(1);
            HudBindings.Instance?.RefreshToolbar();
            Windows.Add(w);
            Refresh(w);
            Rebuild(token, true);
            Store();
        }

        private void Begin(Win w) { _moving = w; _startCentre = w.CentreU; }

        private void Update()
        {
            if (_moving == null) return;
            Mouse mouse = Mouse.current;
            Keyboard kb = Keyboard.current;
            if (mouse == null) { _moving = null; return; }
            Win w = _moving;
            if ((kb != null && kb.escapeKey.wasPressedThisFrame) || mouse.rightButton.wasPressedThisFrame)
            {
                w.CentreU = _startCentre;                          // put back where it was
                Refresh(w);
                Rebuild(w.Token, true);
                _moving = null;
                Store();
                return;
            }
            if (mouse.leftButton.wasPressedThisFrame)
            {
                Rebuild(w.Token, true);                            // set down: the wall's colliders take the hole too
                _moving = null;
                Store();
                return;
            }
            Camera cam = Cam();
            if (cam == null) return;
            Ray ray = cam.ScreenPointToRay(mouse.position.ReadValue());
            var plane = new Plane(_root.TransformDirection(w.Outward), _root.TransformPoint(w.OnX ? new Vector3(w.CentreU, (w.Z0 + w.Z1) * 0.5f, w.Outer) : new Vector3(w.Outer, (w.Z0 + w.Z1) * 0.5f, w.CentreU)));
            if (!plane.Raycast(ray, out float enter)) return;
            Vector3 local = _root.InverseTransformPoint(ray.GetPoint(enter));
            float want = w.OnX ? local.x : local.z;
            float centre = FitCentre(w.Token, want, w.W, w, out bool ok);
            if (!ok || Mathf.Abs(centre - w.CentreU) < 0.002f) return;
            w.CentreU = centre;
            Refresh(w);
            Rebuild(w.Token, false);
        }

        /// <summary>The nearest centre to <paramref name="want"/> where a window of this width fits on the wall: off the corners, off the doors and off the other windows (<paramref name="self"/> aside).</summary>
        private float FitCentre(string token, float want, float width, Win self, out bool ok)
        {
            ok = false;
            float hw = width * 0.5f;
            float lo = float.NegativeInfinity, hi = float.PositiveInfinity;
            if (_wallRange.TryGetValue(token, out Vector2 range)) { lo = range.x + CornerMarginM + hw; hi = range.y - CornerMarginM - hw; }
            if (hi < lo) return want;
            bool onX = token.Split('@')[0] == "front" || token.Split('@')[0] == "back";
            var forbidden = new List<Vector2>();                // centres a window may not take
            float across = 0f;
            int n = 0;
            foreach (Win o in Windows)
            {
                if (o.Token != token) continue;
                across += o.Outer; n++;
                if (o == self || o.Removed) continue;
                forbidden.Add(new Vector2(o.U0 - NeighbourMarginM - hw, o.U1 + NeighbourMarginM + hw));
            }
            if (n > 0) across /= n;
            foreach (Renderer r in _root.GetComponentsInChildren<Renderer>(true))
            {
                if (!(r.name.StartsWith("Door") || r.name.StartsWith("RollLeaf")) || !r.gameObject.activeInHierarchy) continue;
                Bounds b = r.bounds;
                Vector3 c = _root.InverseTransformPoint(b.center);
                Vector3 e = _root.InverseTransformVector(b.extents);
                float cAcross = onX ? c.z : c.x;
                if (Mathf.Abs(cAcross - across) > 0.8f) continue;       // a door on another wall
                float cu = onX ? c.x : c.z, eu = Mathf.Abs(onX ? e.x : e.z);
                forbidden.Add(new Vector2(cu - eu - DoorMarginM - hw, cu + eu + DoorMarginM + hw));
            }
            var cand = new List<float> { Mathf.Clamp(want, lo, hi), lo, hi };
            foreach (Vector2 f in forbidden) { cand.Add(f.x); cand.Add(f.y); }
            float best = want, bestD = float.MaxValue;
            foreach (float c in cand)
            {
                if (c < lo - 1e-4f || c > hi + 1e-4f) continue;
                bool free = true;
                foreach (Vector2 f in forbidden) if (c > f.x + 1e-4f && c < f.y - 1e-4f) { free = false; break; }
                if (!free) continue;
                float d = Mathf.Abs(c - want);
                if (d < bestD) { bestD = d; best = c; ok = true; }
            }
            return best;
        }
    }
}
