from pydantic import Field, field_validator

from app.common.errors import Schema


class CreateRoom(Schema):
    name: str = Field(min_length=1, max_length=100)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("Room name cannot be empty or whitespace only")
        return trimmed
