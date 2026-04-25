# Quickstart: Full-Stack Modernization

**Date**: 2026-04-25
**Feature**: 001-modernize-fullstack

## Prerequisites

- Python 3.13+
- Node.js 18+
- UV package manager
- NPM

## Setup

### Backend

```bash
# Install dependencies (includes new aiosqlite)
cd /path/to/basicToDo
uv sync --locked --all-extras --dev

# Run backend server
python -m backend.app.main
# Server starts on http://0.0.0.0:8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# Dev server starts on http://localhost:5173
```

## Verify the Modernization

### 1. Complete Todo Lifecycle (US1)

1. Open http://localhost:5173
2. Create a todo with a title and description
3. Verify both fields display in the list
4. Click the checkbox to mark it done — verify visual indicator
5. Click again to unmark — verify indicator removed
6. Click Delete — confirm in dialog
7. Scroll to "Deleted" section — verify todo appears there
8. Click Restore — verify todo returns to active list

### 2. Error Handling (US2)

1. Stop the backend server
2. Try to create a todo — verify error toast with retry button
3. Restart the backend
4. Click retry — verify the todo is created

### 3. Pagination (US3)

1. Create 15+ todos
2. Verify pagination controls appear below the list
3. Navigate to page 2 — verify remaining todos appear
4. Navigate back to page 1 — verify original todos intact

### 4. Backend Validation (US4)

```bash
# Invalid pagination — expect 422
curl -s "http://localhost:8000/todo?limit=-1" | python -m json.tool

# Rate limiting — expect 429 after burst
for i in $(seq 1 35); do
  curl -s -o /dev/null -w "%{http_code}\n" \
    -X POST http://localhost:8000/todo \
    -H "Content-Type: application/json" \
    -d "{\"id\":\"$(uuidgen)\",\"title\":\"test $i\"}"
done

# Restore endpoint
curl -s -X PATCH http://localhost:8000/todo/{id}/restore \
  | python -m json.tool
```

### 5. Code Quality (US5)

```bash
# Backend checks
cd backend
uv run mypy backend/app/     # Zero errors
uv run pylint app/*.py        # Zero errors
uv run black --check app/     # Zero reformats needed

# Frontend checks
cd frontend
npm run lint                   # Zero errors

# Full test suites
uv run pytest backend/tests/   # All pass, >= 80% coverage
cd frontend && npm test -- --run  # All pass
```

## Key Changes from Previous Version

| Area | Before | After |
|------|--------|-------|
| DB operations | Synchronous (blocks event loop) | Async via aiosqlite |
| ORM mapping | Dual (declarative + imperative) | Declarative only |
| Timestamps | Fixed at module load | Per-record via `func.now()` |
| Pagination | Hardcoded limit=10, page=1, no controls | Validated params + UI controls |
| Done status | Backend only, invisible in UI | Full toggle with visual indicator |
| Description | Hardcoded "not implemented yet" | Editable text field |
| Soft delete | One-way (no restore) | Restore via UI + PATCH endpoint |
| Rate limiting | Dependency installed, not used | 60/30 req/min enforced |
| Config | Manual os.environ with bugs | Pydantic BaseSettings |
| Validation | Duplicated in 2 form components | Shared useTodoValidation hook |
| Dead code | LoadingOverlay, App.css boilerplate | Removed |
| Error feedback | Success toast before confirmation | Toast after server response |
