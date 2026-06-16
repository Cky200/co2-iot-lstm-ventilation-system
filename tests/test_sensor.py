from unittest.mock import MagicMock, patch

import pytest

from src.hardware.sensor import MQ135Sensor


@pytest.fixture
def mock_sensor():
    with patch('src.hardware.sensor.busio.SPI'), \
         patch('src.hardware.sensor.digitalio.DigitalInOut'), \
         patch('src.hardware.sensor.MCP.MCP3008'), \
         patch('src.hardware.sensor.AnalogIn') as mock_analog_in:

        # Setup mock return values for AnalogIn
        mock_chan = MagicMock()
        mock_chan.value = 32768  # mid-point of 16-bit
        mock_chan.voltage = 1.65 # mid-point of 3.3V
        mock_analog_in.return_value = mock_chan

        sensor = MQ135Sensor(spi_port=0, spi_device=0, channel=0)
        yield sensor, mock_chan

def test_sensor_initialization(mock_sensor):
    sensor, _ = mock_sensor
    assert sensor.channel == 0
    assert sensor.chan is not None

def test_read_raw(mock_sensor):
    sensor, mock_chan = mock_sensor
    assert sensor.read_raw() == 32768

def test_read_voltage(mock_sensor):
    sensor, mock_chan = mock_sensor
    assert sensor.read_voltage() == 1.65

def test_estimate_co2_ppm(mock_sensor):
    sensor, mock_chan = mock_sensor
    # Formula: (1.65 / 3.3) * 1000 + 400 = 500 + 400 = 900
    assert sensor.estimate_co2_ppm() == 900.0

def test_read_voltage_error_handling(mock_sensor):
    sensor, mock_chan = mock_sensor
    from unittest.mock import PropertyMock
    type(mock_chan).voltage = PropertyMock(side_effect=Exception("Read error"))

    assert sensor.read_voltage() == -1.0
