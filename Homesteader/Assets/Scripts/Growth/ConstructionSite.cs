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
        public const float YardM = 4f;

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

        public Vector2 Footprint => _foot;

        /// <summary>The model of the current stage (null before one is built or while it loads).</summary>
        public Transform VisualRoot => _visual != null ? _visual.transform : null;

        /// <summary>True when a point is within the building's footprint (on the ground plane).</summary>
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

        public sealed class LineStatus
        {
            public ConstructionLine Line;
            /// <summary>An "or" line: how each alternative stands, and which one pays (the first complete one, else the nearest to complete).</summary>
            public List<LineStatus> Options;
            public int Chosen;
            public bool IsChoice => Options != null;
            /// <summary>The line that actually pays: itself, or the chosen alternative of an "or" line.</summary>
            public LineStatus Payer => Options != null ? Options[Chosen] : this;
            public int Have;
            /// <summary>Units paid beyond the quantity (a tag line paid by an item bigger than what was left): given back as change when built.</summary>
            public float Over;
            public readonly List<PlacedObject> Matches = new List<PlacedObject>();
            /// <summary>What is taken out of containers (a box, a crate) standing in the yard: which container, which item, how many.</summary>
            public readonly List<Draw> Draws = new List<Draw>();
            /// <summary>Items lying loose on the ground in the yard (dropped, or too heavy for a box) that pay for this line.</summary>
            public readonly List<WorldItem> Loose = new List<WorldItem>();
            public bool Done => Options != null ? Options.Exists(o => o.Done) : Have >= Line.quantity;
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
        }

        public bool Finished => Stage >= _stages.Count;

        public int StageCount => _stages.Count;

        public ConstructionStageData CurrentStage => Finished ? null : _stages[Stage];

        private static bool Matches(string spec, string itemId)
        {
            if (string.IsNullOrEmpty(spec) || string.IsNullOrEmpty(itemId)) return false;
            return spec[0] == '#' ? GrowthRegistry.ToolMatches(spec, itemId) : string.Equals(spec, itemId, System.StringComparison.OrdinalIgnoreCase);
        }

        private int AlreadyDrawn(PlacedObject owner, string itemId)
        {
            int n = 0;
            if (_status == null) return 0;
            foreach (LineStatus earlier in _status)
                foreach (Draw dr in earlier.Payer.Draws) if (dr.Owner == owner && dr.ItemId == itemId) n += dr.Count;
            return n;
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
        private LineStatus EvaluateOne(ConstructionLine line, List<PlacedObject> inYard, List<WorldItem> looseInYard, HashSet<PlacedObject> used, HashSet<WorldItem> usedLoose)
        {
            var st = new LineStatus { Line = line };
            var sources = new List<Source>();
            foreach (PlacedObject o in inYard)
                if (!used.Contains(o) && Matches(line.item_id, o.ItemId))
                    sources.Add(new Source { Kind = 0, Owner = o, ItemId = o.ItemId, Available = 1, Value = GrowthRegistry.UnitValue(line.item_id, o.ItemId) });
            foreach (PlacedObject o in inYard)
            {
                if (o.Contents == null) continue;
                foreach (ContainerStack cs in o.Contents)
                {
                    if (!Matches(line.item_id, cs.ItemId)) continue;
                    int left = cs.Count - AlreadyDrawn(o, cs.ItemId);
                    if (left > 0) sources.Add(new Source { Kind = 1, Owner = o, ItemId = cs.ItemId, Available = left, Value = GrowthRegistry.UnitValue(line.item_id, cs.ItemId) });
                }
            }
            foreach (WorldItem w in looseInYard)
                if (!usedLoose.Contains(w) && Matches(line.item_id, w.ItemId))
                    sources.Add(new Source { Kind = 2, Loose = w, ItemId = w.ItemId, Available = 1, Value = GrowthRegistry.UnitValue(line.item_id, w.ItemId) });

            float need = line.quantity;
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
            st.Have = Mathf.RoundToInt(have);
            st.Over = Mathf.Max(0f, have - need);
            return st;
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
            var usedLoose = new HashSet<WorldItem>();

            // Each placed object pays for one line only (the lines are taken in order). An "or" line takes ONE alternative, in full.
            var used = new HashSet<PlacedObject>();
            foreach (ConstructionLine line in stage.recipe)
            {
                if (line.any_of != null && line.any_of.Count > 0)
                {
                    var choice = new LineStatus { Line = line, Options = new List<LineStatus>() };
                    var optUsed = new List<HashSet<PlacedObject>>();
                    var optUsedLoose = new List<HashSet<WorldItem>>();
                    foreach (ConstructionOption opt in line.any_of)
                    {
                        var u = new HashSet<PlacedObject>(used);
                        var ul = new HashSet<WorldItem>(usedLoose);
                        choice.Options.Add(EvaluateOne(new ConstructionLine { item_id = opt.item_id, quantity = Mathf.Max(1, opt.quantity) }, inYard, looseInYard, u, ul));
                        optUsed.Add(u);
                        optUsedLoose.Add(ul);
                    }
                    // the first complete alternative pays; none complete: the one nearest to it is shown
                    int best = 0;
                    float bestFrac = -1f;
                    for (int k = 0; k < choice.Options.Count; k++)
                    {
                        if (choice.Options[k].Done) { best = k; bestFrac = 2f; break; }
                        float frac = choice.Options[k].Have / (float)Mathf.Max(1, choice.Options[k].Line.quantity);
                        if (frac > bestFrac) { bestFrac = frac; best = k; }
                    }
                    choice.Chosen = best;
                    choice.Have = choice.Options[best].Have;
                    used.UnionWith(optUsed[best]);       // only the paying alternative uses things up
                    usedLoose.UnionWith(optUsedLoose[best]);
                    _status.Add(choice);
                    continue;
                }
                _status.Add(EvaluateOne(line, inYard, looseInYard, used, usedLoose));
            }

            // Tools: in the toolbar, in the yard (placed, in a box, or lying loose). They stay where they are. Every tool of a group is
            // checked, so the hover card can tick the ones that are there; the group is met when any one is.
            HudState hud = HudState.Active;
            foreach (ConstructionToolGroup group in stage.tool_groups)
            {
                var ts = new ToolStatus { Group = group };
                foreach (string tool in group.tools)
                {
                    bool has = false;
                    if (hud != null)
                        foreach (ToolbarSlotData slot in hud.Toolbar)
                            if (slot.Count > 0 && Matches(tool, slot.IconId)) { has = true; break; }
                    if (!has)
                        foreach (PlacedObject o in inYard)
                        {
                            if (Matches(tool, o.ItemId)) { has = true; break; }
                            if (o.Contents != null) foreach (ContainerStack cs in o.Contents) if (cs.Count > 0 && Matches(tool, cs.ItemId)) { has = true; break; }
                            if (has) break;
                        }
                    if (!has) foreach (WorldItem w in looseInYard) if (Matches(tool, w.ItemId)) { has = true; break; }
                    if (has) ts.Present.Add(tool);
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
            if (Finished) return ToggleDoor(player);   // a finished building: the right click works its door
            if (Building) return false;
            if (player != null && DistanceOutside(player.position) > YardM + 1f)
            {
                ToastNotificationSystem.ShowInfo("Too far", "Move closer to the construction site.");
                return false;
            }
            Evaluate(true);
            ConstructionStageData stage = CurrentStage;
            var missing = new List<string>();
            foreach (LineStatus l in _status)
            {
                if (l.Done) continue;
                if (l.IsChoice)
                {
                    var alts = new List<string>();
                    foreach (LineStatus o in l.Options) alts.Add($"{o.Line.quantity} x {LineName(o.Line.item_id)}");
                    missing.Add(string.Join(" or ", alts));
                }
                else missing.Add($"{l.Line.quantity - l.Have} x {LineName(l.Line.item_id)}");
            }
            foreach (ToolStatus t in _tools)
                if (!t.Have) missing.Add(ToolGroupName(t.Group));
            if (missing.Count > 0)
            {
                if (HasDoor) return ToggleDoor(player);   // the shell stands: a right click works the door (the hover list says what is still needed)
                ToastNotificationSystem.ShowWarning("Not ready: " + StageTitle(stage), "Still needed: " + string.Join(", ", missing) + ".");
                return false;
            }

            PedController ped = player != null ? player.GetComponent<PedController>() : null;
            if (ped == null) ped = FindAnyObjectByType<PedController>();
            if (ped == null) { Complete(); return true; }   // nobody to animate
            StartCoroutine(BuildRoutine(ped));
            return true;
        }

        // ------------------------------------------------------------------ building takes time

        /// <summary>How long a stage takes to build, in seconds.</summary>
        public const float BuildSeconds = 30f;

        public bool Building { get; private set; }
        private float _buildStart, _buildEnd;

        /// <summary>0 to 1 while a stage is being built: it follows the clock, so it never stalls while the ped is walking.</summary>
        public float BuildProgress { get { return Building ? Mathf.Clamp01((Time.time - _buildStart) / BuildSeconds) : 0f; } }

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
            Building = true;
            _buildStilts = Stage == 0 && StructureLook.FoundationStyle(PayerIds()) == "stilts";
            _buildStart = Time.time;
            _buildEnd = _buildStart + BuildSeconds;
            ConstructionStageData stage = CurrentStage;
            ToastNotificationSystem.ShowInfo(Name(), "Building the " + StageTitle(stage).ToLowerInvariant() + "...");

            // the materials to fetch: each distinct thing paying this stage, nearest first (a few trips at most)
            var sources = new List<GameObject>();
            foreach (LineStatus line in _status)
            {
                LineStatus l = line.Payer;
                foreach (PlacedObject o in l.Matches) if (o != null && !sources.Contains(o.gameObject)) sources.Add(o.gameObject);
                foreach (Draw dr in l.Draws) if (dr.Owner != null && !sources.Contains(dr.Owner.gameObject)) sources.Add(dr.Owner.gameObject);
                foreach (WorldItem w in l.Loose) if (w != null && !sources.Contains(w.gameObject)) sources.Add(w.gameObject);
            }
            Vector3 here = ped.transform.position;
            sources.Sort((x, y) => (x.transform.position - here).sqrMagnitude.CompareTo((y.transform.position - here).sqrMagnitude));
            if (sources.Count > 5) sources.RemoveRange(5, sources.Count - 5);
            var hidden = new List<GameObject>();

            float start = Time.time, end = start + BuildSeconds;
            float fetchBudget = BuildSeconds * 0.45f;
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
            string clip = (Stage == 0 ? FoundationClips : FramingClips)[0];
            while (!cancelled && Time.time < end)
            {
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
            foreach (GameObject g in hidden) Show(g, true);   // (the used ones are removed by Complete)
            if (cancelled)
            {
                if (Stage == 0 && _grade != null) { _grade.Apply(0f); Homesteader.World.TerrainGrade.RefreshGrass(); }   // the ground goes back
                _status = null;
                ToastNotificationSystem.ShowInfo(Name(), "Building stopped.");
                yield break;
            }
            Complete();
        }

        /// <summary>The time is up: the materials are used up and the stage exists.</summary>
        private void Complete()
        {
            ConstructionStageData stage = CurrentStage;
            // the materials are used up (placed ones, and what is drawn out of boxes); tools stay
            foreach (LineStatus line in _status)
            {
                LineStatus l = line.Payer;   // an "or" line uses up only the alternative that paid
                RememberLooks(l);
                foreach (PlacedObject o in l.Matches) if (o != null) o.Remove();
                foreach (WorldItem w in l.Loose) if (w != null) Destroy(w.gameObject);
                GiveChange(l.Line.item_id, l.Over);
                foreach (Draw dr in l.Draws)
                {
                    if (dr.Owner == null) continue;
                    ContainerRules.Remove(dr.Owner.Contents, dr.ItemId, dr.Count);
                    if (dr.Owner.Contents.Count == 0 && ContainerRules.IsDisposable(dr.Owner.ItemId)) dr.Owner.Remove();   // an emptied cardboard box goes away
                }
            }

            Stage++;
            _status = null;
            RefreshVisual();
            ToastNotificationSystem.ShowInfo(Name(), Finished ? "Construction finished." : StageTitle(stage) + " built.");
            if (Finished) ConstructionHover.ForgetPinAt(transform.position);
        }


        /// <summary>
        /// A tag line paid by an item bigger than what was left (a large bundle for the last 10 studs) is broken down: the surplus comes
        /// back as the next size down, then the next, then single items, dropped on the ground beside the site.
        /// </summary>
        private void GiveChange(string spec, float over)
        {
            if (over < 0.999f || string.IsNullOrEmpty(spec) || spec[0] != '#') return;
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
            ToastNotificationSystem.ShowInfo(Name(), "Site removed. The structure is back in your toolbar.");
            ConstructionHover.ForgetPinAt(transform.position);
            Destroy(gameObject);
            return true;
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
            if (spec[0] != '#') return HudBindings.GetItemName(spec);
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
        private float _nextGrassRefresh;

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
            if (Time.time >= _nextGrassRefresh) { _nextGrassRefresh = Time.time + 3f; Homesteader.World.TerrainGrade.RefreshGrass(); }
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
                    Homesteader.World.TerrainGrade.RefreshGrass();
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
                if (glb.Failed) { BuildStandIn(_stages[Mathf.Max(0, Stage - 1)], parent); yield break; }
                yield return null;
            }
            if (parent == null) yield break;
            LearnFront(prefab);
            GameObject model = Instantiate(prefab, parent);
            model.SetActive(true);
            model.transform.localPosition = Vector3.zero;
            model.transform.localRotation = Quaternion.identity;
            EnsureCollider(model);
            FindDoor(model.transform);
            StructureLook.Apply(model.transform, _lookItems);   // birch logs, a tin roof: the look follows what it was built from
            ShowFoundationVariant(model.transform);
            // windows let light through: the pane casts no shadow (and the walls, roof and a closed door do)
            foreach (Renderer r in model.GetComponentsInChildren<Renderer>(true))
                if (r.name == "WindowGlass") r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
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
        private readonly List<string> _lookItems = new List<string>();
        public List<string> LookItems => _lookItems;

        public void SetLooks(List<string> ids)
        {
            _lookItems.Clear();
            if (ids != null) _lookItems.AddRange(ids);
            StructureLook.Apply(VisualRoot, _lookItems);   // when the model is already showing
        }

        private void RememberLooks(LineStatus l)
        {
            var ids = new List<string>();
            foreach (PlacedObject o in l.Matches) if (o != null) ids.Add(o.ItemId);
            foreach (Draw dr in l.Draws) ids.Add(dr.ItemId);
            foreach (WorldItem w in l.Loose) if (w != null) ids.Add(w.ItemId);
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
            foreach (LineStatus line in _status)
            {
                LineStatus l = line.Payer;
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
        public bool HasDoor => _hinge != null;

        private void FindDoor(Transform model)
        {
            _hinge = null;
            foreach (Transform t in model.GetComponentsInChildren<Transform>(true))
                if (t.name == "DoorHinge") { _hinge = t; break; }
            if (_hinge == null) return;
            _hingeClosed = _hinge.localRotation;
            _leafColliders = _hinge.GetComponentsInChildren<Collider>(true);

            // it swings OUTWARD: the way that carries the leaf towards the front of the building
            Renderer leaf = _hinge.GetComponentInChildren<Renderer>(true);
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
            if (_leafColliders == null) return;
            foreach (Collider c in _leafColliders) if (c != null && c.enabled != solid) c.enabled = solid;
        }

        private void AnimateDoor()
        {
            if (_hinge == null) return;
            float target = DoorOpen ? DoorOpenDegrees : 0f;
            if (Mathf.Approximately(_doorAngle, target)) return;
            _doorAngle = Mathf.MoveTowards(_doorAngle, target, DoorSwingSpeed * Time.deltaTime);
            _hinge.localRotation = _hingeClosed * Quaternion.AngleAxis(_swingSign * _doorAngle, Vector3.up);
            SetLeafSolid(_doorAngle <= 0.5f);
        }

        /// <summary>Opens or closes the door of a finished building (a right click on it, within reach). The shape of the door opening is part of the walls, so open it to walk in.</summary>
        public bool ToggleDoor(Transform player)
        {
            if (_hinge == null) { ToastNotificationSystem.ShowInfo(Name(), "This structure is finished."); return false; }
            if (player != null && DistanceOutside(player.position) > 4f)
            {
                ToastNotificationSystem.ShowInfo("Too far", "Move closer to the door.");
                return false;
            }
            if (DoorOpen && player != null)
            {
                // never shut it on someone standing in the doorway
                Vector3 doorway = _hinge.position;
                Renderer leaf = _hinge.GetComponentInChildren<Renderer>(true);
                if (leaf != null) doorway = leaf.bounds.center;
                Vector2 apart = new Vector2(player.position.x - doorway.x, player.position.z - doorway.z);
                if (apart.magnitude < 1.5f) { ToastNotificationSystem.ShowInfo(Name(), "Step away from the doorway first."); return false; }
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
                    foreach (ConstructionLine l in CurrentStage.recipe) if (Matches(l.item_id, held)) { show = true; break; }
                    if (!show) foreach (ConstructionToolGroup g in CurrentStage.tool_groups) foreach (string t in g.tools) if (Matches(t, held)) { show = true; break; }
                }
            }
            if (_ring != null && _ring.enabled != show) _ring.enabled = show;
        }

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

        /// <summary>The construction site under the cursor (its dirt area or structure is the first thing hit), or null.</summary>
        public static ConstructionSite UnderCursor()
        {
            Camera cam = Camera.main != null ? Camera.main : FindAnyObjectByType<Camera>();
            if (cam == null) return null;
            if (UnityEngine.InputSystem.Mouse.current == null) return null;
            Vector2 pointer = UnityEngine.InputSystem.Mouse.current.position.ReadValue();
            RaycastHit[] hits = Physics.RaycastAll(cam.ScreenPointToRay(pointer), 1000f, Physics.DefaultRaycastLayers, QueryTriggerInteraction.Ignore);
            System.Array.Sort(hits, (a, b) => a.distance.CompareTo(b.distance));
            foreach (RaycastHit h in hits)
            {
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
