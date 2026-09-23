from uuid import UUID

import pytest
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.rooms.models import ChatRoom, RoomMembership
from app.users.model import User


def test_create_and_list_rooms(client, auth_headers):
    res = client.post("/api/rooms", json={"name": "Engineering Lounge"}, headers=auth_headers)
    assert res.status_code == 201
    assert res.json["room"]["name"] == "Engineering Lounge"
    assert res.json["room"]["isMember"] is True

    list_res = client.get("/api/rooms", headers=auth_headers)
    assert list_res.status_code == 200
    assert len(list_res.json["rooms"]) >= 1


def test_join_and_leave_room(client, auth_headers):
    # User 1 creates room
    room_id = client.post(
        "/api/rooms", json={"name": "Gaming Hub"}, headers=auth_headers
    ).json["room"]["id"]

    # User 2 registers and logs in
    client.post(
        "/api/auth/register",
        json={"username": "gamer", "email": "gamer@example.com", "password": "Password123!"},
    )
    login_res = client.post(
        "/api/auth/login",
        json={"email": "gamer@example.com", "password": "Password123!"},
    )
    headers2 = {"Authorization": f"Bearer {login_res.json['accessToken']}"}

    # User 2 joins room
    join_res = client.post(f"/api/rooms/{room_id}/join", headers=headers2)
    assert join_res.status_code == 200
    assert join_res.json["status"] == "joined"

    # Duplicate join -> 409
    dup_res = client.post(f"/api/rooms/{room_id}/join", headers=headers2)
    assert dup_res.status_code == 409
    assert dup_res.json["error"]["code"] == "ALREADY_MEMBER"

    # Member list includes both
    members = client.get(f"/api/rooms/{room_id}/members", headers=headers2).json["members"]
    usernames = [m["username"] for m in members]
    assert "testuser" in usernames and "gamer" in usernames

    # User 2 leaves room
    leave_res = client.post(f"/api/rooms/{room_id}/leave", headers=headers2)
    assert leave_res.status_code == 200
    assert leave_res.json["status"] == "left"


def test_room_membership_integrity_and_access(app, client, auth_headers):
    room_id = client.post(
        "/api/rooms", json={"name": "Private Club"}, headers=auth_headers
    ).json["room"]["id"]

    # Register user 2
    client.post(
        "/api/auth/register",
        json={"username": "stranger", "email": "stranger@example.com", "password": "Password123!"},
    )
    login_res = client.post(
        "/api/auth/login",
        json={"email": "stranger@example.com", "password": "Password123!"},
    )
    headers2 = {"Authorization": f"Bearer {login_res.json['accessToken']}"}

    # Non-member cannot access private room
    res = client.get(f"/api/rooms/{room_id}", headers=headers2)
    assert res.status_code == 403
    assert res.json["error"]["code"] == "ROOM_ACCESS_DENIED"

    # Database level composite primary key integrity
    with app.app_context():
        user = db.session.scalar(db.select(User).where(User.username == "testuser"))
        # Attempt duplicate RoomMembership insertion directly at DB level
        dup_membership = RoomMembership(room_id=UUID(room_id), user_id=user.id)
        db.session.add(dup_membership)
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()
