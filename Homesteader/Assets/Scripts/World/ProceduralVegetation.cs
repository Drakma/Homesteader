using System.Collections.Generic;
using UnityEngine;
using Homesteader.Generation;
using Homesteader.Growth;

namespace Homesteader.World
{
    /// <summary>
    /// Procedural world dressing: flat-shaded low-poly meshes built in code (no Meshy, no GLB) and scattered
    /// by biome after terrain generation. Trees in the forest biomes, rocks and scree on the rocky ridge,
    /// cattails and rocks on shorelines, rocks and woodland debris on river and lake beds, flower clumps
    /// large grass tufts on the prairie, and flower clumps in the meadow (pasture). See docs/PROCEDURAL_VEGETATION.md.
    ///
    /// No colliders (the player walks through them), no saving (deterministic from the world seed, rebuilt
    /// with the world every time).
    /// </summary>
    public static class ProceduralVegetation
    {
        private const string RootName = "ProceduralVegetation";
        private const float MinTreeDistance = 2.8f;      // metres, minimum between any two trees
        public const float TreeScale = 0.5625f;           // global size multiplier
        private const float CandidateSpacing = 2.2f;  // metres between scatter candidates (jittered)
        private const int VariantsPerSpecies = 4;
        private const int CrownTintsPerSpecies = 3;

        private enum Shape { Round, Oval, Columnar, Broad, Conifer, Orchard, Weeping, Birch }

        private sealed class Species
        {
            public string Name;
            public Shape Shape;
            public Color Trunk;
            public Color Crown;
            public float HeightMin, HeightMax;
            public float Density;            // 0..1 chance a candidate in this biome becomes a tree
            public bool Evergreen;           // keeps its crown all year (conifers)
            public Vector4 AgeStages;        // game-day ends of sapling / small / medium stages (w = 1 enables ageing in the shader)
            public string[] Autumn;          // autumn crown colours, one per crown tint
            public Mesh[] Variants;
            public Mesh[] DeadVariants;
            public Material TrunkMat;
            public Material DeadMat;
            public Material[] CrownMats;

            // fruit trees: the fruit is its own submesh at the END of each variant's vertices, so picking can hide just the fruit
            public Color FruitColor;
            public int FruitCount;           // fruits per tree (0 = not a fruit tree)
            public Material FruitMat;
            public int[] FruitFirstVert;     // per variant: index of the first fruit vertex
            public int[] FruitVertCount;     // per variant: how many fruit vertices
            public float FruitRipeAge;       // tree age (game days) from which the fruit is on the tree, from the kit's fruiting stage
            public float Scatter = 1f;       // chance a candidate in its biome becomes this species (1 = every one, as the forests do)
        }

        // Species, by the biome ids that use them. "biome_mixed_forest" picks from several at random.
        private static Dictionary<string, Species[]> Build()
        {
            var maple = new Species { Name = "maple", Shape = Shape.Round, Trunk = Hex("#6b5440"), Crown = Hex("#4f9a32"), HeightMin = 8f, HeightMax = 12f, Density = 0.45f, Autumn = new[] { "#c8401f", "#d8772a", "#d9a12f" } };
            var birch = new Species { Name = "birch", Shape = Shape.Birch, Trunk = Hex("#f1eee6"), Crown = Hex("#7cb848"), HeightMin = 7f, HeightMax = 10f, Density = 0.42f, Autumn = new[] { "#e2c23a", "#d9a82c", "#ecd24e" } };
            var oak = new Species { Name = "oak", Shape = Shape.Broad, Trunk = Hex("#4d3b2b"), Crown = Hex("#3c7a2a"), HeightMin = 8f, HeightMax = 11f, Density = 0.40f, Autumn = new[] { "#a8541f", "#b8742a", "#8c4a22" } };
            var poplar = new Species { Name = "poplar", Shape = Shape.Columnar, Trunk = Hex("#8a7a5c"), Crown = Hex("#5da23a"), HeightMin = 11f, HeightMax = 15f, Density = 0.42f, Autumn = new[] { "#dcb62f", "#e6c53c", "#cfa226" } };
            var pine = new Species { Name = "pine", Shape = Shape.Conifer, Trunk = Hex("#51392a"), Crown = Hex("#265a33"), HeightMin = 9f, HeightMax = 15f, Density = 0.50f, Evergreen = true };

            // Fruit trees (kit groups apple / lemon / orange) and the weeping willow. The fruit trees are scattered thinly through
            // the open biomes, the willow along the banks (see Generate).
            var apple = new Species { Name = "apple", Shape = Shape.Orchard, Trunk = Hex("#5b4636"), Crown = Hex("#5f9f35"), HeightMin = 4.6f, HeightMax = 6.4f, Density = 0.3f, Scatter = 0.05f, FruitColor = Hex("#c8281e"), FruitCount = 24, Autumn = new[] { "#c8a02f", "#d9a12f", "#b8782a" } };
            var lemon = new Species { Name = "lemon", Shape = Shape.Orchard, Trunk = Hex("#6a5440"), Crown = Hex("#4f9a38"), HeightMin = 4.2f, HeightMax = 5.8f, Density = 0.3f, Scatter = 0.04f, Evergreen = true, FruitColor = Hex("#eed84a"), FruitCount = 26 };
            var orange = new Species { Name = "orange", Shape = Shape.Orchard, Trunk = Hex("#5e4a38"), Crown = Hex("#3f8a2e"), HeightMin = 4.4f, HeightMax = 6.0f, Density = 0.3f, Scatter = 0.04f, Evergreen = true, FruitColor = Hex("#f08a1e"), FruitCount = 26 };
            var willow = new Species { Name = "willow", Shape = Shape.Weeping, Trunk = Hex("#6b5e4a"), Crown = Hex("#7fae48"), HeightMin = 8f, HeightMax = 11.5f, Density = 0.5f, Scatter = 0.55f, Autumn = new[] { "#d9c23c", "#c9b030", "#e0cc50" } };
            s_willow = willow;
            s_fruitTrees = new[] { apple, lemon, orange };
            // every tree is built 20% taller than its table height, the willow 40% (their crowns, trunks and fruit scale with the height)
            foreach (Species s in new[] { maple, birch, oak, poplar, pine, apple, lemon, orange, willow })
            {
                float k = s == willow ? WillowHeightScale : TreeHeightScale;
                s.HeightMin *= k;
                s.HeightMax *= k;
            }

            foreach (Species s in new[] { maple, birch, oak, poplar, pine, apple, lemon, orange, willow }) BuildAssets(s);
            foreach (Species s in new[] { maple, birch, oak, poplar, pine, apple, lemon, orange, willow })
            {
                ForestTrees.RegisterSpecies(new ForestTrees.SpeciesInfo
                {
                    Name = s.Name,
                    Display = char.ToUpperInvariant(s.Name[0]) + s.Name.Substring(1),
                    LogItemId = LogItemFor(s.Name),
                    Variants = s.Variants,
                    DeadVariants = s.DeadVariants,
                    TrunkMat = s.TrunkMat,
                    DeadMat = s.DeadMat,
                    CrownMats = s.CrownMats,
                    AgeStages = s.AgeStages,
                    TrunkRadius = Mathf.Max(s.Shape == Shape.Orchard ? 0.14f : 0.22f, (s.HeightMin + s.HeightMax) * 0.5f * (s.Shape == Shape.Broad ? 0.045f : (s.Shape == Shape.Orchard ? 0.04f : 0.032f))),
                    FruitMat = s.FruitMat,
                    FruitFirstVert = s.FruitFirstVert,
                    FruitVertCount = s.FruitVertCount,
                    FruitCount = s.FruitCount,
                    FruitRipeAge = s.FruitRipeAge,
                });
            }

            // A sapling of one of these species grows the same procedural tree the forests use (see ForestTrees.ApplyPlantPrefabs).
            ForestTrees.ApplyPlantPrefabs();
            // Crops (corn, wheat, pumpkin, ...) are drawn procedurally too: their groups' stage prefabs become the ProceduralCrops looks.
            ProceduralCrops.ApplyCropPrefabs();

            return new Dictionary<string, Species[]>
            {
                { "biome_maple_forest", new[] { maple } },
                { "biome_birch_forest", new[] { birch } },
                { "biome_oak_forest", new[] { oak } },
                { "biome_poplar_forest", new[] { poplar } },
                { "biome_pine_hills", new[] { pine } },
                { "biome_mixed_forest", new[] { maple, oak, birch, pine } },
                { "biome_wetland_marsh", new[] { willow } },
                { "biome_willow_grove", new[] { willow } },
            };
        }

        private static Species s_willow;
        private const float TreeHeightScale = 1.2f, WillowHeightScale = 1.4f;
        private static Species[] s_fruitTrees;

        // Fruit trees are an extremely rare find: this chance (per tree placed) turns an ordinary tree in a TREE biome into one.
        private const float FruitTreeChance = 0.006f;

        // Fraction of the trees in the TREE biomes that is left out (a lighter, more open forest).
        private const float ForestThinning = 0f;
        private static bool IsTreeBiome(string id)
        {
            return id == "biome_maple_forest" || id == "biome_birch_forest" || id == "biome_oak_forest"
                || id == "biome_poplar_forest" || id == "biome_pine_hills" || id == "biome_mixed_forest";
        }

        private static float Hash01(float x, float z, int seed)
        {
            unchecked
            {
                int h = seed * 73856093 ^ Mathf.FloorToInt(x * 7.1f) * 19349663 ^ Mathf.FloorToInt(z * 7.1f) * 83492791;
                h ^= h >> 13; h *= 1274126177; h ^= h >> 16;
                return (h & 0xffff) / 65535f;
            }
        }

