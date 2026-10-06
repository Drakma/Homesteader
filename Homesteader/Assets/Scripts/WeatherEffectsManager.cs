// WeatherEffectsManager.cs - Camera-anchored weather VFX for Homesteader.
//
// Manages real-time visual weather effects:
//   Rain    - Stretched raindrop particles falling from overhead emitter box
//   Snow    - Fluffy snowflakes drifting down with lateral sway
//   Wind    - Horizontal dust/leaf streaks
//   Fog     - RenderSettings.fog density interpolation
//   Thunder - Heavy rain + periodic directional-light lightning flashes
//
// Attach to any persistent GameObject (auto-created by HudSceneBootstrap).
// Tracks the main camera position each frame so effects always surround the player.

using System.Collections;
using UnityEngine;
using Homesteader.UI;

namespace Homesteader
{
    [DefaultExecutionOrder(50)]
    public class WeatherEffectsManager : MonoBehaviour
    {
        // ── Inspector overrides ──────────────────────────────────────────
        [Header("Emitter Box (half-extents around player/camera)")]
        [SerializeField] private float _emitterHalfWidth = 65f;
        [SerializeField] private float _emitterHalfDepth = 65f;
        [SerializeField] private float _emitterHeight = 20f;

        [Header("Rain")]
        [SerializeField] private int _rainMaxParticles = 15000;
        [SerializeField] private float _rainSpeed = 16f;
        [SerializeField] private float _rainSize = 0.15f;

        [Header("Snow")]
        [SerializeField] private int _snowMaxParticles = 8000;
        [SerializeField] private float _snowSpeed = 2.0f;
        [SerializeField] private float _blizzardSnowSpeed = 6.5f;
        [SerializeField] private float _snowSize = 0.25f;

        [Header("Wind")]
        [SerializeField] private int _windMaxParticles = 180;
        [SerializeField] private float _windSpeed = 10f;
        [SerializeField] private float _windSize = 0.06f;
        [SerializeField] private float _windMaxTurnDegPerSec = 1f;   // the wind direction never turns faster than this
        [SerializeField] private float _windGustInterval = 5f;     // seconds between gust changes
        [SerializeField] private float _windBaseSpeed = 4f;        // calm-day wind speed
        [SerializeField] private float _windStormSpeed = 18f;      // storm peak wind speed
        [SerializeField] private float _windLerpSpeed = 0.5f;      // how fast wind transitions to new target

        [Header("Fog")]
        [SerializeField] private float _fogFadeSpeed = 0.6f;  // units/sec

        [Header("Lightning")]
        [SerializeField] private float _lightningMinInterval = 4f;
        [SerializeField] private float _lightningMaxInterval = 14f;
        [SerializeField] private float _lightningFlashDuration = 0.12f;
        [SerializeField, Range(0f, 1f)] private float _lightningTreeStrikeChance = 0.05f;
        [SerializeField] private float _lightningTreeStrikeRadius = 55f;

        [Header("Accumulation Dynamics")]
        [SerializeField] private float _snowAccumulationPerGameHour = 0.4f; // 1.0 = about one inch: 2.5 game hours of normal snow, 1 hour in a blizzard (x2.5)
        [SerializeField] private float _snowMeltPerGameHour = 0.3f;      // snow melt per game hour when not snowing (an inch in ~3 hours; rain x3)
        [SerializeField] private float _wetnessGainRate = 0.05f;       // wetness gain per second during rain (~15 sec to soak)
        [SerializeField] private float _wetnessDryingRate = 0.006f;     // drying per second without rain (~3 min to dry out)

        // ── Runtime state ────────────────────────────────────────────────
        private ParticleSystem _rainPS;
        private ParticleSystem _rainSplashPS;
        private ParticleSystem _snowPS;
        private ParticleSystem _windPS;

        private Camera _cachedCam;
        private Transform _cachedPlayer;

        private float _currentSnowCoverage = 0f;
        // How far the ice has advanced 0..1 (0 = open water, 1 = fully frozen for this body). Read by
        // WaterSurface.shader as the global _WaterFreeze; the shader decides WHERE it freezes (from the shore
        // inwards, and how far in), this only says how much.
        private float _waterFreeze = 0f;
        [SerializeField] private float _realSecondsPerWeatherHour = 120f; // real seconds per "hour" of snow/melt/freeze rates
        private float _waterTempC = 10f;
        private float _waterTempTimer = 0f;
        [SerializeField] private float _freezePerGameHour = 0.06f;   // at just below 0C; colder freezes faster
        [SerializeField] private float _thawPerGameHour = 0.15f;     // at just above 0C; warmer thaws faster
        private float _currentGroundWetness = 0f;
        private float _currentRainNow = 0f;   // smoothed 0..1 "raining right now" for ripples

        private HomesteaderWeather _currentWeather = HomesteaderWeather.Sunny;
        private bool _weatherInitialized = false;
        private float _targetFogDensity;
        private float _fogBaseDensity;   // density before the camera-distance compensation
        private Color _targetFogColor;
        private bool _fogEnabled;

        private Light _directionalLight;
        private float _baseLightIntensity;
        private Coroutine _lightningRoutine;

        // Transition smoothing
        private float _rainEmission;
        private float _snowEmission;
        private float _windEmission;

        // Dynamic wind state
        private Vector2 _windDir = new Vector2(1f, 0f);   // current, smoothed wind direction (XZ, unit length)
        private Vector2 _windTargetDir = new Vector2(1f, 0f); // gust target direction, turned toward gradually
        private float _windCurrentSpeed = 0f;               // current wind speed (m/s)
        private float _windTargetSpeed = 0f;                 // target speed we're lerping toward
        private float _windGustTimer = 0f;                    // countdown to next gust change

        private static WeatherEffectsManager s_instance;
        public static WeatherEffectsManager Instance => s_instance;

        /// <summary>The current wind direction as a unit vector in world X, Z: the way the wind is BLOWING toward.</summary>
        public Vector2 WindDirection => _windDir;
        /// <summary>The current wind speed in metres per second.</summary>
        public float WindSpeedMps => _windCurrentSpeed;
        /// <summary>The strongest wind the weather produces (a storm), in metres per second.</summary>
        public float WindStormSpeedMps => _windStormSpeed;

        // Set by lightning coroutine; read by DayNightCycle to apply flash without fighting the per-frame multiply
        public float LightningBoost { get; private set; } = 1f;

        public float SnowCoverage => _currentSnowCoverage;
        public float GroundWetness => _currentGroundWetness;

