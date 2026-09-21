from flask import Blueprint
from flask_jwt_extended import jwt_required

from app.auth import schemas, service
from app.common.errors import body

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.post("/register")
def register():
    return {"user": service.register(body(schemas.Register))}, 201


@auth_bp.post("/login")
def login():
    return service.login(body(schemas.Login))


@auth_bp.get("/me")
@jwt_required()
def me():
    return {"user": service.current_user().public()}
