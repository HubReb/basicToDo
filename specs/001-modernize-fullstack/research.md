# Research: Full-Stack Modernization

**Date**: 2026-04-25
**Feature**: 001-modernize-fullstack

## R1: Async SQLAlchemy with SQLite

**Decision**: Use SQLAlchemy 2.0 async engine with `aiosqlite` driver.

**Rationale**: The current repository layer uses synchronous
`Session` objects inside FastAPI's async route handlers. This blocks
the event loop on every database call. SQLAlchemy 2.0 natively
supports `create_async_engine` and `AsyncSession` which integrate
with `asyncio` without requiring `run_in_executor`.

**Alternatives considered**:
- `databases` library: Lighter but loses SQLAlchemy ORM features
  the project already depends on (relationships, mapped classes).
- `run_in_executor` wrapper: Minimal change but adds thread pool
  overhead and doesn't truly leverage async I/O.
- `encode/databases` + raw SQL: Discards the ORM entirely; too
  large a rewrite for the benefit.

**Implementation notes**:
- Replace `create_engine` with `create_async_engine`
- Replace `Session` with `AsyncSession` from
  `sqlalchemy.ext.asyncio`
- Replace `safe_session_scope` with an async context manager
- Connection string changes from `sqlite:///` to
  `sqlite+aiosqlite:///`
- Add `aiosqlite` to dependencies

---

## R2: Eliminating Dual ORM Mapping

**Decision**: Use declarative mapping only (class-based `ToDoORM`).
Remove the imperative `registry.map_imperatively()` call and the
separate `ToDoEntryData` dataclass.

**Rationale**: The codebase maintains both a declarative ORM class
(`ToDoORM`) and an imperatively-mapped dataclass
(`ToDoEntryData`). This creates confusion about which to use where
and risks schema drift between the two definitions. The declarative
pattern is the standard approach in SQLAlchemy 2.0.

**Alternatives considered**:
- Keep both but document when to use which: Adds cognitive load
  and doesn't prevent drift.
- Use only imperative mapping: Less conventional, harder for new
  contributors to understand.

**Implementation notes**:
- Remove `ToDoEntryData` dataclass and its registry mapping
- Update repository to work directly with `ToDoORM` instances
- Update service layer to accept/return `ToDoORM` or Pydantic
  schemas (with `from_attributes=True` already configured)
- Update builder to construct `ToDoORM` instances directly

---

## R3: Datetime Default Bug Fix

**Decision**: Change `default=datetime.datetime.now()` to
`server_default=func.now()` in the ORM column definition.

**Rationale**: The current code evaluates `datetime.now()` once at
module import time. Every record created in the same process gets
the same timestamp. Using `func.now()` delegates timestamp
generation to SQLite's `CURRENT_TIMESTAMP`, ensuring correctness.

**Alternatives considered**:
- `default=datetime.datetime.now` (callable without parens):
  Correct for Python-side defaults but doesn't work with async
  bulk inserts or raw SQL.
- `server_default=text("CURRENT_TIMESTAMP")`: Equivalent but
  `func.now()` is more portable across databases.

---

## R4: Frontend Shared Validation Hook

**Decision**: Extract a `useTodoValidation` custom hook that
encapsulates title/description validation logic used by both
`TodoForm` and `TodoEditForm`.

**Rationale**: Both form components duplicate identical validation:
non-empty check, max length (255), character count warning. This
violates DRY and means bugs must be fixed in two places.

**Alternatives considered**:
- Zod schema validation: Adds a dependency for simple string
  checks; YAGNI per constitution Principle VI.
- Utility function (non-hook): Would work but a hook can also
  manage the error state, reducing boilerplate in both consumers.

**Implementation notes**:
- Hook signature: `useTodoValidation()` returns
  `{ validateTitle, validateDescription, error, clearError }`
- Both `TodoForm` and `TodoEditForm` consume this hook
- `MAX_TITLE_LENGTH` constant moves into the hook module

---

## R5: Restore Endpoint and UI Pattern

**Decision**: Add a `PATCH /todo/{id}/restore` endpoint and a
collapsible "Deleted" section in the frontend.

**Rationale**: The backend supports soft delete (`deleted` boolean)
but has no restore endpoint. The frontend needs both the API
endpoint and a UI section to view and restore deleted items.

**Alternatives considered**:
- Reuse `PUT /todo/{id}` with `{ deleted: false }`: Semantically
  overloads the update endpoint. Restore is a distinct action.
- Separate `/trash` page: Adds routing complexity; a collapsible
  section on the main page is simpler and keeps context.
- `GET /todo/deleted` endpoint: Needed to list deleted items.
  Could reuse `/todo?deleted=true` query param instead.

**Implementation notes**:
- Add `PATCH /todo/{id}/restore` to API layer
- Add `GET /todo?include_deleted=true` or `GET /todo/deleted`
  for listing deleted items
- Add `restore_to_do` method to repository (sets `deleted=False`)
- Frontend: collapsible section below active list, fetched via
  separate query key

---

## R6: Pagination Backend Support

**Decision**: Add `total_count` to list response and validate
`limit` (1-100) and `page` (1+) query parameters.

**Rationale**: The frontend needs total count to render pagination
controls. The backend currently accepts any integer for limit/page,
including negative values and extremely large numbers.

**Alternatives considered**:
- Cursor-based pagination: More scalable but overkill for SQLite
  with expected data volumes. Offset pagination is simpler.
- No server-side validation (frontend-only): Violates defense in
  depth; API should protect itself.

**Implementation notes**:
- Add Pydantic `Query` validators: `limit: int = Query(10, ge=1, le=100)`,
  `page: int = Query(1, ge=1)`
- Add `count()` query to repository
- Return `total_count` in `ListToDoResponse`
- Frontend computes `total_pages = ceil(total_count / limit)`

---

## R7: Rate Limiting with SlowAPI

**Decision**: Enable `slowapi` rate limiting on all endpoints
with sensible defaults.

**Rationale**: The `slowapi` dependency is already in
`pyproject.toml` but never wired up. Adding rate limiting is
a matter of configuration, not new dependency.

**Alternatives considered**:
- Remove slowapi and rely on reverse proxy: No reverse proxy
  exists in the development setup.
- Custom middleware: Reinvents what slowapi already provides.

**Implementation notes**:
- Add `Limiter` instance in `api.py`
- Default rate: 60 requests/minute per client IP
- Write endpoints (POST, PUT, DELETE): 30 requests/minute
- Return standard 429 response with Retry-After header

---

## R8: Config Class Refactoring

**Decision**: Simplify `config.py` to use Pydantic `BaseSettings`
for configuration management.

**Rationale**: The current `Config` class has control flow issues:
try/except catches `KeyError` but the except block also accesses
`os.environ`, and `_get_db_path()` is called twice. Pydantic
`BaseSettings` handles env var loading, defaults, and validation
in a declarative way that's harder to get wrong.

**Alternatives considered**:
- Fix the existing class manually: Addresses the immediate bugs
  but doesn't prevent future ones.
- python-dotenv only: Doesn't provide validation or typing.

**Implementation notes**:
- Create `Settings(BaseSettings)` with typed fields
- Use `model_config = SettingsConfigDict(env_file=".env")`
- Fields: `database_url`, `host`, `port`, `cors_origins`
- Replace manual `os.environ` access throughout codebase
