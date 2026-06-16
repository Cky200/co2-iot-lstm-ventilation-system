from __future__ import annotations

from ventilation_control.actuator import SimulatedVentilationActuator


def test_simulated_actuator_clamps_speed_and_sets_relay_state():
    actuator = SimulatedVentilationActuator()

    actuator.set_speed(150)
    assert actuator.speed_percent == 100
    assert actuator.relay_on is True

    actuator.shutdown()
    assert actuator.speed_percent == 0
    assert actuator.relay_on is False
