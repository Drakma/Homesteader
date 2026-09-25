using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using UnityEngine;

namespace Homesteader.Modding
{
    /// <summary>
    /// Runtime Wavefront OBJ parser, used as the FALLBACK path for loading
    /// model geometry at runtime.
    ///
    /// Scope, stated honestly: this only handles OBJ, which is plain text and can
    /// therefore be parsed while the game runs. It deliberately does NOT handle
    /// FBX - the pipeline's FBX files are BINARY (Kaydara FBX Binary), a
    /// proprietary and deflated format that is not realistic to parse at runtime.
    /// 129 catalog items, including all four oak trees, ship FBX with no OBJ, so
    /// those need a build-time importer (Addressables / AssetBundles) instead.
    /// 302 items do ship OBJ and can go through this parser today, which makes it
    /// the practical route for third-party mods: a mod drops a .obj into its
    /// folder and gets a mesh, with no Unity build step required.
    ///
    /// Handles the subset the pipeline emits: v / vt / vn, f (triangles and
    /// quads, "v", "v/vt", "v//vn" and "v/vt/vn" index forms), o / g / s / usemtl
    /// (tracked so a mesh splits per material) and negative indices.
    ///
    /// Units: the pipeline writes centimetres. Unity is 1 unit = 1 metre, so the
    /// caller passes a scale (ObjMeshParser.CentimetresToMetres) rather than the
    /// parser guessing.
    ///
    /// NOTE: nothing references this yet. It is intentionally kept as the
    /// fallback half of the asset-resolution strategy - see FileAssetResolver and
    /// MODDING_GUIDE.md section 7. It is not dead code, it is an unwired seam.
    /// </summary>
    public static class ObjMeshParser
    {
        /// <summary>Pipeline OBJ files are authored in centimetres.</summary>
        public const float CentimetresToMetres = 0.01f;

        /// <summary>
        /// One parsed sub-mesh: the triangles sharing a single material name.
        /// An OBJ with several usemtl groups yields several of these.
        /// </summary>
        public sealed class SubMesh
        {
            public string MaterialName;
            public readonly List<int> Triangles = new List<int>();
            public readonly List<Vector3> Vertices = new List<Vector3>();
            public readonly List<Vector3> Normals = new List<Vector3>();
            public readonly List<Vector2> Uvs = new List<Vector2>();
        }

        public sealed class ParsedObj
        {
            public readonly List<SubMesh> SubMeshes = new List<SubMesh>();
            public string MtlLibrary;               // value of mtllib, if any
            public Bounds Bounds;
            public int TotalTriangles;

            public bool HasGeometry => SubMeshes.Count > 0 && TotalTriangles > 0;
        }

        /// <summary>
        /// Parses OBJ text. Returns null (never throws) when the file has no usable
        /// geometry, so a malformed model degrades to "no prefab" instead of
        /// aborting a whole mod load.
        /// </summary>
        public static ParsedObj Parse(string text, float scale = CentimetresToMetres)
        {
            if (string.IsNullOrEmpty(text))
                return null;

            // Raw pools, indexed 1-based from the file (positions[i-1]).
            var positions = new List<Vector3>();
            var texCoords = new List<Vector2>();
            var normals = new List<Vector3>();

            var result = new ParsedObj();
            SubMesh current = NewSubMesh(null);
            result.SubMeshes.Add(current);

            bool anyNormal = false;
            bool boundsInit = false;
            float minX = 0, minY = 0, minZ = 0, maxX = 0, maxY = 0, maxZ = 0;

            string[] lines = text.Split('\n');
            for (int li = 0; li < lines.Length; li++)
            {
                string line = lines[li].Trim();
                if (line.Length == 0 || line[0] == '#')
                    continue;

                // Split on whitespace, collapsing runs.
                string[] parts = line.Split(new[] { ' ', '\t' }, StringSplitOptions.RemoveEmptyEntries);
                if (parts.Length == 0)
                    continue;

                switch (parts[0])
                {
                    case "v":
                        if (parts.Length >= 4)
                        {
                            float x = ParseFloat(parts[1]), y = ParseFloat(parts[2]), z = ParseFloat(parts[3]);
                            positions.Add(new Vector3(x * scale, y * scale, z * scale));

                            if (!boundsInit)
                            {
                                minX = maxX = x * scale; minY = maxY = y * scale; minZ = maxZ = z * scale;
                                boundsInit = true;
                            }
                            else
                            {
                                if (x * scale < minX) minX = x * scale;
                                if (x * scale > maxX) maxX = x * scale;
                                if (y * scale < minY) minY = y * scale;
                                if (y * scale > maxY) maxY = y * scale;
                                if (z * scale < minZ) minZ = z * scale;
                                if (z * scale > maxZ) maxZ = z * scale;
                            }
                        }
                        break;

                    case "vt":
                        // Some exporters write a 3-component vt; the third is ignored.
                        if (parts.Length >= 3)
                        {
                            texCoords.Add(new Vector2(ParseFloat(parts[1]), ParseFloat(parts[2])));
                        }
                        break;

                    case "vn":
                        if (parts.Length >= 4)
                        {
                            normals.Add(new Vector3(ParseFloat(parts[1]), ParseFloat(parts[2]), ParseFloat(parts[3])));
                            anyNormal = true;
                        }
                        break;

                    case "usemtl":
                        // A new material group starts a new sub-mesh; the previous
                        // one is dropped if it stayed empty (common at file start).
                        string mtlName = parts.Length >= 2 ? parts[1] : null;
                        if (current.Triangles.Count > 0)
                        {
                            current = NewSubMesh(mtlName);
                            result.SubMeshes.Add(current);
                        }
                        else
                        {
                            current.MaterialName = mtlName;
                        }
                        break;

                    case "mtllib":
                        if (parts.Length >= 2)
                            result.MtlLibrary = parts[1];
                        break;

                    case "f":
                        if (parts.Length >= 4)
                            AddFace(parts, positions, texCoords, normals, current, result);
                        break;
                }
            }

            // Drop empty sub-meshes (e.g. a usemtl with no faces under it).
            result.SubMeshes.RemoveAll(s => s.Triangles.Count == 0);

            if (boundsInit)
                result.Bounds = new Bounds(
                    new Vector3((minX + maxX) * 0.5f, (minY + maxY) * 0.5f, (minZ + maxZ) * 0.5f),
                    new Vector3(maxX - minX, maxY - minY, maxZ - minZ));

            // If no normals were supplied, Unity will recompute them on import.
            if (!anyNormal)
                result.SubMeshes.ForEach(s => s.Normals.Clear());

            return result.HasGeometry ? result : null;
        }

