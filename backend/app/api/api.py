"""FastAPI routes for ToDo operations."""

from uuid import UUID

from fastapi import FastAPI, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter  # type: ignore[import-untyped]
from slowapi.errors import RateLimitExceeded  # type: ignore[import-untyped]
from slowapi.util import get_remote_address  # type: ignore[import-untyped]

from backend.app.business_logic.exceptions import (
    ToDoAlreadyExistsError,
    ToDoNotFoundError,
    ToDoRepositoryError,
    ToDoValidationError,
)
from backend.app.config import settings
from backend.app.factory import create_todo_service
from backend.app.schemas.api_responses.delete_to_do_response import DeleteToDoResponse
from backend.app.schemas.api_responses.get_list_to_do_response import ListToDoResponse
from backend.app.schemas.api_responses.get_to_do_response import GetToDoResponse
from backend.app.schemas.api_responses.to_do_response import ToDoResponse
from backend.app.schemas.data_schemes.create_todo_schema import ToDoCreateScheme
from backend.app.schemas.data_schemes.update_todo_schema import TodoUpdateScheme

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="ToDo API")
app.state.limiter = limiter


def rate_limit_exceeded_handler(
    request: Request, exc: RateLimitExceeded
) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={"error": "Rate limit exceeded", "retry_after": 30},
        headers={"Retry-After": "30"},
    )


app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)  # type: ignore[arg-type]

# Configure CORS from settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

service = create_todo_service()


@app.get("/")
@limiter.limit("60/minute")
async def health_check(request: Request) -> dict[str, str]:
    """Health check endpoint for testing."""
    return {"status": "ok"}


@app.post("/todo", response_model=ToDoResponse)
@limiter.limit("30/minute")
async def create_todo(request: Request, payload: ToDoCreateScheme) -> ToDoResponse:
    try:
        todo = await service.create_todo(payload)
        return ToDoResponse(success=True, todo_entry=todo)
    except ToDoAlreadyExistsError:
        raise HTTPException(status.HTTP_409_CONFLICT, "ToDo already exists")
    except ToDoValidationError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Bad request")
    except ToDoRepositoryError:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Internal error")


@app.get("/todo", response_model=ListToDoResponse)
@limiter.limit("60/minute")
async def list_todos(
    request: Request,
    limit: int = Query(10, ge=1, le=100),
    page: int = Query(1, ge=1),
) -> ListToDoResponse:
    todos = await service.get_all_todos(limit, page)
    total_count = await service.count_active()
    return ListToDoResponse(
        success=True,
        results=len(todos),
        total_count=total_count,
        todo_entries=todos,
    )


@app.get("/todo/deleted", response_model=ListToDoResponse)
@limiter.limit("60/minute")
async def list_deleted_todos(
    request: Request,
    limit: int = Query(10, ge=1, le=100),
    page: int = Query(1, ge=1),
) -> ListToDoResponse:
    todos = await service.get_deleted_todos(limit, page)
    total_count = await service.count_deleted()
    return ListToDoResponse(
        success=True,
        results=len(todos),
        total_count=total_count,
        todo_entries=todos,
    )


@app.get("/todo/{todo_id}", response_model=GetToDoResponse)
@limiter.limit("60/minute")
async def get_todo(request: Request, todo_id: UUID) -> GetToDoResponse:
    try:
        todo = await service.get_todo(todo_id)
        return GetToDoResponse(success=True, todo_entry=todo)
    except ToDoNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "ToDo not found")


@app.put("/todo/{todo_id}", response_model=ToDoResponse)
@limiter.limit("30/minute")
async def update_todo(
    request: Request, todo_id: UUID, payload: TodoUpdateScheme
) -> ToDoResponse:
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
@limiter.limit("30/minute")
async def delete_todo(request: Request, todo_id: UUID) -> DeleteToDoResponse:
    try:
        await service.delete_todo(todo_id)
        return DeleteToDoResponse(success=True, message="Deleted successfully")
    except ToDoNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "ToDo not found")
    except ToDoValidationError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Bad request")
    except ToDoRepositoryError:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Internal error")


@app.patch("/todo/{todo_id}/restore", response_model=ToDoResponse)
@limiter.limit("30/minute")
async def restore_todo(request: Request, todo_id: UUID) -> ToDoResponse:
    try:
        todo = await service.restore_todo(todo_id)
        return ToDoResponse(success=True, todo_entry=todo)
    except ToDoNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "ToDo not found or not deleted")
    except ToDoValidationError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Bad request")
    except ToDoRepositoryError:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Internal error")
