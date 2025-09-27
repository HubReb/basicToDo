"""
The API call definitions.
"""

import uuid
from datetime import datetime
from logging import INFO
from typing import List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import HTTPException

from backend.app.logger import CustomLogger
from backend.app.models import ToDoEntryData
from backend.app.schemas import (
    ToDoResponse,
    DeleteToDoResponse,
    TodoUpdateEntry,
    ToDoCreateEntry,
    ToDoSchema

)
from backend.app.webservice import Webservice


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

    def get_to_dos(self) -> dict:
        """Get all todos."""
        data = []
        stored_todos = self.webservice.get_all_to_do_entries()
        for to_do in stored_todos:
            data.append({"id": to_do.id, "item": to_do.description})
        return {"data": data}

    def add_to_dos(self, new_todo: ToDoCreateEntry) -> ToDoResponse | HTTPException:
        """Add a toDo."""
        response = self.webservice.add_entry(new_todo)
        return response

    def update_todo(
            self, item_id: uuid.UUID, todo_update: ToDoSchema
    ) -> dict | HTTPException | ToDoResponse:
        """Update a ToDo."""
        for to_do_object in self.webservice.get_all_to_do_entries():
            if not to_do_object.id == item_id:
                continue
            to_do_object.description = todo_update.description
            return self.webservice.update_entry(
                item_id, ToDoSchema.model_validate(to_do_object)
            )
        return {"data": f"Todo with id {item_id} not found."}

    def delete_todos(
            self, item_id: uuid.UUID
    ) -> DeleteToDoResponse | dict | HTTPException:
        """Delete a todo item."""
        todo_copy = self.webservice.get_all_to_do_entries()
        for to_do_object in todo_copy:
            if to_do_object.id != item_id:
                continue
            return self.webservice.delete_entry(item_id)

        return {"data": f"Todo with id {id} not found."}


appLogger = CustomLogger("ApiCallHandler", INFO)
toDoLogger = CustomLogger("DataLogger", INFO)
app = App(["http://localhost:5173", "localhost:5173"], appLogger)


@app.get("/", tags=["root"])
async def read_root() -> dict:
    """Return a dummy message if the root is read."""
    return {"message": "Welcome to your todo list."}


@app.get("/todo", tags=["todos"], response_model=List[ToDoSchema])
async def get_todos() -> dict:
    """Return the todos."""
    return app.get_to_dos()


# Get a specific todo
@app.get("/todo/{todo_id}", response_model=ToDoSchema)
def get_todo(todo_id: str):
    for todo in app.webservice.get_entry(uuid.UUID(todo_id)):
        if todo.id == todo_id:
            return todo
    raise HTTPException(status_code=404, detail="Todo not found")


@app.post("/todo", tags=["todos"])
async def create_todo(todo_entry: ToDoCreateEntry):
    """Add a todo item to the list."""

    return app.add_to_dos(todo_entry)


@app.put("/todo/{id}", tags=["todos"])
async def update_todo(item: uuid.UUID, todo_update: ToDoSchema):
    """Update a todo item description."""
    return app.update_todo(item_id=item, todo_update=todo_update)


@app.delete("/todo/{id}", tags=["todos"])
async def delete_todos(item: uuid.UUID):
    """Delete a todo."""
    return app.delete_todos(item)