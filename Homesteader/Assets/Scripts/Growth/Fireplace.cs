using Homesteader.Controls;
using Homesteader.UI;
using UnityEngine;

namespace Homesteader.Growth
{
    /// <summary>
    /// The fireplace of a finished building. The stage models carry a chimney object ("Chimney") with a firebox and a flue hole in its cap,
    /// and two empties: FireboxPoint (where logs lie and the fire burns) and SmokePoint (the flue). A right click on the chimney with firewood in
    /// hand (an item whose manifest sets burn_minutes) puts it in the firebox; a right click with a lighter (lights_fires) lights it. It burns
    /// the fuel down in game time, lights the room with a flickering warm light and sends smoke out of the flue; when the fuel is gone the fire
    /// goes out. The fuel and whether it burns live on the ConstructionSite (saved with it).
    /// </summary>
    public sealed class Fireplace : MonoBehaviour
    {
        public const float MaxFuelMinutes = 540f;
        private const float MinutesPerLog = 45f;
        private const float ReachMetres = 4f;

        private ConstructionSite _site;
        private Transform _chimney, _firebox, _flue;
        private GameObject _logs;
        private int _shownLogs = -1;
        private ParticleSystem _flames, _smoke;
        private Light _light;
        private float _seed;
        private bool _wasLit;

        private static Material s_logMat, s_particleMat;
        private static Texture2D s_soft;

        /// <summary>Finds the fireplace parts in a freshly shown stage model and (re)binds the site's fireplace to them; null when it has none.</summary>
        public static Fireplace Attach(ConstructionSite site, Transform model)
        {
            Transform chimney = null, firebox = null, flue = null;
            foreach (Transform t in model.GetComponentsInChildren<Transform>(true))
            {
                if (t.name == "Chimney") chimney = t;
                else if (t.name == "FireboxPoint") firebox = t;
                else if (t.name == "SmokePoint") flue = t;
            }
            Fireplace fp = site.GetComponent<Fireplace>();
            if (chimney == null || firebox == null || flue == null)
            {
                if (fp != null) Destroy(fp);
                return null;
            }
            if (fp == null) fp = site.gameObject.AddComponent<Fireplace>();
            fp.Bind(site, chimney, firebox, flue);
            return fp;
        }

        private void Bind(ConstructionSite site, Transform chimney, Transform firebox, Transform flue)
        {
            _site = site;
            _chimney = chimney;
            _firebox = firebox;
            _flue = flue;
            _seed = Random.value * 100f;
            _logs = null;
            _shownLogs = -1;
            _flames = _smoke = null;
            _light = null;
            BuildEffects();
            Refresh();
        }

        // ------------------------------------------------------------------ using it

        /// <summary>True when the mouse is over the chimney (the first thing the ray hits, the player aside).</summary>
        public bool CursorOnChimney()
        {
            Camera cam = Camera.main != null ? Camera.main : FindAnyObjectByType<Camera>();
            if (cam == null || UnityEngine.InputSystem.Mouse.current == null || _chimney == null) return false;
            Vector2 pointer = UnityEngine.InputSystem.Mouse.current.position.ReadValue();
            RaycastHit[] hits = Physics.RaycastAll(cam.ScreenPointToRay(pointer), 1000f, Physics.DefaultRaycastLayers, QueryTriggerInteraction.Ignore);
            System.Array.Sort(hits, (a, b) => a.distance.CompareTo(b.distance));
            foreach (RaycastHit h in hits)
            {
                if (h.collider.GetComponentInParent<PedController>() != null) continue;
                return h.collider.transform.IsChildOf(_chimney) || h.collider.transform == _chimney;
            }
            return false;
        }

