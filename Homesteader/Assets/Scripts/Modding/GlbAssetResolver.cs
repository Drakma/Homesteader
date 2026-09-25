using System;
using System.Collections.Generic;
using System.IO;
using GLTFast;
using UnityEngine;

namespace Homesteader.Modding
{
    /// <summary>
    /// A mod model that is loaded from a .glb file at RUNTIME (glTFast), no editor import or prefab
    /// step needed, so a mod installed as a folder or zip brings its own models. This component sits
    /// on an inactive template object; consumers ask it to load and Instantiate the template once
    /// <see cref="Ready"/> is true.
    /// </summary>
    public sealed class GlbTemplate : MonoBehaviour
    {
        public string Path;
        public bool Solid = true;          // false for walk-through models (crops)
        public bool Ready { get; private set; }
        public bool Failed { get; private set; }
        private bool loading;

        /// <summary>Raised once when the load finishes (successfully or not).</summary>
        public event Action Loaded;

        /// <summary>Starts loading the file (once). Cheap to call every frame.</summary>
        public async void EnsureLoading()
        {
            if (loading || Ready || Failed) return;
            loading = true;
            try
            {
                var gltf = new GltfImport();
                bool ok = await gltf.Load(File.ReadAllBytes(Path), new Uri(Path));
                if (ok && this != null)
                    ok = await gltf.InstantiateMainSceneAsync(transform);
                if (!ok || this == null)
                {
                    Failed = true;
                    Debug.LogWarning($"[Mods] Could not load GLB '{Path}'.");
                    Loaded?.Invoke();
                    return;
                }

                GroundToOrigin();
                if (Solid)
                    foreach (MeshFilter mf in GetComponentsInChildren<MeshFilter>(true))
                        if (mf.sharedMesh != null && mf.GetComponent<Collider>() == null)
                            mf.gameObject.AddComponent<MeshCollider>().sharedMesh = mf.sharedMesh;
                Ready = true;
                Loaded?.Invoke();
            }
            catch (Exception e)
            {
                Failed = true;
                Debug.LogWarning($"[Mods] GLB '{Path}' failed to load: {e.Message}");
                Loaded?.Invoke();
            }
        }

        /// <summary>Shifts the loaded model up so its lowest point sits at y = 0 (ground pivot).</summary>
        private void GroundToOrigin()
        {
            float minY = float.MaxValue;
            foreach (MeshFilter mf in GetComponentsInChildren<MeshFilter>(true))
            {
                if (mf.sharedMesh == null) continue;
                Bounds b = mf.sharedMesh.bounds;
                Matrix4x4 m = mf.transform.localToWorldMatrix;
                for (int i = 0; i < 8; i++)
                {
                    Vector3 c = b.center + Vector3.Scale(b.extents, new Vector3((i & 1) == 0 ? -1 : 1, (i & 2) == 0 ? -1 : 1, (i & 4) == 0 ? -1 : 1));
                    minY = Mathf.Min(minY, m.MultiplyPoint3x4(c).y);
                }
            }
            if (minY == float.MaxValue || Mathf.Abs(minY) < 0.001f) return;
            for (int i = 0; i < transform.childCount; i++)
                transform.GetChild(i).position -= new Vector3(0f, minY, 0f);
        }
    }

    /// <summary>
    /// Resolves a mod asset whose manifest lists a .glb model to a lazily-loaded template
    /// (<see cref="GlbTemplate"/>). Nothing is read from disk until something asks the template to
    /// load, so registering hundreds of assets costs nothing. GLB is the project's default model
    /// format; anything without a GLB falls through to the next resolver.
    /// </summary>
    public sealed class GlbAssetResolver : IModAssetResolver
    {
        private readonly Dictionary<string, GameObject> cache = new Dictionary<string, GameObject>(StringComparer.OrdinalIgnoreCase);
        private readonly Dictionary<string, Dictionary<string, string>> fileIndex =
            new Dictionary<string, Dictionary<string, string>>(StringComparer.OrdinalIgnoreCase);
        private Transform holder;

        public bool TryResolvePrefab(ModInfo mod, ModJsonValue assetManifest, out GameObject prefab)
        {
            prefab = null;
            string glbName = FirstGlb(assetManifest);
            if (glbName == null) return false;

            string path = FindFile(mod, glbName);
            if (path == null) return false;

            string key = mod.Id + "|" + path;
            if (cache.TryGetValue(key, out prefab) && prefab != null) return true;

            if (holder == null)
            {
                var h = new GameObject("GlbTemplates");
                h.SetActive(false);                       // everything under it is inactive: never rendered
                UnityEngine.Object.DontDestroyOnLoad(h);
                holder = h.transform;
            }

            var go = new GameObject("GLB_" + assetManifest.Get("id").AsString(glbName));
            go.transform.SetParent(holder, false);
            var tpl = go.AddComponent<GlbTemplate>();
            tpl.Path = path;
            // Crops are walk-through; everything else (trees, structures, props) is solid.
            tpl.Solid = !(assetManifest.Get("id").AsString("")).StartsWith("crop_", StringComparison.OrdinalIgnoreCase);
            cache[key] = go;
            prefab = go;
            return true;
        }

        private static string FirstGlb(ModJsonValue manifest)
        {
            foreach (ModJsonValue m in manifest.Get("models").Items)
            {
                string file = m.IsObject ? m.Get("file").AsString() : m.AsString();
                if (!string.IsNullOrEmpty(file) &&
                    (file.EndsWith(".glb", StringComparison.OrdinalIgnoreCase) || file.EndsWith(".gltf", StringComparison.OrdinalIgnoreCase)))
                    return System.IO.Path.GetFileName(file);
            }
            return null;
        }

        /// <summary>Finds a model file by name anywhere inside the mod folder (indexed once per mod).</summary>
        private string FindFile(ModInfo mod, string fileName)
        {
            if (!fileIndex.TryGetValue(mod.RootPath, out Dictionary<string, string> index))
            {
                index = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
                string modRoot = System.IO.Path.GetFullPath(mod.RootPath);
                foreach (string ext in new[] { "*.glb", "*.gltf" })
                    foreach (string f in Directory.GetFiles(mod.RootPath, ext, SearchOption.AllDirectories))
                        index.TryAdd(System.IO.Path.GetFileName(f), f);
                fileIndex[mod.RootPath] = index;
            }
            return index.TryGetValue(fileName, out string path) ? path : null;
        }
    }

    /// <summary>Tries each resolver in order and returns the first prefab found.</summary>
    public sealed class CompositeAssetResolver : IModAssetResolver
    {
        private readonly IModAssetResolver[] resolvers;

        public CompositeAssetResolver(params IModAssetResolver[] resolvers) { this.resolvers = resolvers; }

        public bool TryResolvePrefab(ModInfo mod, ModJsonValue assetManifest, out GameObject prefab)
        {
            foreach (IModAssetResolver r in resolvers)
                if (r != null && r.TryResolvePrefab(mod, assetManifest, out prefab)) return true;
            prefab = null;
            return false;
        }
    }
}
