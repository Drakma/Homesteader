// TimeSystem.cs - the game clock for the Homesteader HUD.
//
// Ported from assets/hud_kit/runtime/time_system.py to C#. Shape:
//
//   var ts = new TimeSystem();
//   ts.SetSpeed(HomesteaderSpeed.Speed3X);
//   ts.Tick(Time.deltaTime);
//
// Math matches the Python source: DAYS_PER_SEASON=30, DAYS_PER_YEAR=120,
// real-time clock multiplier 1 real-second per game-minute at 1x,
// 12-hour DAY and NIGHT phases.

using System;
using UnityEngine;

namespace Homesteader.UI
{
    public enum HomesteaderPhase
    {
        Day,
        Night,
    }

    public enum HomesteaderSpeed
    {
        Pause,
        Speed1X,
        Speed3X,
        Speed5X,
        Speed10X,
        Speed9X = Speed10X,
    }

    public enum HomesteaderSeason
    {
        Spring,
        Summer,
        Autumn,
        Winter,
    }

    public enum HomesteaderWeather
    {
        Sunny,
        PartlyCloudy,
        Cloudy,
        Rain,
        Thunderstorm,
        Snow,
        Blizzard,
        Wind,
        Fog,
    }

    [Serializable]
    public struct HudTimeState
    {
        public int DayOfYear;
        public int Month;
        public string MonthName;
        public int DayOfMonth;
        public int WeekOfMonth;
        public float MinuteOfDay;
        public float CycleMinute;
        public HomesteaderPhase Phase;
        public HomesteaderSeason Season;
        public HomesteaderSpeed Speed;
        public string CelestialIconId;
        public float MoonIllumination;
        public HomesteaderWeather Weather;
        public string WeatherIconId;
        public float SunriseMinute;
        public float SunsetMinute;
        public float DaylightHours;
        public string AstronomicalMilestone;
        // Temperature
        public float TemperatureC;        // Live current temperature in Celsius
        public float TodayHighC;          // Estimated high for the day
        public float TodayLowC;           // Estimated low for the day
    }

    public static class TimeConstants
    {
        public const int DaysPerWeek = 7;
        public const int WeeksPerMonth = 4;
        public const int DaysPerMonth = DaysPerWeek * WeeksPerMonth; // 28
        public const int MonthsPerSeason = 3;
        public const int DaysPerSeason = DaysPerMonth * MonthsPerSeason; // 84
        public const int MonthsPerYear = 12;
        public const int DaysPerYear = DaysPerMonth * MonthsPerYear; // 336

        // Astronomical Equinoxes & Solstices (3rd week of Mar, Jun, Sep, Dec):
        // Spring Equinox: Month 3 (March), Week 3, Day 21 = Day 77 (Equal Day & Night: 12h / 12h)
        // Summer Solstice: Month 6 (June), Week 3, Day 21 = Day 161 (Longest Day: 15h day / 9h night)
        // Autumnal Equinox: Month 9 (September), Week 3, Day 21 = Day 245 (Equal Day & Night: 12h / 12h)
        // Winter Solstice: Month 12 (December), Week 3, Day 21 = Day 329 (Longest Night: 15h night / 9h day)
        public const int SpringEquinoxDay = 77;
        public const int SummerSolsticeDay = 161;
        public const int AutumnalEquinoxDay = 245;
        public const int WinterSolsticeDay = 329;

        public const float BaseDaylightHours = 12.0f; // 12 hours at equinox
        public const float MaxSeasonalDaylightDeltaHours = 3.0f; // ±3 hours (9h at winter solstice to 15h at summer solstice)

        // User requirement: Days are 1440 real seconds, Nights are 1440 real seconds nominal.
        public const float DayRealSeconds = 1440f;
        public const float NightRealSeconds = 1440f;
        public const float CycleRealSeconds = DayRealSeconds + NightRealSeconds; // 2880 real seconds

        // 24-hour game clock: 1440 game minutes per day cycle
        public const float DayGameMinutes = 12f * 60f; // Nominal 720 game minutes (12h)
        public const float NightGameMinutes = 12f * 60f; // Nominal 720 game minutes (12h)
        public const float CycleGameMinutes = 1440f; // 24h

