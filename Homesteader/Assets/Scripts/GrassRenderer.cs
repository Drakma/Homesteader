using System.Collections;
using UnityEngine;
using UnityEngine.Rendering;
using Homesteader.Generation;

namespace Homesteader.Grass
{
    /// <summary>
    /// GPU-instanced grass: a compute shader (GrassInstanceGen.compute) scatters blade instances into a
    /// GraphicsBuffer each time the player moves far enough, reading straight from the biome map and terrain
    /// heightmap textures - no CPU per-blade work, no baked Mesh, no chunk streaming. The whole visible region
    /// is drawn with a single Graphics.RenderMeshIndirect call every frame from that one buffer.
    ///
    /// This replaces the earlier CPU-baked-mesh-per-chunk approach, which streamed 25-50m chunks in/out around
    /// the player: correct in principle, but every new chunk still needed a real Mesh built and uploaded to
    /// the GPU in one atomic (non-yieldable) step, which was a recurring hitch while moving. Generating
    /// instances on the GPU has no such step - the "upload" is the compute dispatch itself.
    /// </summary>
    public class GrassRenderer : MonoBehaviour
    {
        [Header("Grass Density (blades per m²)")]
        [SerializeField] private float shortGrassDensity = 120f;
        [SerializeField] private float tallGrassDensity = 180f;

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

        [Header("GPU Region")]
        [Tooltip("The generated region is this many metres square, centred on the player.")]
        [SerializeField] private float regionSize = 140f;
        [Tooltip("Metres per grid cell fed into the compute shader (1 = same granularity as the biome map's own texel size).")]
        [SerializeField] private float cellSize = 1f;
        [Tooltip("Re-dispatch the compute shader once the player has moved this far from where the region was last generated.")]
        [SerializeField] private float regenerateMoveThreshold = 15f;
        [Tooltip("Seconds between checking whether it's time to regenerate - doesn't need per-frame precision.")]
        [SerializeField] private float regenerateCheckInterval = 0.25f;
        [Tooltip("Hard cap on instances a single grid cell can contribute, purely as a GPU buffer safety margin.")]
        [SerializeField] private int maxInstancesPerCell = 200;
        [Tooltip("Total instance buffer capacity. Sized for the worst case (region entirely tall grass at max density) with headroom; the buffer is fixed-size and reused, never reallocated per region.")]
        [SerializeField] private int instanceBufferCapacity = 4_000_000;

        private ComputeShader grassCompute;
        private int kernel;
        private int cullKernel;
        private Material grassMaterial;
        private Mesh bladeMesh;
        private GraphicsBuffer instanceBuffer;    // every instance generated for the region (source of truth)
        private GraphicsBuffer visibleInstanceBuffer; // subset that passed the frustum cull - what's actually drawn
        private GraphicsBuffer argsBuffer;
        private GraphicsBuffer countReadBuffer;   // 1-uint scratch buffer for reading instanceBuffer's count back to the CPU
        private RenderParams renderParams;
        private int totalGeneratedCount;
        private readonly Vector4[] frustumPlanesScratch = new Vector4[6];
        private readonly Plane[] frustumPlanesScratchSrc = new Plane[6];

        private HomesteaderTerrainGenerator terrainGen;
        private Terrain terrain;
        private Transform player;

        private bool isGenerating;
        public bool IsGenerating => isGenerating;

        /// <summary>Debug/verification helper: reads back how many blade instances the last compute dispatch
        /// produced. Involves a GPU readback (stalls until the GPU catches up) - never call this every frame.</summary>
        public int DebugReadInstanceCount()
        {
            if (argsBuffer == null) return -1;
            var data = new GraphicsBuffer.IndirectDrawIndexedArgs[1];
            argsBuffer.GetData(data);
            return (int)data[0].instanceCount;
        }
        private bool ready;
        private float nextRebuildAttempt;

        private bool BuffersUsable() =>
            grassCompute != null && grassMaterial != null && bladeMesh != null
            && instanceBuffer != null && instanceBuffer.IsValid()
            && visibleInstanceBuffer != null && visibleInstanceBuffer.IsValid()
            && argsBuffer != null && argsBuffer.IsValid()
            && countReadBuffer != null && countReadBuffer.IsValid();
        private Vector3 lastGenCenter = new Vector3(float.MaxValue, 0f, float.MaxValue);
        private float nextRegenCheck;

        private static readonly int GrassWindParamsId = Shader.PropertyToID("_GrassWindParams");

