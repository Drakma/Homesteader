using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using Homesteader.Growth;
using Homesteader.UI;

namespace Homesteader.World
{
    /// <summary>One procedural forest tree: where it stands, what it is, and where its triangles sit in a chunk mesh.</summary>
    public sealed class ForestTree
    {
        public int Id;
        public string Species;
        public int Variant;
        public int CrownMat;
        public Vector3 Position;        // world, at the base
        public float Yaw;               // degrees
        public Vector3 Scale;           // the object's own scale (before ageing)
        public float Birth;             // absolute game day
        public float FullHeight;        // metres, mature, at this tree's scale
        public int Hits;                // axe hits taken so far
        public bool Felled;
        public bool Dead;
        public float PickedUntil;       // game day ALL the picked fruit is back (set at every pick; 0 = nothing picked)
        public uint FruitGone;          // bit i set = fruit i has been picked (the fruit is picked one at a time)
        public uint FruitDrawn = uint.MaxValue;   // bit i set = fruit i is currently drawn in the baked mesh (starts with every fruit on)
        public int PickStamp;           // TryPick's per-call mark, so a tree met in two grid cells is tested once
        public Vector3[] FruitOrig;     // the fruit's original vertices (kept once any of it is hidden)

        // where the tree's vertices live: one contiguous range in a chunk mesh
        public Mesh Mesh;
        public (int, int, bool) ChunkKey;
        public int VertStart, VertCount;
        public Vector3[] SavedVerts;    // the tree's original vertices while a live copy stands in for it
    }

    /// <summary>
    /// The registry and rules for chopping the procedural forest. Trees are baked into chunk meshes (ProceduralVegetation.
    /// Combine), so a felled tree is removed by collapsing its vertex range, a stump is left standing, a copy of the tree
    /// falls over, and the logs go to the toolbar. Chopping needs an axe (tag #axe) and takes several hits, more for a
    /// bigger tree. Felled trees are saved by position (GameSave.fellTrees) and re-applied on load.
    /// </summary>
    public static class ForestTrees
    {
        public sealed class SpeciesInfo
        {
            public string Name;
            public string Display;
            public string LogItemId;
            public Mesh[] Variants;
            public Mesh[] DeadVariants;
            public Material TrunkMat;
            public Material DeadMat;
            public Material[] CrownMats;
            public Vector4 AgeStages;   // game-day ends of sapling / small / medium
            public float TrunkRadius;   // metres at full size and scale 1

            // fruit trees: the fruit is the tail of each variant's vertices, so it can be hidden without touching the tree
            public Material FruitMat;
            public int[] FruitFirstVert;
            public int[] FruitVertCount;
            public int FruitCount;          // how many fruit models each tree of this species carries
            public float FruitRipeAge;  // tree age (game days) from which the fruit is on the tree (the kit's fruiting stage)
        }

        // The size of each growth stage relative to a mature tree (same numbers as Vegetation.shader VegAgeScale).
        private static readonly float[] StageSize = { 0.16f, 0.35f, 0.65f, 1f };
        private static readonly string[] StageNames = { "Sapling", "Small", "Medium", "Mature" };
        private static readonly int[] HitsNeeded = { 1, 2, 3, 5 };
        private static readonly float[] LogFractionByStage = { 0f, 0.25f, 0.5f, 1f };

        private const float ReachMetres = 4.5f;
        private const float HitCooldown = 0.35f;
        // Used only when a species has no growth group in the asset kit (the kit is the authority, see ToolSpec / YieldItem).

        private static readonly List<ForestTree> Trees = new List<ForestTree>();
        private static readonly Dictionary<string, SpeciesInfo> Species = new Dictionary<string, SpeciesInfo>();
        private static readonly List<Vector2> FelledPositions = new List<Vector2>();
        private static readonly Dictionary<Mesh, List<Vector3>> VertexCache = new Dictionary<Mesh, List<Vector3>>();
        private static Transform _root;
        private static float _lastHit;
        private static Material _cutWoodMat;
        private static readonly Dictionary<string, Mesh> StumpMeshes = new Dictionary<string, Mesh>();
        private static readonly Dictionary<ForestTree, GameObject> DeadObjects = new Dictionary<ForestTree, GameObject>();

        // ------------------------------------------------------------------ registration (ProceduralVegetation)

        public static void Begin(Transform vegetationRoot)
        {
            Trees.Clear();
            Grid.Clear();
            FruitTrees.Clear();
            FelledPositions.Clear();
            PickedTrees.Clear();
            VertexCache.Clear();
            StumpMeshes.Clear();
            ClearDeadObjects();
            _root = vegetationRoot;
            if (_root != null && _root.GetComponent<FruitTicker>() == null) _root.gameObject.AddComponent<FruitTicker>();
        }

        /// <summary>
        /// Removes every tree, stump and dead trunk whose base is inside an area, with no logs and no stump (the ground under a foundation
        /// was cleared). The chunk mesh is collapsed by SiteClearing; this makes them untouchable and not solid.
        /// </summary>
        public static void ClearIn(System.Func<float, float, bool> inside)
        {
            foreach (ForestTree t in Trees)
                if (!t.Felled && inside(t.Position.x, t.Position.z)) { t.Felled = true; t.Dead = false; }
            var gone = new List<ForestTree>();
            foreach (var kv in DeadObjects)
                if (kv.Value != null && inside(kv.Value.transform.position.x, kv.Value.transform.position.z)) { Object.Destroy(kv.Value); gone.Add(kv.Key); }
            foreach (ForestTree t in gone) DeadObjects.Remove(t);
            if (_root != null)
                foreach (Transform c in _root)
                    if (c != null && c.name.StartsWith("TreeStump_") && inside(c.position.x, c.position.z)) Object.Destroy(c.gameObject);
            ForestSolids.MarkDirty();
        }

        public static void RegisterSpecies(SpeciesInfo info) { Species[info.Name] = info; }

        public static void Register(ForestTree tree)
        {
            tree.Id = Trees.Count;
            Trees.Add(tree);
            if (Species.TryGetValue(tree.Species, out SpeciesInfo sp) && sp.FruitMat != null) FruitTrees.Add(tree);

            long key = CellKey(tree.Position.x, tree.Position.z);
            if (!Grid.TryGetValue(key, out List<ForestTree> cell)) { cell = new List<ForestTree>(); Grid[key] = cell; }
            cell.Add(tree);
        }

        // A coarse grid of the trees by position: the mouse pick only has to look at the cells along the ray, not at all
        // of the thousands of trees (it runs every frame for the hover outline and WAILA).
        private const float GridCell = 8f;
        private static readonly Dictionary<long, List<ForestTree>> Grid = new Dictionary<long, List<ForestTree>>();
        private static int _pickStamp;
        private static long CellKey(float x, float z) { return CellKey(Mathf.FloorToInt(x / GridCell), Mathf.FloorToInt(z / GridCell)); }
        private static long CellKey(int cx, int cz) { return ((long)cx << 32) ^ (uint)cz; }

        private static readonly List<ForestTree> FruitTrees = new List<ForestTree>();

        public static int Count => Trees.Count;

        /// <summary>Rolls the strike chance; on a hit the nearest standing tree in radius is killed by lightning and its position is returned.</summary>
        public static bool TryStrikeLightning(Vector3 origin, float radius, float chance, out Vector3 struckPosition)
        {
            struckPosition = origin;
            if (Random.value > chance) return false;
            ForestTree best = null;
            float bestDistance = radius * radius;
            foreach (ForestTree tree in Trees)
            {
                if (tree.Felled || tree.Dead) continue;
                float distance = (tree.Position - origin).sqrMagnitude;
                if (distance < bestDistance) { bestDistance = distance; best = tree; }
            }
            if (best == null) return false;
            struckPosition = best.Position;
            MakeDead(best);
            return true;
        }

        private static void MakeDead(ForestTree tree)
        {
            if (tree == null || tree.Dead || tree.Felled) return;
            tree.Dead = true;
            tree.Hits = 0;
            if (tree.Mesh == null || tree.VertCount <= 0 || !Species.TryGetValue(tree.Species, out SpeciesInfo sp)) return;
            CollapseInMesh(tree);
            Mesh deadMesh = sp.DeadVariants != null && tree.Variant < sp.DeadVariants.Length ? sp.DeadVariants[tree.Variant] : null;
            if (deadMesh == null) return;
            var go = new GameObject("DeadTree_" + tree.Species);
            if (_root != null) go.transform.SetParent(_root, true);
            go.transform.SetPositionAndRotation(tree.Position, Quaternion.Euler(0f, tree.Yaw, 0f));
            go.transform.localScale = tree.Scale;
            go.AddComponent<MeshFilter>().sharedMesh = deadMesh;
            var renderer = go.AddComponent<MeshRenderer>();
            renderer.sharedMaterials = new[] { sp.DeadMat ?? sp.TrunkMat, sp.DeadMat ?? sp.TrunkMat };
            renderer.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.On;
            DeadObjects[tree] = go;
            ForestSolids.MarkDirty();
          }

          public static void ClearDeadObjects()
          {
            foreach (GameObject go in DeadObjects.Values) if (go != null) Object.Destroy(go);
            DeadObjects.Clear();
          }

        public static List<Vector2> SavedDead()
        {
            var result = new List<Vector2>();
            foreach (ForestTree tree in Trees) if (tree.Dead && !tree.Felled) result.Add(new Vector2(tree.Position.x, tree.Position.z));
            return result;
        }

