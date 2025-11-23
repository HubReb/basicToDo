"""
Backend for the ToDo app.
"""

import uvicorn

from backend.app.data_access.database import Base, engine

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)  # type: ignore[attr-defined]
    uvicorn.run("backend.app.api.api:app", host="0.0.0.0", port=8000, reload=True)