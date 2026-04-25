# Soft Delete Implementation Plan

**Feature**: Add soft deletion functionality to the ToDo API
**Status**: Planning
**Priority**: High
**Estimated Effort**: 4-6 hours

---

## Overview

Implement soft deletion for ToDo items following the clean architecture pattern. The database schema already includes a `deleted` boolean field, but the API endpoints and business logic need to be implemented.

## Current State

### Existing Infrastructure
- ✅ Database schema has `deleted` field (Boolean, default: False)
- ✅ Clean architecture with Repository → Service → API layers
- ✅ SQLAlchemy ORM models in place
- ❌ No API endpoints for soft delete operations
- ❌ No business logic for soft delete/restore
- ❌ List endpoint doesn't filter deleted items

## Requirements

### Functional Requirements
1. **Soft Delete**: Mark a ToDo item as deleted without removing from database
2. **List Active**: Default list endpoint excludes deleted items
3. **List Deleted**: Separate endpoint to retrieve only deleted items
4. **Restore**: Undelete a soft-deleted item
5. **Permanent Delete**: Hard delete (optional, for admin/cleanup)
6. **Filter Control**: Query parameter to include deleted items in main list

### Non-Functional Requirements
- Maintain backward compatibility with existing endpoints
- Follow existing clean architecture pattern
- Comprehensive test coverage (unit + integration)
- Proper error handling for edge cases
- Type safety with MyPy strict mode

---

## Implementation Steps

### Phase 1: Data Access Layer (Repository)

**File**: `backend/app/data_access/repository.py`

#### 1.1 Update ToDoRepositoryInterface

Add new abstract methods:
```python
@abstractmethod
def soft_delete(self, todo_id: str) -> Optional[ToDoEntryData]:
    """Mark a todo as deleted"""
    pass

@abstractmethod
def restore(self, todo_id: str) -> Optional[ToDoEntryData]:
    """Restore a soft-deleted todo"""
    pass

@abstractmethod
def get_deleted(self, limit: int, page: int) -> tuple[list[ToDoEntryData], int]:
    """Get all soft-deleted todos with pagination"""
    pass

@abstractmethod
def get_all(self, limit: int, page: int, include_deleted: bool = False) -> tuple[list[ToDoEntryData], int]:
    """Update existing method to support include_deleted parameter"""
    pass
```

#### 1.2 Implement in ToDoRepository

```python
def soft_delete(self, todo_id: str) -> Optional[ToDoEntryData]:
    """Mark a todo as deleted"""
    with safe_session_scope() as session:
        todo = session.query(ToDo).filter(ToDo.id == todo_id).first()
        if not todo:
            return None

        # Already deleted
        if todo.deleted:
            return None

        todo.deleted = True
        todo.updated_at = datetime.now(timezone.utc)
        session.commit()

        return ToDoEntryData(
            id=todo.id,
            title=todo.title,
            description=todo.description,
            created_at=todo.created_at,
            updated_at=todo.updated_at,
            deleted=todo.deleted,
            done=todo.done
        )

def restore(self, todo_id: str) -> Optional[ToDoEntryData]:
    """Restore a soft-deleted todo"""
    with safe_session_scope() as session:
        todo = session.query(ToDo).filter(ToDo.id == todo_id).first()
        if not todo:
            return None

        # Not deleted, nothing to restore
        if not todo.deleted:
            return None

        todo.deleted = False
        todo.updated_at = datetime.now(timezone.utc)
        session.commit()

        return ToDoEntryData(
            id=todo.id,
            title=todo.title,
            description=todo.description,
            created_at=todo.created_at,
            updated_at=todo.updated_at,
            deleted=todo.deleted,
            done=todo.done
        )

def get_deleted(self, limit: int, page: int) -> tuple[list[ToDoEntryData], int]:
    """Get all soft-deleted todos"""
    with safe_session_scope() as session:
        offset = (page - 1) * limit

        query = session.query(ToDo).filter(ToDo.deleted == True)
        total = query.count()

        todos = query.order_by(ToDo.updated_at.desc()).offset(offset).limit(limit).all()

        return (
            [
                ToDoEntryData(
                    id=todo.id,
                    title=todo.title,
                    description=todo.description,
                    created_at=todo.created_at,
                    updated_at=todo.updated_at,
                    deleted=todo.deleted,
                    done=todo.done
                )
                for todo in todos
            ],
            total
        )

def get_all(self, limit: int, page: int, include_deleted: bool = False) -> tuple[list[ToDoEntryData], int]:
    """Updated to filter deleted items by default"""
    with safe_session_scope() as session:
        offset = (page - 1) * limit

        query = session.query(ToDo)

        # Filter out deleted items unless explicitly requested
        if not include_deleted:
            query = query.filter(ToDo.deleted == False)

        total = query.count()
        todos = query.order_by(ToDo.created_at.desc()).offset(offset).limit(limit).all()

        return (
            [
                ToDoEntryData(
                    id=todo.id,
                    title=todo.title,
                    description=todo.description,
                    created_at=todo.created_at,
                    updated_at=todo.updated_at,
                    deleted=todo.deleted,
                    done=todo.done
                )
                for todo in todos
            ],
            total
        )
```

