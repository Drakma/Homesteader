using System;
using System.Collections.Generic;
using Homesteader.Modding;

namespace Homesteader.Animals
{
    // Data model for animal AI, read from a mod's `animal_ai` JSON files (see docs/ANIMAL_AI.md).
    // Everything here is plain data. The runtime (AnimalBrain) turns it into behaviour.

    /// <summary>One need an animal has (hunger, thirst, energy, ...), 0..1, changing over game time.</summary>
    public sealed class NeedDef
    {
        public string Name;
        public float Start = 0.5f;
        public float RatePerGameHour;     // positive grows, negative shrinks
        public float Min = 0f;
        public float Max = 1f;
    }

    public sealed class SenseDef
    {
        public float SightM = 20f;        // how far it notices players / animals / targets
        public float HearM = 30f;
    }

    public sealed class MovementDef
    {
        public float WalkSpeed = 1.6f;
        public float RunSpeed = 5.0f;
        public float TurnSpeedDeg = 240f;
        public float MaxSlopeDeg = 40f;
        public float ArriveDistM = 0.6f;
        public float SpeedMultiplierAtNight = 1f;
        /// <summary>ground (default: hugs the terrain) | water (swims below the surface, never leaves the water) |
        /// air (flies HoverM above the ground while moving, lands when it stops).</summary>
        public string Medium = "ground";
        public float HoverM = 3f;         // air: cruising height above the ground
        public float DepthM = 0.7f;       // water: depth below the surface
        /// <summary>Ground speed (m/s) the walk / run clips' feet cover at playback 1 (tools/gait_fix.py measures it).
        /// 0 = do not match playback speed to movement speed.</summary>
        public float WalkNativeMps;
        public float RunNativeMps;
    }

    /// <summary>
    /// One test / score term. Used two ways: in `requires` (must evaluate true) and in `score`
    /// (contributes weight * value). Exactly one kind key is set: need, time, hours, weather, season,
    /// sense, current, event, random.
    /// </summary>
    public sealed class TermDef
    {
        public string Kind;               // need | time | hours | weather | season | sense | current | event | random
        public string Key;                // need name / sense tag / behaviour id / event name / time-of-day word
        public List<string> Values = new List<string>();   // weather / season names
        public float Above = float.NaN;   // need or distance thresholds
        public float Below = float.NaN;
        public float Within = float.NaN;  // sense: nearest target closer than this
        public float Beyond = float.NaN;  // sense: nearest target farther than this
        public float FromHour = float.NaN;
        public float ToHour = float.NaN;
        public string Curve = "linear";   // linear | inverse | squared | sqrt | closer | farther
        public float Weight = 1f;         // only used in `score`
        public bool Not;                  // invert a boolean term

        public bool IsBoolean =>
            Kind == "time" || Kind == "hours" || Kind == "weather" || Kind == "season" ||
            Kind == "current" || Kind == "event" ||
            (Kind == "need" && (!float.IsNaN(Above) || !float.IsNaN(Below))) ||
            (Kind == "sense" && (!float.IsNaN(Within) || !float.IsNaN(Beyond)) && Curve == "linear");
    }

    /// <summary>What an animal does when a behaviour wins. `Type` picks a built-in action.</summary>
    public sealed class ActionDef
    {
        public string Type;               // idle | wander | goto | follow | flee | rest | emote | consume | sequence
        public string Anim;               // animation slot name ("idle", "sit", ...) or a raw clip name
        public string Speed = "walk";     // walk | run | a number in m/s
        public string Target;             // sense tag: player, home, water, food, animal:<species>, <custom tag>
        public float Radius = 6f;         // wander radius
        public float MinDist = 2f;        // follow: hold this far behind; flee: keep at least this far
        public float MaxDist = 6f;        // follow: catch up beyond this
        public float ArriveDist = 0.8f;
        public float DurationMin = 2f;    // seconds (idle, emote, rest without `until`)
        public float DurationMax = 5f;
        public string StayNear = "home";  // wander: home | player | none
        public string Need;               // consume / rest: need restored
        public float RestorePerSecond = 0.05f;
        public TermDef Until;             // rest / follow: stop when this becomes true
        public List<ActionDef> Steps = new List<ActionDef>();   // sequence
    }