        /// <summary>Scatters the trees. Returns how many were placed.</summary>
        public static int Generate(HomesteaderTerrainGenerator gen)
        {
            Terrain terrain = gen.GetComponent<Terrain>();
            if (terrain == null) return 0;

            Transform old = gen.transform.Find(RootName);
            if (old != null)
            {
                // the old chunk meshes are runtime meshes nothing else owns: destroying only the objects left them in memory, a world's worth each time
                // one was regenerated (New Game, Load, a new Play session in the editor)
                foreach (MeshFilter mf in old.GetComponentsInChildren<MeshFilter>(true))
                    if (mf.sharedMesh != null && mf.sharedMesh.name.StartsWith("VegChunk_")) Object.DestroyImmediate(mf.sharedMesh);
                Object.DestroyImmediate(old.gameObject);
            }
            var root = new GameObject(RootName).transform;
            root.SetParent(gen.transform, false);
            Tracked.Clear();
            Births.Clear();
            VegetationSeasons.GrowthDay = WorldStartDay;   // a new world starts its trees' clock again (a load restores it)
            TreeByTransform.Clear();
            ForestTrees.Begin(root);
            ForestSolids.Clear();
            WorldRocks.Clear();
            FarmlandSoil.Clear();   // a new world has no tilled ground (a load tills its squares again)
            BerryBushes.Clear();
            BushByTransform.Clear();

            Dictionary<string, Species[]> bySpeciesBiome = Build();
            Vector3 origin = gen.transform.position;
            var rng = new System.Random(gen.worldSeed * 31 + 7);
            float noiseSeed = (gen.worldSeed % 997) * 0.37f;

            int placed = 0;
            var taken = new Dictionary<Vector2Int, Vector2>();
            for (float z = 0f; z < gen.terrainSizeZ; z += CandidateSpacing)
            {
                for (float x = 0f; x < gen.terrainSizeX; x += CandidateSpacing)
                {
                    float rx = x + (float)(rng.NextDouble() - 0.5) * CandidateSpacing * 0.9f;
                    float rz = z + (float)(rng.NextDouble() - 0.5) * CandidateSpacing * 0.9f;
                    // Trees stand on the planting grid, on the centre of a cell, like everything the player places (PlantingValidator.SnapToGrid).
                    Vector3 cell = PlantingValidator.SnapToGrid(new Vector3(origin.x + rx, 0f, origin.z + rz));
                    rx = cell.x - origin.x; rz = cell.z - origin.z;
                    if (rx < 2f || rz < 2f || rx > gen.terrainSizeX - 2f || rz > gen.terrainSizeZ - 2f) continue;

                    BiomeData biome = gen.EvaluateBiomeAt(rx, rz);
                    if (biome == null) continue;
                    bySpeciesBiome.TryGetValue(biome.id, out Species[] options);

                    // Stands with clearings: a slow noise field thins the trees out in patches.
                    if (options == null) continue;
                    Species species = options[rng.Next(options.Length)];
                    if (species.Scatter < 1f && rng.NextDouble() > species.Scatter) continue;   // marsh and grove willows are thin
                    // A hash, not the rng, so the forests keep the layout they had.
                    if (s_fruitTrees != null && IsTreeBiome(biome.id) && Hash01(rx, rz, gen.worldSeed + 5) < FruitTreeChance)
                        species = s_fruitTrees[Mathf.Min(s_fruitTrees.Length - 1, (int)(Hash01(rz, rx, gen.worldSeed + 9) * s_fruitTrees.Length))];

                    // Keep off the water and its banks, and off steep ground.
                    if (gen.IsWaterAt(rx, rz) || gen.IsWaterAt(rx + 3f, rz) || gen.IsWaterAt(rx - 3f, rz)
                        || gen.IsWaterAt(rx, rz + 3f) || gen.IsWaterAt(rx, rz - 3f)) continue;
                    float steepness = terrain.terrainData.GetSteepness(rx / gen.terrainSizeX, rz / gen.terrainSizeZ);
                    if (steepness > 30f) continue;
                    if (gen.IsNearRoad(rx, rz, 3f)) continue;   // a clear verge either side of the road

                    // Enforce a minimum distance to every already-placed tree (3 m grid hash, check 3x3 cells).
                    int cx = Mathf.FloorToInt(rx / MinTreeDistance), cz = Mathf.FloorToInt(rz / MinTreeDistance);
                    bool tooClose = false;
                    for (int ox = -1; ox <= 1 && !tooClose; ox++)
                        for (int oz = -1; oz <= 1 && !tooClose; oz++)
                            if (taken.TryGetValue(new Vector2Int(cx + ox, cz + oz), out Vector2 p)
                                && (p - new Vector2(rx, rz)).sqrMagnitude < MinTreeDistance * MinTreeDistance)
                                tooClose = true;
                    if (tooClose) continue;
                    taken[new Vector2Int(cx, cz)] = new Vector2(rx, rz);

                    // The forests are thinned (cheaper to draw). The skipped spot still counts as taken, so the neighbours do not just fill the gap.
                    if (species.Scatter >= 1f && IsTreeBiome(biome.id) && Hash01(rx, rz, gen.worldSeed + 11) < ForestThinning) continue;

                    float wx = origin.x + rx, wz = origin.z + rz;
                    float wy = terrain.SampleHeight(new Vector3(wx, 0f, wz)) + origin.y;

                    var go = new GameObject("Tree_" + species.Name);
                    go.transform.SetParent(root, false);
                    go.transform.position = new Vector3(wx, wy - 0.15f, wz);
                    go.transform.rotation = Quaternion.Euler(0f, (float)(rng.NextDouble() * 360.0), 0f);
                    float scale = (0.85f + (float)rng.NextDouble() * 0.3f) * TreeScale;
                    go.transform.localScale = new Vector3(scale, scale * (0.92f + (float)rng.NextDouble() * 0.16f), scale);

                    float age = RollAge(species.AgeStages, rng);
                    if (species.FruitCount > 0 && species.FruitRipeAge > 0f && age > species.AgeStages.z && rng.NextDouble() < 0.75)
                        age = species.FruitRipeAge + (float)rng.NextDouble() * 60f;   // most grown fruit trees are already bearing
                    float birth = WorldStartDay - age;
                    Births[go.transform] = birth;

                    int variant = rng.Next(species.Variants.Length);
                    int crown = rng.Next(species.CrownMats.Length);
                    go.AddComponent<MeshFilter>().sharedMesh = species.Variants[variant];
                    var mr = go.AddComponent<MeshRenderer>();
                    mr.sharedMaterials = species.FruitMat != null
                        ? new[] { species.TrunkMat, species.CrownMats[crown], species.FruitMat }
                        : new[] { species.TrunkMat, species.CrownMats[crown] };

                    // Choppable: remember what this tree is (see ForestTrees.cs).
                    var record = new ForestTree
                    {
                        Species = species.Name, Variant = variant, CrownMat = crown,
                        Position = go.transform.position, Yaw = go.transform.eulerAngles.y, Scale = go.transform.localScale,
                        Birth = birth, FullHeight = species.Variants[variant].bounds.size.y * go.transform.localScale.y,
                    };
                    ForestTrees.Register(record);
                    ForestSolids.AddTree(record);
                    TreeByTransform[go.transform] = record;
                    mr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.On;
                    placed++;
                }
            }

            int rocks = ScatterRocks(gen, terrain, root, rng);
            int shore = ScatterShore(gen, terrain, root, rng);
            int bed = ScatterBed(gen, terrain, root, rng);
            int flowers = ScatterFlowers(gen, terrain, root, rng);
            int fieldStones = ScatterFieldStones(gen, terrain, root, rng);
            int tufts = ScatterTufts(gen, terrain, root, rng);
            int shrubs = ScatterShrubs(gen, terrain, root, rng);
            int objects = root.childCount;
            int chunks = Combine(root);
            ForestSolids.StartStreaming(root);
            ForestTrees.RefreshFruit();   // young trees start with no fruit on them (the baked meshes carry it until this)
            root.gameObject.AddComponent<VegetationSeasons>().Init(new List<VegetationSeasons.Entry>(Tracked));
            root.gameObject.AddComponent<VegetationFocusFade>();
            BerryBushes.Started(root);   // small plants fade with distance from the view centre
            Dbg.Log($"[Vegetation] Placed {placed} trees, {rocks} rocks, {fieldStones} field stones, {shore} shoreline cattails/rocks, {bed} bed rocks/debris, {flowers} flower clumps, {tufts} grass tufts and {shrubs} shrubs ({objects} objects merged into {chunks} chunk meshes).");
            return placed;
        }

        // ------------------------------------------------------------------ merging into chunk meshes

        private const float ChunkSize = 32f;   // metres; each chunk is one mesh per shadow mode, so it culls as a unit

        private sealed class ChunkBuild
        {
            public readonly List<Vector3> V = new List<Vector3>();
            public readonly List<Vector3> N = new List<Vector3>();
            public readonly List<Vector2> U1 = new List<Vector2>();   // object origin (world x, z)
            public readonly List<Vector2> U2 = new List<Vector2>();   // object origin world y, uniform scale
            public readonly List<Vector2> U3 = new List<Vector2>();   // birth day (trees), unused
            public readonly Dictionary<Material, List<int>> Tris = new Dictionary<Material, List<int>>();
        }

        /// <summary>
        /// Bakes every scattered object into a few big chunk meshes (world-space vertices), then removes the objects.
        /// Tens of thousands of separate renderers cost far more CPU than a few hundred chunk draws. Each vertex keeps
        /// the origin and scale of its source object (UV1, UV2) so the Vegetation shader can still sway and grow per object.
        /// </summary>
        private static int Combine(Transform root)
        {
            var cache = new Dictionary<Mesh, (Vector3[] v, Vector3[] n, int[][] t)>();
            var chunks = new Dictionary<(int, int, bool), ChunkBuild>();
            var kids = new List<Transform>();
            foreach (Transform c in root) kids.Add(c);

            foreach (Transform c in kids)
            {
                var mf = c.GetComponent<MeshFilter>();
                var mr = c.GetComponent<MeshRenderer>();
                if (mf == null || mr == null || mf.sharedMesh == null) continue;

                Mesh m = mf.sharedMesh;
                if (!cache.TryGetValue(m, out var data))
                {
                    var tris = new int[m.subMeshCount][];
                    for (int i = 0; i < tris.Length; i++) tris[i] = m.GetTriangles(i);
                    data = (m.vertices, m.normals, tris);
                    cache[m] = data;
                }

                Matrix4x4 M = c.localToWorldMatrix;
                Vector3 o = c.position;
                float sc = c.lossyScale.x;
                float birth = Births.TryGetValue(c, out float b) ? b : 0f;
                bool cast = mr.shadowCastingMode != UnityEngine.Rendering.ShadowCastingMode.Off;
                var key = (Mathf.FloorToInt(o.x / ChunkSize), Mathf.FloorToInt(o.z / ChunkSize), cast);
                if (!chunks.TryGetValue(key, out ChunkBuild cb)) { cb = new ChunkBuild(); chunks[key] = cb; }

                int baseIdx = cb.V.Count;
                if (TreeByTransform.TryGetValue(c, out ForestTree tree)) { tree.ChunkKey = key; tree.VertStart = baseIdx; tree.VertCount = data.v.Length; }
                if (BushByTransform.TryGetValue(c, out BerryBush bush)) { bush.ChunkKey = key; bush.VertStart = baseIdx; bush.VertCount = data.v.Length; }
                if (WorldRocks.ByTransform.TryGetValue(c, out WorldRock rock)) { rock.ChunkKey = key; rock.VertStart = baseIdx; rock.VertCount = data.v.Length; }
                for (int i = 0; i < data.v.Length; i++)
                {
                    cb.V.Add(M.MultiplyPoint3x4(data.v[i]));
                    cb.N.Add(M.MultiplyVector(data.n[i]).normalized);
                    cb.U1.Add(new Vector2(o.x, o.z));
                    cb.U2.Add(new Vector2(o.y, sc));
                    cb.U3.Add(new Vector2(birth, 0f));
                }

                Material[] mats = mr.sharedMaterials;
                for (int j = 0; j < data.t.Length; j++)
                {
                    Material mat = mats[Mathf.Min(j, mats.Length - 1)];
                    if (!cb.Tris.TryGetValue(mat, out List<int> list)) { list = new List<int>(); cb.Tris[mat] = list; }
                    int[] src = data.t[j];
                    for (int k = 0; k < src.Length; k++) list.Add(baseIdx + src[k]);
                }
            }

            foreach (Transform c in kids) Object.DestroyImmediate(c.gameObject);

            var meshByKey = new Dictionary<(int, int, bool), Mesh>();
            foreach (var kv in chunks)
            {
                ChunkBuild cb = kv.Value;
                var mats = new List<Material>(cb.Tris.Keys);
                var mesh = new Mesh { name = "VegChunk_" + kv.Key.Item1 + "_" + kv.Key.Item2 };
                mesh.indexFormat = UnityEngine.Rendering.IndexFormat.UInt32;
                mesh.SetVertices(cb.V);
                mesh.SetNormals(cb.N);
                mesh.SetUVs(1, cb.U1);
                mesh.SetUVs(2, cb.U2);
                mesh.SetUVs(3, cb.U3);
                mesh.subMeshCount = mats.Count;
                for (int i = 0; i < mats.Count; i++) mesh.SetTriangles(cb.Tris[mats[i]], i);
                mesh.RecalculateBounds();
                meshByKey[kv.Key] = mesh;

                var go = new GameObject("VegChunk_" + kv.Key.Item1 + "_" + kv.Key.Item2 + (kv.Key.Item3 ? "" : "_ns"));
                go.transform.SetParent(root, false);
                go.transform.SetPositionAndRotation(Vector3.zero, Quaternion.identity);   // vertices are already world space
                go.AddComponent<MeshFilter>().sharedMesh = mesh;
                var mr = go.AddComponent<MeshRenderer>();
                mr.sharedMaterials = mats.ToArray();
                mr.shadowCastingMode = kv.Key.Item3 ? UnityEngine.Rendering.ShadowCastingMode.On : UnityEngine.Rendering.ShadowCastingMode.Off;
            }
            foreach (ForestTree t in TreeByTransform.Values)
                if (meshByKey.TryGetValue(t.ChunkKey, out Mesh m)) t.Mesh = m;
            foreach (BerryBush bb in BushByTransform.Values)
                if (meshByKey.TryGetValue(bb.ChunkKey, out Mesh bm)) bb.Mesh = bm;
            foreach (WorldRock wr in WorldRocks.ByTransform.Values)
                if (meshByKey.TryGetValue(wr.ChunkKey, out Mesh rm)) wr.Mesh = rm;
            return chunks.Count;
        }

        // ------------------------------------------------------------------ rocks and scree (rocky ridge biome)

        private const float RockSpacing = 1.3f;   // candidate grid for rocks and scree, metres

        private static int ScatterRocks(HomesteaderTerrainGenerator gen, Terrain terrain, Transform root, System.Random rng)
        {
            Shader lit = Shader.Find("Universal Render Pipeline/Lit");
            Material[] mats =
            {
                MakeMat(lit, Hex("#7b7b7d")), MakeMat(lit, Hex("#8c8983")), MakeMat(lit, Hex("#66666a")),
            };

            // Mesh variants per size class: boulders, rocks, scree stones.
            Mesh[] boulders = BuildRockMeshes("Boulder", 6, 0.9f, 1.6f, 100);
            Mesh[] stones = BuildRockMeshes("Rock", 6, 0.35f, 0.7f, 200);
            Mesh[] scree = BuildRockMeshes("Scree", 6, 0.1f, 0.25f, 300);

            Vector3 origin = gen.transform.position;
            int placed = 0;
            for (float z = 0f; z < gen.terrainSizeZ; z += RockSpacing)
            {
                for (float x = 0f; x < gen.terrainSizeX; x += RockSpacing)
                {
                    float rx = x + (float)(rng.NextDouble() - 0.5) * RockSpacing;
                    float rz = z + (float)(rng.NextDouble() - 0.5) * RockSpacing;
                    if (rx < 1f || rz < 1f || rx > gen.terrainSizeX - 1f || rz > gen.terrainSizeZ - 1f) continue;

                    BiomeData biome = gen.EvaluateBiomeAt(rx, rz);
                    if (biome == null || biome.id != "biome_rocky_ridge") continue;
                    if (gen.IsNearRoad(rx, rz, 0.8f)) continue;
                    if (gen.IsWaterAt(rx, rz) || gen.IsWaterAt(rx + 2f, rz) || gen.IsWaterAt(rx - 2f, rz)
                        || gen.IsWaterAt(rx, rz + 2f) || gen.IsWaterAt(rx, rz - 2f)) continue;

                    if (rng.NextDouble() < 0.5) continue;   // half as many

                    // Size class: mostly scree, some rocks, a few boulders.
                    double roll = rng.NextDouble();
                    Mesh[] set = roll < 0.04 ? boulders : (roll < 0.22 ? stones : scree);
                    // Boulders and rocks need a little more room than scree.
                    float scale = 0.8f + (float)rng.NextDouble() * 0.5f;

                    float wx = origin.x + rx, wz = origin.z + rz;
                    float wy = terrain.SampleHeight(new Vector3(wx, 0f, wz)) + origin.y;

                    var go = new GameObject("Rock");
                    go.transform.SetParent(root, false);
                    // Sunk a little so they sit in the ground on slopes.
                    go.transform.position = new Vector3(wx, wy - 0.05f * scale, wz);
                    go.transform.rotation = Quaternion.Euler((float)(rng.NextDouble() - 0.5) * 20f, (float)(rng.NextDouble() * 360.0), (float)(rng.NextDouble() - 0.5) * 20f);
                    go.transform.localScale = new Vector3(scale, scale * (0.6f + (float)rng.NextDouble() * 0.5f), scale);

                    { Mesh rockMesh = set[rng.Next(set.Length)]; go.AddComponent<MeshFilter>().sharedMesh = rockMesh; ForestSolids.AddRock(rockMesh, go.transform); WorldRocks.Register(go.transform, rockMesh); }
                    var mr = go.AddComponent<MeshRenderer>();
                    Material m = mats[rng.Next(mats.Length)];
                    mr.sharedMaterials = new[] { m, m };
                    mr.shadowCastingMode = set == scree
                        ? UnityEngine.Rendering.ShadowCastingMode.Off
                        : UnityEngine.Rendering.ShadowCastingMode.On;
                    placed++;
                }
            }
            return placed;
        }

