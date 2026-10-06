using System.Collections.Generic;
using Homesteader.UI;
using UnityEngine;

namespace Homesteader.Growth
{
    /// <summary>
    /// A wind turbine standing in the world. Its model has a node "Yaw" (the head: it turns about the vertical axis) and, under it, "Rotor" (hub and blades, spinning about its
    /// own Z axis); see docs/WIND_TURBINES.md. The head swings to face INTO the wind (WeatherEffectsManager.WindDirection is where the wind blows TOWARD) with a slow, gusty
    /// turn, and the rotor spins faster the stronger the wind blows (it stands still below the cut-in speed and while the game is paused). The power it would make is
    /// <see cref="Watts"/> (the item's max_power_w along a cubic power curve). Added to a placed object by <see cref="AttachIfTurbine"/>; it gives itself up when the model has no such nodes.
    /// </summary>
    public sealed class WindTurbine : MonoBehaviour
    {
        public static readonly List<WindTurbine> All = new List<WindTurbine>();

        private const float CutIn = 2.5f;        // m/s: the blades start to turn
        private const float Rated = 11f;         // m/s: full power
        private const float YawRate = 28f;       // degrees a second the head can turn
        private const float MaxSpin = 13f;       // radians a second at the strongest wind (kept slow enough to be seen at 60 fps)

        private Transform _yaw, _rotor;
        private float _ratedWatts;
        private float _omega;
        private float _seed;
        private float _nextFind;
        private int _tries;

        /// <summary>The power it makes in the wind right now, in watts.</summary>
        public float Watts { get; private set; }

        private void OnEnable() { if (!All.Contains(this)) All.Add(this); }
        private void OnDisable() { All.Remove(this); }

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
        private static void ResetStatics() { All.Clear(); }

        /// <summary>Adds the behaviour to a placed object of the electricity category with a rated power (the model's nodes are looked for once it has loaded).</summary>
        public static void AttachIfTurbine(PlacedObject placed)
        {
            if (placed == null) return;
            AssetCatalogItem info = HudBindings.GetCatalogItem(placed.ItemId);
            if (info == null || info.category != "electricity" || info.max_power_w <= 0f || !placed.ItemId.Contains("turbine_wind")) return;
            if (placed.GetComponent<WindTurbine>() != null) return;
            var t = placed.gameObject.AddComponent<WindTurbine>();
            t._ratedWatts = info.max_power_w;
            t._seed = Random.value * 100f;
        }

        /// <summary>A finished wind turbine STRUCTURE (the site's model): the same behaviour as a placed one.</summary>
        public static void AttachToModel(GameObject model, float ratedWatts)
        {
            if (model == null || model.GetComponent<WindTurbine>() != null) return;
            var t = model.AddComponent<WindTurbine>();
            t._ratedWatts = ratedWatts;
            t._seed = Random.value * 100f;
        }

        private bool Find()
        {
            foreach (Transform t in GetComponentsInChildren<Transform>(true))
            {
                if (_yaw == null && t.name.StartsWith("Yaw")) _yaw = t;
                else if (_rotor == null && t.name.StartsWith("Rotor")) _rotor = t;
            }
            if (_yaw == null || _rotor == null) { _yaw = _rotor = null; return false; }
            // a moving collider is dear and nothing needs it: the head and rotor are for looking at
            foreach (Collider c in _yaw.GetComponentsInChildren<Collider>(true)) Destroy(c);
            return true;
        }

        private void Update()
        {
            if (_yaw == null)
            {
                if (Time.unscaledTime < _nextFind) return;
                _nextFind = Time.unscaledTime + 0.5f;
                if (!Find() && ++_tries > 60) Destroy(this);   // no head and rotor in this model (after half a minute of looking): not a turbine
                return;
            }

            TimeSystem time = TimeSystem.Instance;
            bool paused = time != null && time.IsPaused;
            WeatherEffectsManager weather = WeatherEffectsManager.Instance;
            float v = weather != null ? weather.WindSpeedMps : 0f;
            Vector2 d = weather != null ? weather.WindDirection : Vector2.zero;
            float dt = Time.deltaTime;

            Watts = _ratedWatts * Mathf.Pow(Mathf.Clamp01((v - 3f) / (Rated - 3f)), 3f);
            if (paused) return;

            // the head turns into the wind, wandering a little with the gusts
            if (v > 0.5f && d.sqrMagnitude > 1e-4f)
            {
                Vector3 face = new Vector3(-d.x, 0f, -d.y).normalized;
                float wander = Mathf.Sin(Time.time * 0.9f + _seed) * 6f * Mathf.Clamp01(v / 8f);
                Quaternion target = Quaternion.LookRotation(face, Vector3.up) * Quaternion.Euler(0f, wander, 0f);
                _yaw.rotation = Quaternion.RotateTowards(_yaw.rotation, target, YawRate * dt);
            }

            // the blades spin up and run down slowly (they have weight)
            float want = v < CutIn ? 0f : Mathf.Clamp(v * 1.1f, 0f, MaxSpin);
            _omega = Mathf.Lerp(_omega, want, 1f - Mathf.Exp(-0.8f * dt));
            if (_omega > 0.01f) _rotor.Rotate(0f, 0f, -_omega * Mathf.Rad2Deg * dt, Space.Self);
        }
    }
}
