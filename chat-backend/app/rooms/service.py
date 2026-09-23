from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.common.errors import AppError, commit
from app.extensions import db
from app.rooms.models import ChatRoom, RoomMembership
from app.rooms.schemas import CreateRoom


def get_room_or_404(room_id: UUID) -> ChatRoom:
    """Find a chat room by ID or raise a 404."""
    room = db.session.get(ChatRoom, room_id)
    if not room:
        raise AppError("ROOM_NOT_FOUND", "Room not found", 404)
    return room


def require_member(user_id: UUID, room_id: UUID) -> RoomMembership:
    """Ensure the user belongs to the room; raises 403 if they have not joined."""
    membership = db.session.get(RoomMembership, (room_id, user_id))
    if not membership:
        raise AppError("ROOM_ACCESS_DENIED", "You are not a member of this room", 403)
    return membership


def create_room(user_id: UUID, data: CreateRoom) -> dict:
    """Create a new room and automatically join the creator as its first member."""
    room = ChatRoom(name=data.name, created_by=user_id)
    db.session.add(room)
    db.session.flush()

    membership = RoomMembership(room_id=room.id, user_id=user_id)
    db.session.add(membership)
    commit()

    return room.public(is_member=True)


def list_rooms(user_id: UUID) -> list[dict]:
    """Return all rooms in reverse chronological order, marked with the user's membership status."""
    rooms = db.session.scalars(
        select(ChatRoom).order_by(ChatRoom.created_at.desc())
    ).all()
    user_memberships = set(
        db.session.scalars(
            select(RoomMembership.room_id).where(RoomMembership.user_id == user_id)
        ).all()
    )
    return [room.public(is_member=(room.id in user_memberships)) for room in rooms]


def get_room(user_id: UUID, room_id: UUID) -> dict:
    """Get details for a single room, ensuring the requesting user is a member."""
    room = get_room_or_404(room_id)
    require_member(user_id, room_id)
    return room.public(is_member=True)


def join_room(user_id: UUID, room_id: UUID) -> dict:
    """Join an existing chat room. Prevents duplicate memberships."""
    get_room_or_404(room_id)

    if db.session.get(RoomMembership, (room_id, user_id)):
        raise AppError("ALREADY_MEMBER", "You are already a member of this room", 409)

    membership = RoomMembership(room_id=room_id, user_id=user_id)
    db.session.add(membership)
    commit()

    return {"status": "joined"}


def leave_room(user_id: UUID, room_id: UUID) -> dict:
    """Leave a chat room the user is currently in."""
    get_room_or_404(room_id)

    membership = db.session.get(RoomMembership, (room_id, user_id))
    if not membership:
        raise AppError("NOT_MEMBER", "You are not a member of this room", 400)

    db.session.delete(membership)
    commit()

    return {"status": "left"}


def get_members(user_id: UUID, room_id: UUID) -> list[dict]:
    """List all members in the room in the order they joined."""
    get_room_or_404(room_id)
    require_member(user_id, room_id)

    memberships = db.session.scalars(
        select(RoomMembership)
        .where(RoomMembership.room_id == room_id)
        .options(joinedload(RoomMembership.user))
        .order_by(RoomMembership.joined_at.asc())
    ).all()

    return [
        {
            "id": str(m.user.id),
            "username": m.user.username,
            "email": m.user.email,
            "joinedAt": m.joined_at.isoformat(),
        }
        for m in memberships
    ]
