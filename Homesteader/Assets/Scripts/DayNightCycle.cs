// DayNightCycle.cs - Realistic seasonal solar tracking and celestial illumination for Homesteader.
//
// Requirements:
// - Day phase: 1440 real seconds (12 game hours, 06:00 AM to 06:00 PM)
// - Night phase: 1440 real seconds (12 game hours, 06:00 PM to 06:00 AM)
// - Sun rises in the East (right side of viewport) and sets in the West (left side of viewport)
// - Seasons dynamically dictate solar zenith angle (Summer: ~76°, Winter: ~30°, Spring/Autumn: ~53°)
// - Moon rises in the East and sets in the West during nighttime with soft silvery illumination
// - Driven directly by TimeSystem.Instance and affected by HUD speed controls (Pause, 1X, 3X, 5X, 10X)

using System;
using UnityEngine;
using Homesteader.UI;

namespace Homesteader
{
    [ExecuteAlways]
    public class DayNightCycle : MonoBehaviour
    {
        [Header("Target Lighting References")]
        [Tooltip("Directional light representing the Sun / Moon. If null, auto-resolves from this GameObject or scene.")]
        [SerializeField] private Light _celestialLight;

        [Header("Reference Camera Orientation")]
        [Tooltip("Camera used to align East to the right side of the viewport. Defaults to Camera.main or IsometricLockedCamera.")]
        [SerializeField] private Camera _referenceCamera;

        [Header("Sun Intensity & Colors")]
        [SerializeField] private float _summerSunIntensity = 2.0f;
        [SerializeField] private float _springSunIntensity = 1.8f;
        [SerializeField] private float _autumnSunIntensity = 1.7f;
        [SerializeField] private float _winterSunIntensity = 1.4f;
        [SerializeField] private float _moonIntensity = 0.5f;

        [Header("Ambient Lighting")]
        [SerializeField] private Color _dayAmbientColor = new Color(0.38f, 0.42f, 0.48f);
        [SerializeField] private Color _nightAmbientColor = new Color(0.17f, 0.21f, 0.31f);

        // Canonical world East and South vectors for Homesteader's default isometric view (Yaw = -45°)
        // In the standard camera angle, looking towards (-X, +Z):
        // Right side of screen = (+X, +Z) [East]
        // Left side of screen = (-X, -Z) [West]
        // Bottom of screen = (+X, -Z) [South]
        private static readonly Vector3 DefaultEastDirection = new Vector3(0.7071068f, 0f, 0.7071068f);
        private static readonly Vector3 DefaultSouthDirection = new Vector3(0.7071068f, 0f, -0.7071068f);

        private void Awake()
        {
            ResolveReferences();
            // The day/night ambient colour below is only used in Flat mode. In the default Skybox
            // mode it is ignored, so anything lit (the player, props) stayed evenly bright at night.
            RenderSettings.ambientMode = UnityEngine.Rendering.AmbientMode.Flat;
        }

        private void OnEnable()
        {
            ResolveReferences();
        }

        private void ResolveReferences()
        {
            if (_celestialLight == null)
            {
                _celestialLight = GetComponent<Light>();
                if (_celestialLight == null)
                {
                    // Find directional light in the scene
                    var lights = FindObjectsByType<Light>(FindObjectsInactive.Exclude);
                    foreach (var l in lights)
                    {
                        if (l.type == LightType.Directional)
                        {
                            _celestialLight = l;
                            break;
                        }
                    }
                }
            }

            if (_referenceCamera == null)
            {
                var iso = FindAnyObjectByType<IsometricLockedCamera>();
                if (iso != null)
                {
                    _referenceCamera = iso.GetComponent<Camera>();
                }
                if (_referenceCamera == null)
                {
                    _referenceCamera = Camera.main;
                }
            }
        }

        private void Update()
        {
            UpdateSunPosition();
            UpdateWeatherLighting();
        }

        // ── Weather Lighting Modulation ───────────────────────────────────
        // Applied as a multiplier on top of the celestial intensity computed in
        // UpdateSunPosition. Smooth-lerps so transitions are not jarring.
        private float _weatherIntensityMult = 1f;
        private float _targetWeatherMult = 1f;

