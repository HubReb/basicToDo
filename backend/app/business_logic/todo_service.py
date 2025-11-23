"""Business logic layer for ToDo management (secure version)."""
import uuid
from typing import List

from pydantic import ValidationError

from backend.app.business_logic.builders.builder_interface import BuilderInterface
from backend.app.business_logic.decorators import handle_service_exceptions
from backend.app.business_logic.exceptions import ToDoNotFoundError
from backend.app.business_logic.validators import FieldValidator, ValidatorInterface
from backend.app.data_access.repository import ToDoRepositoryInterface
from backend.app.logger import CustomLogger
from backend.app.schemas.data_schemes.create_todo_schema import ToDoCreateScheme
from backend.app.schemas.data_schemes.todo_schema import ToDoSchema
from backend.app.schemas.data_schemes.update_todo_schema import TodoUpdateScheme


class ToDoService:
    """Application service for ToDo operations (secure)."""

    def __init__(
            self,
            repository: ToDoRepositoryInterface,
            logger: CustomLogger,
            input_sanitizer: ValidatorInterface,
            uuid_validator: ValidatorInterface,
            field_validator: ValidatorInterface,
            builder: BuilderInterface,
    ):
        self.repository = repository
        self.logger = logger
        self.input_sanitizer = input_sanitizer
        self.uuid_validator = uuid_validator
        if not isinstance(field_validator, FieldValidator):
            raise ValidationError(f"Field validator must be of type {FieldValidator.__name__}")
        self.field_validator = field_validator
        self.builder = builder

    @handle_service_exceptions
    async def create_todo(self, payload: ToDoCreateScheme) -> ToDoSchema:
        entry_data = await self.builder.build_from_create_schema(payload)
        self.repository.create_to_do(entry_data)
        return ToDoSchema.model_validate(entry_data)

    @handle_service_exceptions
    async def get_todo(self, to_do_id: str | uuid.UUID) -> ToDoSchema:
        valid_uuid = self.uuid_validator.validate(to_do_id)
        entry = self.repository.get_to_do_entry(valid_uuid)
        if not entry:
            raise ToDoNotFoundError
        return ToDoSchema.model_validate(entry)

    @handle_service_exceptions
    async def update_todo(self, to_do_id: uuid.UUID, payload: TodoUpdateScheme) -> ToDoSchema:
        if payload.done:
            updated_entry = await self.mark_to_do_as_done(to_do_id)
            return updated_entry

        if payload.title is not None:
            payload.title = self.field_validator.validate_required(payload.title, field_name="title")
        if payload.description is not None:
            payload.description = self.field_validator.validate_optional(payload.description)

        updated_entry = self.repository.update_to_do(to_do_id, payload)
        if not updated_entry:
            raise ToDoNotFoundError

        return ToDoSchema.model_validate(updated_entry)

    @handle_service_exceptions
    async def delete_todo(self, to_do_id: uuid.UUID) -> bool:
        deleted = self.repository.delete_to_do(self.uuid_validator.validate(to_do_id))
        if not deleted:
            raise ToDoNotFoundError
        return True

    @handle_service_exceptions
    async def get_all_todos(self, limit: int = 10, page: int = 1) -> List[ToDoSchema]:
        entries = self.repository.get_all_to_do_entries(limit, page)
        result: list[ToDoSchema] = []
        for entry in entries:
            try:
                result.append(ToDoSchema.model_validate(entry))
            except ValidationError as e:
                self.logger.warning("Invalid DB entry skipped: %s", e)
        return result

    @handle_service_exceptions
    async def mark_to_do_as_done(self, to_do_id: uuid.UUID) -> ToDoSchema:
        """Mark a todo as done."""
        entry = self.repository.get_to_do_entry(to_do_id)
        if not entry:
            raise ToDoNotFoundError
        done_entry = TodoUpdateScheme(id=entry.id, done=True, description=entry.description, title=entry.title)
        updated_entry = self.repository.update_to_do(to_do_id, TodoUpdateScheme.model_validate(done_entry))
        return ToDoSchema.model_validate(updated_entry)