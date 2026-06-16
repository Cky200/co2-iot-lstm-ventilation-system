import asyncio
import os

import paho.mqtt.client as mqtt
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from src.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()

MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "iot/co2/sensor1")

@router.websocket("/ws/co2/stream")
async def co2_websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket client connected.")

    # We use a queue to pass messages from MQTT thread to FastAPI async loop
    message_queue: asyncio.Queue = asyncio.Queue()

    def on_message(client, userdata, msg):
        try:
            payload = msg.payload.decode()
            # Push to the async queue from the sync MQTT callback using event loop
            asyncio.run_coroutine_threadsafe(message_queue.put(payload), loop)
        except Exception as e:
            logger.error(f"Error processing MQTT msg for WS: {e}")

    loop = asyncio.get_running_loop()

    # Initialize MQTT client just for this WS connection
    mqtt_client = mqtt.Client(client_id=f"ws_client_{id(websocket)}")
    mqtt_client.on_message = on_message

    try:
        mqtt_client.connect(MQTT_BROKER, 1883, 60)
        mqtt_client.subscribe(MQTT_TOPIC)
        mqtt_client.loop_start()

        while True:
            # Wait for messages from the queue and send them over WS
            data = await message_queue.get()
            await websocket.send_text(data)

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected.")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
