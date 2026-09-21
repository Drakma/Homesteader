using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Homesteader.Generation;
using Homesteader.Growth;
using UnityEngine;

namespace Homesteader.Modding
{
    /// <summary>
    /// The game-side result of applying one mod: what it actually contributed.
    /// Exposed so UI / debug tooling can report "this mod added 3 biomes".
    /// </summary>
    public sealed class ModLoadResult
    {
        public ModInfo Mod;
        public int BiomesAdded;
        public int AssetsRegistered;
        public int FilesIndexed;
        public readonly List<string> Messages = new List<string>();

        public string Summary =>
            $"{Mod.Id}: +{BiomesAdded} biomes, +{AssetsRegistered} assets, {FilesIndexed} files";

        public override string ToString() => Summary;
    }

    /// <summary>
    /// Applies a parsed, ordered set of mods into the running game's registries.
    ///
    /// This is intentionally the ONLY place that mutates game state from mods,
    /// so the merge rules are auditable in one file:
    ///   - Biomes: appended to the terrain generator, de-duplicated by id. A mod
    ///     biome that collides with a core biome id is rejected (core wins),
    ///     never silently overwritten.
    ///   - Assets: parsed into AssetManifestSummary entries and appended to the
    ///     generator's registeredAssets list for spawning.
    ///   - Unknown/unresolvable content is reported, never fatal.
    ///
    /// Prefab binding: mods reference prefabs by id; a modded prefab is resolved
    /// through ModAssetResolver. If no prefab can be resolved, the asset is
    /// still registered so its data (recipes, values) is available, but it will
    /// not spawn in the world.
    /// </summary>
    public static class ModLoader
    {
        public static List<ModLoadResult> ApplyAll(
            IEnumerable<ModInfo> mods,
            HomesteaderTerrainGenerator terrainGenerator,
            IModAssetResolver assetResolver,
            Action<string> log = null)
        {
            var results = new List<ModLoadResult>();

            foreach (ModInfo mod in mods)
            {
                if (!mod.IsValid)
                    continue;

                if (mod.IsDisabled || ModDiscovery.IsDisabledName(mod.SourceName) || ModDiscovery.IsPathDisabled(mod.RootPath))
                {
                    log?.Invoke($"[Mods] Skipping disabled mod '{mod.Id}' ({mod.SourceName}).");
                    continue;
                }

                var result = new ModLoadResult { Mod = mod };

                LoadTags(mod);

                foreach (ModContentEntry entry in mod.Manifest.Contents)
                {
                    try
                    {
                        switch (entry.Type)
                        {
                            case ModContentType.Biome:
                                LoadBiomes(mod, entry, terrainGenerator, result, log);
                                break;

                            case ModContentType.GameRules:
                                LoadGameRules(mod, entry, result, log);
                                break;

                            case ModContentType.Script:
                                result.Messages.Add(
                                    $"Content type 'script' is declared but not executable in this build; " +
                                    $"{entry.Path} was indexed for future use.");
                                break;

                            default:
                                // Every non-biome type is an item-shaped asset that
                                // goes through the same catalog/spawn pipeline.
                                LoadAsset(mod, entry, terrainGenerator, assetResolver, result, log);
                                break;
                        }
                    }
                    catch (Exception ex)
                    {
                        mod.Warnings.Add($"Error applying {entry}: {ex.Message}");
                        log?.Invoke($"[Mods] {mod.Id}: failed on {entry} - {ex.Message}");
                    }
                }

                results.Add(result);
                log?.Invoke($"[Mods] Applied {result.Summary}");
            }

            return results;
        }

        // ------------------------------------------------------------------ Game rules

