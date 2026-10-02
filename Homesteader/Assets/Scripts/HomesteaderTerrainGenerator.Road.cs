using System.Collections.Generic;
using UnityEngine;
using Homesteader.Growth;

namespace Homesteader.Generation
{
    /// <summary>
    /// The starter road: a soft, meandering dirt and gravel road from a map edge to the edge of the starter grass area
    /// (GameRules.StarterRoad). Routed around water over the real terrain, smoothed, then baked into a mask texture the
    /// terrain shader paints a procedural dirt / gravel surface from (see RoadTexture in GenerativeTerrainURP.shader).
    /// Deterministic from the world seed, so nothing is saved.
    /// </summary>
    public partial class HomesteaderTerrainGenerator
    {
        // ------------------------------------------------------------------ state

        private readonly List<Vector2> roadPoints = new List<Vector2>();   // centreline, 1 m apart, map edge -> grass area
        private float[,] roadDist;          // [x, z] 1 m grid: distance to the centreline (RoadFarDist when far)
        private float roadHalfWidth = 1.7f;
        private Texture2D roadMaskTex;      // R = coverage, G = lateral offset (0.5 = centreline), B/A unused

        private const float RoadFarDist = 99f;
        private const int RoadTexelsPerMetre = 2;
        private const float RoadLateralRange = 6f;   // metres either side of the centreline encoded in G (shader must match)
        private const float RoadGridCell = 5f;       // route-finding grid
        private const float RoadFadeLength = 18f;     // metres over which the road blends into the grass at its end

        /// <summary>The road centreline, from the map edge to the grass area (empty when the road is off or was not possible).</summary>
        public IReadOnlyList<Vector2> RoadPoints => roadPoints;

        /// <summary>True when (x, z) is on the road or within margin metres of its edge (margin up to about 6 m).</summary>
        public bool IsNearRoad(float worldX, float worldZ, float margin)
        {
            if (roadDist == null) return false;
            return RoadDistanceAt(worldX, worldZ) < roadHalfWidth + margin;
        }

        /// <summary>Bilinear distance (m) to the road centreline, RoadFarDist when there is no road nearby.</summary>
        private float RoadDistanceAt(float worldX, float worldZ)
        {
            if (roadDist == null) return RoadFarDist;
            int res = roadDist.GetLength(0);
            float fx = Mathf.Clamp(worldX - 0.5f, 0f, res - 1.001f);
            float fz = Mathf.Clamp(worldZ - 0.5f, 0f, res - 1.001f);
            int x0 = Mathf.FloorToInt(fx), z0 = Mathf.FloorToInt(fz);
            int x1 = Mathf.Min(x0 + 1, res - 1), z1 = Mathf.Min(z0 + 1, res - 1);
            float tx = fx - x0, tz = fz - z0;
            float a = Mathf.Lerp(roadDist[x0, z0], roadDist[x1, z0], tx);
            float b = Mathf.Lerp(roadDist[x0, z1], roadDist[x1, z1], tx);
            return Mathf.Lerp(a, b, tz);
        }

        /// <summary>0..1: 1 on the road, easing to 0 about 6 m off its edge. Used to ease terracing off the road bed.</summary>
        private float RoadInfluence(float worldX, float worldZ)
        {
            if (roadDist == null) return 0f;
            float d = RoadDistanceAt(worldX, worldZ);
            return 1f - Mathf.SmoothStep(0f, 1f, Mathf.InverseLerp(roadHalfWidth + 1f, roadHalfWidth + 7f, d));
        }

        // ------------------------------------------------------------------ generation

        /// <summary>Builds the road and its mask. Call after the water mask and distance field exist.</summary>
        private void GenerateStarterRoad()
        {
            roadPoints.Clear();
            roadDist = null;

            var rule = GameRules.StarterRoad;
            var zone = GameRules.StarterZone;
            if (rule.Enabled && zone.Enabled)
            {
                roadHalfWidth = Mathf.Max(0.8f, rule.WidthM * 0.5f);
                BuildRoadRoute(rule, zone);
            }
            BakeRoadMask();
        }

