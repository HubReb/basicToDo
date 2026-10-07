#!/usr/bin/env python3
"""Initialize database schema for testing/deployment."""

import sys
from pathlib import Path

# Put the repository root first, so that the script imports backend.app from
# its own checkout, under the same module names as the application.
repo_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(repo_root))

from backend.app.data_access.database import (  # noqa: E402
    DATABASE_URL,
    Base,
    engine,
    loggable_url,
)
from backend.app.logger import CustomLogger  # noqa: E402

logger = CustomLogger("DBInit")


def init_database() -> None:
    """Create all database tables using SQLAlchemy ORM."""
    try:
        # Without password and query: INFO lines are printed now (TD-3).
        logger.info("Initializing database at: %s", loggable_url(DATABASE_URL))
        Base.metadata.create_all(bind=engine)
        logger.info("Database schema created successfully")

        # Verify tables exist
        from sqlalchemy import inspect

        inspector = inspect(engine)
        tables = inspector.get_table_names()
        logger.info(f"Created tables: {tables}")

        if "toDo" not in tables:
            raise RuntimeError("Failed to create toDo table")

    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    init_database()
