"""Weekly scheduling for ventilation policies."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time


@dataclass(frozen=True)
class ScheduleWindow:
    start: time
    end: time
    days: frozenset[int] = frozenset(range(7))
    min_fan_speed_percent: float = 0.0
    max_fan_speed_percent: float = 100.0
    enabled: bool = True

    def contains(self, moment: datetime) -> bool:
        if not self.enabled:
            return False
        current = moment.time()
        if self.start <= self.end:
            return moment.weekday() in self.days and self.start <= current < self.end
        if current >= self.start:
            return moment.weekday() in self.days
        previous_day = (moment.weekday() - 1) % 7
        return previous_day in self.days and current < self.end


class ScheduleManager:
    def __init__(self, windows: list[ScheduleWindow] | None = None) -> None:
        self.windows = windows or []

    def active_window(self, moment: datetime | None = None) -> ScheduleWindow | None:
        current = moment or datetime.now()
        for window in self.windows:
            if window.contains(current):
                return window
        return None

    def apply(self, speed_percent: float, moment: datetime | None = None) -> tuple[float, str | None]:
        window = self.active_window(moment)
        if window is None:
            return speed_percent, None
        scheduled = max(window.min_fan_speed_percent, min(window.max_fan_speed_percent, speed_percent))
        return scheduled, "schedule_window"
