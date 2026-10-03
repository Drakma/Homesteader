// RadioScriptContext.cs - the facts a radio episode is written from: the day, the almanac forecasts, the sky, and
// what is happening on the player's own farm. Gathered once per episode on the main thread; both script writers
// (templated and Claude) read only this, never the game directly, so an episode is reproducible and the Claude prompt
// can be shown to the player verbatim.

using System.Collections.Generic;
using System.Globalization;
using System.Text;
using Homesteader.Animals;
using Homesteader.Growth;
using Homesteader.UI;
using UnityEngine;

namespace Homesteader.Radio
{
    public sealed class RadioScriptContext
    {
        public struct CropFact { public string Name; public int Count; public int Ready; }
        public struct AnimalFact { public string Name; public int Count; }

        public int WorldSeed;
        public int DayOfYear;
        public int DayOfMonth;
        public string MonthName;
        public string Weekday;
        public string Season;
        public float MinuteOfDay;
        public bool Imperial;

        public List<DailyForecast> Daily = new List<DailyForecast>();   // offset 0 = today, 56 days
        public string AstronomicalBadge = "";
        public string MoonPhase = "";
        public string DaylightTrend = "";

        public readonly List<CropFact> Crops = new List<CropFact>();
        public readonly List<AnimalFact> Animals = new List<AnimalFact>();
        public float Money;
        public float LoanDebt;

        public DailyForecast Today => Daily.Count > 0 ? Daily[0] : default;

        // ------------------------------------------------------------------ gather

        public static RadioScriptContext Gather()
        {
            var c = new RadioScriptContext();
            TimeSystem time = TimeSystem.Instance;
            AlmanacSystem almanac = AlmanacSystem.Instance;

            c.WorldSeed = almanac.WorldSeed;
            c.DayOfYear = time.DayOfYear;
            c.MinuteOfDay = time.MinuteOfDay;
            c.DayOfMonth = time.GetDayOfMonth();
            c.MonthName = time.GetMonthName();
            c.Season = AlmanacSystem.GetSeasonForDay(c.DayOfYear).ToString();
            c.Imperial = HudState.Active.Units == UnitSystem.Imperial;

            c.Daily = almanac.GetDailyForecasts(c.DayOfYear);
            if (c.Daily.Count > 0)
            {
                c.Weekday = c.Daily[0].DayOfWeekName;
                c.AstronomicalBadge = c.Daily[0].AstronomicalBadge ?? "";
                c.MoonPhase = c.Daily[0].MoonPhaseName ?? "";
            }
            c.DaylightTrend = SpokenDaylightTrend(TimeSystem.GetDaylightTrend(c.DayOfYear));

            // Crops: alive plantings grouped by their growth group's display name; "ready" = at the final stage.
            var cropIndex = new Dictionary<string, int>();
            foreach (PlantedGrowth p in PlantedGrowth.All)
            {
                if (p == null || p.Group == null || p.State != PlantedGrowth.PlantState.Alive) continue;
                string name = string.IsNullOrEmpty(p.Group.Name) ? p.Group.Id : p.Group.Name;
                if (!cropIndex.TryGetValue(name, out int idx))
                {
                    idx = c.Crops.Count;
                    cropIndex[name] = idx;
                    c.Crops.Add(new CropFact { Name = name });
                }
                CropFact f = c.Crops[idx];
                f.Count++;
                int finalStage = p.Group.Stages.Count > 0 ? p.Group.Stages[p.Group.Stages.Count - 1].Stage : int.MaxValue;
                if (p.CurrentStage != null && p.CurrentStage.Stage >= finalStage) f.Ready++;
                c.Crops[idx] = f;
            }
            c.Crops.Sort((a, b) => b.Count.CompareTo(a.Count));

            // Animals: every brain in the world grouped by species, named through the item catalog when it is an item.
            var animalIndex = new Dictionary<string, int>();
            foreach (AnimalBrain b in AnimalBrain.All)
            {
                if (b == null || string.IsNullOrEmpty(b.Species)) continue;
                string name = HudBindings.GetItemName(b.Species);
                if (string.IsNullOrEmpty(name) || name == b.Species) name = PrettyId(b.Species);
                if (!animalIndex.TryGetValue(name, out int idx))
                {
                    idx = c.Animals.Count;
                    animalIndex[name] = idx;
                    c.Animals.Add(new AnimalFact { Name = name });
                }
                AnimalFact f = c.Animals[idx];
                f.Count++;
                c.Animals[idx] = f;
            }
            c.Animals.Sort((a, b) => b.Count.CompareTo(a.Count));

            c.Money = HudState.Active.Money;
            c.LoanDebt = HudState.Active.LoanDebt;
            return c;
        }