        /// <summary>Handles a right click on the chimney with the held item: firewood goes in, a lighter lights it. False when the held item means nothing here.</summary>
        public bool Use(string heldId, Transform player)
        {
            AssetCatalogItem item = string.IsNullOrEmpty(heldId) ? null : HudBindings.GetCatalogItem(heldId);
            if (item == null || (item.burn_minutes <= 0f && !item.lights_fires)) return false;
            if (player != null && _site.DistanceOutside(player.position) > ReachMetres)
            {
                ToastNotificationSystem.ShowInfo("Too far", "Move closer to the fireplace.");
                return true;
            }
            if (item.burn_minutes > 0f)
            {
                if (_site.FuelMinutes + item.burn_minutes > MaxFuelMinutes)
                {
                    ToastNotificationSystem.ShowInfo("Fireplace", "The firebox is full.");
                    return true;
                }
                HudState hud = HudState.Active;
                if (hud == null || !hud.ConsumeFromSelectedSlot(1)) return true;
                HudBindings.Instance?.RefreshToolbar();
                _site.FuelMinutes += item.burn_minutes;
                Refresh();
                return true;
            }
            // a lighter
            if (_site.FuelMinutes <= 0f) { ToastNotificationSystem.ShowInfo("Fireplace", "There is nothing in the fireplace to burn."); return true; }
            _site.FireLit = true;
            Refresh();
            return true;
        }

        // ------------------------------------------------------------------ burning

        private void Update()
        {
            if (_site == null) return;
            if (_site.FireLit)
            {
                float speed = 0f;
                TimeSystem time = TimeSystem.Instance;
                if (time != null && !time.IsPaused) speed = TimeSystem.SpeedToMultiplier(time.CurrentSpeed);
                _site.FuelMinutes -= Time.deltaTime * TimeConstants.GameMinutesPerRealSecondAt1X * speed;
                if (_site.FuelMinutes <= 0f) { _site.FuelMinutes = 0f; _site.FireLit = false; Refresh(); }
                else if (LogCount() != _shownLogs) Refresh();
            }
            if (_light != null && _site.FireLit)
            {
                float n = Mathf.PerlinNoise(Time.time * 7f, _seed) * 0.6f + Mathf.PerlinNoise(Time.time * 17f, _seed + 9f) * 0.4f;
                _light.intensity = Mathf.Lerp(1.6f, 3.4f, n);
            }
        }

        private int LogCount()
        {
            return _site.FuelMinutes <= 0f ? 0 : Mathf.Clamp(Mathf.CeilToInt(_site.FuelMinutes / MinutesPerLog), 1, 6);
        }

        /// <summary>Redraws the logs, the flames, the smoke and the light to match the fuel and whether it burns.</summary>
        private void Refresh()
        {
            if (_firebox == null) return;
            int n = LogCount();
            if (_logs != null && n != _shownLogs) { Destroy(_logs); _logs = null; }
            if (_logs == null && n > 0) _logs = MakeLogs(n);
            _shownLogs = n;
            bool lit = _site.FireLit && n > 0;
            if (lit != _wasLit) { _wasLit = lit; Debug.Log($"[Fireplace] {_site.StructureId}: fire {(lit ? "lit" : "out")}, {n} logs, flames={(_flames != null)}, smoke={(_smoke != null)}, light={(_light != null)}."); }
            SetEmitting(_flames, lit);
            SetEmitting(_smoke, lit);
            if (_light != null) _light.enabled = lit;
            if (_logs != null) foreach (Renderer r in _logs.GetComponentsInChildren<Renderer>()) r.sharedMaterial = LogMaterial(lit);
        }

        private static void SetEmitting(ParticleSystem ps, bool on)
        {
            if (ps == null) return;
            ParticleSystem.EmissionModule e = ps.emission;
            e.enabled = on;
            if (on && !ps.isPlaying) ps.Play();
        }

        // ------------------------------------------------------------------ the things you see

