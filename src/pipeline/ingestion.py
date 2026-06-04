import time
import os
import signal
import sys
from src.pipeline.mqtt_client import MQTTClientWrapper
from src.pipeline.db_client import InfluxDBWrapper
from src.utils.logger import get_logger

logger = get_logger(__name__)

MQTT_TOPIC = os.getenv("MQTT_TOPIC", "iot/co2/sensor1")
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")

db_client = None
mqtt_client = None

def handle_message(payload: dict):
    """Callback function when an MQTT message is received."""
    try:
        device_id = payload.get("device_id", "unknown")
        ppm = payload.get("ppm")
        voltage = payload.get("voltage")
        relay_state = payload.get("relay_state")
        
        if ppm is not None and voltage is not None:
            logger.info(f"Ingesting: Device={device_id}, PPM={ppm}, Relay={relay_state}")
            db_client.write_sensor_data(device_id, ppm, voltage, relay_state)
        else:
            logger.warning(f"Incomplete payload received: {payload}")
    except Exception as e:
        logger.error(f"Error handling message: {e}")

def shutdown(signum, frame):
    logger.info("Shutting down ingestion service...")
    if mqtt_client:
        mqtt_client.disconnect()
    if db_client:
        db_client.close()
    sys.exit(0)

def main():
    global db_client, mqtt_client
    
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)
    
    try:
        db_client = InfluxDBWrapper()
        mqtt_client = MQTTClientWrapper(broker_address=MQTT_BROKER, client_id="ingestion_service")
        
        mqtt_client.connect()
        mqtt_client.subscribe(MQTT_TOPIC, handle_message)
        
        logger.info(f"Ingestion service started. Subscribed to {MQTT_TOPIC}")
        
        # Keep main thread alive
        while True:
            time.sleep(1)
            
    except Exception as e:
        logger.error(f"Ingestion service crashed: {e}")
        shutdown(None, None)

if __name__ == "__main__":
    main()
