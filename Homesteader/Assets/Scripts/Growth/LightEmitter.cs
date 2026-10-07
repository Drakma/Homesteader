using System;
using System.Collections.Generic;
using Homesteader.Modding;
using Homesteader.UI;
using UnityEngine;

namespace Homesteader.Growth
{
    /// <summary>
    /// One light an asset emits, from the asset manifest's "lights" list (assets/_schemas/light_emitter.schema.json).
    /// </summary>
    public sealed class LightDef
    {
        public string Id = "light";
        public string Type = "point";               // point | spot
        public Color Color = new Color(1f, 0.93f, 0.78f);
        public float Intensity = 3.5f;
        public float Range = 10f;
        public float SpotAngle = 90f;               // spot only
        public Vector3 Offset;                      // metres, in the model's local space (pivot at its foot)
        public float PitchDeg = 90f;                // spot: 90 = straight down, 0 = horizontal
        public float YawDeg;                        // spot: turn around the model's up axis
        public string On = "night";                 // always | night | hours
        public float FromHour = 18f, ToHour = 6f;   // "hours"
        public float FadeMinutes = 20f;             // game minutes to brighten to full after switching on
        public float DimMinutes = -1f;              // game minutes to dim out after it is due off (< 0 = same as FadeMinutes)
        public float DuskLeadMinutes = 30f;         // "night": switches on this many minutes BEFORE sunset
        public float DawnLagMinutes = 30f;          // "night": switches off this many minutes AFTER sunrise
        public float Flicker;                       // 0 steady .. 1 heavy
        public float StartupFlicker;                // 0 none .. 1: sputters when it first switches on
        public float StartupSeconds = 6f;           // real seconds the sputter lasts (independent of the fade)
        public float MinLevel = 0.25f;              // brightness (0..1) it strikes at; it then brightens over FadeMinutes
        public bool Shadows;
        public bool RequiresPower;
        public float PowerW;                        // informational: the draw when on

        public static List<LightDef> ParseList(ModJsonValue arr)
        {
            var list = new List<LightDef>();
            if (arr == null || !arr.IsArray) return list;
            foreach (ModJsonValue v in arr.Items)
            {
                if (!v.IsObject) continue;
                var d = new LightDef
                {
                    Id = v.Get("id").AsString("light"),
                    Type = v.Get("type").AsString("point").ToLowerInvariant(),
                    Intensity = v.Get("intensity").AsFloat(3.5f),
                    Range = v.Get("range_m").AsFloat(v.Get("range").AsFloat(10f)),
                    SpotAngle = v.Get("spot_angle_deg").AsFloat(90f),
                    PitchDeg = v.Get("pitch_deg").AsFloat(90f),
                    YawDeg = v.Get("yaw_deg").AsFloat(0f),
                    On = v.Get("on").AsString("night").ToLowerInvariant(),
                    FadeMinutes = Mathf.Max(0f, v.Get("fade_minutes").AsFloat(20f)),
                    DimMinutes = v.Has("dim_minutes") ? Mathf.Max(0f, v.Get("dim_minutes").AsFloat(-1f)) : -1f,
                    DuskLeadMinutes = Mathf.Max(0f, v.Get("dusk_lead_minutes").AsFloat(30f)),
                    DawnLagMinutes = Mathf.Max(0f, v.Get("dawn_lag_minutes").AsFloat(30f)),
                    Flicker = Mathf.Clamp01(v.Get("flicker").AsFloat(0f)),
                    StartupFlicker = Mathf.Clamp01(v.Get("startup_flicker").AsFloat(0f)),
                    StartupSeconds = Mathf.Max(0.1f, v.Get("startup_seconds").AsFloat(6f)),
                    MinLevel = Mathf.Clamp01(v.Get("min_level").AsFloat(0.25f)),
                    Shadows = v.Get("shadows").AsBool(false),
                    RequiresPower = v.Get("requires_power").AsBool(false),
                    PowerW = v.Get("power_w").AsFloat(0f),
                };
                string col = v.Get("color").AsString();
                if (!string.IsNullOrEmpty(col) && ColorUtility.TryParseHtmlString(col, out Color c)) d.Color = c;
                ModJsonValue off = v.Get("offset_m");
                if (off.Count >= 3) d.Offset = new Vector3(off.ArrayValue[0].AsFloat(), off.ArrayValue[1].AsFloat(), off.ArrayValue[2].AsFloat());
                ModJsonValue hours = v.Get("hours");
                if (hours.Count >= 2) { d.FromHour = hours.ArrayValue[0].AsFloat(); d.ToHour = hours.ArrayValue[1].AsFloat(); }
                list.Add(d);
            }
            return list;
        }
    }

