"""A ToDo data class"""

from typing import Annotated, Any
from pydantic import BaseModel, PlainValidator


def exists(value: Any) -> Any:
    """Verify value is not null."""
    if value is not None:
        return value
    raise ValueError("value must not be None.")


class ToDo(BaseModel):
    """The todo data class."""

    id: Annotated[str, PlainValidator(exists)]
    description: Annotated[str, PlainValidator(exists)]

    def update(self, description: str):
        """Update the item description."""
        if not description:
            raise ValueError("description must not be None.")
        self.description = description
