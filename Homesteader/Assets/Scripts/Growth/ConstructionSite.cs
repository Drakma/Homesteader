using System.Collections.Generic;
using Homesteader.Generation;
using Homesteader.Modding;
using Homesteader.UI;
using UnityEngine;

namespace Homesteader.Growth
{
    /// <summary>
    /// A structure under construction. Placing a structure (a structure item such as small_cabin, barn, farmhouse) makes a dirt
    /// area the size of its foundation. Materials are PLACED within the yard (the footprint plus <see cref="YardM"/> metres);
    /// hovering the site lists what is there and what a stage still needs, tools included. When everything is there, a right
    /// click on the site builds the stage: the materials are used up, the structure grows to the next stage (foundation,
    /// framing, walls, complete) and the next stage's list takes over. Tools are never used up: each tool group needs ANY ONE
    /// of its tools, either in the toolbar or placed in the yard.
    ///
    /// Stage data (recipe, tools, size, model) comes from the kit: the structure's stage manifests, exported by
    /// tools/generate_unity_asset_catalog.py as construction_stages. A stage shows its own model when it has one, otherwise a
    /// plain stand-in built in code from the stage's size. Saved by GameSave.sites.
    /// </summary>
    public sealed class ConstructionSite : MonoBehaviour
    {
        /// <summary>How far outside the foundation materials and tools still count.</summary>
        public const float YardM = 5f;   // the footprint plus one more grid tile (it was 4 m)

        public static readonly List<ConstructionSite> All = new List<ConstructionSite>();

        public string StructureId { get; private set; }
        /// <summary>Stages built so far: 0 = only the dirt area, 4 = finished.</summary>
        public int Stage { get; private set; }
        public float YawDeg { get; private set; }

        private List<ConstructionStageData> _stages;
        private Vector2 _foot;                       // foundation width (local x) and depth (local z), metres
        private float _drop;                         // how far the ground falls away below the foundation's top edge (the footing fills it)
        private GameObject _patch;
        private GameObject _visual;
        private bool _modelPending;   // a stage model is still loading into the site

        /// <summary>True while any building's model is still being loaded or put up (a load screen waits for this to be false).</summary>
        public static bool AnyModelPending
        {
            get
            {
                foreach (ConstructionSite s in All) if (s != null && s._modelPending) return true;
                return false;
            }
        }
        private int _visualStage = -1;
        private LineRenderer _ring;
        private float _nextEval;
        private List<LineStatus> _status;
        private List<ToolStatus> _tools;

        // ------------------------------------------------------------------ which way is the front

        // The stage models carry an empty named FrontMarker just in front of the door; its direction from the model's origin (on the
        // ground plane, in the model's own space) is the front. Every stage model of every structure shares the convention, so it is
        // learned from the first marker seen. Until one is seen the guess is local +Z.
        private static Vector3 s_front = Vector3.forward;
        private static bool s_frontKnown;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
        private static void ResetFront() { s_front = Vector3.forward; s_frontKnown = false; }

        public static Vector3 FrontLocal => s_front;
        public static bool FrontKnown => s_frontKnown;

        /// <summary>Reads the front from a loaded model (or its template) if it has a FrontMarker.</summary>
        public static void LearnFront(GameObject model)
        {
            if (model == null || s_frontKnown) return;
            foreach (Transform t in model.GetComponentsInChildren<Transform>(true))
            {
                if (t.name != "FrontMarker") continue;
                Vector3 d = model.transform.InverseTransformPoint(t.position);
                d.y = 0f;
                if (d.sqrMagnitude < 0.0001f) return;
                s_front = d.normalized;
                s_frontKnown = true;
                return;
            }
        }

        /// <summary>
        /// A flat amber arrow lying on the ground in front of a foundation, pointing away from it: the FRONT (the door side). Built in
        /// the local space of <paramref name="parent"/>, whose origin is the middle of the foundation.
        /// </summary>
        public static GameObject MakeFrontArrow(Transform parent, Vector2 footprint, Vector3 front)
        {
            Vector3 f = new Vector3(front.x, 0f, front.z).normalized;
            Vector3 side = new Vector3(f.z, 0f, -f.x);
            // distance from the middle to the edge along the front
            float half = Mathf.Min(Mathf.Abs(f.x) > 0.001f ? footprint.x * 0.5f / Mathf.Abs(f.x) : float.MaxValue,
                                   Mathf.Abs(f.z) > 0.001f ? footprint.y * 0.5f / Mathf.Abs(f.z) : float.MaxValue);
            Vector3 baseC = f * (half + 0.5f);
            const float length = 1.6f, width = 1.3f, shaft = 0.35f;
            float y = 0.14f;
            // an arrow: a shaft and a head, in one flat mesh
            Vector3[] v =
            {
                baseC - side * shaft * 0.5f, baseC + side * shaft * 0.5f,
                baseC + f * length * 0.5f + side * shaft * 0.5f, baseC + f * length * 0.5f - side * shaft * 0.5f,
                baseC + f * length * 0.5f - side * width * 0.5f, baseC + f * length * 0.5f + side * width * 0.5f,
                baseC + f * length,
            };
            for (int i = 0; i < v.Length; i++) v[i].y = y;
            var mesh = new Mesh { name = "FrontArrow" };
            mesh.vertices = v;
            mesh.triangles = new[] { 0, 3, 2, 0, 2, 1, 4, 6, 5 };   // clockwise seen from above (Unity's front face)
            mesh.RecalculateNormals();
            var go = new GameObject("FrontArrow");
            go.transform.SetParent(parent, false);
            go.AddComponent<MeshFilter>().sharedMesh = mesh;
            var mr = go.AddComponent<MeshRenderer>();
            var mat = new Material(Shader.Find("Universal Render Pipeline/Unlit")) { hideFlags = HideFlags.DontSave };
            mat.SetColor("_BaseColor", new Color(1f, 0.72f, 0.2f, 1f));
            mat.SetFloat("_Cull", 0f);   // visible from either side whatever the winding
            mr.sharedMaterial = mat;
            mr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            return go;
        }

        // ------------------------------------------------------------------ what a structure is

        public static List<ConstructionStageData> StagesOf(string itemId)
        {
            AssetCatalogItem info = HudBindings.GetCatalogItem(itemId);
            if (info == null || info.construction_stages == null || info.construction_stages.Count == 0) return null;
            foreach (ConstructionStageData st in info.construction_stages)   // the JSON may leave a list out
            {
                if (st.recipe == null) st.recipe = new List<ConstructionLine>();
                if (st.tool_groups == null) st.tool_groups = new List<ConstructionToolGroup>();
                foreach (ConstructionToolGroup g in st.tool_groups) if (g.tools == null) g.tools = new List<string>();
            }
            return info.construction_stages;
        }

        public static bool IsStructure(string itemId) { return StagesOf(itemId) != null; }

        /// <summary>The foundation's width and depth.</summary>
        public static Vector2 FootprintOf(string itemId)
        {
            List<ConstructionStageData> s = StagesOf(itemId);
            return s != null ? new Vector2(Mathf.Max(1f, s[0].width), Mathf.Max(1f, s[0].depth)) : new Vector2(2f, 2f);
        }

        public static ConstructionSite Create(string structureId, Vector3 position, float yawDeg, int stage = 0)
        {
            List<ConstructionStageData> stages = StagesOf(structureId);
            if (stages == null) return null;
            var go = new GameObject("ConstructionSite_" + structureId);
            position = TerrainHeightDetector.PlaceOnGround(position);
            go.transform.SetPositionAndRotation(position, Quaternion.Euler(0f, yawDeg, 0f));
            var site = go.AddComponent<ConstructionSite>();
            site.StructureId = structureId;
            WireNode.Attach(go, structureId);   // a wind turbine can be wired (its manifest's wire_role)
            site.YawDeg = yawDeg;
            site._stages = stages;
            site._foot = FootprintOf(structureId);
            site.Stage = Mathf.Clamp(stage, 0, stages.Count);
            site.FitToGround();
            site.BuildPatch();
            site.StartCoroutine(site.ShowFrontArrow());
            site.RefreshVisual();
            return site;
        }

        private void OnEnable() { All.Add(this); }
        private void OnDisable() { All.Remove(this); }

        // ------------------------------------------------------------------ geometry

        /// <summary>Distance outside the foundation rectangle (0 when inside), measured on the ground plane.</summary>
        public float DistanceOutside(Vector3 world)
        {
            Vector3 local = Quaternion.Euler(0f, -YawDeg, 0f) * (world - transform.position);
            float dx = Mathf.Max(0f, Mathf.Abs(local.x) - _foot.x * 0.5f);
            float dz = Mathf.Max(0f, Mathf.Abs(local.z) - _foot.y * 0.5f);
            return Mathf.Sqrt(dx * dx + dz * dz);
        }

        public bool InYard(Vector3 world) { return DistanceOutside(world) <= YardM; }

        /// <summary>
        /// Moves a point that lies within a building's footprint (plus a margin; buildings with a foundation down) out through the nearest side, so
        /// what falls from a felled tree never lands inside a structure. Other points come back unchanged.
        /// </summary>
        public static Vector3 KeepOut(Vector3 world, float margin)
        {
            foreach (ConstructionSite s in All)
            {
                if (s == null || s.Stage < 1) continue;
                Vector3 local = Quaternion.Euler(0f, -s.YawDeg, 0f) * (world - s.transform.position);
                float hx = s._foot.x * 0.5f + margin, hz = s._foot.y * 0.5f + margin;
                if (Mathf.Abs(local.x) >= hx || Mathf.Abs(local.z) >= hz) continue;
                if (hx - Mathf.Abs(local.x) < hz - Mathf.Abs(local.z)) local.x = (local.x < 0f ? -1f : 1f) * hx;
                else local.z = (local.z < 0f ? -1f : 1f) * hz;
                Vector3 pushed = s.transform.position + Quaternion.Euler(0f, s.YawDeg, 0f) * local;
                pushed.y = world.y;
                world = pushed;
            }
            return world;
        }

        public Vector2 Footprint => _foot;

        /// <summary>The model of the current stage (null before one is built or while it loads).</summary>
        public Transform VisualRoot => _visual != null ? _visual.transform : null;

        /// <summary>True when a point is within the building's footprint (on the ground plane).</summary>
        private Rect _wallRect;               // x, z (as x, y) of the walls in the building's own space
        private Transform _wallRectFor;

        /// <summary>
        /// The rectangle the WALLS of a finished building enclose (in its own space, x and z as x and y), from the walls' parts of the model. The
        /// footprint is not that: a porch is inside the footprint but outside the walls, so "inside the building" for mounting a light or a breaker
        /// box is measured against this.
        /// </summary>
        public Rect WallRect()
        {
            Transform root = VisualRoot;
            if (root != null && _wallRectFor == root) return _wallRect;
            Quaternion inv = Quaternion.Inverse(transform.rotation);
            // x from every wall part; z from the side walls (Wall_Left, Wall_Right) when there are some: on a house with a porch the FRONT wall part
            // includes a gable that stands at the porch's edge, so its extent would put the porch inside the walls
            float x0 = float.MaxValue, x1 = float.MinValue, zAll0 = float.MaxValue, zAll1 = float.MinValue, zSide0 = float.MaxValue, zSide1 = float.MinValue;
            bool any = false, side = false;
            if (root != null)
                foreach (Renderer r in root.GetComponentsInChildren<Renderer>(true))
                {
                    bool wall = false, sideWall = false;
                    for (Transform t = r.transform; t != null && t != root.parent; t = t.parent)
                        if (t.name.StartsWith("Wall_")) { wall = true; sideWall = t.name == "Wall_Left" || t.name == "Wall_Right"; break; }
                    if (!wall) continue;
                    Bounds b = r.bounds;
                    for (int i = 0; i < 8; i++)
                    {
                        Vector3 c = b.center + Vector3.Scale(b.extents, new Vector3((i & 1) == 0 ? -1 : 1, (i & 2) == 0 ? -1 : 1, (i & 4) == 0 ? -1 : 1));
                        Vector3 l = inv * (c - transform.position);
                        x0 = Mathf.Min(x0, l.x); x1 = Mathf.Max(x1, l.x);
                        zAll0 = Mathf.Min(zAll0, l.z); zAll1 = Mathf.Max(zAll1, l.z);
                        if (sideWall) { zSide0 = Mathf.Min(zSide0, l.z); zSide1 = Mathf.Max(zSide1, l.z); side = true; }
                        any = true;
                    }
                }
            Rect rect = !any ? new Rect(-_foot.x * 0.5f, -_foot.y * 0.5f, _foot.x, _foot.y)
                             : side ? Rect.MinMaxRect(x0, zSide0, x1, zSide1) : Rect.MinMaxRect(x0, zAll0, x1, zAll1);
            if (root != null && any) { _wallRectFor = root; _wallRect = rect; }
            return rect;
        }

        /// <summary>True once the walls of the finished model are known (WallRect is measured from them, not from the footprint).</summary>
        public bool WallsKnown { get { Rect unused = WallRect(); return VisualRoot != null && _wallRectFor == VisualRoot; } }

        /// <summary>True when a world point is inside the walls (not on a porch, not outside).</summary>
        public bool IsInsideWalls(Vector3 world)
        {
            Rect r = WallRect();
            Vector3 l = Quaternion.Inverse(transform.rotation) * (world - transform.position);
            return l.x >= r.xMin && l.x <= r.xMax && l.z >= r.yMin && l.z <= r.yMax;
        }

        private float _ceilingY;
        private Transform _ceilingFor;

        /// <summary>
        /// The height (world y) of the ceiling inside a finished building, for ceiling lights: the plates the roof rests on, found from the tops of the
        /// walls of the model (an eave wall ends 0.45 m above the ceiling). Kept for as long as the model stands.
        /// </summary>
        public float CeilingY()
        {
            Transform root = VisualRoot;
            if (root != null && _ceilingFor == root) return _ceilingY;
            float floor = transform.position.y;
            float top = float.MaxValue, tallest = float.MinValue, roofLow = float.MaxValue;
            if (root != null)
                foreach (Renderer r in root.GetComponentsInChildren<Renderer>(true))
                {
                    bool wall = false, roof = false;
                    for (Transform t = r.transform; t != null && t != root.parent; t = t.parent)
                    {
                        if (t.name.StartsWith("Wall_")) { wall = true; break; }
                        if (t.name == "Roof") { roof = true; break; }
                    }
                    if (roof) roofLow = Mathf.Min(roofLow, r.bounds.min.y);   // the lowest point of the roof: the eave
                    if (!wall) continue;
                    float wallTop = r.bounds.max.y;
                    tallest = Mathf.Max(tallest, wallTop);
                    if (wallTop >= floor + 2.3f) top = Mathf.Min(top, wallTop);   // the eave walls: a low piece (a half wall, a sill, a rail) is not the ceiling
                }
            if (top == float.MaxValue && tallest > float.MinValue) top = tallest;
            // the eave walls (blocking up to the rafters) end 0.31 m above the underside of the ceiling joists, which is the ceiling a light hangs from (measured in the built models)
            // the ceiling is just under the roof's eave (measured in the built models: 2.5 to 3.6 m above the floor); with no roof, from the wall tops
            float y = roofLow != float.MaxValue ? Mathf.Clamp(roofLow - 0.06f, floor + 2.4f, floor + 4.5f)
                    : top == float.MaxValue ? floor + 2.9f : Mathf.Clamp(top - 0.31f, floor + 2.4f, floor + 4.5f);
            if (root != null && (top != float.MaxValue || roofLow != float.MaxValue)) { _ceilingFor = root; _ceilingY = y; }   // (not kept while the model is still loading)
            return y;
        }

