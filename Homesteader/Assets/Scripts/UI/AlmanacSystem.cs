// AlmanacSystem.cs - Master astronomical and weather forecasting engine for Homesteader.
//
// Generates:
// 1. Ground-truth weather for any calendar day (336 days per year) using calibrated seasonal probabilities.
// 2. Rolling 32-week forecast (8 weeks daily = 56 days; 24 weeks weekly):
//    - Days 1..21 (Weeks 1..3): VERY accurate (95% confidence).
//    - Days 22..42 (Weeks 4..6): Moderate accuracy (70% confidence).
//    - Days 43..56 (Weeks 7..8): Lower accuracy (50% confidence).
//    - Weeks 9..32 (Weekly outlooks): Climatological / seasonal tendency (40% confidence).
// 3. Exact astronomical data: sunrise, sunset, daylight duration, solstices, equinoxes, and moon phases.

using System;
using System.Collections.Generic;
using UnityEngine;

namespace Homesteader.UI
{
    [Serializable]
    public struct DailyForecast
    {
        public int DayOfYear;
        public int Month;
        public string MonthName;
        public int DayOfMonth;
        public int DayOfWeek; // 1..7 (Monday..Sunday)
        public string DayOfWeekName;
        public int RelativeDayOffset; // 0 = Today, 1 = Tomorrow, etc.
        public HomesteaderSeason Season;

        // Astronomical metrics
        public float SunriseMinute;
        public float SunsetMinute;
        public float DaylightHours;
        public string MoonPhaseName;
        public string MoonIcon;
        public string AstronomicalBadge; // e.g. "★ Spring Equinox", "🌕 Full Moon", etc.

        // Weather forecast
        public HomesteaderWeather ActualWeather; // Ground truth
        public HomesteaderWeather PredictedWeather; // Visible forecast
        public string PredictedWeatherName;
        public string WeatherIconId;
        public int ConfidencePercent;
        public string ConfidenceTier; // "High Confidence", "Moderate Confidence", "Low Confidence"
        // Temperature (Celsius)
        public float HighTempC;   // Predicted daily high
        public float LowTempC;    // Predicted daily low
    }

    [Serializable]
    public struct WeeklyForecast
    {
        public int WeekIndex; // 1..24
        public int StartDayOfYear;
        public int EndDayOfYear;
        public string DateRangeText;
        public HomesteaderSeason Season;

        // Representative / Average Solar Metrics
        public float AvgSunriseMinute;
        public float AvgSunsetMinute;
        public float AvgDaylightHours;

        // Weather Outlook
        public HomesteaderWeather DominantWeather;
        public string DominantWeatherName;
        public string WeatherIconId;
        public int ConfidencePercent; // 40%
        public string SeasonalTrendNote;
        // Temperature (Celsius)
        public float AvgHighTempC;  // Average high across the week
        public float AvgLowTempC;   // Average low across the week
    }

    public sealed class AlmanacSystem
    {
        public const int DailyForecastCount = 56; // 8 weeks * 7 days
        public const int WeeklyForecastCount = 24; // 24 weeks
        public const int TotalWeeks = 32;

        private static AlmanacSystem s_instance;
        public static AlmanacSystem Instance => s_instance ?? (s_instance = new AlmanacSystem());

        private int _worldSeed = 4242;

        public int WorldSeed
        {
            get => _worldSeed;
            set => _worldSeed = value;
        }

        public AlmanacSystem(int seed = 4242)
        {
            _worldSeed = seed;
        }

        private static readonly string[] DayNames = new string[]
        {
            "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"
        };

