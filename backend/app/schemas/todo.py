"""ToDo and response schemas"""

from datetime import datetime
from typing import Any, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


def exists(value: Any) -> Any:
    """Verify value is not null."""
    if value is not None:
        return value
    raise ValueError("value must not be None.")




class ToDoSchema(BaseModel):
    """The todo schema class."""

    id: UUID
    title: str = Field(
        ..., description="The title of the ToDo to be shown.", examples=["Wash dishes"]
    )
    description: Optional[str] = Field(
        ...,
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
    def verify_title_is_not_empty(cls, value):
        """Verify title is not empty."""
        if not value or not value.strip():
            raise ValueError("title must not be empty.")
        return value.strip()

    @field_validator("description")
    def verify_description_is_not_empty(cls, value):
        """Verify description is not empty."""
        if not value or not value.strip():
            raise ValueError("description must not be empty.")
        return value.strip()

    @field_validator("id")
    def validate_id_is_not_null(cls, value):
        """Verify id is not null."""
        if not value:
            raise ValueError("id must not be null.")
        return value

    @field_validator("created_at")
    def validate_created_at_is_not_null(cls, value):
        """Verify created_at is not null."""
        if not value:
            raise ValueError("created_at must not be null.")
        return value


class ApiResponse(BaseModel):
    success: bool
    data: Optional[dict] = None
    message: Optional[str] = None
    error: Optional[str] = None



class ToDoResponse(ApiResponse):
    """Response for ToDo"""

    todo_entry: ToDoSchema

    @field_validator("todo_entry")
    def validate_todo_entry_is_not_null(cls, value):
        """Verify todo_entry is not null."""
        if not value:
            raise ValueError("todo_entry must not be null.")
        return value


class GetToDoResponse(ApiResponse):
    """Response to get ToDo request."""

    todo_entry: ToDoSchema

    @field_validator("todo_entry")
    def validate_todo_entry_is_not_null(cls, value):
        """Verify todo_entry is not null."""
        if not value:
            raise ValueError("todo_entry must not be null.")
        return value


class ListToDoResponse(ApiResponse):
    """List of ToDos"""

    results: Optional[int] = 0
    todo_entries: List[ToDoSchema]

    @field_validator("todo_entries")
    def validate_todo_entry_is_not_null(cls, value):
        """Verify todo_entry is not null."""
        if not value:
            raise ValueError("todo_entry must not be null.")
        return value


class DeleteToDoResponse(ApiResponse):
    """Response to delete user request"""

    message: Optional[str] = None

    # Data models
class ToDoCreateEntry(BaseModel):
    id: UUID
    title: str
    description: str = None

    @field_validator("id")
    def validate_id_is_not_null(cls, value):
        """Verify id is not null."""
        if not value:
            raise ValueError("id must not be null.")
        return value

    @field_validator("title")
    def validate_item_is_not_null(cls, value):
        """Verify item is not null."""
        if not value or not value.strip():
            raise ValueError("item must not be null.")
        return value.strip()

class TodoUpdateEntry(BaseModel):
    id: UUID
    title: Optional[str] = None
    description: Optional[str] = None
    done: Optional[bool] = None

    @field_validator("id")
    def validate_id_is_not_null(cls, value):
        """Verify id is not null."""
        if not value:
            raise ValueError("item must not be null.")
        return value