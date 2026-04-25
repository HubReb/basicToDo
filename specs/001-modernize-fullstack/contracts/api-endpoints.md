# API Endpoint Contracts: Full-Stack Modernization

**Date**: 2026-04-25
**Feature**: 001-modernize-fullstack

## Base URL

`http://localhost:8000`

## Existing Endpoints (modified)

### GET /todo

List active (non-deleted) todos with pagination.

**Query Parameters**:

| Param | Type | Default | Constraints |
|-------|------|---------|-------------|
| limit | int | 10 | 1-100 |
| page | int | 1 | >= 1 |

**Response 200**:
```json
{
  "success": true,
  "results": 10,
  "total_count": 42,
  "todo_entries": [
    {
      "id": "uuid",
      "title": "string",
      "description": "string|null",
      "created_at": "ISO8601",
      "updated_at": "ISO8601|null",
      "deleted": false,
      "done": false
    }
  ]
}
```

**Response 422** (invalid pagination):
```json
{
  "success": false,
  "error": "Validation error",
  "detail": [
    {
      "loc": ["query", "limit"],
      "msg": "ensure this value is greater than or equal to 1"
    }
  ]
}
```

**Changes**: Added `total_count` field. Added pagination param
validation (422 on invalid). Previously accepted any integer.

---

### POST /todo

Create a new todo. No changes to request/response shape.

**Request Body**:
```json
{
  "id": "uuid",
  "title": "string (required, max 255)",
  "description": "string|null (max 255)"
}
```

**Response 200**:
```json
{
  "success": true,
  "todo_entry": { "...todo fields..." }
}
```

**Error Responses**: 400 (validation), 409 (duplicate), 500 (server)

---

### GET /todo/{todo_id}

Get a single active todo by ID. No changes.

**Response 200**: `{ "success": true, "todo_entry": {...} }`
**Response 404**: `{ "success": false, "error": "Not found" }`

---

### PUT /todo/{todo_id}

Update a todo. No changes to contract.

**Request Body**:
```json
{
  "title": "string|null",
  "description": "string|null",
  "done": "bool|null"
}
```

**Response 200**: `{ "success": true, "todo_entry": {...} }`
**Error Responses**: 400, 404, 500

---

### DELETE /todo/{todo_id}

Soft-delete a todo. No changes to contract.

**Response 200**:
```json
{
  "success": true,
  "message": "Todo deleted successfully"
}
```

**Error Responses**: 400, 404, 500

---

## New Endpoints

### GET /todo/deleted

List soft-deleted todos with pagination.

**Query Parameters**: Same as `GET /todo` (limit, page)

**Response 200**:
```json
{
  "success": true,
  "results": 3,
  "total_count": 3,
  "todo_entries": [
    {
      "id": "uuid",
      "title": "string",
      "description": "string|null",
      "created_at": "ISO8601",
      "updated_at": "ISO8601|null",
      "deleted": true,
      "done": false
    }
  ]
}
```

---

### PATCH /todo/{todo_id}/restore

Restore a soft-deleted todo to active status.

**Request Body**: None

**Response 200**:
```json
{
  "success": true,
  "todo_entry": {
    "id": "uuid",
    "title": "string",
    "description": "string|null",
    "created_at": "ISO8601",
    "updated_at": "ISO8601",
    "deleted": false,
    "done": false
  }
}
```

**Response 404**:
```json
{
  "success": false,
  "error": "Todo not found or not deleted"
}
```

**Response 400**: Invalid UUID
**Response 500**: Server error

---

## Rate Limiting

All endpoints are rate-limited per client IP:

| Endpoint Type | Rate Limit |
|---------------|------------|
| Read (GET) | 60 req/min |
| Write (POST, PUT, DELETE, PATCH) | 30 req/min |

**Response 429**:
```json
{
  "error": "Rate limit exceeded",
  "retry_after": 30
}
```

Header: `Retry-After: 30`

---

## Health Check

### GET /

**Response 200**: `{ "status": "ok" }`

No changes.
