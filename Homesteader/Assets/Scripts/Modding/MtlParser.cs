using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using UnityEngine;

namespace Homesteader.Modding
{
    /// <summary>
    /// Runtime Wavefront MTL parser: the companion to ObjMeshParser.
    ///
    /// Reads `newmtl` blocks and pulls the two things that matter for display:
    ///   * `Kd`       - diffuse colour. 365 of the catalog's 403 MTLs carry one.
    ///   * `map_Kd`   - a texture path, which the pipeline points at the shared
    ///                  atlas (assets/textures/palettes/T_Homesteader_Palette.png)
    ///                  via a relative "../../textures/..." reference.
    ///
    /// Textures are loaded from disk when they exist next to the model; otherwise
    /// the material keeps its Kd tint, which still looks correct. Names are
    /// de-duplicated so the same MTL parsed for many models reuses materials.
    /// </summary>
    public static class MtlParser
    {
        private static readonly Dictionary<string, Material> cache =
            new Dictionary<string, Material>(StringComparer.OrdinalIgnoreCase);

        private sealed class MtlDef
        {
            public string Name;
            public Color Diffuse = new Color(0.8f, 0.8f, 0.8f, 1f);
            public bool HasDiffuse;
            public string TexturePath;
        }

        /// <summary>
        /// Loads the .mtl sitting beside <paramref name="objPath"/> (matched by
        /// name first, then any single .mtl in the folder) and returns materials
        /// keyed by their `newmtl` name. Returns an empty map when none is found.
        /// </summary>
        public static Dictionary<string, Material> LoadFor(string objPath)
        {
            var result = new Dictionary<string, Material>(StringComparer.OrdinalIgnoreCase);

            if (string.IsNullOrEmpty(objPath) || !File.Exists(objPath))
                return result;

            string dir = Path.GetDirectoryName(objPath);
            if (string.IsNullOrEmpty(dir) || !Directory.Exists(dir))
                return result;

            string mtlPath = FindMtl(dir, Path.GetFileNameWithoutExtension(objPath));
            if (mtlPath == null)
                return result;

            foreach (MtlDef def in ParseFile(mtlPath))
            {
                Material mat = ToMaterial(def, dir, mtlPath);
                if (mat != null && def.Name != null)
                    result[def.Name] = mat;
            }

            return result;
        }

        private static string FindMtl(string dir, string objStem)
        {
            // Same stem first, then the model-named MTL, then a lone .mtl.
            string sameStem = Path.Combine(dir, objStem + ".mtl");
            if (File.Exists(sameStem)) return sameStem;

            foreach (string candidate in Directory.GetFiles(dir, "*.mtl"))
            {
                if (candidate.EndsWith(objStem + ".mtl", StringComparison.OrdinalIgnoreCase))
                    return candidate;
            }

            string[] all = Directory.GetFiles(dir, "*.mtl");
            return all.Length > 0 ? all[0] : null;
        }

        private static IEnumerable<MtlDef> ParseFile(string path)
        {
            string[] lines;
            try
            {
                lines = File.ReadAllLines(path);
            }
            catch
            {
                yield break;
            }

            MtlDef current = null;

            foreach (string raw in lines)
            {
                string line = raw.Trim();
                if (line.Length == 0 || line[0] == '#')
                    continue;

                string[] parts = line.Split(new[] { ' ', '\t' }, StringSplitOptions.RemoveEmptyEntries);
                if (parts.Length == 0) continue;

                switch (parts[0])
                {
                    case "newmtl":
                        if (current != null) yield return current;
                        current = new MtlDef { Name = parts.Length >= 2 ? parts[1] : null };
                        break;

                    case "Kd":
                        if (current != null && parts.Length >= 4)
                        {
                            current.Diffuse = new Color(
                                ParseFloat(parts[1]), ParseFloat(parts[2]), ParseFloat(parts[3]), 1f);
                            current.HasDiffuse = true;
                        }
                        break;

                    case "map_Kd":
                        if (current != null && parts.Length >= 2)
                        {
                            // The path may contain spaces; the filename is last.
                            current.TexturePath = parts[parts.Length - 1];
                        }
                        break;
                }
            }

            if (current != null) yield return current;
        }

        private static Material ToMaterial(MtlDef def, string modelDir, string mtlPath)
        {
            string cacheKey = $"{mtlPath}::{def.Name}";
            if (cache.TryGetValue(cacheKey, out Material cached) && cached != null)
                return cached;

            Shader shader = Shader.Find("Universal Render Pipeline/Lit")
                            ?? Shader.Find("Standard")
                            ?? Shader.Find("Unlit/Texture");

            if (shader == null)
                return null;

            var mat = new Material(shader) { name = def.Name ?? "mod_material" };

            if (mat.HasProperty("_BaseColor"))
                mat.SetColor("_BaseColor", def.Diffuse);
            else if (mat.HasProperty("_Color"))
                mat.color = def.Diffuse;

            if (!string.IsNullOrEmpty(def.TexturePath))
            {
                Texture2D tex = TryLoadTexture(def.TexturePath, modelDir, mtlPath);
                if (tex != null)
                {
                    if (mat.HasProperty("_BaseMap")) mat.SetTexture("_BaseMap", tex);
                    if (mat.HasProperty("_MainTex")) mat.SetTexture("_MainTex", tex);
                }
            }

            cache[cacheKey] = mat;
            return mat;
        }

        /// <summary>
        /// Resolves a map_Kd path against the model folder, then the MTL's folder.
        /// Paths in this project are relative and walk up with "../../", so both
        /// are tried before giving up.
        /// </summary>
        private static Texture2D TryLoadTexture(string refPath, string modelDir, string mtlPath)
        {
            string normalized = refPath.Replace('\\', '/');

            foreach (string baseDir in new[] { modelDir, Path.GetDirectoryName(mtlPath) })
            {
                if (string.IsNullOrEmpty(baseDir)) continue;

                try
                {
                    string full = Path.GetFullPath(Path.Combine(baseDir, normalized));
                    if (!File.Exists(full)) continue;

                    byte[] bytes = File.ReadAllBytes(full);
                    var tex = new Texture2D(2, 2, TextureFormat.RGBA32, false);
                    if (tex.LoadImage(bytes))
                    {
                        tex.name = Path.GetFileName(full);
                        return tex;
                    }
                }
                catch
                {
                    // A broken texture path must never fail the whole load.
                }
            }

            return null;
        }

        private static float ParseFloat(string s) =>
            float.TryParse(s, NumberStyles.Float, CultureInfo.InvariantCulture, out float v) ? v : 0.8f;

        public static void ClearCache() => cache.Clear();
    }
}