        // Conversion: 720 game minutes / 1440 real seconds = 0.5 game minutes per real second at 1X.
        public const float RealSecondsPerGameMinuteAt1X = DayRealSeconds / DayGameMinutes; // 2.0s
        public const float GameMinutesPerRealSecondAt1X = 1f / RealSecondsPerGameMinuteAt1X; // 0.5

        // Nominal equinox thresholds (06:00 to 18:00)
        public const float SunriseMinute = 6f * 60f; // 360m = 06:00
        public const float NoonThresholdMinute = 10f * 60f; // 600m = 10:00
        public const float AfternoonThresholdMinute = 14f * 60f; // 840m = 14:00 (2:00 PM)
        public const float SunsetMinute = 18f * 60f; // 1080m = 18:00 (6:00 PM)

        public static readonly string[] MonthNames = new string[]
        {
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        };
    }

    public static class WallClock
    {
        public static string Format(float cycleMinute)
        {
            float cm = Mathf.Repeat(cycleMinute, TimeConstants.CycleGameMinutes);
            bool isPm = cm >= TimeConstants.DayGameMinutes;
            float minuteIntoHalf = isPm ? cm - TimeConstants.DayGameMinutes : cm;
            int hour12 = Mathf.FloorToInt(minuteIntoHalf / 60f);
            int mins = Mathf.FloorToInt(minuteIntoHalf % 60f);
            int displayHour = (hour12 == 0) ? 12 : hour12;
            return displayHour.ToString() + ":" + mins.ToString("00");
        }

        public static string FormatWithAmPm(float cycleMinute)
        {
            float cm = Mathf.Repeat(cycleMinute, TimeConstants.CycleGameMinutes);
            bool isPm = cm >= TimeConstants.DayGameMinutes;
            float minuteIntoHalf = isPm ? cm - TimeConstants.DayGameMinutes : cm;
            int hour12 = Mathf.FloorToInt(minuteIntoHalf / 60f);
            int mins = Mathf.FloorToInt(minuteIntoHalf % 60f);
            int displayHour = (hour12 == 0) ? 12 : hour12;
            string suffix = isPm ? "PM" : "AM";
            return displayHour.ToString() + ":" + mins.ToString("00") + " " + suffix;
        }
    }

    public class TimeSystem
    {
        private int _dayOfYear = 141; // Jun 1 - start the game in Summer
        private float _minuteOfDay = 8f * 60f; // Start at 08:00 AM
        private HomesteaderSpeed _speed = HomesteaderSpeed.Speed1X;
        private long _tickCount = 0;

        public HomesteaderSpeed CurrentSpeed
        {
            get { return _speed; }
        }

        public long TickCount
        {
            get { return _tickCount; }
        }

        public int DayOfYear => _dayOfYear;
        public float MinuteOfDay => _minuteOfDay;

        public bool IsPaused => _speed == HomesteaderSpeed.Pause;
        public event Action<bool> OnPauseChanged;

        public TimeSystem()
        {
            UpdateProceduralWeather();
            Time.timeScale = (_speed == HomesteaderSpeed.Pause) ? 0f : 1f;
        }

        public TimeSystem(int startDayOfYear, float startMinute,
                          HomesteaderSpeed speed)
        {
            _dayOfYear = startDayOfYear;
            _minuteOfDay = startMinute;
            _speed = speed;
            UpdateProceduralWeather();
            Time.timeScale = (_speed == HomesteaderSpeed.Pause) ? 0f : 1f;
        }

        public void SetSpeed(HomesteaderSpeed s)
        {
            bool wasPaused = (_speed == HomesteaderSpeed.Pause);
            _speed = s;
            bool isPaused = (s == HomesteaderSpeed.Pause);
            Time.timeScale = isPaused ? 0f : 1f;

            if (wasPaused != isPaused)
            {
                OnPauseChanged?.Invoke(isPaused);
            }
        }

        public void SetDayOfYear(int day)
        {
            _dayOfYear = Mathf.Max(1, day);
            UpdateProceduralWeather();
        }

        public void SetMinuteOfDay(float minute)
        {
            _minuteOfDay = Mathf.Repeat(minute, TimeConstants.CycleGameMinutes);
        }

