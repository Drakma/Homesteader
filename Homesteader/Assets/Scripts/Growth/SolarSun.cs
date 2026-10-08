using System.Collections.Generic;
using UnityEngine;
using Homesteader.UI;

namespace Homesteader.Growth
{
    /// <summary>
    /// The sun as a power source: 0 at sunrise and sunset and all night, a half sine between them with the peak at solar noon (the middle of the day), cut by the weather
    /// (cloud, rain, fog, snow). A solar panel makes its rated watts times this.
    /// </summary>
    public static class SolarSun
    {
        /// <summary>The share of a panel's rated power the sky lets through right now, 0 to 1.</summary>
        public static float Factor(out float sunShare, out float weatherShare)
        {
            sunShare = 0f;
            weatherShare = 1f;
            TimeSystem ts = TimeSystem.Instance;
            if (ts == null) return 0f;
            HudTimeState t = ts.Snapshot();
            float rise = t.SunriseMinute, set = t.SunsetMinute;
            if (set - rise < 1f) return 0f;
            float f = (t.CycleMinute - rise) / (set - rise);
            if (f <= 0f || f >= 1f) return 0f;                      // night: nothing
            sunShare = Mathf.Sin(f * Mathf.PI);                     // noon = 1
            weatherShare = WeatherShare(t.Weather);
            return sunShare * weatherShare;
        }

        public static float Factor() { return Factor(out _, out _); }

        public static float WeatherShare(HomesteaderWeather w)
        {
            switch (w)
            {
                case HomesteaderWeather.Sunny: return 1f;
                case HomesteaderWeather.Wind: return 0.95f;
                case HomesteaderWeather.PartlyCloudy: return 0.75f;
                case HomesteaderWeather.Cloudy: return 0.30f;
                case HomesteaderWeather.Fog: return 0.35f;
                case HomesteaderWeather.Snow: return 0.25f;
                case HomesteaderWeather.Rain: return 0.20f;
                case HomesteaderWeather.Blizzard: return 0.10f;
                case HomesteaderWeather.Thunderstorm: return 0.12f;
                default: return 1f;
            }
        }

        /// <summary>What a solar panel node makes right now, in watts.</summary>
        public static float PanelWatts(WireNode n)
        {
            if (n == null || n.Role != WireRole.SolarPanel) return 0f;
            string panel = MountedPanel.PanelOn(n.gameObject);   // a mount makes power only with a panel fitted
            AssetCatalogItem it = panel != null ? HudBindings.GetCatalogItem(panel) : null;
            return it != null ? it.max_power_w * Factor() : 0f;
        }

        /// <summary>The solar watts reaching a device along its DC wiring (every panel wired to it, through wall entries, breakers, controllers and bus bars).</summary>
        public static float InputWatts(WireNode from)
        {
            var seen = new HashSet<WireNode> { from };
            var queue = new Queue<WireNode>();
            queue.Enqueue(from);
            float sum = 0f;
            while (queue.Count > 0)
            {
                WireNode cur = queue.Dequeue();
                foreach (WireLink l in WireNetwork.Links)
                {
                    if (l.Kind != "dc" || !l.Connects(cur)) continue;
                    WireNode o = l.Other(cur);
                    if (o == null || !seen.Add(o)) continue;
                    if (o.Open) continue;   // a safety disconnect thrown off, or a part that tripped: nothing comes through it
                    if (o.Role == WireRole.SolarPanel) sum += PanelWatts(o);
                    queue.Enqueue(o);   // on past a panel too: panels wired to panels add up
                }
            }
            return sum;
        }

        public static string Power(float w)
        {
            return w >= 1000f ? (w / 1000f).ToString("0.##") + " kW" : Mathf.RoundToInt(w) + " W";
        }
    }
}
