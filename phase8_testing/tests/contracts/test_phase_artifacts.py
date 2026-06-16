from __future__ import annotations


def test_previous_phase_artifacts_exist(repo_root):
    expected_paths = [
        "phase1_hardware_setup/README.md",
        "phase2_data_pipeline/README.md",
        "co2-iot-lstm-ventilation-system/phase4_ml_lstm_model/model.py",
        "phase5_iot_firmware/iot_firmware/main.py",
        "phase5_iot_firmware/tests/test_sensor.py",
        "phase6_ventilation_control/ventilation_control/controller.py",
        "phase6_ventilation_control/tests/test_controller.py",
        "phase7_dashboard_ui/dashboard_ui/app.py",
        "phase7_dashboard_ui/dashboard_ui/templates/dashboard.html",
        "phase7_dashboard_ui/tests/test_app.py",
    ]

    missing = [path for path in expected_paths if not (repo_root / path).exists()]

    assert missing == []


def test_cross_phase_payload_contract_supports_ppm_aliases():
    from dashboard_ui.models import TelemetryPoint

    phase5_payload = {"device_id": "rpi_sensor_01", "co2_ppm": 875, "voltage": 1.7}
    legacy_payload = {"device_id": "rpi_sensor_01", "ppm": 875, "voltage": 1.7}

    assert TelemetryPoint.from_payload(phase5_payload).co2_ppm == 875
    assert TelemetryPoint.from_payload(legacy_payload).co2_ppm == 875
