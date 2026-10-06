using Homesteader.Generation;
using Homesteader.Land;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace Homesteader.DebugTools
{
    /// <summary>
    /// Actually wires up HomesteaderTerrainGenerator + GenerativeTerrainURP, which existed in
    /// the codebase but were never attached to anything in SampleScene - the ground you've
    /// been testing on is a separate, much simpler flat "Ground" plane + mod Zone_ objects.
    ///
    /// Builds a real Terrain (500x500m) at scene load, destroys the old flat Ground so they
    /// don't overlap, and runs the generator. The terrain's own transform sits at Y=-14 so
    /// its flat height (baked at the generator's 14m baseline, see
    /// HomesteaderTerrainGenerator.GenerateTerrain) lands at world Y=0, matching where the
    /// old Ground plane and existing Zone_ objects/player spawn already are.
    /// Bootstraps itself on scene load, same pattern as FpsCounter.
    /// </summary>
    public static class TerrainGeneratorBootstrap
    {
        /// <summary>The world seed of the save being continued (0 = none). The next generated world uses it instead of the default seed.</summary>
        public static int SeedOverride;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        private static void Bootstrap()
        {
            // Register for all future scene loads too. RuntimeInitializeOnLoadMethod
            // only fires once (first scene), so we need sceneLoaded to re-run on
            // scene reloads (e.g. New Game).
            SceneManager.sceneLoaded -= OnSceneLoaded;
            SceneManager.sceneLoaded += OnSceneLoaded;

            // Also run immediately for the first scene.
            OnSceneLoaded(default, LoadSceneMode.Single);
        }

        private static void OnSceneLoaded(Scene scene, LoadSceneMode mode)
        {
            Dbg.Log($"[TerrainGeneratorBootstrap] OnSceneLoaded: scene={scene.name}");

            // Destroy ALL old ground/terrain objects that are not the real generated
            // terrain. The scene may contain a legacy flat "Ground" plane, or leftover
            // Terrain objects from a previous editor-time TerrainPassBuilder run that
            // got saved into the scene. We must clean these up so only ONE terrain
            // generator remains — otherwise two generators with different seeds produce
            // overlapping, conflicting terrain (pink/mixed minimap).
            var existingGens = Object.FindObjectsByType<HomesteaderTerrainGenerator>(FindObjectsInactive.Include);
            if (existingGens.Length > 0)
            {
                // Keep the first, destroy the rest
                for (int i = 1; i < existingGens.Length; i++)
                {
                    Dbg.Log($"[TerrainGeneratorBootstrap] Destroying duplicate generator on '{existingGens[i].gameObject.name}'.");
                    Object.Destroy(existingGens[i].gameObject);
                }

                // Also destroy any legacy "Ground" plane — it's a flat plane from the
                // original scene that should never have a terrain generator. Even if
                // a previous run added one at runtime, it's a duplicate and must go.
                var oldGround = GameObject.Find("Ground");
                if (oldGround != null)
                {
                    Dbg.Log("[TerrainGeneratorBootstrap] Destroying legacy Ground plane.");
                    Object.Destroy(oldGround);
                }

                // Ensure the surviving generator has a valid material and collider.
                // A generator left over from a previous editor run may have a NULL
                // materialTemplate (renders pink) or a missing TerrainCollider.
                var survivingGen = existingGens[0];
                var survivingTerrain = survivingGen.GetComponent<Terrain>();
                if (survivingTerrain != null)
                {
                    if (survivingTerrain.materialTemplate == null)
                    {
                        Shader genShader = Shader.Find("Homesteader/GenerativeTerrainURP");
                        if (genShader != null)
                        {
                            survivingTerrain.materialTemplate = new Material(genShader);
                            Dbg.Log("[TerrainGeneratorBootstrap] Assigned missing material to surviving terrain.");
                        }
                    }
                    if (survivingTerrain.GetComponent<TerrainCollider>() == null)
                    {
                        var tc = survivingTerrain.gameObject.AddComponent<TerrainCollider>();
                        tc.terrainData = survivingTerrain.terrainData;
                    }
                    // Ensure correct Y position
                    if (survivingTerrain.transform.position.y != -14f)
                        survivingTerrain.transform.position = new Vector3(0f, -14f, 0f);
                }

                Dbg.Log("[TerrainGeneratorBootstrap] Generator already exists, skipping creation.");
                return;
            }

            // No generator at all — destroy any legacy Ground and create one
            var legacyGround = GameObject.Find("Ground");
            if (legacyGround != null) Object.Destroy(legacyGround);

            var terrainData = new TerrainData
            {
                heightmapResolution = 513,
            };

            GameObject terrainGO = Terrain.CreateTerrainGameObject(terrainData);
            terrainGO.name = "GeneratedTerrain";
            terrainGO.transform.position = new Vector3(0f, -14f, 0f);

            var terrain = terrainGO.GetComponent<Terrain>();
            Shader shader = Shader.Find("Homesteader/GenerativeTerrainURP");
            if (shader != null)
            {
                terrain.materialTemplate = new Material(shader);
            }
            else
            {
                Debug.LogWarning("[TerrainGeneratorBootstrap] Shader 'Homesteader/GenerativeTerrainURP' not found.");
            }

            var generator = terrainGO.AddComponent<HomesteaderTerrainGenerator>();
            generator.SetupDefaultBiomes();
            // The world is regenerated from its seed, so a save's seed must be used however the scene came to load (Continue, Load, Play in
            // the editor, a reload): the menu hands it over through SeedOverride, but any other path would otherwise build the default
            // seed's world and put the save's buildings on different ground. So when nothing was handed over, read it from the save itself.
            int seed = SeedOverride;
            string loadPath = Homesteader.Save.SaveSlots.ResolveLoadPath();   // the save picked in the Load list, else the newest; makes its game the current one
            if (seed <= 0 && loadPath != null)
            {
                Homesteader.Save.GameSave saved = Homesteader.Save.GameSave.ReadFrom(loadPath);
                if (saved != null && saved.worldSeed > 0) seed = saved.worldSeed;
            }
            if (seed > 0)
            {
                generator.worldSeed = seed;
                generator.InvalidateSeedCache();
                Dbg.Log($"[TerrainGeneratorBootstrap] Using the saved world seed {seed}.");
                SeedOverride = 0;
            }
            // continuing a world: its generated ground comes from the snapshot saved beside the save (the generator checks that it fits)
            if (loadPath != null) generator.PendingSnapshot = WorldSnapshot.TryRead();

            // Always generate synchronously. If a New Game is pending, the
            // WelcomeMenuController will regenerate with the new seed + a
            // progress bar afterward. This avoids leaving an empty terrain
            // (grid-only shader) if the async path is interrupted.
            // A Continue / Load reloads the scene: its world is built by the welcome menu behind the loading bar (async, with progress) instead of
            // here, where the whole generation would freeze the screen before the bar could even be drawn.
            bool deferred = Homesteader.UI.WelcomeMenuController.DeferWorldGeneration;
            Homesteader.UI.WelcomeMenuController.DeferWorldGeneration = false;
            if (!deferred) generator.GenerateTerrain();

            var terrainCollider = terrainGO.GetComponent<TerrainCollider>();
            if (terrainCollider == null)
            {
                terrainCollider = terrainGO.AddComponent<TerrainCollider>();
            }
            terrainCollider.terrainData = terrain.terrainData;
            terrainCollider.enabled = true;

            Dbg.Log($"[TerrainGeneratorBootstrap] Terrain generated successfully. Collider enabled: {terrainCollider.enabled}, terrainData assigned: {terrainCollider.terrainData != null}");
        }

        /// <summary>
        /// Rebuilds land boundaries after scene load. Called via a coroutine
        /// to ensure terrain is ready before walls are placed.
        /// </summary>
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        private static void RebuildLandBoundariesOnLoad()
        {
            // Register for scene loads
            SceneManager.sceneLoaded -= OnSceneLoadedForLand;
            SceneManager.sceneLoaded += OnSceneLoadedForLand;
            OnSceneLoadedForLand(default, LoadSceneMode.Single);
        }

        private static void OnSceneLoadedForLand(Scene scene, LoadSceneMode mode)
        {
            // Initialize ownership and rebuild boundaries. This handles the
            // Continue/Load case. New Game will call CreateLandBoundaries()
            // again after async terrain generation completes.
            Homesteader.Land.LandOwnershipSystem.Initialize();

            var existing = Object.FindAnyObjectByType<Homesteader.Land.LandBoundaryController>();
            if (existing == null)
            {
                var go = new GameObject("LandBoundaries");
                existing = go.AddComponent<Homesteader.Land.LandBoundaryController>();
            }
            existing.RebuildBoundaries();
            Dbg.Log("[TerrainGeneratorBootstrap] Land boundaries rebuilt on scene load.");
        }
    }
}
