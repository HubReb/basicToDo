"""Validator interface for ensuring LSP compliance."""
from abc import ABC, abstractmethod
from typing import Any


class ValidatorInterface(ABC):
    """Common interface for all validators."""

    @abstractmethod
    def validate(self, value: Any, *args: Any, **kwargs: Any) -> Any:
        """Validate input and return validated/transformed value."""
        pass