        /// <summary>
        /// Deterministically generates the ground-truth actual weather for a given calendar day (1..336).
        /// Matches the official seasonal probability distribution:
        /// Winter: Snow (45%), Cloudy (20%), Wind (15%), Fog (10%), Sunny (10%)
        /// Spring: Rain (35%), Partly Cloudy (25%), Sunny (15%), Thunderstorm (10%), Wind (15%)
        /// Summer: Sunny (50%), Partly Cloudy (25%), Thunderstorm (13%), Wind (7%), Cloudy (5%)
        /// Autumn: Wind (30%), Rain (25%), Cloudy (20%), Fog (13%), Partly Cloudy (12%)
        /// </summary>
        public HomesteaderWeather GetActualWeather(int dayOfYear)
        {
            int normalizedDay = NormalizeDay(dayOfYear);
            HomesteaderSeason season = GetSeasonForDay(normalizedDay);

            // Deterministic hash based on world seed and normalized day
            int hash = Hash2D(_worldSeed, normalizedDay, 101);
            int roll = Mathf.Abs(hash % 100);

            switch (season)
            {
                case HomesteaderSeason.Winter:
                    if (roll < 32) return HomesteaderWeather.Snow;
                    if (roll < 45) return HomesteaderWeather.Blizzard; // Dynamic Blizzard events in Winter
                    if (roll < 65) return HomesteaderWeather.Cloudy;
                    if (roll < 80) return HomesteaderWeather.Wind;
                    if (roll < 90) return HomesteaderWeather.Fog;
                    return HomesteaderWeather.Sunny;

                case HomesteaderSeason.Spring:
                    if (roll < 35) return HomesteaderWeather.Rain;
                    if (roll < 60) return HomesteaderWeather.PartlyCloudy;
                    if (roll < 75) return HomesteaderWeather.Sunny;
                    if (roll < 85) return HomesteaderWeather.Thunderstorm;
                    return HomesteaderWeather.Wind;

                case HomesteaderSeason.Summer:
                    if (roll < 50) return HomesteaderWeather.Sunny;
                    if (roll < 75) return HomesteaderWeather.PartlyCloudy;
                    if (roll < 88) return HomesteaderWeather.Thunderstorm;
                    if (roll < 95) return HomesteaderWeather.Wind;
                    return HomesteaderWeather.Cloudy;

                case HomesteaderSeason.Autumn:
                default:
                    if (roll < 30) return HomesteaderWeather.Wind;
                    if (roll < 55) return HomesteaderWeather.Rain;
                    if (roll < 75) return HomesteaderWeather.Cloudy;
                    if (roll < 88) return HomesteaderWeather.Fog;
                    return HomesteaderWeather.PartlyCloudy;
            }
        }

        /// <summary>
        /// Computes the predicted weather for targetDay as observed on currentDay.
        /// Accuracy tiers:
        /// - delta &lt;= 0: 100% accurate (Ground truth)
        /// - 1 &lt;= delta &lt;= 21 (first 21 days): 95% accurate
        /// - 22 &lt;= delta &lt;= 42 (next 21 days): 70% accurate
        /// - 43 &lt;= delta &lt;= 56: 50% accurate
        /// - delta &gt; 56: 40% accurate
        /// </summary>
        public HomesteaderWeather GetPredictedWeather(int currentDay, int targetDay)
        {
            int delta = targetDay - currentDay;
            HomesteaderWeather actual = GetActualWeather(targetDay);

            if (delta <= 0) return actual;

            int accuracyThreshold;
            if (delta <= 21) accuracyThreshold = 95;
            else if (delta <= 42) accuracyThreshold = 70;
            else if (delta <= 56) accuracyThreshold = 50;
            else accuracyThreshold = 40;

            // Stable pseudo-random check based on current day observation and target day
            int hash = Hash3D(_worldSeed, currentDay, targetDay, 307);
            int roll = Mathf.Abs(hash % 100);

            if (roll < accuracyThreshold)
            {
                // Prediction matches actual
                return actual;
            }

            // Inaccurate prediction: roll an alternate plausible weather condition for that season
            int altRoll = Mathf.Abs(Hash3D(_worldSeed + 999, currentDay, targetDay, 401) % 100);
            HomesteaderSeason season = GetSeasonForDay(NormalizeDay(targetDay));
            return GetPlausibleAlternateWeather(actual, season, altRoll);
        }

