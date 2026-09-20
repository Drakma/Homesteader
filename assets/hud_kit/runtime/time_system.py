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


# Per-season slice of the year (number of days). Default: 30 x 4 = 120.
DAYS_PER_SEASON = 30
DAYS_PER_YEAR = DAYS_PER_SEASON * 4

# Real-time clock constants.
REAL_SECONDS_PER_GAME_MINUTE_AT_1X = 1.0     # 1 real second = 1 game minute at 1x

# 12-hour phases. DAY = 12:00 AM -> 11:59 AM. NIGHT = 12:00 PM -> 11:59 PM.
DAY_GAME_MINUTES = 12 * 60       # 720
NIGHT_GAME_MINUTES = 12 * 60     # 720
CYCLE_GAME_MINUTES = DAY_GAME_MINUTES + NIGHT_GAME_MINUTES  # 1440 = 24h


def format_wall_clock(cycle_minute: float) -> str:
    """Map a 0..1440 cycle_minute to 'H:MM AM/PM' on a 12-hour face.

    cycle_minute 0      -> 12:00 AM
    cycle_minute 60     -> 1:00 AM
    cycle_minute 11*60  -> 11:00 AM
    cycle_minute 720    -> 12:00 PM
    cycle_minute 779    -> 12:59 PM
    cycle_minute 1439   -> 11:59 PM
    """
    cm = cycle_minute % CYCLE_GAME_MINUTES
    is_pm = cm >= DAY_GAME_MINUTES
    minute_into_half = cm - DAY_GAME_MINUTES if is_pm else cm
    hour_12 = int(minute_into_half // 60)
    mins = int(minute_into_half % 60)
    display_hour = 12 if hour_12 == 0 else hour_12
    suffix = "PM" if is_pm else "AM"
    return f"{display_hour}:{mins:02d} {suffix}"


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
    day_of_year: int             # 1..365+
    minute_of_day: float         # 0.0..1440.0 (game minutes since cycle start)
    cycle_minute: float          # 0.0..40.0 within the active day cycle
    phase: Phase                 # DAY or NIGHT based on cycle_minute
    season: Season
    speed: Speed


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
        """0-40 game-minute slot within the active day cycle."""
        return self._minute_of_day % CYCLE_GAME_MINUTES

    def phase(self) -> Phase:
        return Phase.DAY if self.cycle_minute() < DAY_GAME_MINUTES \
                        else Phase.NIGHT

    def wall_clock(self) -> str:
        """Format the current cycle_minute as 'H:MM AM/PM'."""
        return format_wall_clock(self.cycle_minute())

    def season(self) -> Season:
        # Spring: days 1..30, Summer: 31..60, Autumn: 61..90, Winter: 91..120.
        # Beyond, cycles again.
        day_in_year_cycle = ((self._day_of_year - 1) % DAYS_PER_YEAR) + 1
        idx = (day_in_year_cycle - 1) // DAYS_PER_SEASON
        return [Season.SPRING, Season.SUMMER,
                Season.AUTUMN, Season.WINTER][min(idx, 3)]

    def snapshot(self) -> TimeState:
        return TimeState(day_of_year=self._day_of_year,
                         minute_of_day=self._minute_of_day,
                         cycle_minute=self.cycle_minute(),
                         phase=self.phase(),
                         season=self.season(),
                         speed=self._speed)

    def to_dict(self):
        s = self.snapshot()
        return {
            "day_of_year": s.day_of_year,
            "minute_of_day": round(s.minute_of_day, 1),
            "cycle_minute": round(s.cycle_minute, 1),
            "phase": s.phase.value,
            "season": s.season.value,
            "speed": s.speed.value,
        }