        /// <summary>
        /// Resets the clock to the default New Game starting point:
        /// Day 141 (June 1, Summer), 08:00 AM, speed 1x.
        /// </summary>
        public void ResetToNewGameDefaults()
        {
            _dayOfYear = 141;            // Jun 1 — start in Summer
            _minuteOfDay = 8f * 60f;     // 08:00 AM
            _speed = HomesteaderSpeed.Speed1X;
            _tickCount = 0;
            UpdateProceduralWeather();
            Time.timeScale = 1f;
            OnPauseChanged?.Invoke(false);
        }

        public void SetSeason(HomesteaderSeason season)
        {
            int year = (_dayOfYear - 1) / TimeConstants.DaysPerYear;
            int baseDay = year * TimeConstants.DaysPerYear;
            switch (season)
            {
                case HomesteaderSeason.Winter:
                    _dayOfYear = baseDay + 1; // Month 1 (Jan 1)
                    break;
                case HomesteaderSeason.Spring:
                    _dayOfYear = baseDay + (2 * TimeConstants.DaysPerMonth) + 1; // Month 3 (Mar 1, Day 57)
                    break;
                case HomesteaderSeason.Summer:
                    _dayOfYear = baseDay + (5 * TimeConstants.DaysPerMonth) + 1; // Month 6 (Jun 1, Day 141)
                    break;
                case HomesteaderSeason.Autumn:
                default:
                    _dayOfYear = baseDay + (8 * TimeConstants.DaysPerMonth) + 1; // Month 9 (Sep 1, Day 225)
                    break;
            }
            UpdateProceduralWeather();
        }

        public void SetTimePreset(float hour)
        {
            SetMinuteOfDay(hour * 60f);
        }

        public float CycleMinute()
        {
            return Mathf.Repeat(_minuteOfDay, TimeConstants.CycleGameMinutes);
        }

        /// <summary>
        /// Calculates total daylight hours for a given day of the year (Day 1..336):
        /// - Spring Equinox (Day 77, 3rd week of March): 12.0 hours (equal day and night: 12h / 12h)
        /// - Summer Solstice (Day 161, 3rd week of June): 15.0 hours (longest daylight of the year)
        /// - Autumnal Equinox (Day 245, 3rd week of September): 12.0 hours (equal day and night: 12h / 12h)
        /// - Winter Solstice (Day 329, 3rd week of December): 9.0 hours (longest night of the year)
        /// Daylight increases from Winter Solstice until Summer Solstice, then declines until Winter Solstice.
        /// </summary>
        public static float GetDaylightHours(int dayOfYear)
        {
            float phase = ((dayOfYear - TimeConstants.SpringEquinoxDay) / (float)TimeConstants.DaysPerYear) * (Mathf.PI * 2f);
            return TimeConstants.BaseDaylightHours + TimeConstants.MaxSeasonalDaylightDeltaHours * Mathf.Sin(phase);
        }

        public static float GetDaylightMinutes(int dayOfYear) => GetDaylightHours(dayOfYear) * 60f;

        public static float GetSunriseMinute(int dayOfYear)
        {
            float halfDay = GetDaylightMinutes(dayOfYear) * 0.5f;
            return 720f - halfDay; // Solar noon is always at 12:00 PM (720m)
        }

        public static float GetSunsetMinute(int dayOfYear)
        {
            float halfDay = GetDaylightMinutes(dayOfYear) * 0.5f;
            return 720f + halfDay; // Solar noon is always at 12:00 PM (720m)
        }

        public float GetDaylightHours() => GetDaylightHours(_dayOfYear);
        public float GetDaylightMinutes() => GetDaylightMinutes(_dayOfYear);
        public float GetSunriseMinute() => GetSunriseMinute(_dayOfYear);
        public float GetSunsetMinute() => GetSunsetMinute(_dayOfYear);

        /// <summary>
        /// Returns the name of the astronomical event if the given day falls within the 3rd week of Mar, Jun, Sep, Dec.
        /// </summary>
        public static string GetAstronomicalEvent(int dayOfYear)
        {
            int dayInYear = ((dayOfYear - 1) % TimeConstants.DaysPerYear) + 1;
            if (dayInYear >= 71 && dayInYear <= 77)
                return "Spring Equinox (Equal Day & Night)";
            if (dayInYear >= 155 && dayInYear <= 161)
                return "Summer Solstice (Longest Day)";
            if (dayInYear >= 239 && dayInYear <= 245)
                return "Autumnal Equinox (Equal Day & Night)";
            if (dayInYear >= 323 && dayInYear <= 329)
                return "Winter Solstice (Longest Night)";
            return null;
        }

