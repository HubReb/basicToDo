"""Async SQLAlchemy database setup."""
import datetime
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy import Boolean, CheckConstraint, Column, String, TIMESTAMP
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.sql import func
from sqlalchemy_utils import UUIDType  # type: ignore[import-untyped]

from backend.app.config import settings


class Base(DeclarativeBase):
    pass


engine = create_async_engine(settings.database_url, echo=False)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


@asynccontextmanager
async def safe_session_scope() -> AsyncGenerator[AsyncSession, None]:
    session = AsyncSessionLocal()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


class ToDoORM(Base):
    __tablename__ = "toDo"

    id = Column(UUIDType(binary=False), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False, index=True)
    description = Column(String(255), nullable=True)
    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at = Column(TIMESTAMP(timezone=True), nullable=True)
    deleted = Column(Boolean, nullable=False, default=False)
    done = Column(Boolean, nullable=False, default=False)

    __table_args__ = (
        CheckConstraint("length(title) <= 255", name="title_length_check"),
        CheckConstraint("length(description) <= 255", name="description_length_check"),
    )

    def __repr__(self) -> str:
        return f"<ToDo(id={self.id}, title='{self.title}')>"
