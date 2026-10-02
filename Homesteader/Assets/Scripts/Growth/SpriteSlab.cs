using System.Collections.Generic;
using UnityEngine;

namespace Homesteader.Growth
{
    /// <summary>
    /// Turns an item icon into a real, lit 3D object: the icon's opaque pixels are extruded into a thin slab (the icon is the
    /// texture on both faces, the pixel edges become the sides). Used where an item has no model: a tool in the hand,
    /// an item lying on the ground. Built once per item id and cached.
    /// </summary>
    public static class SpriteSlab
    {
        private const int Grid = 64;             // icon is sampled down to this many pixels square (keeps the mesh small)
        private const float AlphaCutoff = 0.4f;

        private sealed class Built
        {
            public Mesh Mesh;
            public Material Material;
        }

        private static readonly Dictionary<string, Built> Cache = new Dictionary<string, Built>();

        /// <summary>A slab object for an item icon, <paramref name="height"/> metres tall (its long side), centred on its middle,
        /// standing upright (face toward -Z). Null if the item has no icon.</summary>
        public static GameObject Create(string itemId, float height, float thickness = 0.025f)
        {
            if (!TryBuild(itemId, out Built built)) return null;

            var go = new GameObject("Slab_" + itemId);
            go.AddComponent<MeshFilter>().sharedMesh = built.Mesh;
            var mr = go.AddComponent<MeshRenderer>();
            mr.sharedMaterial = built.Material;
            mr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.On;
            go.transform.localScale = new Vector3(height, height, thickness / 1f);   // mesh is 1 x 1 x 1 (thickness along z)
            return go;
        }

        private static bool TryBuild(string itemId, out Built built)
        {
            if (Cache.TryGetValue(itemId, out built) && built != null && built.Mesh != null) return true;
            built = null;

            Texture2D icon = Homesteader.UI.PhoneController.GetItemIcon(itemId + ".png", itemId);
            if (icon == null) return false;

            Color32[] px = ReadPixels(icon, Grid);
            Mesh mesh = Extrude(px, Grid);
            if (mesh == null) return false;

            Shader shader = Shader.Find("Universal Render Pipeline/Lit") ?? Shader.Find("Standard");
            var mat = new Material(shader) { name = "Slab_" + itemId, hideFlags = HideFlags.DontSave };
            if (mat.HasProperty("_BaseMap")) mat.SetTexture("_BaseMap", icon);
            if (mat.HasProperty("_MainTex")) mat.SetTexture("_MainTex", icon);
            if (mat.HasProperty("_BaseColor")) mat.SetColor("_BaseColor", Color.white);
            if (mat.HasProperty("_Smoothness")) mat.SetFloat("_Smoothness", 0.15f);

            built = new Built { Mesh = mesh, Material = mat };
            Cache[itemId] = built;
            return true;
        }

        /// <summary>Reads a texture's pixels at a smaller size, whether or not the texture is CPU-readable.</summary>
        private static Color32[] ReadPixels(Texture2D src, int size)
        {
            RenderTexture rt = RenderTexture.GetTemporary(size, size, 0, RenderTextureFormat.ARGB32);
            RenderTexture prev = RenderTexture.active;
            Graphics.Blit(src, rt);
            RenderTexture.active = rt;
            var tmp = new Texture2D(size, size, TextureFormat.RGBA32, false);
            tmp.ReadPixels(new Rect(0, 0, size, size), 0, 0);
            tmp.Apply();
            RenderTexture.active = prev;
            RenderTexture.ReleaseTemporary(rt);
            Color32[] result = tmp.GetPixels32();
            Object.Destroy(tmp);
            return result;
        }

