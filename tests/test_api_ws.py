from fastapi.testclient import TestClient
from src.api.main import app
from unittest.mock import patch, MagicMock

client = TestClient(app)

@patch('src.api.routers.websocket.mqtt.Client')
def test_websocket_stream(mock_mqtt_client):
    # This is a bit tricky to fully mock because it involves async Queues and threads,
    # but we can verify the connection accepts.
    
    # We will simulate a connection and immediate disconnect to ensure the endpoint
    # does not crash on startup.
    with client.websocket_connect("/ws/co2/stream") as websocket:
        # Just connecting should call mqtt connect and subscribe
        assert mock_mqtt_client.called
