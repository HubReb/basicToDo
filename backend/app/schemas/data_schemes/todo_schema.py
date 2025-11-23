""" Todo entry data schema """

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class ToDoSchema(BaseModel):
    """The todo schema class."""

    id: UUID
    title: str = Field(
        ..., description="The title of the ToDo to be shown.", examples=["Wash dishes"]
    )
    description: Optional[str] = Field(
        None,
        description="The full description of the ToDo",
        examples=["Read the book until page 223."],
    )
    created_at: datetime
    updated_at: Optional[datetime] = None
    deleted: bool = False
    done: bool = False

    class Config:
        """Configuration for pydantic"""

        from_attributes = True
        populate_by_name = True
        arbitrary_types_allowed = True

    @field_validator("title")
    def verify_title_is_not_empty(cls, value: str) -> str:
        """Verify title is not empty."""
        value = value.strip()
        if not value:
            raise ValueError("title must not be empty.")
        return value

    @field_validator("description")
    def verify_description_is_not_empty(cls, value: str) -> Optional[str]:
        """Verify description is valid (allows None/empty)."""
        if not value:
            return None
        if isinstance(value, str):
            return value.strip()
        raise ValueError("title must be None or a string.")

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

    @field_validator("created_at")
    def validate_created_at_is_not_null(cls, value: datetime) -> datetime:
        """Verify created_at is not null."""
        if not value:
            raise ValueError("created_at must not be null.")
        return value