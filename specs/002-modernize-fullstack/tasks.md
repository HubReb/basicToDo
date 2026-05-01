---
description: "Task list for Modernize Full-Stack ToDo Application"
---

# Tasks: Modernize Full-Stack ToDo Application

**Input**: Design documents from `specs/002-modernize-fullstack/`
**Prerequisites**: plan.md ✅ spec.md ✅ research.md ✅ data-model.md ✅ contracts/ ✅ quickstart.md ✅

**Tests**: Not explicitly requested in spec — no test tasks generated.
**Organization**: Tasks grouped by user story (US1–US7) for independent implementation.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add new dependencies and prepare pyproject.toml / package configs.

- [X] T001 Add `aiosqlite>=0.20.0` and `pydantic-settings>=2.7.0` to dependencies in `pyproject.toml`
- [X] T002 Add `asyncio_mode = "auto"` to `[tool.pytest.ini_options]` in `pyproject.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core backend infrastructure that ALL user stories depend on. MUST be complete
before any user story implementation begins.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T003 Replace `backend/app/config.py` with Pydantic BaseSettings: class `Settings(BaseSettings)` with fields `database_url` (default `sqlite+aiosqlite:///backend/todo.db`), `host` (default `"0.0.0.0"`), `port` (default `8000`), `reload` (default `True`), `cors_origins` (default `["http://localhost:5173"]`); export singleton `settings = Settings()`
- [X] T004 Rewrite `backend/app/data_access/database.py`: replace `create_engine`/`SessionLocal`/`safe_session_scope` with `create_async_engine(settings.database_url)`/`async_sessionmaker(..., class_=AsyncSession)`/`async def safe_session_scope() -> AsyncGenerator[AsyncSession, None]` using `@asynccontextmanager`; remove `mapper_registry`, `to_do_table`, and the `mapper_registry.map_imperatively(ToDoEntryData, to_do_table)` call; keep `ToDoORM` declarative class unchanged
- [X] T005 Empty `backend/app/models/todo.py`: remove the `ToDoEntryData` dataclass entirely (file may be left with only a module docstring)
- [X] T006 Rewrite `backend/app/data_access/repository.py`: change all method signatures from `ToDoEntryData` to `ToDoORM`; make all methods `async def`; replace `session.query(...)` with `await session.execute(select(ToDoORM).where(...))` + `.scalars().first()`; replace `session.query(...).filter(...).all()` with `await session.execute(select(ToDoORM).where(...).offset().limit())` + `.scalars().all()`; add `async def get_count(self) -> int` using `select(func.count(ToDoORM.id)).where(ToDoORM.deleted.is_(False))`; add `async def get_deleted_todos(self, limit, page) -> List[ToDoORM]`; add `async def restore_to_do(self, to_do_id: uuid.UUID) -> Optional[ToDoORM]` that queries `deleted.is_(True)`, sets `deleted=False`, merges
- [X] T007 Update `ToDoRepositoryInterface` in `backend/app/data_access/repository.py` to declare all abstract methods as `async def` and add `get_count`, `get_deleted_todos`, `restore_to_do` to the interface
- [X] T008 Update `backend/app/business_logic/builders/todo_entry_builder.py`: change return type from `ToDoEntryData` to `ToDoORM`; import `ToDoORM` from `backend.app.data_access.database`; set `created_at=datetime.datetime.now(datetime.timezone.utc)` explicitly in the returned `ToDoORM(...)` constructor
- [X] T009 Update `backend/app/factory.py`: import `safe_session_scope` from the async database module; ensure `create_todo_service()` passes the async `safe_session_scope` as the session manager to `ToDoRepository`
- [X] T010 Update `backend/app/business_logic/todo_service.py`: add `await` before every `self.repository.*` call; update type annotations from `ToDoEntryData` to `ToDoORM` where used
- [X] T011 Add `total_count: int = 0` field to `backend/app/schemas/api_responses/get_list_to_do_response.py` in the `ListToDoResponse` Pydantic model
- [X] T012 Update `backend/tests/conftest.py`: replace `MagicMock` repository with `AsyncMock`; replace sync SQLAlchemy session fixtures with async equivalents using `create_async_engine("sqlite+aiosqlite:///:memory:")` and `AsyncSession`

