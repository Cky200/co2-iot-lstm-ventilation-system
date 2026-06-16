from __future__ import annotations

from dashboard_ui.app import create_app, socketio
from dashboard_ui.config import DashboardConfig


def build_app():
    app = create_app(DashboardConfig(secret_key="test", history_limit=10))
    app.config.update(TESTING=True)
    return app


def test_dashboard_routes_and_telemetry_ingest():
    app = build_app()
    client = app.test_client()

    assert client.get("/health").json == {"status": "ok"}
    assert b"Ventilation Dashboard" in client.get("/").data

    response = client.post(
        "/api/telemetry",
        json={"device_id": "sensor-1", "co2_ppm": 1250, "voltage": 1.9, "relay_state": True},
    )

    assert response.status_code == 202
    body = response.get_json()
    assert body["telemetry"]["co2_ppm"] == 1250
    assert body["alert"]["level"] == "warning"

    state = client.get("/api/state").get_json()
    assert state["latest"]["device_id"] == "sensor-1"
    assert state["ventilation"]["relay_state"] is True


def test_ventilation_api_updates_status():
    app = build_app()
    client = app.test_client()

    response = client.post(
        "/api/ventilation",
        json={"relay_on": True, "fan_speed_percent": 65, "mode": "auto", "reason": "pid_control"},
    )

    assert response.status_code == 202
    state = client.get("/api/state").get_json()
    assert state["ventilation"]["fan_speed_percent"] == 65
    assert state["ventilation"]["reason"] == "pid_control"


def test_socketio_receives_snapshot_and_telemetry_events():
    app = build_app()
    client = socketio.test_client(app)

    received = client.get_received()
    assert received[0]["name"] == "state_snapshot"

    ack = client.emit("telemetry", {"device_id": "socket-sensor", "ppm": 950}, callback=True)
    assert ack == {"status": "accepted"}

    events = client.get_received()
    names = [event["name"] for event in events]
    assert "telemetry_update" in names
    assert "alert" in names
    client.disconnect()
