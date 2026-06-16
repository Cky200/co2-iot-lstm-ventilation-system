from __future__ import annotations

from datetime import datetime, time

from ventilation_control.actuator import SimulatedVentilationActuator
from ventilation_control.controller import VentilationController
from ventilation_control.models import AirQualityState, SensorReading, VentilationMode
from ventilation_control.pid import PIDConfig, PIDController
from ventilation_control.safety import SafetyConfig, SafetyOverrideManager
from ventilation_control.schedule import ScheduleManager, ScheduleWindow
from ventilation_control.thresholds import ThresholdConfig, ThresholdManager


def build_controller() -> tuple[VentilationController, SimulatedVentilationActuator]:
    actuator = SimulatedVentilationActuator()
    controller = VentilationController(
        pid=PIDController(PIDConfig(kp=0.2, ki=0.0, kd=0.0, setpoint=800)),
        thresholds=ThresholdManager(
            ThresholdConfig(target_ppm=800, elevated_ppm=900, high_ppm=1200, critical_ppm=1800)
        ),
        safety=SafetyOverrideManager(SafetyConfig(critical_co2_ppm=1800)),
        schedule=ScheduleManager(),
        actuator=actuator,
        min_active_speed_percent=20,
    )
    return controller, actuator


def test_controller_uses_pid_and_min_active_speed():
    controller, actuator = build_controller()

    command = controller.update(SensorReading(co2_ppm=950))

    assert command.air_quality == AirQualityState.ELEVATED
    assert command.fan_speed_percent == 30
    assert command.relay_on is True
    assert actuator.speed_percent == 30


def test_controller_forces_minimum_when_pid_output_is_small_but_co2_elevated():
    controller, actuator = build_controller()
    controller.pid = PIDController(PIDConfig(kp=0.01, ki=0.0, kd=0.0, setpoint=800))

    command = controller.update(SensorReading(co2_ppm=901))

    assert command.fan_speed_percent == 20
    assert actuator.relay_on is True


def test_controller_respects_off_mode():
    controller, actuator = build_controller()
    controller.set_mode(VentilationMode.OFF)

    command = controller.update(SensorReading(co2_ppm=1000))

    assert command.fan_speed_percent == 0
    assert command.reason == "mode_off"
    assert actuator.relay_on is False


def test_controller_applies_safety_override():
    controller, actuator = build_controller()

    command = controller.update(SensorReading(co2_ppm=2000))

    assert command.safety_override is True
    assert command.mode == VentilationMode.EMERGENCY
    assert command.fan_speed_percent == 100
    assert actuator.speed_percent == 100


def test_controller_applies_schedule_window():
    actuator = SimulatedVentilationActuator()
    controller = VentilationController(
        pid=PIDController(PIDConfig(kp=0.1, ki=0.0, kd=0.0, setpoint=800)),
        thresholds=ThresholdManager(),
        safety=SafetyOverrideManager(),
        schedule=ScheduleManager(
            [ScheduleWindow(start=time(9, 0), end=time(17, 0), min_fan_speed_percent=40)]
        ),
        actuator=actuator,
    )

    command = controller.update(SensorReading(co2_ppm=850), now=datetime(2026, 6, 15, 10, 0))

    assert command.fan_speed_percent == 40
    assert "schedule_window" in command.reason
