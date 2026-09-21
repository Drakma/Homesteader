using System;
using System.Collections.Generic;
using System.IO;
using System.IO.Compression;
using System.Linq;
using System.Security.Cryptography;
using System.Text;

namespace Homesteader.Modding
{
    /// <summary>
    /// Scans the mods directory and produces a list of discovered ModInfo
    /// entries, extracting .zip archives into a staging directory first.
    ///
    /// Layout on disk:
    ///   &lt;ModsRoot&gt;/
    ///     my_biome_mod/            &lt;- folder mod
    ///       mod.json
    ///       ...
    ///     some_pack.zip            &lt;- archive mod
    ///       mod.json               (at the zip root OR at a single top-level folder)
    ///       ...
    ///     _staging/                &lt;- extracted archives + index (managed by us)
    ///
    /// Both shapes are accepted. A .zip whose entries all live under one
    /// top-level folder is flattened, so modders who right-click > "Send to >
    /// Compressed folder" on a folder still get a valid mod.
    /// </summary>
    public static class ModDiscovery
    {
        public const string StagingFolderName = "_staging";
        public const string DisabledSuffix = "_disabled";
        public const string LegacyDisabledSuffix = ".disabled";

        /// <summary>
        /// Checks whether a folder or archive name indicates it is disabled.
        /// </summary>
        public static bool IsDisabledName(string name)
        {
            if (string.IsNullOrEmpty(name)) return false;
            return name.EndsWith(DisabledSuffix, StringComparison.OrdinalIgnoreCase) ||
                   name.EndsWith(LegacyDisabledSuffix, StringComparison.OrdinalIgnoreCase);
        }

        /// <summary>
        /// Checks if a path or any of its ancestor directories up the tree ends with '_disabled' or '.disabled'.
        /// </summary>
        public static bool IsPathDisabled(string path)
        {
            if (string.IsNullOrEmpty(path)) return false;
            try
            {
                var dir = new DirectoryInfo(path);
                while (dir != null)
                {
                    if (IsDisabledName(dir.Name)) return true;
                    dir = dir.Parent;
                }
            }
            catch { }
            return false;
        }

        /// <summary>
        /// Strips '_disabled' or '.disabled' from a name.
        /// </summary>
        public static string StripDisabledSuffix(string name)
        {
            if (string.IsNullOrEmpty(name)) return name;
            if (name.EndsWith(DisabledSuffix, StringComparison.OrdinalIgnoreCase))
                return name.Substring(0, name.Length - DisabledSuffix.Length);
            if (name.EndsWith(LegacyDisabledSuffix, StringComparison.OrdinalIgnoreCase))
                return name.Substring(0, name.Length - LegacyDisabledSuffix.Length);
            return name;
        }

        /// <summary>
        /// Renames a folder (category or mod subfolder) to append or remove '_disabled'.
        /// Also renames any accompanying .meta file (in Unity Assets directory).
        /// Returns the new folder path, or original path if failed.
        /// </summary>
        public static string SetFolderDisabled(string folderPath, bool disable, Action<string> log = null)
        {
            if (string.IsNullOrEmpty(folderPath) || !Directory.Exists(folderPath))
            {
                log?.Invoke($"[Mods] Cannot toggle folder, path does not exist: {folderPath}");
                return folderPath;
            }

            folderPath = folderPath.TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar);
            string parentDir = Path.GetDirectoryName(folderPath);
            string folderName = Path.GetFileName(folderPath);

            bool currentlyDisabled = IsDisabledName(folderName);
            if (disable == currentlyDisabled)
                return folderPath; // already in desired state

            string newFolderName = disable ? (folderName + DisabledSuffix) : StripDisabledSuffix(folderName);
            string targetPath = Path.Combine(parentDir, newFolderName);

            try
            {
                // Rename folder
                Directory.Move(folderPath, targetPath);
                log?.Invoke($"[Mods] Renamed folder '{folderName}' -> '{newFolderName}'");

                // Rename .meta file if present
                string metaOld = folderPath + ".meta";
                string metaNew = targetPath + ".meta";
                if (File.Exists(metaOld))
                {
                    if (File.Exists(metaNew)) File.Delete(metaNew);
                    File.Move(metaOld, metaNew);
                    log?.Invoke($"[Mods] Renamed meta '{Path.GetFileName(metaOld)}' -> '{Path.GetFileName(metaNew)}'");
                }

#if UNITY_EDITOR
                UnityEditor.AssetDatabase.Refresh();
#endif
                return targetPath;
            }
            catch (Exception ex)
            {
                log?.Invoke($"[Mods] Failed to rename '{folderName}': {ex.Message}");
                return folderPath;
            }
        }

