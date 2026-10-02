using UnityEngine;
using Homesteader.UI;

namespace Homesteader.World
{
    /// <summary>
    /// Drives the shared cloud globals (_CloudParams) read by the terrain, vegetation, grass and water shaders:
    /// coverage follows the weather and eases in and out, the clouds drift downwind, and the shadow strength follows
    /// the Cloud Shadows setting. Purely visual, nothing is saved.
    /// </summary>
    public sealed class CloudSystem : MonoBehaviour
    {
        /// <summary>Set from Settings > Graphics > Cloud Shadows.</summary>
        public static bool ShadowsEnabled = true;

        private static readonly int CloudParamsId = Shader.PropertyToID("_CloudParams");
        private static readonly int WindId = Shader.PropertyToID("_GrassWindParams");

        private float _coverage = 0.3f;
        private Vector2 _offset;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        private static void Boot()
        {
            if (FindAnyObjectByType<CloudSystem>() != null) return;
            var go = new GameObject("CloudSystem");
            DontDestroyOnLoad(go);
            go.AddComponent<CloudSystem>();
        }

        private static float CoverageFor(HomesteaderWeather w)
        {
            switch (w)
            {
                case HomesteaderWeather.PartlyCloudy: return 0.42f;
                case HomesteaderWeather.Cloudy: return 0.85f;
                case HomesteaderWeather.Rain: return 0.95f;
                case HomesteaderWeather.Thunderstorm: return 1f;
                case HomesteaderWeather.Snow: return 0.9f;
                case HomesteaderWeather.Blizzard: return 1f;
                case HomesteaderWeather.Fog: return 0.6f;
                case HomesteaderWeather.Wind: return 0.25f;
                default: return 0.1f;   // Sunny: a few wisps
            }
        }

        private void Update()
        {
            TimeSystem ts = TimeSystem.Instance;
            float target = CoverageFor(ts != null ? ts.Weather : HomesteaderWeather.Sunny);
            _coverage = Mathf.MoveTowards(_coverage, target, Time.deltaTime * 0.04f);   // about 20 s from clear to overcast

            Vector4 wind = Shader.GetGlobalVector(WindId);
            Vector2 dir = new Vector2(wind.x, wind.y);
            if (dir.sqrMagnitude < 1e-4f) dir = new Vector2(1f, 0.3f);
            dir.Normalize();
            // The noise is sampled at (position + offset), so the offset runs against the wind for the clouds to move with it.
            _offset -= dir * ((2f + wind.z * 0.6f) * Time.deltaTime);

            float strength = ShadowsEnabled ? Mathf.Lerp(0.45f, 0.15f, Mathf.InverseLerp(0.6f, 1f, _coverage)) : 0f;
            Shader.SetGlobalVector(CloudParamsId, new Vector4(_coverage, strength, _offset.x, _offset.y));
        }
    }
}
