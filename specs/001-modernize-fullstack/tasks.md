# Tasks: Full-Stack Modernization

**Input**: Design documents from `specs/001-modernize-fullstack/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Tests are included where they cover new or significantly changed behavior, consistent with the project's existing testing patterns and Constitution Principle III.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (New Dependencies & Configuration)

**Purpose**: Add new dependencies and modernize configuration before any feature work.

- [x] T001 Add `aiosqlite` dependency to `pyproject.toml` and run `uv sync`
- [x] T002 [P] Refactor `backend/app/config.py` from manual `os.environ` to Pydantic `BaseSettings` with typed fields (`database_url`, `host`, `port`, `cors_origins`) per research R8

---

## Phase 2: Foundational (Async Database Layer & ORM Cleanup)

**Purpose**: Migrate the database layer to async and consolidate ORM patterns. BLOCKS all user stories.

**CRITICAL**: No user story work can begin until this phase is complete.

- [x] T003 Convert `backend/app/data_access/database.py`: replace `create_engine` with `create_async_engine`, replace `sessionmaker` with `async_sessionmaker(class_=AsyncSession)`, replace `safe_session_scope` with async context manager, change connection string to `sqlite+aiosqlite:///`, fix `created_at` default from `datetime.datetime.now()` to `server_default=func.now()` per research R1, R3
- [ ] T004 Remove imperative mapping (`registry.map_imperatively`) and `ToDoEntryData` dataclass from `backend/app/data_access/database.py` and `backend/app/models/todo.py` per research R2. Ensure `ToDoORM` declarative class is the single mapping.
- [ ] T005 Convert all methods in `backend/app/data_access/repository.py` to async (`async def`), use `AsyncSession`, update all queries to use `await session.execute()` pattern
- [ ] T006 Update `backend/app/business_logic/todo_service.py`: make all service methods async, await repository calls
- [ ] T007 Update `backend/app/business_logic/builders/todo_entry_builder.py`: build `ToDoORM` instances instead of `ToDoEntryData`
- [ ] T008 Update `backend/app/factory.py`: wire async session scope and async repository into service creation
- [ ] T009 Update `backend/app/api/api.py`: ensure all route handlers are `async def` and await service methods
- [ ] T010 Update `backend/app/main.py`: use async engine for `create_all` (via `async with engine.begin()`)
- [ ] T011 Update `backend/tests/conftest.py`: create async test fixtures (`test_async_engine`, `test_async_session`, `async_session_scope`), update `todo_service_with_real_db` to use async in-memory SQLite
- [ ] T012 Fix all existing backend tests to work with async service/repository (use `pytest-asyncio` `async def` test functions, update mock signatures)
- [ ] T013 Run `uv run pytest backend/tests/` — all existing tests MUST pass with async migration
- [ ] T014 Run `uv run mypy backend/app/` — zero errors with async types

**Checkpoint**: Async database layer complete. All existing tests pass. ORM uses single declarative pattern.

---

## Phase 3: User Story 1 — Complete Todo Lifecycle (Priority: P1) MVP

**Goal**: Expose done toggle, description field, and soft-delete restore in the UI.

**Independent Test**: Create a todo with title and description, mark done, edit description, soft-delete, view in deleted section, restore to active list.

### Backend: Restore Endpoint (US1)

- [ ] T015 [US1] Add `restore_to_do(to_do_id: UUID) -> Optional[ToDoORM]` method to repository interface and implementation in `backend/app/data_access/repository.py` — sets `deleted=False`, `updated_at=now()`
- [ ] T016 [US1] Add `get_deleted_entries(limit: int, page: int) -> List[ToDoORM]` and `count_deleted() -> int` methods to repository in `backend/app/data_access/repository.py`
- [ ] T017 [US1] Add `restore_todo(to_do_id: UUID) -> ToDoSchema` and `get_deleted_todos(limit, page)` methods to `backend/app/business_logic/todo_service.py`
- [ ] T018 [US1] Add `PATCH /todo/{todo_id}/restore` endpoint and `GET /todo/deleted` endpoint to `backend/app/api/api.py` per contracts/api-endpoints.md
- [ ] T019 [US1] Add `total_count: int` field to `ListToDoResponse` in `backend/app/schemas/response_schemes/` and update `GET /todo` and `GET /todo/deleted` handlers to return it
- [ ] T020 [US1] Add `count_active() -> int` method to repository in `backend/app/data_access/repository.py` for total_count support

