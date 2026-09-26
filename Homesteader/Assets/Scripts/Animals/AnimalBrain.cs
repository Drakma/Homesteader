using System;
using System.Collections.Generic;
using System.Text;
using Homesteader.Animation;
using Homesteader.UI;
using UnityEngine;

namespace Homesteader.Animals
{
    /// <summary>
    /// The decision-maker for one animal. Every ~0.25 s it scores each behaviour rule from its
    /// AnimalAIDefinition (needs, time of day, weather, what it senses) and runs the winner.
    /// All rules come from mod data; this class only interprets them.
    /// </summary>
    public sealed class AnimalBrain : MonoBehaviour
    {
        public AnimalAIDefinition Def { get; private set; }
        public string Species { get; private set; }
        public Vector3 Home { get; private set; }
        public AnimalMover Mover { get; private set; }
        public GlbClipPlayer Clips { get; private set; }
        public string CurrentBehaviorId => current != null ? current.Behavior.Id : "<none>";

        /// <summary>Show a debug label (behaviour, needs) over every animal.</summary>
        public static bool ShowDebug;

        private readonly Dictionary<string, float> needs = new Dictionary<string, float>(StringComparer.OrdinalIgnoreCase);
        private readonly Dictionary<string, float> cooldownUntil = new Dictionary<string, float>(StringComparer.OrdinalIgnoreCase);
        private readonly Dictionary<string, float> events = new Dictionary<string, float>(StringComparer.OrdinalIgnoreCase);
        private readonly List<KeyValuePair<string, float>> lastScores = new List<KeyValuePair<string, float>>();

        private sealed class Running
        {
            public BehaviorDef Behavior;
            public AnimalActions.ActionRuntime Action;
            public float StartedAt;
        }

        private Running current;
        private float nextDecision;
        private HudTimeState timeSnap;

        public void Initialize(AnimalAIDefinition def, string species, GlbClipPlayer clips)
        {
            Def = def;
            Species = species;
            Clips = clips;
            Home = transform.position;

            Mover = gameObject.GetComponent<AnimalMover>();
            if (Mover == null) Mover = gameObject.AddComponent<AnimalMover>();
            Mover.Def = def.Movement;

            foreach (NeedDef n in def.Needs.Values) needs[n.Name] = Mathf.Clamp(n.Start, n.Min, n.Max);

            // Map the AI's animation slots onto the locomotion clips the player uses.
            if (clips != null)
            {
                clips.idleClip = def.ClipFor("idle") ?? clips.idleClip;
                clips.walkClip = def.ClipFor("walk") ?? clips.walkClip;
                clips.runClip = def.ClipFor("run") ?? clips.runClip;
                // The player's native gait speeds do not apply to this rig: use the definition's (0 = no matching).
                clips.walkNativeSpeed = def.Movement.WalkNativeMps;
                clips.runNativeSpeed = def.Movement.RunNativeMps;
                clips.playbackScaleRange = new Vector2(0.5f, 3.2f);   // animals' short-stride clips need more headroom than the player
            }

            var target = gameObject.GetComponent<AnimalTarget>();
            if (target == null) target = gameObject.AddComponent<AnimalTarget>();
            if (!target.HasTag("animal")) target.tags.Add("animal");
            foreach (string t in def.Tags) if (!target.HasTag(t)) target.tags.Add(t);
            if (!string.IsNullOrEmpty(species) && !target.HasTag("animal:" + species)) target.tags.Add("animal:" + species);

            nextDecision = Time.time + UnityEngine.Random.value * 0.5f;
        }

        // ---------------------------------------------------------------- public API

        public float GetNeed(string name) => needs.TryGetValue(name, out float v) ? v : 0f;

        public void SetNeed(string name, float value)
        {
            if (Def != null && Def.Needs.TryGetValue(name, out NeedDef n)) needs[name] = Mathf.Clamp(value, n.Min, n.Max);
            else needs[name] = Mathf.Clamp01(value);
        }