        /// <summary>
        /// Returns whether daylight hours are currently increasing towards Summer Solstice or decreasing towards Winter Solstice.
        /// </summary>
        public static string GetDaylightTrend(int dayOfYear)
        {
            int dayInYear = ((dayOfYear - 1) % TimeConstants.DaysPerYear) + 1;
            bool isIncreasing = (dayInYear > TimeConstants.WinterSolsticeDay || dayInYear <= TimeConstants.SummerSolsticeDay);
            return isIncreasing
                ? "Daylight Increasing (towards Summer Solstice)"
                : "Daylight Decreasing (towards Winter Solstice)";
        }

        public HomesteaderPhase GetPhase()
        {
            float cm = CycleMinute();
            float sr = GetSunriseMinute();
            float ss = GetSunsetMinute();
            return (cm >= sr && cm < ss)
                ? HomesteaderPhase.Day
                : HomesteaderPhase.Night;
        }

        /// <summary>
        /// Normalized daylight factor (0.0 at night/horizon to 1.0 at solar noon).
        /// </summary>
        public float GetDaylightFactor()
        {
            float cm = CycleMinute();
            float sr = GetSunriseMinute();
            float ss = GetSunsetMinute();
            if (cm < sr || cm >= ss)
                return 0f;
            float dayProgress = (cm - sr) / (ss - sr);
            return Mathf.Sin(dayProgress * Mathf.PI);
        }

        /// <summary>
        /// Calculates the peak midday solar elevation angle (degrees above horizon)
        /// based on the season and day of the year (Day 1..336).
        /// Summer Solstice peaks at ~76° (June 21), Winter Solstice bottoms at ~30° (December 21), Equinoxes at ~53°.
        /// </summary>
        public static float GetMaxSolarElevation(int dayOfYear)
        {
            float phase = ((dayOfYear - TimeConstants.SpringEquinoxDay) / (float)TimeConstants.DaysPerYear) * (Mathf.PI * 2f);
            return 53f + 23f * Mathf.Sin(phase);
        }

        public string GetWallClock()
        {
            return WallClock.Format(CycleMinute());
        }

        public int GetMonth()
        {
            int dayInYear = ((_dayOfYear - 1) % TimeConstants.DaysPerYear) + 1;
            return ((dayInYear - 1) / TimeConstants.DaysPerMonth) + 1; // 1..12
        }

        public string GetMonthName()
        {
            int m = GetMonth();
            return TimeConstants.MonthNames[m - 1];
        }

        public int GetDayOfMonth()
        {
            int dayInYear = ((_dayOfYear - 1) % TimeConstants.DaysPerYear) + 1;
            return ((dayInYear - 1) % TimeConstants.DaysPerMonth) + 1; // 1..28
        }

        public int GetWeekOfMonth()
        {
            int dom = GetDayOfMonth();
            return Mathf.Clamp(((dom - 1) / TimeConstants.DaysPerWeek) + 1, 1, 4); // 1..4
        }

        /// <summary>
        /// Seasons are 3 months long:
        /// Winter: December (12), January (1), February (2)
        /// Spring: March (3), April (4), May (5)
        /// Summer: June (6), July (7), August (8)
        /// Autumn: September (9), October (10), November (11)
        /// </summary>
        public HomesteaderSeason GetSeason()
        {
            int m = GetMonth();
            switch (m)
            {
                case 12:
                case 1:
                case 2:
                    return HomesteaderSeason.Winter;
                case 3:
                case 4:
                case 5:
                    return HomesteaderSeason.Spring;
                case 6:
                case 7:
                case 8:
                    return HomesteaderSeason.Summer;
                case 9:
                case 10:
                case 11:
                default:
                    return HomesteaderSeason.Autumn;
            }
        }