    /// <summary>A rule: when its `requires` hold, its score competes with the other behaviours.</summary>
    public sealed class BehaviorDef
    {
        public string Id;
        public ActionDef Action;
        public List<TermDef> Requires = new List<TermDef>();
        public List<TermDef> Score = new List<TermDef>();
        public float Base = 0.1f;
        public float CooldownSeconds = 0f;
        public float MinSeconds = 1.5f;   // must run at least this long before something else may take over
        public int Priority = 0;          // higher priority interrupts lower even inside MinSeconds
        public bool Interruptible = true;
        public bool Disabled;             // {"id": "x", "disabled": true} removes an inherited behaviour
    }

    public sealed class AnimalAIDefinition
    {
        public string Id;
        public string SourceMod;
        /// <summary>Definitions this one builds on (parents first). Their needs, senses, movement, animations
        /// and behaviours are inherited; this one overrides by name / id.</summary>
        public List<string> Extends = new List<string>();
        /// <summary>A template: never applied to an animal directly, only extended.</summary>
        public bool Abstract;
        /// <summary>Sense tags this animal carries, so other animals can react to it (e.g. "predator", "prey").</summary>
        public List<string> Tags = new List<string>();
        public ModJsonValue RawSenses;    // kept so a child only overrides the keys it actually sets
        public ModJsonValue RawMovement;
        /// <summary>Resolved definitions: every senses / movement object from the extends chain, parents first.</summary>
        public List<ModJsonValue> SenseLayers = new List<ModJsonValue>();
        public List<ModJsonValue> MovementLayers = new List<ModJsonValue>();
        public List<string> AppliesTo = new List<string>();      // item ids, or "species:<name>"
        public Dictionary<string, NeedDef> Needs = new Dictionary<string, NeedDef>(StringComparer.OrdinalIgnoreCase);
        public SenseDef Senses = new SenseDef();
        public MovementDef Movement = new MovementDef();
        public Dictionary<string, string> Animations = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
        public List<BehaviorDef> Behaviors = new List<BehaviorDef>();

        public string ClipFor(string slotOrClip)
        {
            if (string.IsNullOrEmpty(slotOrClip)) return null;
            return Animations.TryGetValue(slotOrClip, out string clip) ? clip : slotOrClip;
        }
    }

    /// <summary>Reads animal_ai JSON into <see cref="AnimalAIDefinition"/>. Never throws; problems become warnings.</summary>
    public static class AnimalAIParser
    {
        private static readonly HashSet<string> ActionTypes = new HashSet<string>(StringComparer.OrdinalIgnoreCase)
            { "idle", "wander", "goto", "follow", "flee", "rest", "emote", "consume", "sequence" };

        public static AnimalAIDefinition Parse(ModJsonValue root, string sourceMod, Action<string> warn)
        {
            var def = new AnimalAIDefinition { SourceMod = sourceMod, Id = root.Get("id").AsString() };
            if (string.IsNullOrEmpty(def.Id)) { warn("animal_ai file has no \"id\""); return null; }

            def.AppliesTo = root.Get("applies_to").AsStringList();
            def.Extends = root.Get("extends").AsStringList();
            def.Abstract = root.Get("abstract").AsBool(false);
            def.Tags = root.Get("tags").AsStringList();
            if (def.AppliesTo.Count == 0 && !def.Abstract)
                warn($"{def.Id}: \"applies_to\" is empty, so no animal will use it (mark it \"abstract\": true if it is a template)");

            ModJsonValue needs = root.Get("needs");
            if (needs.IsObject)
                foreach (var kv in needs.ObjectValue)
                    def.Needs[kv.Key] = new NeedDef
                    {
                        Name = kv.Key,
                        Start = kv.Value.Get("start").AsFloat(0.5f),
                        RatePerGameHour = kv.Value.Get("rate_per_game_hour").AsFloat(0f),
                        Min = kv.Value.Get("min").AsFloat(0f),
                        Max = kv.Value.Get("max").AsFloat(1f),
                    };

            def.RawSenses = root.Get("senses");
            def.RawMovement = root.Get("movement");
            ApplySenses(def.Senses, def.RawSenses);
            ApplyMovement(def.Movement, def.RawMovement);

            ModJsonValue anims = root.Get("animations");
            if (anims.IsObject)
                foreach (var kv in anims.ObjectValue) def.Animations[kv.Key] = kv.Value.AsString();

            var ids = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
            foreach (ModJsonValue b in root.Get("behaviors").Items)
            {
                var bd = ParseBehavior(b, def.Id, warn);
                if (bd == null) continue;
                if (!ids.Add(bd.Id)) { warn($"{def.Id}: duplicate behavior id '{bd.Id}' ignored"); continue; }
                def.Behaviors.Add(bd);
            }
            if (def.Behaviors.Count == 0 && def.Extends.Count == 0) warn($"{def.Id}: no valid behaviors");

            // Term cross-checks (unknown need / behaviour) run after inheritance is resolved: AnimalAIRegistry.Resolve.
            return def;
        }

