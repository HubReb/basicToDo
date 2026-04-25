# Feature Specification: Modernize Full-Stack ToDo Application

**Feature Branch**: `002-modernize-fullstack`
**Created**: 2026-04-25
**Status**: Draft
**Input**: User description: "Reverse engineer this code base: Backend, frontend. Modernize it to main stream frameworks"

## Context

The existing application is a full-stack ToDo manager consisting of a FastAPI backend and a
React/Chakra UI frontend. Reverse engineering reveals issues that violate the project
constitution:

**Constitution violations found:**

- **Principle I (Async-First I/O)**: The backend uses synchronous SQLAlchemy sessions wrapped
  inside `async def` service methods — blocking the event loop on every DB operation.
- **Principle II (Test Coverage Gate)**: The broken `Config` class and dual ORM mapping
  cause import errors in some environments, threatening test suite stability.
- **Principle III (Single Source of Truth)**: A dual ORM mapping exists (`ToDoORM` declarative
  + `mapper_registry.map_imperatively(ToDoEntryData, ...)`) — two definitions for one table.
  Title validation logic is copy-pasted verbatim in `TodoForm` and `TodoEditForm`.
- **Principle IV (Responsive User Interface)**: No `done` checkbox, no description field,
  no restore UI — features the backend already supports are invisible to users.
- **Principle V (Bounded Performance)**: No rate limiting is wired up despite `slowapi` being
  installed. No `total_count` in list responses makes client-side pagination impossible.

This spec defines the work to bring both layers into full constitution compliance.

---

## User Scenarios & Testing

### User Story 1 — Constitution-Compliant Async Backend (Priority: P1)

As a developer, I need the backend to run on a genuine async I/O stack and use environment-
variable-driven configuration so that it is constitution-compliant, starts without a JSON
config file, and handles concurrent requests without blocking the event loop.

**Why this priority**: Synchronous DB calls inside async routes are a Principle I violation
and the root cause of concurrency bugs. The broken `Config` class prevents clean startup.

**Independent Test**: Start the server with only `DATABASE_URL` set as an env var, issue two
concurrent POST requests, verify both succeed and appear in the DB.

**Acceptance Scenarios**:

1. **Given** `DATABASE_URL` is set as an env var, **When** the server starts, **Then** it
   starts without errors and without requiring any JSON config file.
2. **Given** two simultaneous POST `/todo` requests, **When** they arrive at the same time,
   **Then** both return HTTP 201 and both records persist.
3. **Given** an invalid `DATABASE_URL`, **When** the server starts, **Then** it fails fast
   with a descriptive error.
4. **Given** no `DATABASE_URL` is set, **When** the server starts, **Then** it uses the
   SQLite default path without error.

---

### User Story 2 — Single Declarative ORM Model (Priority: P2)

As a developer, I need a single authoritative ORM mapping so that the Principle III
(Single Source of Truth) requirement is met and schema changes only need to happen in
one place.

**Why this priority**: The dual mapping (`ToDoORM` + `ToDoEntryData`) is an active Principle
III violation. Any schema change must currently be made in two places and can diverge silently.

**Independent Test**: Run the full backend test suite — all tests pass with only `ToDoORM` as
the mapped entity; no `ToDoEntryData` references exist anywhere.

**Acceptance Scenarios**:

1. **Given** `ToDoEntryData` and the imperative mapper are removed, **When** the test suite
   runs, **Then** zero import errors occur and all tests pass.
2. **Given** a `create_to_do` repository call with a `ToDoORM` object, **When** it executes,
   **Then** the record is persisted and retrievable by ID.
3. **Given** existing database rows, **When** the app restarts with the single-model code,
   **Then** all existing data is still accessible.

---

### User Story 3 — Rate Limiting and Validated Pagination with Total Count (Priority: P3)

As an API consumer, I need the list endpoint to return `total_count` alongside results and
the API to enforce rate limits so that Principle V (Bounded Performance) is met and the
frontend can build accurate pagination controls.

**Why this priority**: Without rate limiting the API is unprotected (Principle V violation).
Without `total_count` the UI cannot know whether more pages exist.

**Independent Test**: Call `GET /todo?limit=5&page=1`, verify the response includes
`total_count`. Send 61 read requests in under one minute from the same IP, verify the 61st
returns HTTP 429.

**Acceptance Scenarios**:

1. **Given** 25 todos exist, **When** `GET /todo?limit=5&page=1` is called, **Then** the
   response contains 5 `todo_entries` and `total_count=25`.
2. **Given** `limit=0` or `limit=200`, **When** the request is made, **Then** HTTP 422 is
   returned.
3. **Given** `page=0`, **When** the request is made, **Then** HTTP 422 is returned.
4. **Given** 60 read requests from one IP in one minute, **When** the 61st arrives, **Then**
   HTTP 429 is returned with a `Retry-After` header.
