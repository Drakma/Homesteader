using System;
using System.Collections.Generic;
using Homesteader.Generation;
using Homesteader.UI;
using UnityEngine;

namespace Homesteader.Growth
{
    /// <summary>
    /// Decides whether a growth group may be planted at a ground hit point.
    /// Every rule that comes from data lives in the group's growth.rules (loaded
    /// from the mod); only the world-physics limits below are constants here.
    /// Returns a short player-facing reason on failure.
    /// </summary>
    public static class PlantingValidator
    {
        /// <summary>Ground grid cell size in metres (the grid lines sit on whole world X/Z).</summary>
        public const float GridSizeM = 1f;

        /// <summary>
        /// Snaps a ground point to the centre of the grid cell it falls in. Plants are
        /// placed on cell centres so they sit inside a grid square, not on a line.
        /// </summary>
        public static Vector3 SnapToGrid(Vector3 p)
        {
            p.x = (Mathf.Floor(p.x / GridSizeM) + 0.5f) * GridSizeM;
            p.z = (Mathf.Floor(p.z / GridSizeM) + 0.5f) * GridSizeM;
            return p;
        }


        /// <summary>
        /// How far from the player's own grid square a plant can be placed, in squares.
        /// 1 = the square the player stands on and the eight squares immediately around it.
        /// </summary>
        public const int ReachCells = 1;
        /// <summary>Steepest ground that can be planted, in degrees.</summary>
        public const float MaxSlopeDeg = 25f;
        /// <summary>Minimum distance between two planted groups, in metres.</summary>
        public const float CropSpacingM = 0.5f;
        public const float TreeSpacingM = 2.0f;

        // Standing/flowing water is never plantable regardless of a group's biome list.
        private static readonly HashSet<string> WaterBiomes =
            new HashSet<string>(StringComparer.OrdinalIgnoreCase) { "biome_pond", "biome_river", "biome_lake" };

        public static bool Validate(GrowthGroup group, RaycastHit hit, Transform player, out string reason)
        {
            reason = null;

            if (group == null || !group.IsPlantable)
            {
                reason = "That can't be planted.";
                return false;
            }
            if (group.Stages.Count == 0 || group.Stages[0].Prefab == null)
            {
                reason = $"{group.Name} has no model loaded (generate the mod prefabs).";
                return false;
            }

            // Ground: the click must land on the ground (terrain or the flat "Ground"
            // plane), not a building or prop.
            if (!IsGround(hit.collider))
            {
                reason = "You can only plant in open ground.";
                return false;
            }

            float slope = Vector3.Angle(hit.normal, Vector3.up);
            if (slope > MaxSlopeDeg)
            {
                reason = "The ground is too steep to plant.";
                return false;
            }

            // Only the squares right next to the player: compare grid cells, not metres, so
            // it matches the grid the player sees whatever the player's exact position is.
            if (!InReach(player, hit.point))
            {
                reason = "You can only plant in the squares right next to you.";
                return false;
            }

            // Biome: a planting zone on the ground wins; otherwise the generated terrain's
            // biome map (terrain-local metres) if there is one; otherwise unknown (null).
            string biomeId = PlantingZone.BiomeAt(hit.point);
            string biomeName = null;
            if (biomeId == null)
            {
                var generator = UnityEngine.Object.FindFirstObjectByType<HomesteaderTerrainGenerator>();
                if (generator != null && generator.GetComponent<Terrain>() != null)
                {
                    Vector3 origin = generator.transform.position;
                    BiomeData biome = generator.EvaluateBiomeAt(hit.point.x - origin.x, hit.point.z - origin.z);
                    if (biome != null)
                    {
                        biomeId = biome.id;
                        biomeName = biome.name;
                    }
                }
            }

            if (biomeId != null && WaterBiomes.Contains(biomeId))
            {
                reason = "You can't plant in water.";
                return false;
            }
            if (group.Rules.Biomes.Count > 0 && (biomeId == null || !group.Rules.Biomes.Contains(biomeId)))
            {
                reason = biomeId == null
                    ? $"{group.Name} needs {DescribeBiomes(group.Rules.Biomes)} to grow."
                    : $"{group.Name} can't grow in {(string.IsNullOrEmpty(biomeName) ? Pretty(biomeId) : biomeName)}; it needs {DescribeBiomes(group.Rules.Biomes)}.";
                return false;
            }

            // Season + temperature
            if (!group.Rules.IndoorOk)
            {
                if (!SeasonAllowed(group.Rules, TimeSystem.Instance.GetSeason(), out string allowed))
                {
                    reason = $"{group.Name} can only be planted in {allowed}.";
                    return false;
                }

                float temp = TimeSystem.Instance.Snapshot().TemperatureC;
                if (group.Rules.MinTempC.HasValue && temp < group.Rules.MinTempC.Value)
                {
                    reason = $"Too cold to plant {group.Name} ({temp:0}°C, needs {group.Rules.MinTempC.Value:0}°C+).";
                    return false;
                }
                if (group.Rules.MaxTempC.HasValue && temp > group.Rules.MaxTempC.Value)
                {
                    reason = $"Too hot to plant {group.Name} ({temp:0}°C, max {group.Rules.MaxTempC.Value:0}°C).";
                    return false;
                }
            }

            // Spacing
            float spacing = group.GrowthType == "tree" ? TreeSpacingM : CropSpacingM;
            foreach (PlantedGrowth other in PlantedGrowth.All)
            {
                if (other != null && Vector3.Distance(other.transform.position, hit.point) < spacing)
                {
                    reason = "Something is already growing there.";
                    return false;
                }
            }

            return true;
        }

        /// <summary>True for terrain or the flat scene ground (an object named "Ground").</summary>
        private static bool IsGround(Collider c)
        {
            return c is TerrainCollider || c.gameObject.name == "Ground";
        }

        private static string Pretty(string biomeId)
        {
            return biomeId.StartsWith("biome_") ? biomeId.Substring(6).Replace('_', ' ') : biomeId;
        }

        private static string DescribeBiomes(List<string> ids)
        {
            var names = new List<string>();
            foreach (string id in ids) names.Add(Pretty(id));
            return string.Join(" or ", names);
        }

        /// <summary>True when the point is in the player's own grid square or one of the eight around it.</summary>
        public static bool InReach(Transform player, Vector3 point)
        {
            if (player == null) return true;
            int dx = Mathf.Abs(CellIndex(point.x) - CellIndex(player.position.x));
            int dz = Mathf.Abs(CellIndex(point.z) - CellIndex(player.position.z));
            return dx <= ReachCells && dz <= ReachCells;
        }

        /// <summary>The grid cell index (whole-metre square) a world coordinate falls in.</summary>
        private static int CellIndex(float coordinate)
        {
            return Mathf.FloorToInt(coordinate / GridSizeM);
        }

        /// <summary>True when <paramref name="season"/> is allowed by the rules' planting seasons.</summary>
        public static bool SeasonAllowed(GrowthRules rules, HomesteaderSeason season, out string allowedList)
        {
            allowedList = rules.YearRound ? "any season" : string.Join(" or ", rules.Seasons);
            if (rules.YearRound) return true;
            return rules.Seasons.Contains(SeasonKey(season));
        }

        /// <summary>The schema's season key for a game season (Autumn is "fall").</summary>
        public static string SeasonKey(HomesteaderSeason season)
        {
            switch (season)
            {
                case HomesteaderSeason.Spring: return "spring";
                case HomesteaderSeason.Summer: return "summer";
                case HomesteaderSeason.Autumn: return "fall";
                default: return "winter";
            }
        }
    }
}
