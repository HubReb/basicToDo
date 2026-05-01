# Implementation Plan: Modernize Full-Stack ToDo Application

**Branch**: `002-modernize-fullstack` | **Date**: 2026-04-25 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/002-modernize-fullstack/spec.md`

## Summary

Bring the existing FastAPI + React ToDo application into full compliance with the project
constitution by: (1) migrating the backend to genuine async I/O via SQLAlchemy async engine
and `aiosqlite`; (2) replacing the broken `Config` class with Pydantic BaseSettings;
(3) removing the dual ORM mapping to a single `ToDoORM` declarative model; (4) wiring up
`slowapi` rate limiting and validated pagination with `total_count`; (5) adding restore and
list-deleted endpoints; (6) completing the frontend with description fields, done-checkbox,
pagination controls, restore UI, a shared validation hook, and dead-code removal.

## Technical Context

**Language/Version**: Python 3.13+ (backend) · TypeScript 5.8 / Node 20+ (frontend)
**Primary Dependencies**:
- Backend: FastAPI 0.115+, SQLAlchemy 2.0+ (async), Pydantic v2, pydantic-settings 2.7+,
  aiosqlite 0.20+, uvicorn, slowapi 0.1.9+
- Frontend: React 19, Vite 6, Chakra UI v3, React Query v5, TypeScript 5.8, vitest
**Storage**: SQLite via `aiosqlite` async driver (table name `toDo`, schema unchanged)
**Testing**: pytest + pytest-asyncio (asyncio_mode=auto), pytest-cov ≥80%; vitest + Testing Library
**Target Platform**: Linux server (backend on port 8000) · Browser, desktop-first SPA (frontend on port 5173)
**Project Type**: Full-stack web service + SPA
**Performance Goals**: API p95 < 200ms single-user local; frontend bundle < 500 KB gzip
**Constraints**: No schema migration (table `toDo` preserved); no auth; no mobile scope;
  existing test suite must continue to pass; coverage must not drop below 80%
**Scale/Scope**: Single user, local dev / personal use; ~10 backend files changed, ~15 frontend files

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Pre-Design Status | Post-Design Status |
|-----------|------------------|--------------------|
| I. Async-First I/O | ❌ VIOLATION — sync SQLAlchemy under async routes | ✅ PASS — async engine + AsyncSession + aiosqlite |
| II. Test Coverage Gate | ⚠️ AT RISK — dual mapping causes import fragility | ✅ PASS — single model, async fixtures, coverage ≥80% |
| III. Single Source of Truth | ❌ VIOLATION — dual ORM mapping; copy-paste validation | ✅ PASS — single ToDoORM; useTodoValidation hook |
| IV. Responsive UI | ❌ VIOLATION — description hardcoded; no done/restore UI | ✅ PASS — description + done + restore with optimistic updates |
| V. Bounded Performance | ❌ VIOLATION — no rate limiting wired up; no total_count | ✅ PASS — slowapi wired; total_count returned; rate limits enforced |

All pre-design violations are resolved by this implementation plan. No gate failures remain.

## Project Structure

### Documentation (this feature)

```text
specs/002-modernize-fullstack/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── api-endpoints.md # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit-tasks — NOT created here)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── api/
│   │   └── api.py                          # MODIFY: add rate limiting, restore/deleted routes,
│   │                                       #   pagination Query validation, route ordering fix
│   ├── business_logic/
│   │   ├── builders/
│   │   │   └── todo_entry_builder.py       # MODIFY: set created_at, use ToDoORM only
│   │   ├── todo_service.py                 # MODIFY: add restore_todo / get_deleted_todos;
│   │   │                                   #   ensure all repo calls are awaited
│   │   └── exceptions.py                  # no change
│   ├── config.py                           # REPLACE: Pydantic BaseSettings
│   ├── data_access/
│   │   ├── database.py                     # REPLACE: async engine, AsyncSession,
│   │   │                                   #   remove ToDoEntryData + imperative mapper
│   │   └── repository.py                  # REPLACE: all methods async; add restore +
│   │                                       #   count + get_deleted methods
│   ├── models/
│   │   └── todo.py                         # EMPTY: ToDoEntryData removed
│   ├── factory.py                          # MODIFY: wire async session manager
│   └── schemas/
│       └── api_responses/
│           └── get_list_to_do_response.py  # MODIFY: add total_count field
├── tests/
│   ├── conftest.py                         # MODIFY: async fixtures, AsyncMock repo
│   └── test_api/
│       ├── test_restore_endpoint.py        # NEW: restore + list-deleted tests
│       └── (existing test files)           # MODIFY: fix AsyncMock where needed
└── pyproject.toml                          # MODIFY: add aiosqlite, pydantic-settings;
                                            #   set asyncio_mode = "auto"

frontend/src/
├── components/
│   ├── common/
│   │   └── Pagination.tsx                  # NEW: prev/next controls
│   ├── todos/
│   │   ├── TodoForm.tsx                    # MODIFY: add description field + useTodoValidation
│   │   ├── TodoEditForm.tsx                # MODIFY: add description + useTodoValidation
│   │   ├── TodoItem.tsx                    # MODIFY: add Checkbox, description display
│   │   ├── TodoList.tsx                    # MODIFY: pagination + deleted section
│   │   ├── TodoDeleteButton.tsx            # MODIFY: move success toast to onSuccess
│   │   └── TodoRestoreButton.tsx           # NEW: restore button with optimistic update
│   └── Header.tsx                          # MODIFY: fix justify typo
├── hooks/
│   ├── queries/
│   │   ├── useDeletedTodoList.ts           # NEW: query for deleted todos
│   │   └── useRestoreTodo.ts               # NEW: mutation with optimistic removal
│   └── useTodoValidation.ts               # NEW: shared validation hook (Principle III)
├── services/api/
│   ├── client.ts                           # MODIFY: add patch<T>() method
│   └── todoApi.ts                          # MODIFY: add listDeleted() + restore()
├── types/
│   └── todo.ts                             # MODIFY: add total_count to TodoListResponse
└── App.css                                 # MODIFY: remove Vite boilerplate
```

**Structure Decision**: Web application (Option 2). Backend and frontend are separate
subdirectories at the repo root. No new top-level directories are introduced.

## Complexity Tracking

> No constitution violations remain that require justification. All violations are resolved
> by this plan's implementation approach.
