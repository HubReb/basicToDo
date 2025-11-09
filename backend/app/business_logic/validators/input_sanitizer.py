"""Input sanitizer for SQL injection protection."""
import re
from typing import Any

from backend.app.business_logic.exceptions import ToDoValidationError
from backend.app.business_logic.validators.validator_interface import ValidatorInterface
from backend.app.logger import CustomLogger


class InputSanitizer(ValidatorInterface):
    """Validates and sanitizes text input to prevent SQL injection attacks."""

    _SQL_INJECTION_RE = re.compile(
        r"(?i)(--|;|/\*|\*/|\bxp_cmdshell\b|\b(?:drop|delete|insert|update|exec(?:ute)?|union|select|shutdown|create|alter|rename|truncate|declare|OR)\b)"
    )

    def __init__(self, logger: CustomLogger):
        self.logger = logger

    def validate(self, value: Any, *args: Any, **kwargs: Any) -> str | None:
        """Sanitize input to prevent obvious SQL-injection patterns.

        - Rejects operator tokens (e.g. ';', '--', '/*', '*/') anywhere in string.
        - Rejects SQL keywords as whole words (so 'updated' is allowed).
        - Returns stripped string if OK.
        """
        if value is None:
            return None

        str_value: str
        if not isinstance(value, str):
            self.logger.warning("InputSanitizer received non-string value: %s", type(value))
            str_value = str(value)
        else:
            str_value = value

        if self._SQL_INJECTION_RE.search(str_value):
            self.logger.warning("SQL injection attempt detected: %s", str_value)
            raise ToDoValidationError(f"Invalid characters or SQL keywords in input: {str_value!r}")

        return str_value.strip()
