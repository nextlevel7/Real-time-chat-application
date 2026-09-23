from uuid import UUID

from flask import request, session
from flask_jwt_extended import decode_token
from flask_socketio import emit, join_room, leave_room

from app.common.errors import AppError
from app.extensions import db
from app.messages.cassandra import save_message
from app.rooms.service import require_member
from app.users.model import User


def register_socket_events(socketio):
    @socketio.on("connect")
    def handle_connect(auth=None):
        token = (auth or {}).get("token")
        if not token:
            header = request.headers.get("Authorization", "")
            if header.startswith("Bearer "):
                token = header.split(" ")[1]

        if not token:
            return False

        try:
            payload = decode_token(token)
            user = db.session.get(User, UUID(payload["sub"]))
            if not user:
                return False
            session["user_id"] = str(user.id)
            session["username"] = user.username
            return True
        except Exception:  # noqa: BLE001 - Reject socket connection if token is malformed or invalid
            return False

    @socketio.on("join_room")
    def handle_join_room(data):
        user_id = session.get("user_id")
        room_id = (data or {}).get("roomId")
        if not user_id or not room_id:
            emit("error", {"code": "INVALID_REQUEST", "message": "roomId is required"})
            return

        try:
            room_uuid = UUID(room_id)
            require_member(UUID(user_id), room_uuid)
        except AppError as e:
            emit("error", {"code": e.code, "message": e.message})
            return
        except ValueError:
            emit("error", {"code": "INVALID_REQUEST", "message": "Invalid roomId"})
            return

        join_room(str(room_uuid))
        emit(
            "user_joined",
            {"roomId": str(room_uuid), "username": session.get("username")},
            to=str(room_uuid),
            include_self=False,
        )

    @socketio.on("leave_room")
    def handle_leave_room(data):
        room_id = (data or {}).get("roomId")
        if room_id:
            leave_room(room_id)
            emit(
                "user_left",
                {"roomId": room_id, "username": session.get("username")},
                to=room_id,
                include_self=False,
            )

    @socketio.on("send_message")
    def handle_send_message(data):
        user_id = session.get("user_id")
        username = session.get("username")
        room_id = (data or {}).get("roomId")
        content = ((data or {}).get("content") or "").strip()

        if not user_id or not username:
            emit("error", {"code": "UNAUTHORIZED", "message": "Not authenticated"})
            return

        if not room_id or not content or len(content) > 2000:
            emit("error", {"code": "INVALID_REQUEST", "message": "Invalid message content or room"})
            return

        try:
            room_uuid = UUID(room_id)
            require_member(UUID(user_id), room_uuid)
        except AppError as e:
            emit("error", {"code": e.code, "message": e.message})
            return
        except ValueError:
            emit("error", {"code": "INVALID_REQUEST", "message": "Invalid roomId"})
            return

        msg = save_message(
            room_id=room_uuid,
            sender_id=UUID(user_id),
            sender_username=username,
            content=content,
        )
        emit("receive_message", msg, to=str(room_uuid))

    @socketio.on("typing")
    def handle_typing(data):
        room_id = (data or {}).get("roomId")
        username = session.get("username")
        if room_id and username:
            emit(
                "user_typing",
                {
                    "roomId": room_id,
                    "username": username,
                    "isTyping": bool((data or {}).get("isTyping", True)),
                },
                to=room_id,
                include_self=False,
            )
