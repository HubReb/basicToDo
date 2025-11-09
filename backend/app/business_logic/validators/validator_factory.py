"""Factory for creating validator instances."""
from backend.app.business_logic.validators.field_validator import FieldValidator
from backend.app.business_logic.validators.input_sanitizer import InputSanitizer
from backend.app.business_logic.validators.uuid_validator import UUIDValidator
from backend.app.logger import CustomLogger


class ValidatorFactory:
    """Factory for creating validator instances with proper dependencies."""

    @staticmethod
    def create_input_sanitizer(logger: CustomLogger) -> InputSanitizer:
        """Create an InputSanitizer instance."""
        return InputSanitizer(logger)

    @staticmethod
    def create_uuid_validator(logger: CustomLogger) -> UUIDValidator:
        """Create a UUIDValidator instance."""
        return UUIDValidator(logger)

    @staticmethod
    def create_field_validator(logger: CustomLogger) -> FieldValidator:
        """Create a FieldValidator instance with InputSanitizer dependency."""
        input_sanitizer = ValidatorFactory.create_input_sanitizer(logger)
        return FieldValidator(input_sanitizer, logger)

    @staticmethod
    def create_all_validators(logger: CustomLogger) -> tuple[InputSanitizer, UUIDValidator, FieldValidator]:
        """Create all validators with proper dependencies.

        Returns:
            Tuple of (InputSanitizer, UUIDValidator, FieldValidator)
        """
        input_sanitizer = ValidatorFactory.create_input_sanitizer(logger)
        uuid_validator = ValidatorFactory.create_uuid_validator(logger)
        field_validator = FieldValidator(input_sanitizer, logger)
        return input_sanitizer, uuid_validator, field_validator
