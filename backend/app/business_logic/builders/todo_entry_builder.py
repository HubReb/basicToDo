"""Builder for creating ToDoORM objects."""

import datetime

from backend.app.business_logic.builders.builder_interface import BuilderInterface
from backend.app.business_logic.exceptions import ToDoValidationError
from backend.app.business_logic.validators.field_validator import FieldValidator
from backend.app.business_logic.validators.uuid_validator import UUIDValidator
from backend.app.data_access.database import ToDoORM
from backend.app.schemas.data_schemes.create_todo_schema import ToDoCreateScheme


class ToDoEntryBuilder(BuilderInterface):
    """Builds validated ToDoORM objects from input schemas."""

    def __init__(self, uuid_validator: UUIDValidator, field_validator: FieldValidator):
        self.uuid_validator = uuid_validator
        self.field_validator = field_validator

    async def build_from_create_schema(self, payload: ToDoCreateScheme) -> ToDoORM:
        """Create a sanitized ToDoORM object from create schema."""
        if not payload:
            raise ToDoValidationError("Invalid payload: payload cannot be None")
        if payload.id is None:
            raise ToDoValidationError("Invalid payload: id is required")

        return ToDoORM(
            id=self.uuid_validator.validate(payload.id),
            title=self.field_validator.validate_required(payload.title, "title"),
            description=self.field_validator.validate_optional(payload.description),
            created_at=datetime.datetime.now(datetime.timezone.utc),
            deleted=False,
            done=False,
        )
