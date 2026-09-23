from uuid import UUID

from flask import current_app, jsonify, request
from pydantic import BaseModel, ConfigDict, ValidationError
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import HTTPException

from app.extensions import db, jwt


class AppError(Exception):
    def __init__(self, code: str, message: str, status: int = 400):
        super().__init__(message)
        self.code, self.message, self.status = code, message, status


class Schema(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


def body(schema: type[BaseModel]):
    try:
        return schema.model_validate(request.get_json())
    except ValidationError as exc:
        fields = ", ".join(".".join(map(str, e["loc"])) for e in exc.errors())
        raise AppError("VALIDATION_ERROR", f"Invalid input: {fields}", 422) from exc


def uuid_value(value: str) -> UUID:
    try:
        return UUID(value)
    except (ValueError, TypeError):
        raise AppError("INVALID_ID", "Expected a UUID", 422)


def commit():
    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        raise


def register_errors(app):
    @app.errorhandler(AppError)
    def handle_app_error(exc):
        return jsonify({"error": {"code": exc.code, "message": exc.message}}), exc.status

    @app.errorhandler(HTTPException)
    def handle_http_error(exc):
        code = exc.name.upper().replace(" ", "_")
        return jsonify({"error": {"code": code, "message": exc.description}}), exc.code

    @jwt.unauthorized_loader
    def unauthorized(reason):
        return jsonify({"error": {"code": "UNAUTHORIZED", "message": "Missing authorization header"}}), 401

    @jwt.invalid_token_loader
    def invalid_token(reason):
        return jsonify({"error": {"code": "INVALID_TOKEN", "message": "Invalid token"}}), 401

    @jwt.expired_token_loader
    def expired_token(header, payload):
        return jsonify({"error": {"code": "TOKEN_EXPIRED", "message": "Token has expired"}}), 401

    @app.errorhandler(Exception)
    def handle_unexpected(exc):
        db.session.rollback()
        current_app.logger.exception("Unexpected error")
        return jsonify({"error": {"code": "INTERNAL_ERROR", "message": "An unexpected error occurred"}}), 500