        private static HomesteaderWeather GetPlausibleAlternateWeather(HomesteaderWeather actual, HomesteaderSeason season, int roll)
        {
            // Pick a weather condition different from actual
            HomesteaderWeather[] candidates;
            switch (season)
            {
                case HomesteaderSeason.Winter:
                    candidates = new[] { HomesteaderWeather.Cloudy, HomesteaderWeather.Wind, HomesteaderWeather.Fog, HomesteaderWeather.Sunny, HomesteaderWeather.Snow, HomesteaderWeather.Blizzard };
                    break;
                case HomesteaderSeason.Spring:
                    candidates = new[] { HomesteaderWeather.Rain, HomesteaderWeather.PartlyCloudy, HomesteaderWeather.Sunny, HomesteaderWeather.Thunderstorm, HomesteaderWeather.Wind };
                    break;
                case HomesteaderSeason.Summer:
                    candidates = new[] { HomesteaderWeather.Sunny, HomesteaderWeather.PartlyCloudy, HomesteaderWeather.Thunderstorm, HomesteaderWeather.Cloudy, HomesteaderWeather.Wind };
                    break;
                case HomesteaderSeason.Autumn:
                default:
                    candidates = new[] { HomesteaderWeather.Wind, HomesteaderWeather.Rain, HomesteaderWeather.Cloudy, HomesteaderWeather.Fog, HomesteaderWeather.PartlyCloudy };
                    break;
            }

            for (int i = 0; i < candidates.Length; i++)
            {
                int idx = (roll + i) % candidates.Length;
                if (candidates[idx] != actual) return candidates[idx];
            }
            return HomesteaderWeather.PartlyCloudy;
        }

        /// <summary>
        /// Generates the daily forecasts for the next 8 weeks (56 days) starting from currentDay.
        /// </summary>
        public List<DailyForecast> GetDailyForecasts(int currentDay)
        {
            var list = new List<DailyForecast>(DailyForecastCount);

            for (int offset = 0; offset < DailyForecastCount; offset++)
            {
                int targetDay = currentDay + offset;
                int normDay = NormalizeDay(targetDay);

                int monthIdx = (normDay - 1) / TimeConstants.DaysPerMonth; // 0..11
                int dayOfMonth = ((normDay - 1) % TimeConstants.DaysPerMonth) + 1;
                int dayOfWeekIdx = (normDay - 1) % TimeConstants.DaysPerWeek; // 0..6

                HomesteaderSeason season = GetSeasonForDay(normDay);
                HomesteaderWeather actual = GetActualWeather(targetDay);
                HomesteaderWeather predicted = GetPredictedWeather(currentDay, targetDay);

                int confidence;
                string confidenceTier;
                if (offset == 0) { confidence = 100; confidenceTier = "Current Condition"; }
                else if (offset <= 21) { confidence = 95; confidenceTier = "High Confidence"; }
                else if (offset <= 42) { confidence = 70; confidenceTier = "Moderate Confidence"; }
                else { confidence = 50; confidenceTier = "Low Confidence"; }

                // Moon phase
                int moonAge = ((normDay - 1) % 28) + 1;
                string moonName = GetMoonPhaseName(moonAge);
                string moonIcon = GetMoonPhaseIcon(moonAge);

                // Astronomical milestone tag
                string astroBadge = TimeSystem.GetAstronomicalEvent(normDay);
                if (string.IsNullOrEmpty(astroBadge))
                {
                    if (moonAge == 15) astroBadge = "🌕 Full Moon";
                    else if (moonAge == 1) astroBadge = "🌑 New Moon";
                }

                list.Add(new DailyForecast
                {
                    DayOfYear = normDay,
                    Month = monthIdx + 1,
                    MonthName = TimeConstants.MonthNames[monthIdx],
                    DayOfMonth = dayOfMonth,
                    DayOfWeek = dayOfWeekIdx + 1,
                    DayOfWeekName = DayNames[dayOfWeekIdx],
                    RelativeDayOffset = offset,
                    Season = season,
                    SunriseMinute = TimeSystem.GetSunriseMinute(normDay),
                    SunsetMinute = TimeSystem.GetSunsetMinute(normDay),
                    DaylightHours = TimeSystem.GetDaylightHours(normDay),
                    MoonPhaseName = moonName,
                    MoonIcon = moonIcon,
                    AstronomicalBadge = astroBadge,
                    ActualWeather = actual,
                    PredictedWeather = predicted,
                    PredictedWeatherName = TimeSystem.GetWeatherName(predicted),
                    WeatherIconId = GetWeatherIconId(predicted),
                    ConfidencePercent = confidence,
                    ConfidenceTier = confidenceTier,
                    HighTempC = TimeSystem.GetBaseTemperature(normDay) + TimeSystem.GetDiurnalOffset(870f) + TimeSystem.GetWeatherTemperatureOffset(predicted),
                    LowTempC = TimeSystem.GetBaseTemperature(normDay) + TimeSystem.GetDiurnalOffset(300f) + TimeSystem.GetWeatherTemperatureOffset(predicted),
                });
            }

            return list;
        }

