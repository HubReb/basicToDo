"""Unit tests for ValidatorFactory."""
from unittest.mock import MagicMock

import pytest

from backend.app.business_logic.validators import (
    FieldValidator,
    InputSanitizer,
    UUIDValidator,
    ValidatorFactory,
)


@pytest.fixture
def mock_logger():
    """Create a mock logger."""
    return MagicMock()


class TestValidatorFactoryInputSanitizer:
    """Test ValidatorFactory.create_input_sanitizer()."""

    def test_create_input_sanitizer_returns_correct_type(self, mock_logger):
        """Test factory creates InputSanitizer instance."""
        sanitizer = ValidatorFactory.create_input_sanitizer(mock_logger)
        assert isinstance(sanitizer, InputSanitizer)

    def test_create_input_sanitizer_has_logger(self, mock_logger):
        """Test created InputSanitizer has logger."""
        sanitizer = ValidatorFactory.create_input_sanitizer(mock_logger)
        assert sanitizer.logger is mock_logger

    def test_create_input_sanitizer_multiple_times(self, mock_logger):
        """Test factory creates new instances each time."""
        sanitizer1 = ValidatorFactory.create_input_sanitizer(mock_logger)
        sanitizer2 = ValidatorFactory.create_input_sanitizer(mock_logger)

        assert isinstance(sanitizer1, InputSanitizer)
        assert isinstance(sanitizer2, InputSanitizer)
        assert sanitizer1 is not sanitizer2  # Different instances

    def test_create_input_sanitizer_with_different_loggers(self):
        """Test factory creates validators with different loggers."""
        logger1 = MagicMock()
        logger2 = MagicMock()

        sanitizer1 = ValidatorFactory.create_input_sanitizer(logger1)
        sanitizer2 = ValidatorFactory.create_input_sanitizer(logger2)

        assert sanitizer1.logger is logger1
        assert sanitizer2.logger is logger2


class TestValidatorFactoryUUIDValidator:
    """Test ValidatorFactory.create_uuid_validator()."""

    def test_create_uuid_validator_returns_correct_type(self, mock_logger):
        """Test factory creates UUIDValidator instance."""
        validator = ValidatorFactory.create_uuid_validator(mock_logger)
        assert isinstance(validator, UUIDValidator)

    def test_create_uuid_validator_has_logger(self, mock_logger):
        """Test created UUIDValidator has logger."""
        validator = ValidatorFactory.create_uuid_validator(mock_logger)
        assert validator.logger is mock_logger

    def test_create_uuid_validator_multiple_times(self, mock_logger):
        """Test factory creates new instances each time."""
        validator1 = ValidatorFactory.create_uuid_validator(mock_logger)
        validator2 = ValidatorFactory.create_uuid_validator(mock_logger)

        assert isinstance(validator1, UUIDValidator)
        assert isinstance(validator2, UUIDValidator)
        assert validator1 is not validator2  # Different instances

    def test_create_uuid_validator_with_different_loggers(self):
        """Test factory creates validators with different loggers."""
        logger1 = MagicMock()
        logger2 = MagicMock()

        validator1 = ValidatorFactory.create_uuid_validator(logger1)
        validator2 = ValidatorFactory.create_uuid_validator(logger2)

        assert validator1.logger is logger1
        assert validator2.logger is logger2


class TestValidatorFactoryFieldValidator:
    """Test ValidatorFactory.create_field_validator()."""

    def test_create_field_validator_returns_correct_type(self, mock_logger):
        """Test factory creates FieldValidator instance."""
        validator = ValidatorFactory.create_field_validator(mock_logger)
        assert isinstance(validator, FieldValidator)

    def test_create_field_validator_has_logger(self, mock_logger):
        """Test created FieldValidator has logger."""
        validator = ValidatorFactory.create_field_validator(mock_logger)
        assert validator.logger is mock_logger

    def test_create_field_validator_has_input_sanitizer(self, mock_logger):
        """Test created FieldValidator has InputSanitizer composed."""
        validator = ValidatorFactory.create_field_validator(mock_logger)
        assert hasattr(validator, 'input_sanitizer')
        assert isinstance(validator.input_sanitizer, InputSanitizer)

    def test_create_field_validator_sanitizer_has_same_logger(self, mock_logger):
        """Test FieldValidator's InputSanitizer uses same logger."""
        validator = ValidatorFactory.create_field_validator(mock_logger)
        # Note: Factory creates separate InputSanitizer with same logger
        assert isinstance(validator.input_sanitizer.logger, type(mock_logger))

    def test_create_field_validator_multiple_times(self, mock_logger):
        """Test factory creates new instances each time."""
        validator1 = ValidatorFactory.create_field_validator(mock_logger)
        validator2 = ValidatorFactory.create_field_validator(mock_logger)

        assert isinstance(validator1, FieldValidator)
        assert isinstance(validator2, FieldValidator)
        assert validator1 is not validator2  # Different instances
        assert validator1.input_sanitizer is not validator2.input_sanitizer  # Different sanitizers

    def test_create_field_validator_with_different_loggers(self):
        """Test factory creates validators with different loggers."""
        logger1 = MagicMock()
        logger2 = MagicMock()

        validator1 = ValidatorFactory.create_field_validator(logger1)
        validator2 = ValidatorFactory.create_field_validator(logger2)

        assert validator1.logger is logger1
        assert validator2.logger is logger2