        // ── Lifecycle ────────────────────────────────────────────────────
        private void Awake()
        {
            s_instance = this;
            BuildParticleSystems();
            CacheDirectionalLight();
        }

        private bool _wasPaused = false;

        private void Update()
        {
            ResolveAnchorTargets();
            AnchorToCamera();

            bool isPaused = TimeSystem.Instance.IsPaused;
            if (isPaused)
            {
                if (!_wasPaused)
                {
                    _wasPaused = true;
                    PauseAllWeather();
                }
                return;
            }
            else if (_wasPaused)
            {
                _wasPaused = false;
                ResumeAllWeather();
                // Force weather re-application after unpause so particle targets are set
                _weatherInitialized = false;
            }

            SmoothEmission();
            SmoothFog();
            UpdateGroundAccumulation();
            UpdateWind();
        }

        private void PauseAllWeather()
        {
            if (_rainPS != null && _rainPS.isPlaying) _rainPS.Pause(true);
            if (_rainSplashPS != null && _rainSplashPS.isPlaying) _rainSplashPS.Pause(true);
            if (_snowPS != null && _snowPS.isPlaying) _snowPS.Pause(true);
            if (_windPS != null && _windPS.isPlaying) _windPS.Pause(true);

            if (LightningBoost > 1.05f)
            {
                LightningBoost = 1f;
            }
        }

        private void ResumeAllWeather()
        {
            if (_rainEmission > 0.01f && _rainPS != null && _rainPS.isPaused) _rainPS.Play(true);
            if (_rainEmission > 0.01f && _rainSplashPS != null && _rainSplashPS.isPaused) _rainSplashPS.Play(true);
            if (_snowEmission > 0.01f && _snowPS != null && _snowPS.isPaused) _snowPS.Play(true);
            if (_windEmission > 0.01f && _windPS != null && _windPS.isPaused) _windPS.Play(true);
        }

        private void ResolveAnchorTargets()
        {
            if (_cachedCam == null || !_cachedCam.gameObject.activeInHierarchy)
            {
                _cachedCam = Camera.main;
                if (_cachedCam == null)
                {
                    var isoCam = IsometricLockedCamera.Current;
                    if (isoCam != null) _cachedCam = isoCam.GetComponent<Camera>();
                }
                if (_cachedCam == null)
                {
                    _cachedCam = FindAnyObjectByType<Camera>();
                }
            }

            if (_cachedPlayer == null)
            {
                var p = GameObject.FindWithTag("Player");
                if (p != null) _cachedPlayer = p.transform;
                else
                {
                    var ped = PedController.Current;
                    if (ped != null) _cachedPlayer = ped.transform;
                }
            }
        }

        private void UpdateGroundAccumulation()
        {
            float dt = Time.unscaledDeltaTime;
            // Snow, melt, wetness and ice run on REAL time, not the in-game clock: they no longer stop when
            // the game is paused or speed up with the time-speed setting. The per-"hour" rates keep their
            // meaning; one such hour is _realSecondsPerWeatherHour real seconds (120 = the old 1x pace).
            float gameHours = dt / Mathf.Max(1f, _realSecondsPerWeatherHour);
            bool isRaining = (_currentWeather == HomesteaderWeather.Rain || _currentWeather == HomesteaderWeather.Thunderstorm);
            bool isSnowing = (_currentWeather == HomesteaderWeather.Snow || _currentWeather == HomesteaderWeather.Blizzard);
            float snowRateMult = (_currentWeather == HomesteaderWeather.Blizzard) ? 2.5f : 1.0f;

            // Ground Wetness
            if (isRaining)
            {
                float targetWet = (_currentWeather == HomesteaderWeather.Thunderstorm) ? 1.0f : 0.85f;
                _currentGroundWetness = Mathf.MoveTowards(_currentGroundWetness, targetWet, _wetnessGainRate * dt);
            }
            else
            {
                _currentGroundWetness = Mathf.MoveTowards(_currentGroundWetness, 0f, _wetnessDryingRate * dt);
            }

            // Snow Coverage
            if (isSnowing)
            {
                _currentSnowCoverage = Mathf.MoveTowards(_currentSnowCoverage, 1.0f, _snowAccumulationPerGameHour * snowRateMult * gameHours);
            }
            else
            {
                // Snow melts faster in rain or direct sun
                float meltMult = isRaining ? 3.0f : 1.0f;
                _currentSnowCoverage = Mathf.MoveTowards(_currentSnowCoverage, 0f, _snowMeltPerGameHour * meltMult * gameHours);
            }

            // Water freezing/thawing follows the live temperature, in GAME time like the snow. The temperature is
            // sampled a couple of times a second rather than every frame - it changes over game minutes.
            _waterTempTimer -= dt;
            if (_waterTempTimer <= 0f && TimeSystem.Instance != null)
            {
                _waterTempTimer = 0.5f;
                _waterTempC = TimeSystem.Instance.Snapshot().TemperatureC;
            }
            if (_waterTempC < 0f)
                _waterFreeze = Mathf.MoveTowards(_waterFreeze, 1f, _freezePerGameHour * (1f + -_waterTempC / 5f) * gameHours);
            else if (_waterTempC > 0.5f)
                _waterFreeze = Mathf.MoveTowards(_waterFreeze, 0f, _thawPerGameHour * (1f + _waterTempC / 5f) * gameHours);
            Shader.SetGlobalFloat("_WaterFreeze", _waterFreeze);

            // Push global parameters to shaders (terrain, foliage, buildings)
            // X = SnowCoverage [0..1], Y = GroundWetness [0..1], Z = rain-now [0..1]
            float rainTarget = isRaining ? ((_currentWeather == HomesteaderWeather.Thunderstorm) ? 1.0f : 0.7f) : 0f;
            _currentRainNow = Mathf.MoveTowards(_currentRainNow, rainTarget, 0.5f * dt);
            Shader.SetGlobalVector("_WeatherGroundEffects", new Vector4(_currentSnowCoverage, _currentGroundWetness, _currentRainNow, 0f));
        }

