# Feature Specification: Full-Stack Modernization

**Feature Branch**: `001-modernize-fullstack`
**Created**: 2026-04-25
**Status**: Draft
**Input**: User description: "Reverse engineer this code base: Backend, frontend. Modernize it to main stream frameworks"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Complete Todo Lifecycle (Priority: P1)

A user opens the application and manages their todos through the full
lifecycle: create, view, edit, mark as done, soft-delete, and restore.
Currently, the "done" status exists in the backend but is invisible in
the frontend, descriptions are hardcoded, and deleted items cannot be
restored. After modernization, every field and state transition the
backend supports is usable from the UI.

**Why this priority**: The application's core value proposition is todo
management. Half of the backend capabilities (done, description, restore)
are inaccessible from the frontend, making the product incomplete.

**Independent Test**: Create a todo with title and description, mark it
done (verify visual indicator), edit the description, soft-delete it,
view it in a "deleted" section, restore it, and confirm it reappears
in the active list.

**Acceptance Scenarios**:

1. **Given** a user on the main screen, **When** they create a todo with
   a title and description, **Then** both fields appear in the todo list
   with a timestamp.
2. **Given** an active todo, **When** the user marks it as done, **Then**
   the todo displays a visual "completed" indicator and remains in the
   active list.
3. **Given** a completed todo, **When** the user unmarks it, **Then**
   the completed indicator is removed.
4. **Given** an active todo, **When** the user soft-deletes it, **Then**
   it disappears from the active list and appears in a recoverable
   "deleted" section.
5. **Given** a soft-deleted todo, **When** the user restores it, **Then**
   it reappears in the active list with its original data intact.

---

### User Story 2 - Reliable Error Handling and Feedback (Priority: P2)

A user performs actions that may fail (network errors, validation
failures, server errors) and receives clear, actionable feedback for
every outcome. Currently, some success toasts fire before API
confirmation, error messages are generic, and there is no retry
mechanism visible to the user for all failure scenarios.

**Why this priority**: Trust in the application depends on honest
feedback. Showing "success" before confirmation and displaying vague
errors erodes user confidence and causes confusion.

**Independent Test**: Disconnect the backend, attempt CRUD operations,
and verify that every action shows an appropriate error message with
a retry option. Reconnect and verify retry works.

**Acceptance Scenarios**:

1. **Given** a network failure during todo creation, **When** the
   creation fails, **Then** an error message appears with a retry
   button and the form retains the user's input.
2. **Given** a validation failure (empty title, title too long),
   **When** the user submits, **Then** a specific validation message
   appears inline without a toast.
3. **Given** a server error during deletion, **When** the delete
   fails, **Then** the todo reappears in the list and an error
   toast explains what happened.
4. **Given** any failed mutation, **When** the user clicks retry,
   **Then** the original operation is re-attempted without requiring
   the user to re-enter data.

---

### User Story 3 - Paginated and Navigable Todo List (Priority: P3)

A user with many todos can browse through them efficiently. Currently,
the frontend hardcodes `limit=10, page=1` with no pagination controls,
making todos beyond the first page inaccessible.

**Why this priority**: Without pagination, the application silently
hides data. Users who create more than 10 todos lose visibility of
older items with no indication that more exist.

**Independent Test**: Create 15 todos, verify the first page shows 10,
navigate to page 2 and verify the remaining 5 appear, navigate back
and confirm page 1 is intact.

**Acceptance Scenarios**:

1. **Given** more todos than fit on one page, **When** the list
   loads, **Then** pagination controls appear showing the current
   page and total pages.
2. **Given** the user is on page 1, **When** they navigate to
   page 2, **Then** the next set of todos loads without a full
   page refresh.
3. **Given** the user is on the last page, **When** they look at
   pagination controls, **Then** the "next" control is disabled.

---

### User Story 4 - Backend Robustness and Async Performance (Priority: P4)

The backend handles concurrent requests without blocking and validates
all inputs at system boundaries. Currently, the repository layer is
synchronous (blocking the event loop), pagination parameters are
unvalidated, rate limiting is configured but unused, and the datetime
default is evaluated once at module load.

**Why this priority**: Backend reliability underpins every frontend
feature. Blocking I/O in an async framework defeats its purpose, and
unvalidated pagination is a potential abuse vector.

**Independent Test**: Send concurrent API requests and verify none
block. Send invalid pagination parameters (negative, zero, extremely
large) and verify proper error responses. Verify rate limiting
rejects excessive requests.

**Acceptance Scenarios**:

1. **Given** concurrent API requests, **When** processed by the
   backend, **Then** no request blocks others due to synchronous
   database calls.
2. **Given** invalid pagination parameters (page=0, limit=-1,
   limit=10000), **When** sent to the list endpoint, **Then**
   the API returns a 422 error with a descriptive message.
