import datetime
import uuid
from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import IntegrityError

from backend.app.business_logic.exceptions import (
    ToDoAlreadyExistsError,
    ToDoNotFoundError,
    ToDoValidationError,
)
from backend.app.business_logic.todo_service import ToDoService
from backend.app.models.todo import ToDoEntryData
from backend.app.schemas.todo import ToDoCreateEntry, TodoUpdateEntry


@pytest.fixture
def mock_repository():
    repo = MagicMock()
    return repo


@pytest.fixture
def mock_logger():
    logger = MagicMock()
    return logger


@pytest.fixture
def todo_service(mock_repository, mock_logger):
    return ToDoService(repository=mock_repository, logger=mock_logger)


@pytest.mark.asyncio
async def test_create_todo_success(todo_service, mock_repository):
    todo_id = uuid.uuid4()
    payload = ToDoCreateEntry(id=todo_id, title="Test", description="Desc")
    mock_repository.create_to_do.return_value = None

    result = await todo_service.create_todo(payload)

    assert result.title == "Test"
    mock_repository.create_to_do.assert_called_once()


@pytest.mark.asyncio
async def test_create_todo_already_exists(todo_service, mock_repository):
    todo_id = uuid.uuid4()
    payload = ToDoCreateEntry(id=todo_id, title="Duplicate", description="Desc")
    mock_repository.create_to_do.side_effect = IntegrityError("msg", "params", "orig")

    with pytest.raises(ToDoAlreadyExistsError):
        await todo_service.create_todo(payload)


@pytest.mark.asyncio
async def test_get_todo_success(todo_service, mock_repository):
    todo_id = uuid.uuid4()
    mock_entry = ToDoEntryData(id=todo_id, title="Test", description="Desc",
                               created_at=datetime.datetime.utcnow(), updated_at=None, done=False, deleted=False)
    mock_repository.get_to_do_entry.return_value = mock_entry

    result = await todo_service.get_todo(todo_id)

    assert result.id == todo_id
    mock_repository.get_to_do_entry.assert_called_once_with(todo_id)


@pytest.mark.asyncio
async def test_get_todo_not_found(todo_service, mock_repository):
    mock_repository.get_to_do_entry.return_value = None

    with pytest.raises(ToDoNotFoundError):
        await todo_service.get_todo(uuid.uuid4())


@pytest.mark.asyncio
async def test_get_todo_invalid_uuid(todo_service):
    invalid_id = "not-a-valid-uuid"

    with pytest.raises(ToDoValidationError):
        await todo_service.get_todo(invalid_id)


@pytest.mark.asyncio
async def test_update_todo_success(todo_service, mock_repository):
    todo_id = uuid.uuid4()
    payload = TodoUpdateEntry(id=todo_id, title="Updated", description="Updated")
    mock_entry = ToDoEntryData(id=todo_id, title="Updated", description="Updated",
                               created_at=datetime.datetime.utcnow(), updated_at=datetime.datetime.utcnow(), done=False,
                               deleted=False)
    mock_repository.update_to_do.return_value = mock_entry

    result = await todo_service.update_todo(todo_id, payload)

    assert result.title == "Updated"
    mock_repository.update_to_do.assert_called_once_with(todo_id, payload)


@pytest.mark.asyncio
async def test_update_todo_not_found(todo_service, mock_repository):
    mock_repository.update_to_do.return_value = None
    todo_id = uuid.uuid4()
    payload = TodoUpdateEntry(id=todo_id, title="Updated", description="Updated")

    with pytest.raises(ToDoNotFoundError):
        await todo_service.update_todo(todo_id, payload)


@pytest.mark.asyncio
async def test_update_todo_already_exists(todo_service, mock_repository):
    todo_id = uuid.uuid4()
    payload = TodoUpdateEntry(id=todo_id, title="Duplicate", description="Desc")
    mock_repository.update_to_do.side_effect = IntegrityError("msg", "params", "orig")

    with pytest.raises(ToDoAlreadyExistsError):
        await todo_service.update_todo(todo_id, payload)


@pytest.mark.asyncio
async def test_delete_todo_success(todo_service, mock_repository):
    todo_id = uuid.uuid4()
    mock_repository.delete_to_do.return_value = True

    result = await todo_service.delete_todo(todo_id)

    assert result is True
    mock_repository.delete_to_do.assert_called_once_with(todo_id)


@pytest.mark.asyncio
async def test_delete_todo_not_found(todo_service, mock_repository):
    mock_repository.delete_to_do.return_value = False
    todo_id = uuid.uuid4()

    with pytest.raises(ToDoNotFoundError):
        await todo_service.delete_todo(todo_id)


@pytest.mark.asyncio
async def test_get_all_todos_skips_invalid(todo_service, mock_repository):
    valid_entry = ToDoEntryData(id=uuid.uuid4(), title="Valid", description="Desc",
                                created_at=datetime.datetime.utcnow(), updated_at=None, done=False, deleted=False)
    invalid_entry = "invalid entry"
    mock_repository.get_all_to_do_entries.return_value = [valid_entry, invalid_entry]

    result = await todo_service.get_all_todos()

    assert len(result) == 1
    assert result[0].title == "Valid"