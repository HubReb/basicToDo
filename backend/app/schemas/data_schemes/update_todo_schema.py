""" Update todo entry data schema"""
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, field_validator


class TodoUpdateScheme(BaseModel):
    id: UUID
    title: Optional[str] = None
    description: Optional[str] = None
    done: Optional[bool] = None

    @field_validator("id")
    def verify_id(cls, value: UUID) -> UUID:
        """Verify id is not null."""
        if not value:
            raise ValueError("id must not be null.")
        try:
            UUID(str(value))
        except ValueError as exc:
            raise ValueError(f"id is not a valid UUID: {value}") from exc
        return value