        private void UpdateWeatherLighting()
        {
            if (_celestialLight == null) return;
            if (TimeSystem.Instance.IsPaused) return;

            HomesteaderWeather weather = TimeSystem.Instance.Weather;
            float target = GetWeatherIntensityMultiplier(weather);

            // Smooth transition for weather changes
            _targetWeatherMult = target;
            _weatherIntensityMult = Mathf.MoveTowards(
                _weatherIntensityMult, _targetWeatherMult, Time.deltaTime * 0.5f);

            // Check lightning — when a flash is active, boost overrides weather dimming
            float lightning = WeatherEffectsManager.Instance?.LightningBoost ?? 1f;
            bool isFlashing = lightning > 1.05f;

            // Apply weather dim + lightning boost on top of the celestial intensity set this frame
            _celestialLight.intensity *= (_weatherIntensityMult * lightning);

            // Tint ambient for overcast — but skip during a lightning flash so it punches white
            if (!isFlashing)
            {
                Color ambientTint = GetWeatherAmbientTint(weather);
                if (ambientTint != Color.clear)
                {
                    RenderSettings.ambientLight = Color.Lerp(
                        RenderSettings.ambientLight, ambientTint, Time.deltaTime * 0.4f);
                }
            }

            // Push new weather state to WeatherEffectsManager
            WeatherEffectsManager.Instance?.ApplyWeather(weather);
        }

        private static float GetWeatherIntensityMultiplier(HomesteaderWeather weather)
        {
            switch (weather)
            {
                case HomesteaderWeather.Sunny: return 1.00f;
                case HomesteaderWeather.PartlyCloudy: return 0.85f;
                case HomesteaderWeather.Cloudy: return 0.40f;
                case HomesteaderWeather.Rain: return 0.30f;
                case HomesteaderWeather.Thunderstorm: return 0.15f;
                case HomesteaderWeather.Snow: return 0.75f;
                case HomesteaderWeather.Blizzard: return 0.25f; // Dramatic dimming during blizzard
                case HomesteaderWeather.Wind: return 0.90f;
                case HomesteaderWeather.Fog: return 0.35f;
                default: return 1.00f;
            }
        }

        private static Color GetWeatherAmbientTint(HomesteaderWeather weather)
        {
            switch (weather)
            {
                case HomesteaderWeather.Cloudy:
                    return new Color(0.20f, 0.22f, 0.26f);
                case HomesteaderWeather.Rain:
                    return new Color(0.15f, 0.17f, 0.22f);
                case HomesteaderWeather.Thunderstorm:
                    return new Color(0.10f, 0.11f, 0.16f);
                case HomesteaderWeather.Snow:
                    return new Color(0.24f, 0.27f, 0.34f);
                case HomesteaderWeather.Blizzard:
                    return new Color(0.48f, 0.54f, 0.65f); // Cold frosty white-blue blizzard ambient
                case HomesteaderWeather.Fog:
                    return new Color(0.32f, 0.34f, 0.36f);
                default:
                    return Color.clear; // No override for clear/partly cloudy/wind
            }
        }
        // ─────────────────────────────────────────────────────────────────

