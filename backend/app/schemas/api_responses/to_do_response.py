""" Schema of Todo response of API"""
from pydantic import field_validator

from backend.app.schemas.api_responses.api_response import ApiResponse
from backend.app.schemas.data_schemes.todo_schema import ToDoSchema


class ToDoResponse(ApiResponse):
    """Response for ToDo"""
    todo_entry: ToDoSchema

    @field_validator("todo_entry")
    def validate_todo_entry_is_not_null(cls, value: ToDoSchema) -> ToDoSchema:
        """Verify todo_entry is not null."""
        if not value:
            raise ValueError("todo_entry must not be null.")
        return value