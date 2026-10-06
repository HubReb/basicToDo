import os
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool

from backend.app.models.todo import Base

__all__ = [
    "Base",
    "DATABASE_URL",
    "SessionLocal",
    "engine",
    "get_safe_database_url",
    "safe_session_scope",
]


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
    connect_args=(
        {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
    ),
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine, expire_on_commit=False
)


@contextmanager
def safe_session_scope() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
