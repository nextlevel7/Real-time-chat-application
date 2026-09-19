from sqlalchemy import text

from app import create_app
from app.extensions import db


def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json == {"status": "ok"}