        /// <summary>
        /// Returns the celestial icon ID for the current time of day:
        /// Morning sun (first third of daylight)
        /// Noon sun (middle third of daylight around high noon)
        /// Sunset sun (final third of daylight until sunset)
        /// Night: 4 moon phases mapped to the 4 weeks of the month.
        /// </summary>
        /// <summary>
        /// Returns the celestial icon ID for a specific minute of the day.
        /// Morning sun (first third of daylight)
        /// Noon sun (middle third of daylight around high noon)
        /// Sunset sun (final third of daylight until sunset)
        /// Night: 4 moon phases mapped to the 4 weeks of the month.
        /// </summary>
        public string GetCelestialIconId(float minuteOfDay)
        {
            float cm = Mathf.Repeat(minuteOfDay, (float)TimeConstants.CycleGameMinutes);
            float sr = GetSunriseMinute();
            float ss = GetSunsetMinute();

            if (cm >= sr && cm < ss)
            {
                float dayDuration = ss - sr;
                float t = (cm - sr) / dayDuration;
                if (t < 0.33f)
                {
                    return "morning_sun";
                }
                if (t < 0.67f)
                {
                    return "noon_sun";
                }
                return "sunset_sun";
            }

            switch (GetWeekOfMonth())
            {
                case 1: return "new_moon";
                case 2: return "first_quarter_moon";
                case 3: return "full_moon";
                case 4: return "last_quarter_moon";
                default: return "full_moon";
            }
        }

        public string GetCelestialIconId()
        {
            return GetCelestialIconId(CycleMinute());
        }

        /// <summary>
        /// Returns the fractional illumination of the moon (0.0 at New Moon to 1.0 at Full Moon)
        /// based on the 28-day lunar cycle.
        /// Day 1 = New Moon (0.0), Day 8 = First Quarter (0.5), Day 15 = Full Moon (1.0), Day 22 = Last Quarter (0.5).
        /// </summary>
        public float GetMoonIllumination()
        {
            int dom = GetDayOfMonth();
            float phaseAngle = ((dom - 1f) / (float)TimeConstants.DaysPerMonth) * (Mathf.PI * 2f);
            return (1f - Mathf.Cos(phaseAngle)) * 0.5f;
        }

        /// <summary>
        /// Returns the brightness multiplier for the nighttime moon (minFloor .. 1.0).
        /// Default minFloor is 0.05f so New Moon still retains subtle ambient starlight visibility.
        /// </summary>
        public float GetMoonPhaseBrightness(float minFloor = 0.05f)
        {
            return Mathf.Lerp(minFloor, 1f, GetMoonIllumination());
        }

        private HomesteaderWeather _weather = HomesteaderWeather.Sunny;
        private bool _weatherOverridden = false;

        public HomesteaderWeather Weather => _weather;
        public bool IsWeatherOverridden => _weatherOverridden;

        public void SetWeather(HomesteaderWeather weather, bool userOverride = true)
        {
            _weather = weather;
            _weatherOverridden = userOverride;
        }

        public void ResetWeatherToAuto()
        {
            _weatherOverridden = false;
            UpdateProceduralWeather();
        }

        public string GetWeatherIconId()
        {
            return GetWeatherIconId(_weather);
        }

        public static string GetWeatherIconId(HomesteaderWeather weather)
        {
            switch (weather)
            {
                case HomesteaderWeather.Sunny: return "weather_sunny";
                case HomesteaderWeather.PartlyCloudy: return "weather_partly_cloudy";
                case HomesteaderWeather.Cloudy: return "weather_cloudy";
                case HomesteaderWeather.Rain: return "weather_rain";
                case HomesteaderWeather.Thunderstorm: return "weather_thunderstorm";
                case HomesteaderWeather.Snow: return "weather_snow";
                case HomesteaderWeather.Blizzard: return "weather_blizzard";
                case HomesteaderWeather.Wind: return "weather_wind";
                case HomesteaderWeather.Fog: return "weather_fog";
                default: return "weather_sunny";
            }
        }

        public static string GetWeatherName(HomesteaderWeather weather)
        {
            switch (weather)
            {
                case HomesteaderWeather.Sunny: return "Sunny";
                case HomesteaderWeather.PartlyCloudy: return "Partly Cloudy";
                case HomesteaderWeather.Cloudy: return "Cloudy";
                case HomesteaderWeather.Rain: return "Rain";
                case HomesteaderWeather.Thunderstorm: return "Thunderstorm";
                case HomesteaderWeather.Snow: return "Snow";
                case HomesteaderWeather.Blizzard: return "Blizzard";
                case HomesteaderWeather.Wind: return "Windy";
                case HomesteaderWeather.Fog: return "Fog";
                default: return "Sunny";
            }
        }

