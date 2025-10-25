"""Business logic layer for ToDo management."""
import datetime
import uuid
from typing import List

from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from backend.app.business_logic.exceptions import (
    ToDoAlreadyExistsError,
    ToDoNotFoundError,
    ToDoRepositoryError,
)
from backend.app.data_access.repository import ToDoRepositoryInterface
from backend.app.logger import CustomLogger
from backend.app.models.todo import ToDoEntryData
from backend.app.schemas.todo import (ToDoCreateEntry, ToDoSchema, TodoUpdateEntry)


async def create_entry_data_from_create_entry(payload: ToDoCreateEntry) -> ToDoEntryData:
    """Create a ToDoEntryData object from a ToDoCreateEntry."""
    to_do_schema = payload.model_dump()
    return ToDoEntryData(
        id=to_do_schema.get("id"),
        title=to_do_schema.get("title"),
        description=to_do_schema.get("description"),
        created_at=datetime.datetime.now(),
        updated_at=None,
        deleted=False,
        done=False,
    )


class ToDoService:
    """Application service for ToDo operations."""

    def __init__(self, repository: ToDoRepositoryInterface, logger: CustomLogger):
        self.repository = repository
        self.logger = logger

    async def create_todo(self, payload: ToDoCreateEntry) -> ToDoSchema:
        entry_data = await create_entry_data_from_create_entry(payload)
        try:
            self.repository.create_to_do(entry_data)
            return ToDoSchema.model_validate(entry_data)
        except IntegrityError:
            raise ToDoAlreadyExistsError
        except Exception as exc:
            self.logger.error("Error creating ToDo: %s", exc)
            raise ToDoRepositoryError from exc

    async def get_todo(self, to_do_id: uuid.UUID) -> ToDoSchema:
        entry = self.repository.get_to_do_entry(to_do_id)
        if not entry:
            raise ToDoNotFoundError
        return ToDoSchema.model_validate(entry)

    async def update_todo(self, to_do_id: uuid.UUID, payload: TodoUpdateEntry) -> ToDoSchema:
        try:
            updated_entry = self.repository.update_to_do(to_do_id, payload)
            if not updated_entry:
                raise ToDoNotFoundError
            return ToDoSchema.model_validate(updated_entry)
        except IntegrityError:
            raise ToDoAlreadyExistsError
        except Exception as exc:
            self.logger.error("Update error: %s", exc)
            raise ToDoRepositoryError from exc

    async def delete_todo(self, to_do_id: uuid.UUID) -> bool:
        deleted = self.repository.delete_to_do(to_do_id)
        if not deleted:
            raise ToDoNotFoundError
        return True

    async def get_all_todos(self, limit: int = 10, page: int = 1) -> List[ToDoSchema]:
        entries = self.repository.get_all_to_do_entries(limit, page)
        result: list[ToDoSchema] = []
        for entry in entries:
            try:
                result.append(ToDoSchema.model_validate(entry))
            except ValidationError as e:
                self.logger.warning("Invalid DB entry skipped: %s", e)
        return result