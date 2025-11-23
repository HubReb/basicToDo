from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Mapped, mapped_column  # type: ignore[attr-defined]


@dataclass
class ToDoEntryData:
    """The todo entry data class."""

    id: UUID
    title: str
    description: str
    created_at: datetime | None
    updated_at: datetime | None
    deleted: Mapped[bool] = mapped_column(default=False, name='deleted')
    done: bool = False