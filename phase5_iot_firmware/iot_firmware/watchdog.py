"""Async watchdog for detecting stalled firmware tasks."""

from __future__ import annotations

import asyncio
import inspect
import logging
import os
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

WatchdogCallback = Callable[[str, float], None | Awaitable[None]]


@dataclass
class _Heartbeat:
    name: str
    last_seen: float


class AsyncWatchdog:
    def __init__(
        self,
        *,
        timeout_seconds: float,
        check_interval_seconds: float = 1.0,
        on_timeout: WatchdogCallback | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        self.timeout_seconds = timeout_seconds
        self.check_interval_seconds = check_interval_seconds
        self.on_timeout = on_timeout or self._default_timeout_handler
        self.logger = logger or logging.getLogger(__name__)
        self._heartbeats: dict[str, _Heartbeat] = {}
        self._task: asyncio.Task[None] | None = None
        self._stopped = asyncio.Event()

    def register(self, name: str) -> None:
        self.feed(name)

    def feed(self, name: str) -> None:
        self._heartbeats[name] = _Heartbeat(name=name, last_seen=time.monotonic())

    async def start(self) -> None:
        if self._task is None:
            self._stopped.clear()
            self._task = asyncio.create_task(self._run(), name="firmware-watchdog")

    async def stop(self) -> None:
        self._stopped.set()
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def _run(self) -> None:
        while not self._stopped.is_set():
            now = time.monotonic()
            for heartbeat in list(self._heartbeats.values()):
                age = now - heartbeat.last_seen
                if age > self.timeout_seconds:
                    self.logger.critical("Watchdog timeout for %s after %.2fs", heartbeat.name, age)
                    result = self.on_timeout(heartbeat.name, age)
                    if inspect.isawaitable(result):
                        await result
                    self.feed(heartbeat.name)
            await asyncio.sleep(self.check_interval_seconds)

    @staticmethod
    def _default_timeout_handler(name: str, age: float) -> None:
        raise TimeoutError(f"Watchdog timeout for {name}: {age:.2f}s")


class HardwareWatchdog:
    """Linux watchdog device heartbeat writer."""

    def __init__(self, device_path: str = "/dev/watchdog") -> None:
        self.device_path = device_path
        self._fd: int | None = None

    def start(self) -> None:
        self._fd = os.open(self.device_path, os.O_WRONLY)

    def feed(self) -> None:
        if self._fd is not None:
            os.write(self._fd, b"\0")

    def stop(self) -> None:
        if self._fd is not None:
            os.write(self._fd, b"V")
            os.close(self._fd)
            self._fd = None
