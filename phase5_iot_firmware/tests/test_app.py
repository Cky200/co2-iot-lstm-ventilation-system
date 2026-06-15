from __future__ import annotations

import asyncio

from iot_firmware.app import FirmwareApp
from iot_firmware.config import AppConfig, MQTTConfig, SensorConfig


class FakeSensor:
    async def sample(self, *, sample_count: int, sample_delay_seconds: float) -> dict[str, float]:
        return {"co2_ppm": 515.2, "voltage": 1.234}


class FakeMQTT:
    def __init__(self) -> None:
        self.messages: list[tuple[str, dict]] = []

    async def connect(self) -> None:
        pass

    async def publish_json(self, topic: str, payload: dict, *, retain: bool = False) -> None:
        self.messages.append((topic, payload))

    async def publish_status(self, status: str, **extra) -> None:
        self.messages.append(("status", {"status": status, **extra}))

    async def disconnect(self) -> None:
        pass


def test_app_publishes_sensor_payload():
    asyncio.run(_run_app_publish_test())


async def _run_app_publish_test():
    mqtt = FakeMQTT()
    config = AppConfig(
        device_id="unit-test-device",
        mqtt=MQTTConfig(telemetry_topic="telemetry/topic"),
        sensor=SensorConfig(sample_count=3, sample_delay_seconds=0),
    )
    app = FirmwareApp(config, sensor=FakeSensor(), mqtt_publisher=mqtt)

    await app._publish_sensor_sample()

    topic, payload = mqtt.messages[0]
    assert topic == "telemetry/topic"
    assert payload["device_id"] == "unit-test-device"
    assert payload["co2_ppm"] == 515.2
    assert payload["voltage"] == 1.234
