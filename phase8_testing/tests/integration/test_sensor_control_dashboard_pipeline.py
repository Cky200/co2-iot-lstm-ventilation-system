from __future__ import annotations

import asyncio
from datetime import UTC, datetime

from dashboard_ui.store import DashboardStore
from iot_firmware.sensor import MQ135Calibration, MQ135Sensor
from ventilation_control.actuator import SimulatedVentilationActuator
from ventilation_control.controller import VentilationController
from ventilation_control.models import SensorReading
from ventilation_control.pid import PIDConfig, PIDController
from ventilation_control.safety import SafetyOverrideManager
from ventilation_control.schedule import ScheduleManager
from ventilation_control.thresholds import ThresholdConfig, ThresholdManager


class FakeADC:
    def __init__(self, voltage: float) -> None:
        self.voltage = voltage

    def read_voltage(self, channel: int) -> float:
        assert channel == 0
        return self.voltage


def test_phase5_to_phase6_to_phase7_integration():
    sensor = MQ135Sensor(
        FakeADC(2.0),
        load_resistance_kohm=10.0,
        vcc=5.0,
        calibration=MQ135Calibration(ro_kohm=15.0),
    )
    reading = asyncio.run(sensor.sample(sample_count=3, sample_delay_seconds=0))

    actuator = SimulatedVentilationActuator()
    controller = VentilationController(
        pid=PIDController(PIDConfig(kp=0.3, ki=0.0, kd=0.0, setpoint=400)),
        thresholds=ThresholdManager(
            ThresholdConfig(target_ppm=400, elevated_ppm=500, high_ppm=900, critical_ppm=1500)
        ),
        safety=SafetyOverrideManager(),
        schedule=ScheduleManager(),
        actuator=actuator,
        min_active_speed_percent=20,
    )
    command = controller.update(SensorReading(co2_ppm=reading["co2_ppm"]))

    store = DashboardStore(max_points=10)
    point, alert = store.add_telemetry(
        __import__("dashboard_ui.models", fromlist=["TelemetryPoint"]).TelemetryPoint(
            device_id="integration-device",
            timestamp=datetime.now(UTC),
            co2_ppm=reading["co2_ppm"],
            voltage=reading["voltage"],
            relay_state=command.relay_on,
            fan_speed_percent=command.fan_speed_percent,
        )
    )

    snapshot = store.snapshot()
    assert point.co2_ppm == reading["co2_ppm"]
    assert snapshot["latest"]["device_id"] == "integration-device"
    assert snapshot["ventilation"]["relay_state"] == command.relay_on
    assert alert is None
