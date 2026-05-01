# Data Model: Modernize Full-Stack ToDo Application

**Branch**: `002-modernize-fullstack` | **Date**: 2026-04-25

---

## Entity: Todo

**ORM class**: `ToDoORM` (in `backend/app/data_access/database.py`)
**Table name**: `toDo` (preserved — no migration required)

### Fields

| Field | Type | Nullable | Default | Constraints |
|-------|------|----------|---------|-------------|
| `id` | UUID | No | `uuid.uuid4()` | Primary key |
| `title` | String(255) | No | — | `length(title) <= 255` CHECK |
| `description` | String(255) | Yes | `NULL` | `length(description) <= 255` CHECK |
| `created_at` | TIMESTAMP (tz-aware) | No | `func.now()` (server default) | Set by builder on create |
| `updated_at` | TIMESTAMP (tz-aware) | Yes | `NULL` | Set by repository on update |
| `deleted` | Boolean | No | `False` | Soft-delete flag |
| `done` | Boolean | No | `False` | Completion flag |

### Validation Rules

- `title`: required, trimmed, 1–255 characters. Whitespace-only → rejected (HTTP 400).
- `description`: optional, trimmed, 0–255 characters.
- `id`: must be a valid UUID v4; provided by the client on create.
- `deleted` and `done` are server-controlled; not writable directly via create schema.

### State Transitions

```text
ACTIVE  (deleted=false, done=false)
  │
  ├─[mark done]──────────────► ACTIVE+DONE  (deleted=false, done=true)
  │                                │
  │                                └─[unmark done]─► ACTIVE
  │
  └─[delete]─────────���───────► DELETED  (deleted=true, done=any)
                                   │
                                   └─[restore]──────► ACTIVE (done preserved)
```

### Pydantic Schema (API layer)

**ToDoSchema** (read): all fields above  
**ToDoCreateScheme** (write): `id`, `title`, `description?`  
**TodoUpdateScheme** (write): `title?`, `description?`, `done?`  

`created_at` and `updated_at` are ISO 8601 strings in API responses.  
`deleted` is returned in responses but is not a writable field on create/update.

---

## No Relationships

This application has a single entity. No foreign keys or join tables are required.
