"""ToDo and response schemas"""

from datetime import datetime
from uuid import UUID
from typing import Any, List, Optional
from pydantic import BaseModel, Field


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



class ApiResponse(BaseModel):
    success: bool
    data: Optional[dict] = None
    message: Optional[str] = None
    error: Optional[str] = None


class ToDoResponse(ApiResponse):
    """Response for ToDo"""

    todo_entry: ToDoSchema


class GetToDoResponse(ApiResponse):
    """Response to get ToDo request."""

    todo_entry: ToDoSchema


class ListToDoResponse(ApiResponse):
    """List of ToDos"""

    results: int
    todo_entries: List[ToDoSchema]


class DeleteToDoResponse(ApiResponse):
    """Response to delete user request"""

    message: str

    # Data models
class ToDoCreateEntry(BaseModel):
    id: UUID
    item: str
    created_at: datetime | None

class TodoUpdateEntry(BaseModel):
    item: str