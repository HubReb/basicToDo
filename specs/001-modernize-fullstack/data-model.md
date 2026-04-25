# Data Model: Full-Stack Modernization

**Date**: 2026-04-25
**Feature**: 001-modernize-fullstack

## Entities

### Todo

The single entity in the system. After modernization, the ORM uses
declarative mapping only (removing the imperative `ToDoEntryData`
duplicate).

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| id | UUID | PK, indexed | Generated client-side |
| title | String(255) | NOT NULL, indexed | Required, validated |
| description | String(255) | nullable | Optional |
| created_at | TIMESTAMP(tz) | NOT NULL | `server_default=func.now()` |
| updated_at | TIMESTAMP(tz) | nullable | Set on update |
| deleted | Boolean | NOT NULL, default=False | Soft delete flag |
| done | Boolean | NOT NULL, default=False | Completion status |

**Indexes**:
- Primary key on `id`
- Index on `title` (existing)

### State Transitions

```
                    ┌──────────┐
        create ──►  │  Active  │
                    │ done=F   │
                    │ deleted=F│
                    └────┬─────┘
                         │
              ┌──────────┼──────────┐
              ▼          ▼          ▼
         mark done    update    soft delete
              │          │          │
              ▼          │          ▼
        ┌──────────┐    │    ┌──────────┐
        │ Completed│    │    │ Deleted  │
        │ done=T   │◄───┘    │ deleted=T│
        │ deleted=F│         └────┬─────┘
        └──────────┘              │
                              restore
                                  │
                                  ▼
                            ┌──────────┐
                            │  Active  │
                            │ (original│
                            │  state)  │
                            └──────────┘
```

**Rules**:
- Active → Completed: Sets `done=True`, `updated_at=now()`
- Completed → Active: Sets `done=False`, `updated_at=now()`
- Active/Completed → Deleted: Sets `deleted=True`, `updated_at=now()`
- Deleted → Active: Sets `deleted=False`, `updated_at=now()`.
  Preserves original `done` state.
- Only non-deleted items appear in the main list
- Deleted items appear in the "deleted" section only

## Schemas (Pydantic)

### Input Schemas

**ToDoCreateScheme** (unchanged):
- `id`: UUID (required, client-generated)
- `title`: str (required, non-empty, max 255)
- `description`: Optional[str] (max 255)

**TodoUpdateScheme** (unchanged):
- `title`: Optional[str]
- `description`: Optional[str]
- `done`: Optional[bool]

**PaginationParams** (new):
- `limit`: int (default=10, min=1, max=100)
- `page`: int (default=1, min=1)

### Output Schemas

**ToDoSchema** (unchanged):
- All fields from entity, `from_attributes=True`

**ListToDoResponse** (modified):
- `todo_entries`: List[ToDoSchema]
- `results`: int (count of items in response)
- `total_count`: int (new — total matching items in database)
- `success`: bool

**DeleteToDoResponse** (unchanged):
- `success`: bool
- `message`: str

## Migration Notes

No database migration tool is in use (SQLite with `create_all()`).
Schema changes are backward-compatible:
- No new columns
- No column type changes
- Only behavioral changes (correct `server_default`, removed
  dual mapping)
