import json

import paho.mqtt.client as mqtt

from src.utils.logger import get_logger

logger = get_logger(__name__)

class MQTTClientWrapper:
    def __init__(self, broker_address: str = "localhost", port: int = 1883, client_id: str = "co2_client"):
        self.broker_address = broker_address
        self.port = port
        self.client_id = client_id

        # paho-mqtt 2.0+ requires CallbackAPIVersion.VERSION2, but we use >=1.6.1 in requirements
        # which might be 1.6.x or 2.0+. We'll just use the default constructor for compatibility
        # if using < 2.0, or try/except for 2.0+.
        try:
            self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id)
        except AttributeError:
            self.client = mqtt.Client(client_id=client_id)

        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect

    def _on_connect(self, client, userdata, flags, rc, *args):
        # rc might be reason_code in v2, but it coerces to int
        if int(rc) == 0:
            logger.info(f"Connected to MQTT Broker at {self.broker_address}:{self.port}")
        else:
            logger.error(f"Failed to connect to MQTT broker. Return code: {rc}")

    def _on_disconnect(self, client, userdata, rc, *args):
        logger.warning(f"Disconnected from MQTT broker. Return code: {rc}")

    def connect(self):
        try:
            self.client.connect(self.broker_address, self.port, 60)
            self.client.loop_start()
        except Exception as e:
            logger.error(f"Error connecting to MQTT Broker: {e}")

    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()

    def publish(self, topic: str, payload: dict):
        try:
            msg = json.dumps(payload)
            result = self.client.publish(topic, msg)
            status = result[0]
            if status != 0:
                logger.error(f"Failed to send message to topic {topic}")
        except Exception as e:
            logger.error(f"Error publishing to {topic}: {e}")

    def subscribe(self, topic: str, callback):
        def on_message(client, userdata, msg):
            try:
                payload = json.loads(msg.payload.decode())
                callback(payload)
            except json.JSONDecodeError:
                logger.error(f"Failed to decode JSON payload: {msg.payload}")
            except Exception as e:
                logger.error(f"Error in message callback: {e}")

        self.client.on_message = on_message
        self.client.subscribe(topic)
        logger.info(f"Subscribed to topic: {topic}")