        private void BuildRoadRoute(GameRules.StarterRoadRules rule, GameRules.StarterZoneRules zone)
        {
            float tile = Homesteader.Land.LandOwnershipSystem.TileSize;
            Vector2 centre = new Vector2((zone.TileX + 0.5f) * tile, (zone.TileZ + 0.5f) * tile);
            float half = Mathf.Max(1f, zone.GrassAreaM * 0.5f);

            var rng = new System.Random(worldSeed * 104729 + 7);
            int n = Mathf.CeilToInt(terrainSizeX / RoadGridCell);

            // Cost field over the grid: rough ground, wandering noise, and water.
            var elev = new float[n * n];
            var mul = new float[n * n];
            var wetCost = new float[n * n];
            float seedA = (worldSeed % 977) * 0.61f, seedB = (worldSeed % 613) * 0.37f;
            for (int z = 0; z < n; z++)
                for (int x = 0; x < n; x++)
                {
                    float wx = (x + 0.5f) * RoadGridCell, wz = (z + 0.5f) * RoadGridCell;
                    int i = z * n + x;
                    elev[i] = CalculateElevationAt(wx, wz);
                    // Water is crossed with a bridge (ProceduralBridge) when that beats a long detour: a river is a
                    // fair price, a lake or pond a prohibitive one, and the bank either side is avoided where it can be.
                    if (IsWaterAt(wx, wz)) wetCost[i] = IsInsidePond(wx, wz) ? 400f : 70f;
                    else if (GetWaterDistance(wx, wz) < roadHalfWidth + 5f) wetCost[i] = 30f;
                    // Broad noise makes the route wander instead of running as the crow flies.
                    mul[i] = 1f + 1.3f * Mathf.PerlinNoise(wx * 0.011f + seedA, wz * 0.011f + seedB);
                }

            // One candidate per map edge (random start along it); keep the cheapest, with a little seeded variety.
            List<Vector2> best = null;
            float bestScore = float.MaxValue;
            for (int edge = 0; edge < 4; edge++)
            {
                Vector2 start = RoadEdgeStart(edge, rng);
                Vector2 dir = (start - centre);
                if (dir.sqrMagnitude < 1f) continue;
                dir.Normalize();
                // Where that direction meets the boundary of the grass square.
                float scale = half / Mathf.Max(Mathf.Abs(dir.x), Mathf.Abs(dir.y));
                Vector2 goal = centre + dir * scale;

                List<Vector2> route = RouteRoad(start, goal, n, elev, mul, wetCost, out float cost);
                if (route == null) continue;
                float score = cost * (0.88f + 0.24f * (float)rng.NextDouble());
                if (score < bestScore) { bestScore = score; best = route; }
            }
            if (best == null) return;

            ShapeRoad(best, rule, rng);
        }

        /// <summary>A start point on a map edge (0 = south, 1 = east, 2 = north, 3 = west), kept toward the middle of the edge.</summary>
        private Vector2 RoadEdgeStart(int edge, System.Random rng)
        {
            float along = 0.3f + 0.4f * (float)rng.NextDouble();
            switch (edge)
            {
                case 0: return new Vector2(along * terrainSizeX, 0.5f);
                case 1: return new Vector2(terrainSizeX - 0.5f, along * terrainSizeZ);
                case 2: return new Vector2(along * terrainSizeX, terrainSizeZ - 0.5f);
                default: return new Vector2(0.5f, along * terrainSizeZ);
            }
        }

