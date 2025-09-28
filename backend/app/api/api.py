"""
The API call definitions.
"""

import uuid
from http import HTTPStatus
from typing import List, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import HTTPException
from starlette.responses import JSONResponse

from backend.app.logger import CustomLogger
from backend.app.schemas.todo import (
    GetToDoResponse, ToDoResponse,
    DeleteToDoResponse,
    ToDoCreateEntry,
    ToDoSchema, TodoUpdateEntry

)
from backend.app.business_logic.todo_service import ToDoService


class App(FastAPI):
    """FastAPI app"""

    def __init__(
            self,
            origins: list[str],
            logger: CustomLogger,
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
            allow_headers=["*"],
            allow_origin_regex=".*",
        )
        self.webservice = ToDoService()

    async def get_to_dos(self) -> List[ToDoSchema]:
        """Get all todos."""
        return await self.webservice.get_all_todos()


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
            entry_data.todo_entry.description = todo_update.item
            return await self.webservice.update_todo(
                item_id, ToDoSchema.model_validate(entry_data.todo_entry)
            )
        except HTTPException as e:
            raise HTTPException(HTTPStatus.NOT_FOUND,  f"Todo with id {item_id} not found.") from e

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
app = App(["http://localhost:5173", "localhost:5173"], appLogger)


@app.get("/", tags=["root"])
async def read_root() -> JSONResponse:
    """Return a dummy message if the root is read."""
    return JSONResponse(status_code=HTTPStatus.OK, content={"message": "Welcome to your todo list."})


@app.get("/todo", tags=["todos"], response_model=List[ToDoSchema])
async def get_todos() -> List[ToDoSchema]:
    """Return the todos."""
    return await app.get_to_dos()


# Get a specific todo
@app.get("/todo/{todo_id}", tags=["todos"], response_model=GetToDoResponse)
async def get_todo(todo_id: uuid.UUID) -> Optional[ToDoSchema]:
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


@app.put("/todo/{id}", tags=["todos"], response_model=ToDoResponse)
async def update_todo(item: uuid.UUID, todo_update: TodoUpdateEntry):
    """Update a todo item description."""
    todo = await app.update_todo(item_id=item, todo_update=todo_update)
    return todo


@app.delete("/todo/{id}", tags=["todos"])
async def delete_todos(item: uuid.UUID):
    """Delete a todo."""
    todo = await app.delete_todo(item_id=item)
    return todo