        public static void ApplyDead(List<Vector2> dead)
        {
            if (dead == null) return;
            foreach (Vector2 position in dead)
            {
                ForestTree best = null;
                float bestDistance = 0.6f * 0.6f;
                foreach (ForestTree tree in Trees)
                {
                    float dx = tree.Position.x - position.x, dz = tree.Position.z - position.y;
                    float distance = dx * dx + dz * dz;
                    if (!tree.Felled && distance < bestDistance) { bestDistance = distance; best = tree; }
                }
                MakeDead(best);
            }
        }

        // ------------------------------------------------------------------ growth (mirrors Vegetation.shader)

        private static float NowDay()
        {
            // The growth clock (never goes backwards), as the shader uses it.
            var ts = TimeSystem.Instance;
            float now = ts != null ? ts.DayOfYear + ts.MinuteOfDay / TimeConstants.CycleGameMinutes : WorldStartDayFallback;
            return Mathf.Max(VegetationSeasons.GrowthDay, now);
        }

        private const float WorldStartDayFallback = 141f;

        public static int StageIndex(ForestTree t)
        {
            SpeciesInfo sp = Species[t.Species];
            float age = NowDay() - t.Birth;
            if (age < sp.AgeStages.x) return 0;
            if (age < sp.AgeStages.y) return 1;
            if (age < sp.AgeStages.z) return 2;
            return 3;
        }

        public static float AgeDays(ForestTree t) { return Mathf.Max(0f, NowDay() - t.Birth); }
        public static float CurrentHeight(ForestTree t) { return t.FullHeight * StageSize[StageIndex(t)]; }

        // ------------------------------------------------------------------ picking

        /// <summary>The standing tree the ray passes closest to the camera through (trunk and crown approximated as a fat capsule).</summary>
        public static bool TryPick(Ray ray, out ForestTree picked)
        {
            picked = null;
            if (Trees.Count == 0) return false;
            float bestT = float.MaxValue;
            float now = NowDay();
            int stamp = ++_pickStamp;

            // The part of the ray that can touch a tree: from 40 m up (taller than any tree) down to 5 m below the ground.
            Vector3 o = ray.origin, d = ray.direction;
            float t0, t1;
            if (Mathf.Abs(d.y) > 1e-4f) { t0 = (40f - o.y) / d.y; t1 = (-5f - o.y) / d.y; if (t0 > t1) { float tmp = t0; t0 = t1; t1 = tmp; } t0 = Mathf.Max(t0, 0f); }
            else { t0 = 0f; t1 = 200f; }
            if (t1 <= t0) return false;
            Vector3 p0 = o + d * t0, p1 = o + d * t1;
            float len = new Vector2(p1.x - p0.x, p1.z - p0.z).magnitude;
            int steps = Mathf.Clamp(Mathf.CeilToInt(len / (GridCell * 0.5f)) + 1, 1, 400);

            for (int i = 0; i <= steps; i++)
            {
                Vector3 p = Vector3.Lerp(p0, p1, i / (float)steps);
                int cx = Mathf.FloorToInt(p.x / GridCell), cz = Mathf.FloorToInt(p.z / GridCell);
                for (int ox = -1; ox <= 1; ox++)
                {
                    for (int oz = -1; oz <= 1; oz++)
                    {
                        if (!Grid.TryGetValue(CellKey(cx + ox, cz + oz), out List<ForestTree> cell)) continue;
                        for (int k = 0; k < cell.Count; k++)
                        {
                            ForestTree t = cell[k];
                            if (t.Felled || t.PickStamp == stamp) continue;
                            t.PickStamp = stamp;
                            float h = HeightAt(t, now);
                            // Quick reject: distance from the ray to the tree's base column axis region.
                            Vector3 a = t.Position + Vector3.up * (h * 0.05f);
                            Vector3 b = t.Position + Vector3.up * (h * 0.75f);
                            float radius = Mathf.Clamp(0.35f + h * 0.10f, 0.45f, 2.0f);
                            float along = RaySegmentDistance(ray, a, b, out float rayT);
                            if (along <= radius && rayT < bestT) { bestT = rayT; picked = t; }
                        }
                    }
                }
            }
            return picked != null;
        }

        /// <summary>A tree's height on a given game day (CurrentHeight without asking the clock again for every tree).</summary>
        private static float HeightAt(ForestTree t, float nowDay)
        {
            SpeciesInfo sp = Species[t.Species];
            float age = nowDay - t.Birth;
            int stage = age < sp.AgeStages.x ? 0 : (age < sp.AgeStages.y ? 1 : (age < sp.AgeStages.z ? 2 : 3));
            return t.FullHeight * StageSize[stage];
        }

        /// <summary>Shortest distance between a ray and a segment; rayT is the ray parameter at the closest point.</summary>
        private static float RaySegmentDistance(Ray ray, Vector3 a, Vector3 b, out float rayT)
        {
            Vector3 d1 = ray.direction, d2 = b - a, r = ray.origin - a;
            float aa = Vector3.Dot(d1, d1), e = Vector3.Dot(d2, d2), f = Vector3.Dot(d2, r);
            float c = Vector3.Dot(d1, r), bb = Vector3.Dot(d1, d2);
            float denom = aa * e - bb * bb;
            float s = denom > 1e-6f ? Mathf.Clamp((bb * f - c * e) / denom, 0f, float.MaxValue) : 0f;   // ray param
            float tt = e > 1e-6f ? (bb * s + f) / e : 0f;                                               // segment param
            tt = Mathf.Clamp01(tt);
            s = Mathf.Max(0f, (bb * tt - c) / aa);
            rayT = s;
            return Vector3.Distance(ray.origin + d1 * s, a + d2 * tt);
        }

        // ------------------------------------------------------------------ hover info (WAILA)

        // ------------------------------------------------------------------ what the asset kit says about felling

        /// <summary>The kit's growth group for a species (maple, oak...), if the kit has one.</summary>
        private static GrowthRules KitRules(string species)
        {
            if (GrowthRegistry.TryGetGroup(species, "homesteader", out GrowthGroup g) && g.Rules != null
                && !string.IsNullOrEmpty(g.Rules.YieldItemId) && g.Rules.YieldAmountMax > 0)
                return g.Rules;
            return null;
        }

        // ------------------------------------------------------------------ icons

        /// <summary>How many standing trees of a species the world has (diagnostics and tools).</summary>
        public static int CountOf(string species)
        {
            int n = 0;
            foreach (ForestTree t in Trees) if (!t.Felled && t.Species == species) n++;
            return n;
        }

        /// <summary>The standing tree of a species nearest a point, or null.</summary>
        public static ForestTree NearestOfSpecies(string species, Vector3 from)
        {
            ForestTree best = null;
            float bestD = float.MaxValue;
            foreach (ForestTree t in Trees)
            {
                if (t.Felled || t.Species != species) continue;
                float d = (t.Position - from).sqrMagnitude;
                if (d < bestD) { bestD = d; best = t; }
            }
            return best;
        }

        // ------------------------------------------------------------------ planting: saplings grow the procedural tree

        private static Transform _plantHolder;

        /// <summary>True for a species the game draws procedurally (maple, oak, apple, willow ...).</summary>
        public static bool IsProcedural(string species) { return !string.IsNullOrEmpty(species) && Species.ContainsKey(species); }

        /// <summary>
        /// Gives every kit growth group whose species is procedural stage "prefabs" made from the species mesh, so planting a sapling
        /// grows the same tree the forests have instead of needing the stage model files (the .fbx / .glb in the kit). Stage 1-4
        /// are the sapling / small / medium / mature sizes; a group's fruiting stage is the mature tree with its fruit on.
        /// Called after the species are registered (every world generation), because mods and their groups load before it.
        /// </summary>
        public static void ApplyPlantPrefabs()
        {
            if (_plantHolder == null)
            {
                var h = new GameObject("ProceduralPlantTemplates");
                h.SetActive(false);   // everything under it is inactive: templates are never drawn themselves
                Object.DontDestroyOnLoad(h);
                _plantHolder = h.transform;
            }
            else
            {
                for (int i = _plantHolder.childCount - 1; i >= 0; i--) Object.Destroy(_plantHolder.GetChild(i).gameObject);
            }

            foreach (KeyValuePair<string, SpeciesInfo> kv in Species)
            {
                SpeciesInfo sp = kv.Value;
                if (!GrowthRegistry.TryGetGroup(sp.Name, "homesteader", out GrowthGroup g) || g.Stages.Count == 0 || sp.Variants == null) continue;
                int n = g.Stages.Count;
                int fruitStage = sp.FruitMat != null && g.Rules != null && g.Rules.Fruiting
                    ? (g.Rules.FruitStage > 0 ? g.Rules.FruitStage : n) - 1 : -1;
                for (int i = 0; i < n; i++)
                    g.Stages[i].Prefab = MakePlantTemplate(sp, Mathf.Min(i, StageSize.Length - 1), i == fruitStage);

                // The dead version (a planted tree killed by frost or a bad season) is generated too, in the species' own dead shape;
                // it replaces whatever dead model the kit named, so a procedural tree dies as a procedural tree.
                if (g.Rules != null && sp.DeadVariants != null && sp.DeadVariants.Length > 0)
                {
                    if (g.Rules.Dead == null) g.Rules.Dead = new GrowthVariant { Resource = "(procedural)", Model = "(procedural)" };
                    g.Rules.Dead.Prefab = MakeDeadTemplate(sp);
                }
            }
        }