        public bool IsInside(Vector3 world)
        {
            Vector3 local = Quaternion.Euler(0f, -YawDeg, 0f) * (world - transform.position);
            return Mathf.Abs(local.x) <= _foot.x * 0.5f && Mathf.Abs(local.z) <= _foot.y * 0.5f;
        }

        /// <summary>
        /// The structure stands on the HIGHEST ground under its footprint, and a footing reaches down to the lowest, so no side is
        /// buried and no side has a gap under it.
        /// </summary>
        private void FitToGround()
        {
            float maxY = float.MinValue, minY = float.MaxValue;
            const float step = 0.5f;
            int nx = Mathf.Max(2, Mathf.CeilToInt(_foot.x / step)), nz = Mathf.Max(2, Mathf.CeilToInt(_foot.y / step));
            for (int iz = 0; iz <= nz; iz++)
                for (int ix = 0; ix <= nx; ix++)
                {
                    Vector3 world = transform.TransformPoint(new Vector3(-_foot.x * 0.5f + _foot.x * ix / nx, 0f, -_foot.y * 0.5f + _foot.y * iz / nz));
                    float y = TerrainHeightDetector.GetGroundY(world);
                    maxY = Mathf.Max(maxY, y);
                    minY = Mathf.Min(minY, y);
                }
            Vector3 p = transform.position;
            transform.position = new Vector3(p.x, maxY, p.z);
            _level = maxY;
            _drop = Mathf.Max(0f, maxY - minY);
        }

        /// <summary>Concrete from the foundation's underside down to the lowest ground, with a collider: it fills the gap on the low side.</summary>
        private void AddFooting(Transform parent)
        {
            if (_drop <= 0.01f || Stilted) return;
            Box(parent, "Footing", new Vector3(0f, -_drop, 0f), new Vector3(_foot.x, _drop + 0.02f, _foot.y), new Color(0.58f, 0.58f, 0.56f), true);
        }

        /// <summary>A model without colliders gets one box around its meshes, so the cursor and the player meet it.</summary>
        private void EnsureCollider(GameObject model)
        {
            if (model.GetComponentsInChildren<Collider>(true).Length > 0) return;
            bool any = false;
            Vector3 mn = default, mx = default;
            foreach (MeshFilter mf in model.GetComponentsInChildren<MeshFilter>())
            {
                if (mf.sharedMesh == null) continue;
                Bounds mb = mf.sharedMesh.bounds;
                Vector3 e = mb.extents, c = mb.center;
                for (int i = 0; i < 8; i++)
                {
                    Vector3 corner = c + new Vector3((i & 1) == 0 ? -e.x : e.x, (i & 2) == 0 ? -e.y : e.y, (i & 4) == 0 ? -e.z : e.z);
                    Vector3 l = transform.InverseTransformPoint(mf.transform.TransformPoint(corner));
                    if (!any) { mn = mx = l; any = true; }
                    else { mn = Vector3.Min(mn, l); mx = Vector3.Max(mx, l); }
                }
            }
            if (!any) return;
            var box = new GameObject("Bounds");
            box.transform.SetParent(model.transform.parent, false);
            var bc = box.AddComponent<BoxCollider>();
            bc.center = (mn + mx) * 0.5f;
            bc.size = mx - mn;
        }

        private GameObject _arrow;

        /// <summary>Marks the front on the dirt area. It waits for the foundation model to load (that is where the front is learned).</summary>
        private System.Collections.IEnumerator ShowFrontArrow()
        {
            if (!s_frontKnown && _stages != null && _stages.Count > 0 && ItemRegistry.TryGet(_stages[0].item_id, out ItemRegistry.ItemInfo info) && info.Prefab != null)
            {
                GlbTemplate glb = info.Prefab.GetComponent<GlbTemplate>();
                float until = Time.realtimeSinceStartup + 10f;
                while (glb != null && !glb.Ready && !glb.Failed && Time.realtimeSinceStartup < until) { glb.EnsureLoading(); yield return null; }
                LearnFront(info.Prefab);
            }
            if (Stage == 0 && _arrow == null) _arrow = MakeFrontArrow(transform, _foot, s_front);
        }

        private void BuildPatch()
        {
            _patch = new GameObject("DirtArea");
            _patch.transform.SetParent(transform, false);
            const float step = 0.5f;
            int nx = Mathf.Max(2, Mathf.CeilToInt(_foot.x / step)), nz = Mathf.Max(2, Mathf.CeilToInt(_foot.y / step));
            var verts = new Vector3[(nx + 1) * (nz + 1)];
            var uvs = new Vector2[verts.Length];
            for (int iz = 0; iz <= nz; iz++)
                for (int ix = 0; ix <= nx; ix++)
                {
                    float lx = -_foot.x * 0.5f + _foot.x * ix / nx, lz = -_foot.y * 0.5f + _foot.y * iz / nz;
                    Vector3 world = transform.TransformPoint(new Vector3(lx, 0f, lz));
                    float y = TerrainHeightDetector.GetGroundY(world) - transform.position.y + 0.04f;
                    verts[iz * (nx + 1) + ix] = new Vector3(lx, y, lz);
                    uvs[iz * (nx + 1) + ix] = new Vector2(lx * 0.6f, lz * 0.6f);
                }
            var tris = new List<int>();
            for (int iz = 0; iz < nz; iz++)
                for (int ix = 0; ix < nx; ix++)
                {
                    int a = iz * (nx + 1) + ix, b = a + 1, c = a + nx + 1, d = c + 1;
                    tris.AddRange(new[] { a, c, b, b, c, d });
                }
            var mesh = new Mesh { name = "DirtArea" };
            mesh.vertices = verts;
            mesh.uv = uvs;
            mesh.triangles = tris.ToArray();
            mesh.RecalculateNormals();
            mesh.RecalculateBounds();
            _patch.AddComponent<MeshFilter>().sharedMesh = mesh;
            var mr = _patch.AddComponent<MeshRenderer>();
            mr.sharedMaterial = DirtMaterial();
            mr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            _patch.AddComponent<MeshCollider>().sharedMesh = mesh;
        }

        private static Material _dirt;
        private static Texture2D _dirtTex;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
        private static void ResetStatics() { _dirt = null; _dirtTex = null; }

        private static Material DirtMaterial()
        {
            // The texture is generated, so a scene load can unload it while this material (kept alive by DontSave) lives on, and the
            // dirt then rendered plain white. Keep both alive, and rebuild if the texture is ever gone.
            if (_dirt != null && _dirtTex != null) return _dirt;
            Shader lit = Shader.Find("Universal Render Pipeline/Lit");
            _dirt = new Material(lit) { name = "ConstructionDirt", hideFlags = HideFlags.DontSave };
            const int n = 64;
            var tex = new Texture2D(n, n, TextureFormat.RGBA32, true) { wrapMode = TextureWrapMode.Repeat, filterMode = FilterMode.Bilinear, hideFlags = HideFlags.DontSave };
            _dirtTex = tex;
            var rng = new System.Random(4711);
            for (int y = 0; y < n; y++)
                for (int x = 0; x < n; x++)
                {
                    float v = 0.82f + (float)rng.NextDouble() * 0.3f;
                    if (rng.NextDouble() < 0.05) v *= 0.7f;   // stones and clods
                    tex.SetPixel(x, y, new Color(0.38f * v, 0.26f * v, 0.16f * v, 1f));
                }
            tex.Apply();
            _dirt.SetTexture("_BaseMap", tex);
            _dirt.SetColor("_BaseColor", Color.white);
            _dirt.SetFloat("_Smoothness", 0.04f);
            return _dirt;
        }

        // ------------------------------------------------------------------ what a stage needs

        /// <summary>
        /// How one node of the recipe stands. A leaf is a plain line (Have against its quantity). A section has Children: mode "all" needs every
        /// child, mode "any" needs the Chosen child (the first complete one, else the nearest to complete). An inactive section (its "if" does not
        /// hold) needs nothing.
        /// </summary>
        public sealed class LineStatus
        {
            public ConstructionLine Line;
            public List<LineStatus> Children;
            public bool Any;
            public int Chosen;
            public bool Active = true;
            /// <summary>An "any" section the player has not chosen an option of yet: nothing is evaluated under it, it is a question.</summary>
            public bool Unresolved;
            public string Path;            // where the section sits in the recipe ("2.0"): what a choice is stored under
            public int PickedIndex = -1;   // the option chosen (an index into the section's items)
            public bool IsSection => Children != null;
            public float Have;
            /// <summary>What this line needs here: its quantity, plus per_depth_m x the depth on a well.</summary>
            public float Need;
            public float Needed => Need > 0f ? Need : (Line != null ? Line.quantity : 0f);
            /// <summary>Units paid beyond the quantity (a tag line paid by an item bigger than what was left): given back as change when built.</summary>
            public float Over;
            public readonly List<PlacedObject> Matches = new List<PlacedObject>();
            /// <summary>What is taken out of containers (a box, a crate) standing in the yard: which container, which item, how many.</summary>
            public readonly List<Draw> Draws = new List<Draw>();
            /// <summary>Items lying loose on the ground in the yard (dropped, or too heavy for a box) that pay for this line.</summary>
            public readonly List<WorldItem> Loose = new List<WorldItem>();

            public bool Done
            {
                get
                {
                    if (!Active) return true;
                    if (Unresolved) return false;
                    if (Children == null) return Have >= Needed - 0.0001f;
                    if (Any) return Children.Count == 0 || Children[Chosen].Done;
                    foreach (LineStatus c in Children) if (!c.Done) return false;
                    return true;
                }
            }

            /// <summary>0..1: how close the node is to complete.</summary>
            public float Progress
            {
                get
                {
                    if (!Active) return 1f;
                    if (Unresolved) return 0f;
                    if (Children == null) return Mathf.Clamp01(Have / Mathf.Max(0.0001f, Needed));
                    if (Children.Count == 0) return 1f;
                    if (Any) return Children[Chosen].Progress;
                    float sum = 0f;
                    foreach (LineStatus c in Children) sum += c.Progress;
                    return sum / Children.Count;
                }
            }
        }

        /// <summary>What an evaluation has used up so far, copied for each alternative of an "any" section (only the paying one is kept).</summary>
        private sealed class EvalCtx
        {
            public HashSet<PlacedObject> Used = new HashSet<PlacedObject>();
            public HashSet<WorldItem> UsedLoose = new HashSet<WorldItem>();
            public Dictionary<string, int> Drawn = new Dictionary<string, int>();   // owner instance id + item id -> count
            public List<string> Paid = new List<string>();                          // item ids that paid so far (for "uses" conditions)
            public List<string> Specs = new List<string>();                         // the specs of the lines taken so far, paid or not (a chosen alternative counts before anything is placed)

            public EvalCtx Clone() => new EvalCtx
            {
                Used = new HashSet<PlacedObject>(Used),
                UsedLoose = new HashSet<WorldItem>(UsedLoose),
                Drawn = new Dictionary<string, int>(Drawn),
                Paid = new List<string>(Paid),
                Specs = new List<string>(Specs),
            };

            public void CopyFrom(EvalCtx o) { Used = o.Used; UsedLoose = o.UsedLoose; Drawn = o.Drawn; Paid = o.Paid; Specs = o.Specs; }

            public static string Key(PlacedObject owner, string itemId) => owner.GetHashCode() + "|" + itemId;
        }

        /// <summary>The leaves that actually pay: every active line, only the chosen child of an "any" section.</summary>
        public static IEnumerable<LineStatus> PayingLeaves(IEnumerable<LineStatus> nodes)
        {
            if (nodes == null) yield break;
            foreach (LineStatus n in nodes)
            {
                if (!n.Active) continue;
                if (n.Children == null) { yield return n; continue; }
                if (n.Any)
                {
                    if (n.Children.Count > 0) foreach (LineStatus l in PayingLeaves(new[] { n.Children[n.Chosen] })) yield return l;
                }
                else foreach (LineStatus l in PayingLeaves(n.Children)) yield return l;
            }
        }

        /// <summary>Whether an item matching the spec (an item id, #tag or ~equivalency) paid for an earlier line.</summary>
        private static bool PaidWith(EvalCtx ctx, string spec)
        {
            foreach (string id in ctx.Paid) if (Matches(spec, id)) return true;
            foreach (string s in ctx.Specs) if (string.Equals(s, spec, System.StringComparison.OrdinalIgnoreCase)) return true;   // the stage asks for it (the chosen alternative), even before it is placed
            return false;
        }

        /// <summary>Every spec any line of the recipe names (for the yard ring: show it while the player holds something the stage could use).</summary>
        private static bool RecipeNeeds(List<ConstructionLine> nodes, string held)
        {
            if (nodes == null) return false;
            foreach (ConstructionLine n in nodes)
            {
                if (n.IsSection) { if (RecipeNeeds(n.items, held)) return true; }
                else if (Matches(n.item_id, held)) return true;
            }
            return false;
        }

        /// <summary>A quantity for text: whole numbers plain, fractions to 3 places.</summary>
        public static string Num(float v) => Mathf.Abs(v - Mathf.Round(v)) < 0.0005f ? Mathf.Round(v).ToString("0") : v.ToString("0.###");

        /// <summary>What is still missing, in words, for the "Not ready" toast.</summary>
        private void DescribeMissing(IEnumerable<LineStatus> nodes, List<string> missing)
        {
            foreach (LineStatus n in nodes)
            {
                if (n.Done || n.Unresolved) continue;
                if (n.Children == null) { missing.Add($"{Num(n.Needed - n.Have)} x {LineName(n.Line.item_id)}"); continue; }
                if (n.Any)
                {
                    var alts = new List<string>();
                    foreach (LineStatus c in n.Children)
                    {
                        var part = new List<string>();
                        foreach (LineStatus l in PayingLeaves(new[] { c })) part.Add($"{Num(l.Needed)} x {LineName(l.Line.item_id)}");
                        alts.Add(string.Join(" and ", part));
                    }
                    missing.Add(string.Join(" or ", alts));
                }
                else DescribeMissing(n.Children, missing);
            }
        }

        public struct Draw
        {
            public PlacedObject Owner;
            public string ItemId;
            public int Count;
        }

        public sealed class ToolStatus
        {
            public ConstructionToolGroup Group;
            public bool Have;
            /// <summary>Which of the group's tools are there (in the toolbar, in the yard, in a box or lying loose): the hover card ticks them.</summary>
            public readonly HashSet<string> Present = new HashSet<string>();
            /// <summary>The build speed of the fastest tool of the group that is there (1 = baseline).</summary>
            public float Speed;
            /// <summary>Corded electric tools of the group that are there but have no power (no portable generator reaches the site): they do not count.</summary>
            public readonly HashSet<string> Unpowered = new HashSet<string>();
            /// <summary>The most a corded tool that counts in this group draws (watts), 0 when none is corded.</summary>
            public float DrawW;
        }

        /// <summary>A corded electric tool (its manifest draws power_draw_w): it works at a build site only with a portable generator's power.</summary>
        public static bool IsCorded(string itemId)
        {
            AssetCatalogItem it = HudBindings.GetCatalogItem(itemId);
            return it != null && it.power_draw_w > 0f;
        }