    /// <summary>
    /// Drives the lights an asset emits: builds a Light per <see cref="LightDef"/> as children of the model and
    /// fades them on and off with the time of day. "night" is sunset to sunrise (from the game clock), "hours" is a
    /// from/to hour range, "always" is always on. A light that needs power stays off while
    /// <see cref="PowerCheck"/> says it has none.
    /// </summary>
    public sealed class LightEmitter : MonoBehaviour
    {
        /// <summary>
        /// Set by the game's power system: (item id, world position, watts) -> is it powered right now. While
        /// null every light is treated as powered (so nothing goes dark with no way to fix it).
        /// </summary>
        public static Func<string, Vector3, float, bool> PowerCheck;

        /// <summary>Set by the game's power system: (item id, position, watts) -> how much of its voltage the light gets, 0 (none: it goes out at once) to 1 (full). Below 1 it dims and flickers.</summary>
        public static Func<string, Vector3, float, float> PowerRatio;

        /// <summary>Set by the game's power system: the building a light is mounted in (null when it is not on one).</summary>
        public static Func<Vector3, ConstructionSite> SiteOf;

        private ConstructionSite _site;
        private bool _siteKnown;

        /// <summary>Calls back for every mains-powered light that wants to be on: where it is, the building it is in (or null) and the watts it would draw. For the generators.</summary>
        public static void ForEachDemand(System.Action<Vector3, ConstructionSite, float> f)
        {
            if (SiteOf == null) return;
            foreach (LightEmitter e in instances)
            {
                if (e == null) continue;
                if (!e._siteKnown) { e._site = SiteOf(e.transform.position); e._siteKnown = true; }
                foreach (Runtime r in e.lights) if (r.Def.RequiresPower && r.Want > 0.001f) f(e.transform.position, e._site, r.Def.PowerW * r.Want);
            }
        }

        /// <summary>What the lights of this building would draw right now (their watts times how on they want to be), for the power balance. Lights without a power need draw nothing.</summary>
        public static float WantedWatts(ConstructionSite site)
        {
            if (site == null || SiteOf == null) return 0f;
            float sum = 0f;
            foreach (LightEmitter e in instances)
            {
                if (e == null) continue;
                if (!e._siteKnown) { e._site = SiteOf(e.transform.position); e._siteKnown = true; }
                if (e._site != site) continue;
                foreach (Runtime r in e.lights) if (r.Def.RequiresPower) sum += r.Def.PowerW * r.Want;
            }
            return sum;
        }

        private sealed class Runtime
        {
            public LightDef Def;
            public Light Light;
            public float Level;       // 0..1 current fade
            public float Target;      // 0..1 wanted right now (refreshed a few times a second)
            public float Want;        // the same before the power is taken into account (what it would draw)
            public float Grid = 1f;   // how much of its voltage it gets (0 none, 1 full)
            public bool WasLit;
            public float LitSince;    // Time.time when it last switched on
            public float Seed;
        }

        private readonly List<Runtime> lights = new List<Runtime>();

        /// <summary>A lit light as the map shows it: where, how far it reaches, how bright it is right now (0..1) and its colour.</summary>
        public struct Glow { public Vector3 Position; public float Range; public float Level; public Color Colour; }

        private static readonly List<LightEmitter> instances = new List<LightEmitter>();
        private void OnEnable() { if (!instances.Contains(this)) instances.Add(this); }
        private void OnDisable() => instances.Remove(this);

        /// <summary>Every light that is currently on, for the map to glow around.</summary>
        public static IEnumerable<Glow> ActiveGlows()
        {
            foreach (LightEmitter e in instances)
            {
                if (e == null) continue;
                foreach (Runtime r in e.lights)
                {
                    if (r.Light == null || !r.Light.enabled) continue;
                    yield return new Glow
                    {
                        Position = r.Light.transform.position, Range = r.Def.Range, Colour = r.Def.Color,
                        Level = Mathf.Clamp01(r.Light.intensity / Mathf.Max(0.01f, r.Def.Intensity)),
                    };
                }
            }
        }
        private string itemId;
        private float nextTick;

        /// <summary>Switched off by the player (a right click): it stays dark whatever the time, the room or the power. Saved with the placed or mounted item.</summary>
        public bool SwitchedOff;

        private const float SwitchReach = 4f;

        /// <summary>A plain right click on a light (a lamp, a ceiling or wall light, a post light) switches it off or on. Not with a wrench (that takes it down) or the wire tools.</summary>
        public static bool TryRightClick(Camera cam, Vector2 pointer, Transform player)
        {
            if (cam == null || instances.Count == 0 || WireTool.JoinToolHeld() || AttachedObject.WrenchInHand()) return false;
            LightEmitter e = UnderCursor(cam, pointer);
            if (e == null) return false;
            if (player != null && Vector3.Distance(player.position, e.transform.position) > SwitchReach)
            {
                ToastNotificationSystem.ShowInfo("Too far", "Move closer to the light switch it.");
                return true;
            }
            e.SwitchedOff = !e.SwitchedOff;
            return true;
        }

