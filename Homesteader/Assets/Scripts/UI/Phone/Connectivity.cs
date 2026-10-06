using Homesteader.Growth;
using UnityEngine;

namespace Homesteader.UI
{
    /// <summary>
    /// How the phone is connected right now (docs/INTERNET.md), worked out a few times a second from where the player stands.
    /// CELLULAR: the signal differs from place to place, drops in bad weather (a thunderstorm, and most of all a blizzard), is weaker indoors, and a
    /// powered cellular antenna near by lifts it by 30%. With no bars there is no internet. WI-FI: in range of a powered router or access point the
    /// phone joins it, and that works at full strength as long as that network has internet (a dish, cabled through a router); a Wi-Fi with no
    /// internet behind it leaves the phone on cellular.
    /// </summary>
    public static class Connectivity
    {
        public enum Link { None, Cellular, Wifi }

        public static Link Current { get; private set; }
        public static int Bars { get; private set; }            // 0 to 4, of the link in use
        public static bool Online { get; private set; }         // the phone has internet
        public static float CellStrength { get; private set; }  // 0 to 1
        public static int CellBars { get; private set; }
        public static bool Indoors { get; private set; }
        public static bool Boosted { get; private set; }
        public static string Label { get; private set; } = "5G";

        public const float IdleMbps = 0.5f, InUseMbps = 5f;   // what the phone takes of the homestead's bandwidth on Wi-Fi: in the pocket, and while it is being used

        /// <summary>Set by the phone while it is open: it uses more then.</summary>
        public static bool PhoneInUse;

        private static float s_time = -10f;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
        private static void ResetStatics() { s_time = -10f; Current = Link.Cellular; Bars = 3; Online = true; Label = "5G"; }

        /// <summary>What the weather leaves of the cellular signal.</summary>
        public static float WeatherFactor(HomesteaderWeather w)
        {
            switch (w)
            {
                case HomesteaderWeather.Blizzard: return 0.35f;
                case HomesteaderWeather.Thunderstorm: return 0.5f;
                case HomesteaderWeather.Snow: return 0.75f;
                case HomesteaderWeather.Rain: return 0.8f;
                case HomesteaderWeather.Fog: return 0.9f;
                case HomesteaderWeather.Wind: return 0.92f;
                default: return 1f;
            }
        }

        private static int BarsOf(float s) { return s < 0.18f ? 0 : s < 0.32f ? 1 : s < 0.48f ? 2 : s < 0.64f ? 3 : 4; }

        public static void Refresh()
        {
            if (Time.unscaledTime - s_time < 0.25f) return;
            s_time = Time.unscaledTime;
            PedController ped = PedController.Current;
            if (ped == null || TimeSystem.Instance == null) { Current = Link.Cellular; Bars = CellBars = 3; Online = true; Label = "5G"; return; }
            Vector3 pos = ped.transform.position;

            // cellular: the lie of the land, the weather, the walls, a booster
            HomesteaderWeather weather = TimeSystem.Instance.Snapshot().Weather;
            float wf = WeatherFactor(weather);
            float s = Mathf.Lerp(0.55f, 0.8f, Mathf.PerlinNoise(pos.x / 350f + 11.3f, pos.z / 350f + 4.7f)) * wf;
            Indoors = false;
            foreach (ConstructionSite site in ConstructionSite.All)
                if (site != null && site.Finished && site.IsInsideWalls(pos)) { Indoors = true; break; }
            if (Indoors) s *= 0.65f;
            float boost = Net.CellBoostAt(pos);
            Boosted = boost > 1f;
            s *= boost;
            s += (Mathf.PerlinNoise(Time.unscaledTime * 0.3f, 7.1f) - 0.5f) * 0.06f * (2f - wf);   // it wavers, more in bad weather
            CellStrength = Mathf.Clamp01(s);
            CellBars = BarsOf(CellStrength);

            bool wifi = Net.WifiAt(pos, out float ws, out bool wifiInternet);
            if (wifi && wifiInternet) { Current = Link.Wifi; Bars = Mathf.Clamp(1 + Mathf.FloorToInt(ws * 3.99f), 1, 4); Online = true; Label = "Wi-Fi"; }
            else if (CellBars > 0) { Current = Link.Cellular; Bars = CellBars; Online = true; Label = "5G"; }
            else if (wifi) { Current = Link.Wifi; Bars = Mathf.Clamp(1 + Mathf.FloorToInt(ws * 3.99f), 1, 4); Online = false; Label = "Wi-Fi !"; }
            else { Current = Link.None; Bars = 0; Online = false; Label = "No service"; }
            // on the homestead's Wi-Fi the phone always takes a little of its bandwidth, and more while it is in use; on cellular it takes none of it
            Net.PhoneMbps = Current == Link.Wifi && Online ? (PhoneInUse ? InUseMbps : IdleMbps) : 0f;
        }

        /// <summary>Why there is no internet, for the player.</summary>
        public static string Why()
        {
            Refresh();
            if (Online) return "";
            if (Current == Link.Wifi) return "This Wi-Fi has no internet behind it (it needs a powered dish cabled to its router), and there is no cellular signal here.";
            HomesteaderWeather w = TimeSystem.Instance != null ? TimeSystem.Instance.Snapshot().Weather : HomesteaderWeather.Sunny;
            string cause = WeatherFactor(w) < 0.6f ? "The " + TimeSystem.GetWeatherName(w).ToLowerInvariant() + " has knocked the cellular signal out" : "There is no cellular signal here";
            return cause + (Indoors ? ". Step outside, or set up Wi-Fi or a cellular antenna." : ". Set up Wi-Fi or a cellular antenna.");
        }

        /// <summary>True when the phone has internet; otherwise says why the app did not open (the player cannot see that happen).</summary>
        public static bool Require(string app)
        {
            Refresh();
            if (Online) return true;
            ToastNotificationSystem.ShowWarning("No internet", app + " needs a connection. " + Why());
            return false;
        }
    }
}
