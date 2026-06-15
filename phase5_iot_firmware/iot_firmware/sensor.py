"""MQ-135 calibration and Raspberry Pi ADC reading."""

from __future__ import annotations

import asyncio
import json
import logging
import math
import statistics
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Protocol


class ADCReader(Protocol):
    def read_voltage(self, channel: int) -> float:
        """Read voltage for an ADC channel."""


class MCP3008Reader:
    """MCP3008 ADC reader using Adafruit CircuitPython libraries."""

    def __init__(self) -> None:
        try:
            import board
            import busio
            import digitalio
            import adafruit_mcp3xxx.mcp3008 as MCP
            from adafruit_mcp3xxx.analog_in import AnalogIn
        except ImportError as exc:  # pragma: no cover - depends on Raspberry Pi libs
            raise RuntimeError(
                "MCP3008Reader requires Raspberry Pi hardware dependencies from requirements.txt"
            ) from exc

        self._mcp_module = MCP
        spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
        cs = digitalio.DigitalInOut(board.D8)
        self._mcp = MCP.MCP3008(spi, cs)
        self._analog_in = AnalogIn
        self._channels: dict[int, object] = {}

    def read_voltage(self, channel: int) -> float:
        if channel not in self._channels:
            pin = getattr(self._mcp_module, f"P{channel}")
            self._channels[channel] = self._analog_in(self._mcp, pin)
        return float(getattr(self._channels[channel], "voltage"))


@dataclass(frozen=True)
class MQ135Calibration:
    ro_kohm: float
    clean_air_ppm: float = 400.0
    calibrated_at: float = 0.0
    clean_air_factor: float = 3.6

    @classmethod
    def load(cls, path: Path) -> "MQ135Calibration":
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls(**data)

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(self), indent=2, sort_keys=True), encoding="utf-8")


class MQ135Sensor:
    """Calibrated MQ-135 gas sensor interface."""

    CO2_CURVE_A = 116.6020682
    CO2_CURVE_B = -2.769034857

    def __init__(
        self,
        adc: ADCReader,
        *,
        channel: int = 0,
        load_resistance_kohm: float = 10.0,
        vcc: float = 5.0,
        calibration: MQ135Calibration | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        if load_resistance_kohm <= 0:
            raise ValueError("load_resistance_kohm must be positive")
        if vcc <= 0:
            raise ValueError("vcc must be positive")
        self.adc = adc
        self.channel = channel
        self.load_resistance_kohm = load_resistance_kohm
        self.vcc = vcc
        self.calibration = calibration
        self.logger = logger or logging.getLogger(__name__)

    def read_voltage(self) -> float:
        voltage = self.adc.read_voltage(self.channel)
        if not math.isfinite(voltage) or voltage <= 0:
            raise ValueError(f"Invalid MQ-135 voltage reading: {voltage}")
        if voltage >= self.vcc:
            raise ValueError(f"MQ-135 voltage {voltage} must be below VCC {self.vcc}")
        return voltage

    def sensor_resistance_kohm(self, voltage: float | None = None) -> float:
        reading = self.read_voltage() if voltage is None else voltage
        return self.load_resistance_kohm * ((self.vcc - reading) / reading)

    def co2_ppm(self) -> float:
        if self.calibration is None:
            raise RuntimeError("MQ-135 calibration is required before reading CO2 PPM")
        return self.co2_ppm_from_voltage(self.read_voltage())

    def co2_ppm_from_voltage(self, voltage: float) -> float:
        if self.calibration is None:
            raise RuntimeError("MQ-135 calibration is required before reading CO2 PPM")
        rs_ro_ratio = self.sensor_resistance_kohm(voltage) / self.calibration.ro_kohm
        ppm = self.CO2_CURVE_A * (rs_ro_ratio ** self.CO2_CURVE_B)
        return round(max(ppm, 0.0), 2)

    async def sample(self, *, sample_count: int = 8, sample_delay_seconds: float = 0.05) -> dict[str, float]:
        voltages: list[float] = []
        ppms: list[float] = []
        for _ in range(sample_count):
            voltage = self.read_voltage()
            voltages.append(voltage)
            ppms.append(self.co2_ppm_from_voltage(voltage))
            await asyncio.sleep(sample_delay_seconds)
        return {
            "voltage": round(statistics.fmean(voltages), 4),
            "co2_ppm": round(statistics.fmean(ppms), 2),
        }

    async def calibrate_clean_air(
        self,
        *,
        sample_count: int = 60,
        sample_delay_seconds: float = 1.0,
        clean_air_ppm: float = 400.0,
        clean_air_factor: float = 3.6,
    ) -> MQ135Calibration:
        if sample_count < 3:
            raise ValueError("sample_count must be at least 3")
        resistances = []
        for _ in range(sample_count):
            resistances.append(self.sensor_resistance_kohm())
            await asyncio.sleep(sample_delay_seconds)
        ro = statistics.median(resistances) / clean_air_factor
        self.calibration = MQ135Calibration(
            ro_kohm=round(ro, 6),
            clean_air_ppm=clean_air_ppm,
            clean_air_factor=clean_air_factor,
            calibrated_at=time.time(),
        )
        self.logger.info("MQ-135 calibrated: Ro=%.4fkOhm", self.calibration.ro_kohm)
        return self.calibration