        private static GameObject MakeDeadTemplate(SpeciesInfo sp)
        {
            var go = new GameObject("PlantDead_" + sp.Name);
            go.transform.SetParent(_plantHolder, false);
            float s = StageSize[StageSize.Length - 1] * ProceduralVegetation.TreeScale;
            go.transform.localScale = new Vector3(s, s, s);
            Mesh mesh = sp.DeadVariants[0];
            go.AddComponent<MeshFilter>().sharedMesh = mesh;
            var mr = go.AddComponent<MeshRenderer>();
            mr.sharedMaterials = new[] { sp.DeadMat ?? sp.TrunkMat, sp.DeadMat ?? sp.TrunkMat };
            mr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.On;
            var col = go.AddComponent<CapsuleCollider>();
            col.radius = Mathf.Max(0.2f, sp.TrunkRadius * 0.9f);
            col.height = Mathf.Clamp(mesh.bounds.size.y * 0.55f, 0.6f, 3f / Mathf.Max(0.05f, s));
            col.height = Mathf.Max(col.height, col.radius * 2f);
            col.center = new Vector3(0f, col.height * 0.5f, 0f);
            return go;
        }

        private static readonly Dictionary<string, Mesh> NoFruitMeshes = new Dictionary<string, Mesh>();

        /// <summary>The species' first tree variant with its fruit submesh removed (the same vertices, only trunk and crown triangles).</summary>
        private static Mesh NoFruitMesh(SpeciesInfo sp)
        {
            if (NoFruitMeshes.TryGetValue(sp.Name, out Mesh cached) && cached != null) return cached;
            Mesh src = sp.Variants[0];
            var mesh = new Mesh { name = src.name + "_nofruit" };
            mesh.SetVertices(src.vertices);
            mesh.SetNormals(src.normals);
            mesh.subMeshCount = 2;
            mesh.SetTriangles(src.GetTriangles(0), 0);
            mesh.SetTriangles(src.GetTriangles(1), 1);
            mesh.RecalculateBounds();
            NoFruitMeshes[sp.Name] = mesh;
            return mesh;
        }

        private static GameObject MakePlantTemplate(SpeciesInfo sp, int sizeStage, bool withFruit)
        {
            var go = new GameObject("Plant_" + sp.Name + "_" + sizeStage + (withFruit ? "_fruit" : ""));
            go.transform.SetParent(_plantHolder, false);
            float s = StageSize[sizeStage] * ProceduralVegetation.TreeScale;
            go.transform.localScale = new Vector3(s, s, s);
            // Before the fruiting stage the tree is a mesh WITHOUT the fruit submesh (a property block would not survive Instantiate).
            Mesh mesh = (sp.FruitMat != null && !withFruit) ? NoFruitMesh(sp) : sp.Variants[0];
            go.AddComponent<MeshFilter>().sharedMesh = mesh;
            var mr = go.AddComponent<MeshRenderer>();
            mr.sharedMaterials = (sp.FruitMat != null && withFruit)
                ? new[] { sp.TrunkMat, sp.CrownMats[0], sp.FruitMat }
                : new[] { sp.TrunkMat, sp.CrownMats[0] };
            mr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.On;

            // Trees are solid: a trunk-sized capsule (in the template's own, unscaled units).
            var col = go.AddComponent<CapsuleCollider>();
            float height = Mathf.Clamp(mesh.bounds.size.y * 0.55f, 0.6f, 3f / Mathf.Max(0.05f, s));
            col.radius = Mathf.Max(0.2f, sp.TrunkRadius * 0.9f);
            col.height = Mathf.Max(height, col.radius * 2f);
            col.center = new Vector3(0f, col.height * 0.5f, 0f);
            return go;
        }

        /// <summary>A standalone dead tree of a species (variant 0, mature size), for rendering icons and checking the shapes.</summary>
        public static GameObject MakeDeadIconProxy(string species, int variant = 0)
        {
            if (!Species.TryGetValue(species, out SpeciesInfo sp) || sp.DeadVariants == null || sp.DeadVariants.Length == 0) return null;
            var go = new GameObject("DeadTreeIcon_" + species);
            go.AddComponent<MeshFilter>().sharedMesh = sp.DeadVariants[Mathf.Clamp(variant, 0, sp.DeadVariants.Length - 1)];
            go.AddComponent<MeshRenderer>().sharedMaterials = new[] { sp.DeadMat ?? sp.TrunkMat, sp.DeadMat ?? sp.TrunkMat };
            return go;
        }

        /// <summary>The registered procedural species names (for tools that render their icons).</summary>
        public static List<string> SpeciesNames() { return new List<string>(Species.Keys); }

        /// <summary>A standalone, unscaled-world copy of a species at one growth stage (0 sapling .. 3 mature), for rendering its
        /// asset-kit icon. The caller places, frames and destroys it.</summary>
        public static GameObject MakeIconProxy(string species, int stage)
        {
            if (!Species.TryGetValue(species, out SpeciesInfo sp) || sp.Variants == null || sp.Variants.Length == 0) return null;
            var go = new GameObject("TreeIcon_" + species + "_" + stage);
            go.AddComponent<MeshFilter>().sharedMesh = sp.Variants[0];
            var mr = go.AddComponent<MeshRenderer>();
            mr.sharedMaterials = sp.FruitMat != null ? new[] { sp.TrunkMat, sp.CrownMats[0], sp.FruitMat } : new[] { sp.TrunkMat, sp.CrownMats[0] };
            float s = StageSize[Mathf.Clamp(stage, 0, StageSize.Length - 1)];
            go.transform.localScale = new Vector3(s, s, s);
            return go;
        }

        // ------------------------------------------------------------------ picking fruit (kit: growth.rules.fruit)

        /// <summary>The kit's fruit rules for a species, if its group is a fruiting tree with drops.</summary>
        private static GrowthRules FruitRules(string species)
        {
            if (GrowthRegistry.TryGetGroup(species, "homesteader", out GrowthGroup g) && g.Rules != null
                && g.Rules.Fruiting && g.Rules.FruitDrops.Count > 0)
                return g.Rules;
            return null;
        }

        /// <summary>Tree age (game days) from which this species carries fruit: where the kit's fruiting stage begins.</summary>
        private static float RipeAge(string species)
        {
            return Species.TryGetValue(species, out SpeciesInfo sp) && sp.FruitRipeAge > 0f ? sp.FruitRipeAge : (Species.ContainsKey(species) ? Species[species].AgeStages.z : 0f);
        }

        /// <summary>True when this tree has its fruit on it: old enough (the fruiting stage), not picked recently, not winter-bare.</summary>
        public static bool HasFruitOn(ForestTree t)
        {
            return t != null && !t.Felled && AgeDays(t) >= RipeAge(t.Species) && FruitLeft(t) > 0;
        }

        /// <summary>The fruit layout of the mesh a PLANTED tree of this species uses (variant 0): where its fruit starts, how many vertices each fruit has, how many fruit.</summary>
        public static bool PlantFruitLayout(string species, out int firstVert, out int perFruit, out int total, out Color color)
        {
            firstVert = perFruit = total = 0;
            color = Color.red;
            if (!Species.TryGetValue(species, out SpeciesInfo sp) || sp.FruitMat == null || sp.FruitFirstVert == null || sp.FruitVertCount == null || sp.FruitVertCount.Length == 0) return false;
            total = Mathf.Clamp(sp.FruitCount, 1, 32);
            int count = sp.FruitVertCount[0];
            if (count <= 0 || count % total != 0) return false;
            perFruit = count / total;
            firstVert = sp.FruitFirstVert[0];
            color = sp.FruitMat.GetColor("_BaseColor");
            return true;
        }

        /// <summary>The middle of fruit number <paramref name="bit"/> in the planted tree's mesh, in the tree's own space.</summary>
        public static Vector3 PlantFruitCentre(string species, int bit)
        {
            if (!PlantFruitLayout(species, out int first, out int per, out int total, out _) || !Species.TryGetValue(species, out SpeciesInfo sp)) return Vector3.up * 2f;
            Mesh mesh = sp.Variants[0];
            var verts = mesh.vertices;
            int start = first + Mathf.Clamp(bit, 0, total - 1) * per;
            if (start + per > verts.Length) return Vector3.up * 2f;
            Vector3 sum = Vector3.zero;
            for (int k = 0; k < per; k++) sum += verts[start + k];
            return sum / per;
        }

        public static uint FullFruitMask(int total) => FullMask(total);

        /// <summary>How many fruit models this species' tree carries when full.</summary>
        public static int FruitTotal(string species)
        {
            return Species.TryGetValue(species, out SpeciesInfo sp) ? Mathf.Clamp(sp.FruitCount, 0, 32) : 0;
        }

        private static uint FullMask(int total) => total >= 32 ? uint.MaxValue : (1u << total) - 1u;

        /// <summary>Fruit still on the tree (the picked ones are back after the regrow time).</summary>
        public static int FruitLeft(ForestTree t)
        {
            int total = FruitTotal(t.Species);
            if (total <= 0) return 0;
            ReturnFruit(t);
            uint left = FullMask(total) & ~t.FruitGone;
            int n = 0;
            for (; left != 0; left &= left - 1) n++;
            return n;
        }

        /// <summary>Once the regrow time has passed, everything that was picked is back.</summary>
        private static void ReturnFruit(ForestTree t)
        {
            if (t.FruitGone != 0 && VegetationSeasons.GrowthDay >= t.PickedUntil) { t.FruitGone = 0; t.PickedUntil = 0f; }
        }

