"""CO2 threshold management with hysteresis."""

from __future__ import annotations

from dataclasses import dataclass

from .models import AirQualityState


@dataclass(frozen=True)
class ThresholdConfig:
    target_ppm: float = 800.0
    elevated_ppm: float = 900.0
    high_ppm: float = 1200.0
    critical_ppm: float = 1800.0
    hysteresis_ppm: float = 75.0

    def __post_init__(self) -> None:
        if not self.target_ppm < self.elevated_ppm < self.high_ppm < self.critical_ppm:
            raise ValueError("CO2 thresholds must increase from target to critical")
        if self.hysteresis_ppm < 0:
            raise ValueError("hysteresis_ppm must be non-negative")


class ThresholdManager:
    def __init__(self, config: ThresholdConfig | None = None) -> None:
        self.config = config or ThresholdConfig()
        self._state = AirQualityState.NORMAL

    @property
    def state(self) -> AirQualityState:
        return self._state

    def classify(self, co2_ppm: float) -> AirQualityState:
        cfg = self.config

        if self._state == AirQualityState.CRITICAL:
            if co2_ppm >= cfg.high_ppm - cfg.hysteresis_ppm:
                return self._set(AirQualityState.CRITICAL)
        if self._state == AirQualityState.HIGH:
            if co2_ppm >= cfg.elevated_ppm - cfg.hysteresis_ppm:
                if co2_ppm >= cfg.critical_ppm:
                    return self._set(AirQualityState.CRITICAL)
                return self._set(AirQualityState.HIGH)
        if self._state == AirQualityState.ELEVATED:
            if co2_ppm >= cfg.target_ppm - cfg.hysteresis_ppm:
                if co2_ppm >= cfg.high_ppm:
                    return self._set(AirQualityState.HIGH)
                return self._set(AirQualityState.ELEVATED)

        if co2_ppm >= cfg.critical_ppm:
            return self._set(AirQualityState.CRITICAL)
        if co2_ppm >= cfg.high_ppm:
            return self._set(AirQualityState.HIGH)
        if co2_ppm >= cfg.elevated_ppm:
            return self._set(AirQualityState.ELEVATED)
        return self._set(AirQualityState.NORMAL)

    def _set(self, state: AirQualityState) -> AirQualityState:
        self._state = state
        return state
