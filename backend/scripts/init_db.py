#!/usr/bin/env python3
"""Initialize database schema for testing/deployment."""
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.data_access.database import Base, engine, DATABASE_URL
from app.logger import CustomLogger

logger = CustomLogger("DBInit")

def init_database() -> None:
    """Create all database tables using SQLAlchemy ORM."""
    try:
        logger.info(f"Initializing database at: {DATABASE_URL}")
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
