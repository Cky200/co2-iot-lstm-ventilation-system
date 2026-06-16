from __future__ import annotations

from dashboard_ui.app import create_app
from dashboard_ui.config import DashboardConfig


def test_dashboard_api_health_state_history_and_alerts():
    app = create_app(DashboardConfig(secret_key="phase8-test", history_limit=5))
    app.config.update(TESTING=True)
    client = app.test_client()

    assert client.get("/health").get_json() == {"status": "ok"}
    assert client.get("/api/state").status_code == 200

    response = client.post(
        "/api/telemetry",
        json={
            "device_id": "api-device",
            "timestamp": "2026-06-16T08:00:00Z",
            "ppm": 1300,
            "voltage": 1.9,
            "relay_state": True,
        },
    )

    assert response.status_code == 202
    assert response.get_json()["alert"]["level"] == "warning"

    history = client.get("/api/history?limit=1").get_json()["data"]
    alerts = client.get("/api/alerts").get_json()["data"]
    assert len(history) == 1
    assert history[0]["device_id"] == "api-device"
    assert alerts[-1]["level"] == "warning"


def test_dashboard_api_rejects_invalid_telemetry_payload():
    app = create_app(DashboardConfig(secret_key="phase8-test"))
    app.config.update(TESTING=True)
    client = app.test_client()

    response = client.post("/api/telemetry", json={"device_id": "missing-ppm"})

    assert response.status_code == 400
    assert "requires co2_ppm or ppm" in response.get_json()["error"]