**Tests**: `backend/tests/test_repository.py`
- Test soft_delete marks item as deleted
- Test soft_delete on non-existent item returns None
- Test soft_delete on already deleted item returns None
- Test restore unmarks deleted flag
- Test restore on non-existent item returns None
- Test restore on non-deleted item returns None
- Test get_deleted returns only deleted items
- Test get_all excludes deleted by default
- Test get_all with include_deleted=True includes all items

---

### Phase 2: Business Logic Layer (Service)

**File**: `backend/app/business_logic/todo_service.py`

#### 2.1 Add New Service Methods

```python
def soft_delete_todo(self, todo_id: str) -> Optional[ToDoEntryData]:
    """Soft delete a todo item"""
    # Validate UUID format
    if not self._is_valid_uuid(todo_id):
        raise InvalidUUIDError(f"Invalid UUID format: {todo_id}")

    result = self.repository.soft_delete(todo_id)

    if result is None:
        raise ToDoNotFoundError(f"Todo with id {todo_id} not found or already deleted")

    return result

def restore_todo(self, todo_id: str) -> Optional[ToDoEntryData]:
    """Restore a soft-deleted todo item"""
    # Validate UUID format
    if not self._is_valid_uuid(todo_id):
        raise InvalidUUIDError(f"Invalid UUID format: {todo_id}")

    result = self.repository.restore(todo_id)

    if result is None:
        raise ToDoNotFoundError(f"Todo with id {todo_id} not found or not deleted")

    return result

def get_deleted_todos(self, limit: int = 10, page: int = 1) -> tuple[list[ToDoEntryData], int]:
    """Get all deleted todos with pagination"""
    if limit <= 0 or page <= 0:
        raise ValueError("Limit and page must be positive integers")

    return self.repository.get_deleted(limit, page)

def list_todos(self, limit: int = 10, page: int = 1, include_deleted: bool = False) -> tuple[list[ToDoEntryData], int]:
    """Updated to support include_deleted parameter"""
    if limit <= 0 or page <= 0:
        raise ValueError("Limit and page must be positive integers")

    return self.repository.get_all(limit, page, include_deleted)
```

#### 2.2 Add New Exception Classes

**File**: `backend/app/business_logic/exceptions.py`

```python
class ToDoAlreadyDeletedError(Exception):
    """Raised when trying to soft delete an already deleted todo"""
    pass

class ToDoNotDeletedError(Exception):
    """Raised when trying to restore a non-deleted todo"""
    pass
```

**Tests**: `backend/tests/test_todo_service.py`
- Test soft_delete_todo with valid UUID
- Test soft_delete_todo with invalid UUID raises InvalidUUIDError
- Test soft_delete_todo with non-existent ID raises ToDoNotFoundError
- Test restore_todo with valid UUID
- Test restore_todo with invalid UUID raises InvalidUUIDError
- Test restore_todo with non-deleted item raises ToDoNotFoundError
- Test get_deleted_todos returns only deleted items
- Test list_todos excludes deleted by default
- Test list_todos with include_deleted=True

---

### Phase 3: API Layer (Endpoints)

**File**: `backend/app/api/api.py`

#### 3.1 Update Response Schema

**File**: `backend/app/schemas/todo_response.py`

```python
class ToDoResponse(BaseModel):
    id: str
    title: str
    description: str
    created_at: datetime
    updated_at: Optional[datetime]
    deleted: bool  # Ensure this field is included
    done: bool

class ToDoListResponse(BaseModel):
    todo_entries: list[ToDoResponse]
    results: int
    page: int
    limit: int
```

#### 3.2 Add New Endpoints

