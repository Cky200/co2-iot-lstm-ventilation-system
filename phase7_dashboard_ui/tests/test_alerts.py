from __future__ import annotations

from datetime import UTC, datetime

from dashboard_ui.alerts import AlertManager, AlertThresholds
from dashboard_ui.models import TelemetryPoint


def make_point(ppm: float) -> TelemetryPoint:
    return TelemetryPoint(device_id="test", timestamp=datetime(2026, 6, 16, tzinfo=UTC), co2_ppm=ppm)


def test_alert_manager_emits_levels():
    manager = AlertManager(AlertThresholds(elevated_ppm=900, high_ppm=1200, critical_ppm=1800))

    assert manager.evaluate(make_point(800)) is None
    assert manager.evaluate(make_point(950)).level == "info"
    assert manager.evaluate(make_point(1300)).level == "warning"
    assert manager.evaluate(make_point(1900)).level == "critical"