        // ------------------------------------------------------------------ shoreline: cattails and rocks

        private const float ShoreSpacing = 1.0f;
        private const float ShoreBandMax = 2.6f;    // metres from the water's edge

        private static int ScatterShore(HomesteaderTerrainGenerator gen, Terrain terrain, Transform root, System.Random rng)
        {
            Shader lit = Shader.Find("Universal Render Pipeline/Lit");
            float[] catGrow = { 0.4f, 0.7f, 1f, 0.9f };
            Material stalkMat = Seasonal(MakeMat(lit, Hex("#5f8a3a"), 0.28f, 2f), Four("#8b7a4a", "#6fa040", "#5f8a3a", "#a39550"), catGrow);
            Material headMat = Seasonal(MakeMat(lit, Hex("#5a3a22"), 0.28f, 2f), null, catGrow);
            Material[] rockMats = { MakeMat(lit, Hex("#7b7b7d")), MakeMat(lit, Hex("#8c8983")), MakeMat(lit, Hex("#66666a")) };

            var clumps = new Mesh[6];
            for (int i = 0; i < clumps.Length; i++) clumps[i] = BuildCattailClump(new System.Random(500 + i * 17));
            Mesh[] rocks = BuildRockMeshes("ShoreRock", 6, 0.25f, 0.6f, 400);

            Vector3 origin = gen.transform.position;
            float shoreSeed = (gen.worldSeed % 983) * 0.29f;
            int placed = 0;
            for (float z = 0f; z < gen.terrainSizeZ; z += ShoreSpacing)
            {
                for (float x = 0f; x < gen.terrainSizeX; x += ShoreSpacing)
                {
                    float rx = x + (float)(rng.NextDouble() - 0.5) * ShoreSpacing;
                    float rz = z + (float)(rng.NextDouble() - 0.5) * ShoreSpacing;
                    if (rx < 1f || rz < 1f || rx > gen.terrainSizeX - 1f || rz > gen.terrainSizeZ - 1f) continue;
                    if (gen.IsWaterAt(rx, rz)) continue;

                    float d = gen.GetWaterDistance(rx, rz);
                    if (d > ShoreBandMax) continue;

                    // Cattails grow in groups: a noise field makes dense stands with bare shore between them.
                    float stand = Mathf.SmoothStep(0.45f, 0.6f, Mathf.PerlinNoise(rx * 0.12f + shoreSeed, rz * 0.12f));
                    bool cattail = d < 0.9f && rng.NextDouble() < 0.4 * stand;
                    bool rock = !cattail && rng.NextDouble() < 0.03;
                    if (!cattail && !rock) continue;

                    float wx = origin.x + rx, wz = origin.z + rz;
                    float wy = terrain.SampleHeight(new Vector3(wx, 0f, wz)) + origin.y;

                    var go = new GameObject(cattail ? "Cattail" : "ShoreRock");
                    go.transform.SetParent(root, false);
                    go.transform.rotation = Quaternion.Euler(0f, (float)(rng.NextDouble() * 360.0), 0f);
                    var mr = go.AddComponent<MeshRenderer>();
                    mr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
                    if (cattail)
                    {
                        float s = 0.8f + (float)rng.NextDouble() * 0.5f;
                        go.transform.position = new Vector3(wx, wy - 0.05f, wz);
                        go.transform.localScale = Vector3.one * (s * 0.7f);   // 30% smaller
                        go.AddComponent<MeshFilter>().sharedMesh = clumps[rng.Next(clumps.Length)];
                        mr.sharedMaterials = new[] { stalkMat, headMat };
                    }
                    else
                    {
                        float s = 0.8f + (float)rng.NextDouble() * 0.6f;
                        go.transform.position = new Vector3(wx, wy - 0.05f * s, wz);
                        go.transform.localScale = new Vector3(s, s * (0.6f + (float)rng.NextDouble() * 0.5f), s);
                        { Mesh rockMesh = rocks[rng.Next(rocks.Length)]; go.AddComponent<MeshFilter>().sharedMesh = rockMesh; ForestSolids.AddRock(rockMesh, go.transform); WorldRocks.Register(go.transform, rockMesh); }
                        Material m = rockMats[rng.Next(rockMats.Length)];
                        mr.sharedMaterials = new[] { m, m };
                        mr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.On;
                    }
                    placed++;
                }
            }
            return placed;
        }

        // ------------------------------------------------------------------ a few stones lying in the grass fields

        private const float FieldStoneSpacing = 9f;       // candidate grid, metres
        private const double FieldStoneChance = 0.09;     // per candidate: roughly one stone to every 900 square metres of grass

        private static readonly HashSet<string> FieldStoneBiomes = new HashSet<string> { "biome_grass_plains", "biome_meadow" };

        private static int ScatterFieldStones(HomesteaderTerrainGenerator gen, Terrain terrain, Transform root, System.Random rng)
        {
            Shader lit = Shader.Find("Universal Render Pipeline/Lit");
            Material[] mats = { MakeMat(lit, Hex("#8a8884")), MakeMat(lit, Hex("#7a7873")), MakeMat(lit, Hex("#9a968c")) };
            Mesh[] small = BuildRockMeshes("FieldStone", 6, 0.14f, 0.3f, 700);
            Mesh[] larger = BuildRockMeshes("FieldRock", 4, 0.35f, 0.55f, 800);
            Vector3 origin = gen.transform.position;
            int placed = 0;
            for (float z = 0f; z < gen.terrainSizeZ; z += FieldStoneSpacing)
            {
                for (float x = 0f; x < gen.terrainSizeX; x += FieldStoneSpacing)
                {
                    float rx = x + (float)(rng.NextDouble() - 0.5) * FieldStoneSpacing;
                    float rz = z + (float)(rng.NextDouble() - 0.5) * FieldStoneSpacing;
                    if (rx < 1f || rz < 1f || rx > gen.terrainSizeX - 1f || rz > gen.terrainSizeZ - 1f) continue;
                    if (rng.NextDouble() > FieldStoneChance) continue;

                    BiomeData biome = gen.EvaluateBiomeAt(rx, rz);
                    if (biome == null || !FieldStoneBiomes.Contains(biome.id)) continue;
                    if (gen.IsNearRoad(rx, rz, 1.0f)) continue;
                    if (gen.IsWaterAt(rx, rz) || gen.IsWaterAt(rx + 1.5f, rz) || gen.IsWaterAt(rx - 1.5f, rz) || gen.IsWaterAt(rx, rz + 1.5f) || gen.IsWaterAt(rx, rz - 1.5f)) continue;

                    Mesh[] set = rng.NextDouble() < 0.15 ? larger : small;   // mostly small stones, now and then a bigger rock
                    float scale = 0.8f + (float)rng.NextDouble() * 0.5f;
                    float wx = origin.x + rx, wz = origin.z + rz;
                    float wy = terrain.SampleHeight(new Vector3(wx, 0f, wz)) + origin.y;

                    var go = new GameObject("FieldStone");
                    go.transform.SetParent(root, false);
                    go.transform.position = new Vector3(wx, wy - 0.04f * scale, wz);
                    go.transform.rotation = Quaternion.Euler((float)(rng.NextDouble() - 0.5) * 20f, (float)(rng.NextDouble() * 360.0), (float)(rng.NextDouble() - 0.5) * 20f);
                    go.transform.localScale = new Vector3(scale, scale * (0.6f + (float)rng.NextDouble() * 0.5f), scale);
                    { Mesh rockMesh = set[rng.Next(set.Length)]; go.AddComponent<MeshFilter>().sharedMesh = rockMesh; ForestSolids.AddRock(rockMesh, go.transform); WorldRocks.Register(go.transform, rockMesh); }
                    var mr = go.AddComponent<MeshRenderer>();
                    Material m = mats[rng.Next(mats.Length)];
                    mr.sharedMaterials = new[] { m, m };
                    mr.shadowCastingMode = set == small ? UnityEngine.Rendering.ShadowCastingMode.Off : UnityEngine.Rendering.ShadowCastingMode.On;
                    placed++;
                }
            }
            return placed;
        }

        // ------------------------------------------------------------------ large grass tufts, now and then

        private const float TuftSpacing = 3.0f;

        private static readonly HashSet<string> TuftBiomes = new HashSet<string>
        {
            "biome_grass_plains",
        };

        private static int ScatterTufts(HomesteaderTerrainGenerator gen, Terrain terrain, Transform root, System.Random rng)
        {
            Shader lit = Shader.Find("Universal Render Pipeline/Lit");
            float[] tuftGrow = { 0.45f, 0.8f, 1f, 0.9f };
            var mats = new Material[4];
            string[] tuftSummer = { "#5c9a34", "#6fa83c", "#4a8a30", "#8aaa48" };
            string[] tuftSpring = { "#78b848", "#88c050", "#62a23c", "#9ac058" };
            string[] tuftAutumn = { "#b4a452", "#a89848", "#bcaa5a", "#b09c4c" };
            for (int i = 0; i < mats.Length; i++)
                mats[i] = Seasonal(MakeMat(lit, Hex(tuftSummer[i]), 0.3f, 1.4f), Four("#9c8c5e", tuftSpring[i], tuftSummer[i], tuftAutumn[i]), tuftGrow);
            var tufts = new Mesh[6];
            for (int i = 0; i < tufts.Length; i++) tufts[i] = BuildTuftMesh(new System.Random(1100 + i * 19));

            Vector3 origin = gen.transform.position;
            int placed = 0;
            for (float z = 0f; z < gen.terrainSizeZ; z += TuftSpacing)
            {
                for (float x = 0f; x < gen.terrainSizeX; x += TuftSpacing)
                {
                    float rx = x + (float)(rng.NextDouble() - 0.5) * TuftSpacing;
                    float rz = z + (float)(rng.NextDouble() - 0.5) * TuftSpacing;
                    if (rx < 1f || rz < 1f || rx > gen.terrainSizeX - 1f || rz > gen.terrainSizeZ - 1f) continue;
                    if (rng.NextDouble() > 0.35) continue;   // periodic, but lush

                    BiomeData biome = gen.EvaluateBiomeAt(rx, rz);
                    if (biome == null || !TuftBiomes.Contains(biome.id)) continue;
                    if (gen.IsNearRoad(rx, rz, 0.5f)) continue;
                    if (gen.IsWaterAt(rx, rz)) continue;

                    float wx = origin.x + rx, wz = origin.z + rz;
                    float wy = terrain.SampleHeight(new Vector3(wx, 0f, wz)) + origin.y;

                    var go = new GameObject("GrassTuft");
                    go.transform.SetParent(root, false);
                    go.transform.position = new Vector3(wx, wy - 0.03f, wz);
                    go.transform.rotation = Quaternion.Euler(0f, (float)(rng.NextDouble() * 360.0), 0f);
                    go.transform.localScale = Vector3.one * (0.8f + (float)rng.NextDouble() * 0.6f);
                    go.AddComponent<MeshFilter>().sharedMesh = tufts[rng.Next(tufts.Length)];
                    var mr = go.AddComponent<MeshRenderer>();
                    Material m = mats[rng.Next(mats.Length)];
                    mr.sharedMaterials = new[] { m, m };
                    mr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
                    placed++;
                }
            }
            return placed;
        }

        // ------------------------------------------------------------------ shrubs and bushes

        private const float ShrubSpacing = 2.0f;

        /// <summary>
        /// Shrubs and bushes: low, leafy clumps of small leaf clusters on a few twigs, built and merged like the flowers and tufts (no shadows, they fade
        /// with the view centre). They grow mostly in the tree biomes, in patches (a slow noise field), and gather in thick clumps along the shorelines.
        /// </summary>
        /// <summary>A stand-in object of a berry bush (0 elderberry, 1 blueberry, 2 raspberry, 3 huckleberry, 4 haskap) for rendering its kit icon.</summary>
        public static GameObject MakeBushIconProxy(int kind)
        {
            string[] berryColours = { "#2b1b3d", "#3552c9", "#d6193d", "#3a2a72", "#4252b8" };
            Shader lit = Shader.Find("Universal Render Pipeline/Lit");
            var go = new GameObject("BushIcon_" + kind);
            go.AddComponent<MeshFilter>().sharedMesh = BuildShrubMesh(new System.Random(2300 + kind * 101 + 13), kind, 2.2f);   // bigger berries so they read in a small icon
            var mr = go.AddComponent<MeshRenderer>();
            mr.sharedMaterials = new[] { MakeMat(lit, Hex("#5b4630")), MakeMat(lit, Hex("#4d8a3c")), MakeMat(lit, Hex(berryColours[Mathf.Clamp(kind, 0, 4)])) };
            return go;
        }

