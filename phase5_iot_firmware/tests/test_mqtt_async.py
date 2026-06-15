from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass

from iot_firmware.config import MQTTConfig
from iot_firmware.mqtt_async import AsyncMQTTPublisher


@dataclass
class PublishInfo:
    mid: int
    rc: int = 0


class FakePahoClient:
    def __init__(self) -> None:
        self.on_connect = None
        self.on_disconnect = None
        self.on_publish = None
        self.published: list[tuple[str, str, int, bool]] = []
        self.loop_started = False
        self.loop_stopped = False
        self._mid = 10

    def connect_async(self, host: str, port: int, keepalive: int) -> None:
        assert host == "broker.local"
        asyncio.get_running_loop().call_soon(self.on_connect, self, None, None, 0)

    def loop_start(self) -> None:
        self.loop_started = True

    def loop_stop(self) -> None:
        self.loop_stopped = True

    def publish(self, topic: str, payload: str, qos: int, retain: bool) -> PublishInfo:
        self._mid += 1
        self.published.append((topic, payload, qos, retain))
        asyncio.get_running_loop().call_soon(self.on_publish, self, None, self._mid)
        return PublishInfo(mid=self._mid)

    def disconnect(self) -> None:
        asyncio.get_running_loop().call_soon(self.on_disconnect, self, None, 0)


def test_async_mqtt_publishes_json_and_disconnects():
    asyncio.run(_run_mqtt_publish_test())


async def _run_mqtt_publish_test():
    fake_client = FakePahoClient()
    publisher = AsyncMQTTPublisher(
        MQTTConfig(broker_host="broker.local", client_id="device-1", qos=1),
        client=fake_client,
    )

    await publisher.connect()
    await publisher.publish_json("topic/telemetry", {"b": 2, "a": 1})
    await publisher.disconnect()

    topic, payload, qos, retain = fake_client.published[0]
    assert fake_client.loop_started is True
    assert fake_client.loop_stopped is True
    assert topic == "topic/telemetry"
    assert json.loads(payload) == {"a": 1, "b": 2}
    assert qos == 1
    assert retain is False
