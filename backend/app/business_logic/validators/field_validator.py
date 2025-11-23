"""Field validator for validating required and optional fields."""
from typing import Any

from backend.app.business_logic.exceptions import ToDoValidationError
from backend.app.business_logic.validators.input_sanitizer import InputSanitizer
from backend.app.business_logic.validators.validator_interface import ValidatorInterface
from backend.app.logger import CustomLogger


class FieldValidator(ValidatorInterface):
    """Validates field values with required/optional semantics."""

    def __init__(self, input_sanitizer: InputSanitizer, logger: CustomLogger):
        self.input_sanitizer = input_sanitizer
        self.logger = logger

    def validate(self, value: Any, *args: Any, **kwargs: Any) -> str:
        """Generic validate method for LSP compliance.

        Defaults to required field validation unless 'required' kwarg is False.
        """
        field_name = kwargs.get('field_name', 'field')
        required = kwargs.get('required', True)

        if required:
            return self.validate_required(value, field_name)
        return self.validate_optional(value)

    def validate_required(self, value: str | None, field_name: str) -> str:
        """Validate that a required field is present and not empty after sanitization."""
        sanitized = self.input_sanitizer.validate(value)
        if not sanitized:
            self.logger.warning("Required field '%s' is empty or None", field_name)
            raise ToDoValidationError(f"Invalid payload: {field_name} is required")
        return sanitized

    def validate_optional(self, value: str | None) -> str:
        """Validate an optional field, returning empty string if None or empty."""
        sanitized = self.input_sanitizer.validate(value)
        return sanitized if sanitized else ""
