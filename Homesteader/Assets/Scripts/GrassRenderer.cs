using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using Homesteader.Generation;

namespace Homesteader.Grass
{
    /// <summary>
    /// Bakes all grass blades into chunked static meshes.
    /// Each chunk is a separate GameObject with its own MeshRenderer so Unity
    /// can frustum-cull off-screen chunks — the GPU only processes visible grass.
    /// Zero CPU per-frame work; wind animation is done in the vertex shader.
    /// </summary>
    [RequireComponent(typeof(MeshFilter), typeof(MeshRenderer))]
    public class GrassRenderer : MonoBehaviour
    {
        [Header("Grass Density (blades per m²)")]
        [SerializeField] private float shortGrassDensity = 60f;
        [SerializeField] private float tallGrassDensity = 90f;

        [Header("Blade Dimensions")]
        [SerializeField] private float shortBladeHeight = 0.15f;
        [SerializeField] private float tallBladeHeight = 0.35f;
        [SerializeField] private float bladeWidth = 0.04f;

        [Header("Flowers")]
        [SerializeField] private float flowerChance = 0.08f;

        [Header("Colors")]
        [SerializeField] private Color baseColor = new Color(0.20f, 0.65f, 0.28f, 1f);
        [SerializeField] private Color tipColor = new Color(0.35f, 0.78f, 0.35f, 1f);

        [Header("Wind")]
        [SerializeField] private float windStrength = 0.3f;

        [Header("Chunking")]
        [SerializeField] private int chunkSizeMeters = 50;

        private Material grassMaterial;
        private GameObject chunkContainer;
        private bool isGenerating;
        public bool IsGenerating => isGenerating;
        private readonly List<GameObject> chunkObjects = new List<GameObject>();
        private readonly List<Mesh> chunkMeshes = new List<Mesh>();

        private HomesteaderTerrainGenerator terrainGen;
        private Terrain terrain;

        private static readonly int GrassWindParamsId = Shader.PropertyToID("_GrassWindParams");

        void OnEnable()
        {
            EnsureMaterial();
            // Only auto-generate on play mode entry if terrain already exists
            // (scene load / Continue). During New Game, terrain generation
            // triggers grass via RegenerateGrass() when it finishes.
            if (chunkMeshes.Count == 0 && Application.isPlaying && !isGenerating)
            {
                var gen = FindObjectOfType<HomesteaderTerrainGenerator>();
                if (gen != null && gen.GetBakedBiomeMap() != null && !gen.IsGenerating)
                {
                    StartCoroutine(RegenerateAsync());
                }
            }
        }

        void OnDestroy()
        {
            ReleaseAll();
        }

        void ReleaseAll()
        {
            foreach (var go in chunkObjects) { if (go != null) DestroyImmediate(go); }
            foreach (var m in chunkMeshes) { if (m != null) DestroyImmediate(m); }
            chunkObjects.Clear();
            chunkMeshes.Clear();
            if (grassMaterial != null) DestroyImmediate(grassMaterial);
            if (chunkContainer != null) DestroyImmediate(chunkContainer);
            chunkContainer = null;

            // Clear the parent's own MeshFilter (leftover from old single-mesh approach)
            var ownMF = GetComponent<MeshFilter>();
            if (ownMF != null && ownMF.sharedMesh != null)
            {
                DestroyImmediate(ownMF.sharedMesh);
                ownMF.sharedMesh = null;
            }
        }

        void EnsureMaterial()
        {
            if (grassMaterial != null) return;
            Shader grassShader = Shader.Find("Homesteader/Grass");
            if (grassShader == null)
            {
                Debug.LogError("[GrassRenderer] Grass shader not found!");
                return;
            }
            grassMaterial = new Material(grassShader);
            grassMaterial.SetColor("_BaseColor", baseColor);
            grassMaterial.SetColor("_TipColor", tipColor);
        }

        public void Regenerate()
        {
            // Stop any existing generation and release old chunks
            if (isGenerating)
            {
                StopAllCoroutines();
                isGenerating = false;
            }
            ReleaseAll();
            StartCoroutine(RegenerateAsync());
        }

