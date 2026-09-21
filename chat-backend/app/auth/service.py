from uuid import UUID

from flask import current_app
from flask_jwt_extended import create_access_token, get_jwt_identity
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from app.common.errors import AppError, commit
from app.extensions import db
from app.users.model import User

_DUMMY_HASH = generate_password_hash("not-a-real-account-password")


def register(data) -> dict:
    user = User(
        username=data.username,
        email=data.email,
        password_hash=generate_password_hash(data.password),
    )
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
    valid = check_password_hash(
        user.password_hash if user else _DUMMY_HASH, data.password
    )
    if not user or not valid:
        current_app.logger.info("Login rejected")
        raise AppError("INVALID_CREDENTIALS", "Invalid email or password", 401)
    return {
        "accessToken": create_access_token(identity=str(user.id)),
        "user": user.public(),
    }


def user_by_id(identity: str) -> User:
    try:
        user = db.session.get(User, UUID(identity))
    except ValueError, TypeError, AttributeError:
        user = None
    if user is None:
        raise AppError("UNAUTHENTICATED", "Authentication required", 401)
    return user


def current_user() -> User:
    return user_by_id(get_jwt_identity())
