"""The webservice base class"""
import datetime
import uuid
from typing import Any, List

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from backend.app import schemas
from backend.app.data_access.repository import ToDoRepository
from backend.app.models.todo import ToDoEntryData
from backend.app.schemas.todo import ToDoResponse, ToDoSchema


class ToDoService:
    """To Do service"""

    def __init__(self, repository: ToDoRepository):
        self.repository = repository

    @staticmethod
    def raise_http_exception(
            status_code: int, id_code: uuid.UUID
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
                    detail=f"No ToDo entry with id {id_code} found.",
                )
            case _:
                raise ValueError("{status_code} is unknown.")

    async def update_todo(
        self, to_do_id: uuid.UUID, payload: schemas.todo.ToDoSchema
    ) -> schemas.todo.ToDoResponse | HTTPException:
        """Update an existing entry."""
        update_data: dict[str, Any] = payload.model_dump()
        try:
            updated_entry = self.repository.update_to_do(to_do_id, update_data)
            to_do_schema = schemas.todo.ToDoSchema.model_validate(updated_entry)
            return schemas.todo.ToDoResponse(
                success=True, todo_entry=to_do_schema
            )
        except ValueError:
            return self.raise_http_exception(status.HTTP_404_NOT_FOUND, to_do_id)
        except IntegrityError:
            return self.raise_http_exception(status.HTTP_409_CONFLICT, to_do_id)
        except HTTPException:
            return self.raise_http_exception(
                status.HTTP_500_INTERNAL_SERVER_ERROR, to_do_id
            )

    async def get_todo(self, to_do_id: uuid.UUID) -> schemas.todo.GetToDoResponse | HTTPException:
        """Get an entry."""
        try:
            entry = self.repository.get_to_do_entry(to_do_id)
        except ValueError:
            return self.raise_http_exception(status.HTTP_404_NOT_FOUND, to_do_id)
        try:
            return schemas.todo.GetToDoResponse(
                success=True,
                todo_entry=schemas.todo.ToDoSchema.model_validate(entry),
            )
        except HTTPException:
            return self.raise_http_exception(
                status.HTTP_500_INTERNAL_SERVER_ERROR, to_do_id
            )

    async def create_todo(self, payload: schemas.todo.ToDoCreateEntry) -> ToDoResponse | None:
        """Add a new entry."""
        try:
            to_do_schema = payload.model_dump()
            to_do_orm_data_schema = ToDoEntryData(to_do_schema.get("id"), to_do_schema.get("item"), to_do_schema.get("item"), created_at=datetime.datetime.now(), updated_at=None, deleted=False, done=False)
            self.repository.add_to_do(to_do_orm_data_schema)
            to_do_schema = schemas.todo.ToDoSchema.model_validate(to_do_orm_data_schema)
            return schemas.todo.ToDoResponse(
                success=True, todo_entry=to_do_schema
            )
        except IntegrityError:
            self.raise_http_exception(status.HTTP_409_CONFLICT, payload.id)


    async def delete_todo(
        self, to_do_id: uuid.UUID
    ) -> schemas.todo.DeleteToDoResponse | HTTPException:
        """Delete a todo entry."""
        try:
            self.repository.delete_to_do(to_do_id)
            return schemas.todo.DeleteToDoResponse(
                success=True, message="ToDo deleted successfully."
            )
        except ValueError:
            return self.raise_http_exception(status.HTTP_404_NOT_FOUND, to_do_id)

        except HTTPException:
            return self.raise_http_exception(
                status.HTTP_500_INTERNAL_SERVER_ERROR, to_do_id
            )

    async def get_all_todos(self) -> List[ToDoSchema]:
        """Get all to do entries."""
        data_entries =  self.repository.get_all_to_do_entries()
        return [ToDoSchema.model_validate(data_entry) for data_entry in data_entries]