        /// <summary>What the corded tools building this stage draw right now: the most power-hungry corded tool that counts in each group, while building.</summary>
        public float CordedDrawW()
        {
            if (!Building || Finished || _tools == null) return 0f;
            float sum = 0f;
            foreach (ToolStatus t in _tools) if (t.Have) sum += t.DrawW;
            return sum;
        }

        /// <summary>The build speed of a tool (its manifest's build_speed; 1 when it sets none).</summary>
        private static float ToolSpeed(string itemId)
        {
            AssetCatalogItem item = HudBindings.GetCatalogItem(itemId);
            return item != null && item.build_speed > 0f ? item.build_speed : 1f;
        }

        public bool Finished => Stage >= _stages.Count;

        public int StageCount => _stages.Count;

        public ConstructionStageData CurrentStage => Finished ? null : _stages[Stage];

        private static bool Matches(string spec, string itemId)
        {
            if (string.IsNullOrEmpty(spec) || string.IsNullOrEmpty(itemId)) return false;
            return GrowthRegistry.IsGroupSpec(spec) ? GrowthRegistry.ToolMatches(spec, itemId) : string.Equals(spec, itemId, System.StringComparison.OrdinalIgnoreCase);
        }

        private static int AlreadyDrawn(EvalCtx ctx, PlacedObject owner, string itemId)
        {
            return ctx.Drawn.TryGetValue(EvalCtx.Key(owner, itemId), out int n) ? n : 0;
        }

        private sealed class Source
        {
            public int Kind;                 // 0 placed object, 1 inside a container, 2 lying loose
            public PlacedObject Owner;       // the placed object (kind 0) or the container (kind 1)
            public WorldItem Loose;
            public string ItemId;
            public int Available;
            public float Value;              // what one is worth in the line's units
            public int Taken;
        }

        /// <summary>
        /// One plain line against the yard. A plain item id counts one each; a "#tag" counts each member at its value (see
        /// GrowthRegistry.UnitValue: 1 large bundle = 2 small = 20 studs), so ANY mix worth the quantity pays. Items are picked to
        /// reach the quantity with the least left over: the biggest that still fits, then the smallest that covers the rest.
        /// Sources, in order: placed objects, what is inside containers in the yard, items lying loose.
        /// </summary>
        private LineStatus EvaluateOne(ConstructionLine line, List<PlacedObject> inYard, List<WorldItem> looseInYard, EvalCtx ctx)
        {
            HashSet<PlacedObject> used = ctx.Used;
            HashSet<WorldItem> usedLoose = ctx.UsedLoose;
            var st = new LineStatus { Line = line, Need = NeedOf(line) };
            ctx.Specs.Add(line.item_id);
            var sources = new List<Source>();
            foreach (PlacedObject o in inYard)
                if (!used.Contains(o) && Matches(line.item_id, o.ItemId) && !(o.Contents != null && o.Contents.Count > 0 && GrowthRegistry.BulkOf(o.ItemId, out _, out _)))
                    sources.Add(new Source { Kind = 0, Owner = o, ItemId = o.ItemId, Available = 1, Value = GrowthRegistry.UnitValue(line.item_id, o.ItemId) });
            foreach (PlacedObject o in inYard)
            {
                if (o.Contents == null) continue;
                foreach (ContainerStack cs in o.Contents)
                {
                    if (!Matches(line.item_id, cs.ItemId)) continue;
                    int left = cs.Count - AlreadyDrawn(ctx, o, cs.ItemId);
                    if (left > 0) sources.Add(new Source { Kind = 1, Owner = o, ItemId = cs.ItemId, Available = left, Value = GrowthRegistry.UnitValue(line.item_id, cs.ItemId) });
                }
            }
            foreach (WorldItem w in looseInYard)
                if (!usedLoose.Contains(w) && Matches(line.item_id, w.ItemId))
                    sources.Add(new Source { Kind = 2, Loose = w, ItemId = w.ItemId, Available = 1, Value = GrowthRegistry.UnitValue(line.item_id, w.ItemId) });

            float need = st.Need;
            float have = 0f;
            while (have < need - 0.0001f)
            {
                float remaining = need - have;
                Source best = null;
                foreach (Source src in sources)
                {
                    if (src.Taken >= src.Available) continue;
                    if (src.Value <= remaining + 0.0001f)
                    {
                        if (best == null || best.Value > remaining + 0.0001f || src.Value > best.Value) best = src;   // the biggest that still fits
                    }
                    else if (best == null || (best.Value > remaining + 0.0001f && src.Value < best.Value)) best = src;   // else the smallest that covers the rest
                }
                if (best == null) break;
                int take = best.Value <= remaining + 0.0001f ? Mathf.Clamp(Mathf.FloorToInt((remaining + 0.0001f) / best.Value), 1, best.Available - best.Taken) : 1;
                best.Taken += take;
                have += take * best.Value;
            }

            foreach (Source src in sources)
            {
                if (src.Taken <= 0) continue;
                if (src.Kind == 0) { st.Matches.Add(src.Owner); used.Add(src.Owner); }
                else if (src.Kind == 1) st.Draws.Add(new Draw { Owner = src.Owner, ItemId = src.ItemId, Count = src.Taken });
                else { st.Loose.Add(src.Loose); usedLoose.Add(src.Loose); }
            }
            st.Have = have;
            st.Over = Mathf.Max(0f, have - need);
            foreach (PlacedObject o in st.Matches) ctx.Paid.Add(o.ItemId);
            foreach (Draw dr in st.Draws) { ctx.Paid.Add(dr.ItemId); string k = EvalCtx.Key(dr.Owner, dr.ItemId); ctx.Drawn[k] = AlreadyDrawn(ctx, dr.Owner, dr.ItemId) + dr.Count; }
            foreach (WorldItem w in st.Loose) ctx.Paid.Add(w.ItemId);
            return st;
        }

        /// <summary>One node of the recipe (a line, or a section with its children) against the yard.</summary>
        private LineStatus EvaluateNode(ConstructionLine node, List<PlacedObject> inYard, List<WorldItem> looseInYard, EvalCtx ctx, string path)
        {
            if (!node.IsSection) return EvaluateOne(node, inYard, looseInYard, ctx);
            var st = new LineStatus { Line = node, Children = new List<LineStatus>(), Any = string.Equals(node.mode, "any", System.StringComparison.OrdinalIgnoreCase) };
            if (!string.IsNullOrEmpty(node.uses) && !PaidWith(ctx, node.uses)) st.Active = false;
            if (!string.IsNullOrEmpty(node.not_uses) && PaidWith(ctx, node.not_uses)) st.Active = false;
            if (!st.Active)
            {
                // shown, but needs nothing; its lines are evaluated on a copy so they show what they would take
                EvalCtx probe = ctx.Clone();
                for (int pi = 0; pi < node.items.Count; pi++) st.Children.Add(EvaluateNode(node.items[pi], inYard, looseInYard, probe, path + "." + pi));
                return st;
            }
            if (!st.Any)
            {
                for (int ai = 0; ai < node.items.Count; ai++) st.Children.Add(EvaluateNode(node.items[ai], inYard, looseInYard, ctx, path + "." + ai));
                return st;
            }
            // "any": the player chooses ONE option up front (one option is chosen for them); only that option is on the list. Until it is chosen the
            // section is a question and nothing under it is evaluated.
            st.Path = path;
            int picked = -1;
            if (node.items.Count == 1) picked = 0;
            else if (_choices.TryGetValue(Stage + ":" + path, out int ci) && ci >= 0 && ci < node.items.Count) picked = ci;
            if (picked < 0) { st.Unresolved = true; return st; }
            st.PickedIndex = picked;
            st.Chosen = 0;   // the one child
            st.Children.Add(EvaluateNode(node.items[picked], inYard, looseInYard, ctx, path + "." + picked));
            return st;
        }

        // ------------------------------------------------------------------ choosing between options

        private readonly Dictionary<string, int> _choices = new Dictionary<string, int>();   // "stage:path" -> the option chosen

        /// <summary>The questions still to answer for this stage: the "any" sections with no option chosen yet (only inside the options already chosen).</summary>
        public List<LineStatus> Unresolved()
        {
            Evaluate();
            var found = new List<LineStatus>();
            void Walk(LineStatus n)
            {
                if (n == null || !n.Active) return;
                if (n.Unresolved) { found.Add(n); return; }
                if (n.Children != null) foreach (LineStatus c in n.Children) Walk(c);
            }
            if (_status != null) foreach (LineStatus l in _status) Walk(l);
            return found;
        }

        /// <summary>True when the current stage's recipe has any choice in it (so a reset button makes sense).</summary>
        public bool HasChoices()
        {
            ConstructionStageData stage = CurrentStage;
            if (stage == null || stage.recipe == null) return false;
            bool Has(List<ConstructionLine> items)
            {
                foreach (ConstructionLine n in items)
                    if (n.IsSection && ((string.Equals(n.mode, "any", System.StringComparison.OrdinalIgnoreCase) && n.items.Count > 1) || Has(n.items))) return true;
                return false;
            }
            return Has(stage.recipe);
        }

        /// <summary>Chooses an option of a question (an "any" section). Choices made deeper under it are forgotten.</summary>
        public void Choose(string path, int option)
        {
            if (Building) return;
            string key = Stage + ":" + path;
            var drop = new List<string>();
            foreach (string k in _choices.Keys) if (k.StartsWith(key + ".")) drop.Add(k);
            foreach (string k in drop) _choices.Remove(k);
            _choices[key] = option;
            _status = null;
        }

        /// <summary>Forgets the choices of the current stage: the questions are asked again.</summary>
        public void ResetChoices()
        {
            if (Building) return;
            var drop = new List<string>();
            foreach (string k in _choices.Keys) if (k.StartsWith(Stage + ":")) drop.Add(k);
            foreach (string k in drop) _choices.Remove(k);
            _status = null;
        }

        public List<string> ChoiceList()
        {
            var list = new List<string>();
            foreach (var kv in _choices) list.Add(kv.Key + "=" + kv.Value);
            return list;
        }

        public void SetChoices(List<string> list)
        {
            _choices.Clear();
            if (list == null) return;
            foreach (string e in list)
            {
                int eq = e.LastIndexOf('=');
                if (eq > 0 && int.TryParse(e.Substring(eq + 1), out int v)) _choices[e.Substring(0, eq)] = v;
            }
            _status = null;
        }

        /// <summary>A short label for one option of a question: its title, or what it takes.</summary>
        public static string OptionLabel(ConstructionLine node)
        {
            if (node == null) return "?";
            if (!node.IsSection) return Num(node.quantity) + " x " + LineName(node.item_id);
            if (!string.IsNullOrEmpty(node.section)) return node.section;
            var parts = new List<string>();
            foreach (ConstructionLine c in node.items) parts.Add(OptionLabel(c));
            return string.Join(" and ", parts);
        }

        /// <summary>Counts what is in the yard against the current stage's list (refreshed a few times a second).</summary>
        public void Evaluate(bool force = false)
        {
            if (Building && _status != null) return;   // the list is frozen while the ped works
            if (!force && _status != null && Time.unscaledTime < _nextEval) return;
            _nextEval = Time.unscaledTime + 0.25f;
            _status = new List<LineStatus>();
            _tools = new List<ToolStatus>();
            ConstructionStageData stage = CurrentStage;
            if (stage == null) return;

            var inYard = new List<PlacedObject>();
            foreach (PlacedObject o in PlacedObject.All) if (o != null && InYard(o.transform.position)) inYard.Add(o);
            var looseInYard = new List<WorldItem>();
            foreach (WorldItem w in WorldItem.All) if (w != null && InYard(w.transform.position)) looseInYard.Add(w);

            // Each placed object pays for one line only (the lines are taken in order). A section takes its children as described on LineStatus.
            var ctx = new EvalCtx();
            for (int ri = 0; ri < stage.recipe.Count; ri++)
                _status.Add(EvaluateNode(stage.recipe[ri], inYard, looseInYard, ctx, ri.ToString()));

            // Tools: in the toolbar, in the yard (placed, in a box, or lying loose). They stay where they are. Every tool of a group is
            // checked, so the hover card can tick the ones that are there; the group is met when any one is.
            HudState hud = HudState.Active;
            foreach (ConstructionToolGroup group in stage.tool_groups)
            {
                var ts = new ToolStatus { Group = group };
                foreach (string tool in group.tools)
                {
                    bool has = false;
                    float best = 0f;
                    void Consider(string itemId)
                    {
                        if (!Matches(tool, itemId)) return;
                        if (IsCorded(itemId) && !PortableGenerator.Powers(this)) { ts.Unpowered.Add(tool); return; }   // a corded tool needs a generator at the site
                        has = true;
                        AssetCatalogItem drawInfo = HudBindings.GetCatalogItem(itemId);
                        if (drawInfo != null) ts.DrawW = Mathf.Max(ts.DrawW, drawInfo.power_draw_w);
                        best = Mathf.Max(best, ToolSpeed(itemId));
                    }
                    if (hud != null)
                        foreach (ToolbarSlotData slot in hud.Toolbar)
                        {
                            if (slot.Count <= 0) continue;
                            Consider(slot.IconId);
                            // a toolbox (any container) carried in the toolbar: the tools inside it count too
                            if (slot.Contents != null) foreach (ContainerStack cs in slot.Contents) if (cs != null && cs.Count > 0) Consider(cs.ItemId);
                        }
                    foreach (PlacedObject o in inYard)
                    {
                        Consider(o.ItemId);
                        if (o.Contents != null) foreach (ContainerStack cs in o.Contents) if (cs.Count > 0) Consider(cs.ItemId);
                    }
                    foreach (WorldItem w in looseInYard) Consider(w.ItemId);
                    if (has) { ts.Present.Add(tool); ts.Speed = Mathf.Max(ts.Speed, best); }
                }
                ts.Have = ts.Present.Count > 0;
                _tools.Add(ts);
            }
        }

        public List<LineStatus> Lines { get { Evaluate(); return _status; } }
        public List<ToolStatus> Tools { get { Evaluate(); return _tools; } }

        public bool Ready
        {
            get
            {
                Evaluate();
                if (Finished) return false;
                foreach (LineStatus l in _status) if (!l.Done) return false;
                foreach (ToolStatus t in _tools) if (!t.Have) return false;
                return true;
            }
        }

        // ------------------------------------------------------------------ building a stage

        /// <summary>Right click on the site: build the current stage if everything is there.</summary>
        public bool TryBuild(Transform player)
        {
            if (Finished) return false;   // a finished building: only a click on its door works the door (TryDoorAtCursor), not the walls
            if (Building) return false;
            if (player != null && DistanceOutside(player.position) > YardM + 1f)
            {
                ToastNotificationSystem.ShowInfo("Too far", "Move closer to the construction site.");
                return false;
            }
            Evaluate(true);
            ConstructionStageData stage = CurrentStage;
            List<LineStatus> questions = Unresolved();
            if (questions.Count > 0)
            {
                ToastNotificationSystem.ShowInfo("Choose how to build", "Pin the list (P) and choose an option first: " + (string.IsNullOrEmpty(questions[0].Line.section) ? "the materials" : questions[0].Line.section) + ".");
                return false;
            }
            var missing = new List<string>();
            DescribeMissing(_status, missing);
            foreach (ToolStatus t in _tools)
                if (!t.Have) missing.Add(ToolGroupName(t.Group));
            if (missing.Count > 0)
            {
                ToastNotificationSystem.ShowWarning("Not ready: " + StageTitle(stage), "Still needed: " + string.Join(", ", missing) + ".");
                return false;
            }

            PedController ped = player != null ? player.GetComponent<PedController>() : null;
            if (ped == null) ped = PedController.Current;
            if (ped == null) { Complete(); return true; }   // nobody to animate
            StartCoroutine(BuildRoutine(ped));
            return true;
        }

