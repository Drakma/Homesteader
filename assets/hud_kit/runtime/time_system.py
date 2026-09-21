"""time_system.py - the game clock for the Homesteader HUD.

A 24-hour (real-time at speed=1) full day cycle:
  - 12 hours DAY phase (midnight -> noon)
  - 12 hours NIGHT phase (noon -> midnight)

The cycle repeats indefinitely. Day-of-year increments after each
completed cycle. Calendar rolls year on day >= 365.

Speed multipliers:
  - PAUSE: tick(delta) does nothing
  - 1x, 3x, 5x: game minutes advance proportionally to delta seconds
"""

import enum
import math
from dataclasses import dataclass, field


class Phase(enum.Enum):
    DAY = "day"
    NIGHT = "night"


class Speed(enum.Enum):
    PAUSE = "pause"
    SPEED_1X = "1x"
    SPEED_3X = "3x"
    SPEED_5X = "5x"
    SPEED_9X = "9x"


class Season(enum.Enum):
    SPRING = "Spring"
    SUMMER = "Summer"
    AUTUMN = "Autumn"
    WINTER = "Winter"


# Per-season slice of the year. 28-day months, 4 weeks/month, 3 months/season = 84 days.
DAYS_PER_WEEK = 7
WEEKS_PER_MONTH = 4
DAYS_PER_MONTH = DAYS_PER_WEEK * WEEKS_PER_MONTH  # 28
MONTHS_PER_SEASON = 3
DAYS_PER_SEASON = DAYS_PER_MONTH * MONTHS_PER_SEASON  # 84
MONTHS_PER_YEAR = 12
DAYS_PER_YEAR = DAYS_PER_MONTH * MONTHS_PER_YEAR  # 336

MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

# Real-time clock constants.
REAL_SECONDS_PER_GAME_MINUTE_AT_1X = 1.0     # 1 real second = 1 game minute at 1x

# 12-hour phases. DAY = 06:00 -> 18:00. NIGHT = 18:00 -> 06:00.
DAY_GAME_MINUTES = 12 * 60       # 720
NIGHT_GAME_MINUTES = 12 * 60     # 720
CYCLE_GAME_MINUTES = DAY_GAME_MINUTES + NIGHT_GAME_MINUTES  # 1440 = 24h

SUNRISE_MINUTE = 6 * 60          # 360 = 06:00
NOON_THRESHOLD = 10 * 60         # 600 = 10:00
AFTERNOON_THRESHOLD = 14 * 60    # 840 = 14:00
SUNSET_MINUTE = 18 * 60          # 1080 = 18:00