        public void UpdateSunPosition()
        {
            if (_celestialLight == null)
            {
                ResolveReferences();
                if (_celestialLight == null) return;
            }

            var timeSystem = TimeSystem.Instance;
            var timeSnap = timeSystem.Snapshot();
            float cycleMin = timeSnap.CycleMinute;
            int dayOfYear = timeSnap.DayOfYear;
            HomesteaderSeason season = timeSnap.Season;

            float sunrise = timeSnap.SunriseMinute;
            float sunset = timeSnap.SunsetMinute;
            float dayDuration = Mathf.Max(60f, sunset - sunrise);
            float nightDuration = Mathf.Max(60f, TimeConstants.CycleGameMinutes - dayDuration);

            // Determine if it is Day (sunrise to sunset) or Night (sunset to sunrise)
            bool isDay = (cycleMin >= sunrise && cycleMin < sunset);

            // Calculate seasonal peak solar elevation (degrees above horizon at noon)
            float maxSolarElevation = TimeSystem.GetMaxSolarElevation(dayOfYear);

            // Determine East and South directions.
            // If camera is present, compute relative to camera yaw so viewport right is ALWAYS East
            Vector3 eastDir = DefaultEastDirection;
            Vector3 southDir = DefaultSouthDirection;

            if (_referenceCamera != null)
            {
                float camYaw = _referenceCamera.transform.eulerAngles.y;
                Quaternion camYawRot = Quaternion.Euler(0f, camYaw, 0f);
                eastDir = camYawRot * Vector3.right;
                southDir = camYawRot * Vector3.back;
            }

            if (isDay)
            {
                // Day Phase: Progress goes 0.0 at Sunrise to 1.0 at Sunset
                float dayProgress = (cycleMin - sunrise) / dayDuration;
                float alpha = dayProgress * Mathf.PI; // 0 to PI

                // Horizontal East-to-West motion: +1 at sunrise (East / right side) -> 0 at noon -> -1 at sunset (West / left side)
                float xEastWest = Mathf.Cos(alpha);

                // Vertical elevation angle above horizon (0° at horizon, maxSolarElevation at noon)
                float elevationDeg = maxSolarElevation * Mathf.Sin(alpha);
                float elevationRad = elevationDeg * Mathf.Deg2Rad;

                // Southward declination component (arcs across southern sky)
                float zSouth = Mathf.Cos(elevationRad) * Mathf.Sin(alpha);
                float yUp = Mathf.Sin(elevationRad);

                // Vector pointing towards the Sun in the sky
                Vector3 dirToSun = (xEastWest * Mathf.Cos(elevationRad) * eastDir) +
                                   (zSouth * southDir) +
                                   (yUp * Vector3.up);
                dirToSun.Normalize();

                // Directional light shines along forward, so point forward towards the scene (-dirToSun)
                _celestialLight.transform.rotation = Quaternion.LookRotation(-dirToSun, Vector3.up);

                // Calculate intensity and color based on sun height factor
                float heightFactor = Mathf.Sin(alpha); // 0 at dawn/dusk, 1 at noon
                float baseIntensity = GetSeasonIntensity(season);

                // Smooth horizon fade at dawn and dusk
                float horizonFade = Mathf.SmoothStep(0f, 1f, heightFactor * 3.5f);
                _celestialLight.intensity = baseIntensity * horizonFade;

                // Color temperature based on time of day using seasonal palette
                Color sunriseColor = GetSeasonSunriseColor(season);
                Color noonColor = GetSeasonNoonColor(season);
                Color sunsetColor = GetSeasonSunsetColor(season);

                Color sunColor;
                if (dayProgress <= 0.5f)
                {
                    float t = Mathf.SmoothStep(0f, 1f, dayProgress / 0.5f);
                    sunColor = Color.Lerp(sunriseColor, noonColor, t);
                }
                else
                {
                    float t = Mathf.SmoothStep(0f, 1f, (dayProgress - 0.5f) / 0.5f);
                    sunColor = Color.Lerp(noonColor, sunsetColor, t);
                }

                _celestialLight.color = sunColor;
                _celestialLight.shadowStrength = Mathf.Lerp(0.5f, 1.0f, horizonFade);

                // Set shader globals so the water shader can use the actual sun direction and color
                Shader.SetGlobalVector("_CelestialDir", dirToSun);
                Shader.SetGlobalVector("_CelestialColor", new Vector4(sunColor.r, sunColor.g, sunColor.b, horizonFade));
                Shader.SetGlobalVector("_SkyParams", new Vector4(1f - horizonFade, 0f, 0f, 0f));

                // Ambient light
                RenderSettings.ambientLight = Color.Lerp(_nightAmbientColor, _dayAmbientColor, horizonFade);
            }
            else
            {
                // Night Phase: Progress goes 0.0 at Sunset to 1.0 at Sunrise
                float nightMinute = (cycleMin >= sunset)
                    ? (cycleMin - sunset)
                    : (cycleMin + (TimeConstants.CycleGameMinutes - sunset));

                float nightProgress = nightMinute / nightDuration;
                float beta = nightProgress * Mathf.PI; // 0 to PI

                // Moon rises in the East (right side of viewport) and sets in the West (left side)
                float xEastWest = Mathf.Cos(beta);
                float moonElevationDeg = 48f * Mathf.Sin(beta);
                float moonElevationRad = moonElevationDeg * Mathf.Deg2Rad;

                float zSouth = Mathf.Cos(moonElevationRad) * Mathf.Sin(beta);
                float yUp = Mathf.Sin(moonElevationRad);

                Vector3 dirToMoon = (xEastWest * Mathf.Cos(moonElevationRad) * eastDir) +
                                    (zSouth * southDir) +
                                    (yUp * Vector3.up);
                dirToMoon.Normalize();

                _celestialLight.transform.rotation = Quaternion.LookRotation(-dirToMoon, Vector3.up);

                float moonHeightFactor = Mathf.Sin(beta);
                // Floor the fade so the moon never fully goes out at the start / end of the night.
                float moonFade = Mathf.Max(0.4f, Mathf.SmoothStep(0f, 1f, moonHeightFactor * 2.5f));
                float moonCycleBrightness = timeSystem.GetMoonPhaseBrightness(0.45f); // new moon is still readable

                _celestialLight.intensity = _moonIntensity * moonFade * moonCycleBrightness;
                Color moonColor = GetSeasonNightMoonColor(season);
                _celestialLight.color = moonColor;
                _celestialLight.shadowStrength = Mathf.Lerp(0.05f, 0.45f, moonCycleBrightness);

                // Set shader globals so the water shader can use the actual moon direction and color
                Shader.SetGlobalVector("_CelestialDir", dirToMoon);
                Shader.SetGlobalVector("_CelestialColor", new Vector4(moonColor.r, moonColor.g, moonColor.b, moonFade * moonCycleBrightness));
                Shader.SetGlobalVector("_SkyParams", new Vector4(1f, 0f, 0f, 0f));

                RenderSettings.ambientLight = Color.Lerp(_nightAmbientColor, moonColor * (0.16f + 0.25f * moonCycleBrightness), moonFade);
            }
        }