        /// <summary>Merges a mod's gamerules.json into GameRules (later mods override earlier keys).</summary>
        private static void LoadGameRules(ModInfo mod, ModContentEntry entry, ModLoadResult result, Action<string> log)
        {
            foreach (string file in ModFileResolver.ResolveFiles(mod, entry.Path, ".json"))
            {
                if (!ModJson.TryParse(File.ReadAllText(file), out ModJsonValue root, out string error))
                {
                    mod.Warnings.Add($"Game rules file '{file}' is not valid JSON - {error}");
                    continue;
                }
                GameRules.Apply(mod, root, msg => mod.Warnings.Add($"Game rules: {msg}"));
                result.Messages.Add("Applied game rules from " + Path.GetFileName(file));
                log?.Invoke($"[Mods] {mod.Id}: applied game rules ({Path.GetFileName(file)}).");
            }
        }

        // ------------------------------------------------------------------ Tags

        /// <summary>
        /// Reads the mod's optional root-level tags.json ({"tags": {"name": ["item_id", ...]}}) into the
        /// tag registry. Tags are virtual items standing for interchangeable real ones; a recipe or
        /// harvest tool refers to one as "#name".
        /// </summary>
        private static void LoadTags(ModInfo mod)
        {
            string path = Path.Combine(mod.RootPath, "tags.json");
            if (!File.Exists(path)) return;
            try
            {
                if (!ModJson.TryParse(File.ReadAllText(path), out ModJsonValue root, out string error))
                {
                    mod.Warnings.Add($"tags.json is not valid JSON - {error}");
                    return;
                }
                ModJsonValue tagObj = root.Get("tags");
                if (!tagObj.IsObject) return;
                foreach (KeyValuePair<string, ModJsonValue> kv in tagObj.ObjectValue)
                    GrowthRegistry.RegisterTag(kv.Key, kv.Value.AsStringList());
            }
            catch (Exception ex)
            {
                mod.Warnings.Add($"tags.json could not be read: {ex.Message}");
            }
        }

        // ---------------------------------------------------------------- Biomes

        private static void LoadBiomes(
            ModInfo mod,
            ModContentEntry entry,
            HomesteaderTerrainGenerator generator,
            ModLoadResult result,
            Action<string> log)
        {
            if (generator == null)
            {
                // No terrain generator: biomes have nowhere to apply.
                return;
            }

            foreach (string file in ModFileResolver.ResolveFiles(mod, entry.Path, ".json"))
            {
                string text = File.ReadAllText(file);
                if (!ModJson.TryParse(text, out ModJsonValue root, out string error))
                {
                    mod.Warnings.Add($"Biome file '{file}' is not valid JSON - {error}");
                    continue;
                }

                BiomeData biome = ParseBiome(root, out string parseError);
                if (biome == null)
                {
                    mod.Warnings.Add($"Biome file '{file}' rejected - {parseError}");
                    continue;
                }

                // Core biomes always win: a mod may add new biomes but never
                // silently replace one the base game (or an earlier mod) defined.
                if (generator.biomes.Any(b => b.id == biome.id))
                {
                    mod.Warnings.Add($"Biome '{biome.id}' already exists (base game or an earlier mod); this copy is ignored.");
                    continue;
                }

                generator.biomes.Add(biome);
                result.BiomesAdded++;
            }
        }

        /// <summary>
        /// Maps a biome manifest JSON tree onto the game's BiomeData, mirroring
        /// the exact shape of assets/biomes/*.json.
        /// </summary>
        public static BiomeData ParseBiome(ModJsonValue root, out string error)
        {
            error = null;
            string id = root.Get("id").AsString();
            if (string.IsNullOrWhiteSpace(id))
            {
                error = "missing required field 'id'";
                return null;
            }
            if (!id.StartsWith("biome_", StringComparison.Ordinal))
            {
                error = "biome id must start with 'biome_'";
                return null;
            }

            var biome = new BiomeData
            {
                id = id,
                name = root.Get("name").AsString() ?? id,
                priority = root.Get("priority").AsInt(0),
                description = root.Get("description").AsString(),
                color_hex = root.Get("color_hex").AsString() ?? "#ffffff",
                moisture = root.Get("moisture").AsFloat(0.5f),
                nutrients = root.Get("nutrients").AsFloat(0.5f),
                noise = ParseNoise(root["noise"]),
                elevation = ParseElevation(root["elevation"]),
                generative_ground = ParseGround(root["generative_ground"])
            };

            if (string.IsNullOrWhiteSpace(biome.color_hex) || biome.color_hex[0] != '#')
            {
                error = "color_hex must be a #rrggbb string";
                return null;
            }

            return biome;
        }

