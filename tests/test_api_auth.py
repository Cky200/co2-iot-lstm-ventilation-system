from fastapi.testclient import TestClient
from src.api.main import app
from src.api.dependencies import mock_users_db, get_password_hash

client = TestClient(app)

def test_login_success():
    # Admin user exists in mock_users_db with password 'secret'
    response = client.post(
        "/token",
        data={"username": "admin", "password": "secret"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"

def test_login_failure():
    response = client.post(
        "/token",
        data={"username": "admin", "password": "wrongpassword"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password"
