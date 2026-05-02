"""Input sanitizer for SQL injection protection."""

import re
from typing import Any

from backend.app.business_logic.exceptions import ToDoValidationError
from backend.app.business_logic.validators.validator_interface import ValidatorInterface
from backend.app.logger import CustomLogger


class InputSanitizer(ValidatorInterface):
    """Validates and sanitizes text input to prevent SQL injection attacks."""

    _SQL_INJECTION_RE = re.compile(r"--|;|/\*|\*/|\bxp_cmdshell\b", re.IGNORECASE)

    def __init__(self, logger: CustomLogger):
        self.logger = logger

    def validate(self, value: Any, *args: Any, **kwargs: Any) -> str | None:
        """Sanitize input to prevent obvious SQL-injection patterns.

        Rejects only structural attack markers (statement terminators and
        comment delimiters: ';', '--', '/*', '*/', plus xp_cmdshell). Bare
        SQL keywords are allowed, because (a) the repository uses
        parameterized queries which already neutralize them and (b)
        blocking words like 'delete', 'update', 'create' rejects legitimate
        TODO content like 'Update resume' or 'Delete spam emails'.
        """
        if value is None:
            return None

        str_value: str
        if not isinstance(value, str):
            self.logger.warning(
                "InputSanitizer received non-string value: %s", type(value)
            )
            str_value = str(value)
        else:
            str_value = value

        if self._SQL_INJECTION_RE.search(str_value):
            self.logger.warning("SQL injection attempt detected: %s", str_value)
            raise ToDoValidationError(
                f"Invalid characters or SQL keywords in input: {str_value!r}"
            )

        return str_value.strip()
