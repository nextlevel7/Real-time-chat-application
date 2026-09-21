from uuid import UUID

from flask import current_app, jsonify, request
from pydantic import BaseModel, ConfigDict, ValidationError
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import HTTPException

from app.extensions import db, jwt


class AppError(Exception):
    def __init__(self, code: str, message: str, status: int = 400):
        self.code, self.message, self.status = code, message, status
        super().__init__(message)

    def payload(self) -> dict:
        return {"error": {"code": self.code, "message": self.message}}


class Schema(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


def validate(schema: type[BaseModel], data):
    try:
        return schema.model_validate(data)
    except ValidationError as exc:
        fields = ", ".join(".".join(map(str, e["loc"])) for e in exc.errors())
        raise AppError("VALIDATION_ERROR", f"Invalid input: {fields}", 422) from exc


def body(schema: type[BaseModel]):
    return validate(schema, request.get_json())


def uuid_value(value: str) -> UUID:
    try:
        return UUID(value)
    except (ValueError, TypeError, AttributeError) as exc:
        raise AppError("INVALID_ID", "Expected a UUID", 422) from exc


def register_errors(app):
    @app.errorhandler(AppError)
    def application_error(exc):
        return jsonify(exc.payload()), exc.status

    @app.errorhandler(HTTPException)
    def http_error(exc):
        return jsonify(
            error={
                "code": exc.name.upper().replace(" ", "_"),
                "message": exc.description,
            }
        ), exc.code

    @jwt.unauthorized_loader
    def unauthorized_response(reason):
        return jsonify(
            error={"code": "UNAUTHORIZED", "message": "Missing authorization header"}
        ), 401

    @jwt.invalid_token_loader
    def invalid_token_response(reason):
        return jsonify(error={"code": "INVALID_TOKEN", "message": "Invalid token"}), 401

    @jwt.expired_token_loader
    def expired_token_response(jwt_header, jwt_payload):
        return jsonify(
            error={"code": "TOKEN_EXPIRED", "message": "Token has expired"}
        ), 401

    @app.errorhandler(Exception)
    def unexpected_error(exc):
        db.session.rollback()
        current_app.logger.exception("Unhandled request failure")
        return jsonify(
            error={"code": "INTERNAL_ERROR", "message": "An unexpected error occurred"}
        ), 500


def commit():
    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        raise
