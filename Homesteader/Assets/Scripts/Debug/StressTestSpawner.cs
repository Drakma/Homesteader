using System.Collections;
using System.IO;
using Homesteader.Modding;
using UnityEngine;

namespace Homesteader.DebugTools
{
    /// <summary>
    /// One-off stress test: loads the fruiting-orange-tree GLB once and instantiates many copies
    /// of it in a grid, well clear of the farmland/forest test zones, so poly-count / FPS impact
    /// can be judged visually. Reads straight from the source assets/ folder (not the packaged
    /// mod), so it works whether or not the mod has been repackaged yet.
    ///
    /// NOT auto-run: these are plain GLB clones with no PlantedGrowth/GrowthGroup component, so
    /// they can't be harvested, picked, or otherwise interacted with - they previously spawned
    /// into every play session via RuntimeInitializeOnLoadMethod, which made a normal playtest
    /// look like a real (but broken) orchard. Trigger it deliberately from the Editor menu below
    /// when you actually want the stress-test grid.
    /// </summary>
    public sealed class StressTestSpawner : MonoBehaviour
    {
        private const int Count = 200;
        private const int Columns = 20;
        private const float Spacing = 4f;
        // Immediately left (more negative x) of the farmland zone (x -5..5, z 3..13), 5m gap from its
        // left edge, rows centered on the farmland's z-range. Column 0 (nearest farmland) ends up at
        // x = -10; the far column reaches x = -10 - (Columns-1)*Spacing.
        private static readonly Vector3 Origin = new Vector3(-10f - (Columns - 1) * Spacing, 0f, -10f);

#if UNITY_EDITOR
        [UnityEditor.MenuItem("Homesteader/Debug/Spawn 200-Tree Stress Test")]
        private static void SpawnFromMenu()
        {
            if (FindAnyObjectByType<StressTestSpawner>() != null) return;
            var go = new GameObject("StressTestSpawner_200_OrangeFruiting");
            go.AddComponent<StressTestSpawner>();
        }
#endif

        private void Start() => StartCoroutine(SpawnRoutine());

        private IEnumerator SpawnRoutine()
        {
            string glbPath = Path.GetFullPath(Path.Combine(
                Application.dataPath, "../../assets/logging/orange/stages/tree_fruiting/tree_fruiting_orange.glb"));

            if (!File.Exists(glbPath))
            {
                Debug.LogError($"[StressTest] GLB not found at '{glbPath}'.");
                yield break;
            }

            var holder = new GameObject("StressTest_TemplateHolder");
            holder.SetActive(false);
            var template = holder.AddComponent<GlbTemplate>();
            template.Path = glbPath;
            template.Solid = true;
            template.EnsureLoading();

            float waited = 0f;
            while (!template.Ready && !template.Failed && waited < 60f)
            {
                waited += Time.unscaledDeltaTime;
                yield return null;
            }

            if (template.Failed || !template.Ready)
            {
                Debug.LogError("[StressTest] GLB failed to load - nothing spawned.");
                yield break;
            }

            var parent = new GameObject($"StressTest_{Count}_OrangeFruiting").transform;
            for (int i = 0; i < Count; i++)
            {
                int col = i % Columns;
                int row = i / Columns;
                Vector3 pos = Origin + new Vector3(col * Spacing, 0f, row * Spacing);
                var instance = Instantiate(holder, pos, Quaternion.identity, parent);
                instance.name = $"OrangeFruiting_{i:000}";
                instance.SetActive(true);
            }

            Debug.Log($"[StressTest] Spawned {Count} fruiting orange trees ({Columns} x {Mathf.CeilToInt((float)Count / Columns)} grid, {Spacing}m spacing) at {Origin}. Each tree is 3000 tris -> ~{Count * 3000:N0} tris total.");
        }
    }
}
