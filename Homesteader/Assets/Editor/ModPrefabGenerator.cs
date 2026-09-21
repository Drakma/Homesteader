using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Homesteader.Modding;
using UnityEditor;
using UnityEngine;

namespace Homesteader.Editor
{
    /// <summary>
    /// Builds a prefab for every modded asset that declares a model, so the game
    /// can spawn it at runtime.
    ///
    /// WHY THIS IS EDITOR-ONLY: Unity turns an FBX into a mesh at import time and
    /// that conversion does not exist at runtime in a built player. An FBX can
    /// therefore only reach the game as an already-imported prefab. This menu item
    /// performs that step, and `.sync_state.json` means it is safe to re-run.
    ///
    /// Output layout (inside the mod's own folder, so a mod travels with its
    /// geometry and deleting the mod folder deletes its prefabs):
    ///
    ///   Assets/Mods/&lt;mod_id&gt;/
    ///     prefabs/&lt;model_stem&gt;.prefab
    ///
    /// Prefabs are wired with a MeshFilter + MeshRenderer + collider, and a
    /// material taken from the imported model (including embedded textures), with
    /// the project's atlas material as a fallback.
    /// </summary>
    public static class ModPrefabGenerator
    {
        private const string ModsRoot = "Assets/Mods";
        private const string CoreModsFolder = "_handmade";   // never generate here
        private const string PrefabFolder = "prefabs";
        private const string AtlasMaterialPath = "Assets/Materials/M_Homesteader_Palette.mat";

        [MenuItem("Homesteader/Mods/Generate Mod Prefabs", priority = 100)]
        public static void GenerateAll()
        {
            string[] modFolders = GetModFolders();
            if (modFolders.Length == 0)
            {
                Debug.LogWarning($"[Mods] No mod folders found under {ModsRoot}. " +
                                 "Run tools/sync_mods_to_unity.py first.");
                return;
            }

            int built = 0, skipped = 0, failed = 0;

            try
            {
                AssetDatabase.StartAssetEditing();

                foreach (string modFolder in modFolders)
                {
                    foreach (ModAssetEntry entry in ReadModAssets(modFolder))
                    {
                        try
                        {
                            if (BuildPrefab(modFolder, entry))
                                built++;
                            else
                                skipped++;
                        }
                        catch (Exception ex)
                        {
                            failed++;
                            Debug.LogError($"[Mods] Failed building prefab for " +
                                           $"{entry.ItemId}: {ex.Message}");
                        }
                    }
                }
            }
            finally
            {
                AssetDatabase.StopAssetEditing();
                AssetDatabase.Refresh();
            }

            Debug.Log($"[Mods] Prefab generation complete: {built} built, " +
                      $"{skipped} skipped (no model), {failed} failed.");
        }

        [MenuItem("Homesteader/Mods/Clear Generated Prefabs", priority = 101)]
        public static void ClearGenerated()
        {
            int removed = 0;
            foreach (string modFolder in GetModFolders())
            {
                string prefabDir = $"{modFolder}/{PrefabFolder}";
                if (!AssetDatabase.IsValidFolder(prefabDir))
                    continue;

                foreach (string guid in AssetDatabase.FindAssets("t:Prefab", new[] { prefabDir }))
                {
                    string path = AssetDatabase.GUIDToAssetPath(guid);
                    if (AssetDatabase.DeleteAsset(path))
                        removed++;
                }

                if (AssetDatabase.IsValidFolder(prefabDir) &&
                    AssetDatabase.FindAssets("", new[] { prefabDir }).Length == 0)
                {
                    AssetDatabase.DeleteAsset(prefabDir);
                }
            }

            AssetDatabase.Refresh();
            Debug.Log($"[Mods] Removed {removed} generated prefab(s).");
        }

        // ---------------------------------------------------------------- helpers

        private static string[] GetModFolders()
        {
            if (!AssetDatabase.IsValidFolder(ModsRoot))
                return Array.Empty<string>();

            return AssetDatabase.GetSubFolders(ModsRoot)
                .Where(p => Path.GetFileName(p) != CoreModsFolder)
                .ToArray();
        }

        /// <summary>A single asset JSON inside a mod, with its id and declared models.</summary>
        private sealed class ModAssetEntry
        {
            public string ItemId;
            public string JsonPath;
            public List<string> ModelFiles = new List<string>();
            public Vector3 Dimensions;
        }