        // ── Public API ───────────────────────────────────────────────────
        public void ApplyWeather(HomesteaderWeather weather)
        {
            if (_currentWeather == weather && _weatherInitialized) return;
            _weatherInitialized = true;
            _currentWeather = weather;

            StopLightning();

            switch (weather)
            {
                case HomesteaderWeather.Rain:
                    // Moderate rain when not storming (35% emission)
                    SetTargets(rain: 0.35f, snow: 0f, wind: 0f);
                    SetFog(false, 0.006f, new Color(0.45f, 0.48f, 0.52f, 1f));
                    break;

                case HomesteaderWeather.Thunderstorm:
                    // Full torrential storm rain + lightning + gusts
                    SetTargets(rain: 1f, snow: 0f, wind: 0.4f);
                    SetFog(true, 0.012f, new Color(0.30f, 0.32f, 0.36f, 1f));
                    StartLightning();
                    break;

                case HomesteaderWeather.Snow:
                    // Regular gentle snow - calm straight falling flakes (~1,500 particles at 2 m/s)
                    SetTargets(rain: 0f, snow: 0.20f, wind: 0f);
                    SetFog(true, 0.002f, new Color(0.62f, 0.67f, 0.75f, 1f));
                    ApplySnowVelocity(isBlizzard: false);
                    break;

                case HomesteaderWeather.Blizzard:
                    // Heavy Blizzard: 8,000 particles falling fast (6.5 m/s) and completely straight + gusts + fog
                    SetTargets(rain: 0f, snow: 1.0f, wind: 0.75f);
                    SetFog(true, 0.008f, new Color(0.66f, 0.72f, 0.82f, 1f));
                    ApplySnowVelocity(isBlizzard: true);
                    ToastNotificationSystem.ShowSevere("Blizzard Warning", "Severe blizzard conditions in effect. Temperature dropping rapidly. Click to dismiss.");
                    break;

                case HomesteaderWeather.Wind:
                    // Windy day with gentle scattered dust streaks
                    SetTargets(rain: 0f, snow: 0f, wind: 1f);
                    SetFog(false, 0.001f, Color.clear);
                    break;

                case HomesteaderWeather.Fog:
                    // Calm dense fog - zero wind or dust particles
                    SetTargets(rain: 0f, snow: 0f, wind: 0f);
                    SetFog(true, 0.035f, new Color(0.78f, 0.80f, 0.82f, 1f));
                    break;

                case HomesteaderWeather.Cloudy:
                    SetTargets(rain: 0f, snow: 0f, wind: 0f);
                    SetFog(false, 0.001f, Color.clear);
                    break;

                case HomesteaderWeather.PartlyCloudy:
                    SetTargets(rain: 0f, snow: 0f, wind: 0f);
                    SetFog(false, 0.001f, Color.clear);
                    break;

                case HomesteaderWeather.Sunny:
                default:
                    SetTargets(rain: 0f, snow: 0f, wind: 0f);
                    SetFog(false, 0.001f, Color.clear);
                    break;
            }
        }

        // ── Private helpers ──────────────────────────────────────────────
        private void SetTargets(float rain, float snow, float wind)
        {
            _rainEmission = rain;
            _snowEmission = snow;
            _windEmission = wind;
        }

        private void SetFog(bool enable, float density, Color color)
        {
            _fogEnabled = enable;
            _targetFogDensity = density;
            _targetFogColor = color;
        }

        // Directional light intensity and ambient are fully managed by DayNightCycle
        // based on time of day and weather. WeatherEffectsManager only triggers lightning
        // flashes and fog parameters.

        private void SmoothEmission()
        {
            UpdatePS(_rainPS, _rainEmission, _rainMaxParticles);
            UpdatePS(_rainSplashPS, _rainEmission * 0.45f, 500);
            UpdatePS(_snowPS, _snowEmission, _snowMaxParticles);
            UpdatePS(_windPS, _windEmission, _windMaxParticles);
        }

        private static void UpdatePS(ParticleSystem ps, float targetNorm, int maxParticles)
        {
            if (ps == null) return;
            var emission = ps.emission;
            float target = targetNorm * maxParticles;
            float current = emission.rateOverTime.constant;
            emission.rateOverTime = Mathf.MoveTowards(current, target, maxParticles * Time.unscaledDeltaTime * 1.5f);

            if (targetNorm > 0.01f && !ps.isPlaying) ps.Play();
            else if (targetNorm < 0.01f && emission.rateOverTime.constant < 0.5f) ps.Stop();
        }

        private void SmoothFog()
        {
            RenderSettings.fog = _fogEnabled || _fogBaseDensity > 0.001f;

            _fogBaseDensity = Mathf.MoveTowards(
                _fogBaseDensity,
                _fogEnabled ? _targetFogDensity : 0f,
                _fogFadeSpeed * Time.unscaledDeltaTime * 0.01f);
            // The orthographic camera sits far back from the action so nothing is clipped; fog is measured from the
            // camera, so scale the density down by the same ratio or everything in view greys out (the player too).
            RenderSettings.fogDensity = _fogBaseDensity * IsometricLockedCamera.FogCompensation;

            if (_fogEnabled && _targetFogColor != Color.clear)
            {
                RenderSettings.fogColor = Color.Lerp(
                    RenderSettings.fogColor, _targetFogColor, Time.unscaledDeltaTime * _fogFadeSpeed);
            }
        }

        // ── Dynamic Wind ─────────────────────────────────────────────────
        private void UpdateWind()
        {
            // Determine the wind intensity multiplier based on current weather
            float weatherWind = 0f;
            switch (_currentWeather)
            {
                case HomesteaderWeather.Thunderstorm: weatherWind = 1f; break;
                case HomesteaderWeather.Blizzard:     weatherWind = 0.85f; break;
                case HomesteaderWeather.Wind:        weatherWind = 0.6f; break;
                case HomesteaderWeather.Rain:        weatherWind = 0.2f; break;
                case HomesteaderWeather.Snow:        weatherWind = 0.15f; break;
                default:                             weatherWind = 0f; break;
            }

            // Periodically pick a new gust target: random direction + random speed
            _windGustTimer -= Time.unscaledDeltaTime;
            if (_windGustTimer <= 0f)
            {
                _windGustTimer = _windGustInterval * Random.Range(0.7f, 1.3f);
                // Real wind meanders rather than reversing outright: turn the target by a bounded amount from
                // its current heading instead of picking a fresh direction out of thin air each gust.
                float curAngle = Mathf.Atan2(_windDir.y, _windDir.x) * Mathf.Rad2Deg;
                float turn = Random.Range(-25f, 25f);
                float angle = (curAngle + turn) * Mathf.Deg2Rad;
                _windTargetDir = new Vector2(Mathf.Cos(angle), Mathf.Sin(angle));
                float maxSpeed = Mathf.Lerp(_windBaseSpeed, _windStormSpeed, weatherWind);
                _windTargetSpeed = maxSpeed * Random.Range(0.4f, 1f);
            }

            // If weather has no wind, ramp down to zero
            if (weatherWind < 0.01f)
                _windTargetSpeed = 0f;

            // Smoothly interpolate current speed toward target
            _windCurrentSpeed = Mathf.MoveTowards(_windCurrentSpeed, _windTargetSpeed, _windLerpSpeed * 20f * Time.unscaledDeltaTime);

            // Turn the direction gradually too — a hard snap to a new gust direction would instantly reverse the
            // velocity of every particle already in flight (velocityOverLifetime is re-evaluated every frame).
            // The heading turns at a capped, constant rate (default 1 degree a second) instead of easing toward
            // each new gust target. The easing was fast for a big turn - a 70 degree swing took a few seconds - and
            // everything downwind of the direction (grass, particles, water) visibly swung with it.
            float curDeg = Mathf.Atan2(_windDir.y, _windDir.x) * Mathf.Rad2Deg;
            float tgtDeg = Mathf.Atan2(_windTargetDir.y, _windTargetDir.x) * Mathf.Rad2Deg;
            float newDeg = Mathf.MoveTowardsAngle(curDeg, tgtDeg, _windMaxTurnDegPerSec * Time.unscaledDeltaTime);
            _windDir = new Vector2(Mathf.Cos(newDeg * Mathf.Deg2Rad), Mathf.Sin(newDeg * Mathf.Deg2Rad));

            // Apply wind force to all active particle systems
            ApplyWindToParticles();

            // Set global wind params for grass shader: (dirX, dirZ, speed, gust)
            Shader.SetGlobalVector("_GrassWindParams",
                new Vector4(_windDir.x, _windDir.y, _windCurrentSpeed, _windCurrentSpeed / Mathf.Max(1f, _windStormSpeed)));
        }

