# Quickstart: Modernize Full-Stack ToDo Application

**Branch**: `002-modernize-fullstack` | **Date**: 2026-04-25

Use these scenarios to validate the implementation end-to-end after each phase.

---

## Prerequisites

```bash
# Backend
cd /path/to/basicToDo
uv run python -m backend.app.main   # or: uvicorn backend.app.api.api:app --reload

# Frontend (separate terminal)
cd frontend && npm run dev
```

---

## Scenario 1 — Async Backend Starts Without Config File (US1)

```bash
# No JSON file, just env var
DATABASE_URL=sqlite+aiosqlite:///test_qs.db uv run python -m backend.app.main &
curl http://localhost:8000/
# Expected: {"status":"ok"}

# Concurrent creates
curl -s -X POST http://localhost:8000/todo \
  -H "Content-Type: application/json" \
  -d '{"id":"11111111-1111-1111-1111-111111111111","title":"First"}' &
curl -s -X POST http://localhost:8000/todo \
  -H "Content-Type: application/json" \
  -d '{"id":"22222222-2222-2222-2222-222222222222","title":"Second"}' &
wait
curl http://localhost:8000/todo
# Expected: both todos present in todo_entries
```

---

## Scenario 2 — Single ORM, No Import Errors (US2)

```bash
uv run pytest backend/tests/ -x -q
# Expected: all tests pass, no ImportError for ToDoEntryData
grep -r "ToDoEntryData" backend/ --include="*.py"
# Expected: no matches
```

---

## Scenario 3 — Pagination with Total Count (US3)

```bash
# Create 12 todos (use a loop)
for i in $(seq 1 12); do
  curl -s -X POST http://localhost:8000/todo \
    -H "Content-Type: application/json" \
    -d "{\"id\":\"$(python3 -c 'import uuid; print(uuid.uuid4())')\",\"title\":\"Todo $i\"}" > /dev/null
done

curl "http://localhost:8000/todo?limit=5&page=1"
# Expected: results=5, total_count=12

curl "http://localhost:8000/todo?limit=5&page=3"
# Expected: results=2, total_count=12

curl "http://localhost:8000/todo?limit=0"
# Expected: HTTP 422

curl "http://localhost:8000/todo?page=0"
# Expected: HTTP 422
```

---

## Scenario 4 — Rate Limiting (US3)

```bash
# Send 61 GETs rapidly
for i in $(seq 1 61); do
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/todo)
  echo "$i: $STATUS"
done
# Expected: first 60 return 200, 61st returns 429
```

---

## Scenario 5 — Soft Delete and Restore (US4)

```bash
# Create a todo
ID=$(python3 -c 'import uuid; print(uuid.uuid4())')
curl -s -X POST http://localhost:8000/todo \
  -H "Content-Type: application/json" \
  -d "{\"id\":\"$ID\",\"title\":\"Restore me\"}"

# Soft delete
curl -s -X DELETE http://localhost:8000/todo/$ID
curl -s http://localhost:8000/todo/$ID
# Expected: 404

# List deleted
curl -s http://localhost:8000/todo/deleted
# Expected: todo_entries contains the deleted item

# Restore
curl -s -X PATCH http://localhost:8000/todo/$ID/restore
curl -s http://localhost:8000/todo/$ID
# Expected: 200, deleted=false
```

---

## Scenario 6 — Description and Done Toggle (US5, UI)

1. Open `http://localhost:5173` in a browser.
2. Type a title and a description in the create form, press Enter.
3. Verify: todo appears in the list with description displayed.
4. Click the done checkbox on the todo.
5. Verify: todo shows checked checkbox and distinct styling (e.g. strikethrough / muted).
6. Click Edit, change the description, click Save.
7. Verify: updated description is shown.

---

## Scenario 7 — Pagination Controls (US6, UI)

1. Create 15 todos via the form.
2. Verify: list shows 10 items; Next button is enabled; Previous is disabled.
3. Click Next.
4. Verify: 5 items shown on page 2; Previous is enabled; Next is disabled.
5. Click Previous.
6. Verify: returns to page 1.

---

## Scenario 8 — Restore from Deleted Section (US6, UI)

1. Delete a todo from the list.
2. Open the "Deleted" collapsible section.
3. Verify: the deleted todo appears with a Restore button.
4. Click Restore.
5. Verify: item disappears from the Deleted section immediately (optimistic).
6. Verify: item reappears in the active list.

---

## Scenario 9 — Shared Validation + Dead Code (US7)

```bash
cd frontend
npx tsc --noEmit
# Expected: 0 errors

grep -r "validateTitle" src/ --include="*.ts" --include="*.tsx" -l
# Expected: only useTodoValidation.ts

grep -r "LoadingOverlay" src/ --include="*.ts" --include="*.tsx"
# Expected: no matches

grep "space-betwee" src/components/Header.tsx
# Expected: no matches (typo fixed)
```

---

## Full Suite Validation

```bash
# Backend coverage gate
uv run pytest backend/tests/ --cov=backend/app --cov-fail-under=80 -q
# Expected: PASSED, coverage ≥ 80%

# Frontend type check + unit tests
cd frontend && npx tsc --noEmit && npm run test
# Expected: 0 compile errors, all tests pass

# Bundle size
npm run build
# Expected: dist/assets/*.js gzip < 500 KB (check with: gzip -c dist/assets/*.js | wc -c)
```