        private float GetSeasonIntensity(HomesteaderSeason season)
        {
            switch (season)
            {
                case HomesteaderSeason.Summer: return _summerSunIntensity;
                case HomesteaderSeason.Spring: return _springSunIntensity;
                case HomesteaderSeason.Autumn: return _autumnSunIntensity;
                case HomesteaderSeason.Winter: return _winterSunIntensity;
                default: return 1.8f;
            }
        }

        // Seasonal lighting palettes
        // Spring: Fresh peach dawn (#FFD29D), bright warm white midday (#FFFBE6), soft coral dusk (#FF9E79), cool pastel blue moonlight (#C8DDF2)
        private static readonly Color SpringSunrise = new Color(1.0000f, 0.8235f, 0.6157f); // #FFD29D
        private static readonly Color SpringNoon = new Color(1.0000f, 0.9843f, 0.9020f); // #FFFBE6
        private static readonly Color SpringSunset = new Color(1.0000f, 0.6196f, 0.4745f); // #FF9E79
        private static readonly Color SpringNight = new Color(0.7843f, 0.8667f, 0.9490f); // #C8DDF2

        // Summer: Vivid amber dawn (#FFA451), intense near-white noon (#FFFFF2), hot fiery red-orange dusk (#FF6138), rich deep periwinkle moonlight (#96C5F7)
        private static readonly Color SummerSunrise = new Color(1.0000f, 0.6431f, 0.3176f); // #FFA451
        private static readonly Color SummerNoon = new Color(1.0000f, 1.0000f, 0.9490f); // #FFFFF2
        private static readonly Color SummerSunset = new Color(1.0000f, 0.3804f, 0.2196f); // #FF6138
        private static readonly Color SummerNight = new Color(0.5882f, 0.7725f, 0.9686f); // #96C5F7

        // Autumn: Golden honey dawn (#F8B052), muted amber-white noon (#FFF3C4), deep russet/burnt orange dusk (#D95B30), pale harvest silver-olive moon (#D8D5B5)
        private static readonly Color AutumnSunrise = new Color(0.9725f, 0.6902f, 0.3216f); // #F8B052
        private static readonly Color AutumnNoon = new Color(1.0000f, 0.9529f, 0.7686f); // #FFF3C4
        private static readonly Color AutumnSunset = new Color(0.8510f, 0.3569f, 0.1882f); // #D95B30
        private static readonly Color AutumnNight = new Color(0.8471f, 0.8353f, 0.7098f); // #D8D5B5

        // Winter: Pale rose-gold dawn (#FFC2A6), sharp cool frost-white noon (#EEF5FF), dusty berry/mauve sunset (#D6708A), crisp glacial blue-violet moon (#8EA8D9)
        private static readonly Color WinterSunrise = new Color(1.0000f, 0.7608f, 0.6510f); // #FFC2A6
        private static readonly Color WinterNoon = new Color(0.9333f, 0.9608f, 1.0000f); // #EEF5FF
        private static readonly Color WinterSunset = new Color(0.8392f, 0.4392f, 0.5412f); // #D6708A
        private static readonly Color WinterNight = new Color(0.5569f, 0.6588f, 0.8510f); // #8EA8D9

        public static Color GetSeasonSunriseColor(HomesteaderSeason season)
        {
            switch (season)
            {
                case HomesteaderSeason.Summer: return SummerSunrise;
                case HomesteaderSeason.Autumn: return AutumnSunrise;
                case HomesteaderSeason.Winter: return WinterSunrise;
                case HomesteaderSeason.Spring:
                default: return SpringSunrise;
            }
        }

        public static Color GetSeasonNoonColor(HomesteaderSeason season)
        {
            switch (season)
            {
                case HomesteaderSeason.Summer: return SummerNoon;
                case HomesteaderSeason.Autumn: return AutumnNoon;
                case HomesteaderSeason.Winter: return WinterNoon;
                case HomesteaderSeason.Spring:
                default: return SpringNoon;
            }
        }

        public static Color GetSeasonSunsetColor(HomesteaderSeason season)
        {
            switch (season)
            {
                case HomesteaderSeason.Summer: return SummerSunset;
                case HomesteaderSeason.Autumn: return AutumnSunset;
                case HomesteaderSeason.Winter: return WinterSunset;
                case HomesteaderSeason.Spring:
                default: return SpringSunset;
            }
        }

        public static Color GetSeasonNightMoonColor(HomesteaderSeason season)
        {
            switch (season)
            {
                case HomesteaderSeason.Summer: return SummerNight;
                case HomesteaderSeason.Autumn: return AutumnNight;
                case HomesteaderSeason.Winter: return WinterNight;
                case HomesteaderSeason.Spring:
                default: return SpringNight;
            }
        }
    }
}
