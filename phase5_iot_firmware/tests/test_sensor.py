from __future__ import annotations

import asyncio

import pytest
from iot_firmware.sensor import MQ135Calibration, MQ135Sensor


class FakeADC:
    def __init__(self, voltages: list[float]) -> None:
        self.voltages = voltages
        self.index = 0

    def read_voltage(self, channel: int) -> float:
        assert channel == 0
        value = self.voltages[min(self.index, len(self.voltages) - 1)]
        self.index += 1
        return value


def test_mq135_calibration_round_trip(tmp_path):
    calibration = MQ135Calibration(ro_kohm=9.123, clean_air_ppm=410, calibrated_at=123.0)
    path = tmp_path / "calibration.json"

    calibration.save(path)

    assert MQ135Calibration.load(path) == calibration


def test_mq135_estimates_ppm_from_calibrated_sensor():
    sensor = MQ135Sensor(
        FakeADC([2.0]),
        load_resistance_kohm=10.0,
        vcc=5.0,
        calibration=MQ135Calibration(ro_kohm=15.0),
    )

    ppm = sensor.co2_ppm()

    assert ppm == pytest.approx(116.60, abs=0.1)


def test_mq135_clean_air_calibration_uses_median_resistance():
    sensor = MQ135Sensor(FakeADC([2.0, 2.1, 2.0, 2.2]), load_resistance_kohm=10.0, vcc=5.0)

    calibration = asyncio.run(sensor.calibrate_clean_air(sample_count=4, sample_delay_seconds=0))

    assert calibration.ro_kohm > 0
    assert sensor.calibration == calibration


def test_mq135_rejects_invalid_voltage():
    sensor = MQ135Sensor(FakeADC([0.0]), vcc=5.0)

    with pytest.raises(ValueError):
        sensor.read_voltage()