        public static void ApplySenses(SenseDef s, ModJsonValue v)
        {
            s.SightM = v.Get("sight_m").AsFloat(s.SightM);
            s.HearM = v.Get("hear_m").AsFloat(s.HearM);
        }

        public static void ApplyMovement(MovementDef m, ModJsonValue v)
        {
            m.WalkSpeed = v.Get("walk_speed").AsFloat(m.WalkSpeed);
            m.RunSpeed = v.Get("run_speed").AsFloat(m.RunSpeed);
            m.TurnSpeedDeg = v.Get("turn_speed_deg").AsFloat(m.TurnSpeedDeg);
            m.MaxSlopeDeg = v.Get("max_slope_deg").AsFloat(m.MaxSlopeDeg);
            m.ArriveDistM = v.Get("arrive_dist_m").AsFloat(m.ArriveDistM);
            m.Medium = v.Get("medium").AsString(m.Medium).ToLowerInvariant();
            m.HoverM = v.Get("hover_m").AsFloat(m.HoverM);
            m.DepthM = v.Get("depth_m").AsFloat(m.DepthM);
            m.WalkNativeMps = v.Get("walk_native_mps").AsFloat(m.WalkNativeMps);
            m.RunNativeMps = v.Get("run_native_mps").AsFloat(m.RunNativeMps);
        }

        /// <summary>Checks a resolved definition's terms. Public so the registry can report after inheritance.</summary>
        public static void CrossCheck(AnimalAIDefinition def, Action<string> warn)
        {
            foreach (BehaviorDef bd in def.Behaviors)
            {
                foreach (TermDef t in bd.Requires) CheckTerm(def, bd, t, warn);
                foreach (TermDef t in bd.Score) CheckTerm(def, bd, t, warn);
            }
            if (def.Behaviors.Count == 0) warn($"{def.Id}: no behaviors (after inheritance)");
        }

        private static void CheckTerm(AnimalAIDefinition def, BehaviorDef bd, TermDef t, Action<string> warn)
        {
            if (t.Kind == "need" && !def.Needs.ContainsKey(t.Key))
                warn($"{def.Id}/{bd.Id}: refers to unknown need '{t.Key}'");
            if (t.Kind == "current" && !def.Behaviors.Exists(x => string.Equals(x.Id, t.Key, StringComparison.OrdinalIgnoreCase)))
                warn($"{def.Id}/{bd.Id}: 'current' refers to unknown behavior '{t.Key}'");
        }

        private static BehaviorDef ParseBehavior(ModJsonValue b, string owner, Action<string> warn)
        {
            string id = b.Get("id").AsString();
            if (string.IsNullOrEmpty(id)) { warn($"{owner}: a behavior has no id"); return null; }
            if (b.Get("disabled").AsBool(false)) return new BehaviorDef { Id = id, Disabled = true };

            ActionDef action = ParseAction(b.Get("action"), $"{owner}/{id}", warn);
            if (action == null) return null;

            var bd = new BehaviorDef
            {
                Id = id,
                Action = action,
                Base = b.Get("base").AsFloat(0.1f),
                CooldownSeconds = b.Get("cooldown_s").AsFloat(0f),
                MinSeconds = b.Get("min_s").AsFloat(1.5f),
                Priority = b.Get("priority").AsInt(0),
                Interruptible = b.Get("interruptible").AsBool(true),
            };
            foreach (ModJsonValue t in b.Get("requires").Items) AddTerm(bd.Requires, t, $"{owner}/{id}", warn);
            foreach (ModJsonValue t in b.Get("score").Items) AddTerm(bd.Score, t, $"{owner}/{id}", warn);
            return bd;
        }

        private static void AddTerm(List<TermDef> list, ModJsonValue t, string ctx, Action<string> warn)
        {
            TermDef term = ParseTerm(t, ctx, warn);
            if (term != null) list.Add(term);
        }