        private void ApplyWindToParticles()
        {
            if (_windCurrentSpeed < 0.01f) return;

            float wx = _windDir.x * _windCurrentSpeed;
            float wz = _windDir.y * _windCurrentSpeed;

            // Rain and snow keep a mostly-straight fall with only a gentle lean from wind: at full gust speed
            // (up to ~18 m/s in a storm) applying that directly as lateral velocity drifts particles tens of
            // metres sideways over their multi-second lifetime, carrying them out of the emitter box and leaving
            // only a lopsided sliver of the viewport filled depending on which way the wind is blowing. Precipitation
            // physically leans into wind far less than that, so scale it down to a small fraction of the gust.
            const float RainWindCoupling = 0.12f;
            const float SnowWindCoupling = 0.18f;

            // Rain: mostly falls down, but wind pushes it sideways
            if (_rainPS != null)
            {
                var vel = _rainPS.velocityOverLifetime;
                vel.enabled = true;
                vel.space = ParticleSystemSimulationSpace.World;
                vel.x = new ParticleSystem.MinMaxCurve(wx * RainWindCoupling * 0.85f, wx * RainWindCoupling);
                vel.y = new ParticleSystem.MinMaxCurve(-_rainSpeed, -_rainSpeed);
                vel.z = new ParticleSystem.MinMaxCurve(wz * RainWindCoupling * 0.85f, wz * RainWindCoupling);
            }

            // Snow: light, so wind pushes it a bit more than rain, but still nowhere near full gust speed
            if (_snowPS != null)
            {
                var vel = _snowPS.velocityOverLifetime;
                vel.enabled = true;
                vel.space = ParticleSystemSimulationSpace.World;
                float snowFall = (_currentWeather == HomesteaderWeather.Blizzard) ? _blizzardSnowSpeed : _snowSpeed;
                vel.x = new ParticleSystem.MinMaxCurve(wx * SnowWindCoupling * 0.85f, wx * SnowWindCoupling);
                vel.y = new ParticleSystem.MinMaxCurve(-snowFall, -snowFall);
                vel.z = new ParticleSystem.MinMaxCurve(wz * SnowWindCoupling * 0.85f, wz * SnowWindCoupling);
            }

            // Wind streaks: blow in the wind direction at the current speed
            if (_windPS != null)
            {
                var vel = _windPS.velocityOverLifetime;
                vel.enabled = true;
                vel.space = ParticleSystemSimulationSpace.World;
                vel.x = new ParticleSystem.MinMaxCurve(wx * 0.9f, wx * 1.1f);
                vel.y = new ParticleSystem.MinMaxCurve(-0.3f, 0.3f);
                vel.z = new ParticleSystem.MinMaxCurve(wz * 0.9f, wz * 1.1f);

                // Also rotate the emitter box to align with wind direction
                float yawDeg = Mathf.Atan2(_windDir.y, _windDir.x) * Mathf.Rad2Deg;
                _windPS.transform.rotation = Quaternion.Euler(0f, yawDeg, 0f);
            }
        }

        private void AnchorToCamera()
        {
            // Center the weather box over the camera's viewport center, not just the player.
            // In isometric view the camera is offset from the player by the orbit radius,
            // so the viewport center is between the camera and the player — not at the player.
            Vector3 centerPos;
            if (_cachedCam != null && _cachedPlayer != null)
            {
                // Use the camera's viewport center: the point on the ground that the camera looks at.
                // The player is the focal point; the camera is offset behind/above by the orbit radius.
                // The midpoint between camera and player on the XZ plane is the viewport center.
                Vector3 camPos = _cachedCam.transform.position;
                Vector3 playerPos = _cachedPlayer.position;
                centerPos = new Vector3(
                    (camPos.x + playerPos.x) * 0.5f,
                    playerPos.y,
                    (camPos.z + playerPos.z) * 0.5f);
            }
            else if (_cachedPlayer != null)
            {
                centerPos = _cachedPlayer.position;
            }
            else if (_cachedCam != null)
            {
                centerPos = _cachedCam.transform.position;
            }
            else
            {
                return;
            }

            // Align emitter volume with camera orientation so "top", "left", "right"
            // and perspective depth match the view frustum seamlessly.
            Quaternion camRot = (_cachedCam != null) ? _cachedCam.transform.rotation : Quaternion.identity;

            // centerPos is the viewport-center ground point (the midpoint between camera and player). A large
            // forward shift here used to push the whole emitter away from the camera to "cover the far half" of
            // the screen, which starved the near/bottom half - wind blowing further away emptied everything but a
            // thin strip at the top, and even at rest the bottom third of the screen got no coverage. A small pull
            // *toward* the camera instead keeps the near/bottom edge of the screen filled too.
            Vector3 camFwd = (_cachedCam != null) ? _cachedCam.transform.forward : Vector3.forward;
            camFwd.y = 0f;
            camFwd.Normalize();
            float forwardOffset = -_emitterHalfDepth * 0.2f;

            // In isometric/perspective view, offsetting the emitter up prevents the lower
            // viewport area from having a gap in falling precipitation.
            Vector3 aboveCenter = new Vector3(
                centerPos.x + camFwd.x * forwardOffset,
                centerPos.y + _emitterHeight,
                centerPos.z + camFwd.z * forwardOffset);
            if (_rainPS)
            {
                _rainPS.transform.position = aboveCenter;
                _rainPS.transform.rotation = Quaternion.Euler(0f, camRot.eulerAngles.y, 0f);
            }
            if (_snowPS)
            {
                _snowPS.transform.position = aboveCenter;
                _snowPS.transform.rotation = Quaternion.Euler(0f, camRot.eulerAngles.y, 0f);
            }

            // Splashes: sit at ground level right around player
            Vector3 atGround = new Vector3(centerPos.x, centerPos.y + 0.1f, centerPos.z);
            if (_rainSplashPS)
            {
                _rainSplashPS.transform.position = atGround;
            }

            // Wind: emit at waist/eye level
            Vector3 midCenter = new Vector3(centerPos.x, centerPos.y + 2.5f, centerPos.z);
            if (_windPS)
            {
                _windPS.transform.position = midCenter;
            }
        }

