from __future__ import annotations

import pytest
from ventilation_control.models import SensorReading
from ventilation_control.safety import SafetyConfig, SafetyOverrideManager


def test_safety_forces_full_speed_on_critical_co2():
    safety = SafetyOverrideManager(SafetyConfig(critical_co2_ppm=1800))

    decision = safety.evaluate(SensorReading(co2_ppm=1900))

    assert decision.active is True
    assert decision.fan_speed_percent == 100
    assert decision.reason == "critical_co2"


def test_safety_fails_safe_on_sensor_fault():
    safety = SafetyOverrideManager(SafetyConfig(fail_safe_speed_percent=80))

    decision = safety.evaluate(SensorReading(co2_ppm=0, sensor_ok=False))

    assert decision.active is True
    assert decision.fan_speed_percent == 80
    assert decision.reason == "sensor_fault"


def test_manual_override_takes_precedence_before_environmental_rules():
    safety = SafetyOverrideManager()
    safety.set_manual_override(45)

    decision = safety.evaluate(SensorReading(co2_ppm=2500))

    assert decision.active is True
    assert decision.fan_speed_percent == 45
    assert decision.reason == "manual_override"


def test_emergency_stop_forces_off():
    safety = SafetyOverrideManager()
    safety.set_emergency_stop(True)

    decision = safety.evaluate(SensorReading(co2_ppm=2500))

    assert decision.active is True
    assert decision.fan_speed_percent == 0
    assert decision.reason == "emergency_stop"


def test_manual_override_rejects_invalid_speed():
    safety = SafetyOverrideManager()

    with pytest.raises(ValueError):
        safety.set_manual_override(120)
