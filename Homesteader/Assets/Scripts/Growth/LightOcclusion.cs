using System.Collections.Generic;
using UnityEngine;

namespace Homesteader.Growth
{
    /// <summary>
    /// Whether the lamps, the fire, the lantern and the flashlight are stopped by walls (they cast shadows) or shine straight through them.
    /// Every such light registers here with the shadow mode it wants; the Graphics setting "Light Occlusion" switches them all on or off
    /// (a point light with shadows draws its surroundings several times, so weak machines can turn it off).
    /// Only the few lit lights NEAREST the player cast shadows at a time (<see cref="MaxShadowed"/>): a point light with shadows draws the scene six
    /// times, so a house full of lamps (eight lit: 48 shadow maps a frame) brought the frame rate down.
    /// </summary>
    public static class LightOcclusion
    {
        /// <summary>How many lights cast shadows at once: the nearest lit ones to the player. The rest shine through walls.</summary>
        public const int MaxShadowed = 3;

        private static readonly List<(Light light, LightShadows mode)> s_lights = new List<(Light, LightShadows)>();
        private static readonly List<(Light light, LightShadows mode, float dist)> s_lit = new List<(Light, LightShadows, float)>();
        private static bool s_enabled = true;

        public static bool Enabled
        {
            get => s_enabled;
            set { s_enabled = value; Apply(); }
        }

        /// <summary>Sets a light up to cast shadows (when the option is on and it is among the nearest) and remembers it for later changes of the option.</summary>
        public static void Register(Light light, LightShadows mode = LightShadows.Soft)
        {
            if (light == null) return;
            EnsureRunner();
            s_lights.RemoveAll(e => e.light == null);
            s_lights.Add((light, mode));
            light.shadows = LightShadows.None;   // given by Apply once it is lit and among the nearest
            light.shadowStrength = 1f;
        }

        private static void Apply()
        {
            s_lights.RemoveAll(e => e.light == null);
            s_lit.Clear();
            PedController ped = s_enabled ? PedController.Current : null;
            Camera cam = ped == null && s_enabled ? Camera.main : null;
            Vector3 at = ped != null ? ped.transform.position : cam != null ? cam.transform.position : Vector3.zero;
            foreach (var e in s_lights)
            {
                if (!s_enabled || !e.light.isActiveAndEnabled) { if (e.light.shadows != LightShadows.None) e.light.shadows = LightShadows.None; continue; }
                s_lit.Add((e.light, e.mode, (e.light.transform.position - at).sqrMagnitude));
            }
            s_lit.Sort((a, b) => a.dist.CompareTo(b.dist));
            for (int i = 0; i < s_lit.Count; i++)
            {
                LightShadows want = i < MaxShadowed ? s_lit[i].mode : LightShadows.None;
                if (s_lit[i].light.shadows != want) s_lit[i].light.shadows = want;
            }
        }

        private static Runner s_runner;

        private static void EnsureRunner()
        {
            if (s_runner != null || !Application.isPlaying) return;
            var go = new GameObject("LightOcclusion");
            Object.DontDestroyOnLoad(go);
            s_runner = go.AddComponent<Runner>();
        }

        /// <summary>Chooses the shadow casters again a few times a second (lights switch on and off, the player walks).</summary>
        private sealed class Runner : MonoBehaviour
        {
            private float _next;

            private void Update()
            {
                if (Time.unscaledTime < _next) return;
                _next = Time.unscaledTime + 0.25f;
                Apply();
            }
        }
    }
}
