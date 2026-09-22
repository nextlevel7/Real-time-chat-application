from uuid import UUID

from sqlalchemy import select

from app.common.errors import AppError, commit
from app.extensions import db
from app.rooms.models import ChatRoom, RoomMembership
from app.rooms.schemas import CreateRoom
from app.users.model import User


def create_room(user_id: UUID, data: CreateRoom) -> dict:
    room = ChatRoom(name=data.name, created_by=user_id)
    db.session.add(room)
    # Flush in transaction to assign UUID before adding membership
    db.session.flush()

    membership = RoomMembership(room_id=room.id, user_id=user_id)
    db.session.add(membership)
    commit()

    return room.public(is_member=True)


def list_rooms(user_id: UUID) -> list[dict]:
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
    room = db.session.get(ChatRoom, room_id)
    if not room:
        raise AppError("ROOM_NOT_FOUND", "Room not found", 404)

    require_member(user_id, room_id)
    return room.public(is_member=True)


def join_room(user_id: UUID, room_id: UUID) -> dict:
    room = db.session.get(ChatRoom, room_id)
    if not room:
        raise AppError("ROOM_NOT_FOUND", "Room not found", 404)

    existing = db.session.get(RoomMembership, (room_id, user_id))
    if existing:
        raise AppError("ALREADY_MEMBER", "You are already a member of this room", 409)

    membership = RoomMembership(room_id=room_id, user_id=user_id)
    db.session.add(membership)
    commit()

    return {"status": "joined"}


def leave_room(user_id: UUID, room_id: UUID) -> dict:
    room = db.session.get(ChatRoom, room_id)
    if not room:
        raise AppError("ROOM_NOT_FOUND", "Room not found", 404)

    membership = db.session.get(RoomMembership, (room_id, user_id))
    if not membership:
        raise AppError("NOT_MEMBER", "You are not a member of this room", 400)

    db.session.delete(membership)
    commit()

    return {"status": "left"}


def get_members(user_id: UUID, room_id: UUID) -> list[dict]:
    room = db.session.get(ChatRoom, room_id)
    if not room:
        raise AppError("ROOM_NOT_FOUND", "Room not found", 404)

    require_member(user_id, room_id)

    stmt = (
        select(RoomMembership, User)
        .join(User, RoomMembership.user_id == User.id)
        .where(RoomMembership.room_id == room_id)
        .order_by(RoomMembership.joined_at.asc())
    )
    results = db.session.execute(stmt).all()

    return [
        {
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "joinedAt": membership.joined_at.isoformat(),
        }
        for membership, user in results
    ]


def require_member(user_id: UUID, room_id: UUID) -> RoomMembership:
    membership = db.session.get(RoomMembership, (room_id, user_id))
    if not membership:
        raise AppError("ROOM_ACCESS_DENIED", "You are not a member of this room", 403)
    return membership