**Checkpoint**: `uv run pytest backend/tests/ -x -q` passes with coverage ≥ 80%.

---

## Phase 3: User Story 1 — Constitution-Compliant Async Backend (Priority: P1) 🎯 MVP

**Goal**: Server starts from env vars, handles concurrent requests without blocking, config is clean.

**Independent Test**: `DATABASE_URL=sqlite+aiosqlite:///qs.db uv run python -m backend.app.main` starts; `curl http://localhost:8000/` returns `{"status":"ok"}`; two concurrent POSTs both succeed.

- [X] T013 [US1] Update `backend/app/api/api.py`: replace hardcoded `allow_origins=["http://localhost:5173"]` with `allow_origins=settings.cors_origins`; import `settings` from `backend.app.config`
- [X] T014 [US1] Verify `backend/app/main.py` calls `Base.metadata.create_all` via async engine: replace `Base.metadata.create_all(bind=engine)` with an async startup using `async with engine.begin() as conn: await conn.run_sync(Base.metadata.create_all)`; use `settings.host`, `settings.port`, `settings.reload` in `uvicorn.run`

**Checkpoint**: Server starts with only `DATABASE_URL` env var; health check returns 200.

---

## Phase 4: User Story 2 — Single Declarative ORM Model (Priority: P2)

**Goal**: Zero `ToDoEntryData` references remain; full test suite passes with single `ToDoORM`.

**Independent Test**: `grep -r "ToDoEntryData" backend/ --include="*.py"` returns no matches; `uv run pytest backend/tests/ -x` passes.

- [X] T015 [P] [US2] Search and replace all remaining `ToDoEntryData` imports and type annotations across all backend test files in `backend/tests/` with `ToDoORM` (imported from `backend.app.data_access.database`)
- [X] T016 [P] [US2] Update `backend/tests/test_data/factories.py`: change `ToDoEntryData` factory to produce `ToDoORM` instances; update import path

**Checkpoint**: `grep -r "ToDoEntryData" backend/ --include="*.py"` → no output; tests pass.

---

## Phase 5: User Story 3 — Rate Limiting and Validated Pagination with Total Count (Priority: P3)

**Goal**: `GET /todo` returns `total_count`; out-of-range params → 422; 61st request → 429.

**Independent Test**: `curl "http://localhost:8000/todo?limit=5&page=1"` includes `total_count`; `curl "http://localhost:8000/todo?limit=0"` → 422; 61 rapid GETs → last one 429.

- [X] T017 [US3] Rewrite `backend/app/api/api.py`: add `from slowapi import Limiter, _rate_limit_exceeded_handler`; add `from slowapi.util import get_remote_address`; add `from slowapi.errors import RateLimitExceeded`; create `limiter = Limiter(key_func=get_remote_address)`; set `app.state.limiter = limiter`; add `app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)`
- [X] T018 [US3] In `backend/app/api/api.py` update `list_todos` route: change signature to `async def list_todos(request: Request, limit: int = Query(10, ge=1, le=100), page: int = Query(1, ge=1))`; add `@limiter.limit("60/minute")` decorator; call `await service.get_count()` for `total_count`; return `ListToDoResponse(success=True, results=len(todos), total_count=total_count, todo_entries=todos)`
- [X] T019 [US3] Add `@limiter.limit("60/minute")` and `request: Request` parameter to `get_todo` route in `backend/app/api/api.py`
- [X] T020 [US3] Add `@limiter.limit("30/minute")` and `request: Request` parameter to `create_todo`, `update_todo`, `delete_todo` routes in `backend/app/api/api.py`
- [X] T021 [US3] Add `get_count` method to `ToDoService` in `backend/app/business_logic/todo_service.py`: `async def get_count(self) -> int: return await self.repository.get_count()`

**Checkpoint**: `curl "localhost:8000/todo?limit=5&page=1"` → `total_count` present; `?limit=0` → 422.