        private static BiomeNoiseConfig ParseNoise(ModJsonValue n)
        {
            if (n == null) return new BiomeNoiseConfig();
            return new BiomeNoiseConfig
            {
                frequency = n.Get("frequency").AsFloat(0.003f),
                octaves = Mathf.Clamp(n.Get("octaves").AsInt(4), 1, 8),
                persistence = n.Get("persistence").AsFloat(0.5f),
                threshold = n.Get("threshold").AsFloat(0.45f),
                dither_bandwidth = n.Get("dither_bandwidth").AsFloat(0.08f)
            };
        }

        private static BiomeElevationConfig ParseElevation(ModJsonValue e)
        {
            if (e == null) return new BiomeElevationConfig();
            return new BiomeElevationConfig
            {
                base_offset_m = e.Get("base_offset_m").AsFloat(0f),
                noise_amplitude_m = e.Get("noise_amplitude_m").AsFloat(10f),
                noise_frequency = e.Get("noise_frequency").AsFloat(0.005f),
                max_slope_deg = e.Get("max_slope_deg").AsFloat(45f)
            };
        }

        private static GenerativeGroundConfig ParseGround(ModJsonValue g)
        {
            if (g == null) return new GenerativeGroundConfig();
            return new GenerativeGroundConfig
            {
                shader_mode = g.Get("shader_mode").AsString() ?? "standard_dither",
                primary_color_hex = g.Get("primary_color_hex").AsString() ?? "#15803d",
                secondary_color_hex = g.Get("secondary_color_hex").AsString() ?? "#22c55e",
                slope_color_hex = g.Get("slope_color_hex").AsString() ?? "#6b7280",
                pattern_scale = g.Get("pattern_scale").AsFloat(1f),
                pattern_intensity = g.Get("pattern_intensity").AsFloat(0.5f),
                normal_micro_roughness = g.Get("normal_micro_roughness").AsFloat(0.2f)
            };
        }

        // ---------------------------------------------------------------- Assets

