using System;
using System.Collections.Generic;
using System.Text.RegularExpressions;

namespace Homesteader.Modding
{
    /// <summary>
    /// Turns a raw mod.json document into a validated ModManifest.
    ///
    /// Validation philosophy: a broken mod must never break the game. Anything
    /// that makes a mod's content unusable (missing id, no content entries) is
    /// recorded as an Error; anything merely suspicious (unknown content type,
    /// odd version string) is recorded as a Warning. ModManager logs both and
    /// decides whether the mod still loads.
    /// </summary>
    public static class ModManifestParser
    {
        private const string ManifestFileName = "mod.json";

        // Mod ids are used as dictionary keys and folder-safe names, so we
        // constrain them the same way the asset pipeline constrains item ids.
        private static readonly Regex IdPattern = new Regex("^[a-z0-9_]+$", RegexOptions.Compiled);

        public static string ManifestFileNameFor => ManifestFileName;

        /// <summary>
        /// Parses manifest text. Never throws; returns null and fills
        /// <paramref name="info"/>'s Errors list on failure.
        /// </summary>
        public static ModManifest Parse(string json, string manifestPath, ModInfo info)
        {
            if (!ModJson.TryParse(json, out ModJsonValue root, out string jsonError))
            {
                info?.Errors.Add($"{manifestPath}: invalid JSON - {jsonError}");
                return null;
            }

            if (!root.IsObject)
            {
                info?.Errors.Add($"{manifestPath}: manifest root must be a JSON object.");
                return null;
            }

            var manifest = new ModManifest { Raw = root, ManifestPath = manifestPath };
            var errors = info?.Errors ?? new List<string>();
            var warnings = info?.Warnings ?? new List<string>();

            // --- Required identity ---
            manifest.Id = root.RequireString("id", errors, manifestPath);
            if (manifest.Id != null && !IdPattern.IsMatch(manifest.Id))
            {
                errors.Add($"{manifestPath}: 'id' must be snake_case (a-z, 0-9, underscore); got '{manifest.Id}'.");
            }

            manifest.Name = root.Get("name").AsString() ?? manifest.Id;

            // --- Optional metadata (widely used, so parse defensively) ---
            manifest.Version = root.Get("version").AsString() ?? "1.0.0";
            manifest.Author = root.Get("author").AsString() ?? "Unknown";
            manifest.Description = root.Get("description").AsString();
            manifest.ReleaseDate = root.Get("date").AsString() ?? root.Get("release_date").AsString();
            manifest.Homepage = root.Get("homepage").AsString();
            manifest.Icon = root.Get("icon").AsString();

            if (!string.IsNullOrEmpty(manifest.ReleaseDate) &&
                !DateTime.TryParse(manifest.ReleaseDate, out _))
            {
                warnings.Add($"{manifestPath}: 'date' ('{manifest.ReleaseDate}') is not a recognized date.");
            }

            // --- Compatibility block (either flat or nested under "compatibility") ---
            ModJsonValue compat = root.Get("compatibility");
            manifest.GameVersionMin = root.Get("game_version_min").AsString()
                ?? root.Get("min_game_version").AsString()
                ?? compat.Get("min").AsString();
            manifest.GameVersionMax = root.Get("game_version_max").AsString()
                ?? root.Get("max_game_version").AsString()
                ?? compat.Get("max").AsString();

            AddStrings(manifest.LoadAfter, root["load_after"] ?? root["loadAfter"]);
            AddStrings(manifest.Dependencies, root["dependencies"] ?? root["requires"]);

            // --- Content declarations ---
            int declared = ParseContents(root, manifest, errors, warnings, manifestPath);

            if (manifest.Contents.Count == 0)
            {
                // Only fatal when the manifest declared nothing at all. If it
                // declared entries that were all filtered out (e.g. content
                // types from a newer game version), that's already reported as
                // warnings and the mod is simply inert, not broken.
                if (declared == 0)
                    errors.Add($"{manifestPath}: no usable 'contents' entries; nothing to load.");
                else
                    warnings.Add($"{manifestPath}: none of the {declared} declared content entries could be used; mod will load with no content.");
            }

            return manifest;
        }

        /// <summary>
        /// Reads the manifest's content declarations into the manifest.
        /// Returns how many entries were declared (before filtering), so the
        /// caller can tell "declared nothing" apart from "declared unknown".
        /// </summary>
        private static int ParseContents(
            ModJsonValue root,
            ModManifest manifest,
            List<string> errors,
            List<string> warnings,
            string manifestPath)
        {
            ModJsonValue contents = root["contents"];

            // Mods may declare a single "type" shorthand when they ship one kind
            // of content and don't want the contents[] boilerplate. We treat that
            // as one entry covering the whole mod root.
            if (contents == null)
            {
                string shorthand = root.Get("type").AsString();
                if (!string.IsNullOrEmpty(shorthand))
                {
                    contents = ModJsonValue.NewArray(new List<ModJsonValue>
                    {
                        MakeShorthandEntry(shorthand, root.Get("path").AsString())
                    });
                }
            }

            if (contents == null)
                return 0;

            if (!contents.IsArray)
            {
                errors.Add($"{manifestPath}: 'contents' must be an array.");
                return 0;
            }

            int declared = 0;

            foreach (ModJsonValue item in contents.Items)
            {
                if (!item.IsObject)
                {
                    warnings.Add($"{manifestPath}: ignored non-object entry in 'contents'.");
                    continue;
                }

                declared++;

                // Accept both a bare string ("biome") and the { type, path } object form.
                string type = item.Get("type").AsString() ?? item.AsString();
                string path = item.Get("path").AsString() ?? item.Get("file").AsString();
                string group = item.Get("group").AsString();

                if (string.IsNullOrEmpty(type))
                {
                    warnings.Add($"{manifestPath}: content entry missing 'type'; skipped.");
                    continue;
                }

                if (!ModContentType.IsKnown(type))
                {
                    // Unknown types are tolerated on purpose: a mod built for a
                    // later build of the game should still load everything else.
                    warnings.Add($"{manifestPath}: content entry declares unknown type '{type}'; entry skipped.");
                    continue;
                }

                if (string.IsNullOrEmpty(path))
                {
                    warnings.Add($"{manifestPath}: content entry '{type}' missing 'path'; skipped.");
                    continue;
                }

                manifest.Contents.Add(new ModContentEntry
                {
                    Type = type.ToLowerInvariant(),
                    Path = path.Replace('\\', '/'),
                    Group = group,
                    Extra = item
                });
            }

            return declared;
        }

        private static ModJsonValue MakeShorthandEntry(string type, string path)
        {
            var map = new Dictionary<string, ModJsonValue>(StringComparer.Ordinal)
            {
                ["type"] = ModJsonValue.NewString(type),
                ["path"] = ModJsonValue.NewString(path ?? ".")
            };
            return ModJsonValue.NewObject(map);
        }

        private static void AddStrings(List<string> target, ModJsonValue node)
        {
            if (node == null) return;
            foreach (string s in node.AsStringList())
            {
                if (!string.IsNullOrWhiteSpace(s))
                    target.Add(s);
            }
        }
    }
}
