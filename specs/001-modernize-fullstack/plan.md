# Implementation Plan: Full-Stack Modernization

**Branch**: `001-modernize-fullstack` | **Date**: 2026-04-25 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/001-modernize-fullstack/spec.md`

## Summary

Modernize the basicToDo full-stack application by: (1) exposing all
backend capabilities in the frontend (done status, description field,
soft-delete restore), (2) fixing backend reliability issues (async
database layer, datetime bug, pagination validation, rate limiting),
(3) improving UX consistency (honest error feedback, pagination
controls), and (4) cleaning up code quality (shared validation hook,
single ORM pattern, dead code removal). The existing technology stack
is retained; changes adopt current best practices within each
framework.

## Technical Context

**Language/Version**: Python 3.13+, TypeScript 5.8+
**Primary Dependencies**: FastAPI, SQLAlchemy 2.0 (async), React 19,
Chakra UI 3, TanStack React Query 5, Pydantic, aiosqlite (new)
**Storage**: SQLite via SQLAlchemy async engine (aiosqlite driver)
**Testing**: pytest (backend), vitest (frontend), Playwright (E2E)
**Target Platform**: Web application (Linux/macOS development)
**Project Type**: Web application (REST API + SPA)
**Performance Goals**: <200ms p95 API response, <3s frontend TTI,
<500KB gzipped bundle
**Constraints**: Single-user development context, SQLite database,
no authentication
**Scale/Scope**: ~20 backend source files, ~15 frontend components,
single Todo entity

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Phase 0 Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Clean Architecture | PASS | All changes maintain layered architecture. New restore endpoint follows existing API → Service → Repository flow. |
| II. Type Safety | PASS | Async migration preserves full type annotations. New Pydantic BaseSettings is fully typed. |
| III. Testing Standards | PASS | Each user story includes unit + integration tests. Coverage gate (80%) maintained. |
| IV. UX Consistency | PASS | New UI elements (done toggle, description field, pagination, deleted section) use Chakra UI components. |
| V. Performance | PASS | Async DB layer improves concurrency. No new N+1 patterns. Bundle impact minimal (no new frontend deps). |
| VI. Simplicity | PASS | No speculative abstractions. Each change addresses a concrete current deficiency. aiosqlite is the only new dependency. |

### Post-Phase 1 Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Clean Architecture | PASS | Restore endpoint: API (`PATCH /todo/{id}/restore`) → Service (`restore_todo`) → Repository (`restore_to_do`). Factory wires dependencies. |
| II. Type Safety | PASS | All new functions fully typed. AsyncSession typed via sqlalchemy.ext.asyncio. Pydantic Query validators for pagination. |
| III. Testing Standards | PASS | New tests: restore endpoint (unit + integration), pagination validation, rate limiting, done toggle (frontend), deleted section (frontend). |
| IV. UX Consistency | PASS | Collapsible deleted section uses Chakra Accordion. Done toggle uses Chakra Checkbox. Pagination uses Chakra ButtonGroup. |
| V. Performance | PASS | total_count query adds 1 DB call per list request (acceptable, <5 total). Async eliminates event loop blocking. |
| VI. Simplicity | PASS | Shared validation hook replaces duplicate code. Config refactor reduces complexity. No unnecessary abstractions. |

**No violations. Complexity Tracking table not needed.**

## Project Structure

### Documentation (this feature)

```text
specs/001-modernize-fullstack/
├── plan.md              # This file
├── research.md          # Phase 0: Research decisions
├── data-model.md        # Phase 1: Entity model
├── quickstart.md        # Phase 1: Verification guide
├── contracts/
│   └── api-endpoints.md # Phase 1: API contracts
└── tasks.md             # Phase 2: Task list (via /speckit-tasks)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── main.py                          # Entry point
│   ├── config.py                        # MODIFY: Pydantic BaseSettings
│   ├── factory.py                       # MODIFY: Async wiring
│   ├── logger.py                        # No changes
│   ├── api/
│   │   └── api.py                       # MODIFY: Restore endpoint,
│   │                                    #   pagination validation,
│   │                                    #   rate limiting, total_count
│   ├── business_logic/
│   │   ├── todo_service.py              # MODIFY: Async methods,
│   │   │                                #   restore_todo
│   │   ├── exceptions.py                # No changes
│   │   ├── builders/
│   │   │   ├── builder_interface.py     # No changes
│   │   │   └── todo_entry_builder.py    # MODIFY: Build ToDoORM
│   │   └── validators/                  # No changes
│   ├── data_access/
│   │   ├── database.py                  # MODIFY: Async engine,
│   │   │                                #   AsyncSession, func.now(),
│   │   │                                #   remove imperative mapping
│   │   └── repository.py               # MODIFY: Async methods,
│   │                                    #   restore_to_do,
│   │                                    #   get_deleted_entries,
│   │                                    #   count queries
│   ├── models/
│   │   └── todo.py                      # REMOVE: ToDoEntryData
│   └── schemas/
│       ├── data_schemes/
│       │   ├── create_todo_schema.py    # No changes
│       │   ├── update_todo_schema.py    # No changes
│       │   └── todo_schema.py           # No changes
│       └── response_schemes/
│           └── *.py                     # MODIFY: total_count in list
└── tests/
    ├── conftest.py                      # MODIFY: Async fixtures
    ├── test_api/                        # MODIFY: New endpoint tests
    ├── test_service/                    # MODIFY: Async test methods
    ├── test_validators/                 # No changes
    └── test_builders/                   # MODIFY: Updated builder

