""" Create todo entry data schema"""
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, field_validator


class ToDoCreateScheme(BaseModel):
    id: UUID
    title: str
    description: Optional[str] = None

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
    def validate_title_is_not_null(cls, value: str) -> str:
        """Verify title is not null."""
        if not value or not value.strip():
            raise ValueError("title must not be null.")
        return value.strip()