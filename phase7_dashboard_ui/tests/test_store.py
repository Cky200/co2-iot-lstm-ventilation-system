from __future__ import annotations

from datetime import UTC, datetime

from dashboard_ui.alerts import AlertManager, AlertThresholds
from dashboard_ui.models import TelemetryPoint
from dashboard_ui.store import DashboardStore


def test_store_keeps_bounded_history_and_alerts():
    store = DashboardStore(
        max_points=2,
        max_alerts=2,
        alert_manager=AlertManager(AlertThresholds(elevated_ppm=900, high_ppm=1200, critical_ppm=1800)),
    )

    for ppm in (800, 950, 1300):
        store.add_telemetry(
            TelemetryPoint(device_id="sensor", timestamp=datetime(2026, 6, 16, tzinfo=UTC), co2_ppm=ppm)
        )

    snapshot = store.snapshot()
    assert len(snapshot["history"]) == 2
    assert snapshot["latest"]["co2_ppm"] == 1300
    assert len(snapshot["alerts"]) == 2