        void OnEnable()
        {
            if (!ready && Application.isPlaying)
            {
                var gen = FindObjectOfType<HomesteaderTerrainGenerator>();
                if (gen != null && gen.GetBakedBiomeMap() != null && !gen.IsGenerating)
                {
                    StartCoroutine(InitializeAsync());
                }
            }
        }

        void OnDestroy()
        {
            ReleaseAll();
        }

        void ReleaseAll()
        {
            instanceBuffer?.Dispose();
            instanceBuffer = null;
            visibleInstanceBuffer?.Dispose();
            visibleInstanceBuffer = null;
            argsBuffer?.Dispose();
            argsBuffer = null;
            countReadBuffer?.Dispose();
            countReadBuffer = null;
            totalGeneratedCount = 0;
            if (grassMaterial != null) Destroy(grassMaterial);
            grassMaterial = null;
            if (bladeMesh != null) Destroy(bladeMesh);
            bladeMesh = null;
            ready = false;
            lastGenCenter = new Vector3(float.MaxValue, 0f, float.MaxValue);
        }

        public void Regenerate()
        {
            if (isGenerating) StopAllCoroutines();
            ReleaseAll();
            StartCoroutine(InitializeAsync());
        }

        private static Mesh BuildBladeMesh(float widthUnused)
        {
            // Unit blade in local space: x spans [-1,1] (scaled by half the blade width in the shader), y spans
            // [0,1] bottom-to-tip. The vertex shader scales/rotates/translates this per instance.
            var mesh = new Mesh { name = "GrassBladeGpu" };
            Vector3[] verts =
            {
                new Vector3(-1f, 0f, 0f), new Vector3(1f, 0f, 0f),
                new Vector3(-0.7f, 0.5f, 0f), new Vector3(0.7f, 0.5f, 0f),
                new Vector3(0f, 1f, 0f),
            };
            Vector3[] normals = { Vector3.up, Vector3.up, Vector3.up, Vector3.up, Vector3.up };
            Vector2[] uvs =
            {
                new Vector2(0, 0), new Vector2(1, 0),
                new Vector2(0, 0.5f), new Vector2(1, 0.5f),
                new Vector2(0.5f, 1),
            };
            int[] tris = { 0, 2, 1, 1, 2, 3, 2, 4, 3, 1, 2, 0, 3, 2, 1, 3, 4, 2 };
            mesh.vertices = verts;
            mesh.normals = normals;
            mesh.uv = uvs;
            mesh.triangles = tris;
            mesh.RecalculateBounds();
            return mesh;
        }

        private void ResolvePlayer()
        {
            if (player != null) return;
            var p = GameObject.FindWithTag("Player");
            if (p != null) player = p.transform;
        }