        /// <summary>
        /// Enumerates candidate mod sources under <paramref name="modsRoot"/>.
        /// Discovers both enabled and disabled mods so UI can display all of them.
        /// </summary>
        public static List<ModInfo> Discover(string modsRoot, Action<string> log = null)
        {
            var results = new List<ModInfo>();

            if (string.IsNullOrEmpty(modsRoot) || !Directory.Exists(modsRoot))
            {
                log?.Invoke($"[Mods] Mods directory not found: {modsRoot}");
                return results;
            }

            foreach (string dir in Directory.GetDirectories(modsRoot))
            {
                string name = Path.GetFileName(dir);

                if (string.Equals(name, StagingFolderName, StringComparison.OrdinalIgnoreCase))
                    continue; // our own extraction cache
                if (name.StartsWith(".", StringComparison.Ordinal))
                    continue; // hidden / .git etc.

                bool isFolderDisabled = IsDisabledName(name) || IsPathDisabled(dir);

                // Case 1: Direct mod folder (contains mod.json)
                string manifestPath = Path.Combine(dir, ModManifestParser.ManifestFileNameFor);
                if (File.Exists(manifestPath))
                {
                    results.Add(new ModInfo
                    {
                        SourceName = name,
                        RootPath = dir,
                        WasZipped = false,
                        IsDisabled = isFolderDisabled
                    });
                    if (isFolderDisabled)
                        log?.Invoke($"[Mods] Discovered disabled mod folder '{name}'.");
                }
                else
                {
                    // Case 2: Category folder containing mod subdirectories
                    string[] subDirs = Directory.GetDirectories(dir);
                    bool foundSubMod = false;
                    foreach (string subDir in subDirs)
                    {
                        string subName = Path.GetFileName(subDir);
                        if (subName.StartsWith(".", StringComparison.Ordinal)) continue;

                        string subManifest = Path.Combine(subDir, ModManifestParser.ManifestFileNameFor);
                        if (File.Exists(subManifest))
                        {
                            foundSubMod = true;
                            bool isSubDisabled = isFolderDisabled || IsDisabledName(subName) || IsPathDisabled(subDir);
                            results.Add(new ModInfo
                            {
                                SourceName = subName,
                                RootPath = subDir,
                                WasZipped = false,
                                IsDisabled = isSubDisabled,
                                Category = StripDisabledSuffix(name),
                                CategoryFolderPath = dir
                            });
                            if (isSubDisabled)
                                log?.Invoke($"[Mods] Discovered disabled mod '{subName}' in '{name}'.");
                        }
                    }

                    if (!foundSubMod)
                    {
                        // Folder without mod.json, keep candidate so validation/UI can inspect it
                        results.Add(new ModInfo
                        {
                            SourceName = name,
                            RootPath = dir,
                            WasZipped = false,
                            IsDisabled = isFolderDisabled
                        });
                    }
                }
            }

            foreach (string zip in Directory.GetFiles(modsRoot, "*.zip"))
            {
                string name = Path.GetFileNameWithoutExtension(zip);
                bool isZipDisabled = IsDisabledName(name);

                try
                {
                    string extracted = ExtractZip(zip, modsRoot, log);
                    results.Add(new ModInfo
                    {
                        SourceName = name,
                        RootPath = extracted,
                        WasZipped = true,
                        IsDisabled = isZipDisabled
                    });
                    if (isZipDisabled)
                        log?.Invoke($"[Mods] Discovered disabled mod archive '{Path.GetFileName(zip)}'.");
                }
                catch (Exception ex)
                {
                    var broken = new ModInfo { SourceName = name, RootPath = zip, WasZipped = true, IsDisabled = isZipDisabled };
                    broken.Errors.Add($"Failed to extract '{Path.GetFileName(zip)}': {ex.Message}");
                    results.Add(broken);
                }
            }

            return results;
        }