        public void AddNeed(string name, float delta) => SetNeed(name, GetNeed(name) + delta);

        /// <summary>Raises a named event for a while (for example "called" when the player whistles).</summary>
        public void RaiseEvent(string name, float seconds = 6f) => events[name] = Time.time + seconds;

        // ---------------------------------------------------------------- update

        /// <summary>Every animal with a brain, for things that need to see them all (the map).</summary>
        public static readonly List<AnimalBrain> All = new List<AnimalBrain>();
        private void OnEnable() { if (!All.Contains(this)) All.Add(this); }
        private void OnDisable() => All.Remove(this);

        /// <summary>Carries the "predator" or "aggressive" tag: shown red on the map.</summary>
        public bool IsAggressive
        {
            get
            {
                if (Def == null) return false;
                foreach (string t in Def.Tags)
                    if (string.Equals(t, "predator", System.StringComparison.OrdinalIgnoreCase) ||
                        string.Equals(t, "aggressive", System.StringComparison.OrdinalIgnoreCase)) return true;
                return false;
            }
        }

        private void Update()
        {
            if (Def == null) return;
            float dt = Time.deltaTime;
            if (dt <= 0f) return;

            TickNeeds(dt);

            if (Time.time >= nextDecision)
            {
                nextDecision = Time.time + 0.25f + UnityEngine.Random.value * 0.1f;
                Decide();
            }

            if (current != null)
            {
                current.Action.Tick(this, dt);
                if (current.Action.Done) EndCurrent();
            }
            else
            {
                SetMoving(0f);
            }
        }

        private void TickNeeds(float dt)
        {
            float gameHours = 0f;
            if (TimeSystem.Instance != null)
                gameHours = dt * TimeConstants.GameMinutesPerRealSecondAt1X *
                            TimeSystem.SpeedToMultiplier(TimeSystem.Instance.CurrentSpeed) / 60f;
            if (gameHours <= 0f) return;
            foreach (NeedDef n in Def.Needs.Values)
                needs[n.Name] = Mathf.Clamp(needs[n.Name] + n.RatePerGameHour * gameHours, n.Min, n.Max);
        }

        // ---------------------------------------------------------------- deciding

        private void Decide()
        {
            if (TimeSystem.Instance != null) timeSnap = TimeSystem.Instance.Snapshot();

            BehaviorDef best = null;
            float bestScore = float.NegativeInfinity;
            lastScores.Clear();

            foreach (BehaviorDef b in Def.Behaviors)
            {
                if (cooldownUntil.TryGetValue(b.Id, out float cd) && Time.time < cd && !IsCurrent(b)) continue;
                if (!RequirementsMet(b)) continue;
                float score = Score(b);
                lastScores.Add(new KeyValuePair<string, float>(b.Id, score));
                if (score > bestScore) { bestScore = score; best = b; }
            }

            if (best == null) return;

            if (current == null) { Begin(best); return; }
            if (best == current.Behavior) return;

            // Should the newcomer take over from the running behaviour?
            bool currentStillValid = RequirementsMet(current.Behavior);
            float currentScore = currentStillValid ? Score(current.Behavior) : -1f;
            bool beats = bestScore > currentScore * 1.15f + 0.05f;
            bool ranLongEnough = Time.time - current.StartedAt >= current.Behavior.MinSeconds;
            bool outranks = best.Priority > current.Behavior.Priority;

            if (!currentStillValid && current.Behavior.Interruptible) { Begin(best); return; }
            if (beats && ((current.Behavior.Interruptible && ranLongEnough) || outranks)) Begin(best);
        }

        private bool IsCurrent(BehaviorDef b) => current != null && current.Behavior == b;

        private bool RequirementsMet(BehaviorDef b)
        {
            for (int i = 0; i < b.Requires.Count; i++)
                if (!Test(b.Requires[i])) return false;
            return true;
        }