        /// <summary>True if this tree bears fruit that is ripe now (a fruiting species with the fruit on it).</summary>
        public static bool CanPick(ForestTree t)
        {
            if (t == null || t.Felled) return false;
            return FruitRules(t.Species) != null && HasFruitOn(t);
        }

        /// <summary>Shows or hides the fruit on every fruit tree to match its state (age, picked, felled). Batched per chunk mesh.</summary>
        private static void SyncFruit()
        {
            HashSet<Mesh> dirty = null;
            for (int i = 0; i < FruitTrees.Count; i++)
            {
                ForestTree t = FruitTrees[i];
                if (t.Felled || t.Mesh == null) continue;
                if (!Species.TryGetValue(t.Species, out SpeciesInfo sp) || sp.FruitVertCount == null || t.Variant >= sp.FruitVertCount.Length) continue;
                int total = Mathf.Clamp(sp.FruitCount, 0, 32);
                int count = sp.FruitVertCount[t.Variant];
                if (total <= 0 || count <= 0 || count % total != 0) continue;   // the fruit models are equal; otherwise it is all or nothing below
                // Which fruit should be drawn: none until the tree is old enough, then every one that has not been picked.
                bool ripe = !t.Felled && AgeDays(t) >= RipeAge(t.Species);
                ReturnFruit(t);
                uint want = ripe ? FullMask(total) & ~t.FruitGone : 0u;
                if (want == (t.FruitDrawn & FullMask(total))) continue;
                if (t.SavedVerts != null) continue;   // a live copy stands in for it right now
                int start = t.VertStart + sp.FruitFirstVert[t.Variant];
                List<Vector3> verts = VertexList(t.Mesh);
                if (start + count > verts.Count) continue;
                if (t.FruitOrig == null) t.FruitOrig = verts.GetRange(start, count).ToArray();   // the mesh still holds every fruit here
                int per = count / total;
                uint changed = want ^ (t.FruitDrawn & FullMask(total));
                for (int f = 0; f < total; f++)
                {
                    if ((changed & (1u << f)) == 0) continue;
                    bool show = (want & (1u << f)) != 0;
                    for (int k = 0; k < per; k++) verts[start + f * per + k] = show ? t.FruitOrig[f * per + k] : t.Position;
                }
                t.FruitDrawn = want;
                if (dirty == null) dirty = new HashSet<Mesh>();
                dirty.Add(t.Mesh);
            }
            if (dirty != null)
                foreach (Mesh m in dirty) m.SetVertices(VertexList(m));
        }

        /// <summary>Applies the fruit state to the baked meshes now (it also runs every 1.5 seconds on its own).</summary>
        public static void RefreshFruit() { SyncFruit(); }

        private sealed class RepeatPickEntry
        {
            public System.Func<bool> Again;
            public Transform Player;
            public Vector3 Start;
        }

        private static readonly List<RepeatPickEntry> RepeatPicks = new List<RepeatPickEntry>();

        /// <summary>
        /// One click picks the whole tree, like one click on a berry bush picks every berry: once the first fruit is in the basket the
        /// next one is picked, and so on until none is left. <paramref name="again"/> picks one more and returns false when there is
        /// nothing left to pick. Walking away (more than 0.4 m) stops it.
        /// </summary>
        public static void RepeatPick(System.Func<bool> again, Transform player)
        {
            if (again == null) return;
            RepeatPicks.Clear();   // one run at a time
            RepeatPicks.Add(new RepeatPickEntry { Again = again, Player = player, Start = player != null ? player.position : Vector3.zero });
        }

        private static void TickRepeatPicks()
        {
            for (int i = RepeatPicks.Count - 1; i >= 0; i--)
            {
                RepeatPickEntry e = RepeatPicks[i];
                if (e.Player != null && (e.Player.position - e.Start).sqrMagnitude > 0.16f) { RepeatPicks.RemoveAt(i); continue; }
                if (FruitPickAnimator.Busy) continue;   // the hand is still on the last fruit
                if (!e.Again()) RepeatPicks.RemoveAt(i);
            }
        }

        private sealed class FruitTicker : MonoBehaviour
        {
            private float _next;
            private void Update()
            {
                if (RepeatPicks.Count > 0) TickRepeatPicks();
                if (Time.unscaledTime < _next) return;
                _next = Time.unscaledTime + 1.5f;
                SyncFruit();
            }
        }

        /// <summary>Picks the ripe fruit by hand: the drops go to the toolbar, the tree stays and the fruit regrows.</summary>
        public static bool TryPickFruit(ForestTree t, Transform player, string heldId = null)
        {
            if (!CanPick(t)) return false;
            string need = FruitRules(t.Species).FruitTool;
            if (!string.IsNullOrEmpty(need) && !GrowthRegistry.ToolMatches(need, heldId))
            {
                Notify("Need a tool", $"You need {DescribeTool(need).ToLowerInvariant()} in your active slot to pick this.");
                return false;
            }
            if (player != null)
            {
                Vector3 d = t.Position - player.position;
                d.y = 0f;
                if (d.magnitude > ReachMetres) { Notify("Too far", "Move closer to pick the fruit."); return false; }
            }
            GrowthRules r = FruitRules(t.Species);
            // One fruit at a time: a random one of those still on the tree comes off (the kit's drops are what ONE fruit gives).
            int total = FruitTotal(t.Species);
            uint left = FullMask(total) & ~t.FruitGone;
            int leftCount = 0;
            for (uint m = left; m != 0; m &= m - 1) leftCount++;
            if (leftCount <= 0) return false;
            int nth = UnityEngine.Random.Range(0, leftCount);
            int bit = 0;
            for (int seen = -1; bit < 32; bit++)
            {
                if ((left & (1u << bit)) != 0 && ++seen == nth) break;
            }
            if (FruitPickAnimator.Busy) return true;   // the player's hand is still on the last one

            void TakeOffTree()
            {
                t.FruitGone |= 1u << bit;
                t.PickedUntil = VegetationSeasons.GrowthDay + r.FruitRegrowDays;   // the missing fruit is all back this long after the latest pick
                PickedTrees.Add(t);
                SyncFruit();
            }

            void IntoBasket()
            {
                if (!GrowthDrop.Give(r.FruitDrops)) Notify("Toolbar full", "The fruit didn't fit and was lost.");
            }

            // The gesture: the left hand reaches up, the fruit comes off the tree, the hand bends in to the right hand (the basket) and the item
            // lands in the toolbar. Without a rig that can do it (or no ped), it all happens at once.
            Color fruitColor = Species.TryGetValue(t.Species, out SpeciesInfo fsp) && fsp.FruitMat != null ? fsp.FruitMat.GetColor("_BaseColor") : Color.red;
            var ped = player != null ? player : UnityEngine.Object.FindAnyObjectByType<PedController>()?.transform;
            if (ped != null && FruitPickAnimator.TryBegin(ped, FruitWorldPosition(t, bit), fruitColor, TakeOffTree, IntoBasket)) return true;
            TakeOffTree();
            IntoBasket();
            return true;
        }

        /// <summary>Where fruit number <paramref name="bit"/> hangs on this tree (the middle of its model in the baked mesh).</summary>
        private static Vector3 FruitWorldPosition(ForestTree t, int bit)
        {
            Vector3 fallback = t.Position + Vector3.up * Mathf.Max(1.6f, t.FullHeight * 0.55f);
            if (!Species.TryGetValue(t.Species, out SpeciesInfo sp) || sp.FruitVertCount == null || t.Variant >= sp.FruitVertCount.Length || t.Mesh == null) return fallback;
            int total = Mathf.Clamp(sp.FruitCount, 1, 32), count = sp.FruitVertCount[t.Variant];
            if (count <= 0 || count % total != 0) return fallback;
            int per = count / total;
            int start = t.VertStart + sp.FruitFirstVert[t.Variant] + bit * per;
            List<Vector3> verts = VertexList(t.Mesh);
            if (start + per > verts.Count) return fallback;
            Vector3 sum = Vector3.zero;
            for (int k = 0; k < per; k++) sum += verts[start + k];
            return sum / per;
        }

        private static readonly List<ForestTree> PickedTrees = new List<ForestTree>();

        /// <summary>(x, z, game day the fruit is back) of every tree still regrowing its fruit, for GameSave.</summary>
        public static List<Vector3> SavedPicked()
        {
            var list = new List<Vector3>();
            foreach (ForestTree t in PickedTrees)
                if (!t.Felled && t.PickedUntil > VegetationSeasons.GrowthDay) list.Add(new Vector3(t.Position.x, t.Position.z, t.PickedUntil));
            return list;
        }

        /// <summary>Which fruit of each tree in <see cref="SavedPicked"/> is gone (a bit mask), in the same order.</summary>
        public static List<int> SavedPickedMasks()
        {
            var list = new List<int>();
            foreach (ForestTree t in PickedTrees)
                if (!t.Felled && t.PickedUntil > VegetationSeasons.GrowthDay) list.Add((int)t.FruitGone);
            return list;
        }

        public static void ApplyPicked(List<Vector3> picked, List<int> masks = null)
        {
            if (picked == null) return;
            for (int pi = 0; pi < picked.Count; pi++)
            {
                Vector3 p = picked[pi];
                ForestTree best = null;
                float bestD = 0.6f * 0.6f;
                for (int i = 0; i < Trees.Count; i++)
                {
                    ForestTree t = Trees[i];
                    float dx = t.Position.x - p.x, dz = t.Position.z - p.y;
                    float d = dx * dx + dz * dz;
                    if (d < bestD) { bestD = d; best = t; }
                }
                if (best != null)
                {
                    best.PickedUntil = p.z;
                    // an older save has no mask: everything on that tree counted as picked
                    best.FruitGone = masks != null && pi < masks.Count ? (uint)masks[pi] : FullMask(FruitTotal(best.Species));
                    PickedTrees.Add(best);
                }
            }
        }

