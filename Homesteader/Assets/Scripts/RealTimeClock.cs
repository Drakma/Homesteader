using UnityEngine;
#if UNITY_EDITOR
using UnityEditor;
#endif

namespace Homesteader
{
    /// <summary>
    /// Publishes real (wall-clock) time to shaders as the global <c>_RealTime</c>.
    ///
    /// WHY. Unity's built-in <c>_Time</c> follows <c>Time.timeScale</c>, and the game sets timeScale to 0 while
    /// paused, so every effect driven by it - grass sway, water waves, rain rings - froze with the game clock.
    /// Those effects are visual, not simulation, so they run on <c>_RealTime</c> instead and keep moving
    /// whatever the in-game clock is doing.
    /// </summary>
    public static class RealTimeClock
    {
        private static readonly int RealTimeId = Shader.PropertyToID("_RealTime");

        // ---- Water wind -------------------------------------------------------------------------------------
        // WHY THE WATER GETS ITS OWN, SLOWED WIND. A wave's phase is dot(position, direction) * k - omega * t.
        // Two things make that race when the wind moves:
        //   * DIRECTION: at a point 300 m from the origin with k ~ 5, a direction change of just 0.01 rad
        //     shifts the phase by 15 rad - the waves visibly crawl. So the direction the water sees may turn at
        //     most ~3 degrees a MINUTE, however fast the gameplay wind swings.
        //   * SPEED: with omega depending on the gust, t * omega(gust) changes by (gust change) * t, and t is
        //     the whole session length. So the shader is handed a clock that ACCUMULATES the speed factor
        //     instead of multiplying it by absolute time.
        // Published as _WaterWind = (dirX, dirZ, gust 0..1, waveClock).
        private static readonly int WaterWindId = Shader.PropertyToID("_WaterWind");
        private static readonly int GrassWindId = Shader.PropertyToID("_GrassWindParams");
        private const float MaxWaterTurnRadPerSec = 0.0008f;
        private static float _lastTick = -1f;
        private static float _waterAngle;
        private static bool _waterAngleInit;
        private static float _waveClock;
        private static float _waterGust = 0.3f;

        private static void Tick()
        {
            float now = Time.realtimeSinceStartup;
            Shader.SetGlobalFloat(RealTimeId, now);

            float dt = _lastTick < 0f ? 0f : Mathf.Clamp(now - _lastTick, 0f, 0.25f);
            _lastTick = now;
            if (dt <= 0f && _waterAngleInit) return; // same instant (Update + LateUpdate): already done

            Vector4 w = Shader.GetGlobalVector(GrassWindId);
            Vector2 target = new Vector2(w.x, w.y);
            bool hasWind = target.sqrMagnitude > 1e-4f;
            float targetAngle = hasWind ? Mathf.Atan2(target.y, target.x) : _waterAngle;
            float targetGust = hasWind ? Mathf.Clamp01(w.w) : 0.3f;

            if (!_waterAngleInit && hasWind) { _waterAngle = targetAngle; _waterAngleInit = true; }
            else if (_waterAngleInit)
            {
                float delta = Mathf.DeltaAngle(_waterAngle * Mathf.Rad2Deg, targetAngle * Mathf.Rad2Deg) * Mathf.Deg2Rad;
                _waterAngle += Mathf.Clamp(delta, -MaxWaterTurnRadPerSec * dt, MaxWaterTurnRadPerSec * dt);
            }
            // The gust only scales speed/height, so it can follow the real one, gently.
            _waterGust = Mathf.MoveTowards(_waterGust, targetGust, 0.05f * dt);
            _waveClock += dt * (0.45f + 0.9f * _waterGust);

            Shader.SetGlobalVector(WaterWindId,
                new Vector4(Mathf.Cos(_waterAngle), Mathf.Sin(_waterAngle), _waterGust, _waveClock));
        }

        private sealed class Pump : MonoBehaviour
        {
            private void Update() => Tick();
            private void LateUpdate() => Tick();
        }

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        private static void Boot()
        {
            Tick(); // valid from the very first frame
            var go = new GameObject("RealTimeClock") { hideFlags = HideFlags.HideAndDontSave };
            Object.DontDestroyOnLoad(go);
            go.AddComponent<Pump>();
        }

#if UNITY_EDITOR
        // Also ticks in edit mode, so the scene view animates the same way.
        [InitializeOnLoadMethod]
        private static void EditorBoot() => EditorApplication.update += Tick;
#endif
    }
}