        /// <summary>GLSL-style smoothstep(a, b, x): 0 below a, 1 above b (Mathf.SmoothStep interpolates between a and b by a 0..1 t, which is not this).</summary>
        private static float Edge01(float a, float b, float x)
        {
            float t = Mathf.Clamp01(Mathf.InverseLerp(a, b, x));
            return t * t * (3f - 2f * t);
        }

        private static Material s_twigMat;
        private static Material[] s_leafMats, s_berryMats;
        private static Mesh[][] s_berryMeshes;
        private static Transform s_plantedBushRoot;

        /// <summary>
        /// A berry bush the player planted: built from the same meshes and materials as the generated ones, but on its own mesh (its vertices in
        /// world space, so the picking and digging code treats it like any other bush). `pos` is the ground under it.
        /// </summary>
        public static bool SpawnPlantedBush(int kind, Vector3 pos, float yawDeg, float size, out BerryBush bush)
        {
            bush = null;
            if (s_berryMeshes == null || kind < 0 || kind >= s_berryMeshes.Length) return false;
            int variant = Mathf.Abs(Mathf.RoundToInt(pos.x * 7.3f + pos.z * 3.1f)) % 3;
            Mesh src = s_berryMeshes[kind][variant];
            Mesh m = Object.Instantiate(src);
            Vector3 at = pos + Vector3.down * 0.05f;
            Quaternion rot = Quaternion.Euler(0f, yawDeg, 0f);
            Matrix4x4 trs = Matrix4x4.TRS(at, rot, new Vector3(size, size, size));
            Vector3[] v = m.vertices;
            for (int i = 0; i < v.Length; i++) v[i] = trs.MultiplyPoint3x4(v[i]);
            Vector3[] n = m.normals;
            for (int i = 0; i < n.Length; i++) n[i] = rot * n[i];
            m.vertices = v;
            m.normals = n;
            // the vegetation shader sways and grows each plant round its base, read from these channels (what Combine writes for every bush)
            var uv1 = new List<Vector2>(v.Length);
            var uv2 = new List<Vector2>(v.Length);
            var uv3 = new List<Vector2>(v.Length);
            for (int i = 0; i < v.Length; i++)
            {
                uv1.Add(new Vector2(at.x, at.z));
                uv2.Add(new Vector2(at.y, size));
                uv3.Add(new Vector2(0f, 0f));
            }
            m.SetUVs(1, uv1);
            m.SetUVs(2, uv2);
            m.SetUVs(3, uv3);
            m.RecalculateBounds();
            if (s_plantedBushRoot == null) s_plantedBushRoot = new GameObject("PlantedBushes").transform;
            var go = new GameObject("PlantedBush_" + kind);
            go.transform.SetParent(s_plantedBushRoot, false);
            go.AddComponent<MeshFilter>().sharedMesh = m;
            var mr = go.AddComponent<MeshRenderer>();
            mr.sharedMaterials = new[] { s_twigMat, s_leafMats[variant % s_leafMats.Length], s_berryMats[kind] };
            mr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            bush = new BerryBush { Kind = kind, AssetId = BerryBushes.AssetFor(kind), Position = at, Mesh = m, VertStart = 0, VertCount = m.vertexCount, Planted = true };
            BerryBushes.Register(bush, src);
            return true;
        }

        /// <summary>Removes the bushes the player planted (a world being left).</summary>
        public static void ClearPlantedBushes()
        {
            if (s_plantedBushRoot != null) Object.Destroy(s_plantedBushRoot.gameObject);
            s_plantedBushRoot = null;
        }

        private static int ScatterShrubs(HomesteaderTerrainGenerator gen, Terrain terrain, Transform root, System.Random rng)
        {
            Shader lit = Shader.Find("Universal Render Pipeline/Lit");
            float[] grow = { 0.4f, 0.85f, 1f, 0.9f };
            string[] summer = { "#47803a", "#3f7634", "#56903f", "#6a8f3c" };
            string[] spring = { "#6aa84a", "#5f9c44", "#78b250", "#86b04c" };
            string[] autumn = { "#a88a3c", "#9a7a34", "#b8963e", "#a0782e" };
            var leafMats = new Material[summer.Length];
            for (int i = 0; i < leafMats.Length; i++)
                leafMats[i] = Seasonal(MakeMat(lit, Hex(summer[i]), 0.3f, 1.0f), Four("#6b5a45", spring[i], summer[i], autumn[i]), grow);
            Material twigMat = MakeMat(lit, Hex("#5b4630"), 0.15f, 1.0f);

            var shrubs = new Mesh[8];
            for (int i = 0; i < shrubs.Length; i++) shrubs[i] = BuildShrubMesh(new System.Random(1700 + i * 29));

            // Berry bushes: the same bush with the berries on it (a third submesh with the berry colour: in fruit from summer, gone in winter).
            // 0 elderberry, 1 blueberry, 2 raspberry, 3 huckleberry, 4 haskap.
            string[] berryColours = { "#2b1b3d", "#3552c9", "#d6193d", "#3a2a72", "#4252b8" };
            var berryMats = new Material[berryColours.Length];
            var berryMeshes = new Mesh[berryColours.Length][];
            for (int k = 0; k < berryColours.Length; k++)
            {
                berryMats[k] = Seasonal(MakeMat(lit, Hex(berryColours[k]), 0.3f, 1.0f), null, new[] { 0f, 0.15f, 1f, 0.5f });
                berryMeshes[k] = new Mesh[3];
                for (int v = 0; v < 3; v++) berryMeshes[k][v] = BuildShrubMesh(new System.Random(2300 + k * 101 + v * 13), k);
            }
            s_twigMat = twigMat; s_leafMats = leafMats; s_berryMats = berryMats; s_berryMeshes = berryMeshes;   // kept: a bush planted later is built from the same parts
            float seedB = (gen.worldSeed % 613) * 0.57f;

            // The habitats. Each kind grows in its own clumps (its own noise field), so the five never sit in the same patch.
            int PickBerry(float rx, float rz, BiomeData biome, float waterDist)
            {
                bool forest = IsTreeBiome(biome.id);
                bool? edge = null;
                bool IsEdge()
                {
                    if (edge.HasValue) return edge.Value;
                    bool e = false;
                    const float reach = 7f;
                    for (int d = 0; d < 4 && !e; d++)
                    {
                        float dx = d == 0 ? reach : d == 1 ? -reach : 0f, dz = d == 2 ? reach : d == 3 ? -reach : 0f;
                        BiomeData nb = gen.EvaluateBiomeAt(Mathf.Clamp(rx + dx, 1f, gen.terrainSizeX - 1f), Mathf.Clamp(rz + dz, 1f, gen.terrainSizeZ - 1f));
                        if (nb != null && !nb.id.StartsWith("biome_river") && !nb.id.StartsWith("biome_lake") && !nb.id.StartsWith("biome_pond") && IsTreeBiome(nb.id) != forest) e = true;
                    }
                    edge = e;
                    return e;
                }
                float Clump(int kind) => Edge01(0.70f, 0.78f, Mathf.PerlinNoise(rx * 0.12f + seedB * (kind + 1.3f), rz * 0.12f + 37f * kind));

                // elderberry: near the water
                if (waterDist > 2f && waterDist < 14f && rng.NextDouble() < 0.25 * Clump(0)) return 0;
                // haskap: wet ground, the marsh and the willow grove, or a little farther from the water
                if ((biome.id == "biome_wetland_marsh" || biome.id == "biome_willow_grove" || (waterDist > 5f && waterDist < 22f)) && rng.NextDouble() < 0.25 * Clump(4)) return 4;
                // blueberry and raspberry: the edges of the forests
                float c1 = Clump(1), c2 = Clump(2);
                if ((c1 > 0f || c2 > 0f) && IsEdge())
                {
                    if (rng.NextDouble() < 0.25 * c1) return 1;
                    if (rng.NextDouble() < 0.25 * c2) return 2;
                }
                // huckleberry: under the pines and the other forests, back from the edge
                if (forest && rng.NextDouble() < 0.2 * Clump(3) && !IsEdge()) return 3;
                return -1;
            }

            Vector3 origin = gen.transform.position;
            float noiseSeed = (gen.worldSeed % 977) * 0.43f;
            int placed = 0;
            for (float z = 0f; z < gen.terrainSizeZ; z += ShrubSpacing)
            {
                for (float x = 0f; x < gen.terrainSizeX; x += ShrubSpacing)
                {
                    float rx = x + (float)(rng.NextDouble() - 0.5) * ShrubSpacing;
                    float rz = z + (float)(rng.NextDouble() - 0.5) * ShrubSpacing;
                    if (rx < 1f || rz < 1f || rx > gen.terrainSizeX - 1f || rz > gen.terrainSizeZ - 1f) continue;
                    if (gen.IsWaterAt(rx, rz)) continue;

                    BiomeData biome = gen.EvaluateBiomeAt(rx, rz);
                    if (biome == null || biome.id == "biome_sand" || biome.id == "biome_rocky_ridge") continue;

                    // Patches: a slow noise field; shrubs only appear where it is high, so they come in clumps with open ground between.
                    float patch = Edge01(0.45f, 0.7f, Mathf.PerlinNoise(rx * 0.07f + noiseSeed, rz * 0.07f));
                    float chance;
                    float waterDist = gen.GetWaterDistance(rx, rz);
                    if (waterDist < 9f)
                    {
                        // Shorelines: thick clumps hugging the bank (a faster noise field makes the clumps tighter), thinning out to 9 m.
                        float edge = 1f - Mathf.InverseLerp(1.5f, 9f, waterDist);
                        float clump = Edge01(0.4f, 0.65f, Mathf.PerlinNoise(rx * 0.16f + noiseSeed * 2f, rz * 0.16f));
                        chance = 0.75f * edge * clump + 0.1f * patch;
                    }
                    else if (IsTreeBiome(biome.id) || biome.id == "biome_willow_grove" || biome.id == "biome_wetland_marsh")
                        chance = 0.45f * patch;
                    else
                        chance = 0.025f * patch;   // the odd bush out in the open
                    chance *= 0.55f;   // ordinary bushes are fewer now: the berry bushes take some of their places
                    int berry = PickBerry(rx, rz, biome, waterDist);
                    if (berry < 0 && rng.NextDouble() > chance) continue;

                    if (gen.IsNearRoad(rx, rz, 1.2f)) continue;
                    if (waterDist < 1.0f) continue;

                    float wx = origin.x + rx, wz = origin.z + rz;
                    float wy = terrain.SampleHeight(new Vector3(wx, 0f, wz)) + origin.y;

                    var go = new GameObject("Shrub");
                    go.transform.SetParent(root, false);
                    go.transform.position = new Vector3(wx, wy - 0.05f, wz);
                    go.transform.rotation = Quaternion.Euler(0f, (float)(rng.NextDouble() * 360.0), 0f);
                    float size = (berry >= 0 ? 0.9f : 0.75f) + (float)rng.NextDouble() * 0.7f;
                    go.transform.localScale = new Vector3(size, size * (0.85f + (float)rng.NextDouble() * 0.3f), size);
                    var mr = go.AddComponent<MeshRenderer>();
                    if (berry >= 0)
                    {
                        go.name = "BerryBush_" + berry;
                        Mesh bushMesh = berryMeshes[berry][rng.Next(3)];
                        go.AddComponent<MeshFilter>().sharedMesh = bushMesh;
                        var bush = new BerryBush { Kind = berry, AssetId = BerryBushes.AssetFor(berry), Position = go.transform.position };
                        BerryBushes.Register(bush, bushMesh);
                        BushByTransform[go.transform] = bush;
                        mr.sharedMaterials = new[] { twigMat, leafMats[rng.Next(leafMats.Length)], berryMats[berry] };
                    }
                    else
                    {
                        go.AddComponent<MeshFilter>().sharedMesh = shrubs[rng.Next(shrubs.Length)];
                        mr.sharedMaterials = new[] { twigMat, leafMats[rng.Next(leafMats.Length)] };
                    }
                    mr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
                    placed++;
                }
            }
            return placed;
        }

        /// <summary>One bush: a handful of 20-triangle leaf clusters packed round the middle, on a few twigs (the twigs show once the leaves are gone).</summary>
        private static Mesh BuildShrubMesh(System.Random rng, int berryKind = -1, float berryScale = 1f)
        {
            var mb = new MeshBuilder();
            int clusters = 4 + rng.Next(3);
            for (int i = 0; i < clusters; i++)
            {
                float ang = (float)(rng.NextDouble() * Mathf.PI * 2.0);
                float dist = (float)rng.NextDouble() * 0.45f;
                float r = 0.2f + (float)rng.NextDouble() * 0.18f;
                Vector3 c = new Vector3(Mathf.Cos(ang) * dist, 0.22f + (float)rng.NextDouble() * 0.5f, Mathf.Sin(ang) * dist);
                var p = new Vector3[IcoBase.Length];
                for (int k = 0; k < p.Length; k++)
                {
                    float j = 1f + ((float)rng.NextDouble() - 0.5f) * 0.45f;
                    p[k] = c + new Vector3(IcoBase[k].x * r * j, IcoBase[k].y * r * 0.8f * j, IcoBase[k].z * r * j);
                }
                for (int f = 0; f < IcoFaces.Length; f += 3)
                    mb.Tri(p[IcoFaces[f]], p[IcoFaces[f + 1]], p[IcoFaces[f + 2]], c, true);
            }
            int twigs = 3 + rng.Next(2);
            for (int i = 0; i < twigs; i++)
            {
                float ang = (float)(rng.NextDouble() * Mathf.PI * 2.0);
                Vector3 tip = new Vector3(Mathf.Cos(ang) * (0.15f + (float)rng.NextDouble() * 0.35f), 0.45f + (float)rng.NextDouble() * 0.35f, Mathf.Sin(ang) * (0.15f + (float)rng.NextDouble() * 0.35f));
                AddTube(mb, new Vector3(0f, 0f, 0f), tip, 0.035f, 0.01f, 3, false);
            }
            int berries = berryKind >= 0 ? AddBerries(mb, berryKind, rng, berryScale) : 0;   // last, so the berries are the tail submesh
            int firstBerry = mb.FruitFirst < 0 ? 0 : mb.FruitFirst;
            Mesh result = mb.ToMesh(berryKind >= 0 ? "BerryBush" + berryKind : "Shrub");
            if (berries > 0) BerryBushes.SetLayout(result, firstBerry, OctaFaces.Length, berries);   // 8 triangles (24 vertices) per berry
            return result;
        }