5. **Given** 30 write requests from one IP in one minute, **When** the 31st arrives, **Then**
   HTTP 429 is returned.

---

### User Story 4 — Soft-Delete Restore Endpoint (Priority: P4)

As a user, I want to be able to restore a soft-deleted todo so that accidental deletions do
not cause permanent data loss.

**Why this priority**: The `deleted` boolean flag already exists in the schema — soft delete
is half-implemented. Without a restore path users have no recourse after an accidental delete.

**Independent Test**: Create a todo, delete it (soft), call `PATCH /todo/{id}/restore`, then
`GET /todo/{id}` — verify `deleted=false` and the item appears in the active list.

**Acceptance Scenarios**:

1. **Given** a soft-deleted todo, **When** `PATCH /todo/{id}/restore` is called, **Then**
   `deleted` is set to `false` and the item reappears in the active list.
2. **Given** a non-existent ID, **When** `PATCH /todo/{id}/restore` is called, **Then**
   HTTP 404 is returned.
3. **Given** an active (non-deleted) todo, **When** `PATCH /todo/{id}/restore` is called,
   **Then** HTTP 404 is returned.
4. **Given** `GET /todo/deleted` is called with soft-deleted todos present, **Then** they
   are returned in a paginated list.

---

### User Story 5 — Description and Done-State in the UI (Priority: P5)

As a user, I want to add an optional description to a todo and mark it as done so that I
can capture context and track completion visually — bringing the UI into alignment with the
backend schema which already supports both fields.

**Why this priority**: `description` and `done` are stored in the database but invisible
in the UI. The frontend hardcodes `description` as `"not implemented yet"`, violating
Principle III (Single Source of Truth — the DB has the real value, the UI ignores it).

**Independent Test**: Create a todo with a description via the form; verify both fields
are saved and displayed. Click the done checkbox; verify the item is visually marked complete.

**Acceptance Scenarios**:

1. **Given** the create form, **When** a user fills in title and description and submits,
   **Then** both fields are saved and the description is displayed in the list.
2. **Given** a todo item, **When** the user clicks the done checkbox, **Then** the `done`
   state toggles and the item shows distinct visual styling.
3. **Given** the edit form, **When** a user changes the description, **Then** the updated
   value is shown after saving.
4. **Given** a todo with `done=true`, **When** the list renders, **Then** the item displays
   a checked checkbox.

---

### User Story 6 — Pagination Controls and Deleted-Todo Restore UI (Priority: P6)

As a user, I want to navigate between pages of todos and view and restore soft-deleted items
so that I can manage a large list and recover from accidental deletes without developer
intervention.

**Why this priority**: Pagination is hardcoded to page 1 / limit 10 in the current UI.
The restore API (Story 4) needs a UI surface before it delivers user value.

**Independent Test**: Create 15 todos, verify the list shows 10 items and a Next button.
Click Next, verify 5 items appear. Delete a todo, open the Deleted section, click Restore,
verify the item reappears in the active list with an optimistic update (Principle IV).

**Acceptance Scenarios**:

1. **Given** 15 active todos at page 1 limit 10, **When** the list renders, **Then** a Next
   button is visible and Previous is disabled.
2. **Given** the user clicks Next, **When** the page loads, **Then** the remaining 5 todos
   appear on page 2.
3. **Given** page 2 is active, **When** the user clicks Previous, **Then** page 1 reloads.
4. **Given** a soft-deleted todo, **When** the user opens the Deleted section, **Then** the
   todo is listed with a Restore button.
5. **Given** the user clicks Restore, **When** the API call succeeds, **Then** the item
   disappears from the deleted list and reappears in the active list — optimistic update
   applied before the server responds (Principle IV).

---

### User Story 7 — Shared Validation Hook and Dead-Code Removal (Priority: P7)

As a developer, I need duplicated title-validation logic extracted into a single shared hook
and dead code removed so that Principle III (Single Source of Truth) is fully satisfied on
the frontend.

**Why this priority**: `validateTitle` is copy-pasted in `TodoForm` and `TodoEditForm` —
a clear Principle III violation. Dead code (Vite boilerplate CSS, unused `LoadingOverlay`,
Header typo) inflates the bundle and creates confusion.

**Independent Test**: TypeScript compiles with zero errors. `validateTitle` exists in exactly
one file. The Header renders with `justify="space-between"`. Vite boilerplate and
`LoadingOverlay` are gone.

**Acceptance Scenarios**:

1. **Given** a shared `useTodoValidation` hook, **When** `TodoForm` and `TodoEditForm` use it,
   **Then** the `validateTitle` function is defined exactly once in the codebase.
