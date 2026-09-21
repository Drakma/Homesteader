using System;
using System.Collections.Generic;
using UnityEngine;

namespace Homesteader.Generation
{
    [Serializable]
    public class BiomeNoiseConfig
    {
        public float frequency = 0.003f;
        public int octaves = 4;
        public float persistence = 0.5f;
        public float threshold = 0.45f;
        public float dither_bandwidth = 0.08f;
    }

    [Serializable]
    public class BiomeElevationConfig
    {
        public float base_offset_m = 0f;
        public float noise_amplitude_m = 10f;
        public float noise_frequency = 0.005f;
        public float max_slope_deg = 45f;
    }

    [Serializable]
    public class GenerativeGroundConfig
    {
        public string shader_mode = "standard_dither";
        public string primary_color_hex = "#15803d";
        public string secondary_color_hex = "#22c55e";
        public string slope_color_hex = "#6b7280";
        public float pattern_scale = 1.0f;
        public float pattern_intensity = 0.5f;
        public float normal_micro_roughness = 0.2f;

        [NonSerialized] public Color primaryColor;
        [NonSerialized] public Color secondaryColor;
        [NonSerialized] public Color slopeColor;

        public void InitColors()
        {
            ColorUtility.TryParseHtmlString(primary_color_hex, out primaryColor);
            ColorUtility.TryParseHtmlString(secondary_color_hex, out secondaryColor);
            ColorUtility.TryParseHtmlString(slope_color_hex, out slopeColor);
        }
    }

    [Serializable]
    public class AssetSpawningConfig
    {
        public string[] biomes;
        public float density_per_hectare = 100f;
        public float clustering = 0.5f;
        public float elevation_min_m = -100f;
        public float elevation_max_m = 500f;
        public float slope_max_deg = 45f;
        public float scale_min = 0.8f;
        public float scale_max = 1.2f;
        public bool align_to_surface_normal = false;
    }

    [Serializable]
    public class BiomeData
    {
        public string id;
        public string name;
        public int priority;
        public string description;
        public string color_hex;
        public float moisture = 0.5f;
        public float nutrients = 0.5f;
        public BiomeNoiseConfig noise;
        public BiomeElevationConfig elevation;
        public GenerativeGroundConfig generative_ground;
    }

    [Serializable]
    public class AssetManifestSummary
    {
        public string id;
        public string name;
        public string category;

        /// <summary>
        /// Whether this asset is scattered into the world by terrain generation.
        /// When false (or when no spawning block is present) the asset is data-only:
        /// it can still be crafted/placed by the player, but the generator never
        /// auto-places it. Mirrors properties.is_spawnable in the item manifest.
        /// </summary>
        public bool is_spawnable;

        public AssetSpawningConfig spawning;
        public GameObject prefab;

        /// <summary>
        /// Namespace this asset's id lives in ("core" for built-in content, or a
        /// mod id). Used to disambiguate identical ids from different sources.
        /// </summary>
        public string ns = "core";

        /// <summary>True when the asset can actually be placed by the generator.</summary>
        public bool CanSpawn =>
            is_spawnable && prefab != null && spawning != null &&
            spawning.biomes != null && spawning.biomes.Length > 0;

        /// <summary>Globally unique key: namespace + id.</summary>
        public string QualifiedId => $"{ns}:{id}";
    }
}
