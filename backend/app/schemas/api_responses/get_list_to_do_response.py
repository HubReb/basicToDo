""" Get list of todos response scheme of API"""
from typing import List, Optional

from pydantic import field_validator

from backend.app.schemas.api_responses.api_response import ApiResponse
from backend.app.schemas.data_schemes.todo_schema import ToDoSchema


class ListToDoResponse(ApiResponse):
    """List of ToDos"""

    results: Optional[int] = 0
    todo_entries: List[ToDoSchema]

    @field_validator("todo_entries")
    def validate_todo_entry_is_not_null(cls, value: List[ToDoSchema]) -> List[ToDoSchema]:
        """Verify todo_entries is not null."""
        if not value:
            raise ValueError("todo_entry must not be null.")
        return value