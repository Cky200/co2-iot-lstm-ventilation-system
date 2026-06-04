import sys
from unittest.mock import MagicMock

# Mock hardware modules that cause ImportErrors on non-Raspberry Pi environments (like macOS)
sys.modules['board'] = MagicMock()
sys.modules['busio'] = MagicMock()
sys.modules['digitalio'] = MagicMock()
sys.modules['adafruit_mcp3xxx'] = MagicMock()
sys.modules['adafruit_mcp3xxx.mcp3008'] = MagicMock()
sys.modules['adafruit_mcp3xxx.analog_in'] = MagicMock()

# Mock gpiozero if it also fails
sys.modules['gpiozero'] = MagicMock()
sys.modules['gpiozero.OutputDevice'] = MagicMock()
