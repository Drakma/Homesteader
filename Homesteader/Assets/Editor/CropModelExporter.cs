using System.IO;
using System.Threading.Tasks;
using System;
using System.Reflection;
using System.Threading;
using UnityEditor;
using UnityEngine;
using Homesteader.World;

namespace Homesteader.EditorTools
{
    /// <summary>
    /// Exports the procedural crop looks (ProceduralCrops) as GLB files for the asset kit: assets/_scratch/crop_models/&lt;crop&gt;__&lt;phase&gt;.glb.
    /// tools/build_crop_groups.py puts them into the kit's stage folders and renders the icons. Menu: Homesteader / Export Crop Models.
    /// </summary>
    public static class CropModelExporter
    {
        [MenuItem("Homesteader/Export Crop Models")]
        public static async void ExportAll()
        {
            string root = Path.GetFullPath(Path.Combine(Application.dataPath, "..", "..", "assets", "_scratch", "crop_models"));
            Directory.CreateDirectory(root);
            int ok = 0, bad = 0;
            foreach (string crop in ProceduralCrops.Names)
            {
                foreach (ProceduralCrops.Phase ph in Enum.GetValues(typeof(ProceduralCrops.Phase)))
                {
                    GameObject go = ProceduralCrops.MakeExportModel(crop, ph);
                    string path = Path.Combine(root, crop + "__" + ph.ToString().ToLowerInvariant() + ".glb");
                    try
                    {
                        // glTFast's export assembly is not auto-referenced, and the project's code is one predefined assembly, so go by reflection.
                        Type tSet = Type.GetType("GLTFast.Export.ExportSettings, glTFast.Export", true);
                        Type tFmt = Type.GetType("GLTFast.Export.GltfFormat, glTFast.Export", true);
                        Type tConf = Type.GetType("GLTFast.Export.FileConflictResolution, glTFast.Export", true);
                        Type tExp = Type.GetType("GLTFast.Export.GameObjectExport, glTFast.Export", true);
                        object set = Activator.CreateInstance(tSet);
                        tSet.GetProperty("Format").SetValue(set, Enum.Parse(tFmt, "Binary"));
                        tSet.GetProperty("FileConflictResolution").SetValue(set, Enum.Parse(tConf, "Overwrite"));
                        object export = Activator.CreateInstance(tExp, new object[] { set, null, null, null, null });
                        tExp.GetMethod("AddScene").Invoke(export, new object[] { new[] { go }, go.name });
                        var task = (Task<bool>)tExp.GetMethod("SaveToFileAndDispose").Invoke(export, new object[] { path, default(CancellationToken) });
                        bool done = await task;
                        if (done) ok++; else bad++;
                    }
                    catch (Exception e)
                    {
                        Debug.LogError("Crop export failed for " + path + ": " + e);
                        bad++;
                    }
                    UnityEngine.Object.DestroyImmediate(go);
                }
            }
            Debug.Log("[CropModelExporter] exported " + ok + " crop models (" + bad + " failed) to " + root);
        }

        /// <summary>Triangle counts of every crop look (to check the poly budget).</summary>
        [MenuItem("Homesteader/Report Crop Triangles")]
        public static void Report()
        {
            var sb = new System.Text.StringBuilder("[CropModelExporter] triangles: ");
            foreach (string crop in ProceduralCrops.Names)
            {
                sb.Append(crop).Append(' ');
                foreach (ProceduralCrops.Phase ph in Enum.GetValues(typeof(ProceduralCrops.Phase)))
                    sb.Append(ProceduralCrops.BuildMesh(crop, ph).triangles.Length / 3).Append(' ');
                sb.Append("| ");
            }
            Debug.Log(sb.ToString());
        }
    }
}
