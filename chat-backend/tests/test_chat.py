from uuid import UUID

from flask_jwt_extended import create_access_token

from app.auth.schemas import Register
from app.auth.service import register
from app.extensions import socketio
from app.messages.cassandra import clear_test_messages
from app.rooms.schemas import CreateRoom
from app.rooms.service import create_room, join_room


def test_message_history_rest(client, auth_headers):
    clear_test_messages()
    room_id = client.post(
        "/api/rooms", json={"name": "Dev Chat"}, headers=auth_headers
    ).json["room"]["id"]

    # Post message
    msg_res = client.post(
        f"/api/rooms/{room_id}/messages",
        json={"content": "Hello world!"},
        headers=auth_headers,
    )
    assert msg_res.status_code == 201
    assert msg_res.json["message"]["content"] == "Hello world!"
    assert msg_res.json["message"]["senderUsername"] == "testuser"

    # Get history
    history = client.get(f"/api/rooms/{room_id}/messages", headers=auth_headers).json["messages"]
    assert len(history) == 1
    assert history[0]["content"] == "Hello world!"


def test_websocket_realtime_chat_and_presence(app):
    clear_test_messages()
    with app.app_context():
        # Setup 2 users and a room
        u1 = register(Register(username="chatuser1", email="c1@test.com", password="Password123!"))
        u2 = register(Register(username="chatuser2", email="c2@test.com", password="Password123!"))
        room = create_room(UUID(u1["id"]), CreateRoom(name="Realtime Lounge"))
        join_room(UUID(u2["id"]), UUID(room["id"]))

        token1 = create_access_token(identity=u1["id"])
        token2 = create_access_token(identity=u2["id"])

        client1 = socketio.test_client(app, auth={"token": token1})
        client2 = socketio.test_client(app, auth={"token": token2})
        assert client1.is_connected()
        assert client2.is_connected()

        # Both join room channel
        client1.emit("join_room", {"roomId": room["id"]})
        client2.emit("join_room", {"roomId": room["id"]})
        client1.get_received()
        client2.get_received()

        # Client 1 sends real-time message
        client1.emit("send_message", {"roomId": room["id"], "content": "Live socket message"})
        received = client2.get_received()
        msg_events = [e for e in received if e["name"] == "receive_message"]
        assert len(msg_events) == 1
        assert msg_events[0]["args"][0]["content"] == "Live socket message"
        assert msg_events[0]["args"][0]["senderUsername"] == "chatuser1"

        # Client 1 emits typing indicator
        client1.emit("typing", {"roomId": room["id"], "isTyping": True})
        typing_events = [e for e in client2.get_received() if e["name"] == "user_typing"]
        assert len(typing_events) == 1
        assert typing_events[0]["args"][0]["username"] == "chatuser1"
        assert typing_events[0]["args"][0]["isTyping"] is True

        client1.disconnect()
        client2.disconnect()
