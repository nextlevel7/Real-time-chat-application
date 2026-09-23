import pytest
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.users.model import User


def test_register_and_login(client):
    # User registration
    res = client.post(
        "/api/auth/register",
        json={"username": "alice", "email": "alice@example.com", "password": "Password123!"},
    )
    assert res.status_code == 201
    assert res.json["user"]["username"] == "alice"
    assert "password_hash" not in res.json["user"]

    # Duplicate registration check
    dup = client.post(
        "/api/auth/register",
        json={"username": "alice", "email": "alice2@example.com", "password": "Password123!"},
    )
    assert dup.status_code == 409
    assert dup.json["error"]["code"] == "ACCOUNT_EXISTS"

    # User login
    login = client.post(
        "/api/auth/login",
        json={"email": "alice@example.com", "password": "Password123!"},
    )
    assert login.status_code == 200
    token = login.json["accessToken"]
    assert token

    # Check authenticated session
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json["user"]["username"] == "alice"


def test_login_invalid_credentials(client):
    client.post(
        "/api/auth/register",
        json={"username": "bob", "email": "bob@example.com", "password": "Password123!"},
    )
    res = client.post(
        "/api/auth/login",
        json={"email": "bob@example.com", "password": "WrongPassword!"},
    )
    assert res.status_code == 401
    assert res.json["error"]["code"] == "INVALID_CREDENTIALS"


def test_user_model_bcrypt_and_integrity(app):
    with app.app_context():
        user = User(username="hashuser", email="hash@example.com")
        user.set_password("SecretPassword123!")
        db.session.add(user)
        db.session.commit()

        # Bcrypt hash verification
        assert user.password_hash.startswith("$2b$")
        assert user.check_password("SecretPassword123!") is True
        assert user.check_password("WrongPassword") is False

        # Database unique constraint check
        dup_user = User(username="hashuser", email="other@example.com")
        dup_user.set_password("SecretPassword123!")
        db.session.add(dup_user)
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()