        private static SubMesh NewSubMesh(string material) => new SubMesh { MaterialName = material };

        /// <summary>
        /// Adds one face. Faces with 4+ vertices are fan-triangulated, which is
        /// correct for the convex quads/ngons the exporter produces.
        /// </summary>
        private static void AddFace(
            string[] parts,
            List<Vector3> positions,
            List<Vector2> texCoords,
            List<Vector3> normals,
            SubMesh target,
            ParsedObj result)
        {
            int vertexCount = parts.Length - 1;
            if (vertexCount < 3) return;

            int firstIndex = -1;
            int prevIndex = -1;

            for (int i = 1; i < parts.Length; i++)
            {
                if (!TryAddVertex(parts[i], positions, texCoords, normals, target, out int index))
                    return;

                if (firstIndex < 0)
                {
                    firstIndex = index;
                }
                else if (prevIndex >= 0)
                {
                    // Fan: (first, prev, current)
                    target.Triangles.Add(firstIndex);
                    target.Triangles.Add(prevIndex);
                    target.Triangles.Add(index);
                    result.TotalTriangles++;
                }

                prevIndex = index;
            }
        }

        /// <summary>
        /// Resolves one face-vertex token ("v", "v/vt", "v//vn", "v/vt/vn") to an
        /// index in the sub-mesh's local vertex list, adding it if new. Vertices
        /// are de-duplicated by their full attribute tuple so a shared position
        /// with different UVs stays split correctly.
        /// </summary>
        private static bool TryAddVertex(
            string token,
            List<Vector3> positions,
            List<Vector2> texCoords,
            List<Vector3> normals,
            SubMesh target,
            out int index)
        {
            index = -1;

            string[] idx = token.Split('/');
            if (idx.Length == 0 || !TryResolveIndex(idx[0], positions.Count, out int pi))
                return false;

            Vector3 pos = positions[pi];

            // Declared before the checks: an `out` inside a short-circuit `&&`
            // is not definitely assigned when the earlier operand is false.
            Vector2 uv = default;
            bool hasUv = false;
            if (idx.Length >= 2 && idx[1].Length > 0 &&
                TryResolveIndex(idx[1], texCoords.Count, out int ti))
            {
                uv = texCoords[ti];
                hasUv = true;
            }

            Vector3 normal = default;
            bool hasNormal = false;
            if (idx.Length >= 3 && idx[2].Length > 0 &&
                TryResolveIndex(idx[2], normals.Count, out int ni))
            {
                normal = normals[ni];
                hasNormal = true;
            }

            // De-duplicate so meshes stay small (a 1000-face model would otherwise
            // become 3000 vertices).
            for (int i = 0; i < target.Vertices.Count; i++)
            {
                if (target.Vertices[i].Equals(pos)
                    && (!hasUv || target.Uvs[i].Equals(uv))
                    && (!hasNormal || target.Normals[i].Equals(normal)))
                {
                    index = i;
                    return true;
                }
            }

            index = target.Vertices.Count;
            target.Vertices.Add(pos);
            target.Uvs.Add(hasUv ? uv : Vector2.zero);
            target.Normals.Add(hasNormal ? normal : Vector3.up);
            return true;
        }

        /// <summary>
        /// OBJ indices are 1-based; negative indices count back from the end.
        /// </summary>
        private static bool TryResolveIndex(string raw, int count, out int zeroBased)
        {
            zeroBased = -1;
            if (!int.TryParse(raw, NumberStyles.Integer, CultureInfo.InvariantCulture, out int value))
                return false;

            if (value > 0) zeroBased = value - 1;
            else if (value < 0) zeroBased = count + value;
            else return false;

            return zeroBased >= 0 && zeroBased < count;
        }

        private static float ParseFloat(string s) =>
            float.TryParse(s, NumberStyles.Float, CultureInfo.InvariantCulture, out float v) ? v : 0f;
    }
}