        /// <summary>
        /// Generates the weekly forecasts for the following 24 weeks (Weeks 9..32) starting after the 8-week daily window.
        /// </summary>
        public List<WeeklyForecast> GetWeeklyForecasts(int currentDay)
        {
            var list = new List<WeeklyForecast>(WeeklyForecastCount);
            int startOffset = DailyForecastCount; // 56 days ahead

            for (int w = 0; w < WeeklyForecastCount; w++)
            {
                int weekStartDay = currentDay + startOffset + (w * 7);
                int weekEndDay = weekStartDay + 6;
                int midDay = weekStartDay + 3;
                int normMidDay = NormalizeDay(midDay);
                int normStart = NormalizeDay(weekStartDay);
                int normEnd = NormalizeDay(weekEndDay);

                HomesteaderSeason season = GetSeasonForDay(normMidDay);

                // Find dominant predicted weather across that week
                var counts = new Dictionary<HomesteaderWeather, int>();
                for (int d = weekStartDay; d <= weekEndDay; d++)
                {
                    HomesteaderWeather pw = GetPredictedWeather(currentDay, d);
                    counts[pw] = counts.ContainsKey(pw) ? counts[pw] + 1 : 1;
                }

                HomesteaderWeather dominant = HomesteaderWeather.Sunny;
                int maxCount = -1;
                foreach (var kvp in counts)
                {
                    if (kvp.Value > maxCount)
                    {
                        maxCount = kvp.Value;
                        dominant = kvp.Key;
                    }
                }

                int startMonthIdx = (normStart - 1) / TimeConstants.DaysPerMonth;
                int startDayOfMonth = ((normStart - 1) % TimeConstants.DaysPerMonth) + 1;
                int endMonthIdx = (normEnd - 1) / TimeConstants.DaysPerMonth;
                int endDayOfMonth = ((normEnd - 1) % TimeConstants.DaysPerMonth) + 1;

                string rangeText = (startMonthIdx == endMonthIdx)
                    ? $"{TimeConstants.MonthNames[startMonthIdx]} {startDayOfMonth}–{endDayOfMonth}"
                    : $"{TimeConstants.MonthNames[startMonthIdx]} {startDayOfMonth} – {TimeConstants.MonthNames[endMonthIdx]} {endDayOfMonth}";

                list.Add(new WeeklyForecast
                {
                    WeekIndex = w + 9, // Week 9..32
                    StartDayOfYear = normStart,
                    EndDayOfYear = normEnd,
                    DateRangeText = rangeText,
                    Season = season,
                    AvgSunriseMinute = TimeSystem.GetSunriseMinute(normMidDay),
                    AvgSunsetMinute = TimeSystem.GetSunsetMinute(normMidDay),
                    AvgDaylightHours = TimeSystem.GetDaylightHours(normMidDay),
                    DominantWeather = dominant,
                    DominantWeatherName = TimeSystem.GetWeatherName(dominant),
                    WeatherIconId = GetWeatherIconId(dominant),
                    ConfidencePercent = 40,
                    SeasonalTrendNote = GetSeasonalTrendNote(season, normMidDay, dominant),
                    AvgHighTempC = TimeSystem.GetBaseTemperature(normMidDay) + TimeSystem.GetDiurnalOffset(870f) + TimeSystem.GetWeatherTemperatureOffset(dominant),
                    AvgLowTempC = TimeSystem.GetBaseTemperature(normMidDay) + TimeSystem.GetDiurnalOffset(300f) + TimeSystem.GetWeatherTemperatureOffset(dominant),
                });
            }

            return list;
        }

