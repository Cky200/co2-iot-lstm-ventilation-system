from fastapi.testclient import TestClient

from src.api.dependencies import get_current_active_user, get_db_client
from src.api.main import app

client = TestClient(app)

# Mocking auth dependency
async def override_get_current_active_user():
    return {"username": "admin", "email": "admin@example.com"}

class MockDBClient:
    def query_recent_data(self, minutes_back: int):
        return [
            {
                "time": "2026-06-04T12:00:00Z",
                "ppm": 850.5,
                "voltage": 1.5,
                "relay_state": True
            }
        ]

    def close(self):
        pass

def override_get_db_client():
    yield MockDBClient()

app.dependency_overrides[get_current_active_user] = override_get_current_active_user
app.dependency_overrides[get_db_client] = override_get_db_client

def test_get_co2_history_authenticated():
    response = client.get("/api/v1/co2/history?minutes_back=60")
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["ppm"] == 850.5

def test_get_co2_history_unauthenticated():
    # Remove auth override to test 401
    app.dependency_overrides.pop(get_current_active_user)
    response = client.get("/api/v1/co2/history")
    assert response.status_code == 401
