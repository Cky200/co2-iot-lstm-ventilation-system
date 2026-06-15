"""Runtime configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class MQTTConfig:
    broker_host: str = os.getenv("MQTT_BROKER_HOST", "localhost")
    broker_port: int = int(os.getenv("MQTT_BROKER_PORT", "1883"))
    username: str | None = os.getenv("MQTT_USERNAME")
    password: str | None = os.getenv("MQTT_PASSWORD")
    telemetry_topic: str = os.getenv("MQTT_TELEMETRY_TOPIC", "iot/co2/sensor1")
    status_topic: str = os.getenv("MQTT_STATUS_TOPIC", "iot/co2/sensor1/status")
    tls_enabled: bool = _bool_env("MQTT_TLS_ENABLED", False)
    keepalive_seconds: int = int(os.getenv("MQTT_KEEPALIVE_SECONDS", "60"))
    qos: int = int(os.getenv("MQTT_QOS", "1"))
    client_id: str = os.getenv("MQTT_CLIENT_ID", "co2-rpi-sensor")


@dataclass(frozen=True)
class SensorConfig:
    adc_channel: int = int(os.getenv("MQ135_ADC_CHANNEL", "0"))
    load_resistance_kohm: float = float(os.getenv("MQ135_RL_KOHM", "10.0"))
    vcc: float = float(os.getenv("MQ135_VCC", "5.0"))
    reference_voltage: float = float(os.getenv("ADC_REFERENCE_VOLTAGE", "3.3"))
    calibration_file: Path = Path(os.getenv("MQ135_CALIBRATION_FILE", "calibration.json"))
    sample_count: int = int(os.getenv("MQ135_SAMPLE_COUNT", "8"))
    sample_delay_seconds: float = float(os.getenv("MQ135_SAMPLE_DELAY_SECONDS", "0.05"))


@dataclass(frozen=True)
class OTAConfig:
    manifest_url: str | None = os.getenv("OTA_MANIFEST_URL")
    current_version: str = os.getenv("FIRMWARE_VERSION", "0.1.0")
    staging_dir: Path = Path(os.getenv("OTA_STAGING_DIR", "/tmp/co2-firmware-ota"))
    check_interval_seconds: int = int(os.getenv("OTA_CHECK_INTERVAL_SECONDS", "3600"))
    enabled: bool = _bool_env("OTA_ENABLED", False)


@dataclass(frozen=True)
class AppConfig:
    device_id: str = os.getenv("DEVICE_ID", "rpi_sensor_01")
    read_interval_seconds: float = float(os.getenv("READ_INTERVAL_SECONDS", "5.0"))
    watchdog_timeout_seconds: float = float(os.getenv("WATCHDOG_TIMEOUT_SECONDS", "30.0"))
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    mqtt: MQTTConfig = MQTTConfig()
    sensor: SensorConfig = SensorConfig()
    ota: OTAConfig = OTAConfig()
