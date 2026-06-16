"""Ventilation actuator abstractions."""

from __future__ import annotations

import logging
from typing import Protocol

from .models import clamp


class VentilationActuator(Protocol):
    def set_speed(self, speed_percent: float) -> None:
        """Set requested fan speed."""

    def shutdown(self) -> None:
        """Place actuator in a safe off state."""


class SimulatedVentilationActuator:
    def __init__(self) -> None:
        self.speed_percent = 0.0
        self.relay_on = False

    def set_speed(self, speed_percent: float) -> None:
        self.speed_percent = clamp(speed_percent, 0.0, 100.0)
        self.relay_on = self.speed_percent > 0

    def shutdown(self) -> None:
        self.set_speed(0.0)


class GPIOPWMVentilationActuator:
    """Raspberry Pi PWM fan actuator with relay-compatible behavior."""

    def __init__(self, pwm_pin: int, *, frequency_hz: int = 25_000, logger: logging.Logger | None = None) -> None:
        self.logger = logger or logging.getLogger(__name__)
        try:
            from gpiozero import PWMOutputDevice
        except ImportError as exc:  # pragma: no cover - Raspberry Pi dependency
            raise RuntimeError("gpiozero is required for GPIOPWMVentilationActuator") from exc

        self._device = PWMOutputDevice(pwm_pin, frequency=frequency_hz, initial_value=0.0)
        self.speed_percent = 0.0
        self.relay_on = False

    def set_speed(self, speed_percent: float) -> None:
        self.speed_percent = clamp(speed_percent, 0.0, 100.0)
        self.relay_on = self.speed_percent > 0
        self._device.value = self.speed_percent / 100.0
        self.logger.info("Ventilation speed set to %.1f%%", self.speed_percent)

    def shutdown(self) -> None:
        self.set_speed(0.0)
        self._device.close()