        /// <summary>
        /// The berries on a bush, as small icosahedra on the outer top of the foliage: round ones for blueberry / huckleberry, bumpier and bigger for
        /// raspberry, elongated for haskap, and elderberry in a few flat-topped clusters.
        /// </summary>
        private static int AddBerries(MeshBuilder mb, int kind, System.Random rng, float scale = 1f)
        {
            float radius = (kind == 0 ? 0.026f : kind == 1 ? 0.034f : kind == 2 ? 0.04f : kind == 3 ? 0.036f : 0.03f) * scale;
            Vector3 stretch = kind == 4 ? new Vector3(0.8f, 1.9f, 0.8f) : Vector3.one;
            if (kind == 0)
            {
                for (int c = 0; c < 4; c++)
                {
                    float ang = (float)(rng.NextDouble() * Mathf.PI * 2.0);
                    Vector3 head = new Vector3(Mathf.Cos(ang) * 0.32f, 0.62f + (float)rng.NextDouble() * 0.12f, Mathf.Sin(ang) * 0.32f);
                    for (int b = 0; b < 8; b++)
                    {
                        float a2 = (float)(rng.NextDouble() * Mathf.PI * 2.0), d = (float)rng.NextDouble() * 0.11f;
                        AddBerry(mb, head + new Vector3(Mathf.Cos(a2) * d, (float)rng.NextDouble() * 0.04f, Mathf.Sin(a2) * d), radius, stretch, rng);
                    }
                }
                return 32;
            }
            int count = 14 + rng.Next(8);
            for (int b = 0; b < count; b++)
            {
                float ang = (float)(rng.NextDouble() * Mathf.PI * 2.0);
                float dist = 0.18f + (float)rng.NextDouble() * 0.3f;
                float y = 0.3f + (float)rng.NextDouble() * 0.45f;
                AddBerry(mb, new Vector3(Mathf.Cos(ang) * dist, y, Mathf.Sin(ang) * dist), radius, stretch, rng);
            }
            return count;
        }

        // A berry is an octahedron (8 triangles): at the size of a berry that reads as round, and a bush carries ~20 of them.
        private static readonly Vector3[] OctaBase = { Vector3.up, Vector3.down, Vector3.right, Vector3.left, Vector3.forward, Vector3.back };
        private static readonly int[] OctaFaces = { 0, 2, 4, 0, 4, 3, 0, 3, 5, 0, 5, 2, 1, 4, 2, 1, 3, 4, 1, 5, 3, 1, 2, 5 };

        private static void AddBerry(MeshBuilder mb, Vector3 p, float r, Vector3 stretch, System.Random rng)
        {
            Quaternion q = Quaternion.Euler((float)rng.NextDouble() * 360f, (float)rng.NextDouble() * 360f, (float)rng.NextDouble() * 360f);
            r *= 1.15f;   // an octahedron's corners sit on the sphere, its faces inside it: a little bigger keeps the berry the same visual size
            for (int f = 0; f < OctaFaces.Length; f += 3)
            {
                Vector3 a = p + q * Vector3.Scale(OctaBase[OctaFaces[f]], stretch) * r;
                Vector3 b = p + q * Vector3.Scale(OctaBase[OctaFaces[f + 1]], stretch) * r;
                Vector3 c = p + q * Vector3.Scale(OctaBase[OctaFaces[f + 2]], stretch) * r;
                mb.FruitTri(a, b, c, p);
            }
        }

        /// <summary>A large fountain-shaped tuft: many tapered blades arching outward from one spot.</summary>
        private static Mesh BuildTuftMesh(System.Random rng)
        {
            var mb = new MeshBuilder();
            int blades = 22 + rng.Next(10);
            for (int i = 0; i < blades; i++)
            {
                float ang = (float)(rng.NextDouble() * Mathf.PI * 2.0);
                Vector3 dir = new Vector3(Mathf.Cos(ang), 0f, Mathf.Sin(ang));
                float h = 0.7f + (float)rng.NextDouble() * 0.7f;
                float outward = h * (0.15f + (float)rng.NextDouble() * 0.45f);
                Vector3 b = dir * ((float)rng.NextDouble() * 0.12f);
                Vector3 mid = b + dir * outward * 0.35f + Vector3.up * h * 0.6f;
                Vector3 tip = b + dir * outward + Vector3.up * h;
                AddTube(mb, b, mid, 0.04f, 0.028f, 3, false);
                AddTube(mb, mid, tip, 0.028f, 0.004f, 3, false);
            }
            return mb.ToMesh("GrassTuft");
        }

        // ------------------------------------------------------------------ prairie flower clumps

        private const float FlowerSpacing = 2.0f;

        private static int ScatterFlowers(HomesteaderTerrainGenerator gen, Terrain terrain, Transform root, System.Random rng)
        {
            Shader lit = Shader.Find("Universal Render Pipeline/Lit");
            Material stemMat = Seasonal(MakeMat(lit, Hex("#4f8a30"), 0.12f, 0.7f), Four("#6b6a45", "#5f9a38", "#4f8a30", "#7a8a40"), new[] { 0f, 0f, 1f, 0.5f }, true);
            string[] colours = { "#f4f1e6", "#f2c81d", "#9a5fc8", "#e86fa0", "#d8412f", "#6f8fe0" };
            var headMats = new Material[colours.Length];
            for (int i = 0; i < colours.Length; i++)
                headMats[i] = Seasonal(MakeMat(lit, Hex(colours[i]), 0.12f, 0.7f), null, new[] { 0f, 0f, 1f, 0.35f }, true);   // none until spring begins, in full bloom by summer

            // Several clump meshes per colour; a clump is one colour, like a real patch of one species.
            const int perColour = 3;
            var clumps = new Mesh[colours.Length * perColour];
            for (int i = 0; i < clumps.Length; i++) clumps[i] = BuildFlowerClump(new System.Random(900 + i * 23));

            Vector3 origin = gen.transform.position;
            float noiseSeed = (gen.worldSeed % 991) * 0.41f;
            int placed = 0;
            for (float z = 0f; z < gen.terrainSizeZ; z += FlowerSpacing)
            {
                for (float x = 0f; x < gen.terrainSizeX; x += FlowerSpacing)
                {
                    float rx = x + (float)(rng.NextDouble() - 0.5) * FlowerSpacing;
                    float rz = z + (float)(rng.NextDouble() - 0.5) * FlowerSpacing;
                    if (rx < 1f || rz < 1f || rx > gen.terrainSizeX - 1f || rz > gen.terrainSizeZ - 1f) continue;

                    BiomeData biome = gen.EvaluateBiomeAt(rx, rz);
                    if (biome == null || biome.id != "biome_meadow") continue;
                    if (gen.IsNearRoad(rx, rz, 0.5f)) continue;
                    if (gen.IsWaterAt(rx, rz)) continue;

                    // Patchy: flowers gather in drifts rather than an even carpet.
                    float drift = Mathf.SmoothStep(0.35f, 0.65f, Mathf.PerlinNoise(rx * 0.08f + noiseSeed, rz * 0.08f));
                    if (rng.NextDouble() > 0.15 + 0.6 * drift) continue;

                    // One colour per large drift cell, with a little variety.
                    float hueField = Mathf.PerlinNoise(rx * 0.03f + noiseSeed * 2f, rz * 0.03f);
                    int colour = Mathf.Clamp((int)(hueField * colours.Length), 0, colours.Length - 1);
                    if (rng.NextDouble() < 0.2) colour = rng.Next(colours.Length);

                    float wx = origin.x + rx, wz = origin.z + rz;
                    float wy = terrain.SampleHeight(new Vector3(wx, 0f, wz)) + origin.y;

                    var go = new GameObject("Flowers");
                    go.transform.SetParent(root, false);
                    go.transform.position = new Vector3(wx, wy - 0.03f, wz);
                    go.transform.rotation = Quaternion.Euler(0f, (float)(rng.NextDouble() * 360.0), 0f);
                    go.transform.localScale = Vector3.one * ((0.8f + (float)rng.NextDouble() * 0.6f) * 0.7f);   // 30% smaller
                    go.AddComponent<MeshFilter>().sharedMesh = clumps[colour * perColour + rng.Next(perColour)];
                    var mr = go.AddComponent<MeshRenderer>();
                    mr.sharedMaterials = new[] { stemMat, headMats[colour] };
                    mr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
                    placed++;
                }
            }
            return placed;
        }

        /// <summary>A tight clump of flowers: thin stems (submesh 0) topped with flat petal discs (submesh 1).</summary>
        private static Mesh BuildFlowerClump(System.Random rng)
        {
            var mb = new MeshBuilder();
            int count = 6 + rng.Next(5);
            for (int i = 0; i < count; i++)
            {
                float ang = (float)(rng.NextDouble() * Mathf.PI * 2.0);
                float dist = (float)rng.NextDouble() * 0.45f;
                Vector3 b = new Vector3(Mathf.Cos(ang) * dist, 0f, Mathf.Sin(ang) * dist);
                float h = 0.35f + (float)rng.NextDouble() * 0.35f;
                float leanAng = (float)(rng.NextDouble() * Mathf.PI * 2.0);
                Vector3 top = b + new Vector3(Mathf.Cos(leanAng), 0f, Mathf.Sin(leanAng)) * h * 0.15f + Vector3.up * h;
                AddTube(mb, b, top, 0.012f, 0.008f, 3, false);
                AddTube(mb, top, top + Vector3.up * 0.04f, 0.075f + (float)rng.NextDouble() * 0.03f, 0.05f, 6, true);
            }
            return mb.ToMesh("FlowerClump");
        }

        // ------------------------------------------------------------------ river and lake beds: rocks and woodland debris

        private const float BedSpacing = 1.4f;

        private static int ScatterBed(HomesteaderTerrainGenerator gen, Terrain terrain, Transform root, System.Random rng)
        {
            Shader lit = Shader.Find("Universal Render Pipeline/Lit");
            Material[] rockMats = { MakeMat(lit, Hex("#6d6c68")), MakeMat(lit, Hex("#7d7a72")), MakeMat(lit, Hex("#5a5a5c")) };
            Material[] woodMats = { MakeMat(lit, Hex("#4a3826")), MakeMat(lit, Hex("#5c4630")), MakeMat(lit, Hex("#3b2e22")) };

            Mesh[] rocks = BuildRockMeshes("BedRock", 6, 0.15f, 0.55f, 600);
            var logs = new Mesh[4];
            for (int i = 0; i < logs.Length; i++) logs[i] = BuildDebrisMesh(new System.Random(700 + i * 29), true);
            var sticks = new Mesh[4];
            for (int i = 0; i < sticks.Length; i++) sticks[i] = BuildDebrisMesh(new System.Random(800 + i * 29), false);

            Vector3 origin = gen.transform.position;
            int placed = 0;
            for (float z = 0f; z < gen.terrainSizeZ; z += BedSpacing)
            {
                for (float x = 0f; x < gen.terrainSizeX; x += BedSpacing)
                {
                    float rx = x + (float)(rng.NextDouble() - 0.5) * BedSpacing;
                    float rz = z + (float)(rng.NextDouble() - 0.5) * BedSpacing;
                    if (rx < 1f || rz < 1f || rx > gen.terrainSizeX - 1f || rz > gen.terrainSizeZ - 1f) continue;
                    if (!gen.IsWaterAt(rx, rz)) continue;

                    double roll = rng.NextDouble();
                    if (roll < 0.85) continue;   // leave bare bed between items (15% of spots get one)

                    float wx = origin.x + rx, wz = origin.z + rz;
                    float wy = terrain.SampleHeight(new Vector3(wx, 0f, wz)) + origin.y;

                    var go = new GameObject("BedItem");
                    go.transform.SetParent(root, false);
                    var mr = go.AddComponent<MeshRenderer>();
                    mr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;

                    if (roll < 0.95)
                    {
                        float s = 0.7f + (float)rng.NextDouble() * 0.9f;
                        go.transform.position = new Vector3(wx, wy - 0.06f * s, wz);
                        go.transform.rotation = Quaternion.Euler((float)(rng.NextDouble() - 0.5) * 20f, (float)(rng.NextDouble() * 360.0), (float)(rng.NextDouble() - 0.5) * 20f);
                        go.transform.localScale = new Vector3(s, s * (0.5f + (float)rng.NextDouble() * 0.5f), s);
                        { Mesh rockMesh = rocks[rng.Next(rocks.Length)]; go.AddComponent<MeshFilter>().sharedMesh = rockMesh; ForestSolids.AddRock(rockMesh, go.transform); WorldRocks.Register(go.transform, rockMesh); }
                        Material m = rockMats[rng.Next(rockMats.Length)];
                        mr.sharedMaterials = new[] { m, m };
                    }
                    else
                    {
                        bool log = roll > 0.9875;
                        go.transform.position = new Vector3(wx, wy + 0.02f, wz);
                        go.transform.rotation = Quaternion.Euler(0f, (float)(rng.NextDouble() * 360.0), 0f);
                        go.AddComponent<MeshFilter>().sharedMesh = log ? logs[rng.Next(logs.Length)] : sticks[rng.Next(sticks.Length)];
                        Material m = woodMats[rng.Next(woodMats.Length)];
                        mr.sharedMaterials = new[] { m, m };
                    }
                    placed++;
                }
            }
            return placed;
        }