        /// <summary>
        /// Reads every asset JSON in a mod folder straight off disk. The mod system
        /// uses the same parser at runtime, so the two agree on the format.
        /// </summary>
        private static List<ModAssetEntry> ReadModAssets(string modFolder)
        {
            var entries = new List<ModAssetEntry>();
            string absolute = Path.GetFullPath(modFolder);

            if (!Directory.Exists(absolute))
                return entries;

            foreach (string jsonPath in Directory.GetFiles(absolute, "*.json", SearchOption.AllDirectories))
            {
                if (Path.GetFileName(jsonPath) == "mod.json")
                    continue;

                ModJsonValue root;
                try
                {
                    if (!ModJson.TryParse(File.ReadAllText(jsonPath), out root, out _))
                        continue;
                }
                catch
                {
                    continue;
                }

                string id = root.Get("id").AsString();
                if (string.IsNullOrEmpty(id))
                    continue;

                var entry = new ModAssetEntry
                {
                    ItemId = id,
                    JsonPath = jsonPath.Replace('\\', '/')
                };

                ModJsonValue models = root["models"];
                if (models != null && models.IsArray)
                {
                    foreach (ModJsonValue m in models.Items)
                    {
                        string file = m.IsObject ? m.Get("file").AsString() : m.AsString();
                        if (!string.IsNullOrEmpty(file))
                            entry.ModelFiles.Add(Path.GetFileName(file));
                    }
                }

                ModJsonValue dims = root.Get("category_fields").Get("dimensions_m");
                entry.Dimensions = new Vector3(
                    dims.Get("width").AsFloat(0f),
                    dims.Get("height").AsFloat(0f),
                    dims.Get("depth").AsFloat(0f));

                entries.Add(entry);
            }

            return entries;
        }

        /// <summary>
        /// Builds (or rebuilds) the prefab for one asset. Returns false when the
        /// asset declares no model we can find, which is not an error - plenty of
        /// assets are pure data or inventory-only.
        /// </summary>
        private static bool BuildPrefab(string modFolder, ModAssetEntry entry)
        {
            // Collect every model this asset can use, so an asset with several
            // models (a trunk + a canopy) still produces one prefab whose parts
            // are all present.
            var resolved = new List<(string modelFile, string modelPath)>();
            foreach (string modelFile in entry.ModelFiles)
            {
                string modelPath = FindModelAsset(modFolder, modelFile);
                if (modelPath != null)
                    resolved.Add((modelFile, modelPath));
            }

            if (resolved.Count == 0)
                return false;

            string prefabDir = $"{modFolder}/{PrefabFolder}";
            if (!AssetDatabase.IsValidFolder(prefabDir))
                AssetDatabase.CreateFolder(modFolder, PrefabFolder);

            // The prefab is named after the ASSET ID, not the model file. Two
            // assets in one mod may share a model (recoloured variants) and each
            // still needs its own prefab, keyed the way the runtime resolver
            // looks them up.
            string prefabPath = $"{prefabDir}/{entry.ItemId}.prefab";

            var root = new GameObject(entry.ItemId);

            foreach ((string modelFile, string modelPath) in resolved)
            {
                GameObject model = AssetDatabase.LoadAssetAtPath<GameObject>(modelPath);
                if (model == null)
                    continue;

                GameObject instance = UnityEngine.Object.Instantiate(model);
                instance.name = Path.GetFileNameWithoutExtension(modelFile);
                instance.transform.SetParent(root.transform, false);

                ConfigureInstance(instance, modelPath, entry, modelFile);
            }

            if (root.transform.childCount == 0)
            {
                UnityEngine.Object.DestroyImmediate(root);
                return false;
            }

            // Ground the whole assembly once, after every part is in place.
            GroundToOrigin(root);

            PrefabUtility.SaveAsPrefabAsset(root, prefabPath);
            UnityEngine.Object.DestroyImmediate(root);

            Debug.Log($"[Mods] Built prefab {prefabPath} ({resolved.Count} part(s))");
            return true;
        }

