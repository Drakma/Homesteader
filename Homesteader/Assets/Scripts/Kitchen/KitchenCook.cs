using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace Homesteader.Kitchen
{
    /// <summary>
    /// Makes a meal in front of the player: the ped walks from appliance to appliance (the oven, the stove, the grain mill ... whatever each cooking of the plan needs, in order), works at each
    /// for a moment, then walks to where the meal is served; then the meal is served (everything is taken out of the kitchen only at that point, so walking away part way costs nothing).
    /// Any movement key stops it. There are no cooking clips yet: the ped uses the nearest ones it has (a standing pour at the stove, crouching at the oven).
    /// </summary>
    public sealed class KitchenCook : MonoBehaviour
    {
        private static KitchenCook _inst;

        /// <summary>True while the ped is cooking (the Meal Builder and the Meals List wait).</summary>
        public static bool Busy { get; private set; }

        /// <summary>What the ped is doing now ("Baking Bread ...", "Serving"), for the windows.</summary>
        public static string Status { get; private set; } = "";

        /// <summary>Starts cooking the steps, then calls <paramref name="onServe"/> (or <paramref name="onStopped"/> when the player stopped it). With no ped or nothing to cook it serves at once.</summary>
        public static bool Begin(List<PlanStep> steps, Vector3 serveAt, Action onServe, Action<string> onStopped)
        {
            if (Busy) return false;
            var ped = PedController.Current;
            if (ped == null || steps == null || steps.Count == 0) { onServe?.Invoke(); return true; }
            if (_inst == null)
            {
                var go = new GameObject("KitchenCook");
                DontDestroyOnLoad(go);
                _inst = go.AddComponent<KitchenCook>();
            }
            _inst.StartCoroutine(_inst.Routine(ped, new List<PlanStep>(steps), serveAt, onServe, onStopped));
            return true;
        }

        private static KitchenAnimator.Gesture GestureFor(string applianceId)
        {

            if (Homesteader.Growth.GrowthRegistry.ToolMatches("#appliance_grain_mill", applianceId) || Homesteader.Growth.GrowthRegistry.ToolMatches("#appliance_oil_press", applianceId)) return KitchenAnimator.Gesture.Crank;
            if (Homesteader.Growth.GrowthRegistry.ToolMatches("#appliance_juicer", applianceId) || Homesteader.Growth.GrowthRegistry.ToolMatches("#appliance_blender", applianceId)) return KitchenAnimator.Gesture.Press;
            return KitchenAnimator.Gesture.Stir;
        }

        private static string ClipFor(string applianceId)
        {
            if (!string.IsNullOrEmpty(applianceId) && Homesteader.Growth.GrowthRegistry.ToolMatches("#appliance_oven", applianceId)) return "Crouch_Idle_RT";   // down at the oven door
            return "Farm_Watering_RT";                                                                                                                      // a standing pouring / stirring motion
        }

        /// <summary>Where the ped stands to use something: about a metre from it, on the side the ped comes from.</summary>
        private static Vector3 StandPoint(PedController ped, Vector3 target)
        {
            Vector3 d = ped.transform.position - target;
            d.y = 0f;
            if (d.sqrMagnitude < 0.04f) d = -ped.transform.forward;
            d.y = 0f;
            Vector3 p = target + d.normalized * 1.0f;
            p.y = ped.transform.position.y;
            return p;
        }

        private IEnumerator Walk(PedController ped, Vector3 target, Action<bool> done)
        {
            ped.AutoWalkTo(target);
            float giveUp = Time.time + 12f, markTime = Time.time, best = float.MaxValue;
            while (true)
            {
                if (ped.AutoCancelled) { done(false); yield break; }
                Vector3 d = target - ped.transform.position;
                d.y = 0f;
                float dist = d.magnitude;
                if (dist <= 0.5f || Time.time > giveUp) break;
                if (dist < best - 0.3f) { best = dist; markTime = Time.time; }                    // getting closer
                else if (Time.time - markTime > 1.5f) break;                                       // stuck on something: carry on from here
                yield return null;
            }
            ped.AutoStop();
            done(true);
        }

        private IEnumerator Routine(PedController ped, List<PlanStep> steps, Vector3 serveAt, Action onServe, Action<string> onStopped)
        {
            Busy = true;
            bool ok = true;
            foreach (PlanStep step in steps)
            {
                Status = (step.Meal != null ? MealMaker.NameOf(step.Meal) : "Cooking") + " ...";
                if (step.Appliance != null)
                {
                    bool arrived = true;
                    yield return Walk(ped, StandPoint(ped, step.Appliance.position), r => arrived = r);
                    if (!arrived) { ok = false; break; }
                    float seconds = Mathf.Clamp(1.8f + 0.9f * step.Batches, 2f, 6f);
                    bool oven = !string.IsNullOrEmpty(step.ApplianceId) && Homesteader.Growth.GrowthRegistry.ToolMatches("#appliance_oven", step.ApplianceId);
                    string clip = ClipFor(step.ApplianceId);
                    bool animated = false;
                    if (oven) animated = ped.BeginWork(clip, step.Appliance.position);                    // down at the oven door
                    else
                    {
                        ped.FaceToward(step.Appliance.position);
                        KitchenAnimator.Play(ped, GestureFor(step.ApplianceId), seconds);                  // the arms stir, crank or press (code-driven)
                    }
                    float until = Time.time + seconds;
                    while (Time.time < until)
                    {
                        if (ped.ManualInput) { ok = false; break; }
                        yield return null;
                    }
                    if (animated) ped.EndWork(clip);
                    KitchenAnimator.Stop(ped);
                    if (!ok) break;
                }
                else
                {
                    KitchenAnimator.Play(ped, KitchenAnimator.Gesture.Chop, 1.4f);                       // put together on the counter
                    yield return new WaitForSeconds(1.4f);
                    KitchenAnimator.Stop(ped);
                }
            }
            if (ok)
            {
                Status = "Serving";
                bool arrived = true;
                yield return Walk(ped, StandPoint(ped, serveAt), r => arrived = r);
                ok = arrived;
            }
            ped.AutoStop();
            Busy = false;
            Status = "";
            if (ok) onServe?.Invoke();
            else onStopped?.Invoke("You stopped cooking; nothing was used.");
        }
    }
}