---

## Phase 6: User Story 4 — Soft-Delete Restore Endpoint (Priority: P4)

**Goal**: `PATCH /todo/{id}/restore` un-deletes a todo; `GET /todo/deleted` lists deleted items.

**Independent Test**: Create → delete → `PATCH .../restore` → `GET /todo/{id}` → 200, `deleted=false`.

- [X] T022 [US4] Add `restore_todo` and `get_deleted_todos` methods to `ToDoService` in `backend/app/business_logic/todo_service.py`: `async def restore_todo(self, to_do_id) -> ToDoSchema` (calls `self.repository.restore_to_do`, raises `ToDoNotFoundError` if None); `async def get_deleted_todos(self, limit, page) -> List[ToDoSchema]`
- [X] T023 [US4] Add `GET /todo/deleted` and `PATCH /todo/{todo_id}/restore` routes to `backend/app/api/api.py` **before** the `GET /todo/{todo_id}` route (to prevent path conflict); both with `@limiter.limit("60/minute")` (GET) or `@limiter.limit("30/minute")` (PATCH); add `request: Request` parameter to each
~~- [ ] T024 [US4] Redundant — covered by T007 (Foundational phase already adds `get_deleted_todos`, `restore_to_do`, and `get_count` to `ToDoRepositoryInterface`). No action needed.~~

**Checkpoint**: `curl -X PATCH localhost:8000/todo/{id}/restore` on a deleted todo → 200; on active → 404.

---

## Phase 7: User Story 5 — Description and Done-State in the UI (Priority: P5)

**Goal**: Create/edit forms include description; done checkbox toggles visually; both fields persist.

**Independent Test**: Create a todo with description via form → both fields saved and displayed; click done → checkbox checked and styling changes.

- [X] T025 [P] [US5] Add `total_count: number` field to `TodoListResponse` interface in `frontend/src/types/todo.ts`
- [X] T026 [P] [US5] Add `patch<T>(endpoint: string, body?: unknown, options?: RequestOptions): Promise<T>` method to `ApiClient` class in `frontend/src/services/api/client.ts` (same pattern as `put`)
- [X] T027 [US5] Update `frontend/src/components/todos/TodoForm.tsx`: add `description` state (`useState("")`); add `<Textarea>` field from Chakra UI below the title Input; change `todoData.description` from hardcoded `"not implemented yet"` to `description.trim() || null`; clear description on success
- [X] T028 [US5] Update `frontend/src/components/todos/TodoEditForm.tsx`: add `initialDescription?: string | null` prop; add `description` state pre-populated from prop; add `<Textarea>` field; change `updateData.data.description` from hardcoded `"not implemented yet"` to `description.trim() || null`
- [X] T029 [US5] Update `frontend/src/components/todos/TodoItem.tsx`: add `description: string | null` and `done: boolean` props; add `<Checkbox>` from Chakra UI that calls `useUpdateTodo` with `{ done: !done }` on change using an optimistic update (`onMutate` sets `done` in `['todos', {limit,page}]` cache, `onError` rolls back, `onSettled` invalidates — same pattern as `useDeleteTodo`); display description text below title when present; apply `textDecoration="line-through"` and `opacity={0.6}` to title when `done=true`; pass `initialDescription={description}` to `TodoEditForm`
- [X] T030 [US5] Update `frontend/src/components/todos/TodoList.tsx`: pass `description={todo.description}` and `done={todo.done}` props to each `<TodoItem>`

**Checkpoint**: Create a todo with description; verify both fields in list; check done → strikethrough appears.

---

## Phase 8: User Story 6 — Pagination Controls and Deleted-Todo Restore UI (Priority: P6)

**Goal**: Next/Prev pagination controls work; deleted section lists and restores todos with optimistic update.

**Independent Test**: 15 todos → page 1 shows 10 + Next enabled; click Next → 5 items; delete a todo → open Deleted section → Restore → item reappears in active list immediately.

