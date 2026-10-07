using UnityEngine;
using UnityEngine.Rendering;

namespace Homesteader.World
{
    /// <summary>
    /// Renders the terrain's procedural ground colour (the biome textures, their soft blend and the water bed, all pure noise of the world position)
    /// ONCE into a texture when the world is made, so the lit terrain shader reads one texel per pixel instead of running dozens of noise calls per pixel
    /// every frame. Weather, snow, roads, cliffs, light, shadows and the grid stay live in the shader on top of it.
    ///
    /// The shader's GroundBake pass draws a full-screen triangle into the texture; the shader writes TerrainGroundBase for each texel's world position.
    /// Until the bake exists (or if it fails) the shader falls back to computing the same thing per pixel, so the ground never goes missing.
    /// </summary>
    public static class TerrainGroundBake
    {
        /// <summary>Texels along each side of the map. 4096 over a 500 m map is about 8 texels per metre.</summary>
        public const int Resolution = 4096;
        private const int StripRows = 256;   // drawn a strip at a time so no single draw runs long enough for the driver to give up on it

        private static RenderTexture s_rt;
        private static readonly int BakeId = Shader.PropertyToID("_GroundBake");
        private static readonly int OnId = Shader.PropertyToID("_GroundBakeOn");
        private static readonly int SizeId = Shader.PropertyToID("_BakeSize");
        private static readonly int BlendId = Shader.PropertyToID("_TerrainBlendQuality");

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
        private static void Reset()
        {
            // Enter Play Mode keeps statics: forget the last play's texture, and switch the shader back to computing the ground itself.
            s_rt = null;
            Shader.SetGlobalFloat(OnId, 0f);
        }

        /// <summary>True when a baked ground texture is in use.</summary>
        public static bool Ready => s_rt != null && s_rt.IsCreated();

        /// <summary>Renders the ground again inside a rectangle only (0..1 of the map on each side), after the biome map changed there (tilled farmland).</summary>
        public static void Rebake(Material terrainMaterial, float u0, float v0, float u1, float v1)
        {
            if (!Ready || terrainMaterial == null) return;
            int pass = terrainMaterial.FindPass("GroundBake");
            if (pass < 0) return;
            int x0 = Mathf.Clamp(Mathf.FloorToInt(u0 * Resolution), 0, Resolution - 1);
            int x1 = Mathf.Clamp(Mathf.CeilToInt(u1 * Resolution), x0 + 1, Resolution);
            int y0 = Mathf.Clamp(Mathf.FloorToInt(v0 * Resolution), 0, Resolution - 1);
            int y1 = Mathf.Clamp(Mathf.CeilToInt(v1 * Resolution), y0 + 1, Resolution);

            float oldBlend = Shader.GetGlobalFloat(BlendId);
            Shader.SetGlobalFloat(BlendId, 1f);
            terrainMaterial.SetVector(SizeId, new Vector4(Resolution, Resolution, 0f, 0f));
            Shader.SetGlobalVector(SizeId, new Vector4(Resolution, Resolution, 0f, 0f));
            var cmd = new CommandBuffer { name = "TerrainGroundRebake" };
            cmd.SetRenderTarget(s_rt);
            cmd.SetViewport(new Rect(x0, y0, x1 - x0, y1 - y0));
            cmd.DrawProcedural(Matrix4x4.identity, terrainMaterial, pass, MeshTopology.Triangles, 3);
            Graphics.ExecuteCommandBuffer(cmd);
            cmd.Release();
            s_rt.GenerateMips();
            Shader.SetGlobalFloat(BlendId, oldBlend);
        }

        /// <summary>Renders the ground of the terrain that <paramref name="terrainMaterial"/> draws (its biome map, water mask and bounds must already be set).</summary>
        public static void Bake(Material terrainMaterial)
        {
            Shader.SetGlobalFloat(OnId, 0f);   // draw the live ground until the texture is complete
            if (terrainMaterial == null) return;
            int pass = terrainMaterial.FindPass("GroundBake");
            if (pass < 0) { Debug.LogWarning("[GroundBake] the terrain shader has no GroundBake pass; the ground stays per-pixel."); return; }

            if (s_rt != null) { s_rt.Release(); Object.Destroy(s_rt); s_rt = null; }
            // Linear + 8 bit: the colours are stored exactly as the shader makes them and read back the same way, whatever the project's colour space.
            var rt = new RenderTexture(Resolution, Resolution, 0, RenderTextureFormat.ARGB32, RenderTextureReadWrite.Linear)
            {
                name = "TerrainGroundBake",
                useMipMap = true,
                autoGenerateMips = false,
                filterMode = FilterMode.Trilinear,
                anisoLevel = 8,
                wrapMode = TextureWrapMode.Clamp,
            };
            if (!rt.Create()) { Debug.LogWarning("[GroundBake] could not create the " + Resolution + " px texture; the ground stays per-pixel."); Object.Destroy(rt); return; }

            float oldBlend = Shader.GetGlobalFloat(BlendId);
            Shader.SetGlobalFloat(BlendId, 1f);   // the soft biome blend always: it costs nothing once baked
            terrainMaterial.SetVector(SizeId, new Vector4(Resolution, Resolution, 0f, 0f));
            Shader.SetGlobalVector(SizeId, new Vector4(Resolution, Resolution, 0f, 0f));

            var cmd = new CommandBuffer { name = "TerrainGroundBake" };
            for (int y = 0; y < Resolution; y += StripRows)
            {
                cmd.Clear();
                cmd.SetRenderTarget(rt);
                cmd.SetViewport(new Rect(0f, y, Resolution, Mathf.Min(StripRows, Resolution - y)));
                cmd.DrawProcedural(Matrix4x4.identity, terrainMaterial, pass, MeshTopology.Triangles, 3);
                Graphics.ExecuteCommandBuffer(cmd);
            }
            cmd.Release();
            rt.GenerateMips();

            Shader.SetGlobalFloat(BlendId, oldBlend);
            s_rt = rt;
            Shader.SetGlobalTexture(BakeId, rt);
            Shader.SetGlobalFloat(OnId, 1f);
        }
    }
}
