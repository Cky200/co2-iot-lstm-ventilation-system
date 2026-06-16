from __future__ import annotations

from dashboard_ui.models import TelemetryPoint, VentilationStatus


def test_telemetry_normalizes_phase5_and_legacy_payloads():
    point = TelemetryPoint.from_payload(
        {
            "device_id": "sensor-1",
            "ts": 1781548200,
            "co2_ppm": "901.5",
            "voltage": "1.23",
            "relay_state": "true",
        }
    )

    assert point.device_id == "sensor-1"
    assert point.co2_ppm == 901.5
    assert point.voltage == 1.23
    assert point.relay_state is True

    legacy = TelemetryPoint.from_payload({"ppm": 700, "time": "2026-06-16T08:00:00Z"})
    assert legacy.co2_ppm == 700


def test_ventilation_status_accepts_relay_on_alias():
    status = VentilationStatus.from_payload({"relay_on": True, "fan_speed_percent": 55, "mode": "auto"})

    assert status.relay_state is True
    assert status.fan_speed_percent == 55
    assert status.mode == "auto"
