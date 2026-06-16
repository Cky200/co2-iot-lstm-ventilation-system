# Phase 6: Ventilation Control

Production-ready automated ventilation control for CO2 mitigation. This phase turns sensor readings into fan commands using PID control, threshold hysteresis, safety overrides, and weekly schedules.

## Components

- `PIDController`: proportional, integral, and derivative control with output limits and anti-windup
- `ThresholdManager`: CO2 state classification with hysteresis to prevent relay chatter
- `SafetyOverrideManager`: critical CO2, sensor fault, temperature, humidity, manual override, and emergency stop handling
- `ScheduleManager`: weekly and overnight schedules with min/max fan speed limits
- `VentilationController`: combines PID, thresholds, schedules, and safety into actuator commands
- `GPIOPWMVentilationActuator`: Raspberry Pi PWM output using `gpiozero`
- `SimulatedVentilationActuator`: in-memory actuator for tests and local development

## Install

```bash
cd phase6_ventilation_control
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configuration

Environment variables:

| Variable | Default | Purpose |
| --- | --- | --- |
| `VENT_PWM_PIN` | `18` | Raspberry Pi PWM GPIO pin |
| `VENT_CONTROL_INTERVAL_SECONDS` | `5.0` | Control-loop interval |
| `VENT_MIN_ACTIVE_SPEED_PERCENT` | `20.0` | Minimum fan speed when CO2 is elevated |
| `VENT_PID_KP` | `0.12` | PID proportional gain |
| `VENT_PID_KI` | `0.01` | PID integral gain |
| `VENT_PID_KD` | `0.04` | PID derivative gain |
| `VENT_CO2_SETPOINT` | `800.0` | PID target CO2 ppm |
| `VENT_CO2_TARGET_PPM` | `800.0` | Normal target boundary |
| `VENT_CO2_ELEVATED_PPM` | `900.0` | Elevated CO2 threshold |
| `VENT_CO2_HIGH_PPM` | `1200.0` | High CO2 threshold |
| `VENT_CO2_CRITICAL_PPM` | `1800.0` | Critical safety threshold |
| `VENT_CO2_HYSTERESIS_PPM` | `75.0` | Threshold hysteresis |
| `VENT_FAIL_SAFE_SPEED_PERCENT` | `100.0` | Fan speed on sensor fault |
| `VENT_MAX_TEMPERATURE_C` | `60.0` | High-temperature safety limit |
| `VENT_MIN_TEMPERATURE_C` | `-10.0` | Low-temperature safety limit |
| `VENT_MAX_HUMIDITY_PERCENT` | `95.0` | High-humidity safety limit |

## Smoke Run

Run locally without GPIO:

```bash
python3 -m ventilation_control.main --simulate --co2 950
```

Run on Raspberry Pi with PWM fan hardware:

```bash
python3 -m ventilation_control.main --co2 950
```

## Usage Example

```python
from datetime import time

from ventilation_control.actuator import GPIOPWMVentilationActuator
from ventilation_control.controller import VentilationController
from ventilation_control.models import SensorReading
from ventilation_control.pid import PIDController
from ventilation_control.safety import SafetyOverrideManager
from ventilation_control.schedule import ScheduleManager, ScheduleWindow
from ventilation_control.thresholds import ThresholdManager

controller = VentilationController(
    pid=PIDController(),
    thresholds=ThresholdManager(),
    safety=SafetyOverrideManager(),
    schedule=ScheduleManager([
        ScheduleWindow(start=time(8, 0), end=time(18, 0), min_fan_speed_percent=20)
    ]),
    actuator=GPIOPWMVentilationActuator(pwm_pin=18),
)

command = controller.update(SensorReading(co2_ppm=1050, temperature_c=24.0, humidity_percent=50.0))
print(command)
```

## Tests

```bash
python3 -m pytest phase6_ventilation_control/tests -q
```
