// RadioScriptWriter.cs - the templated script writer: builds an episode for a station from the day's facts
// (RadioScriptContext) and the station's sentence banks. Deterministic for (world seed, day, station), free and
// offline. The Claude script writer (ClaudeScriptWriter.cs) is the optional alternative; this one is always the
// fallback when that fails.

using System;
using System.Collections.Generic;
using System.Text;
using System.Text.RegularExpressions;
using Homesteader.UI;

namespace Homesteader.Radio
{
    [Serializable]
    public sealed class RadioLine
    {
        public string speaker;   // RadioSpeaker.Id
        public string text;
    }

    [Serializable]
    public sealed class RadioEpisode
    {
        public string stationId;
        public int dayOfYear;
        public int worldSeed;
        public string title;
        public string source;    // "templated" or "claude"
        public List<RadioLine> lines = new List<RadioLine>();

        public string FullText()
        {
            var sb = new StringBuilder();
            foreach (RadioLine l in lines) sb.Append(l.speaker).Append(": ").AppendLine(l.text);
            return sb.ToString();
        }
    }

    public static class RadioScriptWriter
    {
        private static readonly Regex Placeholder = new Regex(@"\{([a-z_]+)\}", RegexOptions.Compiled);

        public static RadioEpisode Write(RadioStationDefinition station, RadioScriptContext ctx)
        {
            var ep = new RadioEpisode
            {
                stationId = station.Id,
                dayOfYear = ctx.DayOfYear,
                worldSeed = ctx.WorldSeed,
                title = $"{station.Name}: {ctx.Weekday}, {ctx.MonthName} {ctx.DayOfMonth}",
                source = "templated",
            };

            var rng = new System.Random(unchecked(ctx.WorldSeed * 397 + ctx.DayOfYear * 31 + station.Id.GetHashCode()));
            Dictionary<string, string> vars = BuildVariables(station, ctx, rng);

            foreach (string segment in station.Segments)
            {
                switch (segment)
                {
                    case "today":
                        Emit(ep, station, "today", vars, rng);
                        Emit(ep, station, "today_" + ctx.Today.PredictedWeather.ToString().ToLowerInvariant(), vars, rng, optional: true);
                        if (vars.ContainsKey("frost_day")) Emit(ep, station, "frost", vars, rng, optional: true);
                        break;
                    case "sky":
                        Emit(ep, station, "sky", vars, rng);
                        Emit(ep, station, "moon", vars, rng, optional: true);
                        if (!string.IsNullOrEmpty(ctx.AstronomicalBadge)) Emit(ep, station, "astro", vars, rng, optional: true);
                        break;
                    case "farm":
                        Emit(ep, station, ctx.Crops.Count > 0 ? "farm_crops" : "farm_no_crops", vars, rng, optional: true);
                        if (ctx.Animals.Count > 0) Emit(ep, station, "farm_animals", vars, rng, optional: true);
                        Emit(ep, station, "farm_money", vars, rng, optional: true);
                        break;
                    default:
                        Emit(ep, station, segment, vars, rng, optional: true);
                        break;
                }
            }
            return ep;
        }

        private static void Emit(RadioEpisode ep, RadioStationDefinition station, string bank, Dictionary<string, string> vars, System.Random rng, bool optional = false)
        {
            if (!station.Lines.TryGetValue(bank, out List<string> options) || options.Count == 0)
            {
                if (!optional) ep.lines.Add(new RadioLine { speaker = station.Speakers[0].Id, text = $"(missing line bank '{bank}')" });
                return;
            }
            string template = options[rng.Next(options.Count)];
            string text = Fill(template, vars);

            // "{host}: ..." names the speaker; anything else goes to the first speaker.
            string speaker = station.Speakers[0].Id;
            int colon = text.IndexOf(':');
            if (colon > 0 && colon < 24)
            {
                string tag = text.Substring(0, colon).Trim();
                RadioSpeaker s = station.FindSpeaker(tag);
                if (s != null && string.Equals(s.Id, tag, StringComparison.OrdinalIgnoreCase))
                {
                    speaker = s.Id;
                    text = text.Substring(colon + 1).Trim();
                }
            }
            text = Regex.Replace(text, @"\s{2,}", " ").Trim();
            if (text.Length == 0) return;
            ep.lines.Add(new RadioLine { speaker = speaker, text = text });
        }