def format_wall_clock(cycle_minute: float) -> str:
    cm = cycle_minute % CYCLE_GAME_MINUTES
    is_pm = cm >= DAY_GAME_MINUTES
    minute_into_half = cm - DAY_GAME_MINUTES if is_pm else cm
    hour_12 = int(minute_into_half // 60)
    mins = int(minute_into_half % 60)
    display_hour = 12 if hour_12 == 0 else hour_12
    return f"{display_hour}:{mins:02d}"


def get_celestial_icon_id(cycle_minute: float, day_of_month: int) -> str:
    cm = cycle_minute % CYCLE_GAME_MINUTES
    if SUNRISE_MINUTE <= cm < NOON_THRESHOLD:
        return "morning_sun"
    if NOON_THRESHOLD <= cm < AFTERNOON_THRESHOLD:
        return "noon_sun"
    if AFTERNOON_THRESHOLD <= cm < SUNSET_MINUTE:
        return "sunset_sun"

    week_of_month = min(max(((day_of_month - 1) // DAYS_PER_WEEK) + 1, 1), 4)
    if week_of_month == 1:
        return "new_moon"
    elif week_of_month == 2:
        return "first_quarter_moon"
    elif week_of_month == 3:
        return "full_moon"
    else:
        return "last_quarter_moon"


def speed_to_multiplier(s: Speed) -> float:
    return {
        Speed.PAUSE: 0.0,
        Speed.SPEED_1X: 1.0,
        Speed.SPEED_3X: 3.0,
        Speed.SPEED_5X: 5.0,
        Speed.SPEED_9X: 9.0,
    }[s]


@dataclass
class TimeState:
    """Immutable snapshot returned by TimeSystem.snapshot()."""
    day_of_year: int             # 1..336+
    month: int                   # 1..12
    month_name: str              # "January".."December"
    day_of_month: int            # 1..28
    week_of_month: int           # 1..4
    minute_of_day: float         # 0.0..1440.0 (game minutes since cycle start)
    cycle_minute: float          # 0.0..1440.0 within the active day cycle
    phase: Phase                 # DAY or NIGHT based on cycle_minute
    season: Season
    speed: Speed
    celestial_icon_id: str


class TimeSystem:
    """Game clock controller.

    Use:
        ts = TimeSystem()
        ts.set_speed(Speed.SPEED_3X)
        for _ in range(N_FRAMES):
            ts.tick(real_dt_seconds)   # real seconds passed this frame
            ... = ts.snapshot()
    """

    def __init__(self, start_day_of_year: int = 1,
                 start_minute: float = 8 * 60,
                 speed: Speed = Speed.SPEED_1X):
        self._day_of_year = start_day_of_year
        self._minute_of_day = start_minute      # 0..1440 game minute
        self._speed = speed
        self._tick_count = 0

    @property
    def speed(self) -> Speed:
        return self._speed

    def set_speed(self, s: Speed):
        self._speed = s

    def tick(self, real_dt_seconds: float):
        """Advance the game clock by `real_dt_seconds` real seconds."""
        if real_dt_seconds <= 0:
            return
        multiplier = speed_to_multiplier(self._speed)
        if multiplier == 0.0:
            return
        new_date_pct = (self._minute_of_day
                        + real_dt_seconds * REAL_SECONDS_PER_GAME_MINUTE_AT_1X
                                          * multiplier)
        # Roll over to next day.
        day_delta, new_minute_of_day = divmod(new_date_pct, 1440.0)
        if day_delta > 0:
            self._day_of_year += int(day_delta)
        self._minute_of_day = new_minute_of_day
        self._tick_count += 1

    def cycle_minute(self) -> float:
        """0..1440 game-minute slot within the active day cycle."""
        return self._minute_of_day % CYCLE_GAME_MINUTES

    def phase(self) -> Phase:
        return Phase.DAY if (SUNRISE_MINUTE <= self.cycle_minute() < SUNSET_MINUTE) \
                        else Phase.NIGHT

    def wall_clock(self) -> str:
        """Format the current cycle_minute as 'H:MM'."""
        return format_wall_clock(self.cycle_minute())

    def month(self) -> int:
        day_in_year = ((self._day_of_year - 1) % DAYS_PER_YEAR) + 1
        return ((day_in_year - 1) // DAYS_PER_MONTH) + 1

    def month_name(self) -> str:
        return MONTH_NAMES[self.month() - 1]

    def day_of_month(self) -> int:
        day_in_year = ((self._day_of_year - 1) % DAYS_PER_YEAR) + 1
        return ((day_in_year - 1) % DAYS_PER_MONTH) + 1

    def week_of_month(self) -> int:
        dom = self.day_of_month()
        return min(max(((dom - 1) // DAYS_PER_WEEK) + 1, 1), 4)

    def season(self) -> Season:
        m = self.month()
        if m in (12, 1, 2):
            return Season.WINTER
        elif m in (3, 4, 5):
            return Season.SPRING
        elif m in (6, 7, 8):
            return Season.SUMMER
        else:
            return Season.AUTUMN

    def celestial_icon_id(self) -> str:
        return get_celestial_icon_id(self.cycle_minute(), self.day_of_month())

    def snapshot(self) -> TimeState:
        return TimeState(day_of_year=self._day_of_year,
                         month=self.month(),
                         month_name=self.month_name(),
                         day_of_month=self.day_of_month(),
                         week_of_month=self.week_of_month(),
                         minute_of_day=self._minute_of_day,
                         cycle_minute=self.cycle_minute(),
                         phase=self.phase(),
                         season=self.season(),
                         speed=self._speed,
                         celestial_icon_id=self.celestial_icon_id())

    def to_dict(self):
        s = self.snapshot()
        return {
            "day_of_year": s.day_of_year,
            "month": s.month,
            "month_name": s.month_name,
            "day_of_month": s.day_of_month,
            "week_of_month": s.week_of_month,
            "minute_of_day": round(s.minute_of_day, 1),
            "cycle_minute": round(s.cycle_minute, 1),
            "phase": s.phase.value,
            "season": s.season.value,
            "speed": s.speed.value,
            "celestial_icon_id": s.celestial_icon_id,
        }