- [X] T031 [P] [US6] Add `listDeleted(limit, page)` and `restore(todoId)` methods to `TodoApi` class in `frontend/src/services/api/todoApi.ts`: `listDeleted` calls `apiClient.get<TodoListResponse>('/todo/deleted', {params:{limit,page}})`, `restore` calls `apiClient.patch<TodoResponse>('/todo/${todoId}/restore')`
- [X] T032 [P] [US6] Create `frontend/src/hooks/queries/useDeletedTodoList.ts`: `useQuery` with queryKey `['todos','deleted',{limit,page}]` calling `todoApi.listDeleted(limit,page)`
- [X] T033 [P] [US6] Create `frontend/src/hooks/queries/useRestoreTodo.ts`: `useMutation` with `onMutate` that (1) removes the item from `['todos','deleted',{limit:10,page:1}]` cache and (2) prepends the item to `['todos',{limit:10,page:1}]` active cache (the default view); rollback both caches in `onError` via stored snapshots; invalidate all `['todos']` queries in `onSettled` to sync server state
- [X] T034 [P] [US6] Create `frontend/src/components/common/Pagination.tsx`: props `page`, `totalCount`, `limit`, `onNext`, `onPrev`; renders Previous button (disabled when `page===1`) and Next button (disabled when `page * limit >= totalCount`); uses Chakra UI `ButtonGroup`
- [X] T035 [P] [US6] Create `frontend/src/components/todos/TodoRestoreButton.tsx`: props `id: string`; calls `useRestoreTodo().mutate(id)`; shows toast on success/error; uses Chakra UI `Button` size "sm"
- [X] T036 [US6] Update `frontend/src/components/todos/TodoList.tsx`: add `page` state (default 1); pass `page` and `limit=10` to `useTodoList`; render `<Pagination>` below the list using `data?.total_count`; add collapsible `<Accordion>` section "Deleted todos" using `useDeletedTodoList(10,1)` that maps each deleted todo to a row with title and `<TodoRestoreButton>`
- [X] T037 [US6] Update `frontend/src/components/todos/TodoDeleteButton.tsx`: verify the success toast (`showToast({ title: 'Todo deleted', ... })`) is called inside the `onSuccess` callback of `deleteTodo.mutate(id, { onSuccess: ... })`, not in `onMutate`; move it if needed (fix: user sees "deleted" confirmation only after server confirms, not optimistically)

**Checkpoint**: 15 todos → Next/Prev work; delete a todo → open Deleted → Restore → item reappears immediately.

---

## Phase 9: User Story 7 — Shared Validation Hook and Dead-Code Removal (Priority: P7)

**Goal**: `validateTitle` in one file; Header typo fixed; dead code removed; tsc zero errors.

**Independent Test**: `grep -r "validateTitle" frontend/src --include="*.ts" --include="*.tsx" -l` → only `useTodoValidation.ts`; `npx tsc --noEmit` → 0 errors.

- [X] T038 [P] [US7] Create `frontend/src/hooks/useTodoValidation.ts`: export `useTodoValidation()` hook returning `{ validateTitle, validateDescription, error, setError, clearError }`; `validateTitle(value)` returns error string or null (empty → "Todo title cannot be empty", >255 → "Todo title cannot exceed 255 characters"); `validateDescription` returns null (optional field, no hard validation)
- [X] T039 [P] [US7] Fix typo in `frontend/src/components/Header.tsx`: change `justify="space-betwee"` to `justify="space-between"`
- [X] T040 [P] [US7] Remove Vite boilerplate from `frontend/src/App.css`: delete `.logo`, `@keyframes logo-spin`, `.card`, `.read-the-docs` rules; keep only `#root` base styles
- [X] T041 [P] [US7] Delete `frontend/src/components/common/LoadingOverlay.tsx` (unused component)
- [X] T042 [US7] Refactor `frontend/src/components/todos/TodoForm.tsx`: replace local `validateTitle` function and `error`/`setError` state with `const { validateTitle, error, setError, clearError } = useTodoValidation()`; import from `@/hooks/useTodoValidation`
- [X] T043 [US7] Refactor `frontend/src/components/todos/TodoEditForm.tsx`: replace local `validateTitle` function and `error`/`setError` state with `const { validateTitle, error, setError, clearError } = useTodoValidation()`; import from `@/hooks/useTodoValidation`