### Backend Tests (US1)

- [ ] T021 [P] [US1] Add unit tests for `restore_todo` service method in `backend/tests/test_service/unit/test_restore_todo.py`
- [ ] T022 [P] [US1] Add integration tests for `PATCH /todo/{id}/restore` and `GET /todo/deleted` endpoints in `backend/tests/test_api/test_restore_endpoint.py` — include test that restoring a non-deleted (active) todo returns 404

### Frontend: API & Types (US1)

- [ ] T023 [US1] Add `total_count` to `TodoListResponse` type, add `RestoreTodoResponse` type in `frontend/src/types/todo.ts`
- [ ] T024 [US1] Add `restore(todoId)` and `listDeleted(limit, page)` methods to `frontend/src/services/api/todoApi.ts`

### Frontend: Done Toggle (US1)

- [ ] T025 [US1] Update `TodoItem.tsx` in `frontend/src/components/todos/TodoItem.tsx`: add Chakra Checkbox for done toggle, display description text, pass full todo data (not just id/title) as props
- [ ] T026 [US1] Update `useUpdateTodo.ts` in `frontend/src/hooks/queries/useUpdateTodo.ts`: ensure optimistic update handles `done` toggle correctly

### Frontend: Description Field (US1)

- [ ] T027 [US1] Update `TodoForm.tsx` in `frontend/src/components/todos/TodoForm.tsx`: add optional description textarea input, remove hardcoded `"not implemented yet"` description
- [ ] T028 [US1] Update `TodoEditForm.tsx` in `frontend/src/components/todos/TodoEditForm.tsx`: add description textarea, remove hardcoded description, pass description to update mutation

### Frontend: Deleted Section & Restore (US1)

- [ ] T029 [US1] Create `useDeletedTodoList` hook in `frontend/src/hooks/queries/useDeletedTodoList.ts` using `todoApi.listDeleted()`
- [ ] T030 [US1] Create `useRestoreTodo` hook in `frontend/src/hooks/queries/useRestoreTodo.ts` with optimistic removal from deleted list and cache invalidation of active list
- [ ] T031 [US1] Create `TodoRestoreButton` component in `frontend/src/components/todos/TodoRestoreButton.tsx` using Chakra Button with loading state
- [ ] T032 [US1] Update `TodoList.tsx` in `frontend/src/components/todos/TodoList.tsx`: add collapsible "Deleted" section (Chakra Accordion) below active list, render deleted todos with restore buttons

### Frontend Tests (US1)

- [ ] T033 [P] [US1] Add unit test for TodoItem done toggle and description display in `frontend/src/components/todos/__tests__/TodoItem.test.tsx`
- [ ] T034 [P] [US1] Add E2E test for full lifecycle (create with description, mark done, delete, restore) in `frontend/e2e/todo-crud.spec.ts`

**Checkpoint**: Full todo lifecycle works end-to-end. Done toggle, description, soft-delete restore all functional.

---

## Phase 4: User Story 2 — Reliable Error Handling and Feedback (Priority: P2)

**Goal**: Ensure all mutations show accurate feedback only after server confirmation, with retry on failure.

**Independent Test**: Stop backend, attempt CRUD operations, verify error messages with retry. Restart, verify retry works.