        /// <summary>
        /// TEMPORARY test shortcut (Alt + right click on the site): builds the current stage at once with no materials, no tools and no build time.
        /// Nothing is used up. Remove it (and the Alt branch in PlacementController) when the recipes are settled.
        /// </summary>
        public bool TryBuildFree()
        {
            if (Finished || Building) return false;
            ConstructionStageData stage = CurrentStage;
            Stage++;
            _status = null;
            RefreshVisual();
            if (Finished) ConstructionHover.ForgetPinAt(transform.position);   // (the yard is NOT tidied by itself any more: it moved things out of neighbouring buildings. Tidying is the player's: the Tidy Area key)
            return true;
        }

        // ------------------------------------------------------------------ building takes time

        /// <summary>How long a stage takes to build, in seconds.</summary>
        public const float BuildSeconds = 30f;

        public bool Building { get; private set; }
        private float _buildStart, _buildEnd;
        private float _buildSeconds = BuildSeconds;   // this build's length: the baseline over the speed of its slowest tool group

        /// <summary>
        /// How fast the tools at the site build this stage (1 = baseline): each tool group counts its fastest tool that is there, the stage is as slow as its
        /// slowest group. A primitive tool (a hammer, a hand saw) is below 1, so it takes longer.
        /// </summary>
        public float ToolSpeedNow
        {
            get
            {
                Evaluate();
                float speed = 0f;
                bool any = false;
                foreach (ToolStatus t in _tools)
                {
                    if (!t.Have) continue;
                    speed = any ? Mathf.Min(speed, t.Speed) : t.Speed;
                    any = true;
                }
                return any ? Mathf.Max(0.1f, speed) : 1f;
            }
        }

        /// <summary>How long building the current stage would take now, in seconds.</summary>
        public float EstimatedBuildSeconds => Building ? _buildSeconds : Mathf.Clamp(BuildSeconds / ToolSpeedNow, 5f, 600f);

        /// <summary>0 to 1 while a stage is being built: it follows the clock, so it never stalls while the ped is walking.</summary>
        public float BuildProgress { get { return Building ? Mathf.Clamp01((Time.time - _buildStart) / _buildSeconds) : 0f; } }

        private static readonly string[] FoundationClips = { "Dig", "Hoe" };
        private static readonly string[] FramingClips = { "Fixing_Kneeling_RT", "Chop_Tree_RT" };

        /// <summary>A random spot on the ground just outside the foundation, all the way round (the ped works from outside the walls).</summary>
        private Vector3 _lastSpot = new Vector3(float.MaxValue, 0f, 0f);

        /// <summary>A different random spot each time: all round the foundation, at a varying distance out, and not close to the last one.</summary>
        private Vector3 RandomSpot()
        {
            Vector3 spot = default;
            for (int tries = 0; tries < 8; tries++)
            {
                spot = RandomSpotOnce();
                if ((spot - _lastSpot).sqrMagnitude > 2.5f * 2.5f) break;
            }
            _lastSpot = spot;
            return spot;
        }

        private Vector3 RandomSpotOnce()
        {
            float side = Random.value * 2f * (_foot.x + _foot.y);
            float reach = Random.Range(1.2f, 2.8f);   // how far out from the walls
            float hx = _foot.x * 0.5f + reach, hz = _foot.y * 0.5f + reach;
            Vector3 local;
            if (side < _foot.x) local = new Vector3(-_foot.x * 0.5f + side, 0f, -hz);
            else if (side < _foot.x + _foot.y) local = new Vector3(hx, 0f, -_foot.y * 0.5f + (side - _foot.x));
            else if (side < 2f * _foot.x + _foot.y) local = new Vector3(_foot.x * 0.5f - (side - _foot.x - _foot.y), 0f, hz);
            else local = new Vector3(-hx, 0f, _foot.y * 0.5f - (side - 2f * _foot.x - _foot.y));
            Vector3 w = transform.TransformPoint(local);
            w.y = TerrainHeightDetector.GetGroundY(w);
            return w;
        }

        // The foundation (and the footing under its high side) is a solid wall, so a walk across the site goes round it by its corners.
        private const float AvoidMargin = 0.8f;

        /// <summary>True when the straight line between two points passes through the foundation (grown by AvoidMargin).</summary>
        private bool CrossesSite(Vector3 a, Vector3 b)
        {
            Quaternion inv = Quaternion.Euler(0f, -YawDeg, 0f);
            Vector3 la = inv * (a - transform.position), lb = inv * (b - transform.position);
            float hx = _foot.x * 0.5f + AvoidMargin * 0.9f, hz = _foot.y * 0.5f + AvoidMargin * 0.9f;
            float t0 = 0f, t1 = 1f;
            Vector2 d = new Vector2(lb.x - la.x, lb.z - la.z);
            Vector2 o = new Vector2(la.x, la.z);
            Vector2 h = new Vector2(hx, hz);
            for (int i = 0; i < 2; i++)
            {
                if (Mathf.Abs(d[i]) < 1e-5f) { if (Mathf.Abs(o[i]) > h[i]) return false; continue; }
                float ta = (-h[i] - o[i]) / d[i], tb = (h[i] - o[i]) / d[i];
                if (ta > tb) { float tmp = ta; ta = tb; tb = tmp; }
                t0 = Mathf.Max(t0, ta);
                t1 = Mathf.Min(t1, tb);
                if (t0 > t1) return false;
            }
            return true;
        }

        /// <summary>The way to a point: straight when clear, otherwise round one or two corners of the site, whichever is shortest.</summary>
        private List<Vector3> PathTo(Vector3 from, Vector3 to)
        {
            var path = new List<Vector3>();
            if (CrossesSite(from, to))
            {
                float hx = _foot.x * 0.5f + AvoidMargin + 0.4f, hz = _foot.y * 0.5f + AvoidMargin + 0.4f;
                var corners = new Vector3[4];
                for (int i = 0; i < 4; i++)
                {
                    Vector3 local = new Vector3(i == 0 || i == 3 ? -hx : hx, 0f, i < 2 ? -hz : hz);
                    Vector3 w = transform.TransformPoint(local);
                    w.y = TerrainHeightDetector.GetGroundY(w);
                    corners[i] = w;
                }
                float best = float.MaxValue;
                List<Vector3> bestPath = null;
                for (int i = 0; i < 4; i++)
                {
                    if (!CrossesSite(from, corners[i]) && !CrossesSite(corners[i], to))
                    {
                        float len = (corners[i] - from).magnitude + (to - corners[i]).magnitude;
                        if (len < best) { best = len; bestPath = new List<Vector3> { corners[i] }; }
                    }
                    int j = (i + 1) % 4;   // two neighbouring corners: along one side of the site
                    if (!CrossesSite(from, corners[i]) && !CrossesSite(corners[j], to))
                    {
                        float len = (corners[i] - from).magnitude + (corners[j] - corners[i]).magnitude + (to - corners[j]).magnitude;
                        if (len < best) { best = len; bestPath = new List<Vector3> { corners[i], corners[j] }; }
                    }
                }
                if (bestPath != null) path.AddRange(bestPath);
            }
            path.Add(to);
            return path;
        }

        /// <summary>
        /// Walks to a point round the site (see PathTo). Reports false when the player took over, true on arrival; a leg that makes no progress
        /// for a second (caught on a footing or a rock) is given up so the build carries on from where the ped stands.
        /// </summary>
        private System.Collections.IEnumerator WalkTo(PedController ped, Vector3 target, float arrive, System.Action<bool> done)
        {
            List<Vector3> path = PathTo(ped.transform.position, target);
            for (int leg = 0; leg < path.Count; leg++)
            {
                Vector3 goal = path[leg];
                float tol = leg == path.Count - 1 ? arrive : 0.7f;
                ped.AutoWalkTo(goal);
                float giveUp = Time.time + 8f;
                float bestDist = float.MaxValue, markTime = Time.time;
                while (true)
                {
                    if (ped.AutoCancelled) { done(false); yield break; }
                    Vector3 d = goal - ped.transform.position;
                    d.y = 0f;
                    float dist = d.magnitude;
                    if (dist <= tol || Time.time > giveUp || Time.time > _buildEnd + 1f) break;
                    if (dist < bestDist - 0.3f) { bestDist = dist; markTime = Time.time; }   // getting closer
                    else if (Time.time - markTime > 1.5f) break;                              // not getting closer: stuck, give the leg up
                    yield return null;
                }
            }
            ped.AutoStop();
            done(true);
        }

        private static void Show(GameObject go, bool visible)
        {
            if (go == null) return;
            foreach (Renderer r in go.GetComponentsInChildren<Renderer>(true)) r.enabled = visible;
        }

        /// <summary>
        /// The build takes BuildSeconds. The ped walks to the materials one source at a time (carrying them back, the source disappearing as it is
        /// picked up), then works at random spots round the foundation until the time is up; walking by hand cancels it and puts everything back.
        /// </summary>
        private System.Collections.IEnumerator BuildRoutine(PedController ped)
        {
            Evaluate(true);
            _buildSeconds = Mathf.Clamp(BuildSeconds / ToolSpeedNow, 5f, 600f);   // the tools at the site set the pace
            Building = true;
            _buildStilts = Stage == 0 && StructureLook.FoundationStyle(PayerIds()) == "stilts";
            _buildStart = Time.time;
            _buildEnd = _buildStart + _buildSeconds;
            ConstructionStageData stage = CurrentStage;
            StartCoroutine(RunBuildPreview(stage));   // a stage with a build_motion shows its model being raised, hoisted or fitted while the ped works

            // the materials to fetch: each distinct thing paying this stage, nearest first (a few trips at most)
            var sources = new List<GameObject>();
            foreach (LineStatus l in PayingLeaves(_status))
            {
                foreach (PlacedObject o in l.Matches) if (o != null && !sources.Contains(o.gameObject)) sources.Add(o.gameObject);
                foreach (Draw dr in l.Draws) if (dr.Owner != null && !sources.Contains(dr.Owner.gameObject)) sources.Add(dr.Owner.gameObject);
                foreach (WorldItem w in l.Loose) if (w != null && !sources.Contains(w.gameObject)) sources.Add(w.gameObject);
            }
            Vector3 here = ped.transform.position;
            sources.Sort((x, y) => (x.transform.position - here).sqrMagnitude.CompareTo((y.transform.position - here).sqrMagnitude));
            if (sources.Count > 5) sources.RemoveRange(5, sources.Count - 5);
            var hidden = new List<GameObject>();

            float start = Time.time, end = start + _buildSeconds;
            float fetchBudget = _buildSeconds * 0.45f;
            bool cancelled = false;

            foreach (GameObject src in sources)
            {
                if (src == null) continue;
                if (Time.time - start > fetchBudget) break;
                ped.Carrying = false;
                bool ok = true;
                yield return WalkTo(ped, src.transform.position, 1.1f, r => ok = r);
                if (!ok) { cancelled = true; break; }
                bool crouched = ped.BeginWork("Crouch_Idle_RT", src.transform.position);
                yield return new WaitForSeconds(0.8f);
                if (crouched) ped.EndWork("Crouch_Idle_RT");
                Show(src, false);   // picked up
                hidden.Add(src);
                ped.Carrying = true;
                yield return WalkTo(ped, RandomSpot(), 0.6f, r => ok = r);
                ped.Carrying = false;
                if (!ok) { cancelled = true; break; }
            }

            // the work: a random spot at a time, hammering (digging, for the foundation) until the time is up
            string[] clips = stage != null && stage.build_clips != null && stage.build_clips.Count > 0 ? stage.build_clips.ToArray() : new[] { (Stage == 0 ? FoundationClips : FramingClips)[0] };
            int burst = 0;
            while (!cancelled && Time.time < end)
            {
                string clip = clips[burst++ % clips.Length];   // the stage's own work, one clip after the other
                bool ok = true;
                yield return WalkTo(ped, RandomSpot(), 0.6f, r => ok = r);
                if (!ok) { cancelled = true; break; }
                float until = Mathf.Min(end, Time.time + Random.Range(1.8f, 3.2f));
                bool animated = ped.BeginWork(clip, transform.position);
                while (Time.time < until)
                {
                    if (ped.ManualInput) { cancelled = true; break; }   // the player took over (IsMoving would be stale right after an automatic walk)
                    yield return null;
                }
                if (animated) ped.EndWork(clip);
            }
            ped.AutoStop();
            ped.Carrying = false;

            Building = false;
            EndBuildPreview();
            foreach (GameObject g in hidden) Show(g, true);   // (the used ones are removed by Complete)
            if (cancelled)
            {
                if (Stage == 0 && _grade != null) { _grade.Apply(0f); Homesteader.World.TerrainGrade.GroundChanged(); }   // the ground goes back
                _status = null;
                yield break;
            }
            Complete();
        }

        // ------------------------------------------------------------------ the stage's model moving while it is built

        private GameObject _preview;
        private bool _previewWanted;

        /// <summary>
        /// While a stage with a build_motion is built, its model stands in the site and moves with the progress (the mast is raised, the head hoisted, the blades fitted and spun up);
        /// what was built before is hidden meanwhile (the preview has it too). <see cref="EndBuildPreview"/> puts the finished look back.
        /// </summary>
        private System.Collections.IEnumerator RunBuildPreview(ConstructionStageData stage)
        {
            _previewWanted = false;
            if (stage == null || string.IsNullOrEmpty(stage.build_motion) || string.IsNullOrEmpty(stage.item_id)) yield break;
            if (!ItemRegistry.TryGet(stage.item_id, out ItemRegistry.ItemInfo info) || info.Prefab == null) yield break;
            _previewWanted = true;
            GlbTemplate glb = info.Prefab.GetComponent<GlbTemplate>();
            while (glb != null && !glb.Ready)
            {
                glb.EnsureLoading();
                if (glb.Failed || !_previewWanted) yield break;
                yield return null;
            }
            if (!_previewWanted || !Building) yield break;
            _preview = Instantiate(info.Prefab, transform);
            _preview.name = "BuildPreview";
            _preview.SetActive(true);
            _preview.transform.localPosition = Vector3.zero;
            _preview.transform.localRotation = Quaternion.identity;
            foreach (Collider c in _preview.GetComponentsInChildren<Collider>(true)) Destroy(c);
            if (_visual != null) _visual.SetActive(false);
            _preview.AddComponent<BuildMotionView>().Init(this, stage.build_motion);
        }

        private void EndBuildPreview()
        {
            _previewWanted = false;
            if (_preview != null) Destroy(_preview);
            _preview = null;
            if (_visual != null) _visual.SetActive(true);
        }