        private static string Fill(string template, Dictionary<string, string> vars)
        {
            return Placeholder.Replace(template, m => vars.TryGetValue(m.Groups[1].Value, out string v) ? v : m.Value);
        }

        // ------------------------------------------------------------------ variables

        private static Dictionary<string, string> BuildVariables(RadioStationDefinition station, RadioScriptContext ctx, System.Random rng)
        {
            var v = new Dictionary<string, string>();
            foreach (RadioSpeaker s in station.Speakers)
            {
                v[s.Id] = s.Id;                 // "{host}" stays a speaker tag for Emit to strip
                v[s.Id + "_name"] = s.Name;
            }
            v["frequency"] = station.Frequency;
            v["station"] = station.Name;
            v["part_of_day"] = ctx.PartOfDay;
            v["weekday"] = ctx.Weekday ?? "";
            v["month"] = ctx.MonthName ?? "";
            v["day_of_month"] = ctx.DayOfMonth.ToString();
            v["ordinal_day"] = RadioScriptContext.Ordinal(ctx.DayOfMonth);
            v["day_of_year"] = ctx.DayOfYear.ToString();
            v["season"] = ctx.Season;
            v["season_phrase"] = station.Phrase("season_phrase", ctx.Season, ctx.Season.ToLowerInvariant());
            v["planting_hint"] = station.Phrase("planting_hint", ctx.Season, "");

            if (ctx.Daily.Count > 0)
            {
                DailyForecast t = ctx.Today;
                v["weather_now"] = TimeSystem.GetWeatherName(t.PredictedWeather);
                v["weather_now_lower"] = RadioScriptContext.WeatherSpoken(t.PredictedWeather);
                v["high_today"] = ctx.Temp(t.HighTempC);
                v["low_today"] = ctx.Temp(t.LowTempC);
                v["sunrise"] = RadioScriptContext.Clock(t.SunriseMinute);
                v["sunset"] = RadioScriptContext.Clock(t.SunsetMinute);
                v["daylight_hours"] = RadioScriptContext.Hours(t.DaylightHours);
                v["daylight_trend"] = ctx.DaylightTrend ?? "";
                v["moon_phrase"] = MoonPhrase(ctx.MoonPhase);
                v["astro_badge"] = ctx.AstronomicalBadge ?? "";

                // first frost in the coming week (not today)
                for (int i = 1; i <= 7 && i < ctx.Daily.Count; i++)
                {
                    if (ctx.Daily[i].LowTempC <= 0f && ctx.Today.LowTempC > 0f)
                    {
                        v["frost_day"] = i == 1 ? "tonight" : ctx.Daily[i].DayOfWeekName + " night";
                        v["frost_low"] = ctx.Temp(ctx.Daily[i].LowTempC);
                        break;
                    }
                }

                // three-day outlook: "Tuesday brings rain with a high of 12 degrees, Wednesday ..."
                var parts = new List<string>();
                for (int i = 1; i <= 3 && i < ctx.Daily.Count; i++)
                {
                    DailyForecast d = ctx.Daily[i];
                    string day = i == 1 ? "tomorrow" : d.DayOfWeekName;
                    parts.Add($"{day} {OutlookVerb(d.PredictedWeather, rng)} {RadioScriptContext.WeatherSpoken(d.PredictedWeather)} and a high of {ctx.Temp(d.HighTempC)}");
                }
                v["outlook_phrase"] = JoinSpoken(parts);

                // week ahead (days 1..7): dominant weather, average highs/lows, wet and cold counts
                var counts = new Dictionary<HomesteaderWeather, int>();
                float hi = 0f, lo = 0f; int n = 0, wet = 0, cold = 0;
                for (int i = 1; i <= 7 && i < ctx.Daily.Count; i++)
                {
                    DailyForecast d = ctx.Daily[i];
                    counts[d.PredictedWeather] = counts.TryGetValue(d.PredictedWeather, out int c) ? c + 1 : 1;
                    hi += d.HighTempC; lo += d.LowTempC; n++;
                    if (RadioScriptContext.IsWet(d.PredictedWeather)) wet++;
                    if (d.HighTempC < 5f) cold++;
                }
                HomesteaderWeather dominant = HomesteaderWeather.Sunny; int best = -1;
                foreach (var kv in counts) if (kv.Value > best) { best = kv.Value; dominant = kv.Key; }
                v["week_dominant"] = TimeSystem.GetWeatherName(dominant);
                v["week_dominant_lower"] = RadioScriptContext.WeatherSpoken(dominant);
                v["week_high"] = ctx.Temp(n > 0 ? hi / n : 0f);
                v["week_low"] = ctx.Temp(n > 0 ? lo / n : 0f);
                v["wet_days"] = wet.ToString();
                string noteBank = cold >= 5 ? "week_note_cold" : wet >= 3 ? "week_note_wet" : wet == 0 ? "week_note_dry" : null;
                v["week_note"] = noteBank != null && station.Lines.TryGetValue(noteBank, out var notes) && notes.Count > 0
                    ? Fill(notes[rng.Next(notes.Count)], v) : "";
            }

            // farm
            int cropCount = 0, ready = 0;
            foreach (var c in ctx.Crops) { cropCount += c.Count; ready += c.Ready; }
            v["crop_count"] = cropCount.ToString();
            v["crop_word"] = cropCount == 1 ? "plant" : "plants";
            v["crop_top"] = ctx.Crops.Count > 0 ? ctx.Crops[0].Name.ToLowerInvariant() : "";
            v["crop_nearest_phrase"] = ready > 0 ? (ready == 1 ? "One of them looks ready to harvest." : $"{ready} of them look ready to harvest.") : "";

            var animals = new List<string>();
            foreach (var a in ctx.Animals) animals.Add(CountNoun(a.Count, a.Name.ToLowerInvariant()));
            v["animal_phrase"] = JoinSpoken(animals);

            v["money"] = RadioScriptContext.MoneyText(ctx.Money);
            v["loan_phrase"] = ctx.LoanDebt > 0.5f ? $", with {RadioScriptContext.MoneyText(ctx.LoanDebt)} still owed on the loan" : " and no loan to speak of";
            return v;
        }

