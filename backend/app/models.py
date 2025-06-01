from dataclasses import dataclass
from uuid import UUID
from datetime import datetime


@dataclass
class ToDo:
    """The todo data class."""

    id: UUID
    title: str
    description: str
    created_at: datetime | None
    updated_at: datetime | None
    deleted: bool = False
    done: bool = False

    def update(self, values: dict) -> None:
        """Update all values given"""
        for key, val in values.items():
            # do not set attributes that are not defined
            if not getattr(self, key):
                continue
            setattr(self, key, val)
