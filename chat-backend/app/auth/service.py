from uuid import UUID

from flask_jwt_extended import create_access_token, get_jwt_identity
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.common.errors import AppError, commit
from app.extensions import db
from app.users.model import User


def register(data) -> dict:
    user = User(username=data.username, email=data.email)
    user.set_password(data.password)
    db.session.add(user)
    try:
        commit()
    except IntegrityError as exc:
        raise AppError(
            "ACCOUNT_EXISTS", "Username or email is already registered", 409
        ) from exc
    return user.public()


def login(data) -> dict:
    user = db.session.scalar(select(User).where(User.email == data.email))
    if not user or not user.check_password(data.password):
        raise AppError("INVALID_CREDENTIALS", "Invalid email or password", 401)

    return {
        "accessToken": create_access_token(identity=str(user.id)),
        "user": user.public(),
    }


def user_by_id(identity: str) -> User:
    try:
        user = db.session.get(User, UUID(identity))
    except (ValueError, TypeError):
        user = None

    if not user:
        raise AppError("UNAUTHENTICATED", "Authentication required", 401)
    return user


def current_user() -> User:
    return user_by_id(get_jwt_identity())