        private void CacheDirectionalLight()
        {
            var lights = FindObjectsByType<Light>(FindObjectsInactive.Exclude);
            foreach (var l in lights)
            {
                if (l.type == LightType.Directional)
                {
                    _directionalLight = l;
                    _baseLightIntensity = l.intensity;
                    break;
                }
            }
        }

        // ── Particle System Construction ────────────────────────────────

        /// <summary>
        /// Creates a transparent unlit material compatible with URP.
        /// Tries URP Particles/Unlit first, then Sprites/Default, then a minimal fallback.
        /// </summary>
        private static Material CreateParticleMaterial(Color color, Texture2D texture = null)
        {
            // Ordered preference: URP particle unlit → legacy Particles/Alpha Blended → Sprites/Default
            string[] shaderNames = new[]
            {
                "Universal Render Pipeline/Particles/Unlit",
                "Particles/Standard Unlit",
                "Particles/Alpha Blended",
                "Sprites/Default",
                "UI/Default",
            };

            Shader shader = null;
            foreach (var name in shaderNames)
            {
                shader = Shader.Find(name);
                if (shader != null) break;
            }

            if (shader == null)
            {
                // Absolute fallback: use the built-in default sprite shader
                var mat = new Material(Shader.Find("Hidden/InternalErrorShader") ?? Shader.Find("Standard"));
                if (mat != null) mat.color = color;
                return mat;
            }

            var m = new Material(shader)
            {
                hideFlags = HideFlags.HideAndDontSave
            };

            // URP Unlit surface blending - standard straight alpha
            m.SetFloat("_Surface", 1);      // Transparent
            m.SetFloat("_Blend", 0);        // Alpha
            m.SetFloat("_AlphaClip", 0);
            m.SetInt("_SrcBlend", (int)UnityEngine.Rendering.BlendMode.SrcAlpha);
            m.SetInt("_DstBlend", (int)UnityEngine.Rendering.BlendMode.OneMinusSrcAlpha);
            m.SetInt("_ZWrite", 0);
            m.SetInt("_Cull", 0);           // Off - particles must be visible from all angles
            m.renderQueue = (int)UnityEngine.Rendering.RenderQueue.Transparent;
            m.SetColor("_BaseColor", color);
            m.SetColor("_Color", color);     // Legacy fallback property name

            // Enable the transparent surface keyword for URP Particles/Unlit
            m.EnableKeyword("_SURFACE_TYPE_TRANSPARENT");

            // Explicitly disable pre-multiplied alpha to avoid black borders/halos
            m.DisableKeyword("_ALPHAPREMULTIPLY_ON");
            m.DisableKeyword("_ALPHAMODULATE_ON");

            if (texture != null)
            {
                m.SetTexture("_BaseMap", texture);
                m.SetTexture("_MainTex", texture);
            }

            return m;
        }

        /// <summary>A small soft radial-gradient dot, generated at runtime since there's no dust/streak art asset:
        /// without a texture the particle renders as an opaque hard-edged quad, which reads as a big square.</summary>
        private static Texture2D CreateSoftDotTexture()
        {
            const int size = 32;
            var tex = new Texture2D(size, size, TextureFormat.RGBA32, false) { hideFlags = HideFlags.HideAndDontSave };
            float center = (size - 1) * 0.5f;
            for (int y = 0; y < size; y++)
            {
                for (int x = 0; x < size; x++)
                {
                    float d = Vector2.Distance(new Vector2(x, y), new Vector2(center, center)) / center;
                    float a = Mathf.Clamp01(1f - d);
                    a = a * a; // softer falloff toward the edge
                    tex.SetPixel(x, y, new Color(1f, 1f, 1f, a));
                }
            }
            tex.Apply(false);
            return tex;
        }

        private void BuildParticleSystems()
        {
            var raindropTex = Resources.Load<Texture2D>("WeatherFX/tex_raindrop");
            var snowflakeTex = Resources.Load<Texture2D>("WeatherFX/tex_snowflake");
            var splashTex = Resources.Load<Texture2D>("WeatherFX/tex_splash");
            var windTex = CreateSoftDotTexture(); // no art asset for this one: a plain quad renders as a hard square

            _rainPS = CreatePS("WeatherFX_Rain", Color.white, raindropTex);
            ConfigureRain(_rainPS);

            _rainSplashPS = CreatePS("WeatherFX_RainSplash", Color.white, splashTex);
            ConfigureRainSplash(_rainSplashPS);

            _snowPS = CreatePS("WeatherFX_Snow", Color.white, snowflakeTex);
            ConfigureSnow(_snowPS);

            _windPS = CreatePS("WeatherFX_Wind", new Color(0.85f, 0.82f, 0.75f, 0.35f), windTex);
            ConfigureWind(_windPS);
        }

