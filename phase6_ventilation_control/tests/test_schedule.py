from __future__ import annotations

from datetime import datetime, time

from ventilation_control.schedule import ScheduleManager, ScheduleWindow


def test_schedule_applies_minimum_and_maximum_speed():
    manager = ScheduleManager(
        [
            ScheduleWindow(
                start=time(9, 0),
                end=time(17, 0),
                days=frozenset({0}),
                min_fan_speed_percent=30,
                max_fan_speed_percent=70,
            )
        ]
    )

    assert manager.apply(10, datetime(2026, 6, 15, 10, 0))[0] == 30
    assert manager.apply(90, datetime(2026, 6, 15, 10, 0))[0] == 70
    assert manager.apply(10, datetime(2026, 6, 16, 10, 0))[0] == 10


def test_overnight_schedule_covers_following_morning():
    manager = ScheduleManager(
        [
            ScheduleWindow(
                start=time(22, 0),
                end=time(6, 0),
                days=frozenset({0}),
                min_fan_speed_percent=25,
            )
        ]
    )

    assert manager.active_window(datetime(2026, 6, 15, 23, 0)) is not None
    assert manager.active_window(datetime(2026, 6, 16, 5, 30)) is not None
    assert manager.active_window(datetime(2026, 6, 16, 7, 0)) is None
