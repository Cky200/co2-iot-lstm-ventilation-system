import json
import os
import signal
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from src.pipeline.db_client import InfluxDBWrapper
from src.pipeline.mqtt_client import MQTTClientWrapper
from src.utils.logger import get_logger
from src.utils.metrics import (
    CO2_LEVEL_PPM,
    CO2_READINGS_TOTAL,
    VENTILATION_RELAY_STATUS,
    CO2_VOLTAGE_VOLTS
)

logger = get_logger(__name__)

MQTT_TOPIC = os.getenv("MQTT_TOPIC", "iot/co2/sensor1")
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")

db_client = None
mqtt_client = None


class IngestionMetricsHandler(BaseHTTPRequestHandler):
    """
    HTTP Handler to serve Prometheus metrics and health check responses for the Ingestion Daemon.
    """
    def log_message(self, format, *args):
        # Prevent default log spam to stderr/stdout on every scrape
        pass

    def do_GET(self):
        if self.path == "/metrics":
            self.send_response(200)
            self.send_header("Content-Type", CONTENT_TYPE_LATEST)
            self.end_headers()
            self.wfile.write(generate_latest())
        elif self.path == "/health":
            db_healthy = False
            if db_client is not None:
                try:
                    if db_client.client.ping():
                        db_healthy = True
                except Exception:
                    pass
            
            if db_healthy:
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(
                    json.dumps({
                        "status": "healthy",
                        "database": "connected",
                        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                    }).encode()
                )
            else:
                self.send_response(503)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(
                    json.dumps({
                        "status": "unhealthy",
                        "database": "disconnected",
                        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                    }).encode()
                )
        else:
            self.send_response(404)
            self.end_headers()


def start_metrics_server(port: int = 8001):
    """Starts the Prometheus scraping and health check server."""
    server = HTTPServer(("0.0.0.0", port), IngestionMetricsHandler)
    logger.info(f"Ingestion metrics & health server running on port {port}")
    server.serve_forever()


def handle_message(payload: dict):
    """Callback function when an MQTT message is received."""
    try:
        device_id = payload.get("device_id", "unknown")
        ppm = payload.get("ppm")
        voltage = payload.get("voltage")
        relay_state = payload.get("relay_state")

        if ppm is not None and voltage is not None:
            logger.info(f"Ingesting: Device={device_id}, PPM={ppm}, Relay={relay_state}")
            
            # Record custom Prometheus metrics
            CO2_LEVEL_PPM.labels(device_id=device_id).set(ppm)
            CO2_READINGS_TOTAL.labels(device_id=device_id).inc()
            CO2_VOLTAGE_VOLTS.labels(device_id=device_id).set(voltage)
            if relay_state is not None:
                rel_val = 1 if relay_state else 0
                VENTILATION_RELAY_STATUS.labels(device_id=device_id).set(rel_val)

            if db_client is not None:
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

    # Start the Prometheus exporter and health server thread
    metrics_port = int(os.getenv("METRICS_PORT", "8001"))
    server_thread = threading.Thread(
        target=start_metrics_server,
        args=(metrics_port,),
        daemon=True
    )
    server_thread.start()

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
