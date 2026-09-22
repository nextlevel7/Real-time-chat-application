from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.users.model import User


def utcnow() -> datetime:
    return datetime.now(UTC)


class ChatRoom(db.Model):
    __tablename__ = "rooms"

    id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid4,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    created_by: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        nullable=False,
    )

    creator: Mapped[User] = relationship("User")
    memberships: Mapped[list[RoomMembership]] = relationship(
        "RoomMembership",
        back_populates="room",
        cascade="all, delete-orphan",
    )

    def public(self, is_member: bool | None = None) -> dict:
        data = {
            "id": str(self.id),
            "name": self.name,
            "createdBy": str(self.created_by),
            "createdAt": self.created_at.isoformat(),
        }
        if is_member is not None:
            data["isMember"] = is_member
        return data


class RoomMembership(db.Model):
    __tablename__ = "room_memberships"

    room_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("rooms.id", ondelete="CASCADE"),
        primary_key=True,
    )

    user_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )

    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        nullable=False,
    )

    room: Mapped[ChatRoom] = relationship("ChatRoom", back_populates="memberships")
    user: Mapped[User] = relationship("User")