        private static void LoadAsset(
            ModInfo mod,
            ModContentEntry entry,
            HomesteaderTerrainGenerator generator,
            IModAssetResolver assetResolver,
            ModLoadResult result,
            Action<string> log)
        {
            foreach (string file in ModFileResolver.ResolveFiles(mod, entry.Path, ".json"))
            {
                // Skip stage manifests under stages/ (stages are resources owned by the growth/structure group, not top-level catalog assets)
                string normPath = file.Replace('\\', '/');
                if (normPath.Contains("/stages/"))
                    continue;

                string text = File.ReadAllText(file);
                if (!ModJson.TryParse(text, out ModJsonValue root, out string error))
                {
                    mod.Warnings.Add($"Asset file '{file}' is not valid JSON - {error}");
                    continue;
                }

                string localId = root.Get("id").AsString() ?? Path.GetFileNameWithoutExtension(file);
                string category = root.Get("category").AsString() ?? entry.Type;

                // Namespacing: ids are namespaced by mod so two mods (or a mod
                // and the core game) can both ship an id like "tree_oak" without
                // colliding. The qualified id is what registries key on.
                string ns = NamespaceFor(mod, root);

                var summary = new AssetManifestSummary
                {
                    id = localId,
                    ns = ns,
                    name = root.Get("name").AsString() ?? localId,
                    category = category,
                    is_spawnable = root.Get("properties").Get("is_spawnable").AsBool(false)
                        || root.Get("is_spawnable").AsBool(false), // accept the flat form too
                    spawning = ParseSpawning(root["spawning"])
                };

                // A spawnable asset must name at least one biome; if it doesn't,
                // say so loudly rather than silently never placing it.
                if (summary.is_spawnable &&
                    (summary.spawning == null || summary.spawning.biomes.Length == 0))
                {
                    mod.Warnings.Add(
                        $"Asset '{localId}' sets is_spawnable but declares no 'spawning.biomes'; " +
                        "it will not be placed in the world.");
                }

                // Bind a prefab if the mod ships or otherwise resolves one.
                if (assetResolver != null &&
                    assetResolver.TryResolvePrefab(mod, root, out GameObject prefab))
                {
                    summary.prefab = prefab;
                }

                // Growth groups (which own what plants them and what they drop) are
                // registered independently of terrain generation: they drive gameplay,
                // not world scattering.
                if (GrowthGroup.TryParse(mod, Path.GetDirectoryName(file), root, ns, assetResolver,
                        out GrowthGroup growthGroup, msg => mod.Warnings.Add($"Growth group '{localId}': {msg}")))
                {
                    if (!GrowthRegistry.Register(growthGroup))
                        mod.Warnings.Add($"Growth group '{growthGroup.QualifiedId}' already registered; this copy is ignored.");
                }

                // No terrain generator: nothing to scatter into. Growth groups and use
                // behaviours were registered above; the asset itself stays data-only.
                if (generator == null)
                    continue;

                // Duplicate qualified ids are rejected the same way biomes are:
                // first one wins, later ones are reported and skipped.
                if (generator.registeredAssets.Any(a => a.QualifiedId == summary.QualifiedId))
                {
                    mod.Warnings.Add($"Asset '{summary.QualifiedId}' already registered; this copy is ignored.");
                    continue;
                }

                generator.registeredAssets.Add(summary);
                result.AssetsRegistered++;
            }
        }

        /// <summary>
        /// The namespace an asset belongs to. Mods may set an explicit
        /// "namespace" (or "ns") field to group several mods under one brand;
        /// otherwise the mod's own id is used. Core/built-in content is "core".
        /// </summary>
        private static string NamespaceFor(ModInfo mod, ModJsonValue root)
        {
            string explicitNs = root.Get("namespace").AsString() ?? root.Get("ns").AsString();
            if (!string.IsNullOrWhiteSpace(explicitNs))
                return explicitNs.Trim().ToLowerInvariant();

            return mod?.Manifest?.Id ?? "core";
        }

        private static AssetSpawningConfig ParseSpawning(ModJsonValue s)
        {
            if (s == null) return null;
            return new AssetSpawningConfig
            {
                biomes = s.Get("biomes").AsStringList().ToArray(),
                density_per_hectare = s.Get("density_per_hectare").AsFloat(100f),
                clustering = s.Get("clustering").AsFloat(0.5f),
                elevation_min_m = s.Get("elevation_min_m").AsFloat(-100f),
                elevation_max_m = s.Get("elevation_max_m").AsFloat(500f),
                slope_max_deg = s.Get("slope_max_deg").AsFloat(45f),
                scale_min = s.Get("scale_min").AsFloat(0.8f),
                scale_max = s.Get("scale_max").AsFloat(1.2f),
                align_to_surface_normal = s.Get("align_to_surface_normal").AsBool(false)
            };
        }
    }

    /// <summary>
    /// Resolves a mod's declared asset/prefab reference into an actual
    /// GameObject. The core build ships a null resolver; projects that adopt
    /// Addressables, AssetBundles, or runtime GLB/OBJ import plug in their own.
    /// </summary>
    public interface IModAssetResolver
    {
        bool TryResolvePrefab(ModInfo mod, ModJsonValue assetManifest, out GameObject prefab);
    }

    /// <summary>Default resolver: always declines, so mods load data-only.</summary>
    public sealed class NullModAssetResolver : IModAssetResolver
    {
        public bool TryResolvePrefab(ModInfo mod, ModJsonValue assetManifest, out GameObject prefab)
        {
            prefab = null;
            return false;
        }
    }
}
