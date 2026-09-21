using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;

namespace Homesteader.Modding
{
    /// <summary>
    /// Resolves the file paths a content entry refers to, relative to a mod's
    /// root folder. Supports three forms so modders aren't forced to list every
    /// file individually:
    ///
    ///   "biomes/river.json"      exact file
    ///   "biomes/*.json"          wildcard within one folder
    ///   "biomes"  or  "biomes/"  every matching file under that folder, recursively
    ///
    /// All paths are confined to the mod root: any entry that escapes it (via
    /// ".." or an absolute path) is rejected, so a malicious manifest cannot
    /// read files elsewhere on disk.
    /// </summary>
    public static class ModFileResolver
    {
        /// <summary>
        /// Expands a content entry path into concrete files on disk.
        /// Returns an empty list (never throws) when nothing matches.
        /// </summary>
        public static List<string> ResolveFiles(ModInfo mod, string relativePath, string extension)
        {
            var found = new List<string>();

            if (mod == null || string.IsNullOrEmpty(mod.RootPath) || string.IsNullOrEmpty(relativePath))
                return found;

            string root = Path.GetFullPath(mod.RootPath);

            if (!TryResolveSafe(root, relativePath, out string resolved))
            {
                mod.Warnings.Add($"Content path '{relativePath}' escapes the mod folder and was ignored.");
                return found;
            }

            if (File.Exists(resolved))
            {
                if (MatchesExtension(resolved, extension))
                    found.Add(resolved);
                return found;
            }

            // Directory form: recurse. Wildcard form: split into dir + pattern.
            string searchDir = resolved;
            string pattern = "*";

            if (resolved.Contains('*'))
            {
                searchDir = Path.GetDirectoryName(resolved) ?? root;
                pattern = Path.GetFileName(resolved);

                if (!Directory.Exists(searchDir))
                {
                    mod.Warnings.Add($"Content path '{relativePath}' points at a missing folder.");
                    return found;
                }
            }
            else if (!Directory.Exists(resolved))
            {
                mod.Warnings.Add($"Content path '{relativePath}' does not exist.");
                return found;
            }

            try
            {
                foreach (string file in Directory.EnumerateFiles(searchDir, pattern, SearchOption.AllDirectories))
                {
                    string full = Path.GetFullPath(file);
                    if (!IsWithin(root, full))
                        continue; // belt-and-braces against symlink tricks
                    if (MatchesExtension(full, extension))
                        found.Add(full);
                }
            }
            catch (Exception ex)
            {
                mod.Warnings.Add($"Failed to enumerate '{relativePath}': {ex.Message}");
            }

            return found.OrderBy(f => f, StringComparer.OrdinalIgnoreCase).ToList();
        }

        /// <summary>
        /// Resolves a plain (non-wildcard) reference to an absolute path, or
        /// null when it's missing or unsafe.
        /// </summary>
        public static string ResolveAssetPath(ModInfo mod, string relativePath)
        {
            if (mod == null || string.IsNullOrEmpty(mod.RootPath) || string.IsNullOrEmpty(relativePath))
                return null;

            string root = Path.GetFullPath(mod.RootPath);
            if (!TryResolveSafe(root, relativePath, out string resolved))
                return null;

            return File.Exists(resolved) ? resolved : null;
        }

        private static bool TryResolveSafe(string root, string relativePath, out string resolved)
        {
            resolved = null;
            try
            {
                string combined = Path.GetFullPath(Path.Combine(root, relativePath));
                if (!IsWithin(root, combined))
                    return false;

                resolved = combined;
                return true;
            }
            catch
            {
                return false;
            }
        }

        private static bool IsWithin(string root, string candidate)
        {
            string normalizedRoot = root.TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar)
                                    + Path.DirectorySeparatorChar;
            return candidate.StartsWith(normalizedRoot, StringComparison.OrdinalIgnoreCase)
                   || string.Equals(candidate, root, StringComparison.OrdinalIgnoreCase);
        }

        private static bool MatchesExtension(string file, string extension)
        {
            if (string.IsNullOrEmpty(extension))
                return true;
            return file.EndsWith(extension, StringComparison.OrdinalIgnoreCase);
        }
    }
}
