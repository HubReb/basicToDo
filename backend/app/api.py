"""
The API call definitions.
"""

from logging import INFO
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.logger import CustomLogger
from app.todo import ToDo


class APICallHandler(FastAPI):
    """Handler of the calls to the WebAPT"""

    def __init__(self, origins: list[str], logger: CustomLogger) -> None:
        """Initialize the handler."""
        super().__init__()
        if origins == []:
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
        # this will be replaced by loaded data
        self.todos: list[ToDo] = []

    def get_to_dos(self) -> dict:
        """Get all todos."""
        data = []
        for to_do in self.todos:
            data.append({"id": to_do.id, "item": to_do.description})
        return {"data": data}

    def add_to_dos(self, new_todo: ToDo) -> dict:
        """Add a toDo."""
        if new_todo in self.todos:
            return {"data": "{ToDo already exists.}"}
        self.todos.append(new_todo)
        return {"data": {f"ToDo {new_todo.id} added."}}

    def update_todo(self, item_id: str, body: dict) -> dict:
        """Update a ToDo."""
        for to_do_object in self.todos:
            if not to_do_object.id == item_id:
                continue
            to_do_object.description = body["item"]
            return {"data": f"Todo with id {item_id} has been updated."}
        return {"data": f"Todo with id {item_id} not found."}

    def delete_todos(self, item_id: str) -> dict:
        """Delete a todo item."""
        todo_copy = self.todos[:]
        for to_do_object in todo_copy:
            if to_do_object.id != item_id:
                continue
            self.todos.remove(to_do_object)
            return {"data": f"Todo with id {id} has been removed."}

        return {"data": f"Todo with id {id} not found."}


appLogger = CustomLogger("ApiCallHandler", INFO)
toDoLogger = CustomLogger("DataLogger", INFO)
app = APICallHandler(["http://localhost:5173", "localhost:5173"], appLogger)


@app.get("/", tags=["root"])
async def read_root() -> dict:
    """Return a dummy message if the root is read."""
    return {"message": "Welcome to your todo list."}


todos = [{"id": "1", "item": "Read a book."}, {"id": "2", "item": "Cycle around town."}]
for todo in todos:
    todo_item = ToDo(id=todo["id"], description=todo["item"])
    app.add_to_dos(todo_item)


@app.get("/todo", tags=["todos"])
async def get_todos() -> dict:
    """Return the todos."""
    return app.get_to_dos()


@app.post("/todo", tags=["todos"])
async def add_todo(todo_entry: dict[str, str]) -> dict:
    """Add a todo item to the list."""
    new_todo = ToDo(id=todo_entry["id"], description=todo_entry["item"])
    return app.add_to_dos(new_todo)


@app.put("/todo/{id}", tags=["todos"])
async def update_todo(item: int, body: dict) -> dict:
    """Update a todo item description."""
    return app.update_todo(item_id=str(item), body=body)


@app.delete("/todo/{id}", tags=["todos"])
async def delete_todos(item: int) -> dict:
    """Delete a todo."""
    return app.delete_todos(str(item))
