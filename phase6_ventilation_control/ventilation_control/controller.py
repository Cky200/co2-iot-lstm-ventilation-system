"""High-level ventilation controller."""

from __future__ import annotations

import logging
from datetime import datetime

from .actuator import VentilationActuator
from .models import AirQualityState, ControlCommand, SensorReading, VentilationMode, clamp
from .pid import PIDController
from .safety import SafetyOverrideManager
from .schedule import ScheduleManager
from .thresholds import ThresholdManager


class VentilationController:
    def __init__(
        self,
        *,
        pid: PIDController,
        thresholds: ThresholdManager,
        safety: SafetyOverrideManager,
        schedule: ScheduleManager,
        actuator: VentilationActuator,
        min_active_speed_percent: float = 20.0,
        logger: logging.Logger | None = None,
    ) -> None:
        self.pid = pid
        self.thresholds = thresholds
        self.safety = safety
        self.schedule = schedule
        self.actuator = actuator
        self.min_active_speed_percent = min_active_speed_percent
        self.logger = logger or logging.getLogger(__name__)
        self.mode = VentilationMode.AUTO

    def set_mode(self, mode: VentilationMode) -> None:
        self.mode = mode
        if mode == VentilationMode.OFF:
            self.pid.reset()

    def update(self, reading: SensorReading, *, now: datetime | None = None) -> ControlCommand:
        air_quality = self.thresholds.classify(reading.co2_ppm)
        safety = self.safety.evaluate(reading)

        if safety.active:
            mode = VentilationMode.EMERGENCY if safety.reason in {"critical_co2", "sensor_fault"} else self.mode
            return self._apply(safety.fan_speed_percent, mode, air_quality, safety.reason, safety_override=True)

        if self.mode == VentilationMode.OFF:
            return self._apply(0.0, self.mode, air_quality, "mode_off")

        speed = self.pid.update(reading.co2_ppm)
        reason = "pid_control"

        if air_quality in {AirQualityState.ELEVATED, AirQualityState.HIGH, AirQualityState.CRITICAL}:
            speed = max(speed, self.min_active_speed_percent)
            reason = f"{reason}_{air_quality.value}"

        speed, schedule_reason = self.schedule.apply(speed, now)
        if schedule_reason:
            reason = f"{reason}_{schedule_reason}"

        return self._apply(speed, self.mode, air_quality, reason)

    def shutdown(self) -> None:
        self.actuator.shutdown()

    def _apply(
        self,
        speed_percent: float,
        mode: VentilationMode,
        air_quality: AirQualityState,
        reason: str,
        *,
        safety_override: bool = False,
    ) -> ControlCommand:
        speed = clamp(speed_percent, 0.0, 100.0)
        self.actuator.set_speed(speed)
        command = ControlCommand(
            fan_speed_percent=round(speed, 2),
            relay_on=speed > 0,
            mode=mode,
            air_quality=air_quality,
            reason=reason,
            safety_override=safety_override,
        )
        self.logger.info("Ventilation command: %s", command)
        return command
