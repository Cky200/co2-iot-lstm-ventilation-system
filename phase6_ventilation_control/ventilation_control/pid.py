"""PID controller with output limits and anti-windup."""

from __future__ import annotations

import time
from dataclasses import dataclass

from .models import clamp


@dataclass
class PIDConfig:
    kp: float = 0.12
    ki: float = 0.01
    kd: float = 0.04
    setpoint: float = 800.0
    output_min: float = 0.0
    output_max: float = 100.0
    integral_min: float = -5000.0
    integral_max: float = 5000.0


class PIDController:
    def __init__(self, config: PIDConfig | None = None) -> None:
        self.config = config or PIDConfig()
        self._integral = 0.0
        self._last_error: float | None = None
        self._last_time: float | None = None

    def reset(self) -> None:
        self._integral = 0.0
        self._last_error = None
        self._last_time = None

    def update(self, measured_value: float, *, now: float | None = None) -> float:
        timestamp = time.monotonic() if now is None else now
        error = measured_value - self.config.setpoint

        if self._last_time is None:
            dt = 0.0
        else:
            dt = max(timestamp - self._last_time, 0.0)

        if dt > 0:
            self._integral += error * dt
            self._integral = clamp(self._integral, self.config.integral_min, self.config.integral_max)

        derivative = 0.0
        if self._last_error is not None and dt > 0:
            derivative = (error - self._last_error) / dt

        output = (
            self.config.kp * error
            + self.config.ki * self._integral
            + self.config.kd * derivative
        )

        self._last_error = error
        self._last_time = timestamp
        return clamp(output, self.config.output_min, self.config.output_max)
