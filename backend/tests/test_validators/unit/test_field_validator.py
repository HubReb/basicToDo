"""Unit tests for FieldValidator."""
from unittest.mock import MagicMock

import pytest

from backend.app.business_logic.exceptions import ToDoValidationError
from backend.app.business_logic.validators.field_validator import FieldValidator


@pytest.fixture
def mock_logger():
    """Create a mock logger."""
    return MagicMock()


@pytest.fixture
def mock_input_sanitizer():
    """Create a mock InputSanitizer."""
    return MagicMock()


@pytest.fixture
def validator(mock_input_sanitizer, mock_logger):
    """Create FieldValidator with mocked dependencies."""
    return FieldValidator(mock_input_sanitizer, mock_logger)


class TestFieldValidatorRequired:
    """Test FieldValidator.validate_required() method."""

    def test_validate_required_valid_text(self, validator, mock_input_sanitizer):
        """Test validate_required with valid text."""
        mock_input_sanitizer.validate.return_value = "Valid Title"

        result = validator.validate_required("Valid Title", "title")

        assert result == "Valid Title"
        mock_input_sanitizer.validate.assert_called_once_with("Valid Title")

    def test_validate_required_strips_whitespace(self, validator, mock_input_sanitizer):
        """Test validate_required strips whitespace via sanitizer."""
        mock_input_sanitizer.validate.return_value = "Trimmed"

        result = validator.validate_required("  Trimmed  ", "title")

        assert result == "Trimmed"
        mock_input_sanitizer.validate.assert_called_once_with("  Trimmed  ")

    def test_validate_required_empty_string_raises_error(self, validator, mock_input_sanitizer, mock_logger):
        """Test validate_required raises error for empty string."""
        mock_input_sanitizer.validate.return_value = ""

        with pytest.raises(ToDoValidationError) as exc_info:
            validator.validate_required("", "title")

        assert "title is required" in str(exc_info.value)
        mock_logger.warning.assert_called_once()

    def test_validate_required_whitespace_only_raises_error(self, validator, mock_input_sanitizer, mock_logger):
        """Test validate_required raises error for whitespace-only string."""
        mock_input_sanitizer.validate.return_value = ""  # Sanitizer strips to empty

        with pytest.raises(ToDoValidationError) as exc_info:
            validator.validate_required("   ", "title")

        assert "title is required" in str(exc_info.value)
        mock_logger.warning.assert_called_once()

    def test_validate_required_none_raises_error(self, validator, mock_input_sanitizer, mock_logger):
        """Test validate_required raises error for None."""
        mock_input_sanitizer.validate.return_value = None

        with pytest.raises(ToDoValidationError) as exc_info:
            validator.validate_required(None, "description")

        assert "description is required" in str(exc_info.value)
        mock_logger.warning.assert_called_once()

    @pytest.mark.parametrize("field_name", [
        "title",
        "description",
        "name",
        "email",
        "user_id",
    ])
    def test_validate_required_custom_field_names(self, validator, mock_input_sanitizer, mock_logger, field_name):
        """Test validate_required uses custom field names in error messages."""
        mock_input_sanitizer.validate.return_value = ""

        with pytest.raises(ToDoValidationError) as exc_info:
            validator.validate_required("", field_name)

        assert field_name in str(exc_info.value)

    def test_validate_required_sql_injection_propagates_error(self, validator, mock_input_sanitizer):
        """Test validate_required propagates SQL injection errors from sanitizer."""
        mock_input_sanitizer.validate.side_effect = ToDoValidationError("SQL injection detected")

        with pytest.raises(ToDoValidationError) as exc_info:
            validator.validate_required("DROP TABLE", "title")

        assert "SQL injection detected" in str(exc_info.value)


