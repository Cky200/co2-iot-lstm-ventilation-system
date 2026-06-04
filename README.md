# Hybrid IoT–LSTM CO₂ Monitoring and Automated Ventilation Control System

## Phase 1: Hardware Setup

This is the foundational firmware and hardware interaction layer for the Hybrid IoT-LSTM CO₂ Monitoring system.
It interfaces with an MQ-135 analog CO₂ sensor (via an MCP3008 ADC) and actuates a ventilation relay to maintain safe CO₂ levels.

### Setup Instructions
Please refer to:
1. `docs/setup.md` - For Raspberry Pi environment setup and dependency installation.
2. `docs/hardware_wiring.md` - For wiring the sensor, ADC, and relay to the Raspberry Pi.

### Running the System
```bash
python -m src.firmware.main
```

### Running Tests
```bash
python -m pytest tests/ -v
```