        private GameObject MakeLogs(int n)
        {
            var root = new GameObject("FireLogs");
            root.transform.SetParent(_firebox, false);
            // a small stack: a row of three, then two, then one; each log lies along the wall (the model's Z), 0.36 m long
            Vector3[] spots =
            {
                new Vector3(-0.09f, 0.06f, 0f), new Vector3(0f, 0.06f, 0f), new Vector3(0.09f, 0.06f, 0f),
                new Vector3(-0.045f, 0.165f, 0f), new Vector3(0.045f, 0.165f, 0f), new Vector3(0f, 0.265f, 0f),
            };
            for (int i = 0; i < n; i++)
            {
                GameObject log = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
                Destroy(log.GetComponent<Collider>());
                log.name = "Log";
                log.transform.SetParent(root.transform, false);
                log.transform.localPosition = spots[i];
                log.transform.localRotation = Quaternion.Euler(90f, 0f, 0f);
                log.transform.localScale = new Vector3(0.11f, 0.18f, 0.11f);
            }
            return root;
        }

        private static Material LogMaterial(bool charred)
        {
            if (s_logMat == null)
            {
                Shader sh = Shader.Find("Universal Render Pipeline/Lit") ?? Shader.Find("Standard");
                s_logMat = new Material(sh) { name = "FireLog", hideFlags = HideFlags.DontSave };
            }
            Color c = charred ? new Color(0.16f, 0.1f, 0.07f) : new Color(0.42f, 0.27f, 0.15f);
            if (s_logMat.HasProperty("_BaseColor")) s_logMat.SetColor("_BaseColor", c);
            s_logMat.color = c;
            return s_logMat;
        }

        private static Texture2D SoftDot()
        {
            if (s_soft != null) return s_soft;
            const int n = 32;
            s_soft = new Texture2D(n, n, TextureFormat.RGBA32, false) { hideFlags = HideFlags.DontSave, wrapMode = TextureWrapMode.Clamp };
            for (int y = 0; y < n; y++)
                for (int x = 0; x < n; x++)
                {
                    float d = Vector2.Distance(new Vector2(x + 0.5f, y + 0.5f), new Vector2(n / 2f, n / 2f)) / (n / 2f);
                    s_soft.SetPixel(x, y, new Color(1f, 1f, 1f, Mathf.Clamp01(1f - d) * Mathf.Clamp01(1f - d)));
                }
            s_soft.Apply();
            return s_soft;
        }

        private static Material ParticleMaterial()
        {
            if (s_particleMat != null) return s_particleMat;
            Shader sh = Shader.Find("Sprites/Default");
            s_particleMat = new Material(sh) { name = "FireParticles", hideFlags = HideFlags.DontSave, mainTexture = SoftDot() };
            return s_particleMat;
        }

