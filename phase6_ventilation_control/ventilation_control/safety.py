"""Safety overrides for ventilation control."""

from __future__ import annotations

from dataclasses import dataclass

from .models import SensorReading


@dataclass(frozen=True)
class SafetyConfig:
    fail_safe_speed_percent: float = 100.0
    critical_co2_ppm: float = 1800.0
    max_temperature_c: float = 60.0
    min_temperature_c: float = -10.0
    max_humidity_percent: float = 95.0


@dataclass(frozen=True)
class SafetyDecision:
    active: bool
    fan_speed_percent: float
    reason: str


class SafetyOverrideManager:
    def __init__(self, config: SafetyConfig | None = None) -> None:
        self.config = config or SafetyConfig()
        self.manual_override_speed: float | None = None
        self.emergency_stop = False

    def set_manual_override(self, speed_percent: float | None) -> None:
        if speed_percent is not None and not 0 <= speed_percent <= 100:
            raise ValueError("manual override speed must be between 0 and 100")
        self.manual_override_speed = speed_percent

    def set_emergency_stop(self, enabled: bool) -> None:
        self.emergency_stop = enabled

    def evaluate(self, reading: SensorReading) -> SafetyDecision:
        if self.emergency_stop:
            return SafetyDecision(True, 0.0, "emergency_stop")
        if self.manual_override_speed is not None:
            return SafetyDecision(True, self.manual_override_speed, "manual_override")
        if not reading.sensor_ok:
            return SafetyDecision(True, self.config.fail_safe_speed_percent, "sensor_fault")
        if reading.co2_ppm >= self.config.critical_co2_ppm:
            return SafetyDecision(True, 100.0, "critical_co2")
        if reading.temperature_c is not None:
            if reading.temperature_c >= self.config.max_temperature_c:
                return SafetyDecision(True, self.config.fail_safe_speed_percent, "high_temperature")
            if reading.temperature_c <= self.config.min_temperature_c:
                return SafetyDecision(True, 0.0, "low_temperature")
        if reading.humidity_percent is not None and reading.humidity_percent >= self.config.max_humidity_percent:
            return SafetyDecision(True, self.config.fail_safe_speed_percent, "high_humidity")
        return SafetyDecision(False, 0.0, "none")
