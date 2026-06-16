from unittest.mock import MagicMock, patch

import pytest

from src.hardware.actuator import VentilationController


@pytest.fixture
def mock_ventilation():
    with patch('src.hardware.actuator.OutputDevice') as mock_output_device:
        # Mock instance returned by OutputDevice
        mock_relay = MagicMock()
        mock_output_device.return_value = mock_relay

        controller = VentilationController(pin=17)
        yield controller, mock_relay

def test_ventilation_initialization(mock_ventilation):
    controller, _ = mock_ventilation
    assert controller.is_on is False

def test_turn_on(mock_ventilation):
    controller, mock_relay = mock_ventilation
    controller.turn_on()
    assert controller.is_on is True
    mock_relay.on.assert_called_once()

def test_turn_off(mock_ventilation):
    controller, mock_relay = mock_ventilation
    # First turn on
    controller.turn_on()
    mock_relay.on.assert_called_once()

    # Then turn off
    controller.turn_off()
    assert controller.is_on is False
    mock_relay.off.assert_called_once()

def test_turn_on_idempotent(mock_ventilation):
    controller, mock_relay = mock_ventilation
    controller.turn_on()
    controller.turn_on() # Should not call relay.on() again
    assert mock_relay.on.call_count == 1
