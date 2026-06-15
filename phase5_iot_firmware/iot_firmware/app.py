"""Main asynchronous firmware runtime."""

from __future__ import annotations

import asyncio
import logging
import signal
import time
from contextlib import suppress

from .config import AppConfig
from .mqtt_async import AsyncMQTTPublisher
from .ota import OTAUpdater
from .sensor import MCP3008Reader, MQ135Calibration, MQ135Sensor
from .watchdog import AsyncWatchdog

logger = logging.getLogger(__name__)


class FirmwareApp:
    def __init__(
        self,
        config: AppConfig,
        *,
        sensor: MQ135Sensor | None = None,
        mqtt_publisher: AsyncMQTTPublisher | None = None,
        ota_updater: OTAUpdater | None = None,
        watchdog: AsyncWatchdog | None = None,
    ) -> None:
        self.config = config
        self.sensor = sensor or self._build_sensor()
        self.mqtt = mqtt_publisher or AsyncMQTTPublisher(config.mqtt)
        self.ota = ota_updater or OTAUpdater(
            current_version=config.ota.current_version,
            staging_dir=config.ota.staging_dir,
        )
        self.watchdog = watchdog or AsyncWatchdog(timeout_seconds=config.watchdog_timeout_seconds)
        self._stop_event = asyncio.Event()

    def _build_sensor(self) -> MQ135Sensor:
        calibration = None
        if self.config.sensor.calibration_file.exists():
            calibration = MQ135Calibration.load(self.config.sensor.calibration_file)
        adc = MCP3008Reader()
        return MQ135Sensor(
            adc,
            channel=self.config.sensor.adc_channel,
            load_resistance_kohm=self.config.sensor.load_resistance_kohm,
            vcc=self.config.sensor.vcc,
            calibration=calibration,
        )

    async def run(self) -> None:
        self._install_signal_handlers()
        self.watchdog.register("main-loop")
        await self.watchdog.start()
        await self.mqtt.connect()
        await self.mqtt.publish_status("online", firmware_version=self.config.ota.current_version)

        ota_task = None
        if self.config.ota.enabled and self.config.ota.manifest_url:
            ota_task = asyncio.create_task(self._ota_loop(), name="ota-loop")

        try:
            while not self._stop_event.is_set():
                await self._publish_sensor_sample()
                self.watchdog.feed("main-loop")
                with suppress(asyncio.TimeoutError):
                    await asyncio.wait_for(
                        self._stop_event.wait(),
                        timeout=self.config.read_interval_seconds,
                    )
        finally:
            if ota_task:
                ota_task.cancel()
                with suppress(asyncio.CancelledError):
                    await ota_task
            await self._shutdown()

    async def _publish_sensor_sample(self) -> None:
        reading = await self.sensor.sample(
            sample_count=self.config.sensor.sample_count,
            sample_delay_seconds=self.config.sensor.sample_delay_seconds,
        )
        payload = {
            "device_id": self.config.device_id,
            "ts": int(time.time()),
            "co2_ppm": reading["co2_ppm"],
            "voltage": reading["voltage"],
        }
        await self.mqtt.publish_json(self.config.mqtt.telemetry_topic, payload)

    async def _ota_loop(self) -> None:
        assert self.config.ota.manifest_url is not None
        self.watchdog.register("ota-loop")
        while not self._stop_event.is_set():
            try:
                updated = await self.ota.apply_if_available(self.config.ota.manifest_url)
                if updated:
                    await self.mqtt.publish_status("update_applied")
                    self.request_stop()
            except Exception:
                logger.exception("OTA check failed")
            finally:
                self.watchdog.feed("ota-loop")
            with suppress(asyncio.TimeoutError):
                await asyncio.wait_for(
                    self._stop_event.wait(),
                    timeout=self.config.ota.check_interval_seconds,
                )

    async def _shutdown(self) -> None:
        try:
            await self.mqtt.publish_status("offline")
        except Exception:
            logger.exception("Failed to publish offline status")
        await self.mqtt.disconnect()
        await self.watchdog.stop()

    def request_stop(self) -> None:
        self._stop_event.set()

    def _install_signal_handlers(self) -> None:
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            with suppress(NotImplementedError):
                loop.add_signal_handler(sig, self.request_stop)
