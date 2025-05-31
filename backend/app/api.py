#!/usr/bin/env python3

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = ["http://localhost:5173", "localhost:5173"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["root"])
async def read_root() -> dict:
    return {"message": "Welcome to your todo list."}


todos = [{"id": "1", "item": "Read a book."}, {"id": "2", "item": "Cycle around town."}]


@app.get("/todo", tags=["todos"])
async def get_todos() -> dict:
    return {"data": todos}


@app.post("/todo", tags=["todos"])
async def add_todo(todo: dict) -> dict:
    if todo in todos:
        return {"data": {"Todo already exists."}}
    todos.append(todo)
    return {"data": {"Todo added."}}


@app.put("/todo/{id}", tags=["todos"])
async def update_todo(id: int, body: dict) -> dict:
    for todo in todos:
        if not int(todo["id"]) == id:
            continue
        todo["item"] = body["item"]
        return {"data": f"Todo with id {id} has been updated."}
    return {"data": f"Todo with id {id} not found."}


@app.delete("/todo/{id}", tags=["todos"])
async def delete_todos(id: int) -> dict:
    for todo in todos:
        if int(todo["id"]) == id:
            todos.remove(todo)
            return {"data": f"Todo with id {id} has been removed."}
    return {"data": f"Todo with id {id} not found."}