        /// <summary>A* over the coarse grid, 8 neighbours. Returns the route as world points (start ... goal), or null.</summary>
        private List<Vector2> RouteRoad(Vector2 start, Vector2 goal, int n, float[] elev, float[] mul, float[] wetCost, out float totalCost)
        {
            totalCost = 0f;
            int sx = Mathf.Clamp((int)(start.x / RoadGridCell), 0, n - 1), sz = Mathf.Clamp((int)(start.y / RoadGridCell), 0, n - 1);
            int gx = Mathf.Clamp((int)(goal.x / RoadGridCell), 0, n - 1), gz = Mathf.Clamp((int)(goal.y / RoadGridCell), 0, n - 1);
            int startId = sz * n + sx, goalId = gz * n + gx;

            var g = new float[n * n];
            var prev = new int[n * n];
            var closed = new bool[n * n];
            for (int i = 0; i < g.Length; i++) { g[i] = float.MaxValue; prev[i] = -1; }
            g[startId] = 0f;

            var open = new SortedSet<(float f, int id)>();
            open.Add((Heuristic(sx, sz, gx, gz), startId));

            while (open.Count > 0)
            {
                var top = open.Min;
                open.Remove(top);
                int cur = top.id;
                if (closed[cur]) continue;
                closed[cur] = true;
                if (cur == goalId) break;

                int cx = cur % n, cz = cur / n;
                for (int dz = -1; dz <= 1; dz++)
                    for (int dx = -1; dx <= 1; dx++)
                    {
                        if (dx == 0 && dz == 0) continue;
                        int nx = cx + dx, nz = cz + dz;
                        if (nx < 0 || nz < 0 || nx >= n || nz >= n) continue;
                        int nid = nz * n + nx;
                        if (closed[nid]) continue;

                        float dist = (dx != 0 && dz != 0) ? 1.4142f : 1f;
                        float step = dist * RoadGridCell * 0.5f * (mul[cur] + mul[nid]);
                        step += Mathf.Abs(elev[nid] - elev[cur]) * 10f;      // hills cost: roads follow the easy ground
                        if (nid != goalId) step += wetCost[nid];             // water and its banks (see the cost field above)
                        float ng = g[cur] + step;
                        if (ng < g[nid])
                        {
                            g[nid] = ng;
                            prev[nid] = cur;
                            open.Add((ng + Heuristic(nx, nz, gx, gz), nid));
                        }
                    }
            }

            if (prev[goalId] < 0 && goalId != startId) return null;
            totalCost = g[goalId];

            var cells = new List<Vector2>();
            for (int id = goalId; id >= 0; id = prev[id])
            {
                cells.Add(new Vector2((id % n + 0.5f) * RoadGridCell, (id / n + 0.5f) * RoadGridCell));
                if (id == startId) break;
            }
            cells.Reverse();
            // Exact ends: on the map edge, and on the grass area boundary.
            cells[0] = start;
            cells[cells.Count - 1] = goal;
            return cells;
        }

        private static float Heuristic(int x, int z, int gx, int gz)
        {
            float dx = x - gx, dz = z - gz;
            return Mathf.Sqrt(dx * dx + dz * dz) * RoadGridCell;   // never above the true cost (every step costs at least this)
        }

        /// <summary>Turns the grid route into a soft meandering centreline: spline, even spacing, gentle lateral wander, smoothing.</summary>
        private void ShapeRoad(List<Vector2> route, GameRules.StarterRoadRules rule, System.Random rng)
        {
            // Catmull-Rom through the route points, then even 1 m spacing.
            var spline = new List<Vector2>();
            for (int i = 0; i < route.Count - 1; i++)
            {
                Vector2 p0 = route[Mathf.Max(i - 1, 0)], p1 = route[i], p2 = route[i + 1], p3 = route[Mathf.Min(i + 2, route.Count - 1)];
                for (int s = 0; s < 8; s++)
                {
                    float t = s / 8f, t2 = t * t, t3 = t2 * t;
                    spline.Add(0.5f * ((2f * p1) + (-p0 + p2) * t + (2f * p0 - 5f * p1 + 4f * p2 - p3) * t2 + (-p0 + 3f * p1 - 3f * p2 + p3) * t3));
                }
            }
            spline.Add(route[route.Count - 1]);

            List<Vector2> pts = ResamplePolyline(spline, 1f);
            if (pts.Count < 4) return;

            // Soft meander: slow lateral wander that is zero at both ends, so the road still meets the edge and the grass.
            float seed = (worldSeed % 419) * 0.73f;
            float amp = Mathf.Max(0f, rule.MeanderM);
            int count = pts.Count;
            var shifted = new Vector2[count];
            for (int i = 0; i < count; i++)
            {
                Vector2 tangent = (pts[Mathf.Min(i + 1, count - 1)] - pts[Mathf.Max(i - 1, 0)]).normalized;
                Vector2 normal = new Vector2(-tangent.y, tangent.x);
                float env = Mathf.SmoothStep(0f, 1f, i / 35f) * Mathf.SmoothStep(0f, 1f, (count - 1 - i) / 14f);
                float wander = (Mathf.PerlinNoise(i * 0.035f + seed, 3.7f) - 0.5f) * 2f
                             + (Mathf.PerlinNoise(i * 0.11f + seed, 9.1f) - 0.5f) * 2f * 0.3f;
                Vector2 candidate = pts[i] + normal * wander * amp * env;
                // Never wander into the water: keep the wander only where the bank is well clear.
                bool clear = !IsWaterAt(candidate.x, candidate.y) && GetWaterDistance(candidate.x, candidate.y) > roadHalfWidth + 2.5f;
                shifted[i] = clear ? candidate : pts[i];
            }
            for (int i = 0; i < count; i++) pts[i] = shifted[i];

            // Smooth away kinks (ends stay put).
            for (int iter = 0; iter < 10; iter++)
            {
                var next = new Vector2[count];
                next[0] = pts[0];
                next[count - 1] = pts[count - 1];
                for (int i = 1; i < count - 1; i++) next[i] = (pts[i - 1] + pts[i] * 2f + pts[i + 1]) * 0.25f;
                for (int i = 0; i < count; i++) pts[i] = next[i];
            }

            roadPoints.AddRange(ResamplePolyline(pts, 1f));
        }

