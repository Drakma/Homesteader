using Homesteader.Generation;
using UnityEngine;

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
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        private static void Bootstrap()
        {
            Debug.Log("[TerrainGeneratorBootstrap] Running...");
            if (Object.FindAnyObjectByType<HomesteaderTerrainGenerator>() != null)
            {
                Debug.Log("[TerrainGeneratorBootstrap] Generator already exists, skipping.");
                return;
            }

            var oldGround = GameObject.Find("Ground");
            if (oldGround != null) Object.Destroy(oldGround);

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
            generator.GenerateTerrain();

            var terrainCollider = terrainGO.GetComponent<TerrainCollider>();
            if (terrainCollider == null)
            {
                terrainCollider = terrainGO.AddComponent<TerrainCollider>();
            }
            terrainCollider.terrainData = terrain.terrainData;
            terrainCollider.enabled = true;

            Debug.Log($"[TerrainGeneratorBootstrap] Terrain generated successfully. Collider enabled: {terrainCollider.enabled}, terrainData assigned: {terrainCollider.terrainData != null}");
        }
    }
}