        /// <summary>The tool (an item id or a #tag) that fells this species, from the group's yield.tool in the kit.</summary>
        public static string ToolSpec(string species)
        {
            GrowthRules r = KitRules(species);
            return r != null && !string.IsNullOrEmpty(r.YieldTool) ? r.YieldTool : null;   // no kit rules = no tool fells it (nothing is hard coded)
        }

        /// <summary>The log item this species drops, from the group's yield.item_id in the kit.</summary>
        public static string YieldItem(string species)
        {
            GrowthRules r = KitRules(species);
            return r != null ? r.YieldItemId : null;   // what a tree drops comes from the kit's yield only
        }

        /// <summary>
        /// True when this tree has reached the kit's harvest stage (growth.rules.yield.harvest_stage): it can be cut down from that stage
        /// on, that stage or any later one. With no harvest_stage a fruiting tree is harvestable from its mature stage (the one before the
        /// fruiting stage); any other tree has no stage gate. Stages are the kit's own numbers and age windows, not the four drawn sizes.
        /// </summary>
        public static bool HarvestReady(ForestTree t, out string neededStageName)
        {
            neededStageName = null;
            if (!GrowthRegistry.TryGetGroup(t.Species, "homesteader", out GrowthGroup g) || g.Rules == null) return true;
            int need = g.Rules.HarvestStage > 0 ? g.Rules.HarvestStage
                     : (g.Rules.Fruiting && g.Rules.FruitStage > 1 ? g.Rules.FruitStage - 1 : 0);
            if (need <= 0) return true;
            GrowthStage now = g.StageForAge(AgeDays(t));
            if (now != null && now.Stage >= need) return true;
            GrowthStage wanted = g.Stages.Find(x => x.Stage == need);
            neededStageName = wanted != null ? wanted.Name : "stage " + need;
            return false;
        }

        /// <summary>True when the kit says this species can be cut down at all (its growth group has a yield).</summary>
        public static bool IsFellable(string species) { return KitRules(species) != null; }

        /// <summary>True when the item in hand fells THIS tree: the species is fellable and the item is one of its kit tools.</summary>
        public static bool CanFellTree(ForestTree t, string heldId)
        {
            if (t == null || string.IsNullOrEmpty(heldId)) return false;
            string spec = ToolSpec(t.Species);
            return KitRules(t.Species) != null && spec != null && GrowthRegistry.ToolMatches(spec, heldId);
        }

        /// <summary>True if the item in the active slot can fell trees of ANY species (per the kit's tools).</summary>
        public static bool CanFell(string heldId)
        {
            if (string.IsNullOrEmpty(heldId)) return false;
            foreach (string name in Species.Keys)
            {
                string spec = ToolSpec(name);
                if (spec != null && GrowthRegistry.ToolMatches(spec, heldId)) return true;
            }
            return false;
        }

        private static string DescribeTool(string spec)
        {
            if (string.IsNullOrEmpty(spec)) return "Nothing (by hand)";
            var names = new List<string>();
            foreach (string one in spec.Split(','))
            {
                string s = one.Trim();
                if (s.Length == 0) continue;
                names.Add(s.StartsWith("#") ? char.ToUpperInvariant(s[1]) + s.Substring(2).Replace('_', ' ') : HudBindings.GetItemName(s));
            }
            return string.Join(" or ", names);
        }

        private static int LogsFor(string species, int stage)
        {
            GrowthRules r = KitRules(species);
            int mature = r != null ? r.RollYield() : 0;
            if (stage >= 3) return mature;
            if (stage == 0) return 0;
            return Mathf.Max(1, Mathf.RoundToInt(mature * LogFractionByStage[stage]));
        }

        private static int MaxLogsFor(string species, int stage)
        {
            GrowthRules r = KitRules(species);
            int max = r != null ? r.YieldAmountMax : 0;
            return stage == 0 ? 0 : (stage >= 3 ? max : Mathf.Max(1, Mathf.RoundToInt(max * LogFractionByStage[stage])));
        }

        /// <summary>Right-clicked a tree without the right tool in the active slot: tell the player what it needs.</summary>
        public static void HintTool(ForestTree tree, string heldId = null)
        {
            if (Time.unscaledTime - _lastHint < 2.5f) return;
            _lastHint = Time.unscaledTime;

            // The tool in hand fits the tree's FRUIT (the basket) but there is nothing to pick right now: say so, do not ask for an axe.
            GrowthRules pickRules = FruitRules(tree.Species);
            if (pickRules != null && !string.IsNullOrEmpty(pickRules.FruitTool) && GrowthRegistry.ToolMatches(pickRules.FruitTool, heldId))
            {
                float wait = tree.PickedUntil - VegetationSeasons.GrowthDay;
                float young = RipeAge(tree.Species) - AgeDays(tree);
                ToastNotificationSystem.ShowInfo(Species[tree.Species].Display + " tree",
                    young > 0f ? $"No fruit yet: it bears fruit in {Mathf.CeilToInt(young)} days."
                               : (wait > 0f ? $"Picked recently: ripe again in {Mathf.CeilToInt(wait)} days." : "No ripe fruit right now."));
                return;
            }
            // Ripe fruit: the answer is the fruit tool, not the axe.
            GrowthRules fruit = FruitRules(tree.Species);
            if (fruit != null && HasFruitOn(tree) && !string.IsNullOrEmpty(fruit.FruitTool))
            {
                ToastNotificationSystem.ShowInfo(Species[tree.Species].Display + " tree",
                    $"Put {DescribeTool(fruit.FruitTool).ToLowerInvariant()} in your active slot, then right-click to pick the fruit.");
                return;
            }
            if (!IsFellable(tree.Species))
            {
                ToastNotificationSystem.ShowInfo(Species[tree.Species].Display + " tree", "This tree can't be cut down.");
                return;
            }
            string spec = ToolSpec(tree.Species);
            ToastNotificationSystem.ShowInfo(Species[tree.Species].Display + " tree",
                string.IsNullOrEmpty(spec) ? "Right-click to chop it." : $"Put {DescribeTool(spec).ToLowerInvariant()} in your active slot, then right-click to chop it.");
        }

        private static float _lastHint;
        private static float _lastNotify;

        /// <summary>A failure the player can act on; shown at most every couple of seconds (holding the button must not spam).</summary>
        private static void Notify(string title, string message)
        {
            if (Time.unscaledTime - _lastNotify < 2.5f) return;
            _lastNotify = Time.unscaledTime;
            ToastNotificationSystem.ShowWarning(title, message);
        }

        // ------------------------------------------------------------------ chop sound

        private static AudioClip _chopClip;

        /// <summary>A short wooden "thock": a low thump plus a burst of filtered noise, made in code.</summary>
        private static void PlayChopSound(Vector3 at)
        {
            var audio = Homesteader.Audio.AudioManager.Instance;
            if (audio == null) return;
            if (_chopClip == null)
            {
                const int rate = 44100;
                int n = (int)(rate * 0.22f);
                var data = new float[n];
                var rng = new System.Random(77);
                float lp = 0f;
                for (int i = 0; i < n; i++)
                {
                    float t = i / (float)rate;
                    lp += (((float)rng.NextDouble() * 2f - 1f) - lp) * 0.25f;   // low-passed noise
                    data[i] = (lp * Mathf.Exp(-t * 30f) * 0.9f + Mathf.Sin(2f * Mathf.PI * 120f * t) * Mathf.Exp(-t * 18f) * 0.7f) * 0.8f;
                }
                _chopClip = AudioClip.Create("TreeChop", n, 1, rate, false);
                _chopClip.SetData(data, 0);
            }
            audio.PlaySfx2D(_chopClip, 0.9f);
        }

        // ------------------------------------------------------------------ trunk size (colliders)

        /// <summary>Radius and height of the solid part of the trunk now, for ForestSolids.</summary>
        public static void TrunkSize(ForestTree t, out float radius, out float height)
        {
            SpeciesInfo sp = Species[t.Species];
            float s = StageSize[StageIndex(t)];
            radius = Mathf.Max(0.2f, sp.TrunkRadius * t.Scale.x * s * 0.9f);
            height = Mathf.Clamp(CurrentHeight(t) * 0.55f, 0.6f, 3f);
        }

        // ------------------------------------------------------------------ hover info (WAILA)

