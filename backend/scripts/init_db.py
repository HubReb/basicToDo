#!/usr/bin/env python3
"""Initialize database schema for testing/deployment."""

import asyncio
import sys

from backend.app.config import settings
from backend.app.data_access.database import Base, engine
from backend.app.logger import CustomLogger

logger = CustomLogger("DBInit")


async def init_database() -> None:
    """Create all database tables using SQLAlchemy async ORM."""
    try:
        logger.info(f"Initializing database at: {settings.database_url}")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            tables = await conn.run_sync(
                lambda sync_conn: list(Base.metadata.tables.keys())
            )
        logger.info(f"Created tables: {tables}")
        if "toDo" not in tables:
            raise RuntimeError("Failed to create toDo table")
        logger.info("Database schema created successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        sys.exit(1)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(init_database())
