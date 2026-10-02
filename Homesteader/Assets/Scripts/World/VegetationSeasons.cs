using System.Collections.Generic;
using UnityEngine;
using Homesteader.UI;

namespace Homesteader.World
{
    /// <summary>
    /// Drives the seasonal look of the procedural vegetation. Each tracked material has four keyframes (winter, spring,
    /// summer, autumn) for colour and for "grow" (see Homesteader/Vegetation shader); this blends between them smoothly
    /// from the in-game day of the year. Keyframes sit at the middle of each season, so colours drift through the year
    /// instead of snapping at the season boundary.
    /// </summary>
    public sealed class VegetationSeasons : MonoBehaviour
    {
        public sealed class Entry
        {
            public Material Mat;
            public Color[] Colour;   // winter, spring, summer, autumn (null = leave the colour alone)
            public float[] Grow;     // winter, spring, summer, autumn (null = leave growth alone)
            public float[] Loss;     // winter, spring, summer, autumn leaf loss, 0 = full canopy .. 1 = bare (null = leave it alone)
            public bool AtSeasonStart;   // keyframes sit at the START of each season instead of its middle
        }

        private const float UpdateInterval = 0.5f;   // real seconds

        private List<Entry> _entries = new List<Entry>();
        private float _next;

        public void Init(List<Entry> entries)
        {
            _entries = entries;
            Apply();
        }

        private static readonly int VegDayId = Shader.PropertyToID("_VegDay");

        /// <summary>
        /// The clock trees grow by: the furthest game day ever reached, so it never goes backwards. The in-game clock can
        /// (the Admin app sets a season by jumping to its first day), and trees read (today - birth) as their age, so a jump
        /// back made every tree shrink to a sapling. Growth stops at mature and is never undone.
        /// </summary>
        public static float GrowthDay = 141f;

        public static void RestoreGrowthDay(float day) { GrowthDay = Mathf.Max(GrowthDay, day); }
        private static readonly int VegWindPhaseId = Shader.PropertyToID("_VegWindPhase");
        private float _windPhase;

        private void Update()
        {
            // Absolute game day for tree growth (every frame: it is one float, and growth reads smoothly at high speed).
            // Wind sway phase: advance it by the current wind speed so a change of speed only changes the pace, never jumps.
            var weather = WeatherEffectsManager.Instance;
            float windSpeed = weather != null ? weather.WindSpeedMps : 0f;
            _windPhase += Time.unscaledDeltaTime * (0.7f + windSpeed * 0.3f);
            Shader.SetGlobalFloat(VegWindPhaseId, _windPhase);

            var ts = TimeSystem.Instance;
            if (ts != null) GrowthDay = Mathf.Max(GrowthDay, ts.DayOfYear + ts.MinuteOfDay / TimeConstants.CycleGameMinutes);
            Shader.SetGlobalFloat(VegDayId, GrowthDay);

            if (Time.unscaledTime < _next) return;
            _next = Time.unscaledTime + UpdateInterval;
            Apply();
        }

        /// <summary>Season position in [0,4): 0 = start of winter (1 Dec), 1 = spring, 2 = summer, 3 = autumn.</summary>
        public static float SeasonPosition()
        {
            var ts = TimeSystem.Instance;
            int day = ts != null ? ts.DayOfYear : 141;
            // Winter begins 1 Dec = day 309 of the 336-day year; every season is 84 days.
            float t = Mathf.Repeat(day - 309f, TimeConstants.DaysPerYear) / TimeConstants.DaysPerSeason;
            return t;
        }

        private void Apply()
        {
            float season = SeasonPosition();

            for (int i = 0; i < _entries.Count; i++)
            {
                Entry e = _entries[i];
                if (e.Mat == null) continue;
                // Most materials drift between season centres; flowers and the like key off the season starts.
                float pos = e.AtSeasonStart ? season : season - 0.5f;
                float floor = Mathf.Floor(pos);
                float f = Mathf.SmoothStep(0f, 1f, pos - floor);
                int i0 = ((int)floor % 4 + 4) % 4;
                int i1 = (i0 + 1) % 4;
                if (e.Colour != null) e.Mat.SetColor("_BaseColor", Color.Lerp(e.Colour[i0], e.Colour[i1], f));
                if (e.Grow != null) e.Mat.SetFloat("_Grow", Mathf.Lerp(e.Grow[i0], e.Grow[i1], f));
                if (e.Loss != null) {
                    // Crowns come BACK quickly (the loss falls fast through spring) so the summer start has none missing; they go slowly in autumn.
                    float lf = e.Loss[i1] < e.Loss[i0] ? 1f - (1f - f) * (1f - f) * (1f - f) : f;
                    e.Mat.SetFloat("_LeafLoss", Mathf.Lerp(e.Loss[i0], e.Loss[i1], lf));
                }
            }
        }
    }
}