```python
@router.patch("/todo/{todo_id}/soft-delete")
async def soft_delete_todo(todo_id: str) -> ToDoResponse:
    """
    Soft delete a todo item (mark as deleted without removing from database)

    - **todo_id**: UUID of the todo to soft delete

    Returns the soft-deleted todo item
    Raises 404 if todo not found or already deleted
    Raises 400 if UUID format is invalid
    """
    try:
        result = todo_service.soft_delete_todo(todo_id)
        return ToDoResponse(
            id=result.id,
            title=result.title,
            description=result.description,
            created_at=result.created_at,
            updated_at=result.updated_at,
            deleted=result.deleted,
            done=result.done
        )
    except InvalidUUIDError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ToDoNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.patch("/todo/{todo_id}/restore")
async def restore_todo(todo_id: str) -> ToDoResponse:
    """
    Restore a soft-deleted todo item

    - **todo_id**: UUID of the todo to restore

    Returns the restored todo item
    Raises 404 if todo not found or not deleted
    Raises 400 if UUID format is invalid
    """
    try:
        result = todo_service.restore_todo(todo_id)
        return ToDoResponse(
            id=result.id,
            title=result.title,
            description=result.description,
            created_at=result.created_at,
            updated_at=result.updated_at,
            deleted=result.deleted,
            done=result.done
        )
    except InvalidUUIDError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ToDoNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/todo/deleted")
async def list_deleted_todos(
    limit: int = Query(default=10, ge=1, le=100),
    page: int = Query(default=1, ge=1)
) -> ToDoListResponse:
    """
    Get all soft-deleted todo items with pagination

    - **limit**: Number of items per page (1-100)
    - **page**: Page number (1-based)

    Returns paginated list of deleted todos
    """
    todos, total = todo_service.get_deleted_todos(limit, page)

    return ToDoListResponse(
        todo_entries=[
            ToDoResponse(
                id=todo.id,
                title=todo.title,
                description=todo.description,
                created_at=todo.created_at,
                updated_at=todo.updated_at,
                deleted=todo.deleted,
                done=todo.done
            )
            for todo in todos
        ],
        results=total,
        page=page,
        limit=limit
    )

@router.get("/todo")
async def list_todos(
    limit: int = Query(default=10, ge=1, le=100),
    page: int = Query(default=1, ge=1),
    include_deleted: bool = Query(default=False)
) -> ToDoListResponse:
    """
    Updated: Add include_deleted query parameter

    - **limit**: Number of items per page (1-100)
    - **page**: Page number (1-based)
    - **include_deleted**: Include soft-deleted items (default: False)

    Returns paginated list of todos
    """
    todos, total = todo_service.list_todos(limit, page, include_deleted)

    return ToDoListResponse(
        todo_entries=[
            ToDoResponse(
                id=todo.id,
                title=todo.title,
                description=todo.description,
                created_at=todo.created_at,
                updated_at=todo.updated_at,
                deleted=todo.deleted,
                done=todo.done
            )
            for todo in todos
        ],
        results=total,
        page=page,
        limit=limit
    )
```

**Tests**: `backend/tests/test_api.py`
- Test PATCH /todo/{id}/soft-delete returns 200 and marks as deleted
- Test PATCH /todo/{id}/soft-delete returns 404 for non-existent todo
- Test PATCH /todo/{id}/soft-delete returns 400 for invalid UUID
- Test PATCH /todo/{id}/soft-delete returns 404 for already deleted todo
- Test PATCH /todo/{id}/restore returns 200 and unmarks deleted
- Test PATCH /todo/{id}/restore returns 404 for non-existent todo
- Test PATCH /todo/{id}/restore returns 400 for invalid UUID
- Test PATCH /todo/{id}/restore returns 404 for non-deleted todo
- Test GET /todo/deleted returns only deleted items
- Test GET /todo excludes deleted items by default
- Test GET /todo?include_deleted=true includes deleted items

---

## API Endpoint Summary

### New Endpoints

| Method | Path | Description | Status Code |
|--------|------|-------------|-------------|
| PATCH | `/todo/{id}/soft-delete` | Soft delete a todo | 200, 400, 404 |
| PATCH | `/todo/{id}/restore` | Restore deleted todo | 200, 400, 404 |
| GET | `/todo/deleted` | List deleted todos | 200 |

### Modified Endpoints

| Method | Path | Changes |
|--------|------|---------|
| GET | `/todo` | Added `include_deleted` query parameter |

---

## Testing Strategy