        /// <summary>
        /// Wires a fresh instance: material binding, collider, and a grounding
        /// offset so the model's pivot sits on the terrain rather than sinking.
        /// </summary>
        private static void ConfigureInstance(
            GameObject instance, string modelPath, ModAssetEntry entry, string modelFile)
        {
            // Remove any camera/light the FBX may carry; only geometry belongs in
            // a spawned world object.
            foreach (Camera cam in instance.GetComponentsInChildren<Camera>(true))
                UnityEngine.Object.DestroyImmediate(cam.gameObject);
            foreach (Light light in instance.GetComponentsInChildren<Light>(true))
                UnityEngine.Object.DestroyImmediate(light.gameObject);

            Material fallback = AssetDatabase.LoadAssetAtPath<Material>(AtlasMaterialPath);

            // A "<model>_base_color.png" beside the model is the authored texture. The FBX's own
            // embedded material can lose it (crops came out plain grey), so bind it explicitly.
            Material authored = GetBaseColorMaterial(modelPath);

            foreach (Renderer renderer in instance.GetComponentsInChildren<Renderer>(true))
            {
                if (authored != null)
                {
                    var slots = new Material[Mathf.Max(1, renderer.sharedMaterials.Length)];
                    for (int i = 0; i < slots.Length; i++) slots[i] = authored;
                    renderer.sharedMaterials = slots;
                }

                // If the importer produced no material (common with embedded
                // textures), bind the project atlas so the mesh is at least shaded.
                if (renderer.sharedMaterials == null ||
                    renderer.sharedMaterials.Length == 0 ||
                    renderer.sharedMaterials.All(m => m == null))
                {
                    if (fallback != null)
                        renderer.sharedMaterial = fallback;
                }

                renderer.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.On;
                renderer.receiveShadows = true;
            }

            // Trees are static scenery: give them colliders so the player and
            // other systems can interact with them. Crops are the exception - the player
            // walks through them - so crop stages get no collider at all.
            bool solid = !entry.ItemId.StartsWith("crop_", StringComparison.OrdinalIgnoreCase);
            foreach (MeshFilter filter in instance.GetComponentsInChildren<MeshFilter>(true))
            {
                if (!solid) break;
                if (filter.sharedMesh == null) continue;
                if (filter.GetComponent<Collider>() == null)
                    filter.gameObject.AddComponent<MeshCollider>().sharedMesh = filter.sharedMesh;
            }

            // Ground the model: shift up so its lowest point sits at y = 0. The
            // pipeline pivots most models at the base already, but not all, and a
            // tree that spawns half-buried looks broken.
            GroundToOrigin(instance);
        }

        /// <summary>
        /// The URP/Lit material for "&lt;model&gt;_base_color.png" (created once, then reused),
        /// or null when the model ships no such texture. The texture is searched for in the whole
        /// mod folder, because the prefab is built from a copy of the model under models/ while the
        /// texture sits with the source asset (e.g. stages/&lt;stage&gt;/).
        /// </summary>
        private static Material GetBaseColorMaterial(string modelPath)
        {
            string stem = Path.GetFileNameWithoutExtension(modelPath);
            string[] parts = modelPath.Split('/');
            if (parts.Length < 4) return null;
            string modRoot = string.Join("/", parts.Take(3));          // Assets/Mods/<mod_id>

            string texturePath = null;
            foreach (string guid in AssetDatabase.FindAssets(stem + "_base_color t:Texture2D", new[] { modRoot }))
            {
                string candidate = AssetDatabase.GUIDToAssetPath(guid);
                if (Path.GetFileNameWithoutExtension(candidate) == stem + "_base_color")
                {
                    texturePath = candidate;
                    break;
                }
            }
            if (texturePath == null) return null;

            var texture = AssetDatabase.LoadAssetAtPath<Texture2D>(texturePath);
            string matPath = Path.ChangeExtension(texturePath, ".mat");
            var mat = AssetDatabase.LoadAssetAtPath<Material>(matPath);
            if (mat == null)
            {
                mat = new Material(Shader.Find("Universal Render Pipeline/Lit"));
                AssetDatabase.CreateAsset(mat, matPath);
            }
            mat.SetTexture("_BaseMap", texture);
            mat.SetColor("_BaseColor", Color.white);
            mat.SetFloat("_Smoothness", 0.1f);
            mat.SetFloat("_Metallic", 0f);
            EditorUtility.SetDirty(mat);
            return mat;
        }

        private static void GroundToOrigin(GameObject instance)
        {
            var renderers = instance.GetComponentsInChildren<Renderer>(true);
            if (renderers.Length == 0) return;

            Bounds bounds = renderers[0].bounds;
            for (int i = 1; i < renderers.Length; i++)
                bounds.Encapsulate(renderers[i].bounds);

            float bottom = bounds.min.y;
            if (Mathf.Abs(bottom) < 0.001f) return;   // already grounded

            instance.transform.position -= new Vector3(0f, bottom, 0f);
        }

        private static string FindModelAsset(string modFolder, string modelFile)
        {
            string[] folders = { $"{modFolder}/models", $"{modFolder}", $"{modFolder}/assets" };

            foreach (string folder in folders)
            {
                if (!AssetDatabase.IsValidFolder(folder))
                    continue;

                foreach (string guid in AssetDatabase.FindAssets("t:Model", new[] { folder }))
                {
                    string path = AssetDatabase.GUIDToAssetPath(guid);
                    if (string.Equals(Path.GetFileName(path), modelFile, StringComparison.OrdinalIgnoreCase))
                        return path;
                }
            }

            return null;
        }
    }
}