        /// <summary>A fallen log (with a branch stub) or a small bundle of sticks, lying flat on the ground.</summary>
        private static Mesh BuildDebrisMesh(System.Random rng, bool log)
        {
            var mb = new MeshBuilder();
            if (log)
            {
                float len = 1.8f + (float)rng.NextDouble() * 1.6f;
                float r = 0.1f + (float)rng.NextDouble() * 0.08f;
                float r0 = r, r1 = r * 0.8f;
                Vector3 a = new Vector3(-len * 0.5f, r, 0f), b = new Vector3(len * 0.5f, r * 0.9f, (float)(rng.NextDouble() - 0.5) * 0.3f);
                AddTube(mb, a, b, r0, r1, 6, true);
                Vector3 bs = Vector3.Lerp(a, b, 0.3f + (float)rng.NextDouble() * 0.3f);
                AddTube(mb, bs, bs + new Vector3((float)(rng.NextDouble() - 0.5) * 0.3f, 0.25f, 0.5f), r * 0.35f, r * 0.2f, 4, true);
            }
            else
            {
                int count = 3 + rng.Next(3);
                for (int i = 0; i < count; i++)
                {
                    float len = 0.6f + (float)rng.NextDouble() * 0.9f;
                    float ang = (float)(rng.NextDouble() * Mathf.PI);
                    Vector3 dir = new Vector3(Mathf.Cos(ang), 0f, Mathf.Sin(ang));
                    Vector3 c = new Vector3((float)(rng.NextDouble() - 0.5) * 0.5f, 0.03f, (float)(rng.NextDouble() - 0.5) * 0.5f);
                    AddTube(mb, c - dir * len * 0.5f, c + dir * len * 0.5f, 0.03f, 0.02f, 4, true);
                }
            }
            return mb.ToMesh(log ? "Log" : "Sticks");
        }

        /// <summary>A clump of leaning cattail stalks, each topped with a brown seed head (submesh 0 = stalks, 1 = heads).</summary>
        private static Mesh BuildCattailClump(System.Random rng)
        {
            var mb = new MeshBuilder();
            int stalks = 5 + rng.Next(4);
            for (int i = 0; i < stalks; i++)
            {
                float ang = (float)(rng.NextDouble() * Mathf.PI * 2.0);
                float dist = (float)rng.NextDouble() * 0.35f;
                Vector3 b = new Vector3(Mathf.Cos(ang) * dist, 0f, Mathf.Sin(ang) * dist);
                float h = 1.3f + (float)rng.NextDouble() * 0.9f;
                float leanAng = (float)(rng.NextDouble() * Mathf.PI * 2.0);
                Vector3 lean = new Vector3(Mathf.Cos(leanAng), 0f, Mathf.Sin(leanAng)) * (0.12f + (float)rng.NextDouble() * 0.2f) * h;
                Vector3 Along(float t) => b + lean * t + Vector3.up * (h * t);

                AddTube(mb, Along(0f), Along(1f), 0.03f, 0.018f, 4, false);
                AddTube(mb, Along(0.68f), Along(0.86f), 0.055f, 0.05f, 6, true);
            }
            return mb.ToMesh("CattailClump");
        }

        private static void AddTube(MeshBuilder mb, Vector3 p0, Vector3 p1, float r0, float r1, int sides, bool crown)
        {
            Vector3 centre = (p0 + p1) * 0.5f;
            Vector3 axis = (p1 - p0).normalized;
            Vector3 u = Vector3.Cross(axis, Mathf.Abs(axis.y) > 0.9f ? Vector3.right : Vector3.up).normalized;
            Vector3 v = Vector3.Cross(axis, u);
            for (int i = 0; i < sides; i++)
            {
                float a0 = i * Mathf.PI * 2f / sides, a1 = (i + 1) * Mathf.PI * 2f / sides;
                Vector3 d0 = u * Mathf.Cos(a0) + v * Mathf.Sin(a0);
                Vector3 d1 = u * Mathf.Cos(a1) + v * Mathf.Sin(a1);
                Vector3 b0 = p0 + d0 * r0;
                Vector3 b1 = p0 + d1 * r0;
                Vector3 t0 = p1 + d0 * r1;
                Vector3 t1 = p1 + d1 * r1;
                mb.Tri(b0, t0, t1, centre, crown);
                mb.Tri(b0, t1, b1, centre, crown);
                if (crown) mb.Tri(t0, t1, p1, centre, true);   // cap the seed head
            }
        }

        private static Mesh[] BuildRockMeshes(string name, int count, float radiusMin, float radiusMax, int seed)
        {
            var meshes = new Mesh[count];
            for (int i = 0; i < count; i++)
            {
                var rng = new System.Random(seed + i * 31);
                float r = Mathf.Lerp(radiusMin, radiusMax, (float)rng.NextDouble());
                var mb = new MeshBuilder();
                var radii = new Vector3(r * (0.9f + (float)rng.NextDouble() * 0.5f), r * (0.6f + (float)rng.NextDouble() * 0.3f), r * (0.9f + (float)rng.NextDouble() * 0.5f));
                AddBlob(mb, new Vector3(0f, radii.y * 0.6f, 0f), radii, rng, 0.25f);
                meshes[i] = mb.ToMesh($"{name}_{i}");
            }
            return meshes;
        }

        // ------------------------------------------------------------------ assets per species

        private static void BuildAssets(Species s)
        {
            Shader lit = Shader.Find("Universal Render Pipeline/Lit");
            s.AgeStages = StageEnds(s.Name);
            float sway = s.Shape == Shape.Conifer ? 0.25f : 0.35f;
            s.TrunkMat = MakeMat(lit, s.Trunk, sway, s.HeightMax);
            s.TrunkMat.SetVector("_AgeStages", s.AgeStages);
            if (s.Shape == Shape.Birch) { s.TrunkMat.SetFloat("_Spots", 1f); s.TrunkMat.SetColor("_SpotColor", Hex("#1d1b19")); }   // white bark with black marks
            // Every distinct material is a draw call per chunk (and again in the shadow pass): the newer species use a single crown tint.
            int tints = s.Shape == Shape.Orchard || s.Shape == Shape.Weeping ? 1 : CrownTintsPerSpecies;
            s.CrownMats = new Material[tints];
            float pivotY = (s.HeightMin + s.HeightMax) * 0.5f * 0.62f;   // roughly the crown centre
            for (int i = 0; i < tints; i++)
            {
                Color.RGBToHSV(s.Crown, out float h, out float sat, out float v);
                float shift = (i - 1) * 0.025f;
                Color summer = Color.HSVToRGB(Mathf.Repeat(h + shift, 1f), Mathf.Clamp01(sat + (i - 1) * 0.05f), Mathf.Clamp01(v + (i - 1) * 0.08f));
                Material m = MakeMat(lit, summer, sway, s.HeightMax);
                m.SetFloat("_GrowPivotY", pivotY);
                m.SetVector("_AgeStages", s.AgeStages);
                if (s.Evergreen)
                {
                    // Conifers keep their needles; a touch darker and bluer in winter.
                    Color winter = Color.Lerp(summer, new Color(0.12f, 0.27f, 0.25f), 0.35f);
                    Seasonal(m, new[] { winter, summer, summer, summer }, null);
                }
                else
                {
                    Color.RGBToHSV(summer, out float sh, out float ss, out float sv);
                    Color spring = Color.HSVToRGB(Mathf.Repeat(sh - 0.03f, 1f), Mathf.Clamp01(ss - 0.12f), Mathf.Clamp01(sv + 0.12f));
                    Color autumn = Hex(s.Autumn[i % s.Autumn.Length]);
                    // Crowns fade away one tree at a time, each at its own random moment (see crownFade in the shader): all gone in winter,
                    // some already back in spring, all there in summer, and from mid-autumn more and more of them go.
                    Seasonal(m, new[] { Hex("#6b5a45"), spring, summer, autumn }, null, false, new[] { 1f, 0.3f, 0f, 0.22f });
                }
                s.CrownMats[i] = m;
            }

            if (s.FruitCount > 0)
            {
                // The fruit: gone in winter, on the tree the rest of the year.
                s.FruitMat = MakeMat(lit, s.FruitColor, sway, s.HeightMax);
                s.FruitMat.SetFloat("_GrowPivotY", pivotY);
                s.FruitMat.SetVector("_AgeStages", s.AgeStages);
                Seasonal(s.FruitMat, null, new[] { 0f, 1f, 1f, 1f });
                s.FruitRipeAge = FruitRipeAgeFor(s.Name);
            }

            s.Variants = new Mesh[VariantsPerSpecies];
            s.DeadVariants = new Mesh[VariantsPerSpecies];
            s.FruitFirstVert = new int[VariantsPerSpecies];
            s.FruitVertCount = new int[VariantsPerSpecies];
            s.DeadMat = MakeMat(lit, Color.Lerp(s.Trunk, Hex("#4a3d30"), 0.55f), 0f, s.HeightMax);   // the species' own bark, greyed
            for (int i = 0; i < VariantsPerSpecies; i++)
            {
                var rng = new System.Random(1000 + i * 77 + (int)s.Shape * 13);
                float height = Mathf.Lerp(s.HeightMin, s.HeightMax, (float)rng.NextDouble());
                s.Variants[i] = BuildTreeMesh(s, height, rng, out s.FruitFirstVert[i], out s.FruitVertCount[i]);
                var deadRng = new System.Random(7000 + i * 91 + (int)s.Shape * 17 + NameSeed(s.Name));
                s.DeadVariants[i] = BuildDeadTreeMesh(s, height, deadRng);
            }
        }

        // Every material is the Homesteader/Vegetation shader (wind sway, season growth, snow). The shader argument is
        // kept only so the call sites read the same; sway is the amplitude in metres at swayRef height (0 = rigid).
        private static readonly List<VegetationSeasons.Entry> Tracked = new List<VegetationSeasons.Entry>();

        // Growth, following the asset kit's tree growth groups (logging/<tree>/<tree>.json): four stages -
        // sapling, small, medium, mature - with the stage windows read from the species' own growth group. Each world
        // tree has a birth day, and the shader turns (today - birth) into the stage's size, so trees really grow up as
        // game days pass. Stage heights are the same proportions as the tree prompt sheet (16 / 35 / 65 / 100 percent).
        public const float WorldStartDay = 141f;   // TimeSystem.ResetToNewGameDefaults: a new game starts on day 141
        private static readonly Dictionary<Transform, float> Births = new Dictionary<Transform, float>();
        private static readonly Dictionary<Transform, ForestTree> TreeByTransform = new Dictionary<Transform, ForestTree>();
        private static readonly Dictionary<Transform, BerryBush> BushByTransform = new Dictionary<Transform, BerryBush>();

        /// <summary>The log a felled tree of this species drops (poplar has no plain log item yet, so its medium uncut log).</summary>
        private static string LogItemFor(string species)
        {
            switch (species)
            {
                case "maple": return "mat_log_maple";
                case "birch": return "mat_log_birch";
                case "oak": return "mat_log_oak";
                case "pine": return "mat_log_pine";
                case "apple": return "mat_log_oak";
                case "lemon": return "mat_log_oak";
                case "orange": return "mat_log_oak";
                case "willow": return "mat_log_willowood_uncut_long";
                default: return "mat_log_poplar_uncut_medium";
            }
        }

        /// <summary>The tree age (game days) from which a fruit tree carries its fruit: where the kit's fruit_stage begins (default the last stage).</summary>
        private static float FruitRipeAgeFor(string species)
        {
            if (GrowthRegistry.TryGetGroup(species, "homesteader", out GrowthGroup g) && g.Stages.Count >= 2)
            {
                int stage = g.Rules != null && g.Rules.Fruiting && g.Rules.FruitStage > 0 ? g.Rules.FruitStage : g.Stages.Count;
                stage = Mathf.Clamp(stage, 2, g.Stages.Count);
                return g.Stages[stage - 2].AgeMax;   // the previous stage ends where the fruiting stage begins
            }
            return 150f;
        }

        /// <summary>Stage window ends (sapling, small, medium) in game days for a species; the kit's group wins, else the kit defaults.</summary>
        private static Vector4 StageEnds(string species)
        {
            if (GrowthRegistry.TryGetGroup(species, "homesteader", out GrowthGroup g) && g.Stages.Count >= 4)
                return new Vector4(g.Stages[0].AgeMax, g.Stages[1].AgeMax, g.Stages[2].AgeMax, 1f);
            return new Vector4(15f, 40f, 75f, 1f);
        }

