"""Unit tests for UUIDValidator."""
import uuid
from unittest.mock import MagicMock

import pytest

from backend.app.business_logic.exceptions import ToDoValidationError
from backend.app.business_logic.validators.uuid_validator import UUIDValidator


@pytest.fixture
def mock_logger():
    """Create a mock logger."""
    return MagicMock()


@pytest.fixture
def validator(mock_logger):
    """Create UUIDValidator with mocked logger."""
    return UUIDValidator(mock_logger)


class TestUUIDValidatorValidInputs:
    """Test UUIDValidator with valid UUID inputs."""

    def test_validate_valid_uuid_string(self, validator):
        """Test validation of valid UUID string."""
        uuid_str = "550e8400-e29b-41d4-a716-446655440000"
        result = validator.validate(uuid_str)
        assert isinstance(result, uuid.UUID)
        assert str(result) == uuid_str

    def test_validate_uuid_object_passthrough(self, validator):
        """Test UUID object is returned as-is."""
        uuid_obj = uuid.uuid4()
        result = validator.validate(uuid_obj)
        assert result is uuid_obj
        assert isinstance(result, uuid.UUID)

    def test_validate_uppercase_uuid(self, validator):
        """Test validation of uppercase UUID string."""
        uuid_str = "550E8400-E29B-41D4-A716-446655440000"
        result = validator.validate(uuid_str)
        assert isinstance(result, uuid.UUID)

    def test_validate_mixed_case_uuid(self, validator):
        """Test validation of mixed case UUID string."""
        uuid_str = "550e8400-E29B-41d4-A716-446655440000"
        result = validator.validate(uuid_str)
        assert isinstance(result, uuid.UUID)

    def test_validate_uuid_without_hyphens(self, validator):
        """Test validation of UUID string without hyphens."""
        uuid_str = "550e8400e29b41d4a716446655440000"
        result = validator.validate(uuid_str)
        assert isinstance(result, uuid.UUID)

    def test_validate_uuid_with_braces(self, validator):
        """Test validation of UUID string with braces."""
        uuid_str = "{550e8400-e29b-41d4-a716-446655440000}"
        result = validator.validate(uuid_str)
        assert isinstance(result, uuid.UUID)

    def test_validate_uuid_with_urn_prefix(self, validator):
        """Test validation of UUID string with URN prefix."""
        uuid_str = "urn:uuid:550e8400-e29b-41d4-a716-446655440000"
        result = validator.validate(uuid_str)
        assert isinstance(result, uuid.UUID)


@pytest.mark.parametrize("invalid_uuid,description", [
    ("", "empty string"),
    ("not-a-uuid", "random text"),
    ("123", "short number"),
    ("12345678-1234-1234-1234-1234567890", "too short"),
    ("12345678-1234-1234-1234-1234567890123", "too long"),
    ("550e8400-e29b-41d4-a716", "incomplete UUID"),
    ("550e8400-e29b-41d4-a716-44665544000g", "invalid character 'g'"),
    ("550e8400-e29b-41d4-a716-4466554400zz", "invalid characters 'zz'"),
    ("550e8400-e29b-41d4-a716-446655440000-extra", "extra characters"),
    ("550e8400_e29b_41d4_a716_446655440000", "underscores instead of hyphens"),
    ("   ", "only whitespace"),
    ("null", "null string"),
    ("undefined", "undefined string"),
])
class TestUUIDValidatorInvalidInputs:
    """Test UUIDValidator with invalid UUID inputs."""

    def test_invalid_uuid_raises_error(self, validator, mock_logger, invalid_uuid, description):
        """Test that invalid UUID raises ToDoValidationError."""
        with pytest.raises(ToDoValidationError) as exc_info:
            validator.validate(invalid_uuid)

        assert "Invalid UUID" in str(exc_info.value)
        assert invalid_uuid in str(exc_info.value)
        mock_logger.warning.assert_called_once()


class TestUUIDValidatorNoneInput:
    """Test UUIDValidator with None input."""

    def test_validate_none_raises_error(self, validator):
        """Test that None input raises ToDoValidationError."""
        with pytest.raises(ToDoValidationError):
            validator.validate(None)


class TestUUIDValidatorNonStringInputs:
    """Test UUIDValidator with non-string, non-UUID inputs."""

    def test_validate_integer_raises_error(self, validator):
        """Test that integer input raises ToDoValidationError."""
        with pytest.raises(ToDoValidationError):
            validator.validate(123)

    def test_validate_float_raises_error(self, validator):
        """Test that float input raises ToDoValidationError."""
        with pytest.raises(ToDoValidationError):
            validator.validate(123.45)

    def test_validate_list_raises_error(self, validator):
        """Test that list input raises ToDoValidationError."""
        with pytest.raises(ToDoValidationError):
            validator.validate([])

    def test_validate_dict_raises_error(self, validator):
        """Test that dict input raises ToDoValidationError."""
        with pytest.raises(ToDoValidationError):
            validator.validate({})

    def test_validate_boolean_raises_error(self, validator):
        """Test that boolean input raises ToDoValidationError."""
        with pytest.raises(ToDoValidationError):
            validator.validate(True)


class TestUUIDValidatorEdgeCases:
    """Test UUIDValidator edge cases."""

    def test_validate_all_zeros_uuid(self, validator):
        """Test validation of all-zeros UUID."""
        uuid_str = "00000000-0000-0000-0000-000000000000"
        result = validator.validate(uuid_str)
        assert isinstance(result, uuid.UUID)
        assert str(result) == uuid_str

    def test_validate_all_ones_uuid(self, validator):
        """Test validation of all-ones UUID (max value)."""
        uuid_str = "ffffffff-ffff-ffff-ffff-ffffffffffff"
        result = validator.validate(uuid_str)
        assert isinstance(result, uuid.UUID)

    def test_validate_uuid_preserves_version(self, validator):
        """Test validation preserves UUID version."""
        uuid_v4 = uuid.uuid4()
        result = validator.validate(str(uuid_v4))
        assert result.version == uuid_v4.version

    def test_consecutive_validations_same_uuid(self, validator):
        """Test consecutive validations of same UUID string."""
        uuid_str = "550e8400-e29b-41d4-a716-446655440000"
        result1 = validator.validate(uuid_str)
        result2 = validator.validate(uuid_str)
        assert result1 == result2

    def test_validate_different_uuid_formats_equal(self, validator):
        """Test different UUID formats validate to same UUID."""
        uuid_with_hyphens = "550e8400-e29b-41d4-a716-446655440000"
        uuid_without_hyphens = "550e8400e29b41d4a716446655440000"

        result1 = validator.validate(uuid_with_hyphens)
        result2 = validator.validate(uuid_without_hyphens)
        assert result1 == result2
