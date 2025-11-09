"""Unit tests for InputSanitizer."""
from unittest.mock import MagicMock

import pytest

from backend.app.business_logic.exceptions import ToDoValidationError
from backend.app.business_logic.validators.input_sanitizer import InputSanitizer


@pytest.fixture
def mock_logger():
    """Create a mock logger."""
    return MagicMock()


@pytest.fixture
def sanitizer(mock_logger):
    """Create InputSanitizer with mocked logger."""
    return InputSanitizer(mock_logger)


class TestInputSanitizerValidText:
    """Test InputSanitizer with valid text inputs."""

    def test_validate_simple_text(self, sanitizer):
        """Test validation of simple text without special characters."""
        result = sanitizer.validate("Hello World")
        assert result == "Hello World"

    def test_validate_text_with_spaces(self, sanitizer):
        """Test validation preserves internal spaces."""
        result = sanitizer.validate("This is a test")
        assert result == "This is a test"

    def test_validate_text_with_numbers(self, sanitizer):
        """Test validation allows numbers."""
        result = sanitizer.validate("Test123")
        assert result == "Test123"

    def test_validate_text_with_special_chars(self, sanitizer):
        """Test validation allows safe special characters."""
        result = sanitizer.validate("Test@#$%&*()_+=[]{}|:<>?,./")
        assert result == "Test@#$%&*()_+=[]{}|:<>?,./"

    def test_validate_unicode_text(self, sanitizer):
        """Test validation handles Unicode characters."""
        result = sanitizer.validate("Hello 世界 🌍")
        assert result == "Hello 世界 🌍"

    def test_validate_strips_leading_whitespace(self, sanitizer):
        """Test validation strips leading whitespace."""
        result = sanitizer.validate("  Hello")
        assert result == "Hello"

    def test_validate_strips_trailing_whitespace(self, sanitizer):
        """Test validation strips trailing whitespace."""
        result = sanitizer.validate("Hello  ")
        assert result == "Hello"

    def test_validate_strips_both_whitespace(self, sanitizer):
        """Test validation strips both leading and trailing whitespace."""
        result = sanitizer.validate("  Hello  ")
        assert result == "Hello"

    def test_validate_allows_word_containing_sql_keyword(self, sanitizer):
        """Test validation allows words containing SQL keywords (e.g., 'updated')."""
        result = sanitizer.validate("This was updated yesterday")
        assert result == "This was updated yesterday"


class TestInputSanitizerNoneAndEmpty:
    """Test InputSanitizer with None and empty inputs."""

    def test_validate_none_returns_none(self, sanitizer):
        """Test validation of None returns None."""
        result = sanitizer.validate(None)
        assert result is None

    def test_validate_empty_string_returns_empty(self, sanitizer):
        """Test validation of empty string returns empty string."""
        result = sanitizer.validate("")
        assert result == ""

    def test_validate_whitespace_only_returns_empty(self, sanitizer):
        """Test validation of whitespace-only string returns empty string."""
        result = sanitizer.validate("   ")
        assert result == ""


class TestInputSanitizerNonStringValues:
    """Test InputSanitizer with non-string inputs."""

    def test_validate_integer(self, sanitizer, mock_logger):
        """Test validation converts integer to string."""
        result = sanitizer.validate(123)
        assert result == "123"
        mock_logger.warning.assert_called_once()

    def test_validate_float(self, sanitizer, mock_logger):
        """Test validation converts float to string."""
        result = sanitizer.validate(123.45)
        assert result == "123.45"
        mock_logger.warning.assert_called_once()

    def test_validate_boolean(self, sanitizer, mock_logger):
        """Test validation converts boolean to string."""
        result = sanitizer.validate(True)
        assert result == "True"
        mock_logger.warning.assert_called_once()


@pytest.mark.parametrize("sql_pattern,description", [
    ("--", "double dash comment"),
    (";", "semicolon separator"),
    ("/*", "multi-line comment start"),
    ("*/", "multi-line comment end"),
    ("DROP TABLE users", "DROP keyword"),
    ("DELETE FROM users", "DELETE keyword"),
    ("INSERT INTO users", "INSERT keyword"),
    ("UPDATE users SET", "UPDATE keyword"),
    ("SELECT * FROM users", "SELECT keyword"),
    ("UNION SELECT", "UNION keyword"),
    ("EXEC sp_executesql", "EXEC keyword"),
    ("EXECUTE sp_executesql", "EXECUTE keyword"),
    ("xp_cmdshell 'dir'", "xp_cmdshell"),
    ("SHUTDOWN WITH NOWAIT", "SHUTDOWN keyword"),
    ("CREATE TABLE test", "CREATE keyword"),
    ("ALTER TABLE users", "ALTER keyword"),
    ("RENAME TABLE users", "RENAME keyword"),
    ("TRUNCATE TABLE users", "TRUNCATE keyword"),
    ("DECLARE @var", "DECLARE keyword"),
    ("1=1 OR 1=1", "OR keyword"),
    ("drop table users", "lowercase DROP"),
    ("DeLeTe FrOm users", "mixed case DELETE"),
    ("Test; DROP TABLE", "semicolon followed by DROP"),
    ("Test -- comment", "double dash at end"),
    ("/* malicious */", "complete comment block"),
])
class TestInputSanitizerSQLInjection:
    """Test InputSanitizer detects SQL injection patterns."""

    def test_sql_injection_pattern(self, sanitizer, mock_logger, sql_pattern, description):
        """Test that SQL injection pattern is detected and rejected."""
        with pytest.raises(ToDoValidationError) as exc_info:
            sanitizer.validate(sql_pattern)

        assert "Invalid characters or SQL keywords in input" in str(exc_info.value)
        mock_logger.warning.assert_called_once()
        assert "SQL injection attempt detected" in str(mock_logger.warning.call_args)


class TestInputSanitizerEdgeCases:
    """Test InputSanitizer edge cases."""

    def test_validate_very_long_string(self, sanitizer):
        """Test validation of very long strings."""
        long_string = "a" * 10000
        result = sanitizer.validate(long_string)
        assert result == long_string

    def test_validate_newlines(self, sanitizer):
        """Test validation allows newlines."""
        result = sanitizer.validate("Line1\nLine2")
        assert result == "Line1\nLine2"

    def test_validate_tabs(self, sanitizer):
        """Test validation allows tabs."""
        result = sanitizer.validate("Tab\there")
        assert result == "Tab\there"

    def test_validate_single_quote(self, sanitizer):
        """Test validation allows single quotes (not SQL injection)."""
        result = sanitizer.validate("It's a test")
        assert result == "It's a test"

    def test_validate_double_quote(self, sanitizer):
        """Test validation allows double quotes."""
        result = sanitizer.validate('He said "hello"')
        assert result == 'He said "hello"'