        /// <summary>The light fixture under the cursor (nothing else in front of it), or null.</summary>
        public static LightEmitter UnderCursor(Camera cam, Vector2 pointer)
        {
            RaycastHit[] hits = Physics.RaycastAll(cam.ScreenPointToRay(pointer), 1000f, Physics.DefaultRaycastLayers, QueryTriggerInteraction.Collide);
            Array.Sort(hits, (x, y) => x.distance.CompareTo(y.distance));
            foreach (RaycastHit h in hits)
            {
                if (h.collider.GetComponentInParent<PedController>() != null) continue;
                LightEmitter e = h.collider.GetComponentInParent<LightEmitter>();
                if (e != null) return e;
                if (!h.collider.isTrigger) return null;   // something solid is in front
            }
            return null;
        }

        /// <summary>Adds the emitter and its lights to a placed / spawned model.</summary>
        public static void Attach(GameObject model, string itemId, IList<LightDef> defs)
        {
            if (model == null || defs == null || defs.Count == 0) return;
            var e = model.AddComponent<LightEmitter>();
            e.itemId = itemId;
            foreach (LightDef d in defs)
            {
                var go = new GameObject("Light_" + d.Id);
                go.transform.SetParent(model.transform, false);
                go.transform.localPosition = d.Offset;
                go.transform.localRotation = Quaternion.Euler(d.PitchDeg, d.YawDeg, 0f);
                var l = go.AddComponent<Light>();
                l.type = d.Type == "spot" ? LightType.Spot : LightType.Point;
                l.color = d.Color;
                l.range = Mathf.Max(0.1f, d.Range);
                if (l.type == LightType.Spot) l.spotAngle = Mathf.Clamp(d.SpotAngle, 1f, 179f);
                LightOcclusion.Register(l);   // walls stop the light (the Graphics setting Light Occlusion switches it)
                l.intensity = 0f;
                l.enabled = false;
                e.lights.Add(new Runtime { Def = d, Light = l, Seed = UnityEngine.Random.value * 100f });
            }
        }

        private void Update()
        {
            // Light levels ease every frame; the clock is only read a few times a second.
            bool tick = Time.unscaledTime >= nextTick;
            if (tick) nextTick = Time.unscaledTime + 0.25f;

            HudTimeState t = default;
            if (tick && TimeSystem.Instance != null) t = TimeSystem.Instance.Snapshot();

            bool occupied = !tick || Occupied();
            foreach (Runtime r in lights)
            {
                if (r.Light == null) continue;
                if (tick)
                {
                    r.Want = occupied && !SwitchedOff ? TargetLevel(r.Def, t) : 0f;
                    r.Grid = r.Def.RequiresPower ? GridRatio() : 1f;
                    r.Target = r.Grid > 0f ? r.Want : 0f;
                }
                if (SwitchedOff) { r.Want = 0f; r.Target = 0f; r.Level = 0f; }   // switched off by hand: out at once, no fade
                if (r.Grid <= 0f) r.Level = 0f;   // the power is gone: the light goes out at once
                else r.Level = Mathf.MoveTowards(r.Level, r.Target, Time.deltaTime * 1.5f);   // eases switch-ons
                // It strikes at MinLevel and then brightens over the fade; going off it fades out from wherever it is.
                bool lit = r.Target > 0.001f || r.Level > 0.001f;
                if (lit && !r.WasLit) r.LitSince = Time.time;
                r.WasLit = lit;
                // Switching on it strikes at MinLevel and brightens; going off it DIMS smoothly all the way to dark
                // (no jump from the strike level to off).
                bool dimming = r.Target < r.Level - 0.001f;
                float shown = !lit ? 0f : dimming ? Mathf.Clamp01(r.Level) : Mathf.Lerp(r.Def.MinLevel, 1f, Mathf.Clamp01(r.Level));

                float flick = 1f;
                if (r.Def.Flicker > 0f)
                    flick = 1f - r.Def.Flicker * 0.6f * Mathf.PerlinNoise(r.Seed, Time.time * 9f);
                // Switch-on: a short sputter at the strike level (StartupSeconds), steadying, THEN the slow brighten.
                float since = Time.time - r.LitSince;
                if (r.Def.StartupFlicker > 0f && lit && since < r.Def.StartupSeconds)
                {
                    float amount = r.Def.StartupFlicker * (1f - since / r.Def.StartupSeconds);
                    float n = Mathf.PerlinNoise(r.Seed + 7.3f, Time.time * 14f);
                    float sputter = Mathf.SmoothStep(0f, 1f, (n - 0.3f) * 3f);        // mostly dim, with quick bright stutters
                    flick *= Mathf.Lerp(1f, sputter, amount);
                }
                // a brownout (less voltage than it needs): dim, and cutting in and out
                float brown = 1f;
                if (r.Def.RequiresPower && r.Grid > 0f && r.Grid < 0.98f)
                {
                    float sag = 1f - r.Grid;
                    float n = Mathf.PerlinNoise(r.Seed + 3.1f, Time.time * 5f);
                    float drop = Mathf.SmoothStep(0f, 1f, (sag * 0.9f - n + 0.1f) * 5f);   // the worse the sag, the more of the time it is out
                    brown = Mathf.Lerp(0.15f, 1f, r.Grid) * (1f - 0.95f * drop);
                }
                r.Light.intensity = r.Def.Intensity * shown * flick * brown;
                r.Light.enabled = r.Light.intensity > 0.01f;
            }
        }

