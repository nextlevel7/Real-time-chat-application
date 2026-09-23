from pydantic import Field, field_validator

from app.common.errors import Schema


class SendMessage(Schema):
    content: str = Field(min_length=1, max_length=4000)

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("Message content cannot be blank or whitespace only")
        return trimmed
