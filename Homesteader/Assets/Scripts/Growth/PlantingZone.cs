using System.Collections.Generic;
using UnityEngine;

namespace Homesteader.Growth
{
    /// <summary>
    /// A rectangular patch of ground that counts as a given biome for planting rules,
    /// on worlds that have no generated terrain (e.g. the flat "Ground" plane). A
    /// 10x10 farmland plot is one of these with biomeId "biome_farmland". A growth
    /// group whose growth.rules.planting.biomes names that biome can then only be
    /// planted inside it.
    ///
    /// The zone is axis-aligned in world space (rotation is ignored) and is measured
    /// on the ground plane, so its height does not matter.
    /// </summary>
    public sealed class PlantingZone : MonoBehaviour
    {
        public static readonly List<PlantingZone> All = new List<PlantingZone>();

        [Tooltip("Biome id this zone counts as, e.g. biome_farmland.")]
        public string biomeId = "biome_farmland";

        [Tooltip("Zone size on X and Z, in metres, centred on this object.")]
        public Vector2 size = new Vector2(10f, 10f);

        private void OnEnable() => All.Add(this);
        private void OnDisable() => All.Remove(this);

        public bool Contains(Vector3 worldPoint)
        {
            Vector3 c = transform.position;
            return Mathf.Abs(worldPoint.x - c.x) <= size.x * 0.5f
                && Mathf.Abs(worldPoint.z - c.z) <= size.y * 0.5f;
        }

        /// <summary>The biome id of the zone containing the point, or null when it is in none.</summary>
        public static string BiomeAt(Vector3 worldPoint)
        {
            foreach (PlantingZone zone in All)
                if (zone != null && zone.Contains(worldPoint))
                    return zone.biomeId;
            return null;
        }

        private void OnDrawGizmos()
        {
            Gizmos.color = new Color(0.55f, 0.3f, 0.1f, 0.6f);
            Gizmos.DrawWireCube(transform.position + Vector3.up * 0.05f, new Vector3(size.x, 0.1f, size.y));
        }
    }
}
