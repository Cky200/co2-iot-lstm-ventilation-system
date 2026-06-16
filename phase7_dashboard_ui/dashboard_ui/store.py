"""Thread-safe in-memory dashboard state."""

from __future__ import annotations

from collections import deque
from threading import RLock

from .alerts import AlertManager
from .models import Alert, TelemetryPoint, VentilationStatus


class DashboardStore:
    def __init__(self, *, max_points: int = 300, max_alerts: int = 50, alert_manager: AlertManager | None = None) -> None:
        self.max_points = max_points
        self.max_alerts = max_alerts
        self.alert_manager = alert_manager or AlertManager()
        self._telemetry: deque[TelemetryPoint] = deque(maxlen=max_points)
        self._alerts: deque[Alert] = deque(maxlen=max_alerts)
        self._ventilation = VentilationStatus()
        self._lock = RLock()

    def add_telemetry(self, point: TelemetryPoint) -> tuple[TelemetryPoint, Alert | None]:
        with self._lock:
            self._telemetry.append(point)
            if point.relay_state is not None or point.fan_speed_percent is not None:
                self._ventilation = VentilationStatus(
                    relay_state=bool(point.relay_state),
                    fan_speed_percent=float(point.fan_speed_percent if point.fan_speed_percent is not None else (100 if point.relay_state else 0)),
                    mode=self._ventilation.mode,
                    reason="telemetry_update",
                )
            alert = self.alert_manager.evaluate(point)
            if alert:
                self._alerts.append(alert)
            return point, alert

    def update_ventilation(self, status: VentilationStatus) -> VentilationStatus:
        with self._lock:
            self._ventilation = status
            return self._ventilation

    def snapshot(self) -> dict[str, object]:
        with self._lock:
            latest = self._telemetry[-1].to_dict() if self._telemetry else None
            return {
                "latest": latest,
                "history": [point.to_dict() for point in self._telemetry],
                "ventilation": self._ventilation.to_dict(),
                "alerts": [alert.to_dict() for alert in self._alerts],
            }

    def history(self, limit: int | None = None) -> list[dict[str, object]]:
        with self._lock:
            points = list(self._telemetry)
            if limit is not None:
                points = points[-limit:]
            return [point.to_dict() for point in points]

    def alerts(self) -> list[dict[str, object]]:
        with self._lock:
            return [alert.to_dict() for alert in self._alerts]