2. **Given** the Header component, **When** rendered, **Then** `justify` equals
   `"space-between"` (not `"space-betwee"`).
3. **Given** `App.css`, **When** audited, **Then** Vite boilerplate (logo spin, `.card`,
   `.read-the-docs`) is absent.
4. **Given** `LoadingOverlay.tsx` is unused, **When** it is deleted, **Then** no TypeScript
   import errors occur.

---

### Edge Cases

- What happens if the database file is missing at startup? The app must create it automatically.
- How does soft-delete interact with `GET /todo/{id}`? Soft-deleted items must return HTTP 404.
- What if a user submits a whitespace-only title? Backend rejects with HTTP 400; frontend shows
  an inline error before submission.
- What if `page` is beyond the last page? An empty `todo_entries` array with correct
  `total_count` is returned.
- What if rate limiting blocks a legitimate user? The 429 response must include `Retry-After`.

---

## Requirements

### Functional Requirements

- **FR-001**: The backend MUST use non-blocking async database sessions for all operations
  (Principle I compliance).
- **FR-002**: Configuration MUST be driven by environment variables with sensible defaults;
  no JSON config file dependency (Principle I / startup reliability).
- **FR-003**: The ORM layer MUST use a single declarative model (`ToDoORM`); `ToDoEntryData`
  and the imperative mapper MUST be removed (Principle III compliance).
- **FR-004**: `GET /todo` MUST return a `total_count` field for the total number of
  non-deleted todos (Principle V / pagination).
- **FR-005**: The API MUST enforce rate limits: 60 req/min for reads, 30 req/min for writes,
  per IP; exceeding limits MUST return HTTP 429 with `Retry-After` (Principle V compliance).
- **FR-006**: Pagination parameters `limit` (1–100) and `page` (≥1) MUST be validated;
  out-of-range values MUST return HTTP 422.
- **FR-007**: A `PATCH /todo/{id}/restore` endpoint MUST un-delete a soft-deleted todo.
- **FR-008**: A `GET /todo/deleted` endpoint MUST return a paginated list of soft-deleted todos.
- **FR-009**: The create-todo form MUST include an optional description field; the value MUST
  be sent to the backend (not hardcoded).
- **FR-010**: The edit-todo form MUST include the description field pre-populated with the
  current value.
- **FR-011**: Each todo item MUST display a checkbox toggling `done`; visually distinct styling
  MUST be applied when `done=true` (Principle IV — user sees result immediately).
- **FR-012**: The todo list MUST display Previous / Next pagination controls driven by
  `total_count`; controls MUST be disabled at boundary pages.
- **FR-013**: A collapsible Deleted section MUST list soft-deleted todos with a Restore button
  per item; restore MUST use an optimistic update (Principle IV compliance).
- **FR-014**: Title validation logic MUST exist in a single shared `useTodoValidation` hook
  used by both create and edit forms (Principle III compliance).
- **FR-015**: The Header `justify` prop typo (`"space-betwee"`) MUST be fixed.
- **FR-016**: Dead code (Vite boilerplate in `App.css`, unused `LoadingOverlay.tsx`) MUST be
  removed.

### Key Entities

- **Todo**: `id` (UUID), `title` (string ≤255 chars, required), `description` (string ≤255
  chars, optional), `created_at` (timestamp), `updated_at` (timestamp, nullable),
  `deleted` (boolean, default false), `done` (boolean, default false).

---

## Success Criteria

### Measurable Outcomes

- **SC-001**: Full backend test suite passes with coverage ≥ 80% (Principle II gate).
- **SC-002**: All API endpoints respond within 200ms at p95 for single-user local use
  (Principle V gate).
- **SC-003**: TypeScript compilation completes with zero errors (Principle II gate).
- **SC-004**: Frontend production bundle is under 500 KB gzip (Principle V gate).
- **SC-005**: A user can create, view, edit, mark-done, soft-delete, and restore a todo
  without a page reload.
- **SC-006**: Sending 61 consecutive read requests from one IP in under one minute results
  in a 429 on the 61st (Principle V gate).
- **SC-007**: The `validateTitle` function appears in exactly one source file (Principle III
  gate).

---

## Assumptions

- SQLite is the target database for development and testing; the async driver is `aiosqlite`.
- The frontend runs on Vite + React 19 + Chakra UI v3 + React Query v5; no framework
  migration is in scope.
- The backend runs on FastAPI + SQLAlchemy 2 + Pydantic v2; no framework migration is in
  scope.
- Mobile/responsive design is out of scope; desktop-first single-page app.
- Authentication and multi-user support are out of scope.
- The existing database schema (table `toDo`) must be preserved; no migrations required.
- `pydantic-settings` and `aiosqlite` will be added as backend dependencies.
- `slowapi` is already in `pyproject.toml` and will be wired up as part of this work.
