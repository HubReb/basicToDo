"""ToDo and response schemas"""

from enum import Enum
from datetime import datetime
from uuid import UUID
from typing import Any, List
from pydantic import BaseModel, Field


def exists(value: Any) -> Any:
    """Verify value is not null."""
    if value is not None:
        return value
    raise ValueError("value must not be None.")


class Status(Enum):
    """Response status"""

    SUCCESS = "Success"
    FAILED = "Failed"


class ToDo(BaseModel):
    """The todo data class."""

    id: UUID
    title: str = Field(
        ..., description="The title of the ToDo to be shown.", examples=["Wash dishes"]
    )
    description: str = Field(
        ...,
        description="The full description of the ToDo",
        examples=["Read the book until page 223."],
    )
    created_at: datetime | None
    updated_at: datetime | None
    deleted: bool = False
    done: bool = False

    class Config:
        """Configuration for pydantic"""

        from_attributes = True
        populate_by_name = True
        arbitrary_types_allowed = True


class ToDoResponse(BaseModel):
    """Response for ToDo"""

    status: Status
    todo_entry: ToDo


class GetToDoResponse(BaseModel):
    """Response to get ToDo request."""

    status: Status
    todo_entry: ToDo


class ListToDoResponse(BaseModel):
    """List of ToDos"""

    status: Status
    results: int
    todo_entries: List[ToDo]


class DeleteToDoResponse(BaseModel):
    """Response to delete user request"""

    status: Status
    message: str
