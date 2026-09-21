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
        /// <summary>How far from the player a plant can be placed, in metres.</summary>
        public const float MaxReachM = 8f;
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

            // Ground: the click must land on terrain, not a building or prop.
            if (!(hit.collider is TerrainCollider))
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

            if (player != null && PlanarDistance(player.position, hit.point) > MaxReachM)
            {
                reason = "Too far away to plant there.";
                return false;
            }

            // Biome
            var generator = UnityEngine.Object.FindFirstObjectByType<HomesteaderTerrainGenerator>();
            if (generator != null)
            {
                // Biome maps are in TERRAIN-LOCAL metres (0..terrain size), not world space.
                Vector3 origin = generator.transform.position;
                BiomeData biome = generator.EvaluateBiomeAt(hit.point.x - origin.x, hit.point.z - origin.z);
                if (biome != null)
                {
                    if (WaterBiomes.Contains(biome.id))
                    {
                        reason = "You can't plant in water.";
                        return false;
                    }
                    if (group.Rules.Biomes.Count > 0 && !group.Rules.Biomes.Contains(biome.id))
                    {
                        reason = $"{group.Name} can't grow in {(string.IsNullOrEmpty(biome.name) ? biome.id : biome.name)}.";
                        return false;
                    }
                }
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

        // Reach is measured on the ground plane so standing above or below the spot
        // (a slope, a fall from the spawn point) does not count against the player.
        private static float PlanarDistance(Vector3 a, Vector3 b)
        {
            a.y = 0f; b.y = 0f;
            return Vector3.Distance(a, b);
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
