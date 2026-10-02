using System.Collections.Generic;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;

namespace Homesteader.EditorTools
{
    /// <summary>
    /// Builds Assets/Resources/ShaderWarmup.shadervariants: every shadow and light keyword combination the game's own shaders
    /// (and the URP shaders its props use) can meet, so Shadows, Ultra's cascades and the night lights are compiled while the
    /// game loads instead of hitching the first time they are switched on. ShaderWarmup (runtime) warms it up at start.
    /// Menu: Homesteader / Build Shader Variant Collection.
    /// </summary>
    public static class ShaderVariantCollectionBuilder
    {
        private const string Path = "Assets/Resources/ShaderWarmup.shadervariants";

        private static readonly string[] OwnShaders =
        {
            "Homesteader/Vegetation", "Homesteader/GenerativeTerrainURP", "Homesteader/WaterSurface", "Homesteader/GrassGpu",
        };

        private static readonly string[] UrpShaders =
        {
            "Universal Render Pipeline/Lit", "Universal Render Pipeline/Simple Lit", "Universal Render Pipeline/Unlit",
        };

        private static readonly string[][] MainShadow =
        {
            new string[0],
            new[] { "_MAIN_LIGHT_SHADOWS" },
            new[] { "_MAIN_LIGHT_SHADOWS_CASCADE" },
            new[] { "_MAIN_LIGHT_SHADOWS_CASCADE", "_SHADOWS_SOFT" },
            new[] { "_MAIN_LIGHT_SHADOWS", "_SHADOWS_SOFT" },
        };

        private static readonly string[][] ExtraLights =
        {
            new string[0],
            new[] { "_ADDITIONAL_LIGHTS" },
            new[] { "_ADDITIONAL_LIGHTS", "_ADDITIONAL_LIGHT_SHADOWS" },
            new[] { "_ADDITIONAL_LIGHTS_VERTEX" },
        };

        [MenuItem("Homesteader/Build Shader Variant Collection")]
        public static string Build()
        {
            var svc = new ShaderVariantCollection();
            int added = 0, rejected = 0, missing = 0;
            var all = new List<string>(OwnShaders);
            all.AddRange(UrpShaders);

            foreach (string name in all)
            {
                Shader sh = Shader.Find(name);
                if (sh == null) { missing++; Debug.LogWarning("[ShaderVariants] shader not found: " + name); continue; }
                foreach (string[] shadow in MainShadow)
                    foreach (string[] extra in ExtraLights)
                    {
                        var kw = new List<string>(shadow);
                        kw.AddRange(extra);
                        if (TryAdd(svc, sh, PassType.ScriptableRenderPipeline, kw.ToArray())) added++; else rejected++;
                    }
                // Passes with no keywords of their own.
                foreach (PassType pt in new[] { PassType.ShadowCaster })
                    if (TryAdd(svc, sh, pt, new string[0])) added++;
            }

            AssetDatabase.DeleteAsset(Path);
            AssetDatabase.CreateAsset(svc, Path);
            AssetDatabase.SaveAssets();
            string report = $"[ShaderVariants] {Path}: {added} variants added, {rejected} combinations rejected by the shaders, {missing} shaders missing; {svc.shaderCount} shaders, {svc.variantCount} variants.";
            Debug.Log(report);
            return report;
        }

        private static bool TryAdd(ShaderVariantCollection svc, Shader shader, PassType pass, string[] keywords)
        {
            try { return svc.Add(new ShaderVariantCollection.ShaderVariant(shader, pass, keywords)); }
            catch (System.ArgumentException) { return false; }
        }
    }
}