        private ParticleSystem CreatePS(string psName, Color particleColor, Texture2D texture = null)
        {
            var go = new GameObject(psName);
            go.transform.SetParent(transform);
            var ps = go.AddComponent<ParticleSystem>();
            ps.Stop(true, ParticleSystemStopBehavior.StopEmittingAndClear);

            var main = ps.main;
            main.loop = true;
            main.duration = 999f;
            // These are camera-anchored (repositioned onto the view every frame) so Unity's frustum culling can
            // wrongly decide the emitter box isn't visible yet and freeze the whole system before it ever gets a
            // bounds it can see - Automatic culling then never lets it simulate. Always simulate instead.
            main.cullingMode = ParticleSystemCullingMode.AlwaysSimulate;
            // Real time, so rain/snow keep falling while the game is paused.
            main.useUnscaledTime = true;

            // Assign material so particles don't render as magenta error quads
            var renderer = ps.GetComponent<ParticleSystemRenderer>();
            renderer.material = CreateParticleMaterial(particleColor, texture);
            renderer.trailMaterial = renderer.material;
            // Disable shadow casting and receiving for transparent weather particles
            renderer.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            renderer.receiveShadows = false;

            return ps;
        }

        private void ConfigureRain(ParticleSystem ps)
        {
            var main = ps.main;
            main.maxParticles = _rainMaxParticles;
            main.startLifetime = new ParticleSystem.MinMaxCurve(0.7f, 1.0f);
            main.startSpeed = new ParticleSystem.MinMaxCurve(_rainSpeed * 0.95f, _rainSpeed * 1.05f);
            main.startSize = new ParticleSystem.MinMaxCurve(_rainSize * 0.8f, _rainSize * 1.2f);
            main.startColor = new ParticleSystem.MinMaxGradient(new Color(0.88f, 0.94f, 1.00f, 0.60f));
            main.gravityModifier = 0f;
            main.simulationSpace = ParticleSystemSimulationSpace.World;

            var emission = ps.emission;
            emission.rateOverTime = 0f;

            var shape = ps.shape;
            shape.enabled = true;
            shape.shapeType = ParticleSystemShapeType.Box;
            shape.scale = new Vector3(_emitterHalfWidth * 2f, 0.1f, _emitterHalfDepth * 2f);

            var vel = ps.velocityOverLifetime;
            vel.enabled = true;
            vel.space = ParticleSystemSimulationSpace.World;
            // Fall almost straight down with minuscule air drift (0.1m)
            vel.x = new ParticleSystem.MinMaxCurve(-0.1f, 0.1f);
            vel.y = new ParticleSystem.MinMaxCurve(-_rainSpeed, -_rainSpeed);
            vel.z = new ParticleSystem.MinMaxCurve(-0.1f, 0.1f);

            var r = ps.GetComponent<ParticleSystemRenderer>();
            r.renderMode = ParticleSystemRenderMode.Stretch;
            r.lengthScale = 3.5f;
            r.velocityScale = 0.015f;
            r.material.enableInstancing = true;
        }

        private void ConfigureRainSplash(ParticleSystem ps)
        {
            var main = ps.main;
            main.maxParticles = 600;
            main.startLifetime = new ParticleSystem.MinMaxCurve(0.12f, 0.22f);
            main.startSpeed = new ParticleSystem.MinMaxCurve(0.1f, 0.3f);
            main.startSize = new ParticleSystem.MinMaxCurve(0.12f, 0.24f);
            main.startColor = new Color(0.85f, 0.92f, 1.00f, 0.50f);
            main.gravityModifier = 0f;
            main.simulationSpace = ParticleSystemSimulationSpace.World;

            var emission = ps.emission;
            emission.rateOverTime = 0f;

            var shape = ps.shape;
            shape.enabled = true;
            shape.shapeType = ParticleSystemShapeType.Box;
            shape.scale = new Vector3(_emitterHalfWidth * 2f, 0.2f, _emitterHalfDepth * 2f);

            // Expanding ripple size over lifetime
            var sol = ps.sizeOverLifetime;
            sol.enabled = true;
            AnimationCurve curve = new AnimationCurve();
            curve.AddKey(0f, 0.4f);
            curve.AddKey(1f, 1.2f);
            sol.size = new ParticleSystem.MinMaxCurve(1f, curve);

            // Fade out
            var col = ps.colorOverLifetime;
            col.enabled = true;
            Gradient grad = new Gradient();
            grad.SetKeys(
                new GradientColorKey[] { new GradientColorKey(Color.white, 0f), new GradientColorKey(Color.white, 1f) },
                new GradientAlphaKey[] { new GradientAlphaKey(0.6f, 0f), new GradientAlphaKey(0f, 1f) }
            );
            col.color = grad;

            var r = ps.GetComponent<ParticleSystemRenderer>();
            r.renderMode = ParticleSystemRenderMode.HorizontalBillboard;
        }

        private void ConfigureSnow(ParticleSystem ps)
        {
            var main = ps.main;
            main.maxParticles = _snowMaxParticles;
            main.startLifetime = new ParticleSystem.MinMaxCurve(6f, 9f);
            main.startSpeed = new ParticleSystem.MinMaxCurve(_snowSpeed * 0.85f, _snowSpeed * 1.15f);
            main.startSize = new ParticleSystem.MinMaxCurve(_snowSize * 0.7f, _snowSize * 1.3f);
            main.startColor = new Color(1.00f, 1.00f, 1.00f, 0.85f);
            main.gravityModifier = 0f;
            main.simulationSpace = ParticleSystemSimulationSpace.World;

            var emission = ps.emission;
            emission.rateOverTime = 0f;

            var shape = ps.shape;
            shape.enabled = true;
            shape.shapeType = ParticleSystemShapeType.Box;
            shape.scale = new Vector3(_emitterHalfWidth * 2f, 0.1f, _emitterHalfDepth * 2f);

            var vel = ps.velocityOverLifetime;
            vel.enabled = true;
            vel.space = ParticleSystemSimulationSpace.World;
            // Float almost straight down with gentle tiny lateral flutter (0.15m)
            vel.x = new ParticleSystem.MinMaxCurve(-0.15f, 0.15f);
            vel.y = new ParticleSystem.MinMaxCurve(-_snowSpeed, -_snowSpeed);
            vel.z = new ParticleSystem.MinMaxCurve(-0.15f, 0.15f);

            // Billboard so flakes face camera (appear round/soft, not square)
            var r = ps.GetComponent<ParticleSystemRenderer>();
            r.renderMode = ParticleSystemRenderMode.Billboard;
        }

        private void ApplySnowVelocity(bool isBlizzard)
        {
            if (_snowPS == null) return;
            var vel = _snowPS.velocityOverLifetime;
            vel.enabled = true;
            vel.space = ParticleSystemSimulationSpace.World;

            float speed = isBlizzard ? _blizzardSnowSpeed : _snowSpeed;
            // Blizzard falls fast (6.5 m/s) and perfectly straight down (0 lateral drift)
            float lateral = isBlizzard ? 0f : 0.15f;
            vel.x = new ParticleSystem.MinMaxCurve(-lateral, lateral);
            vel.y = new ParticleSystem.MinMaxCurve(-speed, -speed);
            vel.z = new ParticleSystem.MinMaxCurve(-lateral, lateral);

            var main = _snowPS.main;
            // Shorter lifetime when falling faster so particles don't overshoot below the ground
            main.startLifetime = isBlizzard ? new ParticleSystem.MinMaxCurve(2.5f, 3.5f) : new ParticleSystem.MinMaxCurve(6f, 9f);
        }