        IEnumerator InitializeAsync()
        {
            isGenerating = true;

            terrainGen = FindObjectOfType<HomesteaderTerrainGenerator>();
            if (terrainGen == null) { isGenerating = false; yield break; }
            terrain = terrainGen.GetComponent<Terrain>();
            if (terrain == null) { isGenerating = false; yield break; }

            Texture2D biomeMap = terrainGen.GetBakedBiomeMap();
            if (biomeMap == null) { isGenerating = false; yield break; }

            grassCompute = Resources.Load<ComputeShader>("Compute/GrassInstanceGen");
            if (grassCompute == null)
            {
                Debug.LogError("[GrassRenderer] GrassInstanceGen compute shader not found in Resources/Compute.");
                isGenerating = false;
                yield break;
            }
            kernel = grassCompute.FindKernel("CSGenerate");
            cullKernel = grassCompute.FindKernel("CSCull");

            Shader gpuShader = Shader.Find("Homesteader/GrassGpu");
            if (gpuShader == null)
            {
                Debug.LogError("[GrassRenderer] GrassGpu shader not found!");
                isGenerating = false;
                yield break;
            }
            grassMaterial = new Material(gpuShader) { hideFlags = HideFlags.HideAndDontSave };
            grassMaterial.SetColor("_BaseColor", baseColor);
            grassMaterial.SetColor("_TipColor", tipColor);

            bladeMesh = BuildBladeMesh(bladeWidth);

            const int instanceStrideBytes = 8 * 4; // float3 position + rotationY + height + tint + flower + pad
            instanceBuffer = new GraphicsBuffer(GraphicsBuffer.Target.Append,
                instanceBufferCapacity, instanceStrideBytes);
            // Same capacity as instanceBuffer: worst case (camera can see the whole generated region) every
            // instance passes the cull, so this has to be able to hold all of them too.
            visibleInstanceBuffer = new GraphicsBuffer(GraphicsBuffer.Target.Append,
                instanceBufferCapacity, instanceStrideBytes);
            countReadBuffer = new GraphicsBuffer(GraphicsBuffer.Target.Raw, 1, 4);
            argsBuffer = new GraphicsBuffer(GraphicsBuffer.Target.IndirectArguments, 1,
                GraphicsBuffer.IndirectDrawIndexedArgs.size);
            argsBuffer.SetData(new[]
            {
                new GraphicsBuffer.IndirectDrawIndexedArgs
                {
                    indexCountPerInstance = bladeMesh.GetIndexCount(0),
                    instanceCount = 0,
                    startIndex = 0,
                    baseVertexIndex = 0,
                    startInstance = 0,
                }
            });

            // The render draws only the CULLED list - see CSCull in GrassInstanceGen.compute and DispatchCull()
            // below. Drawing straight from instanceBuffer (every generated instance, unconditionally) was the
            // original version and is what cost the extra frame time: nothing outside the camera's view was
            // ever excluded from the draw.
            grassMaterial.SetBuffer("_Instances", visibleInstanceBuffer);

            renderParams = new RenderParams(grassMaterial)
            {
                worldBounds = new Bounds(Vector3.zero, Vector3.one * 100000f), // recomputed properly once terrain is known, see below
                shadowCastingMode = ShadowCastingMode.Off,
                receiveShadows = false,
            };

            grassCompute.SetTexture(kernel, "_BiomeMap", biomeMap);
            grassCompute.SetTexture(kernel, "_Heightmap", terrain.terrainData.heightmapTexture);
            grassCompute.SetVector("_TerrainOrigin", terrain.transform.position);
            grassCompute.SetVector("_TerrainSize", new Vector2(terrain.terrainData.size.x, terrain.terrainData.size.z));
            grassCompute.SetFloat("_TerrainHeightScale", terrain.terrainData.size.y);
            grassCompute.SetFloat("_ShortDensity", shortGrassDensity);
            grassCompute.SetFloat("_TallDensity", tallGrassDensity);
            grassCompute.SetFloat("_ShortBladeHeight", shortBladeHeight);
            grassCompute.SetFloat("_TallBladeHeight", tallBladeHeight);
            grassCompute.SetFloat("_FlowerChance", flowerChance);
            grassCompute.SetInt("_MaxInstancesPerCell", maxInstancesPerCell);
            grassCompute.SetFloat("_CellSize", cellSize);

            Vector3 terrainOrigin = terrain.transform.position;
            var terrainSize = terrain.terrainData.size;
            renderParams.worldBounds = new Bounds(
                terrainOrigin + new Vector3(terrainSize.x, terrainSize.y, terrainSize.z) * 0.5f,
                new Vector3(terrainSize.x, terrainSize.y + 4f, terrainSize.z));

            yield return null;
            ResolvePlayer();
            Vector3 startPos = player != null ? player.position : terrainOrigin + new Vector3(terrainSize.x * 0.5f, 0f, terrainSize.z * 0.5f);
            DispatchRegenerate(startPos);

            ready = true;
            isGenerating = false;
        }

        private void DispatchRegenerate(Vector3 centerWorldPos)
        {
            int gridDim = Mathf.CeilToInt(regionSize / cellSize);
            // Snap the region origin to a fixed world lattice (multiples of cellSize) instead of centering
            // exactly on the player's continuous position: every regenerate (every ~15m moved) otherwise
            // recomputed the sample grid from a slightly different fractional offset, so a blade at the same
            // world spot got resampled at a slightly different position each time - a visible shift/jitter in
            // the grass carpet as you walked. Snapping keeps the same lattice points across regenerations;
            // only which cells fall inside the region (its extent) changes.
            float rawOriginX = centerWorldPos.x - regionSize * 0.5f;
            float rawOriginZ = centerWorldPos.z - regionSize * 0.5f;
            Vector2 regionOrigin = new Vector2(
                Mathf.Floor(rawOriginX / cellSize) * cellSize,
                Mathf.Floor(rawOriginZ / cellSize) * cellSize);

            instanceBuffer.SetCounterValue(0);
            grassCompute.SetVector("_RegionOrigin", regionOrigin);
            grassCompute.SetFloat("_RegionSize", regionSize);
            grassCompute.SetInt("_GridDim", gridDim);
            grassCompute.SetBuffer(kernel, "_Instances", instanceBuffer);

            int groups = Mathf.CeilToInt(gridDim / 8f);
            grassCompute.Dispatch(kernel, groups, groups, 1);

            // How many instances actually exist now, so DispatchCull (every frame) knows how many threads to
            // check. This is a real CPU/GPU sync stall (GetData blocks until the GPU finishes) - fine here
            // since regeneration only happens once every regenerateMoveThreshold metres of movement, not
            // every frame. A per-frame stall would be a real problem; this occasional one isn't.
            GraphicsBuffer.CopyCount(instanceBuffer, countReadBuffer, 0);
            var countData = new uint[1];
            countReadBuffer.GetData(countData);
            totalGeneratedCount = (int)countData[0];

            lastGenCenter = centerWorldPos;
        }

