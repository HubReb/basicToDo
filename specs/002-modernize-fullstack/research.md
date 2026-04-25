# Research: Modernize Full-Stack ToDo Application

**Branch**: `002-modernize-fullstack` | **Date**: 2026-04-25
**Source**: Direct codebase inspection of `/home/rebekka/projects/basicToDo`

---

## R1 — Async SQLAlchemy Pattern

**Decision**: Use `create_async_engine` + `async_sessionmaker` + `AsyncSession` from
`sqlalchemy.ext.asyncio`. DB URL prefix changes from `sqlite:///` to `sqlite+aiosqlite:///`.
All repository methods become `async def` and use `await session.execute(select(...))`.

**Rationale**: Principle I requires non-blocking I/O. SQLAlchemy 2.0 ships native async
support; no third-party wrapper needed. `aiosqlite` is the only driver required for SQLite.

**Alternatives considered**:
- `databases` library — adds a dependency layer over SQLAlchemy; rejected for unnecessary
  complexity given SQLAlchemy 2.0's native async.
- `encode/orm` — abandoned project; rejected.
- Thread-pool executor to run sync DB calls — technically unblocks the event loop but still
  blocks threads and violates the spirit of Principle I.

---

## R2 — Configuration Management

**Decision**: Replace `Config` class with `pydantic-settings` `BaseSettings`. Fields:
`database_url` (default `sqlite+aiosqlite:///backend/todo.db`), `host`, `port`, `reload`,
`cors_origins`. Settings auto-read from environment variables and optional `.env` file.

**Rationale**: The existing `Config.__init__` contains a self-reference bug
(`self._get_db_path()` called before `self.config_file` is set) and fails without a JSON
file. Pydantic BaseSettings provides type-safe env-var reading with zero boilerplate.

**Alternatives considered**:
- `python-dotenv` + `os.environ` — works but requires manual type coercion and has no
  validation; rejected.
- Keep JSON config + fix bug — still couples the app to a file that must exist; rejected.

---

## R3 — Single ORM Model

**Decision**: Delete `ToDoEntryData` dataclass and `mapper_registry.map_imperatively()`
call from `database.py`. Retain `ToDoORM` as the sole mapped class. Update all repository
method signatures from `ToDoEntryData` to `ToDoORM`.

**Rationale**: Principle III violation. Two definitions for one table. The declarative
`ToDoORM` is strictly superior: it participates in SQLAlchemy's identity map, relationship
loading, and async session tracking. The dataclass + imperative mapper adds no value.

**Alternatives considered**:
- Keep both and add a converter function — still two representations; doubles the change
  surface; rejected.
- Keep only `ToDoEntryData` (dataclass) — loses SQLAlchemy ORM features; rejected.

---

## R4 — Rate Limiting

**Decision**: Use `slowapi` (already in `pyproject.toml`). Create a `Limiter` with
`key_func=get_remote_address`. Apply `@limiter.limit("60/minute")` to GET endpoints and
`@limiter.limit("30/minute")` to POST/PUT/DELETE/PATCH endpoints. Mount
`SlowAPIMiddleware` on the FastAPI app. All rate-limited routes must accept `request:
Request` as a parameter.

**Rationale**: `slowapi` is already a declared dependency — wiring it up is the minimal
change. The 60/30 split mirrors spec requirements (FR-005) and constitution Principle V.

**Alternatives considered**:
- `fastapi-limiter` (Redis-backed) — requires Redis; overkill for single-user local app;
  rejected.
- Manual in-memory counter — no persistence across restarts, no standard headers; rejected.

---

## R5 — Pagination Validation and Total Count

**Decision**: Replace bare `int` parameters on `list_todos` with
`limit: int = Query(10, ge=1, le=100)` and `page: int = Query(1, ge=1)`. Add a
`get_count()` async repository method (`select(func.count(ToDoORM.id)).where(deleted=False)`)
and return `total_count` in `ListToDoResponse`.

**Rationale**: FastAPI's `Query` descriptor provides automatic HTTP 422 on out-of-range
values with no extra code. `total_count` is required for client-side pagination (FR-004).

**Alternatives considered**:
- Manual validation in route body — duplicates FastAPI's built-in capability; rejected.
- Return cursor-based pagination — more complex; unnecessary for this scale; rejected.

---

## R6 — Route Ordering Fix

**Decision**: In `api.py`, define `/todo` (list) and `/todo/deleted` before `/todo/{todo_id}`
(parameterised). FastAPI matches routes in definition order; `"deleted"` would otherwise be
interpreted as a UUID string, causing 422 errors.

**Rationale**: Standard FastAPI practice for literal vs. parameterised path segments.

---

## R7 — Frontend Shared Validation Hook

**Decision**: Create `frontend/src/hooks/useTodoValidation.ts` exporting `validateTitle`
and `validateDescription`. Both `TodoForm` and `TodoEditForm` import from this hook.
Remove the copy-pasted `validateTitle` blocks from each component.

**Rationale**: Principle III — `validateTitle` is currently defined twice with identical
logic. One change point is always better than two.

**Alternatives considered**:
- Plain utility function (not a hook) — valid but less consistent with the existing hook
  pattern in the codebase; a hook allows local `useState` for error state if needed.

---

## R8 — Optimistic Updates for Restore

**Decision**: `useRestoreTodo` mutation uses `onMutate` to immediately remove the item from
the `['todos', 'deleted']` query cache and add it to `['todos', active]`. On error, both
caches are rolled back via `context`. On settled, both queries are invalidated.

**Rationale**: Principle IV — users must see the result before the server responds. Restore
is a write operation with predictable outcome (deleted→active), making optimistic update
safe.

**Alternatives considered**:
- Invalidate-only (no optimistic) — user sees a loading state; violates Principle IV; rejected.
