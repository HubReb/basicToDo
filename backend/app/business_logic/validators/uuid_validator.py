"""UUID validator for validating UUID strings."""
import uuid
from typing import Any

from backend.app.business_logic.exceptions import ToDoValidationError
from backend.app.business_logic.validators.validator_interface import ValidatorInterface
from backend.app.logger import CustomLogger


class UUIDValidator(ValidatorInterface):
    """Validates UUID strings and converts them to UUID objects."""

    def __init__(self, logger: CustomLogger):
        self.logger = logger

    def validate(self, value: Any, *args: Any, **kwargs: Any) -> uuid.UUID:
        """Validate UUID string and return UUID object."""
        try:
            if isinstance(value, uuid.UUID):
                return value
            return uuid.UUID(str(value))
        except ValueError as exc:
            self.logger.warning("Invalid UUID provided: %s", value)
            raise ToDoValidationError(f"Invalid UUID: {value}") from exc