        private AttachedObject _mount;
        private bool _mountKnown;
        private int _mountTries;

        /// <summary>
        /// A light mounted INSIDE a building is on only while the player is in its ROOM (<see cref="RoomMap"/>: the rooms are worked out from the building's
        /// walls): it goes out when they leave the room and comes back on when they return (and draws no power meanwhile). Outside lights (an exterior
        /// sconce, a pole light) and lights that are not mounted on a building are not affected. A building whose rooms cannot be told is one room.
        /// </summary>
        private bool Occupied()
        {
            if (!_mountKnown) { _mount = GetComponentInParent<AttachedObject>(); _mountKnown = _mount != null || ++_mountTries >= 8; }   // (the mount may be added just after the lights)
            if (_mount == null || _mount.Site == null || _mount.Exterior) return true;
            PedController ped = PedController.Current;
            if (ped == null) return true;
            Vector3 player = ped.transform.position;
            if (!_mount.Site.IsInside(player)) return false;
            if (RoomMap.Count(_mount.Site) < 2) return true;   // one room, or the model is still loading
            Vector3 lamp = lights.Count > 0 && lights[0].Light != null ? lights[0].Light.transform.position : transform.position;
            int mine = RoomMap.RoomAt(_mount.Site, lamp), theirs = RoomMap.PlayerRoom(_mount.Site, player);
            return mine < 0 || mine == theirs;   // (a lamp whose room cannot be told follows the building)
        }

        private float GridRatio()
        {
            if (PowerRatio != null) return Mathf.Clamp01(PowerRatio(itemId, transform.position, 0f));
            if (PowerCheck != null) return PowerCheck(itemId, transform.position, 0f) ? 1f : 0f;
            return 1f;
        }

        /// <summary>1 when the light should be fully on for this moment, 0 fully off, ramping across FadeMinutes.</summary>
        private float TargetLevel(LightDef d, HudTimeState t)
        {
            if (d.On == "always") return 1f;

            float from, to;
            if (d.On == "hours") { from = d.FromHour * 60f; to = d.ToHour * 60f; }
            else { from = t.SunsetMinute - d.DuskLeadMinutes; to = t.SunriseMinute + d.DawnLagMinutes; }   // "night": today's sunset / sunrise (they move with the seasons)
            return WindowLevel(t.MinuteOfDay, from, to, d.FadeMinutes, d.DimMinutes >= 0f ? d.DimMinutes : d.FadeMinutes);
        }

        /// <summary>Level (0..1) for an on-window [from, to] in minutes of the day (wrapping midnight): switches on at
        /// `from`, reaching full brightness `fade` minutes later, and starts dimming at `to`, fully off `fade` minutes later.</summary>
        public static float WindowLevel(float minute, float from, float to, float fade) => WindowLevel(minute, from, to, fade, fade);

        public static float WindowLevel(float minute, float from, float to, float fade, float fadeOut)
        {
            float span = Mod(to - from, 1440f);
            if (span < 0.01f) span = 1440f;                      // from == to: always on
            fade = Mathf.Max(0.01f, fade);
            fadeOut = Mathf.Max(0.01f, fadeOut);
            float since = Mod(minute - from, 1440f);             // minutes since the window opened
            if (since <= span) return Mathf.Min(1f, since / fade);
            float pastEnd = since - span;
            return pastEnd < fadeOut ? 1f - pastEnd / fadeOut : 0f;
        }

        private static float Mod(float a, float m) { float r = a % m; return r < 0f ? r + m : r; }
    }
}