        private float Score(BehaviorDef b)
        {
            float s = b.Base;
            for (int i = 0; i < b.Score.Count; i++)
                s += b.Score[i].Weight * Value(b.Score[i]);
            return Mathf.Max(0f, s);
        }

        private void Begin(BehaviorDef b)
        {
            EndCurrent();
            current = new Running { Behavior = b, Action = AnimalActions.Create(b.Action), StartedAt = Time.time };
            current.Action.Begin(this);
        }

        private void EndCurrent()
        {
            if (current == null) return;
            current.Action.End(this);
            if (current.Behavior.CooldownSeconds > 0f)
                cooldownUntil[current.Behavior.Id] = Time.time + current.Behavior.CooldownSeconds;
            current = null;
        }

        // ---------------------------------------------------------------- terms

        /// <summary>True when a boolean-style term holds (used by `requires` and `until`).</summary>
        public bool Test(TermDef t)
        {
            bool r = Value(t) >= 0.5f;
            return t.Not ? !r : r;
        }

        /// <summary>0..1 value of a term (booleans give 0 or 1).</summary>
        public float Value(TermDef t)
        {
            float v = Raw(t);
            if (t.Not && t.IsBoolean) v = v >= 0.5f ? 0f : 1f;
            return v;
        }

        private float Raw(TermDef t)
        {
            switch (t.Kind)
            {
                case "need":
                {
                    float n = GetNeed(t.Key);
                    if (!float.IsNaN(t.Above) || !float.IsNaN(t.Below))
                        return (float.IsNaN(t.Above) || n > t.Above) && (float.IsNaN(t.Below) || n < t.Below) ? 1f : 0f;
                    return Curve(n, t.Curve);
                }
                case "time":
                    return TimeOfDayMatches(t.Key) ? 1f : 0f;
                case "hours":
                {
                    float h = timeSnap.MinuteOfDay / 60f;
                    bool inside = t.FromHour <= t.ToHour ? (h >= t.FromHour && h < t.ToHour) : (h >= t.FromHour || h < t.ToHour);
                    return inside ? 1f : 0f;
                }
                case "weather":
                    return t.Values.Exists(w => string.Equals(w, timeSnap.Weather.ToString(), StringComparison.OrdinalIgnoreCase)) ? 1f : 0f;
                case "season":
                    return t.Values.Exists(w => string.Equals(w, timeSnap.Season.ToString(), StringComparison.OrdinalIgnoreCase)) ? 1f : 0f;
                case "current":
                    return current != null && string.Equals(current.Behavior.Id, t.Key, StringComparison.OrdinalIgnoreCase) ? 1f : 0f;
                case "event":
                    return events.TryGetValue(t.Key, out float until) && Time.time < until ? 1f : 0f;
                case "random":
                    return UnityEngine.Random.value;
                case "sense":
                    return SenseValue(t);
            }
            return 0f;
        }

        private float SenseValue(TermDef t)
        {
            float range = Def.Senses.SightM;
            Transform found = AnimalSenses.Nearest(transform.position, t.Key, range, transform);
            if (found == null) return 0f;
            float d = AnimalSenses.Flat(transform.position, found.position);

            if (!float.IsNaN(t.Within) || !float.IsNaN(t.Beyond))
            {
                bool ok = (float.IsNaN(t.Within) || d <= t.Within) && (float.IsNaN(t.Beyond) || d >= t.Beyond);
                return ok ? 1f : 0f;
            }
            if (t.Curve == "closer") return 1f - Mathf.Clamp01(d / range);
            if (t.Curve == "farther") return Mathf.Clamp01(d / range);
            return 1f;   // "there is one in sight"
        }

