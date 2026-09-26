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
        [SerializeField] private float _emitterHalfWidth = 35f;
        [SerializeField] private float _emitterHalfDepth = 35f;
        [SerializeField] private float _emitterHeight = 16f;

        [Header("Rain")]
        [SerializeField] private int _rainMaxParticles = 2400;
        [SerializeField] private float _rainSpeed = 16f;
        [SerializeField] private float _rainSize = 0.024f;

        [Header("Snow")]
        [SerializeField] private int _snowMaxParticles = 8000;
        [SerializeField] private float _snowSpeed = 2.0f;
        [SerializeField] private float _blizzardSnowSpeed = 6.5f;
        [SerializeField] private float _snowSize = 0.045f;

        [Header("Wind")]
        [SerializeField] private int _windMaxParticles = 180;
        [SerializeField] private float _windSpeed = 10f;
        [SerializeField] private float _windSize = 0.035f;

        [Header("Fog")]
        [SerializeField] private float _fogFadeSpeed = 0.6f;  // units/sec

        [Header("Lightning")]
        [SerializeField] private float _lightningMinInterval = 4f;
        [SerializeField] private float _lightningMaxInterval = 14f;
        [SerializeField] private float _lightningFlashDuration = 0.12f;

        [Header("Accumulation Dynamics")]
        [SerializeField] private float _snowAccumulationPerGameHour = 0.4f; // 1.0 = about one inch: 2.5 game hours of normal snow, 1 hour in a blizzard (x2.5)
        [SerializeField] private float _snowMeltPerGameHour = 0.3f;      // snow melt per game hour when not snowing (an inch in ~3 hours; rain x3)
        [SerializeField] private float _wetnessGainRate = 0.008f;       // wetness gain per second during rain (~2 min to soak)
        [SerializeField] private float _wetnessDryingRate = 0.006f;     // drying per second without rain (~3 min to dry out)

        // ── Runtime state ────────────────────────────────────────────────
        private ParticleSystem _rainPS;
        private ParticleSystem _rainSplashPS;
        private ParticleSystem _snowPS;
        private ParticleSystem _windPS;

        private Camera _cachedCam;
        private Transform _cachedPlayer;

        private float _currentSnowCoverage = 0f;
        private float _currentGroundWetness = 0f;
        private float _currentRainNow = 0f;   // smoothed 0..1 "raining right now" for ripples

        private HomesteaderWeather _currentWeather = HomesteaderWeather.Sunny;
        private float _targetFogDensity;
        private Color _targetFogColor;
        private bool _fogEnabled;

        private Light _directionalLight;
        private float _baseLightIntensity;
        private Coroutine _lightningRoutine;

        // Transition smoothing
        private float _rainEmission;
        private float _snowEmission;
        private float _windEmission;

        private static WeatherEffectsManager s_instance;
        public static WeatherEffectsManager Instance => s_instance;

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
            }

            SmoothEmission();
            SmoothFog();
            UpdateGroundAccumulation();
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
                    var isoCam = FindAnyObjectByType<IsometricLockedCamera>();
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
                    var ped = FindAnyObjectByType<PedController>();
                    if (ped != null) _cachedPlayer = ped.transform;
                }
            }
        }

        private void UpdateGroundAccumulation()
        {
            float dt = Time.deltaTime;
            // Snow depth follows GAME time (so it respects the time-speed setting), not real seconds.
            float gameHours = 0f;
            if (TimeSystem.Instance != null)
            {
                gameHours = dt * TimeConstants.GameMinutesPerRealSecondAt1X
                            * TimeSystem.SpeedToMultiplier(TimeSystem.Instance.CurrentSpeed) / 60f;
            }
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

            // Push global parameters to shaders (terrain, foliage, buildings)
            // X = SnowCoverage [0..1], Y = GroundWetness [0..1], Z = rain-now [0..1]
            float rainTarget = isRaining ? ((_currentWeather == HomesteaderWeather.Thunderstorm) ? 1.0f : 0.7f) : 0f;
            _currentRainNow = Mathf.MoveTowards(_currentRainNow, rainTarget, 0.5f * dt);
            Shader.SetGlobalVector("_WeatherGroundEffects", new Vector4(_currentSnowCoverage, _currentGroundWetness, _currentRainNow, 0f));
        }

        // ── Public API ───────────────────────────────────────────────────
        public void ApplyWeather(HomesteaderWeather weather)
        {
            if (_currentWeather == weather) return;
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
            emission.rateOverTime = Mathf.MoveTowards(current, target, maxParticles * Time.deltaTime * 1.5f);

            if (targetNorm > 0.01f && !ps.isPlaying) ps.Play();
            else if (targetNorm < 0.01f && emission.rateOverTime.constant < 0.5f) ps.Stop();
        }

        private void SmoothFog()
        {
            RenderSettings.fog = _fogEnabled || RenderSettings.fogDensity > 0.001f;

            RenderSettings.fogDensity = Mathf.MoveTowards(
                RenderSettings.fogDensity,
                _fogEnabled ? _targetFogDensity : 0f,
                _fogFadeSpeed * Time.deltaTime * 0.01f);

            if (_fogEnabled && _targetFogColor != Color.clear)
            {
                RenderSettings.fogColor = Color.Lerp(
                    RenderSettings.fogColor, _targetFogColor, Time.deltaTime * _fogFadeSpeed);
            }
        }

        private void AnchorToCamera()
        {
            // Center the weather box over the active player focal point or camera view
            Vector3 centerPos;
            if (_cachedPlayer != null)
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

            // In isometric/perspective view, offsetting the emitter slightly up-camera prevents
            // the near-ground or lower viewport area from having a gap in falling precipitation.
            Vector3 aboveCenter = new Vector3(centerPos.x, centerPos.y + _emitterHeight, centerPos.z);
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
            m.renderQueue = (int)UnityEngine.Rendering.RenderQueue.Transparent;
            m.SetColor("_BaseColor", color);
            m.SetColor("_Color", color);     // Legacy fallback property name

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

        private void BuildParticleSystems()
        {
            var raindropTex = Resources.Load<Texture2D>("WeatherFX/tex_raindrop");
            var snowflakeTex = Resources.Load<Texture2D>("WeatherFX/tex_snowflake");
            var splashTex = Resources.Load<Texture2D>("WeatherFX/tex_splash");

            _rainPS = CreatePS("WeatherFX_Rain", Color.white, raindropTex);
            ConfigureRain(_rainPS);

            _rainSplashPS = CreatePS("WeatherFX_RainSplash", Color.white, splashTex);
            ConfigureRainSplash(_rainSplashPS);

            _snowPS = CreatePS("WeatherFX_Snow", Color.white, snowflakeTex);
            ConfigureSnow(_snowPS);

            _windPS = CreatePS("WeatherFX_Wind", new Color(0.85f, 0.82f, 0.75f, 0.35f), null);
            ConfigureWind(_windPS);
        }

        private ParticleSystem CreatePS(string psName, Color particleColor, Texture2D texture = null)
        {
            var go = new GameObject(psName);
            go.transform.SetParent(transform);
            var ps = go.AddComponent<ParticleSystem>();
            ps.Stop(true, ParticleSystemStopBehavior.StopEmittingAndClear);

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
            main.startColor = new Color(0.88f, 0.94f, 1.00f, 0.60f);
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

            var vel = ps.velocityOverLifetime;
            vel.enabled = true;
            vel.space = ParticleSystemSimulationSpace.World;
            vel.x = new ParticleSystem.MinMaxCurve(_windSpeed * 0.9f, _windSpeed * 1.1f);
            vel.y = new ParticleSystem.MinMaxCurve(-0.3f, 0.3f);
            vel.z = new ParticleSystem.MinMaxCurve(-0.5f, 0.5f);
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
                yield return new WaitForSeconds(
                    Random.Range(_lightningMinInterval, _lightningMaxInterval));

                if (_currentWeather != HomesteaderWeather.Thunderstorm || TimeSystem.Instance.IsPaused) continue;

                // ── First pulse ──────────────────────────────────────────────
                // Set LightningBoost to 4×; DayNightCycle reads this and applies it
                // on top of its own weather-dimmed intensity each frame
                LightningBoost = 4.5f;
                RenderSettings.ambientIntensity = 3.5f;
                RenderSettings.ambientLight = new Color(0.85f, 0.90f, 1.00f);
                yield return new WaitForSeconds(_lightningFlashDuration * 0.35f);

                // Brief dark gap between double-flash
                LightningBoost = 1f;
                RenderSettings.ambientIntensity = origAmbientIntensity;
                RenderSettings.ambientLight = origAmbientLight;
                yield return new WaitForSeconds(_lightningFlashDuration * 0.25f);

                // ── Second pulse (dimmer) ───────────────────────────────────
                LightningBoost = 3.2f;
                RenderSettings.ambientIntensity = 2.5f;
                RenderSettings.ambientLight = new Color(0.80f, 0.86f, 1.00f);
                yield return new WaitForSeconds(_lightningFlashDuration * 0.45f);

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
