"""
Backend for the ToDo app.
"""

import uvicorn

from backend.app.settings import load_settings
from backend.scripts.init_db import init_database

if __name__ == "__main__":
    # SEC-002: 127.0.0.1 and no auto-reload unless BASICTODO_* says otherwise.
    settings = load_settings()
    # Q6.6: the database is brought to the latest revision before serving.
    init_database()
    uvicorn.run(
        "backend.app.api.api:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
    )
