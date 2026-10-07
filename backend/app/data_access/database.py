import os
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool

from backend.app.data_access.database_file import DEFAULT_DATABASE_PATH, protect
from backend.app.models.todo import Base

__all__ = [
    "Base",
    "DATABASE_URL",
    "SessionLocal",
    "engine",
    "get_safe_database_url",
    "loggable_url",
    "safe_session_scope",
]


def get_safe_database_url() -> str:
    """Return a validated and safe database URL."""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        # SEC-014: next to the backend package, not under the working directory.
        db_url = f"sqlite:///{DEFAULT_DATABASE_PATH}"
    elif not db_url.startswith(("sqlite://", "postgresql://", "mysql://")):
        raise RuntimeError(f"Invalid or unsafe DATABASE_URL: {db_url}")
    return db_url


def loggable_url(url: str) -> str:
    """The URL without its password and query string, which may carry one."""
    return make_url(url).set(query={}).render_as_string(hide_password=True)


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
# SEC-014: a new database file is created 0600; an existing one is checked.
protect(engine, DATABASE_URL)

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