        /// <summary>The time is up: the materials are used up and the stage exists.</summary>
        private void Complete()
        {
            ConstructionStageData stage = CurrentStage;
            // the materials are used up (placed ones, and what is drawn out of boxes); tools stay
            foreach (LineStatus l in PayingLeaves(_status))   // an "any" section uses up only the alternative that paid
            {
                RememberLooks(l);
                foreach (PlacedObject o in l.Matches) if (o != null) o.Remove();
                foreach (WorldItem w in l.Loose) if (w != null) Destroy(w.gameObject);
                GiveChange(l.Line.item_id, l.Over);
                foreach (Draw dr in l.Draws)
                {
                    if (dr.Owner == null) continue;
                    ContainerRules.Remove(dr.Owner.Contents, dr.ItemId, dr.Count);
                    if (dr.Owner.Contents.Count == 0 && (ContainerRules.IsDisposable(dr.Owner.ItemId) || WheelbarrowPush.IsPile(dr.Owner.ItemId))) dr.Owner.Remove();   // an emptied cardboard box, or a heap used up, goes away
                }
            }

            Stage++;
            _status = null;
            RefreshVisual();
            if (Finished) ConstructionHover.ForgetPinAt(transform.position);   // (the yard is NOT tidied by itself any more: it moved things out of neighbouring buildings. Tidying is the player's: the Tidy Area key)
        }


        /// <summary>
        /// A tag line paid by an item bigger than what was left (a large bundle for the last 10 studs) is broken down: the surplus comes
        /// back as the next size down, then the next, then single items, dropped on the ground beside the site.
        /// </summary>
        private void GiveChange(string spec, float over)
        {
            if (over < 0.999f || !GrowthRegistry.IsGroupSpec(spec)) return;
            var members = GrowthRegistry.ToolItems(spec);
            members.Sort((a, b) => GrowthRegistry.UnitValue(spec, b).CompareTo(GrowthRegistry.UnitValue(spec, a)));
            int dropped = 0;
            foreach (string id in members)
            {
                float v = GrowthRegistry.UnitValue(spec, id);
                if (v < 1f) continue;
                int n = Mathf.FloorToInt((over + 0.0001f) / v);
                for (int i = 0; i < n && dropped < 40; i++, dropped++)
                {
                    float ang = dropped * 2.4f;
                    Vector3 at = transform.position + new Vector3(Mathf.Cos(ang), 0f, Mathf.Sin(ang)) * (1.2f + 0.15f * dropped);
                    WorldItem.TryDrop(id, at);
                }
                over -= n * v;
                if (over < 0.999f) break;
            }
        }

        /// <summary>
        /// Takes back a site that has not been started (still only the dirt area): the site goes and the structure item returns to the
        /// toolbar. Once the first stage has been built it can no longer be cancelled.
        /// </summary>
        public bool TryCancel(Transform player)
        {
            if (Stage > 0) { ToastNotificationSystem.ShowInfo(Name(), "Building has started; it can't be taken back."); return false; }
            if (Building) return false;
            if (player != null && DistanceOutside(player.position) > YardM + 1f)
            {
                ToastNotificationSystem.ShowInfo("Too far", "Move closer to the construction site.");
                return false;
            }
            HudState hud = HudState.Active;
            if (hud == null) return false;
            int added = hud.AddItemToToolbar(StructureId, 1, HudBindings.GetMaxStack(StructureId));
            if (added <= 0) { ToastNotificationSystem.ShowWarning("Toolbar full", "Make room on the toolbar to take the structure back."); return false; }
            HudBindings.Instance?.RefreshToolbar();
            ConstructionHover.ForgetPinAt(transform.position);
            Destroy(gameObject);
            return true;
        }

        /// <summary>
        /// Admin: removes the structure entirely, at any stage (Alt + right click with a hammer in hand). What is mounted on it goes with it; its wires and pipes are
        /// cut (a link to a removed device is dropped on the next redraw). Nothing is given back.
        /// </summary>
        public void AdminRemove()
        {
            foreach (AttachedObject at in new List<AttachedObject>(AttachedObject.All))
                if (at != null && at.Site == this) Destroy(at.gameObject);
            ConstructionHover.ForgetPinAt(transform.position);
            Destroy(gameObject);
        }

        public string Name() { return HudBindings.GetItemName(StructureId); }

        private static string StageTitle(ConstructionStageData s)
        {
            string n = s != null ? s.name : "stage";
            return string.IsNullOrEmpty(n) ? "Stage" : char.ToUpperInvariant(n[0]) + n.Substring(1);
        }

        public static string LineName(string spec)
        {
            if (string.IsNullOrEmpty(spec)) return "?";
            if (spec[0] == '~') return GrowthRegistry.EquivalencyLabel(spec);
            if (spec[0] != '#') return HudBindings.GetDisplayName(spec);
            string[] parts = spec.Substring(1).Split('_');
            for (int i = 0; i < parts.Length; i++) if (parts[i].Length > 0) parts[i] = char.ToUpperInvariant(parts[i][0]) + parts[i].Substring(1);
            return string.Join(" ", parts);
        }

        /// <summary>"Shovel or Pickaxe" (the first few of a group's alternatives).</summary>
        public static string ToolGroupName(ConstructionToolGroup g)
        {
            var names = new List<string>();
            foreach (string t in g.tools) { names.Add(LineName(t)); if (names.Count == 2) break; }
            string text = string.Join(" or ", names);
            return g.tools.Count > 2 ? text + " or " + (g.tools.Count - 2) + " more" : text;
        }

        // ------------------------------------------------------------------ the picture

        private bool _cleared;

        // The ground is graded up to the foundation's level (see TerrainGrade): gradually while the foundation is built, fully when it exists.
        private float _level;
        private Homesteader.World.TerrainGrade _grade;
        private float _nextGroundRefresh;

        private bool EnsureGrade()
        {
            if (_grade == null) _grade = Homesteader.World.TerrainGrade.Plan(transform.position, YawDeg, _foot, _level);
            return _grade != null && _grade.Any;
        }

        /// <summary>While the foundation is being built the ground rises with the progress.</summary>
        private void GradeWhileBuilding()
        {
            if (!Building || Stage != 0 || _buildStilts || !EnsureGrade()) return;
            _grade.Apply(BuildProgress);
            if (Time.time >= _nextGroundRefresh) { _nextGroundRefresh = Time.time + 3f; Homesteader.World.TerrainGrade.GroundChanged(); }
        }

        private void RefreshVisual()
        {
            if (_visualStage == Stage) return;
            _visualStage = Stage;
            if (Stage >= 1 && !_cleared)
            {
                _cleared = true;   // the foundation is down: whatever grew or lay under it goes
                Homesteader.World.SiteClearing.ClearFootprint(transform.position, YawDeg, _foot);
                if (!Stilted && EnsureGrade())
                {
                    _grade.Apply(1f);   // the ground meets the foundation: no footing needed
                    _drop = 0f;
                    Homesteader.World.TerrainGrade.GroundChanged();
                }
            }
            if (_visual != null) Destroy(_visual);
            _visual = null;
            if (_patch != null) _patch.SetActive(Stage == 0);   // the dirt area is only the marked site: once the foundation is built it goes
            if (_arrow != null) _arrow.SetActive(Stage == 0);
            if (Stage <= 0) return;

            ConstructionStageData done = _stages[Stage - 1];
            _visual = new GameObject("Stage_" + done.name);
            _visual.transform.SetParent(transform, false);
            AddFooting(_visual.transform);
            // A stage with its own model shows it; otherwise a stand-in from the stage's size.
            if (done.item_id != null && ItemRegistry.TryGet(done.item_id, out ItemRegistry.ItemInfo info) && info.Prefab != null)
            {
                _modelPending = true;
                StartCoroutine(ShowModel(info.Prefab, _visual.transform));
                return;
            }
            BuildStandIn(done, _visual.transform);
        }

        private System.Collections.IEnumerator ShowModel(GameObject prefab, Transform parent)
        {
            GlbTemplate glb = prefab.GetComponent<GlbTemplate>();
            while (glb != null && !glb.Ready)
            {
                glb.EnsureLoading();
                if (glb.Failed) { BuildStandIn(_stages[Mathf.Max(0, Stage - 1)], parent); _modelPending = false; yield break; }
                yield return null;
            }
            if (parent == null) { _modelPending = false; yield break; }
            LearnFront(prefab);
            GameObject model = Instantiate(prefab, parent);
            model.SetActive(true);
            model.transform.localPosition = Vector3.zero;
            model.transform.localRotation = Quaternion.identity;
            EnsureCollider(model);
            FindDoor(model.transform);
            StructureLook.Apply(model.transform, _lookItems);   // birch logs, a tin roof: the look follows what it was built from
            ApplyWallPaints(model.transform);                    // and the walls painted one by one
            ShowFoundationVariant(model.transform);
            if (Finished) WindTurbine.AttachToModel(model, HudBindings.GetCatalogItem(StructureId) != null ? HudBindings.GetCatalogItem(StructureId).max_power_w : 0f);   // a finished wind turbine turns into the wind
            if (Finished && !string.IsNullOrEmpty(FittedPanel)) StartCoroutine(ShowFittedPanel(model.transform));   // a well's sub panel on its post
            Fireplace = Fireplace.Attach(this, model.transform);   // a chimney with a firebox: logs, fire and smoke
            // windows let light through: the pane casts no shadow (and the walls, roof and a closed door do)
            foreach (Renderer r in model.GetComponentsInChildren<Renderer>(true))
                if (r.name == "WindowGlass") r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            _modelPending = false;
        }

        // ------------------------------------------------------------------ the door

        // The finished model has its front door as its own object on a hinge (DoorHinge, with the leaf as its child) so it can swing open.
        private Transform _hinge;
        private Quaternion _hingeClosed;
        private float _swingSign = 1f;
        private float _doorAngle;
        private const float DoorOpenDegrees = 105f;
        private const float DoorSwingSpeed = 180f;

        private Collider[] _leafColliders;

        // The items that set how the building looks (see StructureLook): the last log / siding item used for the walls, the last roofing for the roof.
        // ------------------------------------------------------------------ a drilled well (docs/WELLS.md)

        /// <summary>True for a drilled well (its manifest's is_well).</summary>
        public bool IsWell { get { AssetCatalogItem it = HudBindings.GetCatalogItem(StructureId); return it != null && it.is_well; } }

        /// <summary>Metres down to water where this well stands (0 for anything that is not a well).</summary>
        public float WellDepthM => IsWell ? WaterTable.DepthM(transform.position) : 0f;

        /// <summary>The pump that went down the well (saved), or null.</summary>
        public string PumpId { get; set; }

        /// <summary>The sub panel fitted on the well's post (saved), or null.</summary>
        public string FittedPanel { get; private set; }

        /// <summary>What a recipe line needs at this site: its quantity, plus per_depth_m x the well's depth (whole units).</summary>
        public float NeedOf(ConstructionLine line)
        {
            if (line == null) return 0f;
            if (line.per_depth_m <= 0f) return line.quantity;
            return Mathf.Ceil(line.quantity + line.per_depth_m * WellDepthM);
        }

        /// <summary>A finished well and its sub panel in hand: the panel is fitted on the well's post and the well becomes something to wire (AC wire to a breaker box). True when the click was for that.</summary>
        public bool TryFitPanel(string heldId)
        {
            AssetCatalogItem it = HudBindings.GetCatalogItem(StructureId);
            if (it == null || string.IsNullOrEmpty(it.attach_item) || it.attach_item != heldId) return false;
            if (!Finished) { ToastNotificationSystem.ShowInfo("Not finished", "Finish building the well first."); return true; }
            if (!string.IsNullOrEmpty(FittedPanel)) { ToastNotificationSystem.ShowInfo("Already fitted", "This well has its sub panel."); return true; }
            HudState hud = HudState.Active;
            if (hud == null || !hud.ConsumeFromSelectedSlot(1)) return true;
            HudBindings.Instance?.RefreshToolbar();
            FitPanel(heldId);
            return true;
        }

        /// <summary>Puts the sub panel on (a fresh fit or a loaded game): its model on the post, and the well wired as that panel.</summary>
        public void FitPanel(string panelId)
        {
            if (string.IsNullOrEmpty(panelId)) return;
            FittedPanel = panelId;
            WireNode.Attach(gameObject, panelId);
            if (VisualRoot != null && Finished) StartCoroutine(ShowFittedPanel(VisualRoot));
        }

        private GameObject _panelModel;

        private System.Collections.IEnumerator ShowFittedPanel(Transform model)
        {
            if (_panelModel != null || string.IsNullOrEmpty(FittedPanel)) yield break;
            if (!ItemRegistry.TryGet(FittedPanel, out ItemRegistry.ItemInfo info) || info.Prefab == null) yield break;
            var tpl = info.Prefab.GetComponent<Homesteader.Modding.GlbTemplate>();
            if (tpl != null)
            {
                tpl.EnsureLoading();
                float until = Time.realtimeSinceStartup + 15f;
                while (!tpl.Ready && !tpl.Failed && Time.realtimeSinceStartup < until) yield return null;
                if (!tpl.Ready) yield break;
            }
            if (_panelModel != null || model == null) yield break;
            Transform mount = null;
            foreach (Transform t in model.GetComponentsInChildren<Transform>(true)) if (t.name == "PanelMount") { mount = t; break; }
            _panelModel = Instantiate(info.Prefab, mount != null ? mount : model);
            _panelModel.name = "FittedSubPanel";
            _panelModel.SetActive(true);
            foreach (Collider c in _panelModel.GetComponentsInChildren<Collider>(true)) Destroy(c);
            _panelModel.transform.localPosition = mount != null ? Vector3.zero : new Vector3(0.75f, 0.72f, 0.6f);
        }

        private readonly List<string> _lookItems = new List<string>();
        public List<string> LookItems => _lookItems;

        public void SetLooks(List<string> ids)
        {
            _lookItems.Clear();
            if (ids != null) _lookItems.AddRange(ids);
            StructureLook.Apply(VisualRoot, _lookItems);   // when the model is already showing
            ApplyWallPaints(VisualRoot);
        }

        // ------------------------------------------------------------------ painting walls and doors

        // A right click with a paint can in the active slot paints what is under the cursor:
        //   * the OUTSIDE of a wall: that whole wall's siding or logs ("Wall_Front|out" = item id);
        //   * a DOOR: that door leaf ("Door:DoorSlide_b1L" = item id);
        //   * a wall inside: just the section of it in that room, a patch of paint laid over the wall (see PaintPatch).
        // Saved with the site (wallPaints); painted again whenever the model shows (a stage change loads a new one).
        private readonly Dictionary<string, string> _wallPaints = new Dictionary<string, string>();

        /// <summary>
        /// Paint on the inside of a wall, one room's section of it: the connected stretch of wall face around the click (it ends at the corners,
        /// the partitions, the doorways and the window openings), found by testing a grid of cells against the wall with rays, then laid as flat
        /// quads just off the surface. Stored as the grid (origin, directions, cell size) and the runs of painted cells in each row, in the site's
        /// local space, so it is saved small and rebuilt without any rays.
        /// </summary>
        private sealed class PaintPatch
        {
            public string Item;
            public Vector3 O, N, T;                 // grid origin (the bottom left corner of cell 0,0), the wall normal and the direction along the wall
            public float Cell;
            public int Order;                        // newer patches lie over older ones
            public List<Vector3Int> Runs = new List<Vector3Int>();   // row, first column, last column
            public GameObject Go;
        }

        private readonly List<PaintPatch> _patches = new List<PaintPatch>();
        private const float PaintCell = 0.125f;

        private static string F(float v) { return v.ToString("R", System.Globalization.CultureInfo.InvariantCulture); }
        private static float P(string s) { return float.Parse(s, System.Globalization.CultureInfo.InvariantCulture); }
        private static string V(Vector3 v) { return F(v.x) + "," + F(v.y) + "," + F(v.z); }
        private static Vector3 ParseV(string s) { string[] a = s.Split(','); return new Vector3(P(a[0]), P(a[1]), P(a[2])); }