        public static TermDef ParseTerm(ModJsonValue t, string ctx, Action<string> warn)
        {
            var term = new TermDef
            {
                Weight = t.Get("weight").AsFloat(1f),
                Curve = t.Get("curve").AsString("linear"),
                Not = t.Get("not").AsBool(false),
                Above = t.Has("above") ? t.Get("above").AsFloat() : float.NaN,
                Below = t.Has("below") ? t.Get("below").AsFloat() : float.NaN,
                Within = t.Has("within") ? t.Get("within").AsFloat() : float.NaN,
                Beyond = t.Has("beyond") ? t.Get("beyond").AsFloat() : float.NaN,
            };
            if (t.Has("need")) { term.Kind = "need"; term.Key = t.Get("need").AsString(); }
            else if (t.Has("time")) { term.Kind = "time"; term.Key = t.Get("time").AsString(); }
            else if (t.Has("hours"))
            {
                term.Kind = "hours";
                var h = t.Get("hours");
                if (h.Count >= 2) { term.FromHour = h.ArrayValue[0].AsFloat(); term.ToHour = h.ArrayValue[1].AsFloat(); }
                else { warn($"{ctx}: 'hours' needs [from, to]"); return null; }
            }
            else if (t.Has("weather")) { term.Kind = "weather"; term.Values = ToList(t.Get("weather")); }
            else if (t.Has("season")) { term.Kind = "season"; term.Values = ToList(t.Get("season")); }
            else if (t.Has("sense")) { term.Kind = "sense"; term.Key = t.Get("sense").AsString(); }
            else if (t.Has("current")) { term.Kind = "current"; term.Key = t.Get("current").AsString(); }
            else if (t.Has("event")) { term.Kind = "event"; term.Key = t.Get("event").AsString(); }
            else if (t.Has("random")) { term.Kind = "random"; term.Weight = t.Get("random").AsFloat(0.1f); }
            else { warn($"{ctx}: a term has no recognised key (need/time/hours/weather/season/sense/current/event/random)"); return null; }
            return term;
        }

        private static List<string> ToList(ModJsonValue v)
        {
            if (v.IsArray) return v.AsStringList();
            string s = v.AsString();
            return s == null ? new List<string>() : new List<string> { s };
        }

        private static ActionDef ParseAction(ModJsonValue a, string ctx, Action<string> warn)
        {
            if (a.IsNull || !a.IsObject) { warn($"{ctx}: missing \"action\""); return null; }
            string type = a.Get("type").AsString();
            if (string.IsNullOrEmpty(type) || !ActionTypes.Contains(type))
            {
                warn($"{ctx}: unknown action type '{type}' (use idle, wander, goto, follow, flee, rest, emote, consume, sequence)");
                return null;
            }
            var ad = new ActionDef
            {
                Type = type.ToLowerInvariant(),
                Anim = a.Get("anim").AsString(),
                Speed = a.Get("speed").Type == ModJsonValue.NodeType.Number
                    ? a.Get("speed").AsFloat().ToString(System.Globalization.CultureInfo.InvariantCulture)
                    : a.Get("speed").AsString("walk"),
                Target = a.Get("target").AsString(),
                Radius = a.Get("radius").AsFloat(6f),
                MinDist = a.Get("min_dist").AsFloat(2f),
                MaxDist = a.Get("max_dist").AsFloat(6f),
                ArriveDist = a.Get("arrive_dist").AsFloat(0.8f),
                StayNear = a.Get("stay_near").AsString("home"),
                Need = a.Get("need").AsString(),
                RestorePerSecond = a.Get("restore_per_second").AsFloat(0.05f),
            };
            ModJsonValue dur = a.Get("duration");
            if (dur.IsArray && dur.Count >= 2) { ad.DurationMin = dur.ArrayValue[0].AsFloat(); ad.DurationMax = dur.ArrayValue[1].AsFloat(); }
            else if (dur.Type == ModJsonValue.NodeType.Number) { ad.DurationMin = ad.DurationMax = dur.AsFloat(); }
            if (a.Has("until")) ad.Until = ParseTerm(a.Get("until"), ctx + "/until", warn);
            foreach (ModJsonValue step in a.Get("steps").Items)
            {
                ActionDef s = ParseAction(step, ctx + "/step", warn);
                if (s != null) ad.Steps.Add(s);
            }
            if (ad.Type == "sequence" && ad.Steps.Count == 0) { warn($"{ctx}: 'sequence' has no steps"); return null; }
            if ((ad.Type == "goto" || ad.Type == "follow" || ad.Type == "flee" || ad.Type == "consume") && string.IsNullOrEmpty(ad.Target))
            { warn($"{ctx}: '{ad.Type}' needs a \"target\""); return null; }
            return ad;
        }
    }
}
