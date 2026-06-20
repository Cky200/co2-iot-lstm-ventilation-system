import json
import logging
from unittest.mock import MagicMock, patch
# pyrefly: ignore [missing-import]
from fastapi.testclient import TestClient

from src.api.main import app
from src.api.dependencies import get_db_client
from src.utils.logger import JSONFormatter
from src.pipeline.ingestion import IngestionMetricsHandler

client = TestClient(app)


def test_json_formatter():
    # Create a mock log record
    logger = logging.getLogger("test_json_logger")
    formatter = JSONFormatter()
    
    # Standard log record
    record = logger.makeRecord(
        name="test_logger",
        level=logging.INFO,
        fn="test_file.py",
        lno=10,
        msg="Test log message",
        args=(),
        exc_info=None
    )
    
    formatted = formatter.format(record)
    log_json = json.loads(formatted)
    
    assert log_json["level"] == "INFO"
    assert log_json["logger"] == "test_logger"
    assert log_json["message"] == "Test log message"
    assert "timestamp" in log_json


def test_json_formatter_extra():
    logger = logging.getLogger("test_json_logger_extra")
    formatter = JSONFormatter()
    
    # Record with extra fields
    record = logger.makeRecord(
        name="test_logger_extra",
        level=logging.WARNING,
        fn="test_file.py",
        lno=20,
        msg="Warning log",
        args=(),
        exc_info=None
    )
    record.custom_field = "custom_value"
    
    formatted = formatter.format(record)
    log_json = json.loads(formatted)
    
    assert log_json["level"] == "WARNING"
    assert log_json["message"] == "Warning log"
    assert log_json["custom_field"] == "custom_value"


@patch("src.api.main.get_db_client")
def test_api_health_healthy(mock_get_db):
    # Mock DB client returning True for ping
    mock_db = MagicMock()
    mock_db.client.ping.return_value = True
    app.dependency_overrides[get_db_client] = lambda: mock_db
    
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["services"]["database"] == "healthy"
    
    app.dependency_overrides.clear()


@patch("src.api.main.get_db_client")
def test_api_health_unhealthy(mock_get_db):
    # Mock DB client returning False
    mock_db = MagicMock()
    mock_db.client.ping.return_value = False
    app.dependency_overrides[get_db_client] = lambda: mock_db
    
    response = client.get("/health")
    assert response.status_code == 503
    data = response.json()
    assert "unhealthy" in data["detail"]["status"]
    
    app.dependency_overrides.clear()


def test_api_metrics_endpoint():
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
    assert len(response.text) > 0


@patch("src.pipeline.ingestion.db_client")
def test_ingestion_handler_metrics(mock_db_client):
    handler = IngestionMetricsHandler.__new__(IngestionMetricsHandler)
    handler.path = "/metrics"
    handler.send_response = MagicMock()
    handler.send_header = MagicMock()
    handler.end_headers = MagicMock()
    handler.wfile = MagicMock()
    
    handler.do_GET()
    
    handler.send_response.assert_called_with(200)
    handler.wfile.write.assert_called()


@patch("src.pipeline.ingestion.db_client")
def test_ingestion_handler_health_healthy(mock_db_client):
    mock_db = MagicMock()
    mock_db.client.ping.return_value = True
    with patch("src.pipeline.ingestion.db_client", mock_db):
        handler = IngestionMetricsHandler.__new__(IngestionMetricsHandler)
        handler.path = "/health"
        handler.send_response = MagicMock()
        handler.send_header = MagicMock()
        handler.end_headers = MagicMock()
        handler.wfile = MagicMock()
        
        handler.do_GET()
        
        handler.send_response.assert_called_with(200)
        handler.wfile.write.assert_called()
        
        written_data = handler.wfile.write.call_args[0][0].decode()
        assert "healthy" in written_data


@patch("src.pipeline.ingestion.db_client")
def test_ingestion_handler_health_unhealthy(mock_db_client):
    mock_db = MagicMock()
    mock_db.client.ping.return_value = False
    with patch("src.pipeline.ingestion.db_client", mock_db):
        handler = IngestionMetricsHandler.__new__(IngestionMetricsHandler)
        handler.path = "/health"
        handler.send_response = MagicMock()
        handler.send_header = MagicMock()
        handler.end_headers = MagicMock()
        handler.wfile = MagicMock()
        
        handler.do_GET()
        
        handler.send_response.assert_called_with(503)
        handler.wfile.write.assert_called()
        
        written_data = handler.wfile.write.call_args[0][0].decode()
        assert "unhealthy" in written_data