        public List<string> WallPaintList()
        {
            var list = new List<string>();
            foreach (KeyValuePair<string, string> kv in _wallPaints) list.Add(kv.Key + "=" + kv.Value);
            foreach (PaintPatch p in _patches)
            {
                var runs = new System.Text.StringBuilder();
                foreach (Vector3Int r in p.Runs) runs.Append(r.x).Append(':').Append(r.y).Append(':').Append(r.z).Append(';');
                list.Add("P|" + p.Item + "|" + V(p.O) + "|" + V(p.N) + "|" + V(p.T) + "|" + F(p.Cell) + "|" + p.Order + "|" + runs);
            }
            return list;
        }

        public void SetWallPaints(List<string> list)
        {
            _wallPaints.Clear();
            ClearPatches();
            if (list != null)
                foreach (string e in list)
                {
                    try
                    {
                        if (e.StartsWith("P|"))
                        {
                            string[] f = e.Split('|');
                            var p = new PaintPatch { Item = f[1], O = ParseV(f[2]), N = ParseV(f[3]), T = ParseV(f[4]), Cell = P(f[5]), Order = int.Parse(f[6]) };
                            foreach (string r in f[7].Split(';'))
                            {
                                if (r.Length == 0) continue;
                                string[] a = r.Split(':');
                                p.Runs.Add(new Vector3Int(int.Parse(a[0]), int.Parse(a[1]), int.Parse(a[2])));
                            }
                            _patches.Add(p);
                            continue;
                        }
                        int k = e.IndexOf('=');
                        if (k > 0 && !e.Contains("|in=")) _wallPaints[e.Substring(0, k)] = e.Substring(k + 1);   // (older saves painted whole inside walls: dropped)
                    }
                    catch (System.Exception ex) { Debug.LogWarning("[Paint] a saved paint entry could not be read: " + ex.Message); }
                }
            ApplyWallPaints(VisualRoot);
        }

        private void ClearPatches()
        {
            foreach (PaintPatch p in _patches) if (p.Go != null) Destroy(p.Go);
            _patches.Clear();
        }

        private static bool IsWallRoot(string n) { return n == "Wall_Front" || n == "Wall_Back" || n == "Wall_Left" || n == "Wall_Right"; }

        private static Transform WallRootOf(Transform t, Transform stop)
        {
            for (; t != null && t != stop; t = t.parent) if (IsWallRoot(t.name)) return t;
            return null;
        }

        private static bool IsDoorName(string n) { return n == "DoorHinge" || n.StartsWith("DoorHinge_") || n.StartsWith("DoorSlide_") || n.StartsWith("DoorRoll_"); }

        /// <summary>The door object (hinge, slide or roll node) a collider belongs to, or null.</summary>
        private static Transform DoorRootOf(Transform t, Transform stop)
        {
            for (; t != null && t != stop; t = t.parent) if (IsDoorName(t.name)) return t;
            return null;
        }

        private static string Plain(string n)
        {
            int k = n.IndexOf(" (Instance)", System.StringComparison.Ordinal);
            return k >= 0 ? n.Substring(0, k) : n;
        }

        private static bool OutsideMaterial(string n) { return n.StartsWith("Siding") || n.StartsWith("Log"); }
        private static bool InsideMaterial(string n) { return n.StartsWith("Interior"); }
        private static bool DoorMaterial(string n) { return n.StartsWith("Door"); }
        private static bool ShutterMaterial(string n) { return n.StartsWith("Shutter"); }

        private void ApplyWallPaints(Transform root)
        {
            if (root == null) return;
            foreach (KeyValuePair<string, string> kv in _wallPaints)
            {
                AssetCatalogItem paint = HudBindings.GetCatalogItem(kv.Value);
                if (paint == null) continue;
                if (kv.Key.StartsWith("Door:"))
                {
                    string door = kv.Key.Substring(5);
                    foreach (Transform t in root.GetComponentsInChildren<Transform>(true))
                        if (t.name == door) { StructureLook.Paint(t.GetComponentsInChildren<Renderer>(true), DoorMaterial, paint); break; }
                    continue;
                }
                if (kv.Key.StartsWith("Shutter:"))
                {
                    string wallName = kv.Key.Substring(8);
                    foreach (Transform t in root.GetComponentsInChildren<Transform>(true))
                        if (t.name == wallName && IsWallRoot(t.name)) { StructureLook.Paint(t.GetComponentsInChildren<Renderer>(true), ShutterMaterial, paint); break; }
                    continue;
                }
                string[] parts = kv.Key.Split('|');
                if (parts.Length != 2 || parts[1] != "out") continue;
                foreach (Transform t in root.GetComponentsInChildren<Transform>(true))
                    if (t.name == parts[0] && IsWallRoot(t.name)) { StructureLook.Paint(t.GetComponentsInChildren<Renderer>(true), OutsideMaterial, paint); break; }
            }
            foreach (PaintPatch p in _patches) BuildPatch(p, root);
        }

        /// <summary>Lays a patch as quads on the model: one per run of cells, a hair off the wall (newer patches a hair further).</summary>
        private void BuildPatch(PaintPatch p, Transform root)
        {
            AssetCatalogItem paint = HudBindings.GetCatalogItem(p.Item);
            if (paint == null || p.Runs.Count == 0) return;
            if (p.Go != null) Destroy(p.Go);
            Vector3 n = transform.TransformDirection(p.N), t = transform.TransformDirection(p.T), o = transform.TransformPoint(p.O);
            o += n * (0.008f + 0.002f * Mathf.Min(p.Order, 20));   // (a hair off the wall: far enough that the depth buffer keeps it apart from the wall at any zoom)
            var verts = new List<Vector3>();
            var tris = new List<int>();
            foreach (Vector3Int r in p.Runs)
            {
                Vector3 a = o + t * (r.y * p.Cell) + Vector3.up * (r.x * p.Cell);
                Vector3 b = a + t * ((r.z - r.y + 1) * p.Cell);
                Vector3 up = Vector3.up * p.Cell;
                int i = verts.Count;
                verts.Add(root.InverseTransformPoint(a)); verts.Add(root.InverseTransformPoint(b));
                verts.Add(root.InverseTransformPoint(b + up)); verts.Add(root.InverseTransformPoint(a + up));
                tris.AddRange(new[] { i, i + 1, i + 2, i, i + 2, i + 3 });
            }
            var mesh = new Mesh { name = "PaintPatch" };
            mesh.SetVertices(verts);
            var nrm = new Vector3[verts.Count];
            Vector3 nLocal = root.InverseTransformDirection(n);
            for (int k = 0; k < nrm.Length; k++) nrm[k] = nLocal;
            // Each quad is wound so it faces out of the wall, and only that way is drawn (Cull Back): paint on the inside of a wall can not be seen from outside through it.
            for (int q = 0; q + 5 < tris.Count; q += 6)
            {
                Vector3 f = Vector3.Cross(verts[tris[q + 1]] - verts[tris[q]], verts[tris[q + 2]] - verts[tris[q]]);
                if (Vector3.Dot(f, nLocal) < 0f)
                {
                    (tris[q + 1], tris[q + 2]) = (tris[q + 2], tris[q + 1]);
                    (tris[q + 4], tris[q + 5]) = (tris[q + 5], tris[q + 4]);
                }
            }
            mesh.SetTriangles(tris, 0);
            mesh.normals = nrm;
            mesh.RecalculateBounds();
            p.Go = new GameObject("PaintPatch");
            p.Go.transform.SetParent(root, false);
            p.Go.AddComponent<MeshFilter>().sharedMesh = mesh;
            var mr = p.Go.AddComponent<MeshRenderer>();
            var mat = new Material(Shader.Find("Universal Render Pipeline/Lit")) { hideFlags = HideFlags.DontSave };
            Color c = Color.white;
            ColorUtility.TryParseHtmlString(paint.look_color, out c);
            mat.SetColor("_BaseColor", c);
            mat.SetFloat("_Smoothness", paint.look_smoothness);
            mat.SetFloat("_Metallic", paint.look_metallic);
            mat.SetFloat("_Cull", 2f);                      // seen from the front only (see the winding above)
            mr.sharedMaterial = mat;
            mr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
        }

        private static readonly RaycastHit[] s_rayBuf = new RaycastHit[24];

        /// <summary>A collider the paint passes over: people, placed things, window panes and doors (a door is painted as a door).</summary>
        private bool Ignorable(Collider col)
        {
            if (col.GetComponentInParent<PedController>() != null || col.GetComponentInParent<PlacedObject>() != null || col.GetComponentInParent<WorldItem>() != null) return true;
            for (Transform t = col.transform; t != null && t != transform; t = t.parent)
                if (t.name == "WindowGlass" || t.name.StartsWith("Door") || t.name.StartsWith("RollLeaf")) return true;
            return false;
        }

        /// <summary>True when there is wall face at a cell centre: a ray from just in front of it, straight at the wall, meets this building's wall near.</summary>
        private bool WallAt(Vector3 center, Vector3 n)
        {
            int count = Physics.RaycastNonAlloc(center + n * 0.12f, -n, s_rayBuf, 0.3f, Physics.DefaultRaycastLayers, QueryTriggerInteraction.Ignore);
            float best = float.MaxValue;
            int bi = -1;
            for (int i = 0; i < count; i++)
            {
                if (Ignorable(s_rayBuf[i].collider)) continue;
                if (s_rayBuf[i].distance < best) { best = s_rayBuf[i].distance; bi = i; }
            }
            if (bi < 0 || best < 0.04f || best > 0.2f || Vector3.Dot(s_rayBuf[bi].normal, n) < 0.7f) return false;
            return s_rayBuf[bi].collider.GetComponentInParent<ConstructionSite>() == this;
        }

        private PaintPatch MakePatch(RaycastHit hit, string itemId)
        {
            Vector3 n = hit.normal;
            n.y = 0f;
            if (n.sqrMagnitude < 0.25f) return null;
            n.Normalize();
            Vector3 t = Vector3.Cross(Vector3.up, n);
            float c = PaintCell;
            // the floor under the click is row 0
            float yf = hit.point.y - 0.01f;
            int fc = Physics.RaycastNonAlloc(hit.point + n * 0.12f + Vector3.up * 0.15f, Vector3.down, s_rayBuf, 6f, Physics.DefaultRaycastLayers, QueryTriggerInteraction.Ignore);
            float fbest = float.MaxValue;
            for (int i = 0; i < fc; i++)
                if (!Ignorable(s_rayBuf[i].collider) && s_rayBuf[i].distance < fbest && s_rayBuf[i].normal.y > 0.5f) { fbest = s_rayBuf[i].distance; yf = s_rayBuf[i].point.y; }
            Vector3 origin = new Vector3(hit.point.x, yf, hit.point.z) - t * (c * 0.5f);
            int startRow = Mathf.Max(0, Mathf.FloorToInt((hit.point.y - yf) / c));
            Vector3 CenterOf(int k, int r) { return origin + t * ((k + 0.5f) * c) + Vector3.up * ((r + 0.5f) * c); }

            var known = new Dictionary<long, bool>();
            bool Valid(int k, int r)
            {
                if (k < -90 || k > 90 || r < 0 || r > 120) return false;
                long key = ((long)(k + 100) << 16) | (long)r;
                if (!known.TryGetValue(key, out bool v)) { v = WallAt(CenterOf(k, r), n); known[key] = v; }
                return v;
            }
            if (!Valid(0, startRow)) return null;

            var rows = new SortedDictionary<int, List<int>>();
            var seen = new HashSet<long>();
            var queue = new Queue<Vector2Int>();
            queue.Enqueue(new Vector2Int(0, startRow));
            seen.Add(((long)100 << 16) | (long)startRow);
            int total = 0;
            while (queue.Count > 0 && total < 9000)
            {
                Vector2Int q = queue.Dequeue();
                if (!rows.TryGetValue(q.y, out List<int> ks)) { ks = new List<int>(); rows[q.y] = ks; }
                ks.Add(q.x);
                total++;
                foreach (Vector2Int d in new[] { new Vector2Int(1, 0), new Vector2Int(-1, 0), new Vector2Int(0, 1), new Vector2Int(0, -1) })
                {
                    var nb = new Vector2Int(q.x + d.x, q.y + d.y);
                    long key = ((long)(nb.x + 100) << 16) | (long)nb.y;
                    if (nb.y < 0 || nb.x < -90 || nb.x > 90 || nb.y > 120 || !seen.Add(key)) continue;
                    if (Valid(nb.x, nb.y)) queue.Enqueue(nb);
                }
            }
            var patch = new PaintPatch { Item = itemId, Cell = c, Order = _patches.Count };
            patch.O = transform.InverseTransformPoint(origin);
            patch.N = transform.InverseTransformDirection(n);
            patch.T = transform.InverseTransformDirection(t);
            foreach (KeyValuePair<int, List<int>> row in rows)
            {
                row.Value.Sort();
                int start = row.Value[0], prev = start;
                for (int i = 1; i <= row.Value.Count; i++)
                {
                    if (i < row.Value.Count && row.Value[i] == prev + 1) { prev = row.Value[i]; continue; }
                    patch.Runs.Add(new Vector3Int(row.Key, start, prev));
                    if (i < row.Value.Count) { start = row.Value[i]; prev = start; }
                }
            }
            return patch;
        }

        private static string DoorLabel(string door) { return door == "DoorHinge" ? "the front door" : "that door"; }

        /// <summary>Paints what a ray hit with a paint item: a door, the outside of a wall, or the section of an inside wall. False when it is none of them.</summary>
        public bool TryPaint(RaycastHit hit, AssetCatalogItem paint, Transform player)
        {
            Transform root = VisualRoot;
            if (root == null || paint == null || !hit.collider.transform.IsChildOf(root)) return false;
            if (player != null && DistanceOutside(player.position) > YardM + 4f)
            {
                ToastNotificationSystem.ShowInfo("Too far", "Move closer to paint it.");
                return true;
            }
            Transform door = DoorRootOf(hit.collider.transform, root);
            if (door != null)
            {
                _wallPaints["Door:" + door.name] = paint.id;
                ApplyWallPaints(root);
                return true;
            }
            Transform wall = WallRootOf(hit.collider.transform, root);
            Renderer hr = hit.collider.GetComponent<Renderer>();
            if (wall != null && hr != null)
                foreach (Material m in hr.sharedMaterials)
                    if (m != null && ShutterMaterial(Plain(m.name)))
                    {
                        _wallPaints["Shutter:" + wall.name] = paint.id;      // the shutters are part of the wall: all of that wall's shutters
                        ApplyWallPaints(root);
                        return true;
                    }
            Vector3 o = hit.point - transform.position, n = hit.normal;
            o.y = 0f; n.y = 0f;
            if (wall != null && Vector3.Dot(o, n) > 0f)
            {
                _wallPaints[wall.name + "|out"] = paint.id;      // the outside: the whole wall
                ApplyWallPaints(root);
                return true;
            }
            Renderer r = hit.collider.GetComponent<Renderer>();
            bool interior = wall != null;
            if (r != null)
                foreach (Material m in r.sharedMaterials)
                {
                    if (m == null) continue;
                    if (InsideMaterial(Plain(m.name))) interior = true;
                    if (Plain(m.name).StartsWith("Log")) return false;          // the logs of a log wall are not painted
                }
            if (!interior || Mathf.Abs(hit.normal.y) > 0.35f) return false;       // not a wall face (floor, roof, trim)
            PaintPatch patch = MakePatch(hit, paint.id);
            if (patch == null || patch.Runs.Count == 0)
            {
                ToastNotificationSystem.ShowInfo(Name(), "That spot can't be painted.");
                return true;
            }
            _patches.Add(patch);
            BuildPatch(patch, root);
            return true;
        }