        public static void Describe(ForestTree t, out string title, List<(string, string)> rows)
        {
            SpeciesInfo sp = Species[t.Species];
            int stage = StageIndex(t);
            int hitsLeft = Mathf.Max(1, HitsNeeded[stage] - t.Hits);
            title = sp.Display + " Tree";
            rows.Add(("Stage", StageNames[stage]));
            rows.Add(("Age", $"{AgeDays(t):F0} days"));
            rows.Add(("Height", Homesteader.UI.UnitFormat.Length(CurrentHeight(t))));
            int logs = MaxLogsFor(t.Species, stage);
            if (IsFellable(t.Species))
            {
                if (!HarvestReady(t, out string needsStage)) rows.Add(("Harvest", "Not until it is " + needsStage));
                rows.Add(("Logs", logs > 0 ? $"up to {logs}  {HudBindings.GetItemName(YieldItem(t.Species))}" : "None yet (too young)"));
                string chopSpec = ToolSpec(t.Species);
                if (string.IsNullOrEmpty(chopSpec)) rows.Add(("Needs", DescribeTool(chopSpec) + " (active slot)"));
                else rows.Add(("@tools|Chop with", chopSpec));   // the panel rotates through the tools that accept this
                rows.Add(("Chops left", hitsLeft.ToString()));
            }
            GrowthRules fruit = FruitRules(t.Species);
            if (fruit != null)
            {
                float wait = t.PickedUntil - VegetationSeasons.GrowthDay;
                float untilAge = RipeAge(t.Species) - AgeDays(t);
                int fruitLeft = FruitLeft(t), fruitTotal = FruitTotal(t.Species);
                if (untilAge > 0f) rows.Add(("Fruit", $"Bears fruit in {Mathf.CeilToInt(untilAge)} days"));
                else rows.Add(("Fruit", fruitLeft > 0
                    ? $"{fruitLeft} of {fruitTotal} left: " + (string.IsNullOrEmpty(fruit.FruitTool) ? "right-click to pick one" : "pick one with " + DescribeTool(fruit.FruitTool).ToLowerInvariant())
                    : $"All picked: ripe again in {Mathf.CeilToInt(Mathf.Max(wait, 0f))} days"));
                if (untilAge <= 0f && fruitLeft > 0 && !string.IsNullOrEmpty(fruit.FruitTool)) rows.Add(("@tools|Pick with", fruit.FruitTool));
            }
        }

        // ------------------------------------------------------------------ chopping

        public const string ChopClip = "Chop_Tree_RT";
        public const float SwingSeconds = 0.96f;     // length of the Chop_Tree_RT clip
        public const float ChopImpact = 0.15f;       // seconds into the clip where the axe lands (the hand bottoms out)

        /// <summary>One hit with the tool in the active slot. Returns true when the tree came down.</summary>
        public static bool TryChop(ForestTree tree, string heldId, Transform player)
        {
            if (tree == null || tree.Felled) return false;
            if (!IsFellable(tree.Species)) return false;   // the kit gives this species no yield: it is not harvested
            string spec = ToolSpec(tree.Species);
            if (!string.IsNullOrEmpty(spec) && !GrowthRegistry.ToolMatches(spec, heldId))
            {
                Debug.LogWarning($"[Chop] '{heldId}' is not a tool for {tree.Species} (needs {spec}); check the kit's yield.tool and tags.json.");
                Notify("Need a tool", $"You need {DescribeTool(spec).ToLowerInvariant()} in your active slot to chop this tree.");
                return false;
            }
            if (player != null)
            {
                Vector3 d = tree.Position - player.position;
                d.y = 0f;
                if (d.magnitude > ReachMetres)
                {
                    Notify("Too far", "Move closer to chop this tree.");
                    return false;
                }
            }
            if (Time.unscaledTime - _lastHit < HitCooldown) return false;
            _lastHit = Time.unscaledTime;

            if (!HarvestReady(tree, out string needStage))
            {
                Notify("Not ready", $"This tree can't be harvested until it reaches its {needStage} stage.");
                return false;
            }

            int stage = StageIndex(tree);
            tree.Hits++;

            // Every swing answers: a thock, wood chips, and the tree shudders (a live copy stands in for the baked one).
            Vector3 fromPlayer = player != null ? player.position : tree.Position - Vector3.forward;
            PlayChopSound(tree.Position + Vector3.up * 1f);
            SpawnChips(tree.Position + Vector3.up * 0.9f, (fromPlayer - tree.Position).normalized);
            if (tree.Hits < HitsNeeded[stage])
            {
                LiveTree live = BeginLive(tree);
                live.Kick(tree.Position - fromPlayer);
                return false;
            }

            string logItem = YieldItem(tree.Species);
            int logs = LogsFor(tree.Species, stage);
            List<string> uncut = UncutLogs(logItem, logs, stage);   // whole logs that lie where the tree falls, when the kit has them
            if (uncut != null) logs = 0;
            if (logs > 0)
            {
                int added = HudState.Active.AddItemToToolbar(logItem, logs, HudBindings.GetMaxStack(logItem));
                if (added <= 0)
                {
                    tree.Hits = HitsNeeded[stage] - 1;   // not felled: there is nowhere to put the logs
                    Notify("Toolbar full", "Make room on the toolbar to chop this tree.");
                    return false;
                }
                if (HudBindings.Instance != null) HudBindings.Instance.RefreshToolbar();
                if (added < logs) Notify("Toolbar full", "Some of the logs didn't fit and were lost.");
            }

            // More than one yield: the kit's extra drops come with a full-grown tree.
            GrowthRules felling = KitRules(tree.Species);
            var extras = new List<string>();
            if (felling != null && stage >= 3)
                foreach (GrowthDrop d in felling.YieldExtras)
                {
                    int n = d.Roll();
                    for (int i = 0; i < n; i++) extras.Add(d.ItemId);
                }

            Vector3 from = player != null ? player.position : tree.Position - Vector3.forward;
            Fell(tree, from, animate: true, uncut, extras);
            return true;
        }

        private static readonly string[] UncutSizeOrder = { "long", "medium", "medium", "small", "small", "small" };

        /// <summary>
        /// The uncut log items a felled tree leaves on the ground: a grown tree gives long logs and shorter ones, a young one
        /// fewer and shorter. Null when the species has no uncut log models in the kit (it then yields its cut logs to the toolbar).
        /// </summary>
        private static List<string> UncutLogs(string logItem, int count, int stage)
        {
            if (string.IsNullOrEmpty(logItem) || count <= 0) return null;
            var result = new List<string>();
            if (logItem.Contains("_uncut_"))
            {
                // The kit names the exact uncut log (a fruit tree's one long log): that many of it.
                if (!ItemRegistry.TryGet(logItem, out _)) return null;
                for (int i = 0; i < count; i++) result.Add(logItem);
                return result;
            }
            for (int i = 0; i < count; i++)
            {
                int k = stage >= 3 ? i : i + (stage <= 1 ? 3 : 1);
                string id = UncutItemId(logItem, UncutSizeOrder[Mathf.Min(k, UncutSizeOrder.Length - 1)]);
                if (id == null) return null;
                result.Add(id);
            }
            return result;
        }

        private static string UncutItemId(string logItem, string size)
        {
            foreach (string stem in new[] { logItem, logItem.Replace("willow", "willowood") })
            {
                string id = stem + "_uncut_" + size;
                if (ItemRegistry.TryGet(id, out _)) return id;
            }
            return null;
        }

        /// <summary>
        /// Fells a tree the player PLANTED (a model under a PlantedGrowth, not a baked forest tree) the way a generated one falls: the
        /// model topples away from the player, and where it lands its logs lie end to end along the trunk (the kit's uncut log
        /// models) and every other yield is scattered under the crown. A species with no uncut logs puts its logs on the toolbar.
        /// </summary>
        /// <summary>Swings a full-grown tree takes to fell (a planted tree is chopped at its mature size).</summary>
        public static int FullTreeHits => HitsNeeded[HitsNeeded.Length - 1];

        /// <summary>The thock and the wood chips of one swing at a tree.</summary>
        public static void ChopEffects(Vector3 treePos, Vector3 fromPlayer)
        {
            PlayChopSound(treePos + Vector3.up * 1f);
            Vector3 dir = fromPlayer - treePos;
            dir.y = 0f;
            SpawnChips(treePos + Vector3.up * 0.9f, dir.sqrMagnitude > 0.01f ? dir.normalized : Vector3.forward);
        }

        /// <summary>
        /// The radius of a planted tree's trunk, read off its model: the widest reach from the trunk's centre of the geometry in the
        /// lowest 0.4 m (the roots' flare is not counted, so it is the trunk itself). 0 when it can not be measured.
        /// </summary>
        public static float MeasureTrunkRadius(Transform model, Vector3 centre)
        {
            if (model == null) return 0f;
            float best = 0f;
            float floorY = centre.y;
            var verts = new List<Vector3>();
            foreach (MeshFilter mf in model.GetComponentsInChildren<MeshFilter>())
            {
                if (mf.sharedMesh == null) continue;
                mf.sharedMesh.GetVertices(verts);
                Matrix4x4 m = mf.transform.localToWorldMatrix;
                foreach (Vector3 lv in verts)
                {
                    Vector3 w = m.MultiplyPoint3x4(lv);
                    if (w.y < floorY + 0.15f || w.y > floorY + 0.6f) continue;
                    best = Mathf.Max(best, new Vector2(w.x - centre.x, w.z - centre.z).magnitude);
                }
            }
            return best > 0.02f && best < 3f ? best : 0f;
        }

