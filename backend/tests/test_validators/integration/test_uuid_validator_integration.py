"""Integration tests for UUIDValidator with real logger."""
import uuid

import pytest

from backend.app.business_logic.exceptions import ToDoValidationError
from backend.app.business_logic.validators.uuid_validator import UUIDValidator
from backend.app.logger import CustomLogger


@pytest.fixture
def validator():
    """Create UUIDValidator with real logger."""
    logger = CustomLogger("UUIDValidatorIntegrationTest")
    return UUIDValidator(logger)


class TestUUIDValidatorRealWorldScenarios:
    """Test UUIDValidator in realistic ToDo application scenarios."""

    def test_validate_todo_id_from_api(self, validator):
        """Test validation of ToDo ID from API request."""
        # Simulate UUID from API request (string format)
        api_uuid = str(uuid.uuid4())
        result = validator.validate(api_uuid)
        assert isinstance(result, uuid.UUID)
        assert str(result) == api_uuid

    def test_validate_todo_id_from_database(self, validator):
        """Test validation of ToDo ID from database (UUID object)."""
        # Simulate UUID from database (UUID object)
        db_uuid = uuid.uuid4()
        result = validator.validate(db_uuid)
        assert result == db_uuid
        assert result is db_uuid  # Same object

    def test_validate_multiple_todo_ids_batch(self, validator):
        """Test validation of multiple ToDo IDs."""
        todo_ids = [str(uuid.uuid4()) for _ in range(10)]
        results = [validator.validate(todo_id) for todo_id in todo_ids]

        assert len(results) == 10
        assert all(isinstance(r, uuid.UUID) for r in results)
        assert len(set(results)) == 10  # All unique

    def test_validate_uuid_from_url_parameter(self, validator):
        """Test validation of UUID from URL parameter."""
        # URL parameters come as strings
        url_param = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        result = validator.validate(url_param)
        assert isinstance(result, uuid.UUID)

    def test_validate_uuid_roundtrip(self, validator):
        """Test UUID validation roundtrip (create -> validate -> convert)."""
        original_uuid = uuid.uuid4()
        uuid_string = str(original_uuid)
        validated = validator.validate(uuid_string)

        assert validated == original_uuid
        assert str(validated) == uuid_string


class TestUUIDValidatorErrorScenarios:
    """Test UUIDValidator error handling in real scenarios."""

    def test_reject_malformed_user_input(self, validator):
        """Test rejection of malformed user input."""
        malformed_inputs = [
            "123-456-789",
            "not-a-uuid-at-all",
            "12345678",
            "",
        ]

        for malformed_input in malformed_inputs:
            with pytest.raises(ToDoValidationError):
                validator.validate(malformed_input)

    def test_reject_sql_injection_as_uuid(self, validator):
        """Test rejection of SQL injection attempt as UUID."""
        sql_injection = "'; DROP TABLE todos; --"
        with pytest.raises(ToDoValidationError):
            validator.validate(sql_injection)

    def test_reject_script_injection_as_uuid(self, validator):
        """Test rejection of script injection attempt as UUID."""
        script_injection = "<script>alert('xss')</script>"
        with pytest.raises(ToDoValidationError):
            validator.validate(script_injection)


class TestUUIDValidatorDataConsistency:
    """Test UUIDValidator maintains data consistency."""

    def test_same_uuid_string_always_same_result(self, validator):
        """Test same UUID string always produces same result."""
        uuid_str = "550e8400-e29b-41d4-a716-446655440000"

        results = [validator.validate(uuid_str) for _ in range(5)]
        assert all(r == results[0] for r in results)

    def test_uuid_equality_across_formats(self, validator):
        """Test UUID equality across different input formats."""
        base_uuid = "550e8400-e29b-41d4-a716-446655440000"
        formats = [
            base_uuid,
            base_uuid.upper(),
            base_uuid.replace("-", ""),
            f"{{{base_uuid}}}",
            f"urn:uuid:{base_uuid}",
        ]

        results = [validator.validate(fmt) for fmt in formats]
        assert all(r == results[0] for r in results)

    def test_different_validators_same_result(self):
        """Test different validator instances produce same result."""
        logger1 = CustomLogger("Test1")
        logger2 = CustomLogger("Test2")
        validator1 = UUIDValidator(logger1)
        validator2 = UUIDValidator(logger2)

        uuid_str = "550e8400-e29b-41d4-a716-446655440000"
        assert validator1.validate(uuid_str) == validator2.validate(uuid_str)


class TestUUIDValidatorBoundaryConditions:
    """Test UUIDValidator boundary conditions."""

    def test_validate_nil_uuid(self, validator):
        """Test validation of nil UUID (all zeros)."""
        nil_uuid = "00000000-0000-0000-0000-000000000000"
        result = validator.validate(nil_uuid)
        assert result == uuid.UUID(int=0)

    def test_validate_max_uuid(self, validator):
        """Test validation of maximum UUID value."""
        max_uuid = "ffffffff-ffff-ffff-ffff-ffffffffffff"
        result = validator.validate(max_uuid)
        assert isinstance(result, uuid.UUID)

    def test_uuid_version_preserved(self, validator):
        """Test UUID version information is preserved."""
        # UUID v4
        uuid_v4_str = str(uuid.uuid4())
        result = validator.validate(uuid_v4_str)
        assert result.version == 4

    def test_validate_uuid_with_leading_trailing_spaces_fails(self, validator):
        """Test UUID with spaces fails validation."""
        uuid_with_spaces = "  550e8400-e29b-41d4-a716-446655440000  "
        # Python's UUID constructor doesn't strip spaces
        with pytest.raises(ToDoValidationError):
            validator.validate(uuid_with_spaces)
