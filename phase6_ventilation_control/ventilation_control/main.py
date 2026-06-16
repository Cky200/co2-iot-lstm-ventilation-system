"""Example CLI runner for the ventilation controller."""

from __future__ import annotations

import argparse
import logging

from .actuator import GPIOPWMVentilationActuator, SimulatedVentilationActuator
from .config import AppConfig
from .controller import VentilationController
from .models import SensorReading
from .pid import PIDController
from .safety import SafetyOverrideManager
from .schedule import ScheduleManager
from .thresholds import ThresholdManager


def build_controller(config: AppConfig, *, simulate: bool) -> VentilationController:
    actuator = SimulatedVentilationActuator() if simulate else GPIOPWMVentilationActuator(config.pwm_pin)
    return VentilationController(
        pid=PIDController(config.pid),
        thresholds=ThresholdManager(config.thresholds),
        safety=SafetyOverrideManager(config.safety),
        schedule=ScheduleManager(),
        actuator=actuator,
        min_active_speed_percent=config.min_active_speed_percent,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 6 ventilation control smoke runner")
    parser.add_argument("--simulate", action="store_true", help="Use in-memory actuator instead of GPIO")
    parser.add_argument("--co2", type=float, default=900.0, help="Single CO2 reading to control against")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [%(name)s] %(message)s")
    controller = build_controller(AppConfig(), simulate=args.simulate)
    command = controller.update(SensorReading(co2_ppm=args.co2))
    print(command)


if __name__ == "__main__":
    main()
