"""
Backend for the ToDo app.
"""

import uvicorn

if __name__ == "__main__":
    uvicorn.run("backend.app.api.api:app", host="0.0.0.0", port=8000, reload=True)