- [ ] T035 [US2] Fix `TodoDeleteButton.tsx` in `frontend/src/components/todos/TodoDeleteButton.tsx`: move success toast from before mutation to `onSuccess` callback, add error toast with retry in `onError`
- [ ] T036 [US2] Review and fix all mutation hooks (`useCreateTodo.ts`, `useUpdateTodo.ts`, `useDeleteTodo.ts`, `useRestoreTodo.ts`) in `frontend/src/hooks/queries/`: ensure `onError` callbacks show descriptive error toasts with retry actions, ensure `onSuccess` shows success toast (not before)
- [ ] T037 [US2] Update `TodoForm.tsx` in `frontend/src/components/todos/TodoForm.tsx`: retain form input on submission failure (don't clear until `onSuccess`), show inline validation errors without toast
- [ ] T038 [US2] Update `TodoEditForm.tsx` in `frontend/src/components/todos/TodoEditForm.tsx`: retain edit state on failure, show inline errors
- [ ] T039 [P] [US2] Add E2E test for error scenarios in `frontend/e2e/todo-error-handling.spec.ts`: test error display when backend is unreachable, test retry behavior

**Checkpoint**: All user actions show honest feedback. No success before confirmation. Retry works on all mutations.

---

## Phase 5: User Story 3 — Paginated and Navigable Todo List (Priority: P3)

**Goal**: Add pagination controls so all todos are accessible.

**Independent Test**: Create 15 todos, verify pagination shows 2 pages, navigate between them.

### Backend (US3)

- [ ] T040 [US3] Add Pydantic `Query` validation to `GET /todo` and `GET /todo/deleted` endpoints in `backend/app/api/api.py`: `limit: int = Query(10, ge=1, le=100)`, `page: int = Query(1, ge=1)` per research R6
- [ ] T041 [P] [US3] Add unit test for invalid pagination params (negative, zero, >100) in `backend/tests/test_api/test_pagination_validation.py`

### Frontend (US3)

- [ ] T042 [US3] Create `Pagination` component in `frontend/src/components/common/Pagination.tsx`: prev/next buttons, page indicator, disabled states at boundaries, using Chakra ButtonGroup
- [ ] T043 [US3] Update `useTodoList.ts` in `frontend/src/hooks/queries/useTodoList.ts`: accept `page` and `limit` as parameters, include in query key
- [ ] T044 [US3] Update `TodoList.tsx` in `frontend/src/components/todos/TodoList.tsx`: add page state, render `Pagination` component below todo list, compute total pages from `total_count`
- [ ] T045 [P] [US3] Add E2E test for pagination in `frontend/e2e/todo-pagination.spec.ts`: create 15 todos, verify 2 pages, navigate forward/back

**Checkpoint**: All todos accessible via pagination. Controls disabled at boundaries.

---

## Phase 6: User Story 4 — Backend Robustness (Priority: P4)

**Goal**: Wire rate limiting, validate all inputs at API boundaries.

**Independent Test**: Send invalid params (expect 422), burst requests (expect 429).

- [ ] T046 [US4] Wire `slowapi` rate limiting in `backend/app/api/api.py`: create `Limiter` instance, add `@limiter.limit("60/minute")` to GET endpoints, `@limiter.limit("30/minute")` to POST/PUT/DELETE/PATCH endpoints, add `SlowAPIMiddleware`, return 429 with `Retry-After` header per research R7
- [ ] T047 [P] [US4] Add test for rate limiting in `backend/tests/test_api/test_rate_limiting.py`: verify 429 response after exceeding limit
- [ ] T048 [P] [US4] Add test verifying `created_at` timestamp reflects actual creation time (not module load time) in `backend/tests/test_service/integration/test_timestamp.py`

**Checkpoint**: Rate limiting active. Invalid inputs rejected. Timestamps correct.

---

## Phase 7: User Story 5 — Code Quality and Developer Experience (Priority: P5)

**Goal**: Eliminate dead code, deduplicate validation, clean up inconsistencies.

**Independent Test**: Run full linter/type-checker/test suite with zero errors and zero warnings.

- [ ] T049 [US5] Create shared `useTodoValidation` hook in `frontend/src/hooks/useTodoValidation.ts`: extract `validateTitle`, `validateDescription`, `MAX_TITLE_LENGTH`, error state management per research R4
- [ ] T050 [US5] Refactor `TodoForm.tsx` in `frontend/src/components/todos/TodoForm.tsx` to use `useTodoValidation` hook, remove inline validation logic
- [ ] T051 [US5] Refactor `TodoEditForm.tsx` in `frontend/src/components/todos/TodoEditForm.tsx` to use `useTodoValidation` hook, remove inline validation logic
- [ ] T052 [P] [US5] Delete unused `LoadingOverlay.tsx` from `frontend/src/components/common/LoadingOverlay.tsx`
- [ ] T053 [P] [US5] Remove dead CSS boilerplate from `frontend/src/App.css` (`.logo`, `.logo-spin`, `.card`, `.read-the-docs` rules)
- [ ] T054 [P] [US5] Fix typo in `frontend/src/components/Header.tsx`: change `justify="space-betwee"` to `justify="space-between"`
- [ ] T055 [US5] Run `uv run mypy backend/app/` — verify zero errors
- [ ] T056 [US5] Run `cd frontend && npm run lint` — verify zero errors
- [ ] T057 [US5] Run `uv run pytest backend/tests/` — verify all pass with >= 80% coverage
- [ ] T058 [US5] Run `cd frontend && npm test -- --run` — verify all pass

**Checkpoint**: Clean codebase. Single validation source. No dead code. All quality gates green.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final verification across all user stories.

- [ ] T059 Run full E2E test suite: `cd frontend && npx playwright test` — all tests pass
- [ ] T060 Verify quickstart.md scenarios manually in browser per `specs/001-modernize-fullstack/quickstart.md`
- [ ] T061 [P] Run `cd backend && uv run black --check app/` — zero reformats needed
- [ ] T062 Check frontend production bundle size: `cd frontend && npm run build` — verify gzipped output < 500KB

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup (T001) — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Foundational (Phase 2) completion
- **US2 (Phase 4)**: Depends on US1 (Phase 3) — fixes error handling on components US1 creates
- **US3 (Phase 5)**: Depends on Foundational (Phase 2) — can run parallel to US1 if total_count (T019-T020) is complete
- **US4 (Phase 6)**: Depends on Foundational (Phase 2) — can run parallel to US1/US3
- **US5 (Phase 7)**: Depends on US1-US4 — cleanup must happen after feature work
- **Polish (Phase 8)**: Depends on all phases complete

### User Story Dependencies

- **US1 (P1)**: Depends on Phase 2 only. No dependencies on other stories.
- **US2 (P2)**: Depends on US1 (fixes error handling for components introduced in US1).
- **US3 (P3)**: Depends on Foundational (Phase 2) + T019-T020 from US1 (total_count). Backend tasks (T040-T041) are independent of US1; frontend tasks (T042-T044) require T019-T020 to be complete first.
- **US4 (P4)**: Depends on Phase 2. Independent of other stories.
- **US5 (P5)**: Depends on US1-US4 (cleanup after all features stable).

### Within Each User Story

- Backend before frontend (API must exist before UI consumes it)
- Types/API client before hooks
- Hooks before components
- Implementation before tests (tests verify implemented behavior)

### Parallel Opportunities

- T001 and T002 can run in parallel (different files)
- T021 and T022 can run in parallel (different test files)
- T033 and T034 can run in parallel (unit vs E2E)
- T041 and T045 can run in parallel (backend vs frontend tests)
- T046, T047, T048 can run in parallel (different files)
- T052, T053, T054 can run in parallel (independent deletions/fixes)

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T002)
2. Complete Phase 2: Foundational — async migration (T003-T014)
3. Complete Phase 3: User Story 1 — full lifecycle (T015-T034)
4. **STOP and VALIDATE**: Test full lifecycle per quickstart.md
5. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → Async database working
2. Add US1 → Full lifecycle (MVP!)
3. Add US2 → Reliable error handling
4. Add US3 → Pagination
5. Add US4 → Rate limiting + validation
6. Add US5 → Code cleanup
7. Polish → Final verification

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
