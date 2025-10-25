"""Business logic layer for ToDo management (secure version)."""
import datetime
import re
import uuid
from typing import List

from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from backend.app.business_logic.exceptions import (
    ToDoAlreadyExistsError,
    ToDoNotFoundError,
    ToDoRepositoryError,
    ToDoValidationError,
)
from backend.app.data_access.repository import ToDoRepositoryInterface
from backend.app.logger import CustomLogger
from backend.app.models.todo import ToDoEntryData
from backend.app.schemas.todo import ToDoCreateEntry, ToDoSchema, TodoUpdateEntry

# compile once for performance
_SQL_INJECTION_RE = re.compile(
    r"(?i)(--|;|/\*|\*/|\bxp_cmdshell\b|\b(?:drop|delete|insert|update|exec(?:ute)?|union|select|shutdown|create|alter|rename|truncate|declare)\b)"
)


def sanitize_text(value: str | None) -> str | None:
    """Sanitize input to prevent obvious SQL-injection patterns.

    - Rejects operator tokens (e.g. ';', '--', '/*', '*/') anywhere in string.
    - Rejects SQL keywords as whole words (so 'updated' is allowed).
    - Returns stripped string if OK.
    """
    if value is None:
        return None

    # Debug: remove or convert to proper logging in production
    # print(f"Sanitizing value: {value!r}")

    if _SQL_INJECTION_RE.search(value):
        raise ToDoValidationError(f"Invalid characters or SQL keywords in input: {value!r}")

    return value.strip()


def validate_uuid(value: str | uuid.UUID) -> uuid.UUID:
    """Validate UUID string."""
    try:
        return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))
    except ValueError as exc:
        raise ToDoValidationError(f"Invalid UUID: {value}") from exc


async def create_entry_data_from_create_entry(payload: ToDoCreateEntry) -> ToDoEntryData:
    """Create a sanitized ToDoEntryData object from input."""
    return ToDoEntryData(
        id=validate_uuid(payload.id),
        title=sanitize_text(payload.title),
        description=sanitize_text(payload.description),
        created_at=datetime.datetime.now(),
        updated_at=None,
        deleted=False,
        done=False,
    )


class ToDoService:
    """Application service for ToDo operations (secure)."""

    def __init__(self, repository: ToDoRepositoryInterface, logger: CustomLogger):
        self.repository = repository
        self.logger = logger

    async def create_todo(self, payload: ToDoCreateEntry) -> ToDoSchema:
        try:
            # Sanitize the title and description fields before proceeding
            sanitized_title = sanitize_text(payload.title)
            sanitized_description = sanitize_text(payload.description)
            entry_data = await create_entry_data_from_create_entry(payload)
            entry_data.title = sanitized_title
            entry_data.description = sanitized_description
            self.repository.create_to_do(entry_data)
            return ToDoSchema.model_validate(entry_data)
        except IntegrityError:
            raise ToDoAlreadyExistsError
        except ToDoValidationError as ve:
            self.logger.warning("Validation error: %s", ve)
            raise ToDoValidationError from ve
        except Exception as exc:
            self.logger.error("Error creating ToDo: %s", exc)
            raise ToDoRepositoryError from exc

    async def get_todo(self, to_do_id: str | uuid.UUID) -> ToDoSchema:
        try:
            valid_uuid = validate_uuid(to_do_id)
        except ToDoValidationError as ve:
            self.logger.warning("Invalid UUID: %s", ve)
            raise
        try:
            entry = self.repository.get_to_do_entry(valid_uuid)
            if not entry:
                raise ToDoNotFoundError
            return ToDoSchema.model_validate(entry)
        except ToDoNotFoundError:
            raise
        except ToDoValidationError as ve:
            self.logger.warning("Invalid DB entry: %s", ve)
            raise ToDoValidationError from ve
        except Exception as exc:
            self.logger.error("Error retrieving ToDo: %s", exc)
            raise ToDoRepositoryError from exc

    async def update_todo(self, to_do_id: uuid.UUID, payload: TodoUpdateEntry) -> ToDoSchema:
        try:
            # Sanitize the input fields to protect against SQL injection
            sanitized_title = sanitize_text(payload.title)
            sanitized_description = sanitize_text(payload.description)

            # Apply sanitized values to the payload before passing to the repository
            payload.title = sanitized_title
            payload.description = sanitized_description

            updated_entry = self.repository.update_to_do(to_do_id, payload)
            if not updated_entry:
                raise ToDoNotFoundError

            return ToDoSchema.model_validate(updated_entry)
        except ToDoNotFoundError:
            raise
        except IntegrityError:
            raise ToDoAlreadyExistsError
        except ToDoValidationError as ve:
            self.logger.warning("Validation error on update: %s", ve)
            raise ToDoValidationError from ve
        except Exception as exc:
            self.logger.error("Update error: %s", exc)
            raise ToDoRepositoryError from exc

    async def delete_todo(self, to_do_id: uuid.UUID) -> bool:
        try:
            deleted = self.repository.delete_to_do(validate_uuid(to_do_id))
            if not deleted:
                raise ToDoNotFoundError
            return True
        except ToDoNotFoundError:
            self.logger.error("To Do not found: %s", to_do_id)
            raise ToDoNotFoundError
        except Exception as exc:
            self.logger.error("Deletion error: %s", exc)
            raise ToDoRepositoryError from exc

    async def get_all_todos(self, limit: int = 10, page: int = 1) -> List[ToDoSchema]:
        try:
            entries = self.repository.get_all_to_do_entries(limit, page)
            result: list[ToDoSchema] = []
            for entry in entries:
                try:
                    result.append(ToDoSchema.model_validate(entry))
                except ValidationError as e:
                    self.logger.warning("Invalid DB entry skipped: %s", e)
            return result
        except Exception as exc:
            self.logger.error("Error listing ToDos: %s", exc)
            raise ToDoRepositoryError from exc