        public void UpdateProceduralWeather()
        {
            if (_weatherOverridden) return;
            _weather = AlmanacSystem.Instance.GetActualWeather(_dayOfYear);
        }

        // ── Temperature Simulation ──────────────────────────────────────────
        // Seasonal baseline: sinusoidal curve peaking at Summer Solstice (Day 161).
        // Annual range: 0 °C (mid-winter, Day 329) to 28 °C (mid-summer, Day 161).
        // Diurnal curve: min at ~5 AM (-4.5 °C offset), max at ~2:30 PM (+5.5 °C offset).
        // Weather offsets applied on top.

        /// <summary>
        /// Returns the seasonal base temperature in Celsius for a given day of year.
        /// Min ≈ 0 °C at Winter Solstice (Day 329), Max ≈ 28 °C at Summer Solstice (Day 161).
        /// </summary>
        public static float GetBaseTemperature(int dayOfYear)
        {
            // Phase aligned so peak (Day 161) maps to sin=1
            float theta = (2f * Mathf.PI * (dayOfYear - TimeConstants.SpringEquinoxDay)) / TimeConstants.DaysPerYear;
            // Mid-point 14 °C, amplitude 14 °C → range [0, 28] °C
            return 14f + 14f * Mathf.Sin(theta);
        }

        /// <summary>
        /// Returns the diurnal temperature offset in Celsius for a given cycle minute.
        /// Pre-dawn minimum (~5 AM = 300 min): –4.5 °C offset.
        /// Mid-afternoon maximum (~2:30 PM = 870 min): +5.5 °C offset.
        /// </summary>
        public static float GetDiurnalOffset(float cycleMinute)
        {
            // Peak at 870 min (2:30 PM), trough at 300 min (5:00 AM)
            // Map to a sinusoidal with period 1440 min
            const float peakMinute = 870f;
            const float amplitude = 5f;
            float phase = (cycleMinute - peakMinute) * (2f * Mathf.PI / 1440f);
            return amplitude * Mathf.Cos(phase);
        }

        /// <summary>
        /// Weather-based temperature correction in Celsius.
        /// </summary>
        public static float GetWeatherTemperatureOffset(HomesteaderWeather weather)
        {
            switch (weather)
            {
                case HomesteaderWeather.Sunny: return +3.0f;
                case HomesteaderWeather.PartlyCloudy: return +1.0f;
                case HomesteaderWeather.Cloudy: return -1.5f;
                case HomesteaderWeather.Rain: return -3.0f;
                case HomesteaderWeather.Thunderstorm: return -4.0f;
                case HomesteaderWeather.Snow: return -8.0f;  // Clamps to sub-zero
                case HomesteaderWeather.Blizzard: return -12.0f; // Extreme sub-zero blizzard cold
                case HomesteaderWeather.Wind: return -2.0f;
                case HomesteaderWeather.Fog: return -1.0f;
                default: return 0.0f;
            }
        }

        /// <summary>
        /// Returns the current live temperature in Celsius.
        /// </summary>
        public static float GetCurrentTemperature(int dayOfYear, float cycleMinute, HomesteaderWeather weather)
        {
            float temp = GetBaseTemperature(dayOfYear)
                       + GetDiurnalOffset(cycleMinute)
                       + GetWeatherTemperatureOffset(weather);
            // Snow & Blizzard always sub-freezing
            if (weather == HomesteaderWeather.Snow)
                temp = Mathf.Min(temp, -0.5f);
            else if (weather == HomesteaderWeather.Blizzard)
                temp = Mathf.Min(temp, -5.0f);
            return temp;
        }

        /// <summary>
        /// Returns the estimated daily High and Low temperatures in Celsius.
        /// High ≈ base + peak diurnal + weather. Low ≈ base + trough diurnal + weather.
        /// </summary>
        public static void GetDayHighLow(int dayOfYear, HomesteaderWeather weather,
                                         out float highC, out float lowC)
        {
            float wOffset = GetWeatherTemperatureOffset(weather);
            float baseTemp = GetBaseTemperature(dayOfYear);
            highC = baseTemp + GetDiurnalOffset(870f) + wOffset; // 2:30 PM
            lowC = baseTemp + GetDiurnalOffset(300f) + wOffset; // 5:00 AM
            if (weather == HomesteaderWeather.Snow)
            {
                highC = Mathf.Min(highC, -0.5f);
                lowC = Mathf.Min(lowC, -0.5f);
            }
            else if (weather == HomesteaderWeather.Blizzard)
            {
                highC = Mathf.Min(highC, -4.0f);
                lowC = Mathf.Min(lowC, -8.0f);
            }
        }