class TestFieldValidatorOptional:
    """Test FieldValidator.validate_optional() method."""

    def test_validate_optional_valid_text(self, validator, mock_input_sanitizer):
        """Test validate_optional with valid text."""
        mock_input_sanitizer.validate.return_value = "Valid Description"

        result = validator.validate_optional("Valid Description")

        assert result == "Valid Description"
        mock_input_sanitizer.validate.assert_called_once_with("Valid Description")

    def test_validate_optional_empty_string_returns_empty(self, validator, mock_input_sanitizer):
        """Test validate_optional returns empty string for empty input."""
        mock_input_sanitizer.validate.return_value = ""

        result = validator.validate_optional("")

        assert result == ""

    def test_validate_optional_whitespace_only_returns_empty(self, validator, mock_input_sanitizer):
        """Test validate_optional returns empty string for whitespace-only input."""
        mock_input_sanitizer.validate.return_value = ""  # Sanitizer strips to empty

        result = validator.validate_optional("   ")

        assert result == ""

    def test_validate_optional_none_returns_empty(self, validator, mock_input_sanitizer):
        """Test validate_optional returns empty string for None."""
        mock_input_sanitizer.validate.return_value = None

        result = validator.validate_optional(None)

        assert result == ""

    def test_validate_optional_strips_whitespace(self, validator, mock_input_sanitizer):
        """Test validate_optional strips whitespace via sanitizer."""
        mock_input_sanitizer.validate.return_value = "Trimmed"

        result = validator.validate_optional("  Trimmed  ")

        assert result == "Trimmed"

    def test_validate_optional_sql_injection_propagates_error(self, validator, mock_input_sanitizer):
        """Test validate_optional propagates SQL injection errors from sanitizer."""
        mock_input_sanitizer.validate.side_effect = ToDoValidationError("SQL injection detected")

        with pytest.raises(ToDoValidationError) as exc_info:
            validator.validate_optional("DROP TABLE")

        assert "SQL injection detected" in str(exc_info.value)

    def test_validate_optional_with_text_content(self, validator, mock_input_sanitizer):
        """Test validate_optional preserves text content."""
        text = "This is a longer description with multiple words"
        mock_input_sanitizer.validate.return_value = text

        result = validator.validate_optional(text)

        assert result == text


class TestFieldValidatorGeneric:
    """Test FieldValidator.validate() generic method for LSP compliance."""

    def test_validate_defaults_to_required(self, validator, mock_input_sanitizer):
        """Test validate() defaults to required field validation."""
        mock_input_sanitizer.validate.return_value = "Test"

        result = validator.validate("Test", field_name="title")

        assert result == "Test"

    def test_validate_with_required_true(self, validator, mock_input_sanitizer):
        """Test validate() with required=True."""
        mock_input_sanitizer.validate.return_value = "Test"

        result = validator.validate("Test", field_name="title", required=True)

        assert result == "Test"

    def test_validate_with_required_false(self, validator, mock_input_sanitizer):
        """Test validate() with required=False behaves as optional."""
        mock_input_sanitizer.validate.return_value = "Test"

        result = validator.validate("Test", required=False)

        assert result == "Test"

    def test_validate_required_true_empty_raises_error(self, validator, mock_input_sanitizer, mock_logger):
        """Test validate() with required=True raises error for empty."""
        mock_input_sanitizer.validate.return_value = ""

        with pytest.raises(ToDoValidationError):
            validator.validate("", field_name="title", required=True)

    def test_validate_required_false_empty_returns_empty(self, validator, mock_input_sanitizer):
        """Test validate() with required=False returns empty for empty."""
        mock_input_sanitizer.validate.return_value = ""

        result = validator.validate("", required=False)

        assert result == ""

    def test_validate_default_field_name(self, validator, mock_input_sanitizer, mock_logger):
        """Test validate() uses default field name when not provided."""
        mock_input_sanitizer.validate.return_value = ""

        with pytest.raises(ToDoValidationError) as exc_info:
            validator.validate("", required=True)

        assert "field is required" in str(exc_info.value)


class TestFieldValidatorEdgeCases:
    """Test FieldValidator edge cases."""

    def test_validate_very_long_required_field(self, validator, mock_input_sanitizer):
        """Test validate_required with very long string."""
        long_text = "a" * 10000
        mock_input_sanitizer.validate.return_value = long_text

        result = validator.validate_required(long_text, "title")

        assert result == long_text

    def test_validate_very_long_optional_field(self, validator, mock_input_sanitizer):
        """Test validate_optional with very long string."""
        long_text = "b" * 10000
        mock_input_sanitizer.validate.return_value = long_text

        result = validator.validate_optional(long_text)

        assert result == long_text

    def test_validate_unicode_required_field(self, validator, mock_input_sanitizer):
        """Test validate_required with Unicode characters."""
        unicode_text = "Hello 世界 🌍"
        mock_input_sanitizer.validate.return_value = unicode_text

        result = validator.validate_required(unicode_text, "title")

        assert result == unicode_text

    def test_validate_special_characters_required(self, validator, mock_input_sanitizer):
        """Test validate_required with special characters."""
        special_text = "Test@#$%&*()_+=[]{}|"
        mock_input_sanitizer.validate.return_value = special_text

        result = validator.validate_required(special_text, "title")

        assert result == special_text

    def test_consecutive_validations_same_input(self, validator, mock_input_sanitizer):
        """Test consecutive validations produce consistent results."""
        mock_input_sanitizer.validate.return_value = "Test"

        result1 = validator.validate_required("Test", "title")
        result2 = validator.validate_required("Test", "title")

        assert result1 == result2 == "Test"