**Checkpoint**: `grep -r "validateTitle" frontend/src -l` → 1 file; `npx tsc --noEmit` → 0 errors.

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, test coverage gate, bundle size check.

- [X] T044 Run `uv run pytest backend/tests/ --cov=backend/app --cov-fail-under=80 -q` and fix any coverage gaps if below 80%
- [X] T045 Run `cd frontend && npx tsc --noEmit` and fix any remaining TypeScript errors
- [X] T046 Run `cd frontend && npm run build` and verify gzip bundle size < 500 KB
- [X] T047 Run quickstart.md Scenario 9 validation commands to confirm no `validateTitle` duplication and no `LoadingOverlay` references
- [X] T048 [P] Update `backend/tests/test_api/test_list_to_do.py` to assert `total_count` is present in list responses
- [X] T049 [P] Add `backend/tests/test_api/test_restore_endpoint.py`: test `PATCH /todo/{id}/restore` on deleted todo → 200; on active todo → 404; on missing todo → 404
- [X] T050 [P] Add `backend/tests/test_api/test_list_deleted.py`: test `GET /todo/deleted` with deleted items present → 200 + correct entries in `todo_entries`; with no deleted items → 200 + empty `todo_entries`; with `limit` and `page` params → correct pagination (resolves D1 — Principle II compliance: new endpoint must have a test)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — **BLOCKS all user stories**
- **US1 (Phase 3)**: Depends on Phase 2 (async engine, settings)
- **US2 (Phase 4)**: Depends on Phase 2 (ToDoORM established)
- **US3 (Phase 5)**: Depends on Phase 2 (repository has `get_count`) + Phase 3 (routes exist)
- **US4 (Phase 6)**: Depends on Phase 2 (repository has `restore_to_do`) + Phase 3 (routes exist)
- **US5 (Phase 7)**: Depends on Phase 2 (backend complete) — frontend-only changes, can start after Phase 2
- **US6 (Phase 8)**: Depends on US5 (TodoItem props) + US4 (restore endpoint) + US3 (total_count)
- **US7 (Phase 9)**: Depends on US5/US6 (hooks exist to refactor) — can run in parallel with US6
- **Polish (Phase 10)**: Depends on all phases complete

### Parallel Opportunities

Within Phase 2 (T003–T012): T003, T004, T005, T006, T007, T008, T009, T011 can run in parallel after T001–T002 complete.
Within Phase 4 (T015–T016): T015 and T016 are independent files — run in parallel.
Within Phase 7 (T025–T030): T025 and T026 are independent — run in parallel before T027–T030.
Within Phase 8 (T031–T037): T031, T032, T033, T034, T035 are all new files — run in parallel.
Within Phase 9 (T038–T043): T038, T039, T040, T041 are independent — run in parallel.
Within Phase 10: T044, T048, T049, T050 can run in parallel.

---

## Implementation Strategy

### MVP (User Stories 1–2 only)

1. Phase 1: Setup (T001–T002)
2. Phase 2: Foundational (T003–T012) — critical blocker
3. Phase 3: US1 (T013–T014) — async server starts
4. Phase 4: US2 (T015–T016) — single ORM model
5. **STOP and VALIDATE**: `uv run pytest -x -q` passes; server starts from env var

### Incremental Delivery

- After MVP: add Phase 5 (US3) → rate limiting + total_count
- Add Phase 6 (US4) → restore endpoint
- Add Phase 7 (US5) → description + done UI
- Add Phase 8 (US6) → pagination + deleted UI
- Add Phase 9 (US7) → clean up + shared validation
- Phase 10: Polish gates

---

## Notes

- [P] = different files, no inter-task dependencies
- [USN] label maps each task to its user story for traceability
- Phase 2 (T003–T012) is a hard prerequisite for all backend user stories
- Verify `uv run pytest` passes after every backend phase before moving to next
- Frontend phases (7–9) are independent of backend phase ordering after Phase 2 is done