3. **Given** excessive requests from a single client, **When** the
   rate limit is exceeded, **Then** the API returns 429 Too Many
   Requests.
4. **Given** a new todo is created, **When** the created_at
   timestamp is recorded, **Then** it reflects the actual creation
   time, not the server startup time.

---

### User Story 5 - Code Quality and Developer Experience (Priority: P5)

A developer working on the codebase encounters consistent patterns,
no dead code, and clear separation of concerns. Currently, there is
duplicate validation logic between TodoForm and TodoEditForm, unused
components (LoadingOverlay), dead CSS (App.css boilerplate), a config
class with control flow issues, and dual ORM mapping patterns.

**Why this priority**: Maintainability determines how quickly future
features can be added. Inconsistent patterns and dead code slow down
every subsequent change.

**Independent Test**: Run the full linter suite, type checker, and
test suite with zero warnings. Verify no unused exports, no dead
code, and that each architectural layer has a single consistent
pattern.

**Acceptance Scenarios**:

1. **Given** the frontend codebase, **When** a developer looks for
   validation logic, **Then** it exists in exactly one place
   (shared hook or utility), not duplicated across form components.
2. **Given** the backend codebase, **When** a developer examines
   the ORM layer, **Then** there is one mapping pattern
   (declarative or imperative), not both.
3. **Given** the full codebase, **When** linters and type checkers
   run, **Then** zero errors and zero warnings are reported.
4. **Given** the frontend, **When** a developer searches for unused
   components or CSS, **Then** none exist.

---

### Edge Cases

- What happens when a user tries to restore an already-active todo?
- How does the UI behave when the backend is unreachable during
  initial page load (no cached data)?
- What happens when two browser tabs edit the same todo concurrently?
- How does pagination behave when items are deleted while browsing
  page 2?
- What happens when the database file is locked by another process?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST expose all backend-supported todo fields
  (title, description, done, deleted) through the frontend UI.
- **FR-002**: System MUST allow users to toggle the "done" status
  of any active todo with immediate visual feedback.
- **FR-003**: System MUST provide a mechanism to view soft-deleted
  todos and restore them to active status.
- **FR-004**: System MUST display pagination controls when the
  total number of todos exceeds the page size.
- **FR-005**: System MUST validate all user inputs at both frontend
  (inline feedback) and backend (API validation) layers.
- **FR-006**: System MUST display confirmation dialogs before
  destructive actions and show accurate success/failure feedback
  only after server confirmation.
- **FR-007**: Backend MUST process database operations
  asynchronously to avoid blocking the event loop.
- **FR-008**: Backend MUST validate pagination parameters and
  reject invalid values with descriptive errors.
- **FR-009**: Backend MUST enforce rate limiting on all endpoints.
- **FR-010**: System MUST use a single, consistent ORM mapping
  pattern throughout the backend.
- **FR-011**: Frontend MUST eliminate duplicated logic by
  extracting shared validation and form state into reusable hooks.
- **FR-012**: System MUST remove all dead code, unused components,
  and legacy CSS.
- **FR-013**: Backend MUST record timestamps using the actual
  current time, not a value captured at module load.

### Key Entities

- **Todo**: The central entity representing a task. Key attributes:
  unique identifier, title (required, max 255 chars), description
  (optional, max 255 chars), completion status, soft-delete status,
  creation timestamp, last-updated timestamp.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can create a todo with both title and
  description, mark it done, soft-delete it, and restore it—all
  from the UI—within a single session.
- **SC-002**: Every user action that can fail displays an
  appropriate error message within 2 seconds, with a retry option
  that does not require re-entering data.
- **SC-003**: Users can navigate through all their todos using
  pagination controls, with no todos hidden or inaccessible.
- **SC-004**: The system handles 50 concurrent users performing
  CRUD operations without any request blocking or degrading
  response times beyond acceptable thresholds.
- **SC-005**: All static analysis tools (type checkers, linters,
  formatters) report zero errors and zero warnings across the
  entire codebase.
- **SC-006**: Test coverage remains at or above 80% after all
  changes, with new features covered by both unit and integration
  tests.

## Assumptions

- The existing technology stack (FastAPI, React, SQLAlchemy,
  Chakra UI, SQLite) is retained. "Modernize" means adopting
  current best practices and leveraging existing framework
  capabilities (e.g., async SQLAlchemy, React 19 features), not
  replacing the stack.
- SQLite remains the database for development. Async support uses
  aiosqlite as the async driver.
- The application remains single-user for the current scope.
  Authentication and multi-user support are out of scope.
- Mobile-specific responsive design beyond basic viewport
  compatibility is out of scope.
- The soft-delete "recycle bin" is a UI section within the same
  page, not a separate route or page.