        /// <summary>Every frame: cull the full generated instance set (instanceBuffer) against the camera
        /// frustum into visibleInstanceBuffer, which is what the draw call actually reads. Cheap even at
        /// ~1M+ source instances - a compute pass over that many is far less work than shading them all.</summary>
        private void DispatchCull(Camera cam)
        {
            if (!BuffersUsable()) return;
            if (cam == null || totalGeneratedCount <= 0)
            {
                GraphicsBuffer.CopyCount(visibleInstanceBuffer, argsBuffer, 4);
                return;
            }

            GeometryUtility.CalculateFrustumPlanes(cam, frustumPlanesScratchSrc);
            for (int i = 0; i < 6; i++)
            {
                Plane p = frustumPlanesScratchSrc[i];
                frustumPlanesScratch[i] = new Vector4(p.normal.x, p.normal.y, p.normal.z, p.distance);
            }

            visibleInstanceBuffer.SetCounterValue(0);
            grassCompute.SetVectorArray("_FrustumPlanes", frustumPlanesScratch);
            grassCompute.SetInt("_TotalCount", totalGeneratedCount);
            grassCompute.SetBuffer(cullKernel, "_Source", instanceBuffer);
            grassCompute.SetBuffer(cullKernel, "_Visible", visibleInstanceBuffer);

            int groups = Mathf.CeilToInt(totalGeneratedCount / 64f);
            grassCompute.Dispatch(cullKernel, groups, 1, 1);

            GraphicsBuffer.CopyCount(visibleInstanceBuffer, argsBuffer, 4);
        }

        void Update()
        {
            if (grassMaterial != null)
            {
                Vector4 windParams = Shader.GetGlobalVector(GrassWindParamsId);
                if (windParams == Vector4.zero) windParams = new Vector4(1, 0, 0, 0.3f);
                grassMaterial.SetFloat("_WindStrength", Homesteader.UI.GraphicsOptions.WindAnimationOn() ? windStrength * (0.5f + windParams.w * 0.5f) : 0f);
            }

            if (!ready || isGenerating) return;

            /*
              SELF-HEAL WHEN THE BUFFERS ARE GONE. `ready` can be true while the GPU buffers are null or already
              disposed - a regeneration or teardown that released them while an earlier initialisation was still
              finishing and set `ready` afterwards. DispatchCull then threw a NullReferenceException on EVERY
              frame (hundreds of errors a minute) and nothing was drawn. Drop out of the ready state and rebuild
              instead, at most once a second so a persistent failure cannot spin.
            */
            if (!BuffersUsable())
            {
                ready = false;
                if (Time.unscaledTime >= nextRebuildAttempt)
                {
                    nextRebuildAttempt = Time.unscaledTime + 1f;
                    Debug.LogWarning("[GrassRenderer] GPU buffers were released while marked ready - rebuilding.");
                    Regenerate();
                }
                return;
            }

            if (Time.unscaledTime >= nextRegenCheck)
            {
                nextRegenCheck = Time.unscaledTime + regenerateCheckInterval;
                ResolvePlayer();
                if (player != null)
                {
                    float dx = player.position.x - lastGenCenter.x, dz = player.position.z - lastGenCenter.z;
                    if (dx * dx + dz * dz > regenerateMoveThreshold * regenerateMoveThreshold)
                        DispatchRegenerate(player.position);
                }
            }

            DispatchCull(Camera.main);

            if (bladeMesh != null && argsBuffer != null)
                Graphics.RenderMeshIndirect(renderParams, bladeMesh, argsBuffer);
        }
    }
}