        private void ConfigureWind(ParticleSystem ps)
        {
            var main = ps.main;
            main.maxParticles = _windMaxParticles;
            main.startLifetime = new ParticleSystem.MinMaxCurve(1.5f, 3f);
            main.startSpeed = new ParticleSystem.MinMaxCurve(_windSpeed * 0.8f, _windSpeed * 1.2f);
            main.startSize = new ParticleSystem.MinMaxCurve(_windSize * 0.5f, _windSize * 2f);
            main.startColor = new Color(0.80f, 0.78f, 0.70f, 0.35f);
            main.simulationSpace = ParticleSystemSimulationSpace.World;

            var emission = ps.emission;
            emission.rateOverTime = 0f;

            var shape = ps.shape;
            shape.enabled = true;
            shape.shapeType = ParticleSystemShapeType.Box;
            shape.scale = new Vector3(_emitterHalfWidth * 2f, 4f, _emitterHalfDepth * 2f);

            // Velocity is set dynamically by ApplyWindToParticles() each frame
            var vel = ps.velocityOverLifetime;
            vel.enabled = true;
            vel.space = ParticleSystemSimulationSpace.World;
            vel.x = new ParticleSystem.MinMaxCurve(0f, 0f);
            vel.y = new ParticleSystem.MinMaxCurve(-0.3f, 0.3f);
            vel.z = new ParticleSystem.MinMaxCurve(0f, 0f);
        }

        // ── Lightning ────────────────────────────────────────────────────
        private void StartLightning()
        {
            if (_lightningRoutine != null) StopCoroutine(_lightningRoutine);
            _lightningRoutine = StartCoroutine(LightningRoutine());
        }

        private void StopLightning()
        {
            if (_lightningRoutine != null)
            {
                StopCoroutine(_lightningRoutine);
                _lightningRoutine = null;
            }
        }

        // ── Visible bolt at a struck tree ────────────────────────────────

        [SerializeField] private float _boltFadeSeconds = 0.8f;   // how long the bolt stays visible
        [SerializeField] private float _boltStartHeight = 40f;     // how high above the tree the bolt appears
        [SerializeField] private float _boltJitter = 1.6f;         // metres a segment can wander sideways
        [SerializeField] private int _boltSegments = 14;
        [SerializeField] private float _boltWidth = 0.32f;
        [SerializeField] private Color _boltColor = new Color(0.82f, 0.90f, 1.00f, 1f);

        private static AudioClip _thunderClip;

        /// <summary>
        /// Draws a jagged lightning bolt from the sky down to the struck tree: an additive LineRenderer with
        /// random sideways jitter, one short branch offshoot, a bright glow light and dust burst at the impact,
        /// and a thunder crack. Everything fades out together over _boltFadeSeconds and is then removed.
        /// </summary>
        private void SpawnLightningBolt(Vector3 treePos)
        {
            var root = new GameObject("LightningBolt");
            var fade = root.AddComponent<BoltFade>();
            fade.Life = _boltFadeSeconds;

            // Main channel: sky to treetop, wandering sideways as it falls.
            Vector3 top = treePos + Vector3.up * _boltStartHeight;
            var points = new Vector3[_boltSegments + 1];
            points[0] = top;
            points[_boltSegments] = treePos + Vector3.up * 0.1f;
            for (int i = 1; i < _boltSegments; i++)
            {
                float t = i / (float)_boltSegments;
                Vector3 p = Vector3.Lerp(top, points[_boltSegments], t);
                // Tighten the jitter near the strike so it lands on the tree.
                p.x += Random.Range(-_boltJitter, _boltJitter) * t;
                p.z += Random.Range(-_boltJitter, _boltJitter) * t;
                points[i] = p;
            }

            var lr = root.AddComponent<LineRenderer>();
            lr.positionCount = points.Length;
            lr.SetPositions(points);
            lr.useWorldSpace = true;
            lr.widthCurve = new AnimationCurve(
                new Keyframe(0f, 1.0f), new Keyframe(0.7f, 0.7f), new Keyframe(1f, 1.6f));   // wider at the impact
            lr.widthMultiplier = _boltWidth;
            lr.numCapVertices = 2;
            lr.numCornerVertices = 2;
            lr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            lr.receiveShadows = false;

            Shader shader = Shader.Find("Universal Render Pipeline/Particles/Unlit")
                            ?? Shader.Find("Sprites/Default");
            var mat = new Material(shader) { hideFlags = HideFlags.DontSave };
            mat.SetColor("_BaseColor", _boltColor);
            if (mat.HasProperty("_Surface")) { mat.SetFloat("_Surface", 1f); mat.SetInt("_SrcBlend", (int)UnityEngine.Rendering.BlendMode.SrcAlpha); mat.SetInt("_DstBlend", (int)UnityEngine.Rendering.BlendMode.One); mat.SetInt("_ZWrite", 0); }
            mat.renderQueue = 3000;
            lr.material = mat;

            // One branch: splits off a middle segment and streaks away, rejoining nothing.
            int branchAt = Random.Range(4, _boltSegments - 3);
            // (a GameObject can hold only one LineRenderer: AddComponent on the root returned null here, which threw and cut the bolt short)
            var branchGo = new GameObject("BoltBranch");
            branchGo.transform.SetParent(root.transform, false);
            var branch = branchGo.AddComponent<LineRenderer>();
            Vector3 b0 = points[branchAt];
            Vector3 b1 = b0 + new Vector3(Random.Range(-3f, 3f), -Random.Range(2f, 5f), Random.Range(-3f, 3f));
            Vector3 b2 = b1 + new Vector3(Random.Range(-2f, 2f), -Random.Range(1f, 3f), Random.Range(-2f, 2f));
            branch.positionCount = 3;
            branch.SetPositions(new[] { b0, b1, b2 });
            branch.useWorldSpace = true;
            branch.widthMultiplier = _boltWidth * 0.5f;
            branch.numCapVertices = 2;
            branch.material = mat;
            branch.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;

            // The flash: a short-lived bright light right at the tree.
            var lightGo = new GameObject("BoltLight");
            lightGo.transform.SetParent(root.transform, false);
            lightGo.transform.position = treePos + Vector3.up * 2f;
            Light light = lightGo.AddComponent<Light>();
            light.type = LightType.Point;
            light.color = _boltColor;
            light.intensity = 12f;
            light.range = 30f;
            light.shadows = LightShadows.None;
            fade.Light = light;

            // Scorched burst at the impact: the wood-chip system already exists, reuse it in reverse (toward the sky).
            ForestTreesSpawnChips(treePos + Vector3.up * 1.2f, Vector3.up);

            // A thunder crack follows the bolt (a rough burst of decaying noise).
            PlayThunder(treePos);

            root.hideFlags = HideFlags.None;
        }

