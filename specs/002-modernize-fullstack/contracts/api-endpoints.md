# API Contracts: Modernize Full-Stack ToDo Application

**Branch**: `002-modernize-fullstack` | **Date**: 2026-04-25  
**Base URL**: `http://localhost:8000`

---

## General Conventions

- All responses are `application/json`.
- All timestamps are ISO 8601 with timezone (e.g. `2026-04-25T14:00:00+00:00`).
- UUIDs are lowercase hyphenated strings.
- Rate limit headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`.
- 429 responses include `Retry-After` header (seconds).

---

## GET /

Health check.

**Rate limit**: exempt  
**Response 200**:
```json
{ "status": "ok" }
```

---

## GET /todo

List active (non-deleted) todos with pagination.

**Rate limit**: 60/minute per IP  
**Query params**:
| Param | Type | Default | Constraints |
|-------|------|---------|-------------|
| `limit` | int | 10 | 1 ≤ limit ≤ 100 |
| `page` | int | 1 | page ≥ 1 |

**Response 200**:
```json
{
  "success": true,
  "results": 5,
  "total_count": 25,
  "todo_entries": [
    {
      "id": "uuid",
      "title": "string",
      "description": "string | null",
      "created_at": "ISO8601",
      "updated_at": "ISO8601 | null",
      "deleted": false,
      "done": false
    }
  ]
}
```

**Response 422**: `limit` or `page` out of range.

---

## GET /todo/deleted

List soft-deleted todos with pagination.

**Rate limit**: 60/minute per IP  
**Query params**: same as `GET /todo`  
**Response 200**: same shape as `GET /todo` with `deleted: true` entries.  
**Note**: This route MUST be defined before `GET /todo/{todo_id}` in the router.

---

## GET /todo/{todo_id}

Get a single active todo by ID.

**Rate limit**: 60/minute per IP  
**Path param**: `todo_id` — UUID  
**Response 200**:
```json
{ "success": true, "todo_entry": { ...Todo... } }
```
**Response 404**: Todo not found or is soft-deleted.  
**Response 422**: `todo_id` is not a valid UUID.

---

## POST /todo

Create a new todo.

**Rate limit**: 30/minute per IP  
**Request body**:
```json
{ "id": "uuid", "title": "string", "description": "string | null" }
```
**Response 201** (or 200 — FastAPI default):
```json
{ "success": true, "todo_entry": { ...Todo... } }
```
**Response 400**: Validation error (empty title, etc.).  
**Response 409**: Todo with this ID already exists.  
**Response 500**: Repository error.

---

## PUT /todo/{todo_id}

Update an existing active todo.

**Rate limit**: 30/minute per IP  
**Request body** (all fields optional):
```json
{ "title": "string", "description": "string | null", "done": false }
```
**Response 200**:
```json
{ "success": true, "todo_entry": { ...Todo... } }
```
**Response 400**: Validation error.  
**Response 404**: Todo not found or is soft-deleted.

---

## DELETE /todo/{todo_id}

Soft-delete a todo (sets `deleted=true`).

**Rate limit**: 30/minute per IP  
**Response 200**:
```json
{ "success": true, "message": "Deleted successfully" }
```
**Response 404**: Todo not found.

---

## PATCH /todo/{todo_id}/restore

Restore a soft-deleted todo (sets `deleted=false`).

**Rate limit**: 30/minute per IP  
**Response 200**:
```json
{ "success": true, "todo_entry": { ...Todo... } }
```
**Response 404**: Todo not found OR todo is not in deleted state.

---

## Frontend UI Contracts

### useTodoValidation hook

```typescript
interface TodoValidation {
  validateTitle(value: string): string | null   // returns error message or null
  validateDescription(value: string): string | null
  error: string
  setError: (msg: string) => void
  clearError: () => void
}
```

### Pagination component

```typescript
interface PaginationProps {
  page: number
  totalCount: number
  limit: number
  onNext: () => void
  onPrev: () => void
}
// Previous disabled when page === 1
// Next disabled when page * limit >= totalCount
```

### TodoRestoreButton

```typescript
interface TodoRestoreButtonProps {
  id: string
}
// Uses useRestoreTodo mutation
// Optimistic: removes from deleted list, adds to active list before server responds
// Rollback on error
```
