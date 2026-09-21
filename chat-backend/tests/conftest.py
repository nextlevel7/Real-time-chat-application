import pytest

from app import create_app
from app.extensions import db


@pytest.fixture
def app():
    test_config = {
        "TESTING": True,
        "SECRET_KEY": "test-secret-key-for-assessment-testing",
        "JWT_SECRET_KEY": "test-jwt-secret-key-for-assessment-testing",
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
    }
    app = create_app(test_config=test_config)

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_headers(client):
    register_payload = {
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "Password123!",
    }
    client.post("/api/auth/register", json=register_payload)

    login_resp = client.post(
        "/api/auth/login",
        json={
            "email": register_payload["email"],
            "password": register_payload["password"],
        },
    )
    token = login_resp.json["accessToken"]
    return {"Authorization": f"Bearer {token}"}
