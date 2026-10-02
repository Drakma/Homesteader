using UnityEngine;

namespace Homesteader
{
    /// <summary>
    /// Compiles the shader variants in Resources/ShaderWarmup (built by Homesteader / Build Shader Variant Collection) as the
    /// game starts, so switching Shadows or Ultra's cascades on, or the first night light, does not hitch while playing.
    /// </summary>
    public static class ShaderWarmup
    {
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        private static void Warm()
        {
            var svc = Resources.Load<ShaderVariantCollection>("ShaderWarmup");
            if (svc == null) return;
            float t = Time.realtimeSinceStartup;
            svc.WarmUp();
            Debug.Log($"[ShaderWarmup] warmed {svc.variantCount} variants in {Time.realtimeSinceStartup - t:F1}s.");
        }
    }
}