        /// <summary>A right click with a paint can: paints the wall of the building under the cursor. False when nothing paintable is there.</summary>
        public static bool TryPaintAtRay(Ray ray, string paintItemId, Transform player)
        {
            AssetCatalogItem paint = HudBindings.GetCatalogItem(paintItemId);
            if (paint == null) return false;
            RaycastHit[] hits = Physics.RaycastAll(ray, 1000f, Physics.DefaultRaycastLayers, QueryTriggerInteraction.Ignore);
            System.Array.Sort(hits, (a, b) => a.distance.CompareTo(b.distance));
            foreach (RaycastHit h in hits)
            {
                if (h.collider.GetComponentInParent<PedController>() != null) continue;
                ConstructionSite cs = h.collider.GetComponentInParent<ConstructionSite>();
                return cs != null && cs.TryPaint(h, paint, player);   // the first thing hit decides
            }
            return false;
        }

        private void RememberLooks(LineStatus l)
        {
            var ids = new List<string>();
            foreach (PlacedObject o in l.Matches) if (o != null) ids.Add(o.ItemId);
            foreach (Draw dr in l.Draws) ids.Add(dr.ItemId);
            foreach (WorldItem w in l.Loose) if (w != null) ids.Add(w.ItemId);
            foreach (string id in ids)
            {
                AssetCatalogItem pump = HudBindings.GetCatalogItem(id);
                if (pump != null && pump.flow_lph > 0f) PumpId = id;   // a well remembers the pump that went down it
            }
            foreach (string id in ids)
            {
                if (!StructureLook.TryLook(id, out AssetCatalogItem item)) continue;
                // an item replaces whatever set the same parts before it (new bricks over old for the chimney, new paint over old)
                _lookItems.RemoveAll(e => StructureLook.TryLook(e, out AssetCatalogItem other) && SharesPart(item, other));
                _lookItems.Add(id);
            }
        }

        private static bool SharesPart(AssetCatalogItem a, AssetCatalogItem b)
        {
            foreach (string p in a.look_target.Split(',')) if (StructureLook.Styles(b, p.Trim())) return true;
            return false;
        }

        /// <summary>The item ids that will pay for the stage being built.</summary>
        private List<string> PayerIds()
        {
            var ids = new List<string>();
            if (_status == null) return ids;
            foreach (LineStatus l in PayingLeaves(_status))
            {
                foreach (PlacedObject o in l.Matches) if (o != null) ids.Add(o.ItemId);
                foreach (Draw dr in l.Draws) ids.Add(dr.ItemId);
                foreach (WorldItem w in l.Loose) if (w != null) ids.Add(w.ItemId);
            }
            return ids;
        }

        private bool _buildStilts;   // the foundation being built stands on stilts: the ground is not graded for it

        private bool Stilted => _buildStilts || StructureLook.FoundationStyle(_lookItems) == "stilts";

        // ------------------------------------------------------------------ foundation styles

        /// <summary>
        /// Foundation items other than cement make a different foundation (block, brick, stilts): the stage model's "Foundation" object is hidden
        /// and the variant model (struct_foundation_&lt;id&gt;_&lt;style&gt;) stands in its place.
        /// </summary>
        private void ShowFoundationVariant(Transform model)
        {
            string style = StructureLook.FoundationStyle(_lookItems);
            if (style == null || _stages == null || _stages.Count == 0) return;
            string variantId = _stages[0].item_id + "_" + style;
            if (!ItemRegistry.TryGet(variantId, out ItemRegistry.ItemInfo info) || info.Prefab == null) return;
            foreach (Transform t in model.GetComponentsInChildren<Transform>(true))
            {
                if (t.name != "Foundation") continue;
                foreach (Renderer r in t.GetComponentsInChildren<Renderer>(true)) r.enabled = false;
                foreach (Collider c in t.GetComponentsInChildren<Collider>(true)) c.enabled = false;
            }
            StartCoroutine(AddFoundationVariant(info.Prefab, model.parent));
        }

        private System.Collections.IEnumerator AddFoundationVariant(GameObject prefab, Transform parent)
        {
            GlbTemplate glb = prefab.GetComponent<GlbTemplate>();
            while (glb != null && !glb.Ready)
            {
                glb.EnsureLoading();
                if (glb.Failed) yield break;
                yield return null;
            }
            if (parent == null) yield break;
            GameObject inst = Instantiate(prefab, parent);
            inst.SetActive(true);
            inst.transform.localRotation = Quaternion.identity;
            Vector3 pos = Vector3.zero;
            foreach (Transform t in inst.GetComponentsInChildren<Transform>(true))
                if (t.name == "GroundLevel") { pos.y = -t.localPosition.y; break; }   // stilts are modelled with the ground part way up their piles
            inst.transform.localPosition = pos;
            StructureLook.Apply(inst.transform, _lookItems);
        }

        public bool DoorOpen { get; private set; }

        // the fireplace of a finished building (see Fireplace.cs): the fuel in it, in game minutes, and whether it burns. Saved with the site.
        public Fireplace Fireplace { get; private set; }
        public float FuelMinutes;
        public bool FireLit;

        // storage built into a finished structure (a grain silo: the structure's manifest has a container block): what is in it, saved with the site
        public readonly List<ContainerStack> Contents = new List<ContainerStack>();
        public bool IsStorage => Finished && ContainerRules.Capacity(StructureId) > 0f;
        public float StorageCapacityKg => ContainerRules.Capacity(StructureId);
        public float StorageUsedKg => ContainerRules.Used(Contents);

        /// <summary>One line for a toast: how full it is and what is in it.</summary>
        public string StorageSummary()
        {
            string what = "";
            foreach (ContainerStack c in Contents)
                if (c.Count > 0) what += (what.Length > 0 ? ", " : "") + c.Count + "x " + HudBindings.GetItemName(c.ItemId);
            return UnitFormat.WeightPair(StorageUsedKg, StorageCapacityKg) + (what.Length > 0 ? "  (" + what + ")" : "  (empty)");
        }
        public bool HasDoor => _hinge != null;

        // Interior doors: objects of a finished model that a right click opens. "DoorHinge_<n>" (a leaf "DoorLeaf_<n>" as its child) swings like the front
        // door; "DoorSlide_<n>" slides along the wall by the position of its child "SlideTo..." (barn doors, stall doors); "DoorRoll_<n>" rolls up
        // into its header (garage doors: its origin is the top edge, so it is squashed upwards). A closed leaf is solid, an open or moving one is not.
        // Their open state is saved with the site (openDoors) and applied as the model loads.
        private sealed class InteriorDoor
        {
            public Transform Hinge;
            public int Kind;                         // 0 swings, 1 slides, 2 rolls up
            public Quaternion Closed;
            public float Sign = 1f, Angle;           // swing: the way it turns and how far (degrees)
            public Vector3 ClosedPos, Offset, ClosedScale;   // slide: where it rests and how far it travels; roll: its shut scale
            public float T;                          // slide and roll: 0 shut to 1 open
            public bool Open;
            public Collider[] Leaf;
            public Bounds ClosedBounds;              // the leaf while shut, in the world: the doorway
            public float Progress { get { return Kind == 0 ? Angle / DoorOpenDegrees : T; } }
        }

        private readonly List<InteriorDoor> _interior = new List<InteriorDoor>();

        // Which interior doors stand open, by the name of the door object in the model. Saved with the site (openDoors) and applied as the model loads.
        private readonly HashSet<string> _openDoors = new HashSet<string>();

        public List<string> OpenDoorList() { return new List<string>(_openDoors); }

        public void SetOpenDoors(List<string> names)
        {
            _openDoors.Clear();
            if (names != null) foreach (string n in names) _openDoors.Add(n);
            foreach (InteriorDoor d in _interior) if (d.Hinge != null) SnapInterior(d, _openDoors.Contains(d.Hinge.name));   // the model is already showing
        }

        private void SetInteriorOpen(InteriorDoor d, bool open)
        {
            d.Open = open;
            if (open) _openDoors.Add(d.Hinge.name); else _openDoors.Remove(d.Hinge.name);
        }

        /// <summary>Puts a door straight into its open or shut state (no animation): a building that loads with its doors as they were left.</summary>
        private static void SnapInterior(InteriorDoor d, bool open)
        {
            d.Open = open;
            if (d.Kind == 0)
            {
                d.Angle = open ? DoorOpenDegrees : 0f;
                d.Hinge.localRotation = d.Closed * Quaternion.AngleAxis(d.Sign * d.Angle, Vector3.up);
            }
            else
            {
                d.T = open ? 1f : 0f;
                if (d.Kind == 1) d.Hinge.localPosition = d.ClosedPos + d.Offset * d.T;
                else d.Hinge.localScale = new Vector3(d.ClosedScale.x, Mathf.Lerp(d.ClosedScale.y, d.ClosedScale.y * RolledScale, d.T), d.ClosedScale.z);
            }
        }
        private const float InteriorReach = 2f;   // a door answers only within 2 m of the player (measured to the door, not the building)
        private Bounds _hingeBounds;
        private const float SlideSeconds = 1.6f, RollSeconds = 2.4f, RolledScale = 0.06f;

        /// <summary>Distance on the ground from a point to a box (0 inside it).</summary>
        private static float FlatDistance(Bounds b, Vector3 p)
        {
            float dx = Mathf.Max(b.min.x - p.x, 0f, p.x - b.max.x), dz = Mathf.Max(b.min.z - p.z, 0f, p.z - b.max.z);
            return Mathf.Sqrt(dx * dx + dz * dz);
        }

        private void FindInteriorDoors(Transform model)
        {
            _interior.Clear();
            foreach (Transform t in model.GetComponentsInChildren<Transform>(true))
            {
                int kind = t.name.StartsWith("DoorHinge_") ? 0 : t.name.StartsWith("DoorSlide_") ? 1 : t.name.StartsWith("DoorRoll_") ? 2 : -1;
                if (kind < 0) continue;
                // the leaf meshes inside a door (and their parts) carry names that start the same way: only the door itself counts
                bool inside = false;
                for (Transform up = t.parent; up != null && up != model; up = up.parent)
                    if (up.name.StartsWith("DoorHinge_") || up.name.StartsWith("DoorSlide_") || up.name.StartsWith("DoorRoll_")) { inside = true; break; }
                if (inside) continue;
                var door = new InteriorDoor { Hinge = t, Kind = kind, Closed = t.localRotation, ClosedPos = t.localPosition, ClosedScale = t.localScale, Leaf = t.GetComponentsInChildren<Collider>(true) };
                Renderer leaf = t.GetComponentInChildren<Renderer>(true);
                door.ClosedBounds = leaf != null ? leaf.bounds : new Bounds(t.position, Vector3.one * 0.5f);
                if (kind == 1)
                {
                    foreach (Transform child in t)
                        if (child.name.StartsWith("SlideTo")) { door.Offset = child.localPosition; break; }
                }
                if (kind == 0 && leaf != null)
                {
                    // swing towards the front of the building, like the front door
                    Vector3 arm = leaf.bounds.center - t.position;
                    arm.y = 0f;
                    Vector3 front = transform.TransformDirection(s_front.sqrMagnitude > 0.01f ? s_front.normalized : Vector3.back);
                    front.y = 0f;
                    float plus = Vector3.Dot(Quaternion.AngleAxis(DoorOpenDegrees, Vector3.up) * arm, front);
                    float minus = Vector3.Dot(Quaternion.AngleAxis(-DoorOpenDegrees, Vector3.up) * arm, front);
                    door.Sign = plus >= minus ? 1f : -1f;
                }
                _interior.Add(door);
                if (_openDoors.Contains(t.name)) SnapInterior(door, true);   // left open: it loads open
            }
            if (_interior.Count > 0) Debug.Log("[Doors] " + Name() + ": " + _interior.Count + " openable door(s) found (swing, slide, roll-up).");
        }

        private void AnimateInteriorDoors()
        {
            foreach (InteriorDoor d in _interior)
            {
                if (d.Hinge == null) continue;
                if (d.Kind == 0)
                {
                    float target = d.Open ? DoorOpenDegrees : 0f;
                    if (!Mathf.Approximately(d.Angle, target))
                    {
                        d.Angle = Mathf.MoveTowards(d.Angle, target, DoorSwingSpeed * Time.deltaTime);
                        d.Hinge.localRotation = d.Closed * Quaternion.AngleAxis(d.Sign * d.Angle, Vector3.up);
                    }
                }
                else
                {
                    float target = d.Open ? 1f : 0f;
                    if (!Mathf.Approximately(d.T, target))
                    {
                        d.T = Mathf.MoveTowards(d.T, target, Time.deltaTime / (d.Kind == 1 ? SlideSeconds : RollSeconds));
                        float e = Mathf.SmoothStep(0f, 1f, d.T);
                        if (d.Kind == 1) d.Hinge.localPosition = d.ClosedPos + d.Offset * e;
                        else d.Hinge.localScale = new Vector3(d.ClosedScale.x, Mathf.Lerp(d.ClosedScale.y, d.ClosedScale.y * RolledScale, e), d.ClosedScale.z);
                    }
                }
                // the leaf blocks only while it is shut, and this is enforced every frame (not only while it moves), with the colliders looked up
                // again when none were found at the start: a leaf's collider that was added after the model was found must not stay solid
                if (d.Leaf == null || d.Leaf.Length == 0) d.Leaf = d.Hinge.GetComponentsInChildren<Collider>(true);
                bool solid = !d.Open && d.Progress <= 0.005f;
                foreach (Collider c in d.Leaf) if (c != null && c.enabled != solid) c.enabled = solid;
            }
        }

        /// <summary>
        /// A right click aimed at an interior door (its leaf, or the doorway while it stands open) opens or shuts it, whatever stage the building is at:
        /// the click goes to the door first, so it is never taken for "build the next stage".
        /// </summary>
        private InteriorDoor DoorAimedAt(Ray ray)
        {
            InteriorDoor hit = null;
            float bestT = float.MaxValue;
            foreach (InteriorDoor d in _interior)
            {
                if (d.Hinge == null) continue;
                Renderer leaf = d.Hinge.GetComponentInChildren<Renderer>(true);
                if (leaf == null) continue;
                // the leaf in its closed place (open, it stands against the wall or is rolled away): the doorway is what the player aims at
                Bounds b = d.ClosedBounds;
                if (d.Progress > 0.02f) b.Encapsulate(leaf.bounds);
                b.Expand(0.08f);   // the door itself, not the wall around it
                if (b.IntersectRay(ray, out float t) && t < bestT) { bestT = t; hit = d; }
            }
            return hit;
        }

        /// <summary>True when the cursor is on a door of this building that a right click would work from where the player stands (the cursor shows the hand).</summary>
        public bool DoorUnderCursor(Ray ray, Vector3 playerPos)
        {
            InteriorDoor inner = DoorAimedAt(ray);
            if (inner != null) return FlatDistance(inner.ClosedBounds, playerPos) <= InteriorReach;
            if (Finished && _hinge != null)
            {
                Renderer r = _hinge.GetComponentInChildren<Renderer>(true);
                if (r != null)
                {
                    if (MainDoorBounds().IntersectRay(ray, out float t) && FlatDistance(_hingeBounds, playerPos) <= InteriorReach) return true;
                }
            }
            return false;
        }