        // ForestTrees.SpawnChips is private; this tiny helper keeps the bolt code free of reflection.
        private static void ForestTreesSpawnChips(Vector3 at, Vector3 toward)
        {
            var method = typeof(World.ForestTrees).GetMethod("SpawnChips",
                System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Static);
            method?.Invoke(null, new object[] { at, toward });
        }

        /// <summary>A sharp thunder crack: filtered noise with a fast decay and a low rumble tail, made in code.</summary>
        private static void PlayThunder(Vector3 at)
        {
            var audio = Homesteader.Audio.AudioManager.Instance;
            if (audio == null) return;
            if (_thunderClip == null)
            {
                const int rate = 44100;
                int n = (int)(rate * 1.6f);
                var data = new float[n];
                var rng = new System.Random(901);
                float lp = 0f, rumble = 0f;
                for (int i = 0; i < n; i++)
                {
                    float t = i / (float)rate;
                    float crack = (((float)rng.NextDouble() * 2f - 1f) - lp) * 0.6f * Mathf.Exp(-t * 14f);
                    lp += crack;
                    rumble += (((float)rng.NextDouble() * 2f - 1f) - rumble) * 0.04f * Mathf.Exp(-t * 1.8f);
                    data[i] = Mathf.Clamp(crack * 0.9f + rumble * 0.8f, -1f, 1f);
                }
                _thunderClip = AudioClip.Create("ThunderCrack", n, 1, rate, false);
                _thunderClip.SetData(data, 0);
            }
            audio.PlaySfx2D(_thunderClip, 0.85f);
        }

        /// <summary>Fades a spawned bolt (lines, glow light) out and removes it. Lives on the bolt's root object.</summary>
        private sealed class BoltFade : MonoBehaviour
        {
            public float Life = 0.55f;
            public Light Light;
            private float _t;
            private LineRenderer[] _lines;
            private Color[] _start;

            // Start, not Awake: the bolt's lines are added to this object right after the component, so they did not exist yet in Awake
            // (nothing was found to fade).
            private void Start()
            {
                _lines = GetComponentsInChildren<LineRenderer>();
                _start = new Color[_lines.Length];
                for (int i = 0; i < _lines.Length; i++)
                {
                    Material m = _lines[i].material;
                    _start[i] = m != null && m.HasProperty("_BaseColor") ? m.GetColor("_BaseColor") : Color.white;
                }
            }

            private void Update()
            {
                _t += Time.unscaledDeltaTime;
                if (_lines == null) return;   // Start has not run yet
                float k = 1f - Mathf.Clamp01(_t / Life);
                for (int i = 0; i < _lines.Length; i++)
                {
                    Material m = _lines[i].material;
                    if (m != null && m.HasProperty("_BaseColor"))
                        m.SetColor("_BaseColor", _start[i] * new Color(1f, 1f, 1f, k));
                }
                if (Light != null) Light.intensity = 12f * k * k;
                if (_t >= Life) Destroy(gameObject);
            }
        }

        private IEnumerator LightningRoutine()
        {
            // Store pre-flash ambient settings to restore perfectly
            float origAmbientIntensity = RenderSettings.ambientIntensity;
            Color origAmbientLight = RenderSettings.ambientLight;

            while (_currentWeather == HomesteaderWeather.Thunderstorm)
            {
                while (TimeSystem.Instance.IsPaused)
                {
                    yield return null;
                }

                // Random wait between flashes
                yield return new WaitForSecondsRealtime(
                    Random.Range(_lightningMinInterval, _lightningMaxInterval));

                if (_currentWeather != HomesteaderWeather.Thunderstorm || TimeSystem.Instance.IsPaused) continue;

                // Each flash has a 5% chance to kill the nearest standing procedural tree in the storm area:
                // a jagged bolt is drawn from the sky down to it, with a flash and a thunder crack.
                Vector3 strikeOrigin = _cachedPlayer != null ? _cachedPlayer.position : transform.position;
                if (World.ForestTrees.TryStrikeLightning(strikeOrigin, _lightningTreeStrikeRadius, _lightningTreeStrikeChance, out Vector3 struckTree))
                {
                    SpawnLightningBolt(struckTree);
                    Dbg.Log($"[Weather] Lightning struck a tree at ({struckTree.x:F0}, {struckTree.z:F0}); it is now dead.");
                }

                // ── First pulse ──────────────────────────────────────────────
                // Set LightningBoost to 4×; DayNightCycle reads this and applies it
                // on top of its own weather-dimmed intensity each frame
                LightningBoost = 4.5f;
                RenderSettings.ambientIntensity = 3.5f;
                RenderSettings.ambientLight = new Color(0.85f, 0.90f, 1.00f);
                yield return new WaitForSecondsRealtime(_lightningFlashDuration * 0.35f);

                // Brief dark gap between double-flash
                LightningBoost = 1f;
                RenderSettings.ambientIntensity = origAmbientIntensity;
                RenderSettings.ambientLight = origAmbientLight;
                yield return new WaitForSecondsRealtime(_lightningFlashDuration * 0.25f);

                // ── Second pulse (dimmer) ───────────────────────────────────
                LightningBoost = 3.2f;
                RenderSettings.ambientIntensity = 2.5f;
                RenderSettings.ambientLight = new Color(0.80f, 0.86f, 1.00f);
                yield return new WaitForSecondsRealtime(_lightningFlashDuration * 0.45f);

                // ── Return to normal storm lighting ─────────────────────────
                LightningBoost = 1f;
                RenderSettings.ambientIntensity = origAmbientIntensity;
                RenderSettings.ambientLight = origAmbientLight;
            }

            // Ensure boost and ambient are completely restored when loop exits
            LightningBoost = 1f;
            RenderSettings.ambientIntensity = origAmbientIntensity;
            RenderSettings.ambientLight = origAmbientLight;
        }
    }
}
