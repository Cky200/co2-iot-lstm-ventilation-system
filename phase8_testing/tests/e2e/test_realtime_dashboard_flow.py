from __future__ import annotations

from dashboard_ui.app import create_app, socketio
from dashboard_ui.config import DashboardConfig


def test_realtime_dashboard_socketio_flow():
    app = create_app(DashboardConfig(secret_key="phase8-e2e", history_limit=10))
    app.config.update(TESTING=True)
    client = socketio.test_client(app)

    initial_events = client.get_received()
    assert initial_events[0]["name"] == "state_snapshot"

    ack = client.emit(
        "telemetry",
        {
            "device_id": "e2e-device",
            "timestamp": "2026-06-16T08:00:00Z",
            "co2_ppm": 1900,
            "relay_state": True,
            "fan_speed_percent": 100,
        },
        callback=True,
    )

    assert ack == {"status": "accepted"}
    received = client.get_received()
    names = [event["name"] for event in received]
    assert "telemetry_update" in names
    assert "ventilation_status" in names
    assert "alert" in names

    alert_event = next(event for event in received if event["name"] == "alert")
    assert alert_event["args"][0]["level"] == "critical"
    client.disconnect()
