import pytest
from unittest.mock import patch, MagicMock
from src.pipeline.ingestion import handle_message

@patch('src.pipeline.ingestion.db_client')
@patch('src.pipeline.ingestion.logger')
def test_handle_message_valid(mock_logger, mock_db_client):
    payload = {
        "device_id": "sensor_01",
        "ppm": 850.5,
        "voltage": 1.5,
        "relay_state": True
    }
    
    handle_message(payload)
    
    mock_db_client.write_sensor_data.assert_called_once_with(
        "sensor_01", 850.5, 1.5, True
    )
    mock_logger.info.assert_called()

@patch('src.pipeline.ingestion.db_client')
@patch('src.pipeline.ingestion.logger')
def test_handle_message_incomplete(mock_logger, mock_db_client):
    payload = {
        "device_id": "sensor_01",
        "ppm": 850.5
        # missing voltage and relay_state
    }
    
    handle_message(payload)
    
    mock_db_client.write_sensor_data.assert_not_called()
    mock_logger.warning.assert_called()

@patch('src.pipeline.ingestion.db_client')
@patch('src.pipeline.ingestion.logger')
def test_handle_message_exception(mock_logger, mock_db_client):
    # Make the db client raise an exception
    mock_db_client.write_sensor_data.side_effect = Exception("DB Error")
    
    payload = {
        "device_id": "sensor_01",
        "ppm": 850.5,
        "voltage": 1.5,
        "relay_state": True
    }
    
    handle_message(payload)
    
    mock_logger.error.assert_called()