        public static void FellPlanted(Transform model, Vector3 stump, Vector3 away, string logItem, int logs, List<string> extras)
        {
            away.y = 0f;
            if (away.sqrMagnitude < 0.01f) away = Vector3.forward;
            away.Normalize();

            List<string> uncut = UncutLogs(logItem, logs, 3);
            if (uncut == null && logs > 0 && !string.IsNullOrEmpty(logItem))
            {
                int added = HudState.Active.AddItemToToolbar(logItem, logs, HudBindings.GetMaxStack(logItem));
                if (HudBindings.Instance != null) HudBindings.Instance.RefreshToolbar();
                if (added < logs) Notify("Toolbar full", "Some of the logs didn't fit and were lost.");
            }

            float crown = 4f;
            if (model != null)
            {
                foreach (Collider c in model.GetComponentsInChildren<Collider>(true)) c.enabled = false;
                var bounds = new Bounds(model.position, Vector3.zero);
                foreach (Renderer r in model.GetComponentsInChildren<Renderer>()) bounds.Encapsulate(r.bounds);
                crown = Mathf.Max(1.5f, bounds.size.y * 0.7f);
                model.SetParent(null, true);
                var fall = model.gameObject.AddComponent<FallingModel>();
                fall.Begin(away, () =>
                {
                    if (uncut != null) DropUncutLogs(stump, away, uncut);
                    if (extras != null && extras.Count > 0) ScatterDrops(stump + away * crown, extras);
                });
            }
            else
            {
                if (uncut != null) DropUncutLogs(stump, away, uncut);
                if (extras != null && extras.Count > 0) ScatterDrops(stump + away * crown, extras);
            }
        }

        /// <summary>A stump for a planted tree of this species (the same shape as the one a felled forest tree leaves), under a parent.</summary>
        public static void BuildPlantedStump(string species, Transform parent, float trunkRadius = 0f)
        {
            SpeciesInfo sp = null;
            if (!string.IsNullOrEmpty(species)) Species.TryGetValue(species, out sp);
            if (sp == null) foreach (SpeciesInfo any in Species.Values) { sp = any; break; }
            if (sp == null) return;
            var go = new GameObject("TreeStump_" + species);
            go.transform.SetParent(parent, false);
            go.transform.localPosition = Vector3.zero;
            go.transform.localRotation = Quaternion.identity;
            // the cut is as wide as the trunk that was felled (measured off its model); unknown: the species' own trunk
            float w = trunkRadius > 0.01f ? trunkRadius / Mathf.Max(0.01f, sp.TrunkRadius) : 1f;
            go.transform.localScale = new Vector3(w, 1f, w);
            go.AddComponent<MeshFilter>().sharedMesh = StumpMesh(sp);
            var mr = go.AddComponent<MeshRenderer>();
            mr.sharedMaterials = new[] { sp.TrunkMat, CutWoodMat() };
            mr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.On;
        }

        /// <summary>The felled model of a planted tree: topples over, lies a moment, sinks and is removed.</summary>
        private sealed class FallingModel : MonoBehaviour
        {
            private const float FallTime = 1.3f, SinkDelay = 2.0f, SinkTime = 3.0f, SinkDepth = 4.5f;
            private Quaternion _baseRot;
            private Vector3 _axis, _restPos;
            private System.Action _onLanded;
            private float _t;

            public void Begin(Vector3 away, System.Action onLanded)
            {
                _baseRot = transform.rotation;
                _restPos = transform.position;
                _axis = Vector3.Cross(Vector3.up, away).normalized;
                _onLanded = onLanded;
            }

            private void Update()
            {
                _t += Time.deltaTime;
                float u = Mathf.Clamp01(_t / FallTime);
                if (u >= 1f && _onLanded != null) { System.Action landed = _onLanded; _onLanded = null; landed(); }
                float angle = Mathf.Lerp(0f, 92f, u * u);
                if (u >= 1f) angle = 88f + Mathf.Sin((_t - FallTime) * 9f) * Mathf.Exp(-(_t - FallTime) * 5f) * 4f;
                transform.rotation = Quaternion.AngleAxis(angle, -_axis) * _baseRot;
                float sink = _t - (FallTime + SinkDelay);
                if (sink > 0f)
                {
                    float k = Mathf.Clamp01(sink / SinkTime);
                    transform.position = _restPos + Vector3.down * (SinkDepth * k * k);
                    if (k >= 1f) Destroy(gameObject);
                }
            }
        }

        /// <summary>Drops loose items (a fruit tree's fruit) in a spread around a point, where the crown comes down.</summary>
        private static void ScatterDrops(Vector3 centre, List<string> items)
        {
            foreach (string id in items)
            {
                Vector2 o = Random.insideUnitCircle * 1.3f;
                WorldItem.TryDrop(id, centre + new Vector3(o.x, 0f, o.y));
            }
        }

        /// <summary>Lays the logs end to end along the line the tree fell, starting at its stump.</summary>
        private static void DropUncutLogs(Vector3 stump, Vector3 away, List<string> logs)
        {
            float yaw = Mathf.Atan2(-away.z, away.x) * Mathf.Rad2Deg;   // a log model lies along its local X
            float along = 0.5f;
            foreach (string id in logs)
            {
                float length = id.EndsWith("_long") ? 4f : id.EndsWith("_medium") ? 2.4f : 1.3f;
                Vector3 centre = stump + away * (along + length * 0.5f);
                WorldItem.TryDrop(id, centre, yaw);
                along += length + 0.25f;
            }
        }

        /// <summary>Removes the tree from its chunk mesh, leaves a stump and (optionally) lets a copy fall over.</summary>
        private static void Fell(ForestTree tree, Vector3 fellFrom, bool animate, List<string> uncutLogs = null, List<string> scatter = null)
        {
            tree.Felled = true;
            FelledPositions.Add(new Vector2(tree.Position.x, tree.Position.z));
            ForestSolids.MarkDirty();
            CollapseInMesh(tree);
            SpawnStump(tree);
            if (animate)
            {
                Vector3 away = tree.Position - fellFrom;
                away.y = 0f;
                if (away.sqrMagnitude < 0.01f) away = Vector3.forward;
                LiveTree live = BeginLive(tree);
                LiveTrees.Remove(tree);
                Vector3 dir = away.normalized;
                Vector3 stump = tree.Position;
                float crown = Mathf.Max(1.5f, CurrentHeight(tree) * 0.7f);
                bool anything = uncutLogs != null || (scatter != null && scatter.Count > 0);
                live.StartFall(dir, !anything ? (System.Action)null : () =>
                {
                    if (uncutLogs != null) DropUncutLogs(stump, dir, uncutLogs);
                    if (scatter != null) ScatterDrops(stump + dir * crown, scatter);
                });
            }
            else if (LiveTrees.TryGetValue(tree, out LiveTree stale))
            {
                LiveTrees.Remove(tree);
                if (stale != null) Object.Destroy(stale.gameObject);
            }
        }

        private static void CollapseInMesh(ForestTree tree)
        {
            if (tree.Mesh == null || tree.VertCount <= 0) return;
            List<Vector3> verts = VertexList(tree.Mesh);
            for (int i = 0; i < tree.VertCount; i++) verts[tree.VertStart + i] = tree.Position;   // every triangle degenerates
            tree.Mesh.SetVertices(verts);
        }

        // ------------------------------------------------------------------ stump and falling copy

        private static float ScaleNow(ForestTree tree) { return StageSize[StageIndex(tree)]; }

        private static Material CutWoodMat()
        {
            if (_cutWoodMat != null) return _cutWoodMat;
            Shader shader = Shader.Find("Homesteader/Vegetation") ?? Shader.Find("Universal Render Pipeline/Lit");
            _cutWoodMat = new Material(shader) { hideFlags = HideFlags.DontSave, name = "TreeCutWood" };
            _cutWoodMat.SetColor("_BaseColor", new Color(0.78f, 0.64f, 0.42f));
            if (_cutWoodMat.HasProperty("_SwayAmp")) _cutWoodMat.SetFloat("_SwayAmp", 0f);
            return _cutWoodMat;
        }

        private static Mesh StumpMesh(SpeciesInfo sp)
        {
            if (StumpMeshes.TryGetValue(sp.Name, out Mesh cached) && cached != null) return cached;
            const int sides = 8;
            float r0 = sp.TrunkRadius * 1.15f, r1 = sp.TrunkRadius, h = 0.4f;
            var v = new List<Vector3>();
            var n = new List<Vector3>();
            var bark = new List<int>();
            var cut = new List<int>();
            for (int i = 0; i < sides; i++)
            {
                float a0 = i * Mathf.PI * 2f / sides, a1 = (i + 1) * Mathf.PI * 2f / sides;
                Vector3 b0 = new Vector3(Mathf.Cos(a0) * r0, -0.05f, Mathf.Sin(a0) * r0), b1 = new Vector3(Mathf.Cos(a1) * r0, -0.05f, Mathf.Sin(a1) * r0);
                Vector3 t0 = new Vector3(Mathf.Cos(a0) * r1, h, Mathf.Sin(a0) * r1), t1 = new Vector3(Mathf.Cos(a1) * r1, h, Mathf.Sin(a1) * r1);
                Vector3 nrm = new Vector3(Mathf.Cos((a0 + a1) * 0.5f), 0.1f, Mathf.Sin((a0 + a1) * 0.5f)).normalized;
                int k = v.Count;
                v.Add(b0); v.Add(t0); v.Add(t1); v.Add(b1);
                n.Add(nrm); n.Add(nrm); n.Add(nrm); n.Add(nrm);
                bark.AddRange(new[] { k, k + 1, k + 2, k, k + 2, k + 3 });
                // top cap fan (cut wood)
                int c = v.Count;
                v.Add(new Vector3(0f, h, 0f)); v.Add(t0); v.Add(t1);
                n.Add(Vector3.up); n.Add(Vector3.up); n.Add(Vector3.up);
                cut.AddRange(new[] { c, c + 2, c + 1 });
            }
            var mesh = new Mesh { name = "Stump_" + sp.Name };
            mesh.SetVertices(v);
            mesh.SetNormals(n);
            mesh.subMeshCount = 2;
            mesh.SetTriangles(bark, 0);
            mesh.SetTriangles(cut, 1);
            mesh.RecalculateBounds();
            StumpMeshes[sp.Name] = mesh;
            return mesh;
        }