        private void BuildEffects()
        {
            // flames: a few short-lived warm sprites rising from the logs
            _flames = MakeSystem("Flames", _firebox, new Vector3(0f, 0.12f, 0f), ps =>
            {
                var main = ps.main;
                main.loop = true;
                main.startLifetime = 0.55f;
                main.startSpeed = 0.35f;
                main.startSize = new ParticleSystem.MinMaxCurve(0.16f, 0.28f);
                main.startColor = new ParticleSystem.MinMaxGradient(new Color(1f, 0.75f, 0.2f, 0.9f), new Color(1f, 0.35f, 0.08f, 0.9f));
                main.simulationSpace = ParticleSystemSimulationSpace.Local;
                main.gravityModifier = -0.05f;
                main.maxParticles = 80;
                var emission = ps.emission;
                emission.rateOverTime = 26f;
                var shape = ps.shape;
                shape.shapeType = ParticleSystemShapeType.Box;
                shape.rotation = new Vector3(-90f, 0f, 0f);          // emit upward
                shape.scale = new Vector3(0.12f, 0.28f, 0.02f);       // spread across the firebox depth and along the logs
                var col = ps.colorOverLifetime;
                col.enabled = true;
                var g = new Gradient();
                g.SetKeys(new[] { new GradientColorKey(new Color(1f, 0.85f, 0.35f), 0f), new GradientColorKey(new Color(0.9f, 0.2f, 0.05f), 1f) },
                          new[] { new GradientAlphaKey(0.9f, 0f), new GradientAlphaKey(0.7f, 0.6f), new GradientAlphaKey(0f, 1f) });
                col.color = g;
                var size = ps.sizeOverLifetime;
                size.enabled = true;
                size.size = new ParticleSystem.MinMaxCurve(1f, new AnimationCurve(new Keyframe(0f, 0.8f), new Keyframe(0.4f, 1f), new Keyframe(1f, 0.1f)));
            });
            // smoke from the flue: grey, slow, growing and fading, left behind in the world
            _smoke = MakeSystem("Smoke", _flue, Vector3.zero, ps =>
            {
                var main = ps.main;
                main.loop = true;
                main.startLifetime = 4.5f;                              // short enough to stay on screen from the isometric camera (it rises about 4 m)
                main.startSpeed = 0.9f;
                main.startSize = new ParticleSystem.MinMaxCurve(0.6f, 0.9f);                    // big enough to read from the isometric camera
                main.startColor = new Color(0.4f, 0.4f, 0.43f, 1f);
                main.simulationSpace = ParticleSystemSimulationSpace.World;
                main.gravityModifier = -0.02f;
                main.maxParticles = 120;
                var emission = ps.emission;
                emission.rateOverTime = 22f;
                var shape = ps.shape;
                shape.shapeType = ParticleSystemShapeType.Cone;
                shape.angle = 6f;
                shape.radius = 0.07f;
                shape.rotation = new Vector3(-90f, 0f, 0f);          // out of the flue, upward
                var vel = ps.velocityOverLifetime;
                vel.enabled = true;
                vel.space = ParticleSystemSimulationSpace.World;
                vel.x = new ParticleSystem.MinMaxCurve(0.25f);         // a little drift (all three axes must use the same curve mode)
                vel.y = new ParticleSystem.MinMaxCurve(0f);
                vel.z = new ParticleSystem.MinMaxCurve(0f);
                var col = ps.colorOverLifetime;
                col.enabled = true;
                var g = new Gradient();
                g.SetKeys(new[] { new GradientColorKey(new Color(0.3f, 0.3f, 0.33f), 0f), new GradientColorKey(new Color(0.62f, 0.62f, 0.66f), 1f) },
                          new[] { new GradientAlphaKey(0f, 0f), new GradientAlphaKey(1f, 0.08f), new GradientAlphaKey(0.85f, 0.55f), new GradientAlphaKey(0f, 1f) });
                col.color = g;
                var size = ps.sizeOverLifetime;
                size.enabled = true;
                size.size = new ParticleSystem.MinMaxCurve(1f, new AnimationCurve(new Keyframe(0f, 0.6f), new Keyframe(1f, 3.4f)));
            });
            var lightGo = new GameObject("FireLight");
            lightGo.transform.SetParent(_firebox, false);
            lightGo.transform.localPosition = new Vector3(0f, 0.35f, 0f);
            _light = lightGo.AddComponent<Light>();
            _light.type = LightType.Point;
            _light.color = new Color(1f, 0.6f, 0.26f);
            _light.range = 7f;
            _light.intensity = 2.4f;
            _light.shadows = LightShadows.None;   // a point light with shadows draws the whole room six times: too dear for a flickering fire
            _light.enabled = false;
        }

        private static ParticleSystem MakeSystem(string name, Transform parent, Vector3 local, System.Action<ParticleSystem> setup)
        {
            var go = new GameObject(name);
            go.transform.SetParent(parent, false);
            go.transform.localPosition = local;
            go.transform.localRotation = Quaternion.identity;
            var ps = go.AddComponent<ParticleSystem>();
            ps.Stop();
            var r = go.GetComponent<ParticleSystemRenderer>();
            r.sharedMaterial = ParticleMaterial();
            r.sortingOrder = 5;
            r.renderMode = ParticleSystemRenderMode.Billboard;
            r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            setup(ps);
            return ps;
        }
    }
}
