"""
The API call definitions.
"""

import uuid
from http import HTTPStatus
from logging import INFO
from typing import List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import HTTPException

from backend.app.logger import CustomLogger
from backend.app.schemas.todo import (
    GetToDoResponse, ToDoResponse,
    DeleteToDoResponse,
    ToDoCreateEntry,
    ToDoSchema, TodoUpdateEntry

)
from backend.app.business_logic.webservice import Webservice


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
        )
        self.webservice = Webservice()

    def get_to_dos(self) -> List[ToDoSchema]:
        """Get all todos."""
        return self.webservice.get_all_to_do_entries()


    def add_to_dos(self, new_todo: ToDoCreateEntry) -> ToDoResponse | HTTPException:
        """Add a toDo."""
        response = self.webservice.add_entry(new_todo)
        return response

    def update_todo(
            self, item_id: uuid.UUID, todo_update: TodoUpdateEntry
    ) -> HTTPException | ToDoResponse:
        """Update a ToDo."""
        try:
            entry_data = self.webservice.get_entry(item_id)
            entry_data.description = todo_update.item
            return self.webservice.update_entry(
                item_id, ToDoSchema.model_validate(entry_data)
            )
        except HTTPException as e:
            raise HTTPException(HTTPStatus.NOT_FOUND,  f"Todo with id {item_id} not found.") from e

    def delete_todo(
            self, item_id: uuid.UUID
    ) -> DeleteToDoResponse | HTTPException:
        """Delete a todo item."""
        try:
            return self.webservice.delete_entry(item_id)
        except HTTPException as e:
            raise HTTPException(HTTPStatus.NOT_FOUND) from e


appLogger = CustomLogger("ApiCallHandler", INFO)
app = App(["http://localhost:5173", "localhost:5173"], appLogger)


@app.get("/", tags=["root"])
async def read_root() -> dict:
    """Return a dummy message if the root is read."""
    return {"message": "Welcome to your todo list."}


@app.get("/todo", tags=["todos"], response_model=List[ToDoSchema])
async def get_todos() -> List[ToDoSchema]:
    """Return the todos."""
    return app.get_to_dos()


# Get a specific todo
@app.get("/todo/{todo_id}", tags=["todos"], response_model=GetToDoResponse)
def get_todo(todo_id: str):
    for todo in app.webservice.get_entry(uuid.UUID(todo_id)):
        if todo.id == todo_id:
            return todo
    raise HTTPException(status_code=404, detail="Todo not found")


@app.post("/todo", tags=["todos"])
async def create_todo(todo_entry: ToDoCreateEntry, response_model=ToDoResponse):
    """Add a todo item to the list."""
    return app.add_to_dos(todo_entry)


@app.put("/todo/{id}", tags=["todos"], response_model=ToDoResponse)
async def update_todo(item: uuid.UUID, todo_update: TodoUpdateEntry):
    """Update a todo item description."""
    return app.update_todo(item_id=item, todo_update=todo_update)


@app.delete("/todo/{id}", tags=["todos"])
async def delete_todos(item: uuid.UUID):
    """Delete a todo."""
    return app.delete_todo(item)