        /// <summary>
        /// What a click on the front door must hit: the doorway (the leaf where it hangs shut) and the leaf where it is now, so an open door
        /// can be shut by clicking the leaf standing open or the empty doorway. Padded sideways so a thin door is not hard to hit.
        /// </summary>
        private Bounds MainDoorBounds()
        {
            Bounds b = _hingeBounds;
            if (_hinge != null && _doorAngle > 0.5f)
            {
                Renderer leaf = _hinge.GetComponentInChildren<Renderer>(true);
                if (leaf != null) b.Encapsulate(leaf.bounds);
            }
            b.Expand(new Vector3(0.2f, 0.1f, 0.2f));
            return b;
        }

        /// <summary>The ray reaches the door box without a wall of the building in front of it (the door's own leaf does not count).</summary>
        private bool DoorNotHiddenBehindWall(Ray ray, float doorDistance)
        {
            // the casing, trim and cladding around a door stand up to a few tens of centimetres proud of it: only something further in front than that hides it
            RaycastHit[] hits = Physics.RaycastAll(ray, Mathf.Max(0f, doorDistance - 0.7f), Physics.DefaultRaycastLayers, QueryTriggerInteraction.Ignore);
            foreach (RaycastHit h in hits)
            {
                if (h.collider.GetComponentInParent<PedController>() != null) continue;
                if (_hinge != null && h.collider.transform.IsChildOf(_hinge)) continue;
                if (h.collider.GetComponentInParent<ConstructionSite>() == this) return false;
            }
            return true;
        }

        public bool TryDoorAtCursor(Ray ray, Transform player)
        {
            InteriorDoor hit = DoorAimedAt(ray);
            if (hit == null)
            {
                // the front door: only a click on the door itself (its leaf in the doorway) works it
                if ((Finished || HasDoor) && _hinge != null)
                {
                    if (MainDoorBounds().IntersectRay(ray, out float t) && DoorNotHiddenBehindWall(ray, t)) return ToggleDoor(player);
                }
                return false;
            }
            if (player != null)
            {
                if (FlatDistance(hit.ClosedBounds, player.position) > InteriorReach)
                {
                    ToastNotificationSystem.ShowInfo("Too far", "Move closer to the door.");
                    return true;
                }
                if (hit.Open && FlatDistance(hit.ClosedBounds, player.position) < 0.45f)
                {
                    ToastNotificationSystem.ShowInfo(Name(), "Step away from the doorway first.");
                    return true;
                }
            }
            SetInteriorOpen(hit, !hit.Open);
            return true;
        }

        /// <summary>The interior door nearest to a point within reach, or null.</summary>
        private InteriorDoor NearestInteriorDoor(Vector3 p)
        {
            InteriorDoor best = null;
            float bestD = InteriorReach;
            foreach (InteriorDoor d in _interior)
            {
                if (d.Hinge == null) continue;
                float dist = FlatDistance(d.ClosedBounds, p);
                if (dist < bestD) { bestD = dist; best = d; }
            }
            return best;
        }

        private void FindDoor(Transform model)
        {
            _hinge = null;
            FindInteriorDoors(model);
            foreach (Transform t in model.GetComponentsInChildren<Transform>(true))
                if (t.name == "DoorHinge") { _hinge = t; break; }
            if (_hinge == null) return;
            _hingeClosed = _hinge.localRotation;
            _leafColliders = _hinge.GetComponentsInChildren<Collider>(true);

            // it swings OUTWARD: the way that carries the leaf towards the front of the building
            Renderer leaf = _hinge.GetComponentInChildren<Renderer>(true);
            _hingeBounds = leaf != null ? leaf.bounds : new Bounds(_hinge.position, Vector3.one * 0.5f);
            if (leaf != null)
            {
                Vector3 arm = leaf.bounds.center - _hinge.position;
                arm.y = 0f;
                Vector3 front = transform.TransformDirection(s_front.sqrMagnitude > 0.01f ? s_front.normalized : Vector3.back);
                front.y = 0f;
                float plus = Vector3.Dot(Quaternion.AngleAxis(DoorOpenDegrees, Vector3.up) * arm, front);
                float minus = Vector3.Dot(Quaternion.AngleAxis(-DoorOpenDegrees, Vector3.up) * arm, front);
                _swingSign = plus >= minus ? 1f : -1f;
            }
            _doorAngle = DoorOpen ? DoorOpenDegrees : 0f;
            _hinge.localRotation = _hingeClosed * Quaternion.AngleAxis(_swingSign * _doorAngle, Vector3.up);
            SetLeafSolid(_doorAngle <= 0.5f);
        }

        /// <summary>The leaf blocks only while it is shut: open or swinging it has no collider, so it can never trap the player or push them about.</summary>
        private void SetLeafSolid(bool solid)
        {
            if ((_leafColliders == null || _leafColliders.Length == 0) && _hinge != null) _leafColliders = _hinge.GetComponentsInChildren<Collider>(true);
            if (_leafColliders == null) return;
            foreach (Collider c in _leafColliders) if (c != null && c.enabled != solid) c.enabled = solid;
        }

        private void AnimateDoor()
        {
            AnimateInteriorDoors();
            if (_hinge == null) return;
            float target = DoorOpen ? DoorOpenDegrees : 0f;
            if (Mathf.Approximately(_doorAngle, target)) { if (DoorOpen) SetLeafSolid(false); return; }
            _doorAngle = Mathf.MoveTowards(_doorAngle, target, DoorSwingSpeed * Time.deltaTime);
            _hinge.localRotation = _hingeClosed * Quaternion.AngleAxis(_swingSign * _doorAngle, Vector3.up);
            SetLeafSolid(_doorAngle <= 0.5f);
        }

        /// <summary>Opens or closes the door of a finished building (a right click on it, within reach). The shape of the door opening is part of the walls, so open it to walk in.</summary>
        public bool ToggleDoor(Transform player)
        {
            if (_hinge == null) { ToastNotificationSystem.ShowInfo(Name(), "This structure is finished."); return false; }
            if (player != null && FlatDistance(_hingeBounds, player.position) > InteriorReach)
            {
                ToastNotificationSystem.ShowInfo("Too far", "Move closer to the door.");
                return false;
            }
            if (DoorOpen && player != null)
            {
                // never shut it on someone standing in the doorway
                // only when the player stands in the doorway itself (the door is within reach, so 1.5 m round it would make it impossible to shut)
                if (FlatDistance(_hingeBounds, player.position) < 0.45f) { ToastNotificationSystem.ShowInfo(Name(), "Step away from the doorway first."); return false; }
            }
            SetDoor(!DoorOpen);
            return true;
        }

        public void SetDoor(bool open)
        {
            DoorOpen = open;
        }

        private void BuildStandIn(ConstructionStageData stage, Transform parent)
        {
            float w = Mathf.Max(0.5f, stage.width > 0f ? stage.width : _foot.x), d = Mathf.Max(0.5f, stage.depth > 0f ? stage.depth : _foot.y);
            float h = Mathf.Max(0.1f, stage.height);
            string n = (stage.name ?? "").ToLowerInvariant();
            Color concrete = new Color(0.62f, 0.62f, 0.6f), timber = new Color(0.72f, 0.56f, 0.34f), wall = new Color(0.66f, 0.5f, 0.32f), roof = new Color(0.34f, 0.2f, 0.16f);
            if (n.StartsWith("found"))
            {
                Box(parent, "Slab", Vector3.zero, new Vector3(w, h, d), concrete, true);
            }
            else if (n.StartsWith("fram"))
            {
                Box(parent, "Slab", Vector3.zero, new Vector3(w, _stages[0].height, d), concrete, true);
                float post = 0.14f;
                float fh = h;
                for (float x = -w * 0.5f; x <= w * 0.5f + 0.01f; x += Mathf.Max(1.2f, w / Mathf.Max(1, Mathf.FloorToInt(w / 1.5f))))
                    foreach (float z in new[] { -d * 0.5f + post * 0.5f, d * 0.5f - post * 0.5f })
                        Box(parent, "Post", new Vector3(Mathf.Clamp(x, -w * 0.5f + post * 0.5f, w * 0.5f - post * 0.5f), _stages[0].height, z), new Vector3(post, fh, post), timber, false);
                foreach (float x in new[] { -w * 0.5f + post * 0.5f, w * 0.5f - post * 0.5f })
                    for (float z = -d * 0.5f; z <= d * 0.5f + 0.01f; z += Mathf.Max(1.2f, d / Mathf.Max(1, Mathf.FloorToInt(d / 1.5f))))
                        Box(parent, "Post", new Vector3(x, _stages[0].height, Mathf.Clamp(z, -d * 0.5f + post * 0.5f, d * 0.5f - post * 0.5f)), new Vector3(post, fh, post), timber, false);
                Box(parent, "TopPlateX", new Vector3(0f, _stages[0].height + fh - post, -d * 0.5f + post * 0.5f), new Vector3(w, post, post), timber, false);
                Box(parent, "TopPlateX2", new Vector3(0f, _stages[0].height + fh - post, d * 0.5f - post * 0.5f), new Vector3(w, post, post), timber, false);
                Box(parent, "TopPlateZ", new Vector3(-w * 0.5f + post * 0.5f, _stages[0].height + fh - post, 0f), new Vector3(post, post, d), timber, false);
                Box(parent, "TopPlateZ2", new Vector3(w * 0.5f - post * 0.5f, _stages[0].height + fh - post, 0f), new Vector3(post, post, d), timber, false);
            }
            else if (n.StartsWith("wall"))
            {
                Box(parent, "Slab", Vector3.zero, new Vector3(w, _stages[0].height, d), concrete, true);
                Box(parent, "Walls", new Vector3(0f, _stages[0].height, 0f), new Vector3(w, h - _stages[0].height, d), wall, true);
            }
            else
            {
                // finished, without a model: walls with a pitched roof
                Box(parent, "Slab", Vector3.zero, new Vector3(w, _stages[0].height, d), concrete, true);
                float wallH = h * 0.7f;
                Box(parent, "Walls", new Vector3(0f, _stages[0].height, 0f), new Vector3(w, wallH, d), wall, true);
                Box(parent, "Roof", new Vector3(0f, _stages[0].height + wallH, 0f), new Vector3(w * 1.05f, Mathf.Max(0.15f, h - wallH - _stages[0].height), d * 1.05f), roof, true);
            }
        }

        private static void Box(Transform parent, string name, Vector3 baseCentre, Vector3 size, Color colour, bool collider)
        {
            var go = GameObject.CreatePrimitive(PrimitiveType.Cube);
            go.name = name;
            go.transform.SetParent(parent, false);
            go.transform.localScale = size;
            go.transform.localPosition = baseCentre + Vector3.up * (size.y * 0.5f);
            var mr = go.GetComponent<MeshRenderer>();
            var mat = new Material(Shader.Find("Universal Render Pipeline/Lit")) { hideFlags = HideFlags.DontSave };
            mat.SetColor("_BaseColor", colour);
            mat.SetFloat("_Smoothness", 0.1f);
            mr.sharedMaterial = mat;
            Collider c = go.GetComponent<Collider>();
            if (c != null) { if (collider) c.enabled = true; else Destroy(c); }
        }

        // ------------------------------------------------------------------ the yard ring

        private void Update()
        {
            GradeWhileBuilding();
            AnimateDoor();
            if (_ring == null) BuildRing();
            // The yard shows while the player holds something this stage needs (or a tool for it).
            bool show = false;
            if (!Finished)
            {
                string held = HeldItemId();
                if (held != null)
                {
                    show = RecipeNeeds(CurrentStage.recipe, held);
                    if (!show) foreach (ConstructionToolGroup g in CurrentStage.tool_groups) foreach (string t in g.tools) if (Matches(t, held)) { show = true; break; }
                }
            }
            if (_ring != null && _ring.enabled != show) _ring.enabled = show;
        }

        public static string HeldItem() { return HeldItemId(); }

        private static string HeldItemId()
        {
            HudState state = HudState.Active;
            if (state == null || state.SelectedSlot < 0 || state.SelectedSlot >= state.Toolbar.Count) return null;
            ToolbarSlotData slot = state.Toolbar[state.SelectedSlot];
            return slot.Count > 0 && !string.IsNullOrEmpty(slot.IconId) ? slot.IconId : null;
        }

        private void BuildRing()
        {
            var go = new GameObject("YardRing");
            go.transform.SetParent(transform, false);
            _ring = go.AddComponent<LineRenderer>();
            _ring.useWorldSpace = false;
            _ring.loop = true;
            _ring.positionCount = 4;
            float hx = _foot.x * 0.5f + YardM, hz = _foot.y * 0.5f + YardM;
            float y = 0.12f;
            _ring.SetPositions(new[] { new Vector3(-hx, y, -hz), new Vector3(hx, y, -hz), new Vector3(hx, y, hz), new Vector3(-hx, y, hz) });
            _ring.widthMultiplier = 0.08f;
            _ring.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            var mat = new Material(Shader.Find("Universal Render Pipeline/Unlit")) { hideFlags = HideFlags.DontSave };
            Color c = new Color(1f, 0.85f, 0.45f, 1f);
            mat.SetColor("_BaseColor", c);
            _ring.material = mat;
            _ring.startColor = _ring.endColor = c;
            _ring.enabled = false;
        }

        // ------------------------------------------------------------------ picking

        /// <summary>
        /// True when a building or a placed object stands between the camera and a point `distance` along the ray: a click on a house is not a
        /// click on the bush behind it. (Hidden roofs and walls of the cutaway are on the Ignore Raycast layer, so the inside of a building stays open.)
        /// </summary>
        public static bool SolidBefore(Ray ray, float distance)
        {
            RaycastHit[] hits = Physics.RaycastAll(ray, Mathf.Max(0f, distance - 0.2f), Physics.DefaultRaycastLayers, QueryTriggerInteraction.Ignore);
            foreach (RaycastHit h in hits)
            {
                if (h.collider.GetComponentInParent<PedController>() != null) continue;
                if (h.collider.GetComponentInParent<ConstructionSite>() != null || h.collider.GetComponentInParent<PlacedObject>() != null) return true;
            }
            return false;
        }

        /// <summary>The construction site under the cursor (its dirt area or structure is the first thing hit), or null.</summary>
        public static ConstructionSite UnderCursor()
        {
            Camera cam = Camera.main != null ? Camera.main : FindAnyObjectByType<Camera>();
            if (cam == null) return null;
            if (UnityEngine.InputSystem.Mouse.current == null) return null;
            Vector2 pointer = UnityEngine.InputSystem.Mouse.current.position.ReadValue();
            RaycastHit[] hits = Homesteader.UI.HoverTarget.SortedHits(cam, pointer);
            foreach (RaycastHit h in hits)
            {
                if (h.collider == null) continue;
                if (h.collider.GetComponentInParent<PedController>() != null) continue;
                return h.collider.GetComponentInParent<ConstructionSite>();   // the first thing hit decides: a material lying on it is not the site
            }
            return null;
        }

        // ------------------------------------------------------------------ saving

        public static void Clear()
        {
            foreach (ConstructionSite s in new List<ConstructionSite>(All)) if (s != null) Destroy(s.gameObject);
        }
    }
}