### Unit Tests (Repository Layer)
- Test all new repository methods with mocked database
- Test edge cases (non-existent IDs, already deleted, not deleted)
- Test pagination for get_deleted

### Unit Tests (Service Layer)
- Test business logic with mocked repository
- Test validation (UUID format, positive integers)
- Test exception handling

### Integration Tests (API Layer)
- Test full request/response cycle
- Test status codes
- Test request validation
- Test error responses

### End-to-End Tests
- Test complete soft delete → list → restore flow
- Test that deleted items don't appear in default list
- Test pagination with deleted items

---

## Migration Plan

### Database Migration
No migration needed - `deleted` field already exists in schema.

### API Versioning
Not required - new endpoints don't break existing functionality.

### Backward Compatibility
- ✅ Existing `GET /todo` will exclude deleted items by default
- ✅ This is a **breaking change** if clients expect deleted items
- **Mitigation**: Update CHANGELOG and API documentation
- Consider adding deprecation notice if current behavior needs to be maintained

---

## Implementation Checklist

### Phase 1: Repository Layer (1-2 hours)
- [ ] Add interface methods to `ToDoRepositoryInterface`
- [ ] Implement `soft_delete` method
- [ ] Implement `restore` method
- [ ] Implement `get_deleted` method
- [ ] Update `get_all` to filter deleted items
- [ ] Write unit tests for repository methods
- [ ] Verify MyPy type checking passes

### Phase 2: Service Layer (1-2 hours)
- [ ] Add new exception classes
- [ ] Implement `soft_delete_todo` method
- [ ] Implement `restore_todo` method
- [ ] Implement `get_deleted_todos` method
- [ ] Update `list_todos` signature
- [ ] Write unit tests for service methods
- [ ] Verify MyPy type checking passes

### Phase 3: API Layer (1-2 hours)
- [ ] Add `PATCH /todo/{id}/soft-delete` endpoint
- [ ] Add `PATCH /todo/{id}/restore` endpoint
- [ ] Add `GET /todo/deleted` endpoint
- [ ] Update `GET /todo` with `include_deleted` parameter
- [ ] Update response schemas
- [ ] Write integration tests for all endpoints
- [ ] Verify MyPy type checking passes

### Phase 4: Testing & Documentation (1 hour)
- [ ] Run full test suite (`pytest backend/tests/`)
- [ ] Verify coverage >= 80%
- [ ] Run MyPy (`mypy backend/app/`)
- [ ] Run Pylint (`pylint backend/app/*.py`)
- [ ] Update API documentation (Swagger/OpenAPI)
- [ ] Update CHANGELOG.md
- [ ] Update README.md with new endpoints

---

## Potential Issues & Solutions

### Issue 1: Existing deleted items in database
**Problem**: If there are already soft-deleted items, default list will change behavior
**Solution**:
- Run a data audit before deploying
- Consider a feature flag to gradually roll out
- Communicate change in release notes

### Issue 2: Hard delete functionality
**Problem**: Soft-deleted items accumulate forever
**Decision Needed**: Should we implement hard delete?
**Options**:
- Add `DELETE /todo/{id}/permanent` endpoint (admin only)
- Add background job to purge old deleted items (e.g., after 30 days)
- Leave for future iteration

### Issue 3: Cascade deletes
**Problem**: No relationships currently, but if added in future
**Solution**: Document expected behavior in schema

---

## Future Enhancements

1. **Batch Operations**
   - `POST /todo/batch/soft-delete` - Delete multiple items
   - `POST /todo/batch/restore` - Restore multiple items

2. **Deleted Timestamp**
   - Add `deleted_at` field to track when item was deleted
   - Useful for "deleted X days ago" UI

3. **Audit Log**
   - Track who deleted/restored items
   - Requires user authentication system

4. **Auto-purge**
   - Scheduled job to permanently delete items after N days
   - Configurable retention period

5. **Recycle Bin UI**
   - Frontend feature to manage deleted items
   - "Empty Recycle Bin" functionality

---

## Success Criteria

✅ All new endpoints return correct responses
✅ Existing endpoints maintain backward compatibility
✅ Test coverage >= 80%
✅ MyPy strict mode passes
✅ Pylint passes with no errors
✅ API documentation updated
✅ All CI/CD checks pass

---

## References

- Clean Architecture Pattern: `/CLAUDE.md`
- Database Schema: `/CLAUDE.md#database-schema`
- Existing Tests: `/backend/tests/`
- API Documentation: `http://localhost:8000/docs`
