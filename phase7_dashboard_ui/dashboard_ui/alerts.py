"""CO2 alert generation for the dashboard."""

from __future__ import annotations

from dataclasses import dataclass

from .models import Alert, TelemetryPoint


@dataclass(frozen=True)
class AlertThresholds:
    elevated_ppm: float = 900.0
    high_ppm: float = 1200.0
    critical_ppm: float = 1800.0

    def __post_init__(self) -> None:
        if not self.elevated_ppm < self.high_ppm < self.critical_ppm:
            raise ValueError("Alert thresholds must increase from elevated to critical")


class AlertManager:
    def __init__(self, thresholds: AlertThresholds | None = None) -> None:
        self.thresholds = thresholds or AlertThresholds()

    def evaluate(self, point: TelemetryPoint) -> Alert | None:
        ppm = point.co2_ppm
        if ppm >= self.thresholds.critical_ppm:
            return Alert("critical", "Critical CO2 level detected", ppm, point.timestamp)
        if ppm >= self.thresholds.high_ppm:
            return Alert("warning", "High CO2 level detected", ppm, point.timestamp)
        if ppm >= self.thresholds.elevated_ppm:
            return Alert("info", "CO2 level is elevated", ppm, point.timestamp)
        return None
