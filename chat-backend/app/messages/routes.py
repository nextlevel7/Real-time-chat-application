from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from app.auth.service import current_user
from app.common.errors import body, uuid_value
from app.messages import schemas, service

messages_bp = Blueprint("messages", __name__, url_prefix="/api/rooms")


@messages_bp.get("/<room_id>/messages")
@jwt_required()
def get_messages(room_id: str):
    user = current_user()
    limit = min(max(request.args.get("limit", default=50, type=int), 1), 100)
    return {
        "messages": service.get_room_history(user.id, uuid_value(room_id), limit)
    }


@messages_bp.post("/<room_id>/messages")
@jwt_required()
def post_message(room_id: str):
    user = current_user()
    data = body(schemas.SendMessage)
    return {
        "message": service.post_message(
            user.id, user.username, uuid_value(room_id), data
        )
    }, 201
