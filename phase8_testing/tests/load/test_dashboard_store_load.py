from __future__ import annotations

from datetime import UTC, datetime

from dashboard_ui.models import TelemetryPoint
from dashboard_ui.store import DashboardStore


def test_dashboard_store_handles_high_volume_ingestion_quickly():
    store = DashboardStore(max_points=500, max_alerts=100)

    for index in range(2_000):
        store.add_telemetry(
            TelemetryPoint(
                device_id=f"load-device-{index % 4}",
                timestamp=datetime(2026, 6, 16, tzinfo=UTC),
                co2_ppm=700 + (index % 900),
                voltage=1.5,
                relay_state=index % 2 == 0,
            )
        )

    snapshot = store.snapshot()
    assert len(snapshot["history"]) == 500
    assert snapshot["latest"]["device_id"] == "load-device-3"
    assert len(snapshot["alerts"]) <= 100