        private static void SpawnStump(ForestTree tree)
        {
            SpeciesInfo sp = Species[tree.Species];
            var go = new GameObject("TreeStump_" + tree.Species);
            if (_root != null) go.transform.SetParent(_root, true);
            float s = Mathf.Max(0.05f, tree.Scale.x * ScaleNow(tree));   // the cut is exactly as wide as the trunk was (see TrunkSize)
            go.transform.SetPositionAndRotation(tree.Position, Quaternion.Euler(0f, tree.Yaw, 0f));
            go.transform.localScale = new Vector3(s, 1f, s);
            go.AddComponent<MeshFilter>().sharedMesh = StumpMesh(sp);
            var mr = go.AddComponent<MeshRenderer>();
            mr.sharedMaterials = new[] { sp.TrunkMat, CutWoodMat() };
            mr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.On;
        }

        // ------------------------------------------------------------------ live copy: shudders when hit, then falls

        private static readonly Dictionary<ForestTree, LiveTree> LiveTrees = new Dictionary<ForestTree, LiveTree>();

        /// <summary>The cached vertex list of a chunk mesh (edit it, then SetVertices it back).</summary>
        public static List<Vector3> VertexListFor(Mesh mesh) => VertexList(mesh);

        private static List<Vector3> VertexList(Mesh mesh)
        {
            if (!VertexCache.TryGetValue(mesh, out List<Vector3> verts))
            {
                verts = new List<Vector3>(mesh.vertexCount);
                mesh.GetVertices(verts);
                VertexCache[mesh] = verts;
            }
            return verts;
        }

        /// <summary>Takes the baked tree out of its chunk mesh and stands a live copy in its place. Returns the copy.</summary>
        private static LiveTree BeginLive(ForestTree tree)
        {
            if (LiveTrees.TryGetValue(tree, out LiveTree existing) && existing != null) return existing;

            if (tree.Mesh != null && tree.VertCount > 0 && tree.SavedVerts == null)
            {
                List<Vector3> verts = VertexList(tree.Mesh);
                tree.SavedVerts = verts.GetRange(tree.VertStart, tree.VertCount).ToArray();
                CollapseInMesh(tree);
            }

            SpeciesInfo sp = Species[tree.Species];
            var go = new GameObject("ChoppingTree_" + tree.Species);
            float s = ScaleNow(tree);
            go.transform.SetPositionAndRotation(tree.Position, Quaternion.Euler(0f, tree.Yaw, 0f));
            go.transform.localScale = new Vector3(tree.Scale.x * s, tree.Scale.y * s, tree.Scale.z * s);
            go.AddComponent<MeshFilter>().sharedMesh = sp.Variants[tree.Variant];
            var mr = go.AddComponent<MeshRenderer>();
            mr.sharedMaterials = sp.FruitMat != null ? new[] { sp.TrunkMat, sp.CrownMats[tree.CrownMat], sp.FruitMat } : new[] { sp.TrunkMat, sp.CrownMats[tree.CrownMat] };
            mr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.On;

            LiveTree live = go.AddComponent<LiveTree>();
            live.Tree = tree;
            LiveTrees[tree] = live;
            return live;
        }

        /// <summary>The player stopped hitting it: put the baked tree back and remove the live copy.</summary>
        private static void EndLive(ForestTree tree)
        {
            if (!LiveTrees.TryGetValue(tree, out LiveTree live)) return;
            LiveTrees.Remove(tree);
            if (!tree.Felled && tree.SavedVerts != null && tree.Mesh != null)
            {
                List<Vector3> verts = VertexList(tree.Mesh);
                for (int i = 0; i < tree.SavedVerts.Length; i++) verts[tree.VertStart + i] = tree.SavedVerts[i];
                tree.Mesh.SetVertices(verts);
                tree.SavedVerts = null;
            }
            if (live != null) Object.Destroy(live.gameObject);
        }

        private sealed class LiveTree : MonoBehaviour
        {
            [System.NonSerialized] public ForestTree Tree;
            private Quaternion _baseRot;
            private Vector3 _axis = Vector3.right;
            private float _angle, _vel, _idle;
            private bool _falling;
            private float _fallT;
            private const float FallDuration = 1.3f;
            private const float SinkDelay = 2.0f;      // seconds it lies still after landing
            private const float SinkDuration = 3.0f;
            private const float SinkDepth = 4.5f;      // deeper than the crown is wide, so nothing pokes out before it is removed
            private Vector3 _restPos;

            private void Awake() { _baseRot = transform.rotation; _restPos = transform.position; }

            /// <summary>A hit: the top rocks away from the player and settles back.</summary>
            public void Kick(Vector3 away)
            {
                away.y = 0f;
                if (away.sqrMagnitude < 0.01f) away = Vector3.forward;
                _axis = Vector3.Cross(Vector3.up, away.normalized).normalized;
                _vel += 70f;      // degrees per second
                _idle = 0f;
            }

            private System.Action _onLanded;

            public void StartFall(Vector3 away, System.Action onLanded = null)
            {
                _onLanded = onLanded;
                _axis = Vector3.Cross(Vector3.up, away).normalized;
                _falling = true;
                _fallT = 0f;
            }

            private void Update()
            {
                float dt = Time.deltaTime;
                if (_falling)
                {
                    _fallT += dt;
                    float u = Mathf.Clamp01(_fallT / FallDuration);
                    if (u >= 1f && _onLanded != null) { System.Action landed = _onLanded; _onLanded = null; landed(); }   // the logs drop where it lands
                    float angle = Mathf.Lerp(0f, 92f, u * u);          // slow start, then it goes
                    if (u >= 1f) angle = 88f + Mathf.Sin((_fallT - FallDuration) * 9f) * Mathf.Exp(-(_fallT - FallDuration) * 5f) * 4f;
                    transform.rotation = Quaternion.AngleAxis(angle, -_axis) * _baseRot;

                    // Lies there a moment, then sinks into the ground before it is removed.
                    float sinkT = _fallT - (FallDuration + SinkDelay);
                    if (sinkT > 0f)
                    {
                        float k = Mathf.Clamp01(sinkT / SinkDuration);
                        transform.position = _restPos + Vector3.down * (SinkDepth * k * k);
                        if (k >= 1f) Destroy(gameObject);
                    }
                    return;
                }

                // A damped spring around upright.
                float acc = -190f * _angle - 9f * _vel;
                _vel += acc * dt;
                _angle += _vel * dt;
                transform.rotation = Quaternion.AngleAxis(_angle, -_axis) * _baseRot;

                _idle += dt;
                if (_idle > 4f && Mathf.Abs(_angle) < 0.4f && Tree != null) EndLive(Tree);
            }
        }

        // ------------------------------------------------------------------ wood chips

        private static ParticleSystem _chips;

        private static void SpawnChips(Vector3 at, Vector3 towardPlayer)
        {
            if (_chips == null)
            {
                var go = new GameObject("TreeChips");
                _chips = go.AddComponent<ParticleSystem>();
                var main = _chips.main;
                main.playOnAwake = false;
                main.loop = false;
                main.startLifetime = 0.7f;
                main.startSpeed = new ParticleSystem.MinMaxCurve(2.2f, 4.5f);
                main.startSize = new ParticleSystem.MinMaxCurve(0.05f, 0.11f);
                main.startColor = new ParticleSystem.MinMaxGradient(new Color(0.55f, 0.40f, 0.24f), new Color(0.75f, 0.58f, 0.36f));
                main.gravityModifier = 1.6f;
                main.simulationSpace = ParticleSystemSimulationSpace.World;
                main.maxParticles = 80;
                var emission = _chips.emission;
                emission.enabled = false;
                var shape = _chips.shape;
                shape.shapeType = ParticleSystemShapeType.Cone;
                shape.angle = 40f;
                shape.radius = 0.05f;
                var renderer = go.GetComponent<ParticleSystemRenderer>();
                Shader sh = Shader.Find("Universal Render Pipeline/Particles/Unlit") ?? Shader.Find("Sprites/Default");
                var mat = new Material(sh) { hideFlags = HideFlags.DontSave };
                mat.SetColor("_BaseColor", Color.white);
                renderer.sharedMaterial = mat;
            }
            _chips.transform.position = at;
            _chips.transform.rotation = Quaternion.LookRotation(towardPlayer.sqrMagnitude > 0.01f ? towardPlayer : Vector3.up, Vector3.up) * Quaternion.Euler(-35f, 0f, 0f);
            _chips.Emit(12);
        }

        // ------------------------------------------------------------------ save and load

        /// <summary>Positions (x, z) of every felled tree, for GameSave.</summary>
        public static List<Vector2> SavedFelled() { return new List<Vector2>(FelledPositions); }

        /// <summary>Re-fells saved trees after the world has been generated: no logs, no animation.</summary>
        public static void ApplyFelled(List<Vector2> felled)
        {
            if (felled == null) return;
            foreach (Vector2 p in felled)
            {
                ForestTree best = null;
                float bestD = 0.6f * 0.6f;
                for (int i = 0; i < Trees.Count; i++)
                {
                    ForestTree t = Trees[i];
                    if (t.Felled) continue;
                    float dx = t.Position.x - p.x, dz = t.Position.z - p.y;
                    float d = dx * dx + dz * dz;
                    if (d < bestD) { bestD = d; best = t; }
                }
                if (best != null) Fell(best, best.Position - Vector3.forward, animate: false);
            }
        }
    }
}
