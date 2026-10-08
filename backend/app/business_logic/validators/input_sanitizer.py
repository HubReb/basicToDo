"""Input sanitizer: normalises text input."""

from typing import Any

from backend.app.business_logic.validators.validator_interface import ValidatorInterface
from backend.app.logger import CustomLogger


class InputSanitizer(ValidatorInterface):
    """Normalises text input: strips surrounding whitespace.

    It no longer rejects SQL keywords or operator tokens (Q6.1): that list
    turned away ordinary titles such as "Tea or coffee" and protected
    nothing, since every query binds its values as parameters.
    """

    def __init__(self, logger: CustomLogger):
        self.logger = logger

    def validate(self, value: Any, *args: Any, **kwargs: Any) -> str | None:
        """Return the value as a stripped string, or None for None."""
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

        return str_value.strip()
