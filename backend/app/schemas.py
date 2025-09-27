"""ToDo and response schemas"""

from enum import Enum
from datetime import datetime
from uuid import UUID
from typing import Any, List
from pydantic import BaseModel, Field

from backend.app.models import ToDoEntryData


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

class Status(Enum):
    """Response status"""

    SUCCESS = "Success"
    FAILED = "Failed"


class ToDoResponse(BaseModel):
    """Response for ToDo"""

    status: Status
    todo_entry: ToDoSchema


class GetToDoResponse(BaseModel):
    """Response to get ToDo request."""

    status: Status
    todo_entry: ToDoSchema


class ListToDoResponse(BaseModel):
    """List of ToDos"""

    status: Status
    results: int
    todo_entries: List[ToDoSchema]


class DeleteToDoResponse(BaseModel):
    """Response to delete user request"""

    status: Status
    message: str

    # Data models
class ToDoCreateEntry(BaseModel):
    id: UUID
    item: str
    created_at: datetime | None

class TodoUpdateEntry(BaseModel):
    item: str