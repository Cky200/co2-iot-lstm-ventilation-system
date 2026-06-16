from __future__ import annotations

import pytest

from ventilation_control.models import AirQualityState
from ventilation_control.thresholds import ThresholdConfig, ThresholdManager


def test_thresholds_classify_co2_levels():
    manager = ThresholdManager(ThresholdConfig(target_ppm=800, elevated_ppm=900, high_ppm=1200, critical_ppm=1800))

    assert manager.classify(700) == AirQualityState.NORMAL
    assert manager.classify(950) == AirQualityState.ELEVATED
    assert manager.classify(1300) == AirQualityState.HIGH
    assert manager.classify(1900) == AirQualityState.CRITICAL


def test_threshold_hysteresis_prevents_flapping():
    manager = ThresholdManager(
        ThresholdConfig(target_ppm=800, elevated_ppm=900, high_ppm=1200, critical_ppm=1800, hysteresis_ppm=100)
    )

    assert manager.classify(950) == AirQualityState.ELEVATED
    assert manager.classify(850) == AirQualityState.ELEVATED
    assert manager.classify(699) == AirQualityState.NORMAL


def test_threshold_config_rejects_invalid_order():
    with pytest.raises(ValueError):
        ThresholdConfig(target_ppm=900, elevated_ppm=800, high_ppm=1200, critical_ppm=1800)
