"""
Backend for the ToDo app.
"""

import uvicorn

from backend.scripts.init_db import init_database

if __name__ == "__main__":
    # Q6.6: the database is brought to the latest revision before serving.
    init_database()
    uvicorn.run("backend.app.api.api:app", host="0.0.0.0", port=8000, reload=True)
