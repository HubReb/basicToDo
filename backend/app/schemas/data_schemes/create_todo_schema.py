"""Create todo entry data schema"""

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from backend.app.schemas.data_schemes.text_rules import (
    MAX_TEXT_LENGTH,
    clean_description,
    clean_title,
)


class ToDoCreateScheme(BaseModel):
    id: UUID
    title: str = Field(json_schema_extra={"maxLength": MAX_TEXT_LENGTH})
    description: Optional[str] = Field(
        default=None, json_schema_extra={"maxLength": MAX_TEXT_LENGTH}
    )

    @field_validator("id")
    def verify_id(cls, value: UUID) -> UUID:
        """Verify id is not null."""
        if not value:
            raise ValueError("id must be a valid UUID.")
        try:
            UUID(str(value))
        except ValueError as exc:
            raise ValueError(f"id is not a valid UUID: {value}") from exc
        return value

    @field_validator("title")
    def validate_title(cls, value: str) -> str:
        """Q6.2: no control characters, stripped, not blank, at most 255 characters."""
        return clean_title(value)

    @field_validator("description")
    def validate_description(cls, value: Optional[str]) -> Optional[str]:
        """Q6.2: no control characters but tab and line breaks, stripped, at most 255."""
        return clean_description(value)
