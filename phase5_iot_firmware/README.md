# Phase 5: IoT Firmware

Production Raspberry Pi firmware for MQ-135 CO2 telemetry. The runtime samples an MQ-135 sensor through an MCP3008 ADC, publishes telemetry asynchronously to MQTT, supervises long-running tasks with a watchdog, and can apply OTA update bundles from a signed-off manifest source.

## Features

- Async MQTT publishing with `asyncio` and `paho-mqtt`
- MQ-135 calibration persistence and ppm estimation
- Retry logic with exponential backoff and jitter
- Software watchdog and optional Linux `/dev/watchdog` heartbeat support
- OTA manifest download, SHA-256 verification, archive extraction, and optional install command
- Unit tests with mocked hardware and MQTT clients

## Install

```bash
cd phase5_iot_firmware
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On Raspberry Pi, enable SPI before running:

```bash
sudo raspi-config
# Interface Options -> SPI -> Enable
```

## Configure

The firmware is configured through environment variables.

| Variable | Default | Purpose |
| --- | --- | --- |
| `DEVICE_ID` | `rpi_sensor_01` | Device identifier included in telemetry |
| `MQTT_BROKER_HOST` | `localhost` | MQTT broker hostname |
| `MQTT_BROKER_PORT` | `1883` | MQTT broker port |
| `MQTT_USERNAME` / `MQTT_PASSWORD` | unset | MQTT credentials |
| `MQTT_TLS_ENABLED` | `false` | Enable TLS for MQTT |
| `MQTT_TELEMETRY_TOPIC` | `iot/co2/sensor1` | Telemetry topic |
| `MQTT_STATUS_TOPIC` | `iot/co2/sensor1/status` | Retained status topic |
| `MQ135_ADC_CHANNEL` | `0` | MCP3008 channel |
| `MQ135_RL_KOHM` | `10.0` | MQ-135 load resistance |
| `MQ135_VCC` | `5.0` | Sensor supply voltage |
| `MQ135_CALIBRATION_FILE` | `calibration.json` | Calibration file path |
| `READ_INTERVAL_SECONDS` | `5.0` | Sensor publish interval |
| `WATCHDOG_TIMEOUT_SECONDS` | `30.0` | Task watchdog timeout |
| `OTA_ENABLED` | `false` | Enable OTA checks |
| `OTA_MANIFEST_URL` | unset | OTA manifest URL |

## Calibrate MQ-135

Run calibration in clean outdoor air after the MQ-135 has warmed up. This example collects 60 samples and stores `calibration.json`.

```bash
python - <<'PY'
import asyncio
from pathlib import Path
from iot_firmware.sensor import MCP3008Reader, MQ135Sensor

async def main():
    sensor = MQ135Sensor(MCP3008Reader(), channel=0, load_resistance_kohm=10.0, vcc=5.0)
    calibration = await sensor.calibrate_clean_air(sample_count=60, sample_delay_seconds=1)
    calibration.save(Path("calibration.json"))
    print(calibration)

asyncio.run(main())
PY
```

## Run

```bash
export MQTT_BROKER_HOST=192.168.1.10
export DEVICE_ID=rpi_sensor_01
python -m iot_firmware.main
```

## OTA Manifest

The manifest must be JSON:

```json
{
  "version": "0.1.1",
  "url": "https://updates.example.com/co2-firmware-0.1.1.tar.gz",
  "sha256": "expected_archive_sha256_hex",
  "install_command": ["./install.sh"]
}
```

The updater downloads the archive into `OTA_STAGING_DIR`, verifies SHA-256, extracts the archive into a versioned release directory, then runs `install_command` from that directory when provided. Keep the manifest endpoint protected and publish only immutable archives.

## Test

```bash
cd phase5_iot_firmware
pytest -q
```
