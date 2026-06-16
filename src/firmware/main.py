import os
import sys
import time

from src.hardware.actuator import VentilationController
from src.hardware.sensor import MQ135Sensor
from src.pipeline.mqtt_client import MQTTClientWrapper
from src.utils.config import (
    ADC_SPI_DEVICE,
    ADC_SPI_PORT,
    CO2_DANGER_THRESHOLD,
    CO2_SAFE_THRESHOLD,
    MQ135_ADC_CHANNEL,
    READ_INTERVAL,
    RELAY_GPIO_PIN,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)

MQTT_TOPIC = os.getenv("MQTT_TOPIC", "iot/co2/sensor1")
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
DEVICE_ID = os.getenv("DEVICE_ID", "rpi_sensor_01")

def main():
    logger.info("Starting Firmware - CO2 Monitoring System")

    try:
        sensor = MQ135Sensor(
            spi_port=ADC_SPI_PORT,
            spi_device=ADC_SPI_DEVICE,
            channel=MQ135_ADC_CHANNEL
        )
        ventilation = VentilationController(pin=RELAY_GPIO_PIN)

        # Initialize MQTT Client
        mqtt_client = MQTTClientWrapper(broker_address=MQTT_BROKER, client_id=f"fw_{DEVICE_ID}")
        mqtt_client.connect()

    except Exception as e:
        logger.error(f"Hardware or Broker initialization failed: {e}. Exiting.")
        sys.exit(1)

    logger.info(f"Target Safe Threshold: {CO2_SAFE_THRESHOLD} ppm")
    logger.info(f"Target Danger Threshold: {CO2_DANGER_THRESHOLD} ppm")

    try:
        while True:
            ppm = sensor.estimate_co2_ppm()
            voltage = sensor.read_voltage()

            logger.info(f"Sensor Reading -> Voltage: {voltage:.2f}V | Estimated CO2: {ppm:.2f} ppm")

            # Simple Hysteresis Control Logic
            if ppm >= CO2_DANGER_THRESHOLD and not ventilation.is_on:
                logger.warning(f"CO2 levels high ({ppm:.2f} ppm). Turning on ventilation.")
                ventilation.turn_on()
            elif ppm <= CO2_SAFE_THRESHOLD and ventilation.is_on:
                logger.info(f"CO2 levels normalized ({ppm:.2f} ppm). Turning off ventilation.")
                ventilation.turn_off()

            # Publish telemetry data to MQTT broker
            payload = {
                "device_id": DEVICE_ID,
                "ppm": ppm,
                "voltage": voltage,
                "relay_state": ventilation.is_on
            }
            mqtt_client.publish(MQTT_TOPIC, payload)

            time.sleep(READ_INTERVAL)

    except KeyboardInterrupt:
        logger.info("System interrupted by user. Shutting down...")
    except Exception as e:
        logger.error(f"Unexpected error in main loop: {e}")
    finally:
        # Cleanup
        ventilation.turn_off()
        mqtt_client.disconnect()
        logger.info("System shutdown complete.")

if __name__ == "__main__":
    main()
