"""FastAPI routes for ToDo operations."""

from contextlib import asynccontextmanager
from typing import Annotated, Any, AsyncIterator
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, Query, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from backend.app.api.body_limit import MAX_BODY_BYTES, BodyLimitMiddleware
from backend.app.business_logic.exceptions import (
    ToDoAlreadyExistsError,
    ToDoNotFoundError,
    ToDoRepositoryError,
    ToDoValidationError,
)
from backend.app.data_access.database import DATABASE_URL
from backend.app.data_access.schema import assert_at_head
from backend.app.factory import create_todo_service
from backend.app.schemas.api_responses.delete_to_do_response import DeleteToDoResponse
from backend.app.schemas.api_responses.get_list_to_do_response import ListToDoResponse
from backend.app.schemas.api_responses.get_to_do_response import GetToDoResponse
from backend.app.schemas.api_responses.to_do_response import ToDoResponse
from backend.app.schemas.data_schemes.create_todo_schema import ToDoCreateScheme
from backend.app.schemas.data_schemes.update_todo_schema import TodoUpdateScheme
from backend.app.settings import load_settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Serve only a database at the latest revision (Q6.6).

    A database made before the UTC migration would otherwise be served with
    local times labelled as UTC. backend/scripts/init_db.py and
    backend/app/main.py prepare it.
    """
    assert_at_head(DATABASE_URL)
    yield


# FastAPI >= 0.142 would start exporting OpenTelemetry data as soon as an
# OTEL_EXPORTER_OTLP_* variable is set; keep the legacy behaviour (no export).
app = FastAPI(title="ToDo API", telemetry={"auto_configure": False}, lifespan=lifespan)
settings = load_settings()

# add_middleware puts each new middleware outside the previous ones. So the
# Host check (SEC-003) runs first and answers a foreign Host before any body
# is read, and CORS wraps the body limit (Q8b), so a 413 carries CORS headers.
app.add_middleware(BodyLimitMiddleware, max_bytes=MAX_BODY_BYTES)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Accept"],
)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=list(settings.trusted_hosts))

service = create_todo_service()


def require_json(request: Request) -> None:
    """SEC-003: requests with a body must declare it as application/json."""
    media_type = (
        request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    )
    if media_type != "application/json":
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            "Content-Type must be application/json",
        )


def _sendable(value: Any) -> Any:
    """The value with unpaired surrogates replaced by U+FFFD, so it encodes as UTF-8."""
    if isinstance(value, str):
        return value.encode("utf-16", "surrogatepass").decode("utf-16", "replace")
    if isinstance(value, dict):
        return {key: _sendable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_sendable(item) for item in value]
    return value


@app.exception_handler(RequestValidationError)
async def request_validation_error(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """FastAPI's 422, except that echoed input is made sendable (Q6.2).

    The default handler echoes the rejected input; an unpaired surrogate in
    it made the 422 response itself fail with a 500.
    """
    return JSONResponse(
        status_code=422, content={"detail": _sendable(jsonable_encoder(exc.errors()))}
    )


@app.get("/")
async def health_check() -> dict[str, str]:
    """Health check endpoint for testing."""
    return {"status": "ok"}


@app.post("/todo", response_model=ToDoResponse, dependencies=[Depends(require_json)])
async def create_todo(payload: ToDoCreateScheme) -> ToDoResponse:
    try:
        todo = await service.create_todo(payload)
        return ToDoResponse(success=True, todo_entry=todo)
    except ToDoAlreadyExistsError:
        raise HTTPException(status.HTTP_409_CONFLICT, "ToDo already exists")
    except ToDoValidationError:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Invalid input")
    except ToDoRepositoryError:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Internal error")


@app.get("/todo/{todo_id}", response_model=GetToDoResponse)
async def get_todo(todo_id: UUID) -> GetToDoResponse:
    try:
        todo = await service.get_todo(todo_id)
        return GetToDoResponse(success=True, todo_entry=todo)
    except ToDoNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "ToDo not found")


@app.put(
    "/todo/{todo_id}", response_model=ToDoResponse, dependencies=[Depends(require_json)]
)
async def update_todo(todo_id: UUID, payload: TodoUpdateScheme) -> ToDoResponse:
    try:
        todo = await service.update_todo(todo_id, payload)
        return ToDoResponse(success=True, todo_entry=todo)
    except ToDoNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "ToDo not found")
    except ToDoValidationError:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Invalid input")
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
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Invalid input")
    except ToDoRepositoryError:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Internal error")


@app.get("/todo", response_model=ListToDoResponse)
async def list_todos(
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
    page: Annotated[int, Query(ge=1, le=1_000_000)] = 1,
) -> ListToDoResponse:
    """The active todos, newest first: `limit` per page (1 to 100), `total` over all pages."""
    todos = await service.get_all_todos(limit, page)
    total = await service.count_todos()
    return ListToDoResponse(
        success=True, results=len(todos), total=total, todo_entries=todos
    )