        private static Mesh Extrude(Color32[] px, int n)
        {
            bool Solid(int x, int y) => x >= 0 && y >= 0 && x < n && y < n && px[y * n + x].a >= AlphaCutoff * 255f;

            var v = new List<Vector3>();
            var uv = new List<Vector2>();
            var nrm = new List<Vector3>();
            var tri = new List<int>();
            float cell = 1f / n;
            const float half = 0.5f;   // z from -0.5 to +0.5 (scaled to the thickness by the caller)

            void Quad(Vector3 a, Vector3 b, Vector3 c, Vector3 d, Vector2 uvA, Vector2 uvC, Vector3 normal)
            {
                int k = v.Count;
                v.Add(a); v.Add(b); v.Add(c); v.Add(d);
                uv.Add(new Vector2(uvA.x, uvA.y)); uv.Add(new Vector2(uvC.x, uvA.y)); uv.Add(new Vector2(uvC.x, uvC.y)); uv.Add(new Vector2(uvA.x, uvC.y));
                for (int i = 0; i < 4; i++) nrm.Add(normal);
                // Unity's front face is the one whose normal is cross(b - a, c - a): wind each quad to match its stated normal.
                if (Vector3.Dot(Vector3.Cross(b - a, c - a), normal) >= 0f)
                { tri.Add(k); tri.Add(k + 1); tri.Add(k + 2); tri.Add(k); tri.Add(k + 2); tri.Add(k + 3); }
                else
                { tri.Add(k); tri.Add(k + 2); tri.Add(k + 1); tri.Add(k); tri.Add(k + 3); tri.Add(k + 2); }
            }

            for (int y = 0; y < n; y++)
            {
                int x = 0;
                while (x < n)
                {
                    if (!Solid(x, y)) { x++; continue; }
                    int x0 = x;
                    while (x < n && Solid(x, y)) x++;
                    // Front and back faces: one quad per horizontal run.
                    float l = x0 * cell - half, r = x * cell - half, b = y * cell - half, t = (y + 1) * cell - half;
                    Vector2 uvLo = new Vector2(x0 * cell, y * cell), uvHi = new Vector2(x * cell, (y + 1) * cell);
                    Quad(new Vector3(l, b, -half), new Vector3(r, b, -half), new Vector3(r, t, -half), new Vector3(l, t, -half), uvLo, uvHi, Vector3.back);
                    Quad(new Vector3(r, b, half), new Vector3(l, b, half), new Vector3(l, t, half), new Vector3(r, t, half), new Vector2(uvHi.x, uvLo.y), new Vector2(uvLo.x, uvHi.y), Vector3.forward);
                }
            }

            // Sides: a wall wherever a solid pixel meets an empty one, textured with that pixel's own colour.
            for (int y = 0; y < n; y++)
            {
                for (int x = 0; x < n; x++)
                {
                    if (!Solid(x, y)) continue;
                    float l = x * cell - half, r = (x + 1) * cell - half, b = y * cell - half, t = (y + 1) * cell - half;
                    Vector2 c0 = new Vector2((x + 0.5f) * cell, (y + 0.5f) * cell);
                    if (!Solid(x - 1, y)) Quad(new Vector3(l, b, half), new Vector3(l, b, -half), new Vector3(l, t, -half), new Vector3(l, t, half), c0, c0, Vector3.left);
                    if (!Solid(x + 1, y)) Quad(new Vector3(r, b, -half), new Vector3(r, b, half), new Vector3(r, t, half), new Vector3(r, t, -half), c0, c0, Vector3.right);
                    if (!Solid(x, y - 1)) Quad(new Vector3(l, b, half), new Vector3(r, b, half), new Vector3(r, b, -half), new Vector3(l, b, -half), c0, c0, Vector3.down);
                    if (!Solid(x, y + 1)) Quad(new Vector3(l, t, -half), new Vector3(r, t, -half), new Vector3(r, t, half), new Vector3(l, t, half), c0, c0, Vector3.up);
                }
            }

            if (v.Count == 0) return null;
            var mesh = new Mesh { name = "SpriteSlab", indexFormat = v.Count > 60000 ? UnityEngine.Rendering.IndexFormat.UInt32 : UnityEngine.Rendering.IndexFormat.UInt16 };
            mesh.SetVertices(v);
            mesh.SetUVs(0, uv);
            mesh.SetNormals(nrm);
            mesh.SetTriangles(tri, 0);
            mesh.RecalculateBounds();
            return mesh;
        }
    }
}