        /// <summary>A starting age for a world tree: a mixed-age stand, mostly mature, some still coming up.</summary>
        private static float RollAge(Vector4 ends, System.Random rng)
        {
            double r = rng.NextDouble();
            float lo, hi;
            if (r < 0.08) { lo = 0f; hi = ends.x; }                    // sapling
            else if (r < 0.20) { lo = ends.x; hi = ends.y; }          // small
            else if (r < 0.40) { lo = ends.y; hi = ends.z; }          // medium
            else { lo = ends.z; hi = ends.z + 30f; }                  // mature
            return Mathf.Lerp(lo, hi, (float)rng.NextDouble());
        }

        private static Material MakeMat(Shader shader, Color color, float sway = 0f, float swayRef = 1f)
        {
            Shader veg = Shader.Find("Homesteader/Vegetation");
            var m = new Material(veg != null ? veg : shader) { hideFlags = HideFlags.DontSave };
            m.SetColor("_BaseColor", color);
            m.SetFloat("_SwayAmp", sway);
            m.SetFloat("_SwayRef", swayRef);
            m.SetFloat("_Grow", 1f);
            return m;
        }

        /// <summary>Registers a material for seasonal colour / growth. Arrays are winter, spring, summer, autumn.</summary>
        private static Material Seasonal(Material m, Color[] colour, float[] grow, bool atSeasonStart = false, float[] loss = null)
        {
            Tracked.Add(new VegetationSeasons.Entry { Mat = m, Colour = colour, Grow = grow, AtSeasonStart = atSeasonStart, Loss = loss });
            return m;
        }

        private static Color[] Four(string winter, string spring, string summer, string autumn)
        {
            return new[] { Hex(winter), Hex(spring), Hex(summer), Hex(autumn) };
        }

        private static Color Hex(string hex)
        {
            ColorUtility.TryParseHtmlString(hex, out Color c);
            return c;
        }

        // ------------------------------------------------------------------ mesh building (flat shaded)

        private sealed class MeshBuilder
        {
            public readonly List<Vector3> Verts = new List<Vector3>();
            public readonly List<Vector3> Normals = new List<Vector3>();
            public readonly List<int> TrunkTris = new List<int>();
            public readonly List<int> CrownTris = new List<int>();
            public readonly List<int> FruitTris = new List<int>();
            public int FruitFirst = -1;      // index of the first fruit vertex (fruit is added last)

            public void FruitTri(Vector3 a, Vector3 b, Vector3 c, Vector3 centre)
            {
                if (FruitFirst < 0) FruitFirst = Verts.Count;
                Vector3 n = Vector3.Cross(b - a, c - a);
                if (n.sqrMagnitude < 1e-10f) return;
                n.Normalize();
                Vector3 mid = (a + b + c) / 3f;
                if (Vector3.Dot(n, mid - centre) < 0f) { (b, c) = (c, b); n = -n; }
                int i = Verts.Count;
                Verts.Add(a); Verts.Add(b); Verts.Add(c);
                Normals.Add(n); Normals.Add(n); Normals.Add(n);
                FruitTris.Add(i); FruitTris.Add(i + 1); FruitTris.Add(i + 2);
            }

            /// <summary>Adds one flat-shaded triangle, wound so it faces away from outsideOf.</summary>
            public void Tri(Vector3 a, Vector3 b, Vector3 c, Vector3 centre, bool crown)
            {
                Vector3 n = Vector3.Cross(b - a, c - a);
                if (n.sqrMagnitude < 1e-10f) return;
                n.Normalize();
                Vector3 mid = (a + b + c) / 3f;
                if (Vector3.Dot(n, mid - centre) < 0f) { (b, c) = (c, b); n = -n; }

                List<int> tris = crown ? CrownTris : TrunkTris;
                int i = Verts.Count;
                Verts.Add(a); Verts.Add(b); Verts.Add(c);
                Normals.Add(n); Normals.Add(n); Normals.Add(n);
                tris.Add(i); tris.Add(i + 1); tris.Add(i + 2);
            }

            public Mesh ToMesh(string name)
            {
                var mesh = new Mesh { name = name };
                mesh.SetVertices(Verts);
                mesh.SetNormals(Normals);
                mesh.subMeshCount = FruitTris.Count > 0 ? 3 : 2;
                mesh.SetTriangles(TrunkTris, 0);
                mesh.SetTriangles(CrownTris, 1);
                if (FruitTris.Count > 0) mesh.SetTriangles(FruitTris, 2);
                mesh.RecalculateBounds();
                return mesh;
            }
        }

        /// <summary>
        /// The dead version of a species, in its own silhouette: no crown, a snapped trunk and bare limbs. Conifers keep a tall spar with
        /// stubs of branches in whorls; round and broad trees a thick trunk with big forks; the willow a stump with drooping limbs; the
        /// fruit trees a short gnarled trunk; the slender birch and poplar a pale spar with a few short branches. Each variant is its own roll.
        /// </summary>
        private static int NameSeed(string name)
        {
            int h = 17;
            foreach (char c in name) h = h * 31 + c;
            return Mathf.Abs(h % 100000);
        }

        private static Mesh BuildDeadTreeMesh(Species s, float height, System.Random rng)
        {
            var mb = new MeshBuilder();
            switch (s.Shape)
            {
                case Shape.Conifer: BuildDeadConifer(mb, height, rng); break;
                case Shape.Weeping: BuildDeadWeeping(mb, height, rng); break;
                case Shape.Orchard: BuildDeadBroadleaf(mb, s.Shape, height * 0.9f, 0.55f, 0.75f, rng); break;
                case Shape.Oval:
                case Shape.Birch:
                case Shape.Columnar: BuildDeadBroadleaf(mb, s.Shape, height, 0.85f, 0.30f, rng); break;
                case Shape.Broad: BuildDeadBroadleaf(mb, s.Shape, height, 0.62f, 1.1f, rng); break;
                default: BuildDeadBroadleaf(mb, s.Shape, height, 0.66f, 0.85f, rng); break;
            }
            return mb.ToMesh("DeadTree_" + s.Name);
        }

        /// <param name="trunkFrac">How tall the trunk stands (fraction of the living height).</param>
        /// <param name="reach">How far the bare limbs reach, relative to the living crown width.</param>
        private static void BuildDeadBroadleaf(MeshBuilder mb, Shape shape, float height, float trunkFrac, float reach, System.Random rng)
        {
            float trunkH = height * trunkFrac;
            float trunkR = Mathf.Max(shape == Shape.Orchard ? 0.14f : 0.22f, height * (shape == Shape.Broad ? 0.045f : (shape == Shape.Orchard ? 0.04f : 0.034f)));
            AddTrunk(mb, trunkH, trunkR * 1.2f, trunkR * 0.5f);   // the top is snapped: it ends thick
            // the limbs start on the trunk: the branch heights run from 75% of the trunk up to its top, so the crown size passed here is tiny
            AddBranches(mb, shape == Shape.Orchard ? Shape.Round : shape, trunkH * 0.80f, height * 0.30f * reach, trunkH * 0.06f, trunkR, rng);
        }

        /// <summary>A dead conifer: a tall bare spar, a snapped top and short stubs of branches in whorls down it.</summary>
        private static void BuildDeadConifer(MeshBuilder mb, float height, System.Random rng)
        {
            float trunkH = height * 0.88f;
            float trunkR = Mathf.Max(0.2f, height * 0.03f);
            AddTrunk(mb, trunkH, trunkR * 1.25f, trunkR * 0.35f);
            int whorls = 6;
            for (int w = 0; w < whorls; w++)
            {
                float y = trunkH * (0.18f + w * 0.13f);
                float stubLen = height * 0.17f * (1f - w * 0.12f);
                int arms = 4;
                float turn = (float)(rng.NextDouble() * Mathf.PI);
                for (int a = 0; a < arms; a++)
                {
                    float ang = turn + a * (Mathf.PI * 2f / arms) + ((float)rng.NextDouble() - 0.5f) * 0.5f;
                    float len = stubLen * (0.45f + (float)rng.NextDouble() * 0.7f);   // many are broken off short
                    Vector3 start = new Vector3(Mathf.Cos(ang) * trunkR * 0.4f, y, Mathf.Sin(ang) * trunkR * 0.4f);
                    Vector3 end = start + new Vector3(Mathf.Cos(ang) * len, -len * 0.22f, Mathf.Sin(ang) * len);
                    AddTube(mb, start, end, trunkR * 0.32f, trunkR * 0.08f, 3, false);
                }
            }
        }

        /// <summary>A dead willow: a thick short trunk forking into a few bare limbs that bend over and hang.</summary>
        private static void BuildDeadWeeping(MeshBuilder mb, float height, System.Random rng)
        {
            float trunkH = height * 0.36f;
            float trunkR = Mathf.Max(0.26f, height * 0.045f);
            AddTrunk(mb, trunkH, trunkR * 1.2f, trunkR * 0.7f);
            int limbs = 5;
            float a0 = (float)(rng.NextDouble() * Mathf.PI * 2.0);
            for (int i = 0; i < limbs; i++)
            {
                float ang = a0 + i * (Mathf.PI * 2f / limbs) + ((float)rng.NextDouble() - 0.5f) * 0.4f;
                float reach = height * (0.20f + (float)rng.NextDouble() * 0.10f);
                float lift = height * (0.20f + (float)rng.NextDouble() * 0.10f);
                Vector3 start = new Vector3(Mathf.Cos(ang) * trunkR * 0.3f, trunkH * 0.92f, Mathf.Sin(ang) * trunkR * 0.3f);
                Vector3 mid = start + new Vector3(Mathf.Cos(ang) * reach * 0.6f, lift, Mathf.Sin(ang) * reach * 0.6f);
                Vector3 end = mid + new Vector3(Mathf.Cos(ang) * reach * 0.5f, -lift * 1.1f, Mathf.Sin(ang) * reach * 0.5f);   // it bends over
                AddTube(mb, start, mid, trunkR * 0.4f, trunkR * 0.28f, 4, false);
                AddTube(mb, mid, end, trunkR * 0.28f, trunkR * 0.08f, 4, false);
            }
        }

        private static Mesh BuildTreeMesh(Species s, float height, System.Random rng, out int fruitFirst, out int fruitVerts)
        {
            var mb = new MeshBuilder();
            switch (s.Shape)
            {
                case Shape.Conifer: BuildConifer(mb, height, rng); break;
                case Shape.Weeping: BuildWeeping(mb, height, rng); break;
                case Shape.Birch: BuildBirch(mb, height, rng); break;
                default: BuildBroadleaf(mb, s.Shape, height, rng, s.FruitCount); break;
            }
            fruitFirst = mb.FruitFirst < 0 ? 0 : mb.FruitFirst;
            fruitVerts = mb.FruitFirst < 0 ? 0 : mb.Verts.Count - mb.FruitFirst;
            return mb.ToMesh($"Tree_{s.Name}");
        }

        /// <summary>
        /// The birch: a slender white trunk that stays bare for its lower half, then a loose column of many small leaf clusters up the top half
        /// (instead of one tall crown). Each cluster is a 20-triangle icosahedron, so the whole crown stays cheap.
        /// </summary>
        private static void BuildBirch(MeshBuilder mb, float height, System.Random rng)
        {
            float trunkR = Mathf.Max(0.2f, height * 0.028f);
            AddTrunk(mb, height * 0.97f, trunkR, trunkR * 0.3f);

            const int clusters = 28;
            for (int i = 0; i < clusters; i++)
            {
                float t = Mathf.Lerp(0.5f, 0.97f, (i + (float)rng.NextDouble() * 0.8f) / clusters);
                float u = Mathf.InverseLerp(0.45f, 1.02f, t);
                float spread = height * 0.15f * Mathf.Pow(Mathf.Sin(u * Mathf.PI), 0.8f) + height * 0.02f;   // fullest in the middle of the crown, narrow at the top
                float ang = (float)(rng.NextDouble() * Mathf.PI * 2.0);
                float dist = spread * (0.35f + (float)rng.NextDouble() * 0.65f);
                float r = height * (0.034f + (float)rng.NextDouble() * 0.022f) * Mathf.Lerp(1f, 0.8f, u);
                Vector3 c = new Vector3(Mathf.Cos(ang) * dist, height * t, Mathf.Sin(ang) * dist);
                Vector3[] p = new Vector3[IcoBase.Length];
                for (int k = 0; k < p.Length; k++)
                {
                    float j = 1f + ((float)rng.NextDouble() - 0.5f) * 0.4f;
                    p[k] = c + new Vector3(IcoBase[k].x * r * j, IcoBase[k].y * r * 0.8f * j, IcoBase[k].z * r * j);
                }
                for (int f = 0; f < IcoFaces.Length; f += 3)
                    mb.Tri(p[IcoFaces[f]], p[IcoFaces[f + 1]], p[IcoFaces[f + 2]], c, true);
            }

            // Bare limbs through the upper half: hidden in the summer crown, visible once the leaves are gone.
            AddBranches(mb, Shape.Oval, height * 0.5f, height * 0.17f, height * 0.3f, trunkR, rng);
        }

