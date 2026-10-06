"""The todo entry: a dataclass that is also the one mapping of the toDo table."""

import datetime
import uuid

from sqlalchemy import TIMESTAMP, Boolean, CheckConstraint, String, Uuid, func
from sqlalchemy.orm import DeclarativeBase, Mapped, MappedAsDataclass, mapped_column


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
    # func.now() is the database clock (UTC on SQLite). It fills updated_at
    # when an entry is inserted with updated_at=None (RULE-035).
    created_at: Mapped[datetime.datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, insert_default=func.now()
    )
    updated_at: Mapped[datetime.datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True, insert_default=func.now()
    )
    deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    done: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