        private bool TimeOfDayMatches(string word)
        {
            switch ((word ?? "").ToLowerInvariant())
            {
                case "day": return timeSnap.Phase == HomesteaderPhase.Day;
                case "night": return timeSnap.Phase == HomesteaderPhase.Night;
                case "dawn": return Mathf.Abs(timeSnap.MinuteOfDay - timeSnap.SunriseMinute) < 75f;
                case "dusk": return Mathf.Abs(timeSnap.MinuteOfDay - timeSnap.SunsetMinute) < 75f;
            }
            return false;
        }

        private static float Curve(float v, string curve)
        {
            switch (curve)
            {
                case "inverse": return 1f - v;
                case "squared": return v * v;
                case "sqrt": return Mathf.Sqrt(v);
                default: return v;
            }
        }

        // ---------------------------------------------------------------- helpers for actions

        public float SpeedFor(string speed)
        {
            if (string.Equals(speed, "walk", StringComparison.OrdinalIgnoreCase) || string.IsNullOrEmpty(speed)) return Def.Movement.WalkSpeed;
            if (string.Equals(speed, "run", StringComparison.OrdinalIgnoreCase)) return Def.Movement.RunSpeed;
            return float.TryParse(speed, System.Globalization.NumberStyles.Float,
                System.Globalization.CultureInfo.InvariantCulture, out float v) ? v : Def.Movement.WalkSpeed;
        }

        /// <summary>Resolves a target tag to a world position. "home" and "player" are built in.</summary>
        public bool TryResolveTarget(string tag, out Vector3 pos, out Transform t)
        {
            t = null;
            pos = Vector3.zero;
            if (string.Equals(tag, "home", StringComparison.OrdinalIgnoreCase)) { pos = Home; return true; }
            float range = string.Equals(tag, "player", StringComparison.OrdinalIgnoreCase) ? Def.Senses.SightM * 2f : 80f;
            t = AnimalSenses.Nearest(transform.position, tag, range, transform);
            if (t == null) return false;
            pos = t.position;
            return true;
        }

        /// <summary>Drives the locomotion animation from the speed actually being moved at.</summary>
        public void SetMoving(float metresPerSecond)
        {
            if (Clips == null || !Clips.IsReady) return;
            if (Clips.ActionActive) return;
            float mid = (Def.Movement.WalkSpeed + Def.Movement.RunSpeed) * 0.5f;
            Clips.SetLocomotion(metresPerSecond < 0.05f ? 0f : (metresPerSecond > mid ? 1f : 0.5f), false, metresPerSecond);
        }

        public void PlayAnim(string slotOrClip, bool loop)
        {
            if (Clips == null || !Clips.IsReady || string.IsNullOrEmpty(slotOrClip)) return;
            Clips.BeginAction(Def.ClipFor(slotOrClip), loop);
        }

        public void StopAnim()
        {
            if (Clips != null && Clips.ActionActive) Clips.EndAction();
        }

        // ---------------------------------------------------------------- debug

        private void OnGUI()
        {
            if (!ShowDebug || Def == null) return;
            Camera cam = Camera.main;
            if (cam == null) cam = Camera.current != null ? Camera.current : (Camera.allCamerasCount > 0 ? Camera.allCameras[0] : null);
            if (cam == null) return;
            Vector3 sp = cam.WorldToScreenPoint(transform.position + Vector3.up * 1.1f);
            if (sp.z < 0f) return;

            var sb = new StringBuilder();
            sb.Append(Def.Id).Append(": ").AppendLine(CurrentBehaviorId);
            foreach (var kv in needs) sb.Append(kv.Key).Append(' ').Append(kv.Value.ToString("0.00")).Append("  ");
            sb.AppendLine();
            lastScores.Sort((a, b) => b.Value.CompareTo(a.Value));
            for (int i = 0; i < Mathf.Min(3, lastScores.Count); i++)
                sb.Append(lastScores[i].Key).Append(' ').Append(lastScores[i].Value.ToString("0.00")).Append("   ");

            var rect = new Rect(sp.x - 130f, Screen.height - sp.y - 40f, 260f, 60f);
            GUI.Label(rect, sb.ToString());
        }
    }
}
