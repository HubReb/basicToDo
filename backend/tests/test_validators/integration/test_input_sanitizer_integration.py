"""Integration tests for InputSanitizer with real logger."""

import pytest

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
    """Former attack vectors: since Q6.1 ordinary text, safe through bound parameters."""

    def test_keeps_sql_like_title_as_text(self, sanitizer):
        """SQL in a title is ordinary text (Q6.1)."""
        malicious_title = "'; DROP TABLE todos; --"
        assert sanitizer.validate(malicious_title) == malicious_title.strip()

    def test_keeps_sql_like_description_as_text(self, sanitizer):
        """SQL in a description is ordinary text (Q6.1)."""
        malicious_desc = "Test /* */ SELECT password FROM users"
        assert sanitizer.validate(malicious_desc) == malicious_desc.strip()

    def test_keeps_union_select_as_text(self, sanitizer):
        """A UNION SELECT string is ordinary text (Q6.1)."""
        attack = "1' UNION SELECT username, password FROM users--"
        assert sanitizer.validate(attack) == attack.strip()

    def test_keeps_waitfor_delay_as_text(self, sanitizer):
        """A WAITFOR DELAY string is ordinary text (Q6.1)."""
        attack = "1'; WAITFOR DELAY '00:00:05'--"
        assert sanitizer.validate(attack) == attack.strip()

    def test_keeps_stacked_query_as_text(self, sanitizer):
        """A stacked-query string is ordinary text (Q6.1)."""
        attack = "value'; DELETE FROM todos WHERE '1'='1"
        assert sanitizer.validate(attack) == attack.strip()


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

    def test_sql_keyword_alone_is_text(self, sanitizer):
        """A lone SQL keyword is ordinary text, stripped (Q6.1)."""
        assert sanitizer.validate("  DROP  ") == "  DROP  ".strip()

    def test_sql_keyword_at_start_is_text(self, sanitizer):
        """A SQL keyword at the start is ordinary text (Q6.1)."""
        assert sanitizer.validate("DROP this idea") == "DROP this idea".strip()

    def test_sql_keyword_at_end_is_text(self, sanitizer):
        """A SQL keyword at the end is ordinary text (Q6.1)."""
        assert sanitizer.validate("Please DROP") == "Please DROP".strip()
