"""The todo entry: a dataclass that is also the one mapping of the toDo table."""

import datetime
import uuid
from typing import Any

from sqlalchemy import TIMESTAMP, Boolean, CheckConstraint, Dialect, String, Uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, MappedAsDataclass, mapped_column
from sqlalchemy.types import TypeDecorator


def utc_now() -> datetime.datetime:
    """The current time, timezone-aware in UTC (Q6.6)."""
    return datetime.datetime.now(datetime.timezone.utc)


class UTCDateTime(TypeDecorator[datetime.datetime]):
    """A timestamp stored as UTC, read back timezone-aware in UTC (Q6.6).

    The column type, and so the DDL, stays TIMESTAMP; SQLite keeps the text
    "YYYY-MM-DD HH:MM:SS.ffffff" without an offset, which this type defines
    as UTC. A naive value is refused: its zone would be a guess.
    """

    impl = TIMESTAMP
    cache_ok = True

    def __init__(self) -> None:
        super().__init__(timezone=True)

    def process_bind_param(
        self, value: datetime.datetime | None, dialect: Dialect
    ) -> datetime.datetime | None:
        if value is None:
            return None
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("timestamps must be timezone-aware")
        return value.astimezone(datetime.timezone.utc).replace(tzinfo=None)

    def process_result_value(
        self, value: Any | None, dialect: Dialect
    ) -> datetime.datetime | None:
        if value is None:
            return None
        stored: datetime.datetime = value  # SQLite gives a naive UTC datetime
        return stored.replace(tzinfo=datetime.timezone.utc)


class Base(DeclarativeBase):
    """Declarative base; its metadata holds the schema."""


class ToDoEntryData(MappedAsDataclass, Base):
    """The todo entry data class."""

    __tablename__ = "toDo"
    __table_args__ = (
        CheckConstraint("length(title) <= 255", name="title_length_check"),
        CheckConstraint("length(description) <= 255", name="description_length_check"),
    )

    # Uuid stores CHAR(32) hex on SQLite, as sqlalchemy_utils.UUIDType(binary=False) did.
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, insert_default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Both in UTC (Q6.6). A None at insert means "now"; the builder sets both
    # to the same instant, and the repository refreshes updated_at on every change.
    created_at: Mapped[datetime.datetime | None] = mapped_column(
        UTCDateTime(), nullable=False, insert_default=utc_now
    )
    updated_at: Mapped[datetime.datetime | None] = mapped_column(
        UTCDateTime(), nullable=True, insert_default=utc_now
    )
    deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    done: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
