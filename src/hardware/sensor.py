import board
import busio
import digitalio
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn
from src.utils.logger import get_logger

logger = get_logger(__name__)

class MQ135Sensor:
    """
    Interfaces with the MQ-135 sensor via an MCP3008 ADC over SPI.
    """
    def __init__(self, spi_port: int = 0, spi_device: int = 0, channel: int = 0):
        self.channel = channel
        try:
            # Create SPI bus
            self.spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
            # Create CS (Chip Select)
            self.cs = digitalio.DigitalInOut(board.D8)
            # Create MCP object
            self.mcp = MCP.MCP3008(self.spi, self.cs)
            # Create analog input channel
            self.chan = AnalogIn(self.mcp, getattr(MCP, f"P{self.channel}"))
            logger.info("MQ135Sensor initialized successfully via MCP3008.")
        except Exception as e:
            logger.error(f"Failed to initialize MQ135Sensor: {e}")
            raise

    def read_raw(self) -> int:
        """Reads the raw 10-bit ADC value (0-1023) or 16-bit mapped value depending on library."""
        try:
            # CircuitPython mcp3xxx library maps 10-bit to 16-bit (0-65535)
            # We can use chan.value for 16-bit or map it back if needed.
            # Voltage can be read directly via chan.voltage
            return self.chan.value
        except Exception as e:
            logger.error(f"Error reading raw value from MQ135: {e}")
            return -1

    def read_voltage(self) -> float:
        """Reads the voltage value."""
        try:
            return self.chan.voltage
        except Exception as e:
            logger.error(f"Error reading voltage from MQ135: {e}")
            return -1.0

    def estimate_co2_ppm(self) -> float:
        """
        Estimates CO2 PPM based on the voltage read.
        Note: This is a rough estimation. For production accuracy,
        a proper calibration curve (using Ro and RL) is required.
        """
        voltage = self.read_voltage()
        if voltage < 0:
            return -1.0
        
        # Placeholder for actual R0 calibration and PPM calculation formula.
        # Assuming a linear approximation for demonstration.
        # In a real scenario, use Ro, Rs, and the sensor datasheet curve.
        ppm = (voltage / 3.3) * 1000 + 400 # Base atmospheric CO2 is ~400ppm
        return round(ppm, 2)
