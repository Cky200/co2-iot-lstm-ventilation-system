"""Shared domain models for ventilation control."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class VentilationMode(str, Enum):
    AUTO = "auto"
    MANUAL = "manual"
    OFF = "off"
    EMERGENCY = "emergency"


class AirQualityState(str, Enum):
    NORMAL = "normal"
    ELEVATED = "elevated"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class SensorReading:
    co2_ppm: float
    temperature_c: float | None = None
    humidity_percent: float | None = None
    sensor_ok: bool = True


@dataclass(frozen=True)
class ControlCommand:
    fan_speed_percent: float
    relay_on: bool
    mode: VentilationMode
    air_quality: AirQualityState
    reason: str
    safety_override: bool = False


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))