        private static List<Vector2> ResamplePolyline(List<Vector2> src, float step)
        {
            var result = new List<Vector2> { src[0] };
            float carry = 0f;
            for (int i = 1; i < src.Count; i++)
            {
                Vector2 a = src[i - 1], b = src[i];
                float segLen = Vector2.Distance(a, b);
                if (segLen < 1e-5f) continue;
                float d = step - carry;
                while (d <= segLen)
                {
                    result.Add(Vector2.Lerp(a, b, d / segLen));
                    d += step;
                }
                carry = segLen - (d - step);
            }
            if (Vector2.Distance(result[result.Count - 1], src[src.Count - 1]) > 0.05f) result.Add(src[src.Count - 1]);
            return result;
        }

        // ------------------------------------------------------------------ mask

        /// <summary>Builds roadDist (1 m) and the road mask texture (2 texels / m). With no road, a black 1 x 1 mask.</summary>
        private void BakeRoadMask()
        {
            if (roadPoints.Count < 2)
            {
                roadDist = null;
                if (roadMaskTex == null || roadMaskTex.width != 1)
                {
                    roadMaskTex = new Texture2D(1, 1, TextureFormat.RGBA32, false, true) { wrapMode = TextureWrapMode.Clamp };
                }
                roadMaskTex.SetPixel(0, 0, new Color(0f, 0.5f, 0f, 0f));
                roadMaskTex.Apply();
                return;
            }

            int res = Mathf.RoundToInt(terrainSizeX);
            roadDist = new float[res, res];
            for (int z = 0; z < res; z++)
                for (int x = 0; x < res; x++) roadDist[x, z] = RoadFarDist;

            int S = RoadTexelsPerMetre;
            int N = res * S;
            var bestD = new float[N, N];
            var bestLat = new float[N, N];
            var bestIdx = new int[N, N];
            for (int z = 0; z < N; z++)
                for (int x = 0; x < N; x++) bestD[x, z] = float.MaxValue;

            int count = roadPoints.Count;
            float brush = roadHalfWidth + 2.2f;                 // metres either side painted into the mask
            int brushTexels = Mathf.CeilToInt(brush * S) + 1;
            const int distBrush = 8;                            // metres either side kept in roadDist

            for (int i = 0; i < count; i++)
            {
                Vector2 p = roadPoints[i];
                Vector2 tangent = (roadPoints[Mathf.Min(i + 1, count - 1)] - roadPoints[Mathf.Max(i - 1, 0)]).normalized;

                // Distance grid (vegetation clearance, terrace easing).
                int cx = Mathf.RoundToInt(p.x), cz = Mathf.RoundToInt(p.y);
                for (int dz = -distBrush; dz <= distBrush; dz++)
                    for (int dx = -distBrush; dx <= distBrush; dx++)
                    {
                        int px = cx + dx, pz = cz + dz;
                        if (px < 0 || pz < 0 || px >= res || pz >= res) continue;
                        float d = Vector2.Distance(new Vector2(px + 0.5f, pz + 0.5f), p);
                        if (d < roadDist[px, pz]) roadDist[px, pz] = d;
                    }

                // Mask texels.
                int tx = Mathf.RoundToInt(p.x * S), tz = Mathf.RoundToInt(p.y * S);
                for (int dz = -brushTexels; dz <= brushTexels; dz++)
                    for (int dx = -brushTexels; dx <= brushTexels; dx++)
                    {
                        int px = tx + dx, pz = tz + dz;
                        if (px < 0 || pz < 0 || px >= N || pz >= N) continue;
                        Vector2 c = new Vector2((px + 0.5f) / S, (pz + 0.5f) / S);
                        float d = Vector2.Distance(c, p);
                        if (d >= bestD[px, pz]) continue;
                        bestD[px, pz] = d;
                        bestIdx[px, pz] = i;
                        // Signed lateral offset: which side of the centreline this texel lies on.
                        bestLat[px, pz] = tangent.x * (c.y - p.y) - tangent.y * (c.x - p.x);
                    }
            }

            var pixels = new Color32[N * N];
            for (int pz = 0; pz < N; pz++)
                for (int px = 0; px < N; px++)
                {
                    float d = bestD[px, pz];
                    if (d > brush) { pixels[pz * N + px] = new Color32(0, 128, 0, 0); continue; }

                    float wx = (px + 0.5f) / S, wz = (pz + 0.5f) / S;
                    int idx = bestIdx[px, pz];

                    // Width drifts slowly along the road; the edge is ragged and soft (worn dirt, not a painted line).
                    float widthVar = 0.85f + 0.3f * Mathf.PerlinNoise(idx * 0.045f + 11.3f, 0.5f);
                    // Toward the grass the road narrows and frays: a worn track that gives way to the lawn, not a cut-off.
                    float endDist = count - 1 - idx;
                    float fadeT = Mathf.Clamp01(endDist / RoadFadeLength);
                    float hw = roadHalfWidth * widthVar * Mathf.Lerp(0.55f, 1f, Mathf.SmoothStep(0f, 1f, fadeT));
                    float ragged = (Mathf.PerlinNoise(wx * 0.45f + 3.1f, wz * 0.45f + 7.7f) - 0.5f) * 0.7f
                                 + (Mathf.PerlinNoise(wx * 1.6f + 9.4f, wz * 1.6f + 1.3f) - 0.5f) * 0.3f;
                    float edge = d + ragged;
                    float coverage = 1f - Mathf.SmoothStep(0f, 1f, Mathf.InverseLerp(hw - 0.3f, hw + 0.5f, edge));   // GLSL-style smoothstep

                    // Break the fade up with noise so the road dissolves into patches of bare dirt and gravel that thin out
                    // into the grass, instead of shrinking away in one clean gradient.
                    float patch = Mathf.PerlinNoise(wx * 0.55f + 21.7f, wz * 0.55f + 5.3f);
                    float t = fadeT * 1.3f - (1f - patch) * 0.45f;
                    coverage *= Mathf.SmoothStep(0f, 1f, Mathf.Clamp01(t / 0.6f));

                    float lat = Mathf.Clamp(bestLat[px, pz] / (2f * RoadLateralRange) + 0.5f, 0f, 1f);
                    pixels[pz * N + px] = new Color32((byte)Mathf.RoundToInt(Mathf.Clamp01(coverage) * 255f), (byte)Mathf.RoundToInt(lat * 255f), 0, 255);
                }

            if (roadMaskTex == null || roadMaskTex.width != N)
            {
                roadMaskTex = new Texture2D(N, N, TextureFormat.RGBA32, false, true)
                {
                    filterMode = FilterMode.Bilinear,
                    wrapMode = TextureWrapMode.Clamp,
                };
            }
            roadMaskTex.SetPixelData(pixels, 0);
            roadMaskTex.Apply();
        }

        /// <summary>Hands the road mask to the terrain material (called wherever the other terrain maps are assigned).</summary>
        private void ApplyRoadMaskToMaterial(Material mat)
        {
            if (mat == null) return;
            mat.SetTexture("_RoadMask", roadMaskTex != null ? roadMaskTex : Texture2D.blackTexture);
            mat.SetVector("_RoadParams", new Vector4(RoadLateralRange, roadHalfWidth, 0f, 0f));
        }
    }
}
