using System.Collections.Generic;
using System.IO;
using UnityEngine;

namespace Homesteader.Modding
{
    /// <summary>
    /// Turns a parsed OBJ into a runtime GameObject.
    ///
    /// This is the fallback path for mods that ship plain .obj geometry instead of
    /// FBX. It exists because OBJ is text and can be parsed while the game runs,
    /// whereas an FBX must go through Unity's editor importer.
    ///
    /// Meshes are built once and cached by model path, so spawning a thousand
    /// trees shares one mesh rather than allocating a thousand.
    /// </summary>
    public static class ObjPrefabBuilder
    {
        private static readonly Dictionary<string, GameObject> cache =
            new Dictionary<string, GameObject>();

        /// <summary>
        /// Builds (or returns a cached) prefab for a parsed OBJ. Materials are
        /// resolved from the sibling .mtl when present, falling back to the
        /// project atlas by name, and finally to an unlit default so the mesh is
        /// always visible rather than invisible.
        /// </summary>
        public static GameObject Build(string modelName, ObjMeshParser.ParsedObj parsed, string objPath)
        {
            if (parsed == null || !parsed.HasGeometry)
                return null;

            string key = objPath ?? modelName;
            if (cache.TryGetValue(key, out GameObject cachedPrefab) && cachedPrefab != null)
                return cachedPrefab;

            var root = new GameObject(Path.GetFileNameWithoutExtension(modelName));

            // Resolve the MTL once for the whole model.
            Dictionary<string, Material> materials = MtlParser.LoadFor(objPath);

            // Each sub-mesh (one per usemtl group) becomes its own child object so
            // one OBJ can carry several materials.
            int index = 0;
            foreach (ObjMeshParser.SubMesh sub in parsed.SubMeshes)
            {
                Mesh mesh = ToMesh(sub, $"{root.name}_mesh{index}");
                if (mesh == null) continue;

                var child = new GameObject(
                    string.IsNullOrEmpty(sub.MaterialName) ? $"part{index}" : sub.MaterialName);
                child.transform.SetParent(root.transform, false);

                child.AddComponent<MeshFilter>().sharedMesh = mesh;
                var renderer = child.AddComponent<MeshRenderer>();

                Material mat = ResolveMaterial(sub.MaterialName, materials);
                if (mat != null)
                    renderer.sharedMaterial = mat;

                renderer.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.On;
                renderer.receiveShadows = true;

                child.AddComponent<MeshCollider>().sharedMesh = mesh;
                index++;
            }

            if (root.transform.childCount == 0)
            {
                Object.Destroy(root);
                return null;
            }

            cache[key] = root;
            return root;
        }

        /// <summary>Converts a parsed sub-mesh into a Unity Mesh.</summary>
        private static Mesh ToMesh(ObjMeshParser.SubMesh sub, string name)
        {
            if (sub.Vertices.Count == 0 || sub.Triangles.Count == 0)
                return null;

            var mesh = new Mesh { name = name };

            // 65k+ vertices needs a 32-bit index buffer.
            if (sub.Vertices.Count > 65000)
                mesh.indexFormat = UnityEngine.Rendering.IndexFormat.UInt32;

            mesh.SetVertices(sub.Vertices);
            mesh.SetTriangles(sub.Triangles, 0);

            if (sub.Uvs.Count == sub.Vertices.Count)
                mesh.SetUVs(0, sub.Uvs);

            if (sub.Normals.Count == sub.Vertices.Count)
                mesh.SetNormals(sub.Normals);
            else
                mesh.RecalculateNormals();

            mesh.RecalculateBounds();
            // Trees are lit scenery; tangents keep normal maps working.
            mesh.RecalculateTangents();

            return mesh;
        }

        private static Material ResolveMaterial(string name, Dictionary<string, Material> fromMtl)
        {
            if (!string.IsNullOrEmpty(name) && fromMtl != null &&
                fromMtl.TryGetValue(name, out Material mat) && mat != null)
            {
                return mat;
            }

            // Name-free fallback: a shared default so geometry is never invisible.
            return DefaultMaterial();
        }

        private static Material defaultMaterial;

        private static Material DefaultMaterial()
        {
            if (defaultMaterial != null)
                return defaultMaterial;

            // The project ships a palette material; prefer it so runtime-built
            // meshes match the rest of the art direction.
            defaultMaterial = Resources.Load<Material>("M_Homesteader_Palette");
            if (defaultMaterial != null)
                return defaultMaterial;

            Shader shader = Shader.Find("Universal Render Pipeline/Lit")
                            ?? Shader.Find("Standard")
                            ?? Shader.Find("Unlit/Texture");

            if (shader != null)
            {
                defaultMaterial = new Material(shader) { name = "ModFallback" };
                // Slight desaturation so an untextured mod model reads as a
                // placeholder rather than a finished asset.
                if (defaultMaterial.HasProperty("_BaseColor"))
                    defaultMaterial.SetColor("_BaseColor", new Color(0.78f, 0.76f, 0.72f, 1f));
                else if (defaultMaterial.HasProperty("_Color"))
                    defaultMaterial.color = new Color(0.78f, 0.76f, 0.72f, 1f);
            }

            return defaultMaterial;
        }

        /// <summary>Clears the mesh cache (used when reloading mods).</summary>
        public static void ClearCache()
        {
            cache.Clear();
            defaultMaterial = null;
        }
    }
}
