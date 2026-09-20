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
        Speed9X,
    }

    public enum HomesteaderSeason
    {
        Spring,
        Summer,
        Autumn,
        Winter,
    }

    [Serializable]
    public struct HudTimeState
    {
        public int DayOfYear;
        public float MinuteOfDay;
        public float CycleMinute;
        public HomesteaderPhase Phase;
        public HomesteaderSeason Season;
        public HomesteaderSpeed Speed;
    }

    public static class TimeConstants
    {
        public const int DaysPerSeason = 30;
        public const int DaysPerYear = DaysPerSeason * 4;
        public const int DayGameMinutes = 12 * 60;
        public const int NightGameMinutes = 12 * 60;
        public const int CycleGameMinutes = DayGameMinutes + NightGameMinutes;
        public const float RealSecondsPerGameMinuteAt1X = 1.0f;
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
            string suffix = isPm ? "PM" : "AM";
            return displayHour.ToString() + ":" + mins.ToString("00") + suffix;
        }
    }

    public class TimeSystem
    {
        private int _dayOfYear = 1;
        private float _minuteOfDay = 8f * 60f;
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

        public TimeSystem() { }

        public TimeSystem(int startDayOfYear, float startMinute,
                          HomesteaderSpeed speed)
        {
            _dayOfYear = startDayOfYear;
            _minuteOfDay = startMinute;
            _speed = speed;
        }

        public void SetSpeed(HomesteaderSpeed s)
        {
            _speed = s;
        }

        public float CycleMinute()
        {
            return Mathf.Repeat(_minuteOfDay, TimeConstants.CycleGameMinutes);
        }

        public HomesteaderPhase GetPhase()
        {
            return CycleMinute() < TimeConstants.DayGameMinutes
                ? HomesteaderPhase.Day
                : HomesteaderPhase.Night;
        }

        public string GetWallClock()
        {
            return WallClock.Format(CycleMinute());
        }

        public HomesteaderSeason GetSeason()
        {
            int dayInYearCycle = ((_dayOfYear - 1) % TimeConstants.DaysPerYear) + 1;
            int idx = (dayInYearCycle - 1) / TimeConstants.DaysPerSeason;
            if (idx > 3) idx = 3;
            if (idx < 0) idx = 0;
            return (HomesteaderSeason)idx;
        }

        public HudTimeState Snapshot()
        {
            return new HudTimeState
            {
                DayOfYear = _dayOfYear,
                MinuteOfDay = _minuteOfDay,
                CycleMinute = CycleMinute(),
                Phase = GetPhase(),
                Season = GetSeason(),
                Speed = _speed,
            };
        }

        public void Tick(float realDeltaSeconds)
        {
            if (realDeltaSeconds <= 0f) { return; }
            float multiplier = SpeedToMultiplier(_speed);
            if (multiplier == 0f) { return; }
            float added = realDeltaSeconds
                          * TimeConstants.RealSecondsPerGameMinuteAt1X
                          * multiplier;
            float newDatePct = _minuteOfDay + added;
            float minutesPerDay = TimeConstants.CycleGameMinutes;
            int dayDelta = Mathf.FloorToInt(newDatePct / minutesPerDay);
            float newMinuteOfDay = newDatePct - dayDelta * minutesPerDay;
            if (dayDelta > 0)
            {
                _dayOfYear += dayDelta;
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
                case HomesteaderSpeed.Speed9X: return 9f;
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
