from flask import Blueprint
from flask_jwt_extended import jwt_required

from app.auth.service import current_user
from app.common.errors import body, uuid_value
from app.rooms import schemas, service

rooms_bp = Blueprint("rooms", __name__, url_prefix="/api/rooms")


@rooms_bp.post("")
@jwt_required()
def create_room():
    user = current_user()
    data = body(schemas.CreateRoom)
    return {"room": service.create_room(user.id, data)}, 201


@rooms_bp.get("")
@jwt_required()
def list_rooms():
    user = current_user()
    return {"rooms": service.list_rooms(user.id)}


@rooms_bp.get("/<room_id>")
@jwt_required()
def get_room(room_id: str):
    user = current_user()
    return {"room": service.get_room(user.id, uuid_value(room_id))}


@rooms_bp.post("/<room_id>/join")
@jwt_required()
def join_room(room_id: str):
    user = current_user()
    return service.join_room(user.id, uuid_value(room_id))


@rooms_bp.post("/<room_id>/leave")
@jwt_required()
def leave_room(room_id: str):
    user = current_user()
    return service.leave_room(user.id, uuid_value(room_id))


@rooms_bp.get("/<room_id>/members")
@jwt_required()
def get_members(room_id: str):
    user = current_user()
    return {"members": service.get_members(user.id, uuid_value(room_id))}
