"""The webservice base class"""
import datetime
import uuid
from typing import List

from fastapi import HTTPException, status
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from backend.app.data_access.repository import ToDoRepository, ToDoRepositoryInterface
from backend.app.logger import CustomLogger
from backend.app.models.todo import ToDoEntryData
from backend.app.schemas.todo import DeleteToDoResponse, GetToDoResponse, ToDoCreateEntry, ToDoResponse, ToDoSchema, \
    TodoUpdateEntry


async def create_entry_data_from_create_entry(payload: ToDoCreateEntry) -> ToDoEntryData:
    """Create a ToDoEntryData object from a ToDoCreateEntry."""
    to_do_schema = payload.model_dump()
    to_do_data_schema = ToDoEntryData(to_do_schema.get("id"), to_do_schema.get("title"),
                                      to_do_schema.get("description"), created_at=datetime.datetime.now(),
                                      updated_at=None, deleted=False, done=False)
    return to_do_data_schema


class ToDoService:
    """To Do service"""

    def __init__(self, repository: ToDoRepositoryInterface, logger: CustomLogger):
        self.repository = repository
        self.logger = logger

    @staticmethod
    def raise_http_exception(
            status_code: int
    ) -> HTTPException:
        """Raise an exception error"""
        match status_code:
            case status.HTTP_409_CONFLICT:
                raise HTTPException(
                    status_code=status_code,
                    detail="A ToDo with the given details does already exists.",
                )
            case status.HTTP_500_INTERNAL_SERVER_ERROR:
                raise HTTPException(
                    status_code=status_code,
                    detail="An error occurred while creating the ToDo entry.",
                )
            case status.HTTP_404_NOT_FOUND:
                raise HTTPException(
                    status_code=status_code,
                    detail="No ToDo entry.",
                )
            case _:
                raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR)

    async def update_todo(
            self, to_do_id: uuid.UUID, payload: TodoUpdateEntry
    ) -> ToDoResponse | HTTPException:
        """Update an existing entry."""
        try:
            updated_entry = self.repository.update_to_do(to_do_id, payload)
            to_do_schema = ToDoSchema.model_validate(updated_entry)
            return ToDoResponse(
                success=True, todo_entry=to_do_schema
            )
        except ValueError:
            return self.raise_http_exception(status.HTTP_404_NOT_FOUND)
        except IntegrityError:
            return self.raise_http_exception(status.HTTP_409_CONFLICT)
        except HTTPException:
            return self.raise_http_exception(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def get_todo(self, to_do_id: uuid.UUID) -> GetToDoResponse | HTTPException:
        """Get a specific entry."""
        entry = self.repository.get_to_do_entry(to_do_id)
        if not entry:
            return self.raise_http_exception(status.HTTP_404_NOT_FOUND)
        try:
            return GetToDoResponse(
                success=True,
                todo_entry=ToDoSchema.model_validate(entry),
            )
        except HTTPException:
            return self.raise_http_exception(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def create_todo(self, payload: ToDoCreateEntry) -> ToDoResponse | HTTPException:
        """Add a new entry."""
        to_do_data_schema = await create_entry_data_from_create_entry(payload)
        try:
            self.repository.create_to_do(to_do_data_schema)
            to_do_schema = ToDoSchema.model_validate(to_do_data_schema)
            return ToDoResponse(
                success=True, todo_entry=to_do_schema
            )
        except IntegrityError:
            return self.raise_http_exception(status.HTTP_409_CONFLICT)

    async def delete_todo(
        self, to_do_id: uuid.UUID
    ) -> DeleteToDoResponse | HTTPException:
        """Soft delete a todo entry."""
        success = self.repository.delete_to_do(to_do_id)
        if success:
            return DeleteToDoResponse(
                success=True, message="ToDo deleted successfully."
            )
        return self.raise_http_exception(status.HTTP_404_NOT_FOUND)

    async def get_all_todos(self, limit: int = 10, page: int = 1) -> List[ToDoSchema]:
        """Get all to do entries."""
        data_entries = self.repository.get_all_to_do_entries(limit, page)
        entries_schemata = []
        for entry in data_entries:
            try:
                entries_schemata.append(ToDoSchema.model_validate(entry))
            except ValidationError as e:
                # do not stop with 500 because of invalid database entries
                self.logger.error("Validation error: %s entry %s", e, entry.id)
        return entries_schemata