        /// <summary>
        /// Extracts a mod zip into &lt;modsRoot&gt;/_staging/&lt;name&gt;. Reuses an
        /// existing extraction when the archive hasn't changed (hash match) so
        /// startup stays fast on repeat runs.
        /// </summary>
        private static string ExtractZip(string zipPath, string modsRoot, Action<string> log)
        {
            string stagingRoot = Path.Combine(modsRoot, StagingFolderName);
            Directory.CreateDirectory(stagingRoot);

            string hash = ShortHash(zipPath);
            string target = Path.Combine(stagingRoot, hash);
            string stampFile = target + ".hash";

            if (Directory.Exists(target) && File.Exists(stampFile) &&
                File.ReadAllText(stampFile) == hash)
            {
                log?.Invoke($"[Mods] Reusing cached extraction for '{Path.GetFileName(zipPath)}'.");
                return ResolveManifestRoot(target);
            }

            if (Directory.Exists(target))
                Directory.Delete(target, true);

            Directory.CreateDirectory(target);
            ZipFile.ExtractToDirectory(zipPath, target);
            File.WriteAllText(stampFile, hash);

            log?.Invoke($"[Mods] Extracted '{Path.GetFileName(zipPath)}' to staging.");
            return ResolveManifestRoot(target);
        }

        /// <summary>
        /// Handles the "everything is inside one folder" zip shape by returning
        /// the single top-level subfolder when it is the only child.
        /// </summary>
        private static string ResolveManifestRoot(string extractedDir)
        {
            if (File.Exists(Path.Combine(extractedDir, ModManifestParser.ManifestFileNameFor)))
                return extractedDir;

            string[] dirs = Directory.GetDirectories(extractedDir);
            if (dirs.Length == 1 &&
                File.Exists(Path.Combine(dirs[0], ModManifestParser.ManifestFileNameFor)))
            {
                return dirs[0];
            }

            return extractedDir;
        }

        private static string ShortHash(string filePath)
        {
            using var sha = SHA1.Create();
            using var stream = File.OpenRead(filePath);
            byte[] hash = sha.ComputeHash(stream);
            var sb = new StringBuilder(12);
            for (int i = 0; i < 6; i++)
                sb.Append(hash[i].ToString("x2"));
            return sb.ToString();
        }

        /// <summary>
        /// Orders mods so that declared dependencies load first, then applies
        /// load_after ordering, then falls back to alphabetical for stability.
        /// Cycles are broken deterministically and reported as warnings.
        /// </summary>
        public static void ResolveLoadOrder(List<ModInfo> mods, Action<string> log = null)
        {
            var byId = new Dictionary<string, ModInfo>(StringComparer.OrdinalIgnoreCase);
            foreach (ModInfo mod in mods)
            {
                if (!mod.IsValid)
                    continue;
                if (byId.ContainsKey(mod.Manifest.Id))
                {
                    mod.Warnings.Add($"Duplicate mod id '{mod.Manifest.Id}' - the first one wins.");
                    continue;
                }
                byId[mod.Manifest.Id] = mod;
            }

            var ordered = new List<ModInfo>();
            var visited = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
            var inProgress = new HashSet<string>(StringComparer.OrdinalIgnoreCase);

            // Deterministic base ordering keeps results reproducible across runs.
            var roots = mods
                .Where(m => m.IsValid)
                .OrderBy(m => m.Manifest.Id, StringComparer.OrdinalIgnoreCase)
                .ToList();

            void Visit(ModInfo mod)
            {
                string id = mod.Manifest.Id;
                if (visited.Contains(id))
                    return;

                if (inProgress.Contains(id))
                {
                    mod.Warnings.Add($"Dependency cycle detected at '{id}'; ordering truncated.");
                    return;
                }

                inProgress.Add(id);

                foreach (string dep in mod.Manifest.Dependencies)
                {
                    if (byId.TryGetValue(dep, out ModInfo depMod))
                        Visit(depMod);
                    else
                        mod.Warnings.Add($"Missing dependency '{dep}'.");
                }

                foreach (string after in mod.Manifest.LoadAfter)
                {
                    if (byId.TryGetValue(after, out ModInfo afterMod))
                        Visit(afterMod);
                }

                inProgress.Remove(id);
                visited.Add(id);
                ordered.Add(mod);
            }

            foreach (ModInfo mod in roots)
                Visit(mod);

            // Mods that failed validation keep their slot at the end, so error
            // reporting stays in a stable order.
            foreach (ModInfo mod in mods.Where(m => !m.IsValid))
                ordered.Add(mod);

            for (int i = 0; i < ordered.Count; i++)
                ordered[i].Order = i;

            mods.Clear();
            mods.AddRange(ordered);
        }

        /// <summary>Gets or creates the default mods directory (next to the game data).</summary>
        public static string EnsureModsDirectory(string modsRoot)
        {
            if (!Directory.Exists(modsRoot))
                Directory.CreateDirectory(modsRoot);
            return modsRoot;
        }
    }
}
