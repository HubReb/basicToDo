"""
Backend for the ToDo app.
"""
import asyncio

import uvicorn

from backend.app.config import settings
from backend.app.data_access.database import Base, engine


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


if __name__ == "__main__":
    asyncio.run(init_db())
    uvicorn.run(
        "backend.app.api.api:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
    )
