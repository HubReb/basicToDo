"""
The API call definitions.
"""

import time
import uuid
from http import HTTPStatus
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

from backend.app.business_logic.todo_service import ToDoService
from backend.app.factory import create_todo_service
from backend.app.logger import CustomLogger
from backend.app.schemas.todo import (DeleteToDoResponse, GetToDoResponse, ToDoCreateEntry, ToDoResponse, ToDoSchema,
                                      TodoUpdateEntry)

request_counter: int = 0
last_request_time: float = time.time()
rate_limit_window: int = 60
max_requests_per_window: int = 100


class RateLimiterMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        global last_request_time, request_counter

        current_time = time.time()
        if current_time - last_request_time > rate_limit_window:
            request_counter = 0
            last_request_time = current_time

        request_counter += 1

        if request_counter > max_requests_per_window:
            return Response("Rate limit exceeded", status_code=429)

        response = await call_next(request)
        return response

class App(FastAPI):
    """FastAPI app"""

    def __init__(
            self,
            origins: list[str],
            logger: CustomLogger,
            service: ToDoService = Depends(create_todo_service),
    ) -> None:
        """Initialize the handler."""
        super().__init__()
        if not origins:
            raise ValueError(f"origins is {origins}.")
        if not logger:
            raise ValueError("Parameter logger is None.")

        self.origins = origins
        self.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=[
                "Content-Security-Policy",
                "X-Content-Type-Options",
                "X-Frame-Options"
            ],
            allow_origin_regex=".*",
        )
        self.webservice = service

    async def get_to_dos(self, limit: int = 10, page: int = 1) -> List[ToDoSchema]:
        """Get all todos."""
        return await self.webservice.get_all_todos(limit, page)


    async def add_to_dos(self, new_todo: ToDoCreateEntry) -> ToDoResponse:
        """Add a toDo."""
        response = await self.webservice.create_todo(new_todo)
        return response

    async def update_todo(
            self, item_id: uuid.UUID, todo_update: TodoUpdateEntry
    ) -> ToDoResponse:
        """Update a ToDo."""
        try:
            entry_data = await self.webservice.get_todo(item_id)
            entry_data.todo_entry.description = todo_update.description
            entry_data.todo_entry.title = todo_update.title
            updated_entry_data = TodoUpdateEntry(**entry_data.todo_entry.model_dump())
            return await self.webservice.update_todo(
                item_id, TodoUpdateEntry.model_validate(updated_entry_data)
            )
        except HTTPException as e:
            raise HTTPException(HTTPStatus.NOT_FOUND, f"Todo not found.") from e

    async def delete_todo(
            self, item_id: uuid.UUID
    ) -> DeleteToDoResponse:
        """Delete a todo item."""
        try:
            return await self.webservice.delete_todo(item_id)
        except HTTPException as e:
            raise HTTPException(HTTPStatus.NOT_FOUND) from e


appLogger = CustomLogger("ApiCallHandler")
# TODO: Get this from config
todo_service = create_todo_service()
app = App(["http://localhost:5173", "localhost:5173"], appLogger, todo_service)
app.add_middleware(RateLimiterMiddleware)

@app.get("/", tags=["root"])
async def read_root() -> JSONResponse:
    """Return a dummy message if the root is read."""
    return JSONResponse(status_code=HTTPStatus.OK, content={"message": "Welcome to your todo list."})


@app.get("/todo", tags=["todos"], response_model=List[ToDoSchema])
async def get_todos(limit: int = 10, page: int = 1) -> List[ToDoSchema]:
    """Return the todos."""
    return await app.get_to_dos(limit, page)


# Get a specific todo
@app.get("/todo/entry", tags=["todos"], response_model=GetToDoResponse)
async def get_todo(todo_id: uuid.UUID) -> Optional[GetToDoResponse]:
    """Get a specific todo entry."""
    try:
        todo = await app.webservice.get_todo(todo_id)
        return todo
    except HTTPException as e:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Todo not found") from e


@app.post("/todo", tags=["todos"])
async def create_todo(todo_entry: ToDoCreateEntry, response_model=ToDoResponse):
    """Add a todo item to the list."""
    todo_entry = await app.add_to_dos(todo_entry)
    return todo_entry


@app.put("/todo/entry", tags=["todos"], response_model=ToDoResponse)
async def update_todo(item: uuid.UUID, todo_update: TodoUpdateEntry):
    """Update a todo item description."""
    todo = await app.update_todo(item_id=item, todo_update=todo_update)
    return todo


@app.delete("/todo/entry", tags=["todos"])
async def delete_todo(item: uuid.UUID):
    """Delete a todo."""
    todo = await app.delete_todo(item_id=item)
    return todo