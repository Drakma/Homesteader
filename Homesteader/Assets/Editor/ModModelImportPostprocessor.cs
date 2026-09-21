using System;
using UnityEditor;
using UnityEngine;

namespace Homesteader.Editor
{
    /// <summary>
    /// Applies the project's import rules to any model that lands under
    /// `Assets/Mods/`.
    ///
    /// This exists because getting model import settings wrong is silent: the file
    /// imports, the prefab builds, and the tree renders at 100x scale (the
    /// pipeline authors in centimetres) or with no material at all. Setting them
    /// here means nobody has to remember to set them by hand in the Inspector.
    ///
    /// Conventions enforced:
    ///   * Scale Factor 1 with Convert Units ON  -> centimetre-authored FBX lands
    ///     at 1 unit = 1 metre, matching the project standard.
    ///   * Materials imported so embedded textures resolve. The pipeline bakes
    ///     textures INTO the FBX (Video/Texture nodes), so without this the mesh
    ///     imports untextured.
    ///   * Weld/normals preserved, tangents calculated, shadows enabled for
    ///     world-placed geometry.
    /// </summary>
    public sealed class ModModelImportPostprocessor : AssetPostprocessor
    {
        private const string ModsRoot = "Assets/Mods/";

        private void OnPreprocessModel()
        {
            if (!assetPath.StartsWith(ModsRoot, StringComparison.OrdinalIgnoreCase))
                return;

            var importer = assetImporter as ModelImporter;
            if (importer == null)
                return;

            ApplyProjectModelSettings(importer);
        }

        /// <summary>
        /// The shared import profile, exposed so the prefab generator and the
        /// project's own tooling can assert the same values.
        /// </summary>
        public static void ApplyProjectModelSettings(ModelImporter importer)
        {
            // Metric scale: the pipeline writes centimetres.
            importer.globalScale = 1f;
            importer.useFileScale = true;
            importer.bakeAxisConversion = true;

            // Geometry quality.
            importer.isReadable = true;              // needed for colliders / sampling
            importer.importNormals = ModelImporterNormals.Import;
            importer.importTangents = ModelImporterTangents.CalculateMikk;
            importer.weldVertices = true;
            importer.meshCompression = ModelImporterMeshCompression.Off;

            // Materials + textures. Extract keeps embedded textures usable and
            // writes them next to the model, so the prefab has something to bind.
            importer.materialImportMode = ModelImporterMaterialImportMode.ImportStandard;
            importer.materialLocation = ModelImporterMaterialLocation.External;
            importer.materialName = ModelImporterMaterialName.BasedOnMaterialName;
            importer.materialSearch = ModelImporterMaterialSearch.Everywhere;

            // Trees are static world geometry; animated rigs stay untouched.
            importer.importAnimation = false;
            importer.importBlendShapes = false;
            importer.importVisibility = false;
            importer.importCameras = false;
            importer.importLights = false;
        }
    }
}
