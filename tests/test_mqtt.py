from unittest.mock import patch

from src.pipeline.mqtt_client import MQTTClientWrapper


@patch("src.pipeline.mqtt_client.mqtt.Client")
def test_mqtt_client_initialization(mock_mqtt):
    client = MQTTClientWrapper(broker_address="test_broker", port=1883, client_id="test_id")
    assert client.broker_address == "test_broker"
    assert client.port == 1883
    assert client.client_id == "test_id"
    mock_mqtt.assert_called_once()

@patch("src.pipeline.mqtt_client.mqtt.Client")
def test_mqtt_connect(mock_mqtt):
    client = MQTTClientWrapper()
    client.connect()
    client.client.connect.assert_called_with("localhost", 1883, 60)
    client.client.loop_start.assert_called_once()

@patch("src.pipeline.mqtt_client.mqtt.Client")
def test_mqtt_publish(mock_mqtt):
    client = MQTTClientWrapper()
    # Mock publish to return success (status 0)
    client.client.publish.return_value = (0, 1)

    payload = {"test": "data"}
    client.publish("test/topic", payload)

    client.client.publish.assert_called_with("test/topic", '{"test": "data"}')