frontend/
├── src/
│   ├── App.tsx                          # No changes
│   ├── App.css                          # REMOVE: Dead boilerplate
│   ├── index.css                        # No changes
│   ├── components/
│   │   ├── Header.tsx                   # FIX: Typo
│   │   ├── todos/
│   │   │   ├── TodoList.tsx             # MODIFY: Deleted section,
│   │   │   │                            #   pagination controls
│   │   │   ├── TodoItem.tsx             # MODIFY: Done toggle,
│   │   │   │                            #   description display
│   │   │   ├── TodoForm.tsx             # MODIFY: Description input,
│   │   │   │                            #   shared validation hook
│   │   │   ├── TodoEditForm.tsx         # MODIFY: Description input,
│   │   │   │                            #   shared validation hook
│   │   │   ├── TodoDeleteButton.tsx     # FIX: Toast after confirmation
│   │   │   └── TodoRestoreButton.tsx    # NEW
│   │   ├── common/
│   │   │   ├── Spinner.tsx              # No changes
│   │   │   ├── LoadingOverlay.tsx       # REMOVE: Unused
│   │   │   └── Pagination.tsx           # NEW
│   │   └── errors/                      # No changes
│   ├── hooks/
│   │   ├── queries/
│   │   │   ├── useTodoList.ts           # MODIFY: Accept page/limit
│   │   │   ├── useDeletedTodoList.ts    # NEW
│   │   │   ├── useCreateTodo.ts         # No changes
│   │   │   ├── useUpdateTodo.ts         # No changes
│   │   │   ├── useDeleteTodo.ts         # No changes
│   │   │   └── useRestoreTodo.ts        # NEW
│   │   ├── useTodoValidation.ts         # NEW: Shared validation
│   │   └── useToast.ts                  # No changes
│   ├── services/api/
│   │   ├── client.ts                    # No changes
│   │   └── todoApi.ts                   # MODIFY: restore(), listDeleted()
│   └── types/
│       └── todo.ts                      # MODIFY: total_count, restore types
└── e2e/
    ├── todo-crud.spec.ts                # MODIFY: Done toggle, restore tests
    └── todo-validation.spec.ts          # No changes
```

**Structure Decision**: Retains existing web application layout
(backend/ + frontend/). No new top-level directories. Changes
are modifications to existing files plus a small number of new
files (3 frontend components/hooks, 0 new backend files beyond
the restore method additions).

## Complexity Tracking

> No violations identified. All changes align with constitution
> principles.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| (none) | — | — |