        private static string GetSeasonalTrendNote(HomesteaderSeason season, int dayOfYear, HomesteaderWeather dominant)
        {
            if (dayOfYear >= 70 && dayOfYear <= 84) return "Spring thaw transition; daytime warming, ideal for cool-season planting.";
            if (dayOfYear >= 154 && dayOfYear <= 168) return "Solstice peak solar radiation; high soil evaporation, maintain irrigation.";
            if (dayOfYear >= 238 && dayOfYear <= 252) return "Autumnal equinox cooling; harvest window for major field crops.";
            if (dayOfYear >= 322 && dayOfYear <= 336) return "Deep winter freeze; lowest solar elevation, insulate livestock and pipes.";

            switch (season)
            {
                case HomesteaderSeason.Spring:
                    return (dominant == HomesteaderWeather.Rain || dominant == HomesteaderWeather.Thunderstorm)
                        ? "Frequent precipitation expected; monitor field drainage."
                        : "Mild growing conditions; optimal for early root vegetables.";
                case HomesteaderSeason.Summer:
                    return (dominant == HomesteaderWeather.Sunny)
                        ? "Clear skies and high solar yield; check water cistern levels."
                        : "Scattered convective storms; watch wind-sensitive structures.";
                case HomesteaderSeason.Autumn:
                    return (dominant == HomesteaderWeather.Wind)
                        ? "Brisk seasonal gusts; secure loose homestead equipment."
                        : "Crisp autumn weather; good foraging and firewood preparation.";
                case HomesteaderSeason.Winter:
                default:
                    return (dominant == HomesteaderWeather.Snow)
                        ? "Snow accumulation likely; ensure generator fuel reserves."
                        : "Sub-freezing temperatures; keep animal bedding dry.";
            }
        }

        public static int NormalizeDay(int day)
        {
            int d = (day - 1) % TimeConstants.DaysPerYear;
            if (d < 0) d += TimeConstants.DaysPerYear;
            return d + 1;
        }

        public static HomesteaderSeason GetSeasonForDay(int dayOfYear)
        {
            int d = NormalizeDay(dayOfYear);
            int seasonIdx = (d - 1) / TimeConstants.DaysPerSeason; // 0..3
            switch (seasonIdx)
            {
                case 0: return HomesteaderSeason.Winter;
                case 1: return HomesteaderSeason.Spring;
                case 2: return HomesteaderSeason.Summer;
                case 3: return HomesteaderSeason.Autumn;
                default: return HomesteaderSeason.Winter;
            }
        }

        public static string GetMoonPhaseName(int moonAge)
        {
            if (moonAge == 1) return "New Moon";
            if (moonAge >= 2 && moonAge <= 7) return "Waxing Crescent";
            if (moonAge == 8) return "First Quarter";
            if (moonAge >= 9 && moonAge <= 14) return "Waxing Gibbous";
            if (moonAge == 15) return "Full Moon";
            if (moonAge >= 16 && moonAge <= 21) return "Waning Gibbous";
            if (moonAge == 22) return "Last Quarter";
            return "Waning Crescent";
        }

        public static string GetMoonPhaseIcon(int moonAge)
        {
            if (moonAge == 1) return "🌑";
            if (moonAge >= 2 && moonAge <= 7) return "🌒";
            if (moonAge == 8) return "🌓";
            if (moonAge >= 9 && moonAge <= 14) return "🌔";
            if (moonAge == 15) return "🌕";
            if (moonAge >= 16 && moonAge <= 21) return "🌖";
            if (moonAge == 22) return "🌗";
            return "🌘";
        }

        public static string GetWeatherIconId(HomesteaderWeather w)
        {
            switch (w)
            {
                case HomesteaderWeather.Sunny: return "weather_sunny";
                case HomesteaderWeather.PartlyCloudy: return "weather_partly_cloudy";
                case HomesteaderWeather.Cloudy: return "weather_cloudy";
                case HomesteaderWeather.Rain: return "weather_rain";
                case HomesteaderWeather.Thunderstorm: return "weather_thunderstorm";
                case HomesteaderWeather.Snow: return "weather_snow";
                case HomesteaderWeather.Wind: return "weather_wind";
                case HomesteaderWeather.Fog: return "weather_fog";
                default: return "weather_sunny";
            }
        }

        private static int Hash2D(int seed, int x, int prime)
        {
            unchecked
            {
                int h = seed;
                h = (h * 397) ^ (x * prime);
                h ^= (h >> 13);
                h = (h * 571) ^ x;
                return h;
            }
        }

        private static int Hash3D(int seed, int x, int y, int prime)
        {
            unchecked
            {
                int h = seed;
                h = (h * 397) ^ (x * prime);
                h = (h * 701) ^ (y * 1013);
                h ^= (h >> 13);
                h = (h * 571) ^ (x + y);
                return h;
            }
        }
    }
}
