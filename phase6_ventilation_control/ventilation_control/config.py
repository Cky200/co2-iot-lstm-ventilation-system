"""Environment-backed configuration for Phase 6."""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from .pid import PIDConfig
from .safety import SafetyConfig
from .thresholds import ThresholdConfig


@dataclass(frozen=True)
class AppConfig:
    pwm_pin: int = int(os.getenv("VENT_PWM_PIN", "18"))
    control_interval_seconds: float = float(os.getenv("VENT_CONTROL_INTERVAL_SECONDS", "5.0"))
    min_active_speed_percent: float = float(os.getenv("VENT_MIN_ACTIVE_SPEED_PERCENT", "20.0"))
    pid: PIDConfig = field(default_factory=lambda: PIDConfig(
        kp=float(os.getenv("VENT_PID_KP", "0.12")),
        ki=float(os.getenv("VENT_PID_KI", "0.01")),
        kd=float(os.getenv("VENT_PID_KD", "0.04")),
        setpoint=float(os.getenv("VENT_CO2_SETPOINT", "800.0")),
    ))
    thresholds: ThresholdConfig = field(default_factory=lambda: ThresholdConfig(
        target_ppm=float(os.getenv("VENT_CO2_TARGET_PPM", "800.0")),
        elevated_ppm=float(os.getenv("VENT_CO2_ELEVATED_PPM", "900.0")),
        high_ppm=float(os.getenv("VENT_CO2_HIGH_PPM", "1200.0")),
        critical_ppm=float(os.getenv("VENT_CO2_CRITICAL_PPM", "1800.0")),
        hysteresis_ppm=float(os.getenv("VENT_CO2_HYSTERESIS_PPM", "75.0")),
    ))
    safety: SafetyConfig = field(default_factory=lambda: SafetyConfig(
        fail_safe_speed_percent=float(os.getenv("VENT_FAIL_SAFE_SPEED_PERCENT", "100.0")),
        critical_co2_ppm=float(os.getenv("VENT_CO2_CRITICAL_PPM", "1800.0")),
        max_temperature_c=float(os.getenv("VENT_MAX_TEMPERATURE_C", "60.0")),
        min_temperature_c=float(os.getenv("VENT_MIN_TEMPERATURE_C", "-10.0")),
        max_humidity_percent=float(os.getenv("VENT_MAX_HUMIDITY_PERCENT", "95.0")),
    ))