        /// <summary>
        /// Converts Celsius to Fahrenheit.
        /// </summary>
        public static float CelsiusToFahrenheit(float c) => c * 9f / 5f + 32f;

        /// <summary>
        /// Formats a temperature for display in the active unit system with superscript unit indicator.
        /// Uses Rich Text markup &lt;size=75%&gt;F&lt;/size&gt; or standard °F / °C so fonts that lack phonetic
        /// extensions do not substitute characters.
        /// </summary>
        public static string FormatTemperature(float tempC, Homesteader.UI.UnitSystem units)
        {
            if (units == Homesteader.UI.UnitSystem.Imperial)
                return $"{Mathf.RoundToInt(CelsiusToFahrenheit(tempC))}°<size=75%>F</size>";
            return $"{Mathf.RoundToInt(tempC)}°<size=75%>C</size>";
        }

        /// <summary>
        /// Formats a Hi/Lo temperature pair for display.
        /// Returns e.g. "H: 82° / L: 56°"
        /// </summary>
        public static string FormatHighLow(float highC, float lowC, Homesteader.UI.UnitSystem units)
        {
            return $"H: {FormatTemperature(highC, units)} / L: {FormatTemperature(lowC, units)}";
        }
        // ───────────────────────────────────────────────────────────────────

        public HudTimeState Snapshot()
        {
            float cycleMin = CycleMinute();
            GetDayHighLow(_dayOfYear, _weather, out float highC, out float lowC);
            return new HudTimeState
            {
                DayOfYear = _dayOfYear,
                Month = GetMonth(),
                MonthName = GetMonthName(),
                DayOfMonth = GetDayOfMonth(),
                WeekOfMonth = GetWeekOfMonth(),
                MinuteOfDay = _minuteOfDay,
                CycleMinute = cycleMin,
                Phase = GetPhase(),
                Season = GetSeason(),
                Speed = _speed,
                CelestialIconId = GetCelestialIconId(),
                MoonIllumination = GetMoonIllumination(),
                Weather = _weather,
                WeatherIconId = GetWeatherIconId(),
                SunriseMinute = GetSunriseMinute(),
                SunsetMinute = GetSunsetMinute(),
                DaylightHours = GetDaylightHours(),
                AstronomicalMilestone = GetAstronomicalEvent(_dayOfYear),
                TemperatureC = GetCurrentTemperature(_dayOfYear, cycleMin, _weather),
                TodayHighC = highC,
                TodayLowC = lowC,
            };
        }

        public void Tick(float realDeltaSeconds)
        {
            if (realDeltaSeconds <= 0f) { return; }
            float multiplier = SpeedToMultiplier(_speed);
            if (multiplier == 0f) { return; }
            float added = realDeltaSeconds
                          * TimeConstants.GameMinutesPerRealSecondAt1X
                          * multiplier;
            float newDatePct = _minuteOfDay + added;
            float minutesPerDay = TimeConstants.CycleGameMinutes;
            int dayDelta = Mathf.FloorToInt(newDatePct / minutesPerDay);
            float newMinuteOfDay = newDatePct - dayDelta * minutesPerDay;
            if (dayDelta > 0)
            {
                _dayOfYear += dayDelta;
                UpdateProceduralWeather();
            }
            _minuteOfDay = newMinuteOfDay;
            _tickCount += 1;
        }

        public static float SpeedToMultiplier(HomesteaderSpeed s)
        {
            switch (s)
            {
                case HomesteaderSpeed.Pause: return 0f;
                case HomesteaderSpeed.Speed1X: return 1f;
                case HomesteaderSpeed.Speed3X: return 3f;
                case HomesteaderSpeed.Speed5X: return 5f;
                case HomesteaderSpeed.Speed10X: return 10f;
                default: return 1f;
            }
        }

        private static TimeSystem s_instance;

        public static TimeSystem Instance
        {
            get
            {
                if (s_instance == null) s_instance = new TimeSystem();
                return s_instance;
            }
        }
    }
}