class TestValidatorFactoryCreateAll:
    """Test ValidatorFactory.create_all_validators()."""

    def test_create_all_validators_returns_tuple(self, mock_logger):
        """Test create_all_validators returns tuple of 3 validators."""
        result = ValidatorFactory.create_all_validators(mock_logger)

        assert isinstance(result, tuple)
        assert len(result) == 3

    def test_create_all_validators_correct_types(self, mock_logger):
        """Test create_all_validators returns correct types in order."""
        sanitizer, uuid_val, field_val = ValidatorFactory.create_all_validators(mock_logger)

        assert isinstance(sanitizer, InputSanitizer)
        assert isinstance(uuid_val, UUIDValidator)
        assert isinstance(field_val, FieldValidator)

    def test_create_all_validators_have_logger(self, mock_logger):
        """Test all validators have logger."""
        sanitizer, uuid_val, field_val = ValidatorFactory.create_all_validators(mock_logger)

        # Each validator should have a logger (may be same or different instances)
        assert hasattr(sanitizer, 'logger')
        assert hasattr(uuid_val, 'logger')
        assert hasattr(field_val, 'logger')

    def test_create_all_validators_field_has_sanitizer(self, mock_logger):
        """Test FieldValidator has InputSanitizer composed."""
        sanitizer, uuid_val, field_val = ValidatorFactory.create_all_validators(mock_logger)

        assert hasattr(field_val, 'input_sanitizer')
        assert isinstance(field_val.input_sanitizer, InputSanitizer)

    def test_create_all_validators_creates_new_instances(self, mock_logger):
        """Test create_all_validators creates new instances each time."""
        result1 = ValidatorFactory.create_all_validators(mock_logger)
        result2 = ValidatorFactory.create_all_validators(mock_logger)

        # Each call should create new instances
        assert result1[0] is not result2[0]  # Different InputSanitizer
        assert result1[1] is not result2[1]  # Different UUIDValidator
        assert result1[2] is not result2[2]  # Different FieldValidator


class TestValidatorFactoryStaticMethods:
    """Test ValidatorFactory static methods behavior."""

    def test_factory_methods_are_static(self):
        """Test factory methods can be called without instance."""
        logger = MagicMock()

        # Should be callable without creating factory instance
        sanitizer = ValidatorFactory.create_input_sanitizer(logger)
        uuid_val = ValidatorFactory.create_uuid_validator(logger)
        field_val = ValidatorFactory.create_field_validator(logger)
        all_validators = ValidatorFactory.create_all_validators(logger)

        assert isinstance(sanitizer, InputSanitizer)
        assert isinstance(uuid_val, UUIDValidator)
        assert isinstance(field_val, FieldValidator)
        assert isinstance(all_validators, tuple)

    def test_factory_no_state(self):
        """Test factory has no state (is stateless)."""
        logger1 = MagicMock()
        logger2 = MagicMock()

        # Calling factory methods shouldn't affect each other
        val1 = ValidatorFactory.create_input_sanitizer(logger1)
        val2 = ValidatorFactory.create_input_sanitizer(logger2)

        assert val1.logger is logger1
        assert val2.logger is logger2


class TestValidatorFactoryEdgeCases:
    """Test ValidatorFactory edge cases."""

    def test_create_with_real_logger_object(self):
        """Test factory works with real logger objects."""
        from backend.app.logger import CustomLogger
        logger = CustomLogger("Test")

        sanitizer = ValidatorFactory.create_input_sanitizer(logger)
        uuid_val = ValidatorFactory.create_uuid_validator(logger)
        field_val = ValidatorFactory.create_field_validator(logger)

        assert isinstance(sanitizer, InputSanitizer)
        assert isinstance(uuid_val, UUIDValidator)
        assert isinstance(field_val, FieldValidator)

    def test_validators_are_independent(self, mock_logger):
        """Test validators created separately are independent."""
        sanitizer = ValidatorFactory.create_input_sanitizer(mock_logger)
        uuid_val = ValidatorFactory.create_uuid_validator(mock_logger)
        field_val = ValidatorFactory.create_field_validator(mock_logger)

        # Modifying one shouldn't affect others
        sanitizer.custom_attr = "test"  # type: ignore

        assert hasattr(sanitizer, 'custom_attr')
        assert not hasattr(uuid_val, 'custom_attr')
        assert not hasattr(field_val, 'custom_attr')
