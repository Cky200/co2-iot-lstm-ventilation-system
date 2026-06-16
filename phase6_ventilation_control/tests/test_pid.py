from __future__ import annotations

import pytest

from ventilation_control.pid import PIDConfig, PIDController


def test_pid_output_increases_when_co2_is_above_setpoint():
    controller = PIDController(PIDConfig(kp=0.2, ki=0.0, kd=0.0, setpoint=800))

    output = controller.update(1000, now=10.0)

    assert output == pytest.approx(40.0)


def test_pid_clamps_output_and_integral():
    controller = PIDController(
        PIDConfig(
            kp=1.0,
            ki=1.0,
            kd=0.0,
            setpoint=0,
            output_min=0,
            output_max=50,
            integral_min=-10,
            integral_max=10,
        )
    )

    controller.update(100, now=0.0)
    output = controller.update(100, now=10.0)

    assert output == 50


def test_pid_reset_clears_derivative_history():
    controller = PIDController(PIDConfig(kp=0.0, ki=0.0, kd=1.0, setpoint=100))
    controller.update(120, now=1.0)

    controller.reset()
    output = controller.update(120, now=2.0)

    assert output == 0