        private static string OutlookVerb(HomesteaderWeather w, System.Random rng)
        {
            string[] verbs = { "brings", "looks like", "gives us" };
            return verbs[rng.Next(verbs.Length)];
        }

        /// <summary>A noun phrase for the moon: "a full moon", "a new moon, so a dark night", "a waxing crescent moon".</summary>
        private static string MoonPhrase(string phase)
        {
            if (string.IsNullOrEmpty(phase)) return "a quiet sky";
            string p = phase.ToLowerInvariant().Replace(" moon", "").Trim();
            if (p.Contains("full")) return "a full moon";
            if (p.Contains("new")) return "a new moon, so a dark night";
            return (StartsWithVowel(p) ? "an " : "a ") + p + " moon";
        }

        public static string CountNoun(int count, string noun)
        {
            string word = count == 1 ? noun : Plural(noun);
            string num = count == 1 ? (StartsWithVowel(noun) ? "an" : "a") : count.ToString();
            return num + " " + word;
        }

        private static bool StartsWithVowel(string s) => s.Length > 0 && "aeiou".IndexOf(char.ToLowerInvariant(s[0])) >= 0;

        private static string Plural(string noun)
        {
            if (noun.EndsWith("sheep") || noun.EndsWith("deer") || noun.EndsWith("fish")) return noun;
            if (noun.EndsWith("s") || noun.EndsWith("x") || noun.EndsWith("ch") || noun.EndsWith("sh")) return noun + "es";
            if (noun.EndsWith("y") && noun.Length > 1 && "aeiou".IndexOf(noun[noun.Length - 2]) < 0) return noun.Substring(0, noun.Length - 1) + "ies";
            return noun + "s";
        }

        public static string JoinSpoken(List<string> parts)
        {
            if (parts.Count == 0) return "";
            if (parts.Count == 1) return parts[0];
            if (parts.Count == 2) return parts[0] + " and " + parts[1];
            return string.Join(", ", parts.GetRange(0, parts.Count - 1)) + ", and " + parts[parts.Count - 1];
        }
    }
}