        IEnumerator RegenerateAsync()
        {
            isGenerating = true;
            terrainGen = FindObjectOfType<HomesteaderTerrainGenerator>();
            if (terrainGen == null)
            {
                Debug.LogWarning("[GrassRenderer] No terrain generator found.");
                isGenerating = false;
                yield break;
            }

            terrain = terrainGen.GetComponent<Terrain>();
            if (terrain == null) { isGenerating = false; yield break; }

            Texture2D biomeMap = terrainGen.GetBakedBiomeMap();
            if (biomeMap == null)
            {
                Debug.LogWarning("[GrassRenderer] No biome map found.");
                isGenerating = false;
                yield break;
            }

            Vector3 origin = terrainGen.transform.position;
            float sizeX = terrainGen.terrainSizeX;
            float sizeZ = terrainGen.terrainSizeZ;
            int mapRes = biomeMap.width;
            Color[] pixels = biomeMap.GetPixels();

            // Clean up old chunks
            ReleaseAll();
            EnsureMaterial();

            // Blade template (local space, Y-up, centered at base)
            float w = bladeWidth;
            Vector3[] bladeVerts = new Vector3[]
            {
                new Vector3(-w * 0.5f, 0f, 0f),
                new Vector3( w * 0.5f, 0f, 0f),
                new Vector3(-w * 0.35f, 0.5f, 0f),
                new Vector3( w * 0.35f, 0.5f, 0f),
                new Vector3(0f, 1f, 0f),
            };
            Vector2[] bladeUVs = new Vector2[]
            {
                new Vector2(0, 0), new Vector2(1, 0),
                new Vector2(0, 0.5f), new Vector2(1, 0.5f),
                new Vector2(0.5f, 1),
            };
            int[] bladeTris = new int[]
            {
                0, 2, 1,  1, 2, 3,  2, 4, 3,
                1, 2, 0,  3, 2, 1,  3, 4, 2,
            };

            // Group blades by chunk
            int chunksX = Mathf.CeilToInt(sizeX / chunkSizeMeters);
            int chunksZ = Mathf.CeilToInt(sizeZ / chunkSizeMeters);
            int totalChunks = chunksX * chunksZ;

            var chunkData = new List<List<Vector3>>(totalChunks);
            var chunkUVs = new List<List<Vector2>>(totalChunks);
            var chunkUV2s = new List<List<Vector2>>(totalChunks);
            var chunkNormals = new List<List<Vector3>>(totalChunks);
            var chunkTris = new List<List<int>>(totalChunks);
            var chunkVertOffsets = new int[totalChunks];
            var chunkBladeCounts = new int[totalChunks];

            for (int i = 0; i < totalChunks; i++)
            {
                chunkData.Add(new List<Vector3>(20000));
                chunkUVs.Add(new List<Vector2>(20000));
                chunkUV2s.Add(new List<Vector2>(20000));
                chunkNormals.Add(new List<Vector3>(20000));
                chunkTris.Add(new List<int>(24000));
            }

            int totalBlades = 0;
            int bladesSinceYield = 0;

            for (int py = 0; py < mapRes; py++)
            {
                for (int px = 0; px < mapRes; px++)
                {
                    Color c = pixels[py * mapRes + px];
                    int biomeMode = (int)(c.a * 16.0f);

                    bool isShortGrass = (biomeMode == 0);
                    bool isTallGrass = (biomeMode == 13);
                    if (!isShortGrass && !isTallGrass) continue;

                    float density = isTallGrass ? tallGrassDensity : shortGrassDensity;
                    float bladeHeight = isTallGrass ? tallBladeHeight : shortBladeHeight;

                    // Edge fade: check 8 neighbors for non-grass biomes
                    int grassNeighbors = 0;
                    int totalNeighbors = 0;
                    for (int dx = -2; dx <= 2; dx++)
                    {
                        for (int dy = -2; dy <= 2; dy++)
                        {
                            if (dx == 0 && dy == 0) continue;
                            int nx = px + dx;
                            int ny = py + dy;
                            if (nx < 0 || nx >= mapRes || ny < 0 || ny >= mapRes) continue;
                            totalNeighbors++;
                            int nMode = (int)(pixels[ny * mapRes + nx].a * 16.0f);
                            if (nMode == 0 || nMode == 13) grassNeighbors++;
                        }
                    }
                    float edgeFade = totalNeighbors > 0 ? (float)grassNeighbors / totalNeighbors : 1f;
                    edgeFade = edgeFade * edgeFade; // sharper falloff

                    float worldX = origin.x + (float)px / mapRes * sizeX;
                    float worldZ = origin.z + (float)py / mapRes * sizeZ;

                    int count = Mathf.RoundToInt(density);

                    for (int i = 0; i < count; i++)
                    {
                        float rx = worldX + Random.value;
                        float rz = worldZ + Random.value;

                        float terrainY = terrain.SampleHeight(new Vector3(rx, 0, rz));
                        terrainY += origin.y;

                        float relX = rx - origin.x;
                        float relZ = rz - origin.z;
                        int cx = Mathf.Clamp(Mathf.FloorToInt(relX / chunkSizeMeters), 0, chunksX - 1);
                        int cz = Mathf.Clamp(Mathf.FloorToInt(relZ / chunkSizeMeters), 0, chunksZ - 1);
                        int chunkIdx = cz * chunksX + cx;

                        float rot = Random.value * Mathf.PI * 2f;
                        float heightVar = Random.Range(0.7f, 1.1f);
                        float height = bladeHeight * heightVar * edgeFade;
                        float tint = Random.value;

                        float flower = 0f;
                        if (isShortGrass && Random.value < flowerChance)
                            flower = Mathf.Ceil(Random.value * 5f);

                        float cosR = Mathf.Cos(rot);
                        float sinR = Mathf.Sin(rot);

                        var verts = chunkData[chunkIdx];
                        var uvs = chunkUVs[chunkIdx];
                        var uv2s = chunkUV2s[chunkIdx];
                        var norms = chunkNormals[chunkIdx];
                        var tris = chunkTris[chunkIdx];
                        int vertOffset = chunkVertOffsets[chunkIdx];

                        for (int v = 0; v < 5; v++)
                        {
                            Vector3 lv = bladeVerts[v];
                            Vector3 scaled = new Vector3(lv.x, lv.y * height, lv.z);
                            Vector3 rotated = new Vector3(
                                scaled.x * cosR + scaled.z * sinR,
                                scaled.y,
                                -scaled.x * sinR + scaled.z * cosR
                            );
                            verts.Add(new Vector3(rx + rotated.x, terrainY + rotated.y, rz + rotated.z));
                            uvs.Add(bladeUVs[v]);
                            uv2s.Add(new Vector2(tint, flower));
                            norms.Add(Vector3.up);
                        }

                        for (int t = 0; t < bladeTris.Length; t++)
                        {
                            tris.Add(vertOffset + bladeTris[t]);
                        }

                        chunkVertOffsets[chunkIdx] += 5;
                        chunkBladeCounts[chunkIdx]++;
                        totalBlades++;
                        bladesSinceYield++;

                        if (bladesSinceYield >= 5000)
                        {
                            bladesSinceYield = 0;
                            yield return null;
                        }
                    }
                }
            }

            // Create a child container at origin so chunk world positions are correct
            // without modifying the parent (terrain) transform.
            chunkContainer = new GameObject("GrassChunks");
            chunkContainer.transform.SetParent(transform, false);
            chunkContainer.transform.position = Vector3.zero;
            chunkContainer.transform.rotation = Quaternion.identity;
            chunkContainer.transform.localScale = Vector3.one;

            // Create a GameObject + Mesh per chunk — yield after each
            int activeChunks = 0;
            for (int i = 0; i < totalChunks; i++)
            {
                if (chunkData[i].Count == 0) continue;

                int cx = i % chunksX;
                int cz = i / chunksX;

                var mesh = new Mesh
                {
                    name = $"GrassChunk_{cx}_{cz}",
                    indexFormat = UnityEngine.Rendering.IndexFormat.UInt32
                };
                mesh.SetVertices(chunkData[i]);
                mesh.SetUVs(0, chunkUVs[i]);
                mesh.SetUVs(1, chunkUV2s[i]);
                mesh.SetNormals(chunkNormals[i]);
                mesh.SetTriangles(chunkTris[i], 0);
                mesh.RecalculateBounds();

                var go = new GameObject($"GrassChunk_{cx}_{cz}");
                go.transform.SetParent(chunkContainer.transform, false);
                go.transform.position = Vector3.zero;
                go.transform.rotation = Quaternion.identity;
                go.transform.localScale = Vector3.one;

                var mf = go.AddComponent<MeshFilter>();
                mf.sharedMesh = mesh;

                var mr = go.AddComponent<MeshRenderer>();
                mr.sharedMaterial = grassMaterial;
                mr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
                mr.receiveShadows = false;

                chunkObjects.Add(go);
                chunkMeshes.Add(mesh);
                activeChunks++;

                yield return null;
            }

            Debug.Log($"[GrassRenderer] Built {activeChunks} chunks, {totalBlades} blades.");
            isGenerating = false;
        }

        void Update()
        {
            if (grassMaterial == null) return;

            // Update wind strength from global wind params
            Vector4 windParams = Shader.GetGlobalVector(GrassWindParamsId);
            if (windParams == Vector4.zero) windParams = new Vector4(1, 0, 0, 0.3f);
            grassMaterial.SetFloat("_WindStrength", windStrength * (0.5f + windParams.w * 0.5f));
        }
    }
}
