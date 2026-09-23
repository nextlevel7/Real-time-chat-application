from uuid import UUID

from flask import request, session
from flask_jwt_extended import decode_token
from flask_socketio import emit, join_room, leave_room

from app.common.errors import AppError
from app.extensions import db
from app.messages.cassandra import save_message
from app.rooms.service import require_member
from app.users.model import User


ROOM_ACTIVE_USERS: dict[str, set[str]] = {}
SID_ROOMS: dict[str, set[str]] = {}
SID_USER: dict[str, str] = {}


def _is_user_in_room(username: str, room_id: str) -> bool:
    return any(
        room_id in rooms and SID_USER.get(sid) == username
        for sid, rooms in SID_ROOMS.items()
    )


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
            SID_USER[request.sid] = user.username
            SID_ROOMS[request.sid] = set()
            return True
        except Exception:  # noqa: BLE001 - Reject socket connection if token is malformed or invalid
            return False

    @socketio.on("disconnect")
    def handle_disconnect():
        username = SID_USER.pop(request.sid, session.get("username"))
        rooms = SID_ROOMS.pop(request.sid, set())
        for room_id in rooms:
            if username and not _is_user_in_room(username, room_id):
                if room_id in ROOM_ACTIVE_USERS:
                    ROOM_ACTIVE_USERS[room_id].discard(username)
                    if not ROOM_ACTIVE_USERS[room_id]:
                        del ROOM_ACTIVE_USERS[room_id]
                emit(
                    "user_left",
                    {"roomId": room_id, "username": username},
                    to=room_id,
                    include_self=False,
                )
                active_users = sorted(list(ROOM_ACTIVE_USERS.get(room_id, set())))
                emit(
                    "active_users",
                    {"roomId": room_id, "users": active_users},
                    to=room_id,
                )

    @socketio.on("join_room")
    def handle_join_room(data):
        user_id = session.get("user_id")
        username = session.get("username") or SID_USER.get(request.sid)
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

        room_str = str(room_uuid)
        join_room(room_str)

        if room_str not in ROOM_ACTIVE_USERS:
            ROOM_ACTIVE_USERS[room_str] = set()
        if username:
            ROOM_ACTIVE_USERS[room_str].add(username)

        if request.sid in SID_ROOMS:
            SID_ROOMS[request.sid].add(room_str)
        else:
            SID_ROOMS[request.sid] = {room_str}

        emit(
            "user_joined",
            {"roomId": room_str, "username": username},
            to=room_str,
            include_self=False,
        )
        active_users = sorted(list(ROOM_ACTIVE_USERS[room_str]))
        emit(
            "active_users",
            {"roomId": room_str, "users": active_users},
            to=room_str,
        )

    @socketio.on("leave_room")
    def handle_leave_room(data):
        room_id = (data or {}).get("roomId")
        username = session.get("username") or SID_USER.get(request.sid)
        if room_id:
            leave_room(room_id)
            if request.sid in SID_ROOMS:
                SID_ROOMS[request.sid].discard(room_id)
            if username and not _is_user_in_room(username, room_id):
                if room_id in ROOM_ACTIVE_USERS:
                    ROOM_ACTIVE_USERS[room_id].discard(username)
                    if not ROOM_ACTIVE_USERS[room_id]:
                        del ROOM_ACTIVE_USERS[room_id]
                emit(
                    "user_left",
                    {"roomId": room_id, "username": username},
                    to=room_id,
                    include_self=False,
                )
                active_users = sorted(list(ROOM_ACTIVE_USERS.get(room_id, set())))
                emit(
                    "active_users",
                    {"roomId": room_id, "users": active_users},
                    to=room_id,
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
