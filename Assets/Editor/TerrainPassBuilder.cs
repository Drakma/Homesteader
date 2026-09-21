using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using Homesteader.Generation;

namespace Homesteader.Editor
{
    public static class TerrainPassBuilder
    {
        [MenuItem("Homesteader/Generate Biome Terrain Pass")]
        public static void ExecuteTerrainPass()
        {
            var activeScene = EditorSceneManager.GetActiveScene();
            Debug.Log($"[Homesteader] Starting Procedural Generative Terrain Pass on scene: {activeScene.name}");

            // 1. Find or create Terrain GameObject sized to 500m x 500m
            Terrain terrain = Object.FindAnyObjectByType<Terrain>();
            GameObject terrainObj;

            if (terrain == null)
            {
                terrainObj = new GameObject("ProceduralTerrain");
                terrainObj.transform.position = Vector3.zero;

                TerrainData tData = new TerrainData
                {
                    heightmapResolution = 513,
                    size = new Vector3(500f, 50f, 500f)
                };

                // Save terrain data asset to project
                string assetPath = "Assets/ProceduralTerrainData.asset";
                AssetDatabase.CreateAsset(tData, assetPath);
                AssetDatabase.SaveAssets();

                terrain = terrainObj.AddComponent<Terrain>();
                terrain.terrainData = tData;
                terrainObj.AddComponent<TerrainCollider>().terrainData = tData;
            }
            else
            {
                terrainObj = terrain.gameObject;
                if (terrain.terrainData != null)
                {
                    // Ensure existing terrain data is resized to 500m x 500m
                    terrain.terrainData.size = new Vector3(500f, 50f, 500f);
                }
            }

            // 2. Ensure Generative Terrain Material is assigned and configured
            Shader genShader = Shader.Find("Homesteader/GenerativeTerrainURP");
            Material genMat = null;
            if (genShader != null)
            {
                string matPath = "Assets/M_GenerativeTerrain.mat";
                genMat = AssetDatabase.LoadAssetAtPath<Material>(matPath);
                if (genMat == null)
                {
                    genMat = new Material(genShader);
                    AssetDatabase.CreateAsset(genMat, matPath);
                    AssetDatabase.SaveAssets();
                }
                else
                {
                    genMat.shader = genShader;
                }

                genMat.SetVector("_TerrainBounds", new Vector4(500f, 500f, 50f, 0f));
                terrain.materialTemplate = genMat;
                Debug.Log("[Homesteader] Assigned M_GenerativeTerrain.mat to Terrain (Bounds: 500m x 500m).");
            }

            // 3. Attach and configure HomesteaderTerrainGenerator
            HomesteaderTerrainGenerator generator = terrainObj.GetComponent<HomesteaderTerrainGenerator>();
            if (generator == null)
            {
                generator = terrainObj.AddComponent<HomesteaderTerrainGenerator>();
            }

            generator.terrainSizeX = 500f;
            generator.terrainSizeZ = 500f;
            generator.terrainHeight = 50f;
            generator.SetupDefaultBiomes();

            // 4. Run procedural generation pass
            generator.GenerateTerrain();

            // Save baked biome texture asset (strictly Linear and Point filtered to prevent phantom mode blending)
            Texture2D bakedTex = generator.GetBakedBiomeMap();
            if (bakedTex != null)
            {
                string texPath = "Assets/T_BakedBiomeMap.asset";
                Texture2D existing = AssetDatabase.LoadAssetAtPath<Texture2D>(texPath);
                if (existing == null)
                {
                    Texture2D assetTex = new Texture2D(bakedTex.width, bakedTex.height, TextureFormat.RGBA32, false, true)
                    {
                        name = "T_BakedBiomeMap",
                        filterMode = FilterMode.Point,
                        wrapMode = TextureWrapMode.Clamp
                    };
                    assetTex.SetPixels(bakedTex.GetPixels());
                    assetTex.Apply();
                    AssetDatabase.CreateAsset(assetTex, texPath);
                    if (genMat != null) genMat.SetTexture("_BiomeMap", assetTex);
                }
                else
                {
                    existing.filterMode = FilterMode.Point;
                    existing.SetPixels(bakedTex.GetPixels());
                    existing.Apply();
                    if (genMat != null) genMat.SetTexture("_BiomeMap", existing);
                    EditorUtility.SetDirty(existing);
                }
                AssetDatabase.SaveAssets();
            }

            EditorUtility.SetDirty(terrainObj);
            EditorSceneManager.MarkSceneDirty(activeScene);
            Debug.Log("[Homesteader] Terrain Pass complete! 500m x 500m terrain with compact biomes evaluated successfully.");
        }
    }
}
