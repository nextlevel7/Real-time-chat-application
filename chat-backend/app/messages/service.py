from uuid import UUID

from app.common.errors import AppError
from app.extensions import db
from app.messages.cassandra import get_messages, save_message
from app.messages.schemas import SendMessage
from app.rooms.models import ChatRoom
from app.rooms.service import require_member


def get_room_history(user_id: UUID, room_id: UUID, limit: int = 50) -> list[dict]:
    room = db.session.get(ChatRoom, room_id)
    if not room:
        raise AppError("ROOM_NOT_FOUND", "Room not found", 404)

    # Enforce relational membership authorization before querying Cassandra
    require_member(user_id, room_id)
    return get_messages(room_id, limit)


def post_message(
    user_id: UUID, username: str, room_id: UUID, data: SendMessage
) -> dict:
    room = db.session.get(ChatRoom, room_id)
    if not room:
        raise AppError("ROOM_NOT_FOUND", "Room not found", 404)

    require_member(user_id, room_id)
    return save_message(
        room_id=room_id,
        sender_id=user_id,
        sender_username=username,
        content=data.content,
    )
