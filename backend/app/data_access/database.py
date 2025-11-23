import datetime
import os
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from sqlalchemy import Boolean, CheckConstraint, Column, String, TIMESTAMP, Table, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, registry, sessionmaker
from sqlalchemy.pool import QueuePool
from sqlalchemy.sql import func
from sqlalchemy_utils import UUIDType  # type: ignore[import-untyped]

from backend.app.models.todo import ToDoEntryData

Base = declarative_base()


def get_safe_database_url() -> str:
    """Return a validated and safe database URL."""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        # Use relative path from project root or current working directory
        # This works in both local dev and CI environments
        db_path = Path("backend/todo.db")

        # Ensure parent directory exists
        db_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert to absolute path for SQLite
        db_url = f"sqlite:///{db_path.absolute()}"
    elif not db_url.startswith(("sqlite://", "postgresql://", "mysql://")):
        raise RuntimeError(f"Invalid or unsafe DATABASE_URL: {db_url}")
    return db_url


DATABASE_URL = get_safe_database_url()

engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine, expire_on_commit=False
)  # type: ignore

@contextmanager
def safe_session_scope() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise
    finally:
        session.close()


# ORM-Table Definition (with constraint)
class ToDoORM(Base):  # type: ignore
    __tablename__ = "toDo"

    id = Column(UUIDType(binary=False), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False, index=True)
    description = Column(String(255), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.datetime.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=True)
    deleted = Column(Boolean, nullable=False, default=False)
    done = Column(Boolean, nullable=False, default=False)

    __table_args__ = (
        CheckConstraint("length(title) <= 255", name="title_length_check"),
        CheckConstraint("length(description) <= 255", name="description_length_check"),
    )

    def __repr__(self) -> str:
        return f"<ToDo(id={self.id}, title='{self.title}')>"


mapper_registry = registry()
to_do_table = Table(
    "toDo",
    mapper_registry.metadata,
    Column("id", UUIDType(binary=False), primary_key=True, index=True, default=uuid.uuid4),
    Column("title", String(255), nullable=False, index=True),
    Column("description", String(255), nullable=True),
    Column("created_at", TIMESTAMP(timezone=True), nullable=False, default=func.now()),
    Column("updated_at", TIMESTAMP(timezone=True), nullable=True, default=func.now()),
    Column("deleted", Boolean, nullable=False, default=False),
    Column("done", Boolean, nullable=False, default=False),
)
mapper_registry.map_imperatively(ToDoEntryData, to_do_table)