"""Integration tests for InputSanitizer with real logger."""
import pytest

from backend.app.business_logic.exceptions import ToDoValidationError
from backend.app.business_logic.validators.input_sanitizer import InputSanitizer
from backend.app.logger import CustomLogger


@pytest.fixture
def sanitizer():
    """Create InputSanitizer with real logger."""
    logger = CustomLogger("InputSanitizerIntegrationTest")
    return InputSanitizer(logger)


class TestInputSanitizerRealWorldScenarios:
    """Test InputSanitizer in realistic ToDo application scenarios."""

    def test_sanitize_typical_todo_title(self, sanitizer):
        """Test sanitization of typical ToDo title."""
        title = "Buy groceries for dinner"
        result = sanitizer.validate(title)
        assert result == "Buy groceries for dinner"

    def test_sanitize_todo_with_emojis(self, sanitizer):
        """Test sanitization preserves emojis."""
        title = "🎉 Birthday party planning 🎂"
        result = sanitizer.validate(title)
        assert result == "🎉 Birthday party planning 🎂"

    def test_sanitize_todo_with_dates(self, sanitizer):
        """Test sanitization of ToDo with dates."""
        title = "Meeting on 2024-01-15 at 3:30 PM"
        result = sanitizer.validate(title)
        assert result == "Meeting on 2024-01-15 at 3:30 PM"

    def test_sanitize_todo_with_urls(self, sanitizer):
        """Test sanitization preserves URLs."""
        description = "Check https://example.com for details"
        result = sanitizer.validate(description)
        assert result == "Check https://example.com for details"

    def test_sanitize_todo_with_email(self, sanitizer):
        """Test sanitization preserves email addresses."""
        description = "Contact user@example.com"
        result = sanitizer.validate(description)
        assert result == "Contact user@example.com"

    def test_sanitize_multiline_description(self, sanitizer):
        """Test sanitization of multi-line descriptions."""
        description = "Step 1: Do this\nStep 2: Do that\nStep 3: Finish"
        result = sanitizer.validate(description)
        assert result == "Step 1: Do this\nStep 2: Do that\nStep 3: Finish"

    def test_sanitize_code_snippet_safe(self, sanitizer):
        """Test sanitization of safe code snippets."""
        description = "Run command: npm install"
        result = sanitizer.validate(description)
        assert result == "Run command: npm install"

    def test_sanitize_mathematical_expression(self, sanitizer):
        """Test sanitization of mathematical expressions."""
        description = "Calculate: (5 + 3) * 2 = 16"
        result = sanitizer.validate(description)
        assert result == "Calculate: (5 + 3) * 2 = 16"


class TestInputSanitizerAttackVectors:
    """Test InputSanitizer against common attack vectors."""

    def test_block_sql_injection_in_todo_title(self, sanitizer):
        """Test blocking SQL injection attempt in ToDo title."""
        malicious_title = "'; DROP TABLE todos; --"
        with pytest.raises(ToDoValidationError):
            sanitizer.validate(malicious_title)

    def test_block_sql_injection_in_description(self, sanitizer):
        """Test blocking SQL injection in description."""
        malicious_desc = "Test /* */ SELECT password FROM users"
        with pytest.raises(ToDoValidationError):
            sanitizer.validate(malicious_desc)

    def test_block_union_based_injection(self, sanitizer):
        """Test blocking UNION-based SQL injection."""
        attack = "1' UNION SELECT username, password FROM users--"
        with pytest.raises(ToDoValidationError):
            sanitizer.validate(attack)

    def test_block_time_based_injection(self, sanitizer):
        """Test blocking time-based SQL injection."""
        attack = "1'; WAITFOR DELAY '00:00:05'--"
        with pytest.raises(ToDoValidationError):
            sanitizer.validate(attack)

    def test_block_stacked_queries(self, sanitizer):
        """Test blocking stacked query injection."""
        attack = "value'; DELETE FROM todos WHERE '1'='1"
        with pytest.raises(ToDoValidationError):
            sanitizer.validate(attack)


class TestInputSanitizerDataConsistency:
    """Test InputSanitizer maintains data consistency."""

    def test_consecutive_validations_same_result(self, sanitizer):
        """Test that consecutive validations produce same result."""
        text = "  Test Title  "
        result1 = sanitizer.validate(text)
        result2 = sanitizer.validate(text)
        assert result1 == result2 == "Test Title"

    def test_validate_none_multiple_times(self, sanitizer):
        """Test validating None multiple times."""
        assert sanitizer.validate(None) is None
        assert sanitizer.validate(None) is None

    def test_validate_empty_multiple_times(self, sanitizer):
        """Test validating empty string multiple times."""
        assert sanitizer.validate("") == ""
        assert sanitizer.validate("   ") == ""

    def test_different_instances_same_behavior(self):
        """Test different sanitizer instances behave identically."""
        logger1 = CustomLogger("Test1")
        logger2 = CustomLogger("Test2")
        sanitizer1 = InputSanitizer(logger1)
        sanitizer2 = InputSanitizer(logger2)

        text = "  Hello World  "
        assert sanitizer1.validate(text) == sanitizer2.validate(text)


class TestInputSanitizerBoundaryConditions:
    """Test InputSanitizer boundary conditions."""

    def test_exactly_one_character(self, sanitizer):
        """Test validation of single character."""
        result = sanitizer.validate("a")
        assert result == "a"

    def test_exactly_sql_keyword_length(self, sanitizer):
        """Test words that are exactly SQL keyword length but valid."""
        result = sanitizer.validate("ORDERED")  # 7 chars like 'EXECUTE'
        assert result == "ORDERED"

    def test_whitespace_around_sql_keyword(self, sanitizer):
        """Test that isolated SQL keywords are caught."""
        with pytest.raises(ToDoValidationError):
            sanitizer.validate("  DROP  ")

    def test_sql_keyword_at_start(self, sanitizer):
        """Test SQL keyword at start of string."""
        with pytest.raises(ToDoValidationError):
            sanitizer.validate("DROP this idea")

    def test_sql_keyword_at_end(self, sanitizer):
        """Test SQL keyword at end of string."""
        with pytest.raises(ToDoValidationError):
            sanitizer.validate("Please DROP")
