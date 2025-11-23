"""FastAPI routes for ToDo operations."""
from uuid import UUID

from fastapi import FastAPI, HTTPException, status

from backend.app.business_logic.exceptions import (
    ToDoAlreadyExistsError,
    ToDoNotFoundError,
    ToDoRepositoryError, ToDoValidationError,
)
from backend.app.factory import create_todo_service
from backend.app.schemas.api_responses.delete_to_do_response import DeleteToDoResponse
from backend.app.schemas.api_responses.get_list_to_do_response import ListToDoResponse
from backend.app.schemas.api_responses.get_to_do_response import GetToDoResponse
from backend.app.schemas.api_responses.to_do_response import ToDoResponse
from backend.app.schemas.data_schemes.create_todo_schema import ToDoCreateScheme
from backend.app.schemas.data_schemes.update_todo_schema import TodoUpdateScheme

app = FastAPI(title="ToDo API")
service = create_todo_service()


@app.post("/todo", response_model=ToDoResponse)
async def create_todo(payload: ToDoCreateScheme) -> ToDoResponse:
    try:
        todo = await service.create_todo(payload)
        return ToDoResponse(success=True, todo_entry=todo)
    except ToDoAlreadyExistsError:
        raise HTTPException(status.HTTP_409_CONFLICT, "ToDo already exists")
    except ToDoValidationError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Bad request")
    except ToDoRepositoryError:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Internal error")


@app.get("/todo/{todo_id}", response_model=GetToDoResponse)
async def get_todo(todo_id: UUID) -> GetToDoResponse:
    try:
        todo = await service.get_todo(todo_id)
        return GetToDoResponse(success=True, todo_entry=todo)
    except ToDoNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "ToDo not found")


@app.put("/todo/{todo_id}", response_model=ToDoResponse)
async def update_todo(todo_id: UUID, payload: TodoUpdateScheme) -> ToDoResponse:
    try:
        todo = await service.update_todo(todo_id, payload)
        return ToDoResponse(success=True, todo_entry=todo)
    except ToDoNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "ToDo not found")
    except ToDoValidationError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Bad request")
    except ToDoRepositoryError:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Internal error")


@app.delete("/todo/{todo_id}", response_model=DeleteToDoResponse)
async def delete_todo(todo_id: UUID) -> DeleteToDoResponse:
    try:
        await service.delete_todo(todo_id)
        return DeleteToDoResponse(success=True, message="Deleted successfully")
    except ToDoNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "ToDo not found")
    except ToDoValidationError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Bad request")
    except ToDoRepositoryError:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Internal error")


@app.get("/todo", response_model=ListToDoResponse)
async def list_todos(limit: int = 10, page: int = 1) -> ListToDoResponse:
    todos = await service.get_all_todos(limit, page)
    return ListToDoResponse(success=True, results=len(todos), todo_entries=todos)