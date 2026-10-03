using System;
using System.Collections.Generic;

namespace Homesteader.Modding
{
    /// <summary>
    /// The kinds of content a mod can contribute. A single mod may declare
    /// more than one type (e.g. a biome mod that also ships the ground textures
    /// and the trees that grow in it), so this is a flags-style registry rather
    /// than a single enum value.
    ///
    /// Kept as plain string constants (not an enum) so a mod author can ship a
    /// newer content type than this build knows about without the manifest
    /// failing to parse - unknown types are reported as warnings and skipped,
    /// never treated as fatal.
    /// </summary>
    public static class ModContentType
    {
        public const string Structure = "structure";     // buildings, cabins, barns, sheds
        public const string Building = "building";       // construction parts and containers: framing, doors, crates, boxes
        public const string Biome = "biome";             // terrain regions + ground shading
        public const string Food = "food";               // edible items
        public const string Ingredient = "ingredient";   // cooking inputs
        public const string Farming = "farming";         // crops, seeds, produce
        public const string Ranching = "ranching";       // livestock, feed, byproducts
        public const string Logging = "logging";         // trees, timber, firewood
        public const string Fishing = "fishing";         // fish, rods, tackle
        public const string Tool = "tool";               // hand + power tools
        public const string Electricity = "electricity"; // generation, storage, wiring
        public const string Water = "water";             // wells, pumps, tanks, pipes
        public const string Waste = "waste";             // septic, sewage, refuse
        public const string Internet = "internet";       // connectivity hardware
        public const string Vehicle = "vehicle";         // trucks, tractors, trailers
        public const string Appliance = "appliance";     // powered household goods
        public const string Material = "material";       // raw building materials
        public const string Fuel = "fuel";               // combustible / energy stores
        public const string Ped = "ped";                 // NPC villagers / characters
        public const string Texture = "texture";         // standalone ground/foliage textures
        public const string Recipe = "recipe";           // crafting / cooking recipes
        public const string Script = "script";           // reserved: code-level extension
        public const string GameRules = "gamerules";     // planting/harvest rules + farmland zones as data
        public const string AnimalAi = "animal_ai";      // animal behaviour rules (needs, senses, behaviours) as data
        public const string Radio = "radio";             // Steadify radio stations (speakers, segments, sentence banks) as data

        /// <summary>Every content type this build understands.</summary>
        public static readonly string[] All =
        {
            Structure, Building, Biome, Food, Ingredient, Farming, Ranching, Logging, Fishing,
            Tool, Electricity, Water, Waste, Internet, Vehicle, Appliance, Material,
            Fuel, Ped, Texture, Recipe, Script, GameRules, AnimalAi, Radio
        };

        private static readonly HashSet<string> Known = new HashSet<string>(All, StringComparer.OrdinalIgnoreCase);

        public static bool IsKnown(string type) => !string.IsNullOrEmpty(type) && Known.Contains(type);
    }

    /// <summary>
    /// One declared content payload inside a mod manifest. The mod author
    /// points at a file (relative to the mod root) and states what it is.
    /// </summary>
    public sealed class ModContentEntry
    {
        /// <summary>"biome" / "structure" / "food" / ... See ModContentType.</summary>
        public string Type;

        /// <summary>
        /// Path to the payload, relative to the mod root. May be a wildcard
        /// like "assets/structure_*.json" to pull in a group.
        /// </summary>
        public string Path;

        /// <summary>Optional subcategory / grouping hint (e.g. "cabin", "wildlife").</summary>
        public string Group;

        /// <summary>
        /// Optional per-entry override applied after the shared manifest
        /// defaults - lets one mod ship a biome and an item from the same file
        /// set with different metadata.
        /// </summary>
        public ModJsonValue Extra;

        public override string ToString() => $"{Type}:{Path}";
    }

    /// <summary>
    /// A fully parsed mod manifest (mod.json at the root of a mod folder/zip).
    /// </summary>
    public sealed class ModManifest
    {
        // --- Identity ---
        public string Id;                 // required, unique, snake_case
        public string Name;               // display name
        public string Version = "1.0.0";  // semver-ish
        public string Author = "Unknown";
        public string Description;
        public string ReleaseDate;        // ISO-8601 (YYYY-MM-DD)
        public string Homepage;
        public string Icon;               // relative path to a preview image

        // --- Compatibility / dependency wiring ---
        public string GameVersionMin;     // lowest supported game version
        public string GameVersionMax;     // highest supported game version (optional)
        public readonly List<string> LoadAfter = new List<string>();
        public readonly List<string> Dependencies = new List<string>();

        // --- Content ---
        public readonly List<ModContentEntry> Contents = new List<ModContentEntry>();

        /// <summary>Raw parsed tree, for mod types that read their own custom block.</summary>
        public ModJsonValue Raw;

        /// <summary>Where the manifest was found on disk (inside the staging dir).</summary>
        public string ManifestPath;

        /// <summary>True when the manifest declared at least one content entry.</summary>
        public bool HasContent => Contents.Count > 0;

        public IEnumerable<string> DeclaredTypes()
        {
            var seen = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
            foreach (var entry in Contents)
            {
                if (entry.Type != null && seen.Add(entry.Type))
                    yield return entry.Type;
            }
        }

        public override string ToString() => $"{Id} v{Version} ({Author})";
    }

    /// <summary>
    /// A discovered mod on disk, before or after its manifest has been parsed.
    /// Tracks the search order and any problems found.
    /// </summary>
    public sealed class ModInfo
    {
        /// <summary>Folder or zip file name (not the manifest id - those can differ).</summary>
        public string SourceName;

        /// <summary>Absolute path to the mod folder, or to the extracted zip staging dir.</summary>
        public string RootPath;

        /// <summary>True when the source was a .zip this build extracted to staging.</summary>
        public bool WasZipped;

        /// <summary>Parsed manifest; null when parsing failed.</summary>
        public ModManifest Manifest;

        /// <summary>Load order index, ascending = loads earlier.</summary>
        public int Order;

        public bool IsValid => Manifest != null;

        /// <summary>Non-fatal problems (unknown content types, missing optional files).</summary>
        public readonly List<string> Warnings = new List<string>();

        /// <summary>Fatal problems; a mod with any of these is not loaded.</summary>
        public readonly List<string> Errors = new List<string>();

        public string Id => Manifest?.Id ?? SourceName;

        /// <summary>True when this mod or its parent folder ends with '_disabled' or '.disabled'.</summary>
        public bool IsDisabled;

        /// <summary>Optional category name (from parent folder or manifest).</summary>
        public string Category;

        /// <summary>Path to parent category folder, if organized in a category subdirectory.</summary>
        public string CategoryFolderPath;

        public override string ToString() => $"{SourceName} -> {(IsValid ? Manifest.Id : "<invalid>")}{(IsDisabled ? " [DISABLED]" : "")}";
    }
}
