"""
SQL Injection and input validation tests for ToDoService.
"""

from uuid import uuid4

import pytest

from backend.app.business_logic.exceptions import (ToDoNotFoundError, ToDoValidationError)
from backend.app.factory import create_todo_service
from backend.app.schemas.data_schemes.create_todo_schema import ToDoCreateScheme
from backend.app.schemas.data_schemes.update_todo_schema import TodoUpdateScheme


@pytest.fixture
def todo_service():
    """Provide a clean service instance for each test."""
    return create_todo_service()


@pytest.mark.asyncio
async def test_create_valid_todo(todo_service):
    """Should create todo with normal text."""
    todo = ToDoCreateScheme(
        id=uuid4(),
        title="Buy milk",
        description="Remember to buy almond milk"
    )
    result = await todo_service.create_todo(todo)
    assert result.title == "Buy milk"
    assert result.description == "Remember to buy almond milk"


@pytest.mark.asyncio
async def test_update_valid_todo(todo_service):
    """Should allow updating with valid text."""
    todo = ToDoCreateScheme(id=uuid4(), title="Clean kitchen", description="Morning task")
    created = await todo_service.create_todo(todo)

    update = TodoUpdateScheme(
        id=created.id,
        title="Clean kitchen (updated)",
        description="Before lunch",
        done=False
    )
    updated = await todo_service.update_todo(created.id, update)
    assert updated.title.endswith("(updated)")


# --- 🚫 INJECTION ATTEMPTS --- #

@pytest.mark.asyncio
async def test_create_todo_with_sql_injection_attempt(todo_service):
    """Should raise validation error on SQL keywords."""
    malicious_inputs = [
        "DROP TABLE todo;",
        "Robert'); DROP TABLE students;--",
        "title'; DELETE FROM todo WHERE 'a'='a",
        "1; EXEC xp_cmdshell('rm -rf /')",
        "normal -- malicious comment",
        "safe; UPDATE todo SET done=1"
    ]

    for payload in malicious_inputs:
        with pytest.raises(ToDoValidationError):
            todo = ToDoCreateScheme(
                id=uuid4(),
                title=payload,
                description="attack test"
            )
            await todo_service.create_todo(todo)


@pytest.mark.asyncio
async def test_update_todo_with_sql_injection(todo_service):
    """Should reject SQL in title or description during update."""
    todo = ToDoCreateScheme(id=uuid4(), title="Test", description="Legit")
    created = await todo_service.create_todo(todo)

    bad_update = TodoUpdateScheme(
        id=created.id,
        title="; DROP TABLE toDo;",
        description="none",
        done=False
    )

    with pytest.raises(ToDoValidationError):
        await todo_service.update_todo(created.id, bad_update)


@pytest.mark.asyncio
async def test_get_todo_with_invalid_uuid(todo_service):
    """Should raise validation error for malformed UUIDs."""
    with pytest.raises(ToDoValidationError):
        await todo_service.get_todo("not-a-valid-uuid")


@pytest.mark.asyncio
async def test_delete_todo_with_invalid_uuid(todo_service):
    """Should raise validation error for invalid UUID in delete."""
    with pytest.raises(ToDoValidationError):
        await todo_service.delete_todo("'; DROP DATABASE main;--")


@pytest.mark.asyncio
async def test_get_todo_not_found(todo_service):
    """Should raise ToDoNotFoundError for non-existent IDs."""
    with pytest.raises(ToDoNotFoundError):
        await todo_service.get_todo(uuid4())