        /// <summary>The HUD's trend label ("Daylight Increasing (towards Summer Solstice)") as a spoken sentence.</summary>
        private static string SpokenDaylightTrend(string label)
        {
            if (string.IsNullOrEmpty(label)) return "";
            string l = label.ToLowerInvariant();
            if (l.Contains("increas")) return "The days are getting longer towards the summer solstice.";
            if (l.Contains("decreas") || l.Contains("shorten")) return "The days are getting shorter towards the winter solstice.";
            if (l.Contains("solstice") || l.Contains("equinox")) return "";   // the almanac badge covers the day itself
            return "";
        }

        private static string PrettyId(string id)
        {
            string s = id;
            if (s.StartsWith("animal_")) s = s.Substring(7);
            s = s.Replace('_', ' ');
            return s;
        }

        // ------------------------------------------------------------------ formatting helpers (spoken text)

        /// <summary>A temperature as the player will hear it, in their unit setting: "12 degrees" or "minus 3 degrees".</summary>
        public string Temp(float celsius)
        {
            float v = Imperial ? celsius * 9f / 5f + 32f : celsius;
            int r = Mathf.RoundToInt(v);
            return (r < 0 ? "minus " + (-r) : r.ToString()) + " degrees";
        }

        public static string Clock(float minute)
        {
            int h = Mathf.FloorToInt(minute / 60f) % 24;
            int m = Mathf.FloorToInt(minute % 60f);
            string ampm = h >= 12 ? "PM" : "AM";   // no periods: a sentence-ending "p.m.." reads badly
            int h12 = h % 12; if (h12 == 0) h12 = 12;
            return m == 0 ? $"{h12} {ampm}" : $"{h12}:{m:00} {ampm}";
        }

        public static string Hours(float hours)
        {
            int h = Mathf.FloorToInt(hours);
            int m = Mathf.RoundToInt((hours - h) * 60f);
            if (m == 60) { h++; m = 0; }
            if (m == 0) return h == 1 ? "one hour" : $"{h} hours";
            return $"{h} hours and {m} minutes";
        }

        public static string Ordinal(int n)
        {
            int rem100 = n % 100;
            if (rem100 >= 11 && rem100 <= 13) return n + "th";
            switch (n % 10)
            {
                case 1: return n + "st";
                case 2: return n + "nd";
                case 3: return n + "rd";
                default: return n + "th";
            }
        }

        public static string MoneyText(float amount)
        {
            return "$" + Mathf.RoundToInt(amount).ToString("N0", CultureInfo.InvariantCulture);
        }

        public static string WeatherSpoken(HomesteaderWeather w)
        {
            switch (w)
            {
                case HomesteaderWeather.Sunny: return "clear skies";
                case HomesteaderWeather.PartlyCloudy: return "a mix of sun and cloud";
                case HomesteaderWeather.Cloudy: return "overcast skies";
                case HomesteaderWeather.Rain: return "rain";
                case HomesteaderWeather.Thunderstorm: return "thunderstorms";
                case HomesteaderWeather.Snow: return "snow";
                case HomesteaderWeather.Blizzard: return "blizzard conditions";
                case HomesteaderWeather.Wind: return "strong wind";
                case HomesteaderWeather.Fog: return "fog";
                default: return TimeSystem.GetWeatherName(w).ToLowerInvariant();
            }
        }

        public static bool IsWet(HomesteaderWeather w) =>
            w == HomesteaderWeather.Rain || w == HomesteaderWeather.Thunderstorm || w == HomesteaderWeather.Snow || w == HomesteaderWeather.Blizzard;

        public string PartOfDay
        {
            get
            {
                if (MinuteOfDay < 12 * 60) return "morning";
                if (MinuteOfDay < 17 * 60) return "afternoon";
                return "evening";
            }
        }

        // ------------------------------------------------------------------ fact sheet for the Claude writer

        /// <summary>Plain-text facts, one per line. This is everything the Claude script writer is allowed to know.</summary>
        public string ToFactSheet()
        {
            var sb = new StringBuilder();
            sb.AppendLine($"Date: {Weekday}, {MonthName} {DayOfMonth} (day {DayOfYear} of 336), {Season}.");
            sb.AppendLine($"Time of broadcast: {PartOfDay}.");
            sb.AppendLine($"Units: {(Imperial ? "Fahrenheit" : "Celsius")} (say temperatures as plain numbers of degrees).");
            if (Daily.Count > 0)
            {
                DailyForecast t = Daily[0];
                sb.AppendLine($"Today: {WeatherSpoken(t.PredictedWeather)}, high {Temp(t.HighTempC)}, low {Temp(t.LowTempC)}.");
                sb.AppendLine($"Sunrise {Clock(t.SunriseMinute)}, sunset {Clock(t.SunsetMinute)}, {Hours(t.DaylightHours)} of daylight. {DaylightTrend}");
                sb.AppendLine($"Moon: {MoonPhase}.");
                if (!string.IsNullOrEmpty(AstronomicalBadge)) sb.AppendLine($"Almanac event today: {AstronomicalBadge}.");
                sb.AppendLine("Forecast for the next 7 days (confidence falls further out):");
                for (int i = 1; i <= 7 && i < Daily.Count; i++)
                {
                    DailyForecast d = Daily[i];
                    sb.AppendLine($"  {d.DayOfWeekName}: {WeatherSpoken(d.PredictedWeather)}, high {Temp(d.HighTempC)}, low {Temp(d.LowTempC)}" + (d.LowTempC <= 0f ? " (frost)" : "") + ".");
                }
                int wet = 0, cold = 0;
                for (int i = 8; i <= 21 && i < Daily.Count; i++) { if (IsWet(Daily[i].PredictedWeather)) wet++; if (Daily[i].HighTempC < 5f) cold++; }
                sb.AppendLine($"Weeks two and three: {wet} wet days, {cold} cold days out of 14.");
            }
            if (Crops.Count == 0) sb.AppendLine("Farm: no crops planted.");
            else
            {
                sb.Append("Farm crops: ");
                for (int i = 0; i < Crops.Count && i < 6; i++)
                    sb.Append(i > 0 ? "; " : "").Append($"{Crops[i].Count} {Crops[i].Name}" + (Crops[i].Ready > 0 ? $" ({Crops[i].Ready} ready to harvest)" : ""));
                sb.AppendLine(".");
            }
            if (Animals.Count == 0) sb.AppendLine("Farm animals: none.");
            else
            {
                sb.Append("Farm animals: ");
                for (int i = 0; i < Animals.Count && i < 6; i++)
                    sb.Append(i > 0 ? "; " : "").Append($"{Animals[i].Count} {Animals[i].Name}");
                sb.AppendLine(".");
            }
            sb.AppendLine($"Money: {MoneyText(Money)}" + (LoanDebt > 0.5f ? $", loan outstanding {MoneyText(LoanDebt)}." : ", no loan."));
            return sb.ToString();
        }
    }
}