        /// <summary>The weeping willow: a short crooked trunk, a low dome of leaves and a curtain of long drooping strands.</summary>
        private static void BuildWeeping(MeshBuilder mb, float height, System.Random rng)
        {
            float trunkH = height * 0.30f;
            float trunkR = Mathf.Max(0.24f, height * 0.04f);
            AddTrunk(mb, trunkH + height * 0.12f, trunkR, trunkR * 0.6f);

            float rx = height * 0.30f, ry = height * 0.21f;
            Vector3 centre = new Vector3(0f, trunkH + ry * 0.8f, 0f);
            AddBlob(mb, centre, new Vector3(rx, ry, rx), rng, 0.12f);

            // The curtain: thin strands from the rim of the dome down to just above the ground, each leaning out a little.
            int strands = 22;
            float a0 = (float)(rng.NextDouble() * Mathf.PI * 2.0);
            for (int i = 0; i < strands; i++)
            {
                float ang = a0 + i * (Mathf.PI * 2f / strands) + ((float)rng.NextDouble() - 0.5f) * 0.18f;
                float rimR = rx * (0.55f + (float)rng.NextDouble() * 0.45f);
                float y0 = centre.y - ry * (0.15f + (float)rng.NextDouble() * 0.35f);
                float drop = y0 - (0.35f + (float)rng.NextDouble() * 0.6f);
                Vector3 top = new Vector3(Mathf.Cos(ang) * rimR, y0, Mathf.Sin(ang) * rimR);
                Vector3 end = top + new Vector3(Mathf.Cos(ang) * 0.15f, -drop, Mathf.Sin(ang) * 0.15f);
                float r = Mathf.Max(0.06f, height * 0.0125f);
                AddTube(mb, top, end, r * 1.5f, r * 0.5f, 3, true);   // one segment per strand: the curtain reads the same at a third of the triangles
            }
        }

        /// <summary>Small low-poly fruits on the crown's surface, in their own submesh (added last, so they are the tail of the vertices).</summary>
        private static void AddFruit(MeshBuilder mb, Vector3 centre, Vector3 radii, int count, float fruitRadius, System.Random rng)
        {
            for (int n = 0; n < count; n++)
            {
                // a point on the lower and outer part of the crown (the fruit hangs where you can see it)
                float ang = (float)(rng.NextDouble() * Mathf.PI * 2.0);
                float up = Mathf.Lerp(-0.55f, 0.55f, (float)rng.NextDouble());
                float ring = Mathf.Sqrt(1f - up * up);
                Vector3 dir = new Vector3(Mathf.Cos(ang) * ring, up, Mathf.Sin(ang) * ring);
                Vector3 p = centre + new Vector3(dir.x * radii.x, dir.y * radii.y, dir.z * radii.z) * 0.96f;   // tucked into the leaves: the crown surface is lumpy, so fruit on the ideal surface floats
                for (int f = 0; f < IcoFaces.Length; f += 3)
                    mb.FruitTri(p + IcoBase[IcoFaces[f]] * fruitRadius, p + IcoBase[IcoFaces[f + 1]] * fruitRadius, p + IcoBase[IcoFaces[f + 2]] * fruitRadius, p);
            }
        }

        private static void BuildBroadleaf(MeshBuilder mb, Shape shape, float height, System.Random rng, int fruitCount = 0)
        {
            float trunkFrac, widthRatio, vertScale;
            switch (shape)
            {
                case Shape.Oval: trunkFrac = 0.34f; widthRatio = 0.62f; vertScale = 1.0f; break;
                case Shape.Columnar: trunkFrac = 0.22f; widthRatio = 0.40f; vertScale = 1.0f; break;
                case Shape.Broad: trunkFrac = 0.36f; widthRatio = 1.55f; vertScale = 0.8f; break;
                case Shape.Orchard: trunkFrac = 0.34f; widthRatio = 1.2f; vertScale = 0.88f; break;
                default: trunkFrac = 0.40f; widthRatio = 1.2f; vertScale = 0.92f; break; // Round
            }

            float trunkH = height * trunkFrac;
            float crownH = height - trunkH;
            float ry = crownH / 1.75f * vertScale;
            float rx = ry * widthRatio;
            float trunkR = Mathf.Max(shape == Shape.Orchard ? 0.14f : 0.22f, height * (shape == Shape.Broad ? 0.045f : (shape == Shape.Orchard ? 0.04f : 0.032f)));

            AddTrunk(mb, trunkH + ry * 0.6f, trunkR, trunkR * 0.6f);

            Vector3 centre = new Vector3(0f, trunkH + ry * 0.75f, 0f);
            AddBlob(mb, centre, new Vector3(rx, ry, rx), rng, 0.14f);

            // A couple of smaller lobes so the crown isn't a single ball.
            int lobes = (shape == Shape.Broad || shape == Shape.Orchard) ? 3 : (shape == Shape.Columnar ? 0 : 2);
            for (int i = 0; i < lobes; i++)
            {
                float ang = (float)(rng.NextDouble() * Mathf.PI * 2.0);
                float off = rx * (0.55f + (float)rng.NextDouble() * 0.25f);
                Vector3 lc = centre + new Vector3(Mathf.Cos(ang) * off, (float)(rng.NextDouble() - 0.35) * ry * 0.6f, Mathf.Sin(ang) * off);
                float k = 0.55f + (float)rng.NextDouble() * 0.15f;
                AddBlob(mb, lc, new Vector3(rx * k, ry * k, rx * k), rng, 0.14f);
            }

            AddBranches(mb, shape, trunkH, rx, ry, trunkR, rng);

            // Last of all, so the fruit is the tail of this variant's vertices.
            if (fruitCount > 0) AddFruit(mb, centre, new Vector3(rx, ry, rx), fruitCount, Mathf.Max(0.12f, height * 0.046f), rng);
        }

        /// <summary>Bare branches in the trunk submesh: hidden inside the summer crown, visible once the leaves are gone.</summary>
        private static void AddBranches(MeshBuilder mb, Shape shape, float trunkH, float rx, float ry, float trunkR, System.Random rng)
        {
            int count = shape == Shape.Broad ? 8 : (shape == Shape.Columnar ? 5 : 6);
            float lift = shape == Shape.Broad ? 0.45f : (shape == Shape.Columnar ? 1.3f : 0.85f);   // upward lean
            float reach = shape == Shape.Columnar ? rx * 1.1f : rx * 0.95f;
            float yLow = trunkH * 0.75f, yHigh = trunkH + ry * 0.9f;
            float ang0 = (float)(rng.NextDouble() * Mathf.PI * 2.0);

            for (int i = 0; i < count; i++)
            {
                // Spread round the trunk (golden-angle spacing), higher branches shorter.
                float ang = ang0 + i * 2.39996f;
                float t = count <= 1 ? 0f : (float)i / (count - 1);
                float y = Mathf.Lerp(yLow, yHigh, t);
                float len = reach * Mathf.Lerp(1.05f, 0.55f, t) * (0.85f + (float)rng.NextDouble() * 0.3f);
                Vector3 dir = new Vector3(Mathf.Cos(ang), lift * (0.6f + (float)rng.NextDouble() * 0.5f), Mathf.Sin(ang)).normalized;

                Vector3 start = new Vector3(Mathf.Cos(ang) * trunkR * 0.3f, y, Mathf.Sin(ang) * trunkR * 0.3f);
                Vector3 mid = start + dir * len * 0.55f;
                Vector3 end = start + dir * len + Vector3.up * len * 0.12f;
                float r0 = Mathf.Max(0.05f, trunkR * Mathf.Lerp(0.55f, 0.3f, t));
                AddTube(mb, start, mid, r0, r0 * 0.6f, 3, false);
                AddTube(mb, mid, end, r0 * 0.6f, r0 * 0.15f, 3, false);

                // A couple of twigs off the outer half.
                for (int k = 0; k < 1; k++)   // one twig per branch (two cost triangles in every tree and its shadow for a look you only see in winter)
                {
                    float side = (k == 0 ? 1f : -1f) * (0.5f + (float)rng.NextDouble() * 0.5f);
                    Vector3 perp = Vector3.Cross(dir, Vector3.up).normalized;
                    Vector3 tb = Vector3.Lerp(mid, end, 0.25f + (float)rng.NextDouble() * 0.3f);
                    Vector3 te = tb + (dir * 0.6f + perp * side + Vector3.up * 0.5f).normalized * len * 0.35f;
                    AddTube(mb, tb, te, r0 * 0.35f, r0 * 0.1f, 3, false);
                }
            }
        }

        private static void BuildConifer(MeshBuilder mb, float height, System.Random rng)
        {
            float trunkH = height * 0.16f;
            float trunkR = Mathf.Max(0.2f, height * 0.028f);
            AddTrunk(mb, height * 0.55f, trunkR, trunkR * 0.45f);

            const int tiers = 4;
            float span = height - trunkH;
            float maxR = height * 0.30f;
            for (int i = 0; i < tiers; i++)
            {
                // Tiers start closer together and each cone is taller and wider, so they overlap much more.
                float baseY = trunkH + span * 0.19f * i;
                float coneH = span * 0.50f - i * span * 0.03f;
                float r = maxR * (1f - i * 0.18f);
                AddCone(mb, baseY, coneH, r, 8, rng);
            }
        }

        private static void AddTrunk(MeshBuilder mb, float h, float r0, float r1)
        {
            const int sides = 6;
            Vector3 centre = new Vector3(0f, h * 0.5f, 0f);
            for (int i = 0; i < sides; i++)
            {
                float a0 = i * Mathf.PI * 2f / sides, a1 = (i + 1) * Mathf.PI * 2f / sides;
                Vector3 b0 = new Vector3(Mathf.Cos(a0) * r0, 0f, Mathf.Sin(a0) * r0);
                Vector3 b1 = new Vector3(Mathf.Cos(a1) * r0, 0f, Mathf.Sin(a1) * r0);
                Vector3 t0 = new Vector3(Mathf.Cos(a0) * r1, h, Mathf.Sin(a0) * r1);
                Vector3 t1 = new Vector3(Mathf.Cos(a1) * r1, h, Mathf.Sin(a1) * r1);
                mb.Tri(b0, t0, t1, centre, false);
                mb.Tri(b0, t1, b1, centre, false);
            }
        }

        private static void AddCone(MeshBuilder mb, float baseY, float height, float radius, int sides, System.Random rng)
        {
            Vector3 apex = new Vector3(0f, baseY + height, 0f);
            Vector3 centre = new Vector3(0f, baseY + height * 0.3f, 0f);
            float twist = (float)(rng.NextDouble() * Mathf.PI);
            for (int i = 0; i < sides; i++)
            {
                float a0 = twist + i * Mathf.PI * 2f / sides, a1 = twist + (i + 1) * Mathf.PI * 2f / sides;
                float j0 = 1f + ((float)rng.NextDouble() - 0.5f) * 0.16f;
                float j1 = 1f + ((float)rng.NextDouble() - 0.5f) * 0.16f;
                Vector3 p0 = new Vector3(Mathf.Cos(a0) * radius * j0, baseY, Mathf.Sin(a0) * radius * j0);
                Vector3 p1 = new Vector3(Mathf.Cos(a1) * radius * j1, baseY, Mathf.Sin(a1) * radius * j1);
                mb.Tri(apex, p0, p1, centre, true);
            }
        }

        // ---- icosphere (one subdivision: 42 verts, 80 faces), jittered, then scaled to an ellipsoid

        private static readonly Vector3[] IcoBase = BuildIcoBase();
        private static readonly int[] IcoFaces =
        {
            0,11,5,  0,5,1,  0,1,7,  0,7,10,  0,10,11,
            1,5,9,   5,11,4,  11,10,2, 10,7,6,  7,1,8,
            3,9,4,   3,4,2,   3,2,6,   3,6,8,   3,8,9,
            4,9,5,   2,4,11,  6,2,10,  8,6,7,   9,8,1,
        };

        private static Vector3[] BuildIcoBase()
        {
            float t = (1f + Mathf.Sqrt(5f)) * 0.5f;
            var v = new[]
            {
                new Vector3(-1, t, 0), new Vector3(1, t, 0), new Vector3(-1, -t, 0), new Vector3(1, -t, 0),
                new Vector3(0, -1, t), new Vector3(0, 1, t), new Vector3(0, -1, -t), new Vector3(0, 1, -t),
                new Vector3(t, 0, -1), new Vector3(t, 0, 1), new Vector3(-t, 0, -1), new Vector3(-t, 0, 1),
            };
            for (int i = 0; i < v.Length; i++) v[i].Normalize();
            return v;
        }

        private static void AddBlob(MeshBuilder mb, Vector3 centre, Vector3 radii, System.Random rng, float jitter)
        {
            var verts = new List<Vector3>(IcoBase);
            var midCache = new Dictionary<long, int>();
            int Mid(int a, int b)
            {
                long key = a < b ? ((long)a << 32) | (uint)b : ((long)b << 32) | (uint)a;
                if (midCache.TryGetValue(key, out int idx)) return idx;
                verts.Add(((verts[a] + verts[b]) * 0.5f).normalized);
                idx = verts.Count - 1;
                midCache[key] = idx;
                return idx;
            }

            var faces = new List<int>();
            for (int f = 0; f < IcoFaces.Length; f += 3)
            {
                int a = IcoFaces[f], b = IcoFaces[f + 1], c = IcoFaces[f + 2];
                int ab = Mid(a, b), bc = Mid(b, c), ca = Mid(c, a);
                faces.AddRange(new[] { a, ab, ca, b, bc, ab, c, ca, bc, ab, bc, ca });
            }

            // Jitter each shared vertex once so the blob stays closed, then scale to the ellipsoid.
            var pos = new Vector3[verts.Count];
            for (int i = 0; i < verts.Count; i++)
            {
                float r = 1f + ((float)rng.NextDouble() - 0.5f) * 2f * jitter;
                Vector3 d = verts[i] * r;
                pos[i] = centre + new Vector3(d.x * radii.x, d.y * radii.y, d.z * radii.z);
            }

            for (int f = 0; f < faces.Count; f += 3)
                mb.Tri(pos[faces[f]], pos[faces[f + 1]], pos[faces[f + 2]], centre, true);
        }
    }
}
