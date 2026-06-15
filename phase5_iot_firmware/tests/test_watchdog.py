from __future__ import annotations

import asyncio

from iot_firmware.watchdog import AsyncWatchdog


def test_watchdog_invokes_timeout_callback():
    asyncio.run(_run_watchdog_test())


async def _run_watchdog_test():
    events: list[tuple[str, float]] = []

    async def on_timeout(name: str, age: float) -> None:
        events.append((name, age))

    watchdog = AsyncWatchdog(
        timeout_seconds=0.01,
        check_interval_seconds=0.005,
        on_timeout=on_timeout,
    )
    watchdog.register("sensor-loop")
    await watchdog.start()
    await asyncio.sleep(0.04)
    await watchdog.stop()

    assert events
    assert events[0][0] == "sensor-loop"
