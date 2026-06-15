"""Asyncio-friendly MQTT publisher built on paho-mqtt."""

from __future__ import annotations

import asyncio
import json
import logging
import ssl
import time
from typing import Any

from .config import MQTTConfig
from .retry import retry_async

try:
    import paho.mqtt.client as mqtt
except ImportError:  # pragma: no cover - exercised only when dependency is absent
    mqtt = None  # type: ignore[assignment]


class MQTTPublishError(RuntimeError):
    """Raised when MQTT publish acknowledgement fails."""


class AsyncMQTTPublisher:
    """Small async wrapper around paho-mqtt's network loop thread."""

    def __init__(
        self,
        config: MQTTConfig,
        *,
        logger: logging.Logger | None = None,
        client: Any | None = None,
    ) -> None:
        if mqtt is None and client is None:
            raise RuntimeError("paho-mqtt is required. Install dependencies from requirements.txt")

        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        self._loop: asyncio.AbstractEventLoop | None = None
        self._connected = asyncio.Event()
        self._connect_future: asyncio.Future[None] | None = None
        self._disconnect_future: asyncio.Future[None] | None = None
        self._pending_publishes: dict[int, asyncio.Future[None]] = {}
        self._client = client or self._build_client()
        self._bind_callbacks()

    def _build_client(self) -> Any:
        assert mqtt is not None
        try:
            client = mqtt.Client(
                client_id=self.config.client_id,
                protocol=mqtt.MQTTv311,
                callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            )
        except (AttributeError, TypeError):
            client = mqtt.Client(client_id=self.config.client_id, protocol=mqtt.MQTTv311)

        if self.config.username:
            client.username_pw_set(self.config.username, self.config.password)
        if self.config.tls_enabled:
            client.tls_set(cert_reqs=ssl.CERT_REQUIRED)
        return client

    def _bind_callbacks(self) -> None:
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_publish = self._on_publish

    async def connect(self) -> None:
        self._loop = asyncio.get_running_loop()
        await retry_async(
            self._connect_once,
            attempts=6,
            base_delay=0.5,
            max_delay=20.0,
            logger=self.logger,
            operation_name="mqtt connect",
        )

    async def _connect_once(self) -> None:
        assert self._loop is not None
        self._connect_future = self._loop.create_future()
        self._client.connect_async(
            self.config.broker_host,
            self.config.broker_port,
            self.config.keepalive_seconds,
        )
        self._client.loop_start()
        await asyncio.wait_for(self._connect_future, timeout=15)

    async def publish_json(self, topic: str, payload: dict[str, Any], *, retain: bool = False) -> None:
        await self._connected.wait()
        encoded = json.dumps(payload, separators=(",", ":"), sort_keys=True)
        await retry_async(
            lambda: self._publish_once(topic, encoded, retain=retain),
            attempts=4,
            base_delay=0.25,
            max_delay=5.0,
            retry_exceptions=(MQTTPublishError, asyncio.TimeoutError),
            logger=self.logger,
            operation_name=f"mqtt publish {topic}",
        )

    async def publish_status(self, status: str, **extra: Any) -> None:
        payload = {
            "status": status,
            "device_id": self.config.client_id,
            "ts": int(time.time()),
            **extra,
        }
        await self.publish_json(self.config.status_topic, payload, retain=True)

    async def _publish_once(self, topic: str, payload: str, *, retain: bool) -> None:
        assert self._loop is not None
        info = self._client.publish(topic, payload=payload, qos=self.config.qos, retain=retain)
        if getattr(info, "rc", 0) != 0:
            raise MQTTPublishError(f"publish returned rc={info.rc}")

        future = self._loop.create_future()
        self._pending_publishes[getattr(info, "mid")] = future
        await asyncio.wait_for(future, timeout=10)

    async def disconnect(self) -> None:
        if self._loop is None:
            return
        self._disconnect_future = self._loop.create_future()
        self._client.disconnect()
        try:
            await asyncio.wait_for(self._disconnect_future, timeout=5)
        except asyncio.TimeoutError:
            self.logger.warning("Timed out waiting for MQTT disconnect acknowledgement")
        finally:
            self._client.loop_stop()
            self._connected.clear()

    def _on_connect(self, _client: Any, _userdata: Any, _flags: Any, reason_code: Any, *_args: Any) -> None:
        rc = int(getattr(reason_code, "value", reason_code))
        if rc == 0:
            self._call_soon_threadsafe(self._mark_connected)
        else:
            self._call_soon_threadsafe(self._fail_connect, RuntimeError(f"MQTT connect failed rc={rc}"))

    def _on_disconnect(self, _client: Any, _userdata: Any, reason_code: Any, *_args: Any) -> None:
        rc = int(getattr(reason_code, "value", reason_code))
        self._call_soon_threadsafe(self._mark_disconnected, rc)

    def _on_publish(self, _client: Any, _userdata: Any, mid: int, *_args: Any) -> None:
        self._call_soon_threadsafe(self._complete_publish, mid)

    def _call_soon_threadsafe(self, callback: Any, *args: Any) -> None:
        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(callback, *args)

    def _mark_connected(self) -> None:
        self._connected.set()
        if self._connect_future and not self._connect_future.done():
            self._connect_future.set_result(None)
        self.logger.info("Connected to MQTT broker %s:%s", self.config.broker_host, self.config.broker_port)

    def _fail_connect(self, error: BaseException) -> None:
        if self._connect_future and not self._connect_future.done():
            self._connect_future.set_exception(error)

    def _mark_disconnected(self, rc: int) -> None:
        self._connected.clear()
        if self._disconnect_future and not self._disconnect_future.done():
            self._disconnect_future.set_result(None)
        if rc != 0:
            self.logger.warning("Unexpected MQTT disconnect rc=%s", rc)

    def _complete_publish(self, mid: int) -> None:
        future = self._pending_publishes.pop(mid, None)
        if future and not future.done():
            future.set_result(None)
