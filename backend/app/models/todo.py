from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class ToDoEntryData:
    """The todo entry data class."""

    id: UUID
    title: str
    description: str
    created_at: datetime | None
    updated_at: datetime | None
    deleted: bool = False
    done: bool = False