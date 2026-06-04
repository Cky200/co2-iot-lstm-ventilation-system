import os

# ADC Configuration (MCP3008)
ADC_SPI_PORT = int(os.getenv("ADC_SPI_PORT", 0))
ADC_SPI_DEVICE = int(os.getenv("ADC_SPI_DEVICE", 0))
MQ135_ADC_CHANNEL = int(os.getenv("MQ135_ADC_CHANNEL", 0)) # CH0

# Actuator Configuration
RELAY_GPIO_PIN = int(os.getenv("RELAY_GPIO_PIN", 17))

# Application Thresholds (in PPM)
CO2_SAFE_THRESHOLD = float(os.getenv("CO2_SAFE_THRESHOLD", 800.0))
CO2_DANGER_THRESHOLD = float(os.getenv("CO2_DANGER_THRESHOLD", 1200.0))

# Reading Intervals (Seconds)
READ_INTERVAL = float(os.getenv("READ_INTERVAL